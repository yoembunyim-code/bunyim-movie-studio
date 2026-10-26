import streamlit as st
import os
import subprocess
import tempfile
import numpy as np
import scipy.io.wavfile as wav
import re
import time

# ប្រើ faster-whisper ជំនួស whisper ដើម ដើម្បីដោះស្រាយ Error និងបង្កើនល្បឿន
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    st.error("⚠️ សូមដំឡើង `faster-whisper` ជាមុនសិន៖ `pip install faster-whisper`")

# ប្រើ deep-translator ជំនួស translate (គាំទ្រខ្មែរល្អជាង)
try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False

st.set_page_config(
    page_title="VoiceClone Studio Pro - Exact Subtitle-Audio Sync Master",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stApp { background-color: #05070C !important; color: #E2E8F0;
        font-family: 'Khmer OS Battambang', 'Segoe UI', sans-serif; }
    .header-bar { display:flex; align-items:center; justify-content:space-between;
        background: linear-gradient(90deg, #0B101D 0%, #151D30 100%);
        padding:12px 20px; border-radius:12px; border:1px solid #1E293B;
        box-shadow:0 4px 20px rgba(0,0,0,0.6); margin-bottom:15px; }
    .brand-title { font-size:20px; font-weight:800;
        background: linear-gradient(135deg,#38BDF8 0%,#818CF8 50%,#C084FC 100%);
        -webkit-background-clip:text; -webkit-text-fill-color:transparent;
        display:flex; align-items:center; gap:10px; }
    .card-panel { background:#0D121F; border:1px solid #1E293B; border-radius:12px;
        padding:18px; box-shadow:0 4px 12px rgba(0,0,0,0.4); margin-bottom:20px; }
    .stButton > button { background: linear-gradient(135deg,#0EA5E9 0%,#2563EB 100%) !important;
        color:#FFF !important; font-weight:700 !important; border:none !important;
        border-radius:8px !important; padding:8px 16px !important;
        transition:all 0.3s ease !important; box-shadow:0 0 10px rgba(14,165,233,0.3) !important; }
    .stButton > button:hover { background: linear-gradient(135deg,#0284C7 0%,#1D4ED8) !important;
        box-shadow:0 0 18px rgba(14,165,233,0.6) !important; transform:translateY(-2px); }
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background-color:#111827 !important; color:#F3F4F6 !important;
        border:1px solid #374151 !important; border-radius:8px !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="header-bar">
        <div class="brand-title">🎙️ VOICECLONE STUDIO PRO
            <span style="font-size:13px;font-weight:normal;color:#94A3B8;">| EXACT SUBTITLE-AUDIO SYNC MASTER</span>
        </div>
        <div><span style="background:rgba(16,185,129,0.2);color:#34D399;border:1px solid #10B981;
            padding:4px 12px;border-radius:20px;font-size:11px;font-weight:bold;">⚡ 100% Exact Sync Active</span></div>
    </div>
""", unsafe_allow_html=True)

# ============ កែ VOICE PROFILES ឲ្យសមស្របជាងមុន ============
VOICE_PROFILES = {
    "អ្នកសម្រាយរឿង (រៀបរាប់អន្លង់អន្លោច ពីរោះធម្មជាតិ)": ("km-KH-PisethNeural", "+0Hz", "+0%"),
    "តួប្រុស (សំឡេងប្រុសធ្ងន់ច្បាស់មានអំណាច)": ("km-KH-PisethNeural", "-3Hz", "-2%"),
    "តួស្រី (សំឡេងស្រីស្រទន់ពីរោះធម្មជាតិ)": ("km-KH-SreymomNeural", "+0Hz", "+0%"),
    "តួស្រីក្មេង (សំឡេងស្រីក្មេងរស់រវើក)": ("km-KH-SreymomNeural", "+5Hz", "+5%"),
    "តួចាស់/ព្រឹទ្ធាចារ្យ (សំឡេងបុរសចាស់ទុំស្ងប់ស្ងាត់)": ("km-KH-PisethNeural", "-5Hz", "-8%"),
    "តួអង្គរងផ្សេងៗ": ("km-KH-SreymomNeural", "+2Hz", "+0%")
}

# ============ មុខងារបកប្រែថ្មី (ប្រសើរជាងមុន) ============
def translate_to_khmer(text, context_hint=""):
    """បកប្រែជាមួយ context និង fallback ច្រើនស្រទាប់"""
    if not text or not text.strip():
        return ""
    
    clean = text.strip()
    
    # ព្យាយាម deep-translator មុន (គុណភាពខ្ពស់ជាង)
    if TRANSLATOR_AVAILABLE:
        for _ in range(3):
            try:
                translator = GoogleTranslator(source='auto', target='km')
                result = translator.translate(clean)
                if result and result.strip() and result != clean:
                    return result.strip()
            except Exception:
                time.sleep(0.5) # បន្ថែម delay បន្តិចការពារ Rate Limit
    
    # Fallback ទៅ translate library ដើម
    try:
        from translate import Translator
        for _ in range(2):
            try:
                translator = Translator(to_lang="km")
                result = translator.translate(clean)
                if result and result.strip():
                    return result.strip()
            except Exception:
                pass
    except Exception:
        pass
    
    return clean


def merge_short_segments(segments, min_duration=1.2, max_chars=200):
    """បញ្ចូល segment ខ្លីៗចូលគ្នា ដើម្បីឲ្យបកប្រែមាន context ល្អ"""
    merged = []
    buffer = None
    
    for seg in segments:
        # faster-whisper ប្រើ object មិនមែន dict ទេ
        text = seg.text.strip()
        start = seg.start
        end = seg.end
        
        if not text:
            continue
        
        if buffer is None:
            buffer = {"start": start, "end": end, "text": text}
        else:
            combined_len = len(buffer["text"]) + len(text)
            combined_dur = end - buffer["start"]
            # បញ្ចូលបើនៅជាប់គ្នា និងមិនវែងពេក
            if combined_len <= max_chars and combined_dur <= 12.0:
                buffer["end"] = end
                buffer["text"] += " " + text
            else:
                merged.append(buffer)
                buffer = {"start": start, "end": end, "text": text}
    
    if buffer is not None:
        merged.append(buffer)
    
    return merged


def detect_speaker_by_pitch(wav_file_path, start_sec, duration_sec, prev_speaker=None):
    """កំណត់តួអង្គដោយ pitch ដែលត្រឹមត្រូវជាងមុន (median + harmonics)"""
    default = "អ្នកសម្រាយរឿង (រៀបរាប់អន្លង់អន្លោច ពីរោះធម្មជាតិ)"
    try:
        rate, data = wav.read(wav_file_path)
        if len(data.shape) > 1:
            data = data[:, 0]
        data = data.astype(np.float32)
        
        start_sample = max(0, int(start_sec * rate))
        end_sample = min(len(data), int((start_sec + duration_sec) * rate))
        segment = data[start_sample:end_sample]
        
        if len(segment) < rate * 0.3:  # ខ្លីពេក
            return prev_speaker or default
        
        segment = segment - np.mean(segment)
        fft_size = min(len(segment), 2**14)
        spec = np.fft.rfft(segment[:fft_size] * np.hanning(fft_size))
        power = np.abs(spec) ** 2
        freqs = np.fft.rfftfreq(fft_size, d=1.0/rate)
        
        valid_mask = (freqs >= 70) & (freqs <= 350)
        if not np.any(valid_mask):
            return prev_speaker or default
        
        valid_power = power[valid_mask]
        valid_freqs = freqs[valid_mask]
        
        threshold = np.max(valid_power) * 0.3
        peak_indices = np.where(valid_power > threshold)[0]
        
        if len(peak_indices) > 0:
            peak_freqs = valid_freqs[peak_indices]
            dominant_freq = float(np.median(peak_freqs))
        else:
            dominant_freq = float(valid_freqs[np.argmax(valid_power)])
        
        if dominant_freq >= 200:
            detected = "តួស្រីក្មេង (សំឡេងស្រីក្មេងរស់រវើក)"
        elif dominant_freq >= 165:
            detected = "តួស្រី (សំឡេងស្រីស្រទន់ពីរោះធម្មជាតិ)"
        elif dominant_freq >= 130:
            detected = "តួប្រុស (សំឡេងប្រុសធ្ងន់ច្បាស់មានអំណាច)"
        elif dominant_freq >= 95:
            detected = "តួចាស់/ព្រឹទ្ធាចារ្យ (សំឡេងបុរសចាស់ទុំស្ងប់ស្ងាត់)"
        else:
            detected = default
        
        if prev_speaker and prev_speaker == detected:
            return detected
        return detected
    except Exception:
        return prev_speaker or default


def estimate_khmer_speech_duration(text, base_rate=13.0):
    """ប៉ាន់ស្មានរយៈពេលនិយាយខ្មែរ"""
    if not text:
        return 0.0
    khmer_chars = len(re.findall(r'[\u1780-\u17FF]', text))
    other_chars = len(text) - khmer_chars
    total = khmer_chars + (other_chars * 0.5)
    return max(0.5, total / base_rate)


# ============ UI ============
col_left, col_right = st.columns([1.1, 1.9])

with col_left:
    st.markdown('<div class="card-panel">', unsafe_allow_html=True)
    st.markdown("### 📺 Video Preview & Download Center")
    uploaded_file = st.file_uploader("Upload Long Video (Up to 2GB .MP4, .MKV, .MOV)",
                                      type=["mp4", "mkv", "mov"])
    
    if uploaded_file is not None:
        if 'rendered_video_path' in st.session_state and os.path.exists(st.session_state.rendered_video_path):
            st.markdown("🎉 **Rendered Video Result:**")
            st.video(st.session_state.rendered_video_path)
            with open(st.session_state.rendered_video_path, "rb") as file:
                st.download_button(
                    label="📥 Download វីដេអូ Ultra HD (.MP4)",
                    data=file, file_name="exact_synced_movie.mp4",
                    mime="video/mp4", use_container_width=True
                )
        else:
            st.video(uploaded_file)
        st.success(f"📁 Loaded: {uploaded_file.name} ({uploaded_file.size/(1024*1024):.2f} MB)")
    else:
        st.info("📌 Drop your video file here (Up to 2GB).")
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="card-panel">', unsafe_allow_html=True)
    st.markdown("### 🎛️ Quick Action Control Center")
    
    st.markdown("##### ⚡ Quick Action Switches:")
    act1, act2, act3, act4, act5 = st.columns(5)
    with act1: enable_blur = st.checkbox("✨ Blur", value=True, key="cb_blur")
    with act2: enable_text = st.checkbox("📝 Text", value=True, key="cb_text")
    with act3: enable_sub  = st.checkbox("🟢 Sub", value=True, key="cb_sub")
    with act4: enable_med  = st.checkbox("⚡ Med", value=True, key="cb_med")
    with act5: enable_sav  = st.checkbox("💾 Save", value=True, key="cb_sav")

    with st.expander("✂️ Video Trimmer & Timeline Cutter", expanded=False):
        tc1, tc2 = st.columns(2)
        with tc1:
            trim_start = st.number_input("Start Seconds", min_value=0.0, value=0.0, step=1.0)
        with tc2:
            trim_duration = st.number_input("Duration (0 = full)", min_value=0.0, value=0.0, step=1.0)

    with st.expander("📚 Character Voice Profiles", expanded=True):
        voice_keys = list(VOICE_PROFILES.keys())
        v1, v2 = st.columns(2)
        with v1:
            narrator_profile = st.selectbox("សំឡេងអ្នកសម្រាយរឿង", voice_keys, index=0)
            male_profile     = st.selectbox("សំឡេងតួប្រុស", voice_keys, index=1)
        with v2:
            female_profile   = st.selectbox("សំឡេងតួស្រី", voice_keys, index=2)
            elder_profile    = st.selectbox("សំឡេងតួចាស់/ព្រឹទ្ធាចារ្យ", voice_keys, index=4)
        other_profile = st.selectbox("សំឡេងតួអង្គរង", voice_keys, index=5)
        
        st.markdown("---")
        st.markdown("**🗣️ Voice Tuning:**")
        t1, t2 = st.columns(2)
        with t1:
            pitch_shift = st.slider("Pitch Shift (Hz)", -8, 8, 0, 1)
        with t2:
            rate_shift = st.slider("Speed Rate (%)", -20, 20, 0, 2)

    with st.expander("⚙️ Advanced Director Settings", expanded=False):
        burn_subtitles    = st.checkbox("🟢 Burn Subtitles on Video", value=enable_sub)
        suppress_original = st.checkbox("🟢 Mute Original Voices", value=True)
        bgm_volume        = st.slider("🎵 BGM Volume", 0.1, 1.5, 0.4, 0.1)
        voice_volume      = st.slider("🗣️ AI Voice Volume", 1.5, 4.0, 2.5, 0.1)
        anti_copy_audio   = st.checkbox("🟢 Audio Copyright Protection", value=True)

    if 'auto_subtitles' not in st.session_state:
        st.session_state.auto_subtitles = []

    tb1, tb2, tb3 = st.columns(3)
    with tb1: btn_extract = st.button("🪄 1. AI Extract & Auto Translate", use_container_width=True)
    with tb2: btn_force   = st.button("🌐 2. Force Khmer Translate All", use_container_width=True)
    with tb3: btn_clear   = st.button("🗑️ Reset Script", use_container_width=True)

    if btn_clear:
        st.session_state.auto_subtitles = []
        if 'rendered_video_path' in st.session_state:
            del st.session_state.rendered_video_path
        st.rerun()

    # ============ EXTRACT ============
    if btn_extract:
        if uploaded_file is None:
            st.warning("⚠️ Please upload a video file first!")
        elif not WHISPER_AVAILABLE:
            st.error("❌ សូមដំឡើង faster-whisper សិន៖ pip install faster-whisper")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            try:
                status_text.text("⏳ Buffering video safely in chunks...")
                progress_bar.progress(10)
                
                raw_tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                for chunk in iter(lambda: uploaded_file.read(4 * 1024 * 1024), b""):
                    raw_tfile.write(chunk)
                raw_video_path = raw_tfile.name
                raw_tfile.close()
                
                # Trim
                trimmed_video_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
                trim_cmd = ["ffmpeg", "-y", "-ss", str(trim_start)]
                if trim_duration > 0:
                    trim_cmd.extend(["-t", str(trim_duration)])
                trim_cmd.extend(["-i", raw_video_path, "-c", "copy", trimmed_video_path])
                res = subprocess.run(trim_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                input_video_path = trimmed_video_path if (res.returncode == 0 and
                    os.path.exists(trimmed_video_path) and
                    os.path.getsize(trimmed_video_path) > 1000) else raw_video_path
                
                status_text.text("⏳ Extracting audio...")
                progress_bar.progress(25)
                
                audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                wav_path   = tempfile.NamedTemporaryFile(delete=False, suffix='.wav').name
                subprocess.run(["ffmpeg", "-y", "-i", input_video_path, "-q:a", "0", "-map", "a", audio_path],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                subprocess.run(["ffmpeg", "-y", "-i", input_video_path, "-ar", "16000", "-ac", "1", wav_path],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                status_text.text("⏳ Faster-Whisper AI recognizing speech (Lighter & Faster)...")
                progress_bar.progress(50)
                
                # ប្តូរមកប្រើ faster-whisper
                # ប្រើ "small" ឬ "base" អាស្រ័យលើ RAM របស់ Server
                model = WhisperModel("small", device="cpu", compute_type="int8")
                segments, info = model.transcribe(
                    audio_path,
                    language=None, 
                    beam_size=5,
                    vad_filter=True, 
                )
                
                # faster-whisper ត្រឡប់មកវិញជា generator ត្រូវបំលែងជា list ដើម្បីអាន
                raw_segments = list(segments)
                
                status_text.text("⏳ Merging segments & translating with context...")
                progress_bar.progress(75)
                
                merged_segments = merge_short_segments(raw_segments)
                
                st.session_state.auto_subtitles = []
                prev_speaker = None
                
                for i, seg in enumerate(merged_segments):
                    start_time = round(seg["start"], 2)
                    duration   = round(seg["end"] - seg["start"], 2)
                    original   = seg["text"].strip()
                    
                    context = ""
                    if st.session_state.auto_subtitles:
                        context = st.session_state.auto_subtitles[-1]["khmer"][-80:]
                    
                    khmer_text = translate_to_khmer(original, context)
                    detected = detect_speaker_by_pitch(wav_path, start_time, duration, prev_speaker)
                    prev_speaker = detected
                    
                    st.session_state.auto_subtitles.append({
                        "time_sec": start_time,
                        "duration": duration,
                        "speaker":  detected,
                        "khmer":    khmer_text,
                        "original": original,
                    })
                    
                    progress_bar.progress(75 + int(25 * (i + 1) / len(merged_segments)))
                
                progress_bar.progress(100)
                status_text.text("✅ Extraction & Translation Complete!")
                st.success("✅ បានទាញយក បកប្រែ និងបែងចែកតួអង្គជោគជ័យ!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")

    # ============ FORCE TRANSLATE ============
    if btn_force and st.session_state.auto_subtitles:
        progress = st.progress(0)
        for idx, sub in enumerate(st.session_state.auto_subtitles):
            original = sub.get("original", "")
            if original:
                translated = translate_to_khmer(original)
                if translated:
                    st.session_state.auto_subtitles[idx]["khmer"] = translated
            progress.progress(int(100 * (idx + 1) / len(st.session_state.auto_subtitles)))
        st.success("✅ Force Translation Finished!")
        st.rerun()

    # ============ SCRIPT EDITOR ============
    if st.session_state.auto_subtitles:
        st.markdown("---")
        with st.expander(f"📝 Pro Timeline Script Editor ({len(st.session_state.auto_subtitles)} lines)", expanded=False):
            role_options = list(VOICE_PROFILES.keys())
            
            for idx, sub in enumerate(st.session_state.auto_subtitles):
                c1, c2, c3, c4 = st.columns([0.8, 0.8, 1.2, 3])
                with c1:
                    st.session_state.auto_subtitles[idx]["time_sec"] = st.number_input(
                        f"Start #{idx+1}", value=float(sub["time_sec"]), step=0.1, key=f"s_{idx}")
                with c2:
                    st.session_state.auto_subtitles[idx]["duration"] = st.number_input(
                        f"Dur #{idx+1}", value=float(sub["duration"]), step=0.1, key=f"d_{idx}")
                with c3:
                    cur_sp = sub.get("speaker", role_options[0])
                    if cur_sp not in role_options:
                        cur_sp = role_options[0]
                    st.session_state.auto_subtitles[idx]["speaker"] = st.selectbox(
                        f"Role #{idx+1}", role_options,
                        index=role_options.index(cur_sp), key=f"r_{idx}")
                with c4:
                    st.session_state.auto_subtitles[idx]["khmer"] = st.text_area(
                        f"Khmer #{idx+1}", sub["khmer"], key=f"k_{idx}", height=60)
                st.markdown("---")
        
        st.markdown("### 🚀 Export & Preview Pro Video")
        
        if st.button("🎬 Render & Preview Final Video (Exact Sync Master)", use_container_width=True):
            if uploaded_file is not None:
                progress_bar = st.progress(0)
                status_text = st.empty()
                try:
                    status_text.text("⏳ Preparing render environment...")
                    progress_bar.progress(8)
                    
                    raw_tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                    for chunk in iter(lambda: uploaded_file.read(4 * 1024 * 1024), b""):
                        raw_tfile.write(chunk)
                    raw_video_path = raw_tfile.name
                    raw_tfile.close()
                    
                    trimmed_video_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
                    trim_cmd = ["ffmpeg", "-y", "-ss", str(trim_start)]
                    if trim_duration > 0:
                        trim_cmd.extend(["-t", str(trim_duration)])
                    trim_cmd.extend(["-i", raw_video_path, "-c", "copy", trimmed_video_path])
                    res = subprocess.run(trim_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    input_video_path = trimmed_video_path if (res.returncode == 0 and
                        os.path.exists(trimmed_video_path) and
                        os.path.getsize(trimmed_video_path) > 1000) else raw_video_path
                    
                    # ===== SRT =====
                    srt_path = tempfile.NamedTemporaryFile(delete=False, suffix='.srt',
                                                          mode='w', encoding='utf-8')
                    
                    def fmt(sec):
                        h = int(sec // 3600); m = int((sec % 3600) // 60)
                        s = int(sec % 60); ms = int((sec - int(sec)) * 1000)
                        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
                    
                    srt_idx = 1
                    for sub in st.session_state.auto_subtitles:
                        txt = sub["khmer"].strip()
                        if not txt: continue
                        start = sub["time_sec"]; end = start + sub["duration"]
                        srt_path.write(f"{srt_idx}\n{fmt(start)} --> {fmt(end)}\n{txt}\n\n")
                        srt_idx += 1
                    srt_path.close()
                    
                    # ===== Voice =====
                    audio_inputs = []
                    valid_subs = []
                    
                    for i, sub in enumerate(st.session_state.auto_subtitles):
                        txt = sub["khmer"].strip()
                        if not txt: continue
                        
                        status_text.text(f"⏳ Generating voice #{i+1}/{len(st.session_state.auto_subtitles)}...")
                        line_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                        
                        role = sub.get("speaker", list(VOICE_PROFILES.keys())[0])
                        if "តួប្រុស" in role:        v_name = male_profile
                        elif "តួស្រីក្មេង" in role:   v_name = female_profile
                        elif "តួស្រី" in role:         v_name = female_profile
                        elif "តួចាស់" in role:         v_name = elder_profile
                        elif "តួអង្គរង" in role:       v_name = other_profile
                        else:                           v_name = narrator_profile
                        
                        voice, v_pitch, v_rate = VOICE_PROFILES.get(v_name,
                            ("km-KH-PisethNeural", "+0Hz", "+0%"))
                        
                        try:
                            base_pitch = int(v_pitch.replace("Hz", "").replace("+", ""))
                            new_pitch = base_pitch + pitch_shift
                            final_pitch = f"{'+' if new_pitch >= 0 else ''}{new_pitch}Hz"
                        except Exception:
                            final_pitch = v_pitch
                        try:
                            base_rate = int(v_rate.replace("%", "").replace("+", ""))
                            new_rate = base_rate + rate_shift
                            final_rate = f"{'+' if new_rate >= 0 else ''}{new_rate}%"
                        except Exception:
                            final_rate = v_rate
                        
                        edge_cmd = [
                            "edge-tts", "--text", txt,
                            "--voice", voice,
                            "--rate",  final_rate,
                            f"--pitch={final_pitch}",
                            "--write-media", line_path
                        ]
                        subprocess.run(edge_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        
                        if os.path.exists(line_path) and os.path.getsize(line_path) > 100:
                            valid_subs.append(sub)
                            audio_inputs.extend(["-i", line_path])
                    
                    if not valid_subs:
                        st.error("❌ No valid subtitles or audio generation failed.")
                        st.stop()
                    
                    progress_bar.progress(65)
                    status_text.text("⏳ Rendering video with exact sync...")
                    
                    output_video_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
                    
                    # ===== Filters =====
                    video_filters = []
                    if burn_subtitles:
                        escaped = srt_path.name.replace('\\', '/').replace(':', '\\:')
                        video_filters.append(
                            f"subtitles='{escaped}':force_style='FontName=Khmer OS Battambang,"
                            f"FontSize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
                            f"BackColour=&H80000000,BorderStyle=1,Outline=1.5,Shadow=0,Alignment=2'"
                        )
                    final_vf = ",".join(video_filters) if video_filters else None
                    
                    filter_parts = []
                    mix_inputs   = []
                    
                    orig_vol = "0.03" if suppress_original else "0.15"
                    bgm_f = f"[0:a]volume={orig_vol}[orig]; [orig]pan=stereo|c0=c0|c1=c1,volume={bgm_volume}"
                    if anti_copy_audio:
                        bgm_f += ",asetrate=44100*1.02,aresample=44100"
                    bgm_f += "[bgm]"
                    filter_parts.append(bgm_f)
                    mix_inputs.append("[bgm]")
                    
                    for idx, sub in enumerate(valid_subs):
                        delay_ms = int(sub["time_sec"] * 1000)
                        target_dur = sub["duration"]
                        est_dur = estimate_khmer_speech_duration(sub["khmer"])
                        
                        speed = 1.0
                        if target_dur > 0 and est_dur > 0:
                            ratio = est_dur / target_dur
                            if ratio > 1.15:
                                speed = min(1.4, ratio)
                            elif ratio < 0.7:
                                speed = max(0.75, ratio)
                        
                        stream_idx = idx + 1
                        if abs(speed - 1.0) > 0.05:
                            filter_parts.append(
                                f"[{stream_idx}:a]volume={voice_volume},"
                                f"atempo={speed:.2f},"
                                f"adelay={delay_ms}|{delay_ms}[a{idx}]"
                            )
                        else:
                            filter_parts.append(
                                f"[{stream_idx}:a]volume={voice_volume},"
                                f"adelay={delay_ms}|{delay_ms}[a{idx}]"
                            )
                        mix_inputs.append(f"[a{idx}]")
                    
                    total_inputs = len(valid_subs) + 1
                    mix_filter = "".join(mix_inputs) + \
                        f"amix=inputs={total_inputs}:duration=first:dropout_transition=2[aout]"
                    filter_parts.append(mix_filter)
                    
                    full_filter = ";".join(filter_parts)
                    
                    ffmpeg_cmd = ["ffmpeg", "-y", "-i", input_video_path] + audio_inputs + [
                        "-filter_complex", full_filter,
                        "-map", "0:v", "-map", "[aout]"
                    ]
                    if final_vf:
                        ffmpeg_cmd.extend(["-vf", final_vf])
                    ffmpeg_cmd.extend([
                        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                        "-c:a", "aac", "-b:a", "192k",
                        output_video_path
                    ])
                    
                    process = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
                    if process.returncode == 0 and os.path.exists(output_video_path) and os.path.getsize(output_video_path) > 0:
                        progress_bar.progress(100)
                        status_text.text("🎉 Exact Sync Render Completed!")
                        st.success("✅ Render ជោគជ័យ! សំឡេងត្រូវមាត់តួអង្គ អក្សរលោតត្រូវគ្នា Ultra HD។")
                        st.session_state.rendered_video_path = output_video_path
                        st.rerun()
                    else:
                        err = process.stderr.decode('utf-8', errors='ignore')[:600]
                        st.error(f"❌ FFmpeg failed:\n{err}")
                except Exception as e:
                    st.error(f"❌ Render Exception: {e}")
    else:
        st.info("👆 Upload a video and click **'AI Extract & Auto Translate'** to start.")
    
    st.markdown('</div>', unsafe_allow_html=True)
