import streamlit as st
import os
import subprocess
import tempfile
import requests
import whisper
from translate import Translator

# Page Configuration with Large Upload Support
st.set_page_config(
    page_title="VoiceClone Studio Pro - Multi-Voice Cards Studio",
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
        margin-bottom: 20px;
    }
    .brand-title {
        font-size: 22px;
        font-weight: 800;
        background: linear-gradient(135deg, #38BDF8 0%, #818CF8 50%, #C084FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .badge-container { display: flex; gap: 10px; }
    .badge-vip {
        background: rgba(225, 29, 72, 0.2);
        color: #FB7185;
        border: 1px solid #F43F5E;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
    }
    .badge-ready {
        background: rgba(16, 185, 129, 0.2);
        color: #34D399;
        border: 1px solid #10B981;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
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
            🎙️ VOICECLONE STUDIO PRO <span style="font-size:14px; font-weight:normal; color:#94A3B8;">| MULTI-VOICE CARDS & BGM STUDIO</span>
        </div>
        <div class="badge-container">
            <span class="badge-vip">❤️ Pro Voice Library</span>
            <span class="badge-ready">🟢 1GB Video Support Active</span>
        </div>
    </div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([1.1, 1.9])

with col_left:
    st.markdown('<div class="card-panel">', unsafe_allow_html=True)
    st.markdown("### 📺 Video Preview (Up to 1GB)")
    uploaded_file = st.file_uploader("Upload Video File (.MP4, .MKV, .MOV)", type=["mp4", "mkv", "mov"])
    
    if uploaded_file is not None:
        st.video(uploaded_file)
        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.success(f"📁 Loaded: {uploaded_file.name} ({file_size_mb:.2f} MB)")
    else:
        st.info("📌 Drop your video file here to extract and auto dub.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="card-panel">', unsafe_allow_html=True)
    st.markdown("### 🎛️ Voice Library & Studio Control Center")
    
    # Visual Voice Library Cards Section (Similar to VoiceClone Studio Pro interface)
    with st.expander("📚 Voice Library Cards (ជ្រើសរើសសំឡេងតួអង្គជាកាត)", expanded=True):
        st.markdown("📌 ជ្រើសរើសម៉ូដសំឡេង AI សម្រាប់តួអង្គក្នុងរឿងរបស់អ្នក៖")
        
        vc1, vc2, vc3 = st.columns(3)
        with vc1:
            st.info("🎙️ **អ្នកសម្រាយរឿង**\n\n- សំឡេង៖ ក្រាស់ច្បាស់\n- ស្ទីល៖ អន្លង់អន្លោច")
            narrator_profile = st.selectbox("เลือก Narrator", ["Piseth Pro (ប្រុស)", "Sreymom Pro (ស្រី)"], key="n_pro")
        with vc2:
            st.info("🎬 **តួប្រុសក្នុងរឿង**\n\n- សំឡេង៖ ធ្ងន់អង់អាច\n- ស្ទីល៖ ធម្មជាតិ")
            male_profile = st.selectbox("เลือก Male", ["Piseth Pro (ប្រុស)", "Sreymom Pro (ស្រី)"], key="m_pro")
        with vc3:
            st.info("🌸 **តួស្រីក្នុងរឿង**\n\n- សំឡេង៖ ស្រទន់ពីរោះ\n- ស្ទីល៖ រណ្ដំចិត្ត")
            female_profile = st.selectbox("เลือก Female", ["Sreymom Pro (ស្រី)", "Piseth Pro (ប្រុស)"], key="f_pro")

    with st.expander("⚙️ Advanced Director Settings (BGM & Subtitle)", expanded=False):
        burn_subtitles = st.checkbox("🟢 បញ្ចូលអក្សររត់ (Subtitles) លើវីដេអូផ្ទាល់", value=True)
        bgm_volume = st.slider("🎵 កម្រិតសម្លេងភ្លេងអម (BGM Volume)", min_value=0.1, max_value=1.0, value=0.4, step=0.1)
        anti_copy_audio = st.checkbox("🟢 បើកប្រព័ន្ធការពារ Copyright សម្លេង (Audio Shift)", value=True)

    if 'auto_subtitles' not in st.session_state:
        st.session_state.auto_subtitles = []

    tb_col1, tb_col2, tb_col3 = st.columns(3)
    with tb_col1:
        btn_extract = st.button("🪄 1. Extract & Auto Translate", use_container_width=True)
    with tb_col2:
        btn_force = st.button("🌐 2. Force Khmer Translate", use_container_width=True)
    with tb_col3:
        btn_clear = st.button("🗑️ Reset Script", use_container_width=True)

    if btn_clear:
        st.session_state.auto_subtitles = []
        st.rerun()

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
                
                status_text.text("⏳ Extracting audio track via FFmpeg...")
                progress_bar.progress(35)
                
                audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                extract_cmd = ["ffmpeg", "-y", "-i", input_video_path, "-q:a", "0", "-map", "a", audio_path]
                subprocess.run(extract_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                status_text.text("⏳ Running Whisper AI speech recognition...")
                progress_bar.progress(60)
                
                model = whisper.load_model("base")
                result = model.transcribe(audio_path)
                
                status_text.text("⏳ Translating text to Khmer...")
                progress_bar.progress(85)
                
                translator = Translator(to_lang="km")
                st.session_state.auto_subtitles = []
                
                for segment in result["segments"]:
                    start_time = round(segment["start"], 2)
                    duration = round(segment["end"] - segment["start"], 2)
                    original_text = segment["text"].strip()
                    
                    khmer_text = original_text
                    if original_text:
                        try:
                            translated = translator.translate(original_text)
                            if translated:
                                khmer_text = translated
                        except Exception:
                            pass
                            
                    st.session_state.auto_subtitles.append({
                        "time_sec": start_time,
                        "duration": duration,
                        "speaker": "សម្រាយរឿង",
                        "khmer": khmer_text
                    })
                
                progress_bar.progress(100)
                status_text.text("🎉 Script extracted successfully!")
                st.success("✅ Extracted & Translated into Khmer!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error: {e}")
        else:
            st.warning("⚠️ Please upload a video file first!")

    if btn_force and st.session_state.auto_subtitles:
        translator = Translator(to_lang="km")
        for idx, sub in enumerate(st.session_state.auto_subtitles):
            current_text = sub["khmer"].strip()
            if current_text:
                try:
                    translated = translator.translate(current_text)
                    if translated:
                        st.session_state.auto_subtitles[idx]["khmer"] = translated
                except Exception:
                    pass
        st.success("✅ Force Translation Finished!")
        st.rerun()

    # Subtitles Editor Grid
    if st.session_state.auto_subtitles:
        st.markdown("---")
        st.markdown("💡 *Script Editor: កែសម្រួលអត្ថបទ ថិរវេលា និងជ្រើសរើសតួអង្គឱ្យបានត្រឹមត្រូវ។*")
        
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
                st.session_state.auto_subtitles[idx]["speaker"] = st.selectbox(
                    f"Role #{idx+1}", ["សម្រាយរឿង", "តួប្រុស", "តួស្រី"],
                    index=["សម្រាយរឿង", "តួប្រុស", "តួស្រី"].index(sub["speaker"]) if sub["speaker"] in ["សម្រាយរឿង", "តួប្រុស", "តួស្រី"] else 0,
                    key=f"r_{idx}"
                )
            with c4:
                st.session_state.auto_subtitles[idx]["khmer"] = st.text_area(
                    f"Khmer Script #{idx+1}", sub["khmer"], key=f"k_{idx}", height=60
                )
                
        st.markdown("---")
        st.markdown("### 🚀 Export Pro Dubbed Video (BGM + Multi-Voices + Subtitles)")
        
        if st.button("🎬 Render Final Pro Video", use_container_width=True):
            if uploaded_file is not None:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    status_text.text("⏳ Preparing rendering environment...")
                    progress_bar.progress(10)
                    
                    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                    tfile.write(uploaded_file.read())
                    input_video_path = tfile.name
                    tfile.close()
                    
                    # Create SRT Subtitle File
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
                        if not clean_text or clean_text in ["。", ".", "ฯ", "?", "!"]:
                            continue
                            
                        status_text.text(f"⏳ Generating audio line #{i+1}...")
                        line_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                        
                        # Map selected voice profile
                        if sub["speaker"] == "តួប្រុស":
                            voice = "km-KH-PisethNeural" if "Piseth" in male_profile else "km-KH-SreymomNeural"
                        elif sub["speaker"] == "តួស្រី":
                            voice = "km-KH-SreymomNeural" if "Sreymom" in female_profile else "km-KH-PisethNeural"
                        else:
                            voice = "km-KH-PisethNeural" if "Piseth" in narrator_profile else "km-KH-SreymomNeural"
                            
                        edge_cmd = [
                            "edge-tts",
                            "--text", clean_text,
                            "--voice", voice,
                            "--rate", "+0%",
                            "--write-media", line_audio_path
                        ]
                        subprocess.run(edge_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        
                        if os.path.exists(line_audio_path) and os.path.getsize(line_audio_path) > 100:
                            valid_subtitles.append(sub)
                            audio_inputs.extend(["-i", line_audio_path])
                    
                    if valid_subtitles:
                        progress_bar.progress(60)
                        status_text.text("⏳ Mixing Background Music (BGM) with AI Voices via FFmpeg...")
                        
                        output_video_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
                        
                        filter_complex_parts = []
                        mix_inputs = []
                        
                        bgm_filter = f"[0:a]pan=stereo|c0=c0-c1|c1=c1-c0,volume={bgm_volume}"
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
                                filter_complex_parts.append(f"[{stream_idx}:a]volume=2.0,atempo={speed_factor},adelay={delay_ms}|{delay_ms}[a{idx}]")
                            else:
                                filter_complex_parts.append(f"[{stream_idx}:a]volume=2.0,adelay={delay_ms}|{delay_ms}[a{idx}]")
                                
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
                            "-preset", "fast",
                            "-c:a", "aac",
                            output_video_path
                        ])
                        
                        process = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        
                        if process.returncode == 0 and os.path.exists(output_video_path) and os.path.getsize(output_video_path) > 0:
                            progress_bar.progress(100)
                            status_text.text("🎉 Video Rendering Completed Successfully!")
                            st.success("✅ បាន Render វីដេអូរួចរាល់! ភ្លេងអម (BGM) លឺស្រទន់ៗអមជាមួយសំឡេង AI តាមតួអង្គ និងអត្ថបទរត់លើវីដេអូ។")
                            
                            with open(output_video_path, "rb") as file:
                                st.download_button(
                                    label="📥 Download Pro Dubbed Video (.MP4)",
                                    data=file,
                                    file_name="movie_time_multivoice.mp4",
                                    mime="video/mp4",
                                    use_container_width=True
                                )
                        else:
                            st.error(f"❌ FFmpeg Render failed: {process.stderr.decode('utf-8')[:300]}")
                    else:
                        st.error("❌ No valid subtitles found or audio generation failed.")
                except Exception as e:
                    st.error(f"❌ Render Exception: {e}")
    else:
        st.info("👆 Upload a video up to 1GB and click **'Extract & Auto Translate'** to start.")
    
    st.markdown('</div>', unsafe_allow_html=True)
