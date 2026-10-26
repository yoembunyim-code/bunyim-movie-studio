import streamlit as st
import os
import subprocess
import tempfile
import numpy as np
import scipy.io.wavfile as wav
import re
import time

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    st.error("⚠️ សូមដំឡើង `faster-whisper` ជាមុនសិន៖ `pip install faster-whisper`")

# ប្រើ deep-translator ដែលមានស្ថិរភាពជាង
try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False
    st.error("⚠️ សូមដំឡើង `deep-translator` ជាមុនសិន៖ `pip install deep-translator`")

st.set_page_config(
    page_title="Khmer Voice & Subtitle Master",
    page_icon="🎙️", layout="wide", initial_sidebar_state="expanded"
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
        <div class="brand-title">🎙️ KHMER VOICE & SUBTITLE MASTER
            <span style="font-size:13px;font-weight:normal;color:#94A3B8;">| UNLIMITED TRANSLATION PRO</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# ============ កំណត់សំឡេងឱ្យត្រូវនឹងតួអង្គ ============
VOICE_PROFILES = {
    "អ្នកសម្រាយរឿង (Narrator)": ("km-KH-PisethNeural", "+0Hz", "+0%"),
    "តួប្រុស (Male)": ("km-KH-PisethNeural", "-2Hz", "-5%"),
    "តួស្រី (Female)": ("km-KH-SreymomNeural", "+0Hz", "+0%"),
    "តួស្រីក្មេង (Young Female)": ("km-KH-SreymomNeural", "+8Hz", "+5%"),
    "តួចាស់ (Elder)": ("km-KH-PisethNeural", "-5Hz", "-10%"),
    "តួអង្គរង (Other)": ("km-KH-SreymomNeural", "+2Hz", "+0%")
}

# ============ មុខងារបកប្រែ (ប្រើ deep-translator + retry logic) ============
def translate_to_khmer(text):
    if not text or not text.strip():
        return ""
    clean = text.strip()
    
    if not TRANSLATOR_AVAILABLE:
        return clean

    # ព្យាយាមបកប្រែរហូតដល់ 5 ដង ដើម្បីកាត់បន្ថយបញ្ហា Rate Limit ឬ Server រវល់
    for attempt in range(5):
        try:
            translator = GoogleTranslator(source='auto', target='km')
            result = translator.translate(clean)
            if result and result.strip() and result.strip() != clean:
                return result.strip()
        except Exception:
            time.sleep(1.5) # រង់ចាំបន្តិចមុននឹងព្យាយាមម្តងទៀត
            
    return clean # ប្រសិនបើបរាជ័យទាំងអស់ ទើបយកអត្ថបទដើម

# ============ មុខងារបំញ្ចូល Segment ខ្លីៗ ============
def merge_short_segments(segments, max_chars=200):
    merged = []
    buffer = None
    for seg in segments:
        text = seg.text.strip()
        if not text: continue
        
        if buffer is None:
            buffer = {"start": seg.start, "end": seg.end, "text": text}
        else:
            combined_len = len(buffer["text"]) + len(text)
            combined_dur = seg.end - buffer["start"]
            if combined_len <= max_chars and combined_dur <= 12.0:
                buffer["end"] = seg.end
                buffer["text"] += " " + text
            else:
                merged.append(buffer)
                buffer = {"start": seg.start, "end": seg.end, "text": text}
    if buffer is not None:
        merged.append(buffer)
    return merged

# ============ មុខងារវិភាគសំឡេងដើម្បីរកតួអង្គ (Pitch Detection) ============
def detect_speaker_by_pitch(wav_file_path, start_sec, duration_sec, prev_speaker=None):
    default = "អ្នកសម្រាយរឿង (Narrator)"
    try:
        rate, data = wav.read(wav_file_path)
        if len(data.shape) > 1: data = data[:, 0]
        data = data.astype(np.float32)
        
        start_sample = max(0, int(start_sec * rate))
        end_sample = min(len(data), int((start_sec + duration_sec) * rate))
        segment = data[start_sample:end_sample]
        
        if len(segment) < rate * 0.3: return prev_speaker or default
        
        segment = segment - np.mean(segment)
        fft_size = min(len(segment), 2**14)
        spec = np.fft.rfft(segment[:fft_size] * np.hanning(fft_size))
        power = np.abs(spec) ** 2
        freqs = np.fft.rfftfreq(fft_size, d=1.0/rate)
        
        valid_mask = (freqs >= 70) & (freqs <= 350)
        if not np.any(valid_mask): return prev_speaker or default
        
        valid_power = power[valid_mask]
        valid_freqs = freqs[valid_mask]
        
        threshold = np.max(valid_power) * 0.3
        peak_indices = np.where(valid_power > threshold)[0]
        
        if len(peak_indices) > 0:
            dominant_freq = float(np.median(valid_freqs[peak_indices]))
        else:
            dominant_freq = float(valid_freqs[np.argmax(valid_power)])
        
        if dominant_freq >= 200: detected = "តួស្រីក្មេង (Young Female)"
        elif dominant_freq >= 165: detected = "តួស្រី (Female)"
        elif dominant_freq >= 130: detected = "តួប្រុស (Male)"
        elif dominant_freq >= 95: detected = "តួចាស់ (Elder)"
        else: detected = default
        return detected
    except Exception:
        return prev_speaker or default

# ============ ប្រវែងសំឡេងខ្មែរ (ដើម្បីឲ្យ Sync ត្រូវ) ============
def estimate_khmer_speech_duration(text, base_rate=13.0):
    if not text: return 0.0
    khmer_chars = len(re.findall(r'[\u1780-\u17FF]', text))
    other_chars = len(text) - khmer_chars
    total = khmer_chars + (other_chars * 0.5)
    return max(0.5, total / base_rate)


# ============ UI ចាប់ផ្តើម ============
col_left, col_right = st.columns([1.1, 1.9])

with col_left:
    st.markdown('<div class="card-panel">', unsafe_allow_html=True)
    st.markdown("### 📺 Video Preview & Download")
    uploaded_file = st.file_uploader("Upload Video", type=["mp4", "mkv", "mov"])
    
    if uploaded_file is not None:
        if 'rendered_video_path' in st.session_state and os.path.exists(st.session_state.rendered_video_path):
            st.markdown("🎉 **Rendered Video Result:**")
            st.video(st.session_state.rendered_video_path)
            with open(st.session_state.rendered_video_path, "rb") as file:
                st.download_button("📥 Download វីដេអូ", data=file, file_name="khmer_synced.mp4", mime="video/mp4", use_container_width=True)
        else:
            st.video(uploaded_file)
        st.success(f"📁 Loaded: {uploaded_file.name}")
    else:
        st.info("📌 Drop your video file here.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="card-panel">', unsafe_allow_html=True)
    st.markdown("### 🎛️ Control Center")
    
    with st.expander("📚 Character Voice Profiles", expanded=True):
        voice_keys = list(VOICE_PROFILES.keys())
        v1, v2 = st.columns(2)
        with v1:
            narrator_profile = st.selectbox("សំឡេងអ្នកសម្រាយ", voice_keys, index=0)
            male_profile     = st.selectbox("សំឡេងតួប្រុស", voice_keys, index=1)
        with v2:
            female_profile   = st.selectbox("សំឡេងតួស្រី", voice_keys, index=2)
            elder_profile    = st.selectbox("សំឡេងតួចាស់", voice_keys, index=4)

    with st.expander("⚙️ Settings", expanded=True):
        burn_subtitles = st.checkbox("🟢 បញ្ចូលអក្សររត់", value=True)
        voice_volume   = st.slider("🗣️ កម្រិតសំឡេង AI", 1.5, 4.0, 2.5, 0.1)

    if 'auto_subtitles' not in st.session_state:
        st.session_state.auto_subtitles = []

    if st.button("🪄 1. Extract & Translate", use_container_width=True):
        if uploaded_file is None:
            st.warning("⚠️ Please upload a video first!")
        elif not WHISPER_AVAILABLE or not TRANSLATOR_AVAILABLE:
            st.error("❌ សូមដំឡើងបណ្ណាល័យដែលខ្វះខាតសិន។")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            try:
                status_text.text("⏳ កំពុងរៀបចំវីដេអូ...")
                progress_bar.progress(10)
                
                raw_tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                for chunk in iter(lambda: uploaded_file.read(4 * 1024 * 1024), b""):
                    raw_tfile.write(chunk)
                raw_video_path = raw_tfile.name
                raw_tfile.close()
                
                status_text.text("⏳ កំពុងទាញយកសំឡេង...")
                progress_bar.progress(25)
                audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                wav_path   = tempfile.NamedTemporaryFile(delete=False, suffix='.wav').name
                subprocess.run(["ffmpeg", "-y", "-i", raw_video_path, "-q:a", "0", "-map", "a", audio_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                subprocess.run(["ffmpeg", "-y", "-i", raw_video_path, "-ar", "16000", "-ac", "1", wav_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                status_text.text("⏳ AI កំពុងស្តាប់សំឡេង...")
                progress_bar.progress(50)
                
                model = WhisperModel("small", device="cpu", compute_type="int8")
                segments, info = model.transcribe(audio_path, language=None, beam_size=5, vad_filter=True)
                raw_segments = list(segments)
                
                status_text.text("⏳ កំពុងបកប្រែជាភាសាខ្មែរ...")
                progress_bar.progress(75)
                
                merged_segments = merge_short_segments(raw_segments)
                st.session_state.auto_subtitles = []
                prev_speaker = None
                
                for i, seg in enumerate(merged_segments):
                    start_time = round(seg["start"], 2)
                    duration   = round(seg["end"] - seg["start"], 2)
                    original   = seg["text"].strip()
                    
                    khmer_text = translate_to_khmer(original)
                    
                    detected = detect_speaker_by_pitch(wav_path, start_time, duration, prev_speaker)
                    prev_speaker = detected
                    
                    st.session_state.auto_subtitles.append({
                        "time_sec": start_time, "duration": duration, "speaker": detected,
                        "khmer": khmer_text, "original": original,
                    })
                    progress_bar.progress(75 + int(25 * (i + 1) / len(merged_segments)))
                
                progress_bar.progress(100)
                status_text.text("✅ បកប្រែរួចរាល់!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")

    # ============ SCRIPT EDITOR & RENDER ============
    if st.session_state.auto_subtitles:
        st.markdown("---")
        with st.expander(f"📝 កែសម្រួលអត្ថបទ ({len(st.session_state.auto_subtitles)} បន្ទាត់)", expanded=False):
            role_options = list(VOICE_PROFILES.keys())
            for idx, sub in enumerate(st.session_state.auto_subtitles):
                c1, c2, c3, c4 = st.columns([0.8, 0.8, 1.2, 3])
                with c1: st.session_state.auto_subtitles[idx]["time_sec"] = st.number_input(f"Start #{idx+1}", value=float(sub["time_sec"]), step=0.1, key=f"s_{idx}")
                with c2: st.session_state.auto_subtitles[idx]["duration"] = st.number_input(f"Dur #{idx+1}", value=float(sub["duration"]), step=0.1, key=f"d_{idx}")
                with c3:
                    cur_sp = sub.get("speaker", role_options[0])
                    if cur_sp not in role_options: cur_sp = role_options[0]
                    st.session_state.auto_subtitles[idx]["speaker"] = st.selectbox(f"Role #{idx+1}", role_options, index=role_options.index(cur_sp), key=f"r_{idx}")
                with c4: st.session_state.auto_subtitles[idx]["khmer"] = st.text_area(f"Khmer #{idx+1}", sub["khmer"], key=f"k_{idx}", height=60)
                st.markdown("---")
        
        if st.button("🎬 Render & Preview Final Video", use_container_width=True):
            if uploaded_file is not None:
                progress_bar = st.progress(0)
                status_text = st.empty()
                try:
                    status_text.text("⏳ កំពុងរៀបចំ...")
                    progress_bar.progress(8)
                    
                    raw_tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                    for chunk in iter(lambda: uploaded_file.read(4 * 1024 * 1024), b""): raw_tfile.write(chunk)
                    raw_video_path = raw_tfile.name
                    raw_tfile.close()
                    
                    srt_path = tempfile.NamedTemporaryFile(delete=False, suffix='.srt', mode='w', encoding='utf-8')
                    def fmt(sec):
                        h = int(sec // 3600); m = int((sec % 3600) // 60); s = int(sec % 60); ms = int((sec - int(sec)) * 1000)
                        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
                    
                    srt_idx = 1
                    for sub in st.session_state.auto_subtitles:
                        txt = sub["khmer"].strip()
                        if not txt: continue
                        start = sub["time_sec"]; end = start + sub["duration"]
                        srt_path.write(f"{srt_idx}\n{fmt(start)} --> {fmt(end)}\n{txt}\n\n")
                        srt_idx += 1
                    srt_path.close()
                    
                    audio_inputs = []
                    valid_subs = []
                    
                    for i, sub in enumerate(st.session_state.auto_subtitles):
                        txt = sub["khmer"].strip()
                        if not txt: continue
                        status_text.text(f"⏳ កំពុងបង្កើតសំឡេង #{i+1}/{len(st.session_state.auto_subtitles)}...")
                        line_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                        
                        role = sub.get("speaker", list(VOICE_PROFILES.keys())[0])
                        if "តួប្រុស" in role: v_name = male_profile
                        elif "តួស្រីក្មេង" in role: v_name = female_profile
                        elif "តួស្រី" in role: v_name = female_profile
                        elif "តួចាស់" in role: v_name = elder_profile
                        else: v_name = narrator_profile
                        
                        voice, v_pitch, v_rate = VOICE_PROFILES.get(v_name, ("km-KH-PisethNeural", "+0Hz", "+0%"))
                        
                        edge_cmd = ["edge-tts", "--text", txt, "--voice", voice, "--rate", v_rate, f"--pitch={v_pitch}", "--write-media", line_path]
                        subprocess.run(edge_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        
                        if os.path.exists(line_path) and os.path.getsize(line_path) > 100:
                            valid_subs.append(sub)
                            audio_inputs.extend(["-i", line_path])
                    
                    if not valid_subs:
                        st.error("❌ មិនអាចបង្កើតសំឡេងបានទេ។")
                        st.stop()
                    
                    progress_bar.progress(65)
                    status_text.text("⏳ កំពុង Render វីដេអូ...")
                    output_video_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
                    
                    video_filters = []
                    if burn_subtitles:
                        escaped = srt_path.name.replace('\\', '/').replace(':', '\\:')
                        video_filters.append(f"subtitles='{escaped}':force_style='FontName=Khmer OS Battambang,FontSize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=1,Outline=1.5,Shadow=0,Alignment=2'")
                    final_vf = ",".join(video_filters) if video_filters else None
                    
                    filter_parts = []
                    mix_inputs   = []
                    
                    bgm_f = f"[0:a]volume=0.05[bgm]"
                    filter_parts.append(bgm_f)
                    mix_inputs.append("[bgm]")
                    
                    for idx, sub in enumerate(valid_subs):
                        delay_ms = int(sub["time_sec"] * 1000)
                        target_dur = sub["duration"]
                        est_dur = estimate_khmer_speech_duration(sub["khmer"])
                        
                        speed = 1.0
                        if target_dur > 0 and est_dur > 0:
                            ratio = est_dur / target_dur
                            if ratio > 1.15: speed = min(1.3, ratio)
                            elif ratio < 0.7: speed = max(0.8, ratio)
                        
                        stream_idx = idx + 1
                        if abs(speed - 1.0) > 0.05:
                            filter_parts.append(f"[{stream_idx}:a]volume={voice_volume},atempo={speed:.2f},adelay={delay_ms}|{delay_ms}[a{idx}]")
                        else:
                            filter_parts.append(f"[{stream_idx}:a]volume={voice_volume},adelay={delay_ms}|{delay_ms}[a{idx}]")
                        mix_inputs.append(f"[a{idx}]")
                    
                    total_inputs = len(valid_subs) + 1
                    mix_filter = "".join(mix_inputs) + f"amix=inputs={total_inputs}:duration=first:dropout_transition=2[aout]"
                    filter_parts.append(mix_filter)
                    
                    full_filter = ";".join(filter_parts)
                    
                    ffmpeg_cmd = ["ffmpeg", "-y", "-i", raw_video_path] + audio_inputs + ["-filter_complex", full_filter, "-map", "0:v", "-map", "[aout]"]
                    if final_vf: ffmpeg_cmd.extend(["-vf", final_vf])
                    ffmpeg_cmd.extend(["-c:v", "libx264", "-preset", "fast", "-crf", "22", "-c:a", "aac", "-b:a", "192k", output_video_path])
                    
                    process = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
                    if process.returncode == 0 and os.path.exists(output_video_path) and os.path.getsize(output_video_path) > 0:
                        progress_bar.progress(100)
                        status_text.text("🎉 រួចរាល់!")
                        st.session_state.rendered_video_path = output_video_path
                        st.rerun()
                    else:
                        err = process.stderr.decode('utf-8', errors='ignore')[:600]
                        st.error(f"❌ FFmpeg failed:\n{err}")
                except Exception as e:
                    st.error(f"❌ Render Exception: {e}")
    else:
        st.info("👆 Upload a video and click **'Extract & Translate'** to start.")
    
    st.markdown('</div>', unsafe_allow_html=True)
