import streamlit as st
import os
import subprocess
import tempfile
import whisper
import numpy as np
import scipy.io.wavfile as wav
import urllib.request
import urllib.parse
import json
import time

# Page Configuration
st.set_page_config(
    page_title="VoiceClone Studio Pro - Simple & Fast Khmer",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
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
    }
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background-color: #111827 !important;
        color: #F3F4F6 !important;
        border: 1px solid #374151 !important;
        border-radius: 8px !important;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="header-bar">
        <div class="brand-title">
            🎙️ VOICECLONE STUDIO PRO | 2-VOICE SYSTEM
        </div>
        <div>
            <span style="background: rgba(16, 185, 129, 0.2); color: #34D399; border: 1px solid #10B981; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: bold;">⚡ Fast & Clean Active</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# 2 Simple Main Voices
VOICE_PROFILES = {
    "តួប្រុស (សំឡេងធ្ងន់ច្បាស់មានអំណាច)": ("km-KH-PisethNeural", "-1Hz", "+0%"),
    "តួស្រី/អ្នកសម្រាយ (សំឡេងស្រទន់ពីរោះមានមនោសញ្ចេតនា)": ("km-KH-SreymomNeural", "+1Hz", "+0%")
}

col_left, col_right = st.columns([1.1, 1.9])

with col_left:
    st.markdown('<div class="card-panel">', unsafe_allow_html=True)
    st.markdown("### 📺 Video Preview & Download")
    uploaded_file = st.file_uploader("Upload Video File (Up to 2GB .MP4, .MKV)", type=["mp4", "mkv", "mov"])
    
    if uploaded_file is not None:
        if 'rendered_video_path' in st.session_state and os.path.exists(st.session_state.rendered_video_path):
            st.markdown("🎉 **Rendered Video Result:**")
            st.video(st.session_state.rendered_video_path)
            
            with open(st.session_state.rendered_video_path, "rb") as file:
                st.download_button(
                    label="📥 Download វីដេអូរួចរាល់ (.MP4)",
                    data=file,
                    file_name="khmer_movie_recap.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )
        else:
            st.video(uploaded_file)
            
        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.success(f"📁 Loaded: {uploaded_file.name} ({file_size_mb:.2f} MB)")
    else:
        st.info("📌 Drop your video file here.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="card-panel">', unsafe_allow_html=True)
    st.markdown("### 🎛️ Control Center (2 សម្លេងងាយស្រួល)")
    
    with st.expander("🎙️ កំណត់សំឡេងหลัก (2 Choices)", expanded=True):
        voice_keys = list(VOICE_PROFILES.keys())
        default_voice = st.selectbox("សំឡេងនិយាយលំនាំដើម (Default Voice)", voice_keys, index=1)

    with st.expander("⚙️ Advanced Settings", expanded=False):
        burn_subtitles = st.checkbox("🟢 បញ្ចូលអក្សររត់ (Subtitles) លើវីដេអូ", value=True)
        suppress_original = st.checkbox("🟢 បន្ថយសំឡេងដើមវីដេអូ", value=True)
        bgm_volume = st.slider("🎵 កម្រិតភ្លេង BGM", min_value=0.1, max_value=1.5, value=0.3, step=0.1)
        voice_volume = st.slider("🗣️ កម្រិតសំឡេង AI និយាយ", min_value=1.5, max_value=4.0, value=2.5, step=0.1)

    if 'auto_subtitles' not in st.session_state:
        st.session_state.auto_subtitles = []

    tb_col1, tb_col2 = st.columns(2)
    with tb_col1:
        btn_extract = st.button("🪄 1. AI Extract & Translate to Khmer", use_container_width=True)
    with tb_col2:
        btn_clear = st.button("🗑️ Reset Script", use_container_width=True)

    if btn_clear:
        st.session_state.auto_subtitles = []
        if 'rendered_video_path' in st.session_state:
            del st.session_state.rendered_video_path
        st.rerun()

    # Fast & Stable Khmer Translation
    def translate_to_khmer(text):
        if not text:
            return ""
        for _ in range(3):
            try:
                url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=km&dt=t&q={urllib.parse.quote(text)}"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    res_data = json.loads(response.read().decode('utf-8'))
                    translated_text = "".join([item[0] for item in res_data[0] if item[0]])
                    if translated_text.strip():
                        time.sleep(0.1)
                        return translated_text
            except Exception:
                time.sleep(0.3)
        return text

    if btn_extract:
        if uploaded_file is not None:
            progress_bar = st.progress(0)
            status_text = st.empty()
            try:
                status_text.text("⏳ Buffering video file...")
                progress_bar.progress(15)
                raw_tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                for chunk in iter(lambda: uploaded_file.read(4 * 1024 * 1024), b""):
                    raw_tfile.write(chunk)
                input_video_path = raw_tfile.name
                raw_tfile.close()

                audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                subprocess.run(["ffmpeg", "-y", "-i", input_video_path, "-q:a", "0", "-map", "a", audio_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                status_text.text("⏳ Whisper AI Transcribing...")
                progress_bar.progress(50)
                model = whisper.load_model("base")
                result = model.transcribe(audio_path)

                status_text.text("⏳ Translating to Khmer...")
                progress_bar.progress(80)
                st.session_state.auto_subtitles = []
                total_seg = len(result["segments"])
                
                for idx, segment in enumerate(result["segments"]):
                    start_time = round(segment["start"], 2)
                    duration = round(segment["end"] - segment["start"], 2)
                    original_text = segment["text"].strip()
                    khmer_text = translate_to_khmer(original_text)
                    
                    st.session_state.auto_subtitles.append({
                        "time_sec": start_time,
                        "duration": duration,
                        "speaker": default_voice,
                        "khmer": khmer_text
                    })
                    status_text.text(f"⏳ Translating {idx+1}/{total_seg}...")
                
                progress_bar.progress(100)
                status_text.text("✅ Complete!")
                st.success("✅ បានទាញយក និងបកប្រែជាភាសាខ្មែរជោគជ័យ!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")
        else:
            st.warning("⚠️ Please upload a video file first!")

    if st.session_state.auto_subtitles:
        st.markdown("---")
        with st.expander(f"📝 Script Editor ({len(st.session_state.auto_subtitles)} lines)", expanded=False):
            role_options = list(VOICE_PROFILES.keys())
            for idx, sub in enumerate(st.session_state.auto_subtitles):
                c1, c2, c3 = st.columns([1, 1, 3])
                with c1:
                    st.session_state.auto_subtitles[idx]["time_sec"] = st.number_input(f"Start #{idx+1}", value=sub["time_sec"], step=0.1, key=f"s_{idx}")
                with c2:
                    st.session_state.auto_subtitles[idx]["speaker"] = st.selectbox(f"Voice #{idx+1}", role_options, index=role_options.index(sub.get("speaker", default_voice)), key=f"r_{idx}")
                with c3:
                    st.session_state.auto_subtitles[idx]["khmer"] = st.text_area(f"Khmer #{idx+1}", sub["khmer"], key=f"k_{idx}", height=50)

        if st.button("🎬 Render Final Video (Fast & Synced)", use_container_width=True):
            if uploaded_file is not None:
                progress_bar = st.progress(0)
                status_text = st.empty()
                try:
                    status_text.text("⏳ Rendering Video...")
                    progress_bar.progress(30)
                    raw_tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                    for chunk in iter(lambda: uploaded_file.read(4 * 1024 * 1024), b""):
                        raw_tfile.write(chunk)
                    input_video_path = raw_tfile.name
                    raw_tfile.close()

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
                            ms = int((sec - int(sec)) * 1000)
                            return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"
                        srt_path.write(f"{i+1}\n{format_time(start_sec)} --> {format_time(end_sec)}\n{clean_text}\n\n")
                    srt_path.close()

                    audio_inputs = []
                    valid_subtitles = []
                    for i, sub in enumerate(st.session_state.auto_subtitles):
                        clean_text = sub["khmer"].strip()
                        if not clean_text:
                            continue
                        line_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                        role = sub.get("speaker", default_voice)
                        voice, voice_pitch, voice_rate = VOICE_PROFILES.get(role, ("km-KH-SreymomNeural", "+0Hz", "+0%"))
                        
                        edge_cmd = ["edge-tts", "--text", clean_text, "--voice", voice, "--rate", voice_rate, f"--pitch={voice_pitch}", "--write-media", line_audio_path]
                        subprocess.run(edge_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        if os.path.exists(line_audio_path) and os.path.getsize(line_audio_path) > 100:
                            valid_subtitles.append(sub)
                            audio_inputs.extend(["-i", line_audio_path])

                    if valid_subtitles:
                        output_video_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
                        escaped_srt_path = srt_path.name.replace('\\', '/').replace(':', '\\:')
                        vf_str = f"subtitles='{escaped_srt_path}':force_style='FontName=Sans,FontSize=18,PrimaryColour=&H00FFFFFF,BorderStyle=1,Outline=1.5,Alignment=2'" if burn_subtitles else None

                        filter_complex_parts = [f"[0:a]volume=0.03[orig]; [orig]pan=stereo|c0=c0|c1=c1,volume={bgm_volume}[bgm]"]
                        mix_inputs = ["[bgm]"]

                        for idx, sub in enumerate(valid_subtitles):
                            delay_ms = int(sub["time_sec"] * 1000)
                            target_duration = sub["duration"]
                            char_count = len(sub["khmer"])
                            est_duration = char_count / 10.0
                            speed_factor = 1.0
                            if est_duration > target_duration and target_duration > 0:
                                speed_factor = min(round(est_duration / target_duration, 2), 2.2)
                            stream_idx = idx + 1
                            if speed_factor != 1.0:
                                filter_complex_parts.append(f"[{stream_idx}:a]volume={voice_volume},atempo={speed_factor},adelay={delay_ms}|{delay_ms}[a{idx}]")
                            else:
                                filter_complex_parts.append(f"[{stream_idx}:a]volume={voice_volume},adelay={delay_ms}|{delay_ms}[a{idx}]")
                            mix_inputs.append(f"[a{idx}]")

                        mix_filter = "".join(mix_inputs) + f"amix=inputs={len(valid_subtitles)+1}:duration=first[aout]"
                        filter_complex_parts.append(mix_filter)

                        ffmpeg_cmd = ["ffmpeg", "-y", "-i", input_video_path] + audio_inputs + [
                            "-filter_complex", ";".join(filter_complex_parts),
                            "-map", "0:v", "-map", "[aout]"
                        ]
                        if vf_str:
                            ffmpeg_cmd.extend(["-vf", vf_str])
                        ffmpeg_cmd.extend(["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "aac", "-b:a", "192k", output_video_path])
                        
                        process = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        if process.returncode == 0 and os.path.exists(output_video_path):
                            progress_bar.progress(100)
                            st.success("✅ Render រួចរាល់ដោយជោគជ័យ!")
                            st.session_state.rendered_video_path = output_video_path
                            st.rerun()
                except Exception as e:
                    st.error(f"❌ Exception: {e}")
    else:
        st.info("👆 Upload a video and click **'AI Extract & Translate to Khmer'**.")
    
    st.markdown('</div>', unsafe_allow_html=True)
