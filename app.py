import streamlit as st
import os
import subprocess
import tempfile
import whisper
import numpy as np
import scipy.io.wavfile as wav
from translate import Translator

# Page Configuration with Large Upload Support
st.set_page_config(
    page_title="VoiceClone Studio Pro - Interactive Top Bar & Video Preview",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Dark Cyberpunk & Pro Styling
st.markdown("""
    <style>
    .stApp {
        background-color: #05070C !important;
        color: #E2E8F0;
        font-family: 'Khmer OS Battambang', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .header-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: linear-gradient(90deg, #0B101D 0%, #151D30 100%);
        padding: 12px 20px;
        border-radius: 12px;
        border: 1px solid #1E293B;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6);
        margin-bottom: 15px;
    }
    .brand-title {
        font-size: 20px;
        font-weight: 800;
        background: linear-gradient(135deg, #38BDF8 0%, #818CF8 50%, #C084FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .card-panel {
        background: #0D121F;
        border: 1px solid #1E293B;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        margin-bottom: 20px;
    }
    .stButton > button {
        background: linear-gradient(135deg, #0EA5E9 0%, #2563EB 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 0 10px rgba(14, 165, 233, 0.3) !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #0284C7 0%, #1D4ED8) !important;
        box-shadow: 0 0 18px rgba(14, 165, 233, 0.6) !important;
        transform: translateY(-2px);
    }
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background-color: #111827 !important;
        color: #F3F4F6 !important;
        border: 1px solid #374151 !important;
        border-radius: 8px !important;
    }
    </style>
""", unsafe_allow_html=True)

# Header Banner
st.markdown("""
    <div class="header-bar">
        <div class="brand-title">
            🎙️ VOICECLONE STUDIO PRO <span style="font-size:13px; font-weight:normal; color:#94A3B8;">| INTERACTIVE CONTROL & PREVIEW STUDIO</span>
        </div>
        <div>
            <span style="background: rgba(16, 185, 129, 0.2); color: #34D399; border: 1px solid #10B981; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: bold;">⚡ 2H+ Ultrafast Ready</span>
        </div>
    </div>
""", unsafe_allow_html=True)

VOICE_PROFILES = {
    "អ្នកសម្រាយរឿង (រៀបរាប់អន្លង់អន្លោច)": ("km-KH-PisethNeural", "+0Hz"),
    "តួប្រុស (សំឡេងប្រុសធ្ងន់ច្បាស់)": ("km-KH-PisethNeural", "-2Hz"),
    "តួស្រី (សំឡេងស្រីស្រទន់ពីរោះ)": ("km-KH-SreymomNeural", "+2Hz"),
    "តួចាស់/ព្រឹទ្ធាចារ្យ (សំឡេងបុរសចាស់ទុំ)": ("km-KH-PisethNeural", "-6Hz"),
    "តួអង្គរងផ្សេងៗ": ("km-KH-SreymomNeural", "+0Hz")
}

col_left, col_right = st.columns([1.1, 1.9])

with col_left:
    st.markdown('<div class="card-panel">', unsafe_allow_html=True)
    st.markdown("### 📺 Video Preview & Result Player")
    uploaded_file = st.file_uploader("Upload Long Video File (.MP4, .MKV, .MOV)", type=["mp4", "mkv", "mov"])
    
    if uploaded_file is not None:
        if 'rendered_video_path' in st.session_state and os.path.exists(st.session_state.rendered_video_path):
            st.markdown("🎉 **Rendered Video Result (ចាក់មើលទីនេះមុន Download):**")
            st.video(st.session_state.rendered_video_path)
        else:
            st.video(uploaded_file)
            
        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.success(f"📁 Loaded: {uploaded_file.name} ({file_size_mb:.2f} MB)")
    else:
        st.info("📌 Drop your video file here.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="card-panel">', unsafe_allow_html=True)
    st.markdown("### 🎛️ Interactive Action Bar & Studio Center")
    
    # Interactive Top Action Bar (Buttons like Blur, Text, Sub, Med, Sav)
    st.markdown("##### ⚡ Quick Action Control Bar:")
    act1, act2, act3, act4, act5 = st.columns(5)
    with act1:
        btn_blur = st.checkbox("✨ Blur", value=True, key="b_blur")
    with act2:
        btn_text = st.checkbox("📝 Text", value=True, key="b_text")
    with act3:
        btn_sub = st.checkbox("🟢 Sub", value=True, key="b_sub")
    with act4:
        btn_med = st.checkbox("⚡ Med", value=True, key="b_med")
    with act5:
        btn_sav = st.checkbox("💾 Save", value=True, key="b_sav")
    
    with st.expander("📚 Character Voice Profiles (កំណត់សំឡេងសម្រាប់ AI)", expanded=True):
        st.markdown("📌 កំណត់សំឡេង AI ឱ្យត្រូវទៅនឹងតួអង្គក្នុងរឿង៖")
        
        voice_keys = list(VOICE_PROFILES.keys())
        
        v1, v2 = st.columns(2)
        with v1:
            narrator_profile = st.selectbox("សំឡេងអ្នកសម្រាយរឿង", voice_keys, index=0)
            male_profile = st.selectbox("សំឡេងតួប្រុស", voice_keys, index=1)
        with v2:
            female_profile = st.selectbox("សំឡេងតួស្រី", voice_keys, index=2)
            elder_profile = st.selectbox("សំឡេងតួចាស់/ព្រឹទ្ធាចារ្យ", voice_keys, index=3)

        other_profile = st.selectbox("សំឡេងតួអង្គរងផ្សេងៗ", voice_keys, index=4)

    with st.expander("⚙️ Advanced Director Settings (BGM & Volume Boost)", expanded=False):
        burn_subtitles = st.checkbox("🟢 បញ្ចូលអក្សររត់ (Subtitles) លើវីដេអូផ្ទាល់", value=btn_sub)
        suppress_original = st.checkbox("🟢 បន្ថយសំឡេងដើមវីដេអូ (Mute Original Voices)", value=True)
        bgm_volume = st.slider("🎵 កម្រិតសម្លេងភ្លេងអម BGM (Volume)", min_value=0.1, max_value=1.5, value=0.4, step=0.1)
        voice_volume = st.slider("🗣️ កម្រិតសំឡេង AI និយាយ (Voice Volume - ខ្លាំងច្បាស់)", min_value=1.5, max_value=4.0, value=2.5, step=0.1)
        anti_copy_audio = st.checkbox("🟢 បើកប្រព័ន្ធការពារ Copyright សម្លេង (Audio Shift)", value=True)

    if 'auto_subtitles' not in st.session_state:
        st.session_state.auto_subtitles = []

    tb_col1, tb_col2, tb_col3 = st.columns(3)
    with tb_col1:
        btn_extract = st.button("🪄 1. AI Extract & Auto Translate", use_container_width=True)
    with tb_col2:
        btn_force = st.button("🌐 2. Force Khmer Translate All", use_container_width=True)
    with tb_col3:
        btn_clear = st.button("🗑️ Reset Script", use_container_width=True)

    if btn_clear:
        st.session_state.auto_subtitles = []
        if 'rendered_video_path' in st.session_state:
            del st.session_state.rendered_video_path
        st.rerun()

    def translate_to_khmer(text):
        if not text:
            return ""
        for _ in range(3):
            try:
                translator = Translator(to_lang="km")
                translated = translator.translate(text)
                if translated and translated.strip():
                    return translated
            except Exception:
                pass
        return text

    def analyze_audio_pitch(wav_file_path, start_sec, duration_sec):
        try:
            rate, data = wav.read(wav_file_path)
            if len(data.shape) > 1:
                data = data[:, 0]
                
            start_sample = int(start_sec * rate)
            end_sample = int((start_sec + duration_sec) * rate)
            
            segment = data[start_sample:end_sample]
            if len(segment) == 0:
                return "អ្នកសម្រាយរឿង"
                
            fft_spectrum = np.abs(np.fft.rfft(segment))
            freqs = np.fft.rfftfreq(len(segment), d=1.0/rate)
            peak_freq = freqs[np.argmax(fft_spectrum)]
            
            if peak_freq > 185:
                return "តួស្រី"
            elif 80 <= peak_freq <= 135:
                return "តួចាស់/ព្រឹទ្ធាចារ្យ"
            elif 135 < peak_freq <= 185:
                return "តួប្រុស"
            else:
                return "អ្នកសម្រាយរឿង"
        except Exception:
            return "អ្នកសម្រាយរឿង"

    if btn_extract:
        if uploaded_file is not None:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("⏳ Saving video file...")
                progress_bar.progress(15)
                
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                tfile.write(uploaded_file.read())
                input_video_path = tfile.name
                tfile.close()
                
                status_text.text("⏳ Extracting audio track...")
                progress_bar.progress(35)
                
                audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                wav_path = tempfile.NamedTemporaryFile(delete=False, suffix='.wav').name
                
                subprocess.run(["ffmpeg", "-y", "-i", input_video_path, "-q:a", "0", "-map", "a", audio_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                subprocess.run(["ffmpeg", "-y", "-i", input_video_path, "-ar", "16000", "-ac", "1", wav_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                status_text.text("⏳ Running Whisper AI Speech Recognition...")
                progress_bar.progress(60)
                
                model = whisper.load_model("base")
                result = model.transcribe(audio_path)
                
                status_text.text("⏳ Translating script to Khmer & Analyzing Roles...")
                progress_bar.progress(85)
                
                st.session_state.auto_subtitles = []
                
                for segment in result["segments"]:
                    start_time = round(segment["start"], 2)
                    duration = round(segment["end"] - segment["start"], 2)
                    original_text = segment["text"].strip()
                    
                    khmer_text = translate_to_khmer(original_text)
                    detected_role = analyze_audio_pitch(wav_path, start_time, duration)
                            
                    st.session_state.auto_subtitles.append({
                        "time_sec": start_time,
                        "duration": duration,
                        "speaker": detected_role,
                        "khmer": khmer_text
                    })
                
                progress_bar.progress(100)
                status_text.text("🎉 Extraction & Role Mapping Complete!")
                st.success("✅ បានទាញយក និងបកប្រែវីដេអូរយៈពេលវែងជាភាសាខ្មែរជោគជ័យ!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error: {e}")
        else:
            st.warning("⚠️ Please upload a video file first!")

    if btn_force and st.session_state.auto_subtitles:
        for idx, sub in enumerate(st.session_state.auto_subtitles):
            current_text = sub["khmer"].strip()
            if current_text:
                translated = translate_to_khmer(current_text)
                if translated:
                    st.session_state.auto_subtitles[idx]["khmer"] = translated
        st.success("✅ Force Translation Finished!")
        st.rerun()

    if st.session_state.auto_subtitles:
        st.markdown("---")
        st.markdown("💡 *Script Editor: កែសម្រួលអត្ថបទវែងៗតាមតម្រូវការ។*")
        
        role_options = ["អ្នកសម្រាយរឿង", "តួប្រុស", "តួស្រី", "តួចាស់/ព្រឹទ្ធាចារ្យ", "តួអង្គរងផ្សេងៗ"]
        
        for idx, sub in enumerate(st.session_state.auto_subtitles):
            c1, c2, c3, c4 = st.columns([0.8, 0.8, 1.2, 3])
            with c1:
                st.session_state.auto_subtitles[idx]["time_sec"] = st.number_input(
                    f"Start #{idx+1}", value=sub["time_sec"], step=0.1, key=f"s_{idx}"
                )
            with c2:
                st.session_state.auto_subtitles[idx]["duration"] = st.number_input(
                    f"Dur #{idx+1}", value=sub["duration"], step=0.1, key=f"d_{idx}"
                )
            with c3:
                current_speaker = sub.get("speaker", "អ្នកសម្រាយរឿង")
                if current_speaker not in role_options:
                    current_speaker = "អ្នកសម្រាយរឿង"
                st.session_state.auto_subtitles[idx]["speaker"] = st.selectbox(
                    f"Role #{idx+1}", role_options,
                    index=role_options.index(current_speaker),
                    key=f"r_{idx}"
                )
            with c4:
                st.session_state.auto_subtitles[idx]["khmer"] = st.text_area(
                    f"Khmer Script #{idx+1}", sub["khmer"], key=f"k_{idx}", height=60
                )
                
        st.markdown("---")
        st.markdown("### 🚀 Export & Preview Long Video")
        
        if st.button("🎬 Render & Preview Video (Ultrafast)", use_container_width=True):
            if uploaded_file is not None:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    status_text.text("⏳ Preparing video rendering environment...")
                    progress_bar.progress(10)
                    
                    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                    tfile.write(uploaded_file.read())
                    input_video_path = tfile.name
                    tfile.close()
                    
                    srt_path = tempfile.NamedTemporaryFile(delete=False, suffix='.srt', mode='w', encoding='utf-8')
                    for i, sub in enumerate(st.session_state.auto_subtitles):
                        clean_text = sub["khmer"].strip()
                        if not clean_text:
                            continue
                        
                        start_sec = sub["time_sec"]
                        end_sec = start_sec + sub["duration"]
                        
                        def format_time(sec):
                            hours = int(sec // 3600)
                            minutes = int((sec % 3600) // 60)
                            seconds = int(sec % 60)
                            milliseconds = int((sec - int(sec)) * 1000)
                            return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
                        
                        srt_path.write(f"{i+1}\n")
                        srt_path.write(f"{format_time(start_sec)} --> {format_time(end_sec)}\n")
                        srt_path.write(f"{clean_text}\n\n")
                    srt_path.close()
                    
                    audio_inputs = []
                    valid_subtitles = []
                    
                    for i, sub in enumerate(st.session_state.auto_subtitles):
                        clean_text = sub["khmer"].strip()
                        if not clean_text:
                            continue
                            
                        status_text.text(f"⏳ Generating AI audio line #{i+1}...")
                        line_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                        
                        role = sub.get("speaker", "អ្នកសម្រាយរឿង")
                        if role == "តួប្រុស":
                            v_name = male_profile
                        elif role == "តួស្រី":
                            v_name = female_profile
                        elif role == "តួចាស់/ព្រឹទ្ធាចារ្យ":
                            v_name = elder_profile
                        elif role == "តួអង្គរងផ្សេងៗ":
                            v_name = other_profile
                        else:
                            v_name = narrator_profile
                            
                        voice, voice_pitch = VOICE_PROFILES.get(v_name, ("km-KH-PisethNeural", "+0Hz"))
                            
                        edge_cmd = [
                            "edge-tts",
                            "--text", clean_text,
                            "--voice", voice,
                            "--rate", "+0%",
                            f"--pitch={voice_pitch}",
                            "--write-media", line_audio_path
                        ]
                        subprocess.run(edge_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        
                        if os.path.exists(line_audio_path) and os.path.getsize(line_audio_path) > 100:
                            valid_subtitles.append(sub)
                            audio_inputs.extend(["-i", line_audio_path])
                    
                    if valid_subtitles:
                        progress_bar.progress(60)
                        status_text.text("⏳ Rendering Video with Ultrafast Speed...")
                        
                        output_video_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
                        
                        filter_complex_parts = []
                        mix_inputs = []
                        
                        orig_vol = "0.03" if suppress_original else "0.15"
                        bgm_filter = f"[0:a]volume={orig_vol}[orig]; [orig]pan=stereo|c0=c0|c1=c1,volume={bgm_volume}"
                        if anti_copy_audio:
                            bgm_filter += ",asetrate=44100*1.02,aresample=44100"
                        bgm_filter += "[bgm]"
                        
                        filter_complex_parts.append(bgm_filter)
                        mix_inputs.append("[bgm]")
                        
                        for idx, sub in enumerate(valid_subtitles):
                            delay_ms = int(sub["time_sec"] * 1000)
                            target_duration = sub["duration"]
                            char_count = len(sub["khmer"])
                            estimated_audio_duration = char_count / 11.5
                            
                            speed_factor = 1.0
                            if estimated_audio_duration > target_duration and target_duration > 0:
                                speed_factor = min(round(estimated_audio_duration / target_duration, 2), 2.0)
                            
                            stream_idx = idx + 1
                            if speed_factor != 1.0:
                                filter_complex_parts.append(f"[{stream_idx}:a]volume={voice_volume},atempo={speed_factor},adelay={delay_ms}|{delay_ms}[a{idx}]")
                            else:
                                filter_complex_parts.append(f"[{stream_idx}:a]volume={voice_volume},adelay={delay_ms}|{delay_ms}[a{idx}]")
                                
                            mix_inputs.append(f"[a{idx}]")
                        
                        total_inputs = len(valid_subtitles) + 1
                        mix_filter = "".join(mix_inputs) + f"amix=inputs={total_inputs}:duration=first:dropout_transition=2[aout]"
                        filter_complex_parts.append(mix_filter)
                        
                        full_filter_str = ";".join(filter_complex_parts)
                        
                        ffmpeg_cmd = ["ffmpeg", "-y", "-i", input_video_path]
                        ffmpeg_cmd.extend(audio_inputs)
                        
                        if burn_subtitles:
                            escaped_srt_path = srt_path.name.replace('\\', '/').replace(':', '\\:')
                            video_filter = f"subtitles='{escaped_srt_path}':force_style='FontName=Khmer OS Battambang,FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=4,Alignment=2'"
                            ffmpeg_cmd.extend(["-vf", video_filter])
                            
                        ffmpeg_cmd.extend([
                            "-filter_complex", full_filter_str,
                            "-map", "0:v" if not burn_subtitles else "0:v",
                            "-map", "[aout]",
                            "-c:v", "libx264",
                            "-preset", "ultrafast",
                            "-c:a", "aac",
                            output_video_path
                        ])
                        
                        process = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        
                        if process.returncode == 0 and os.path.exists(output_video_path) and os.path.getsize(output_video_path) > 0:
                            progress_bar.progress(100)
                            status_text.text("🎉 Video Rendered Successfully!")
                            st.success("✅ បាន Render រួចរាល់! វីដេអូបានបង្ហាញនៅផ្ទាំងខាងឆ្វេង អ្នកអាចចុច Play មើលសិន រួចค่อย Download ខាងក្រោម! 👇")
                            
                            # Save to session state to display video on left panel player
                            st.session_state.rendered_video_path = output_video_path
                            
                            with open(output_video_path, "rb") as file:
                                st.download_button(
                                    label="📥 Download Final Video (.MP4)",
                                    data=file,
                                    file_name="rendered_long_movie.mp4",
                                    mime="video/mp4",
                                    use_container_width=True
                                )
                            st.rerun()
                        else:
                            st.error(f"❌ FFmpeg Render failed: {process.stderr.decode('utf-8')[:300]}")
                    else:
                        st.error("❌ No valid subtitles found or audio generation failed.")
                except Exception as e:
                    st.error(f"❌ Render Exception: {e}")
    else:
        st.info("👆 Upload a video and click **'AI Extract & Auto Translate'** to start.")
    
    st.markdown('</div>', unsafe_allow_html=True)
