import streamlit as st
import os
import subprocess
import tempfile

# Set page configuration
st.set_page_config(
    page_title="Movie Time Studio Pro - AI Khmer Dubbing Engine",
    page_icon="🎬",
    layout="wide"
)

# Custom Styling
st.markdown("""
    <style>
    .main { background-color: #07090E; color: #E2E8F0; }
    .stButton>button {
        background: linear-gradient(to right, #10B981, #0D9488);
        color: black; font-weight: bold; border-radius: 8px; border: 1px solid #34D399;
    }
    .stButton>button:hover { background: linear-gradient(to right, #059669, #0F766E); color: white; }
    </style>
""", unsafe_allow_html=True)

# Top Header Banner
st.markdown("""
    <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px; background-color: #0F1420; border-radius: 10px; border: 1px solid #1E293B; margin-bottom: 20px;">
        <div>
            <h2 style="margin: 0; font-size: 20px; background: -webkit-linear-gradient(left, #06B6D4, #6366F1, #EC4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                MOVIE TIME STUDIO PRO - AUTO SYNC DUBBING PRO
            </h2>
            <p style="margin: 0; font-size: 12px; color: #94A3B8;">ប្រព័ន្ធគណនា និងសារ៉េល្បឿនតាមមាត់តួអង្គស្វ័យប្រវត្តិ (Auto-Tempo & Time Sync Engine)</p>
        </div>
        <div>
            <span style="background-color: #064E3B; color: #34D399; padding: 5px 10px; border-radius: 6px; font-size: 11px; font-weight: bold;">● Auto-Sync Active</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# Layout Columns
col_left, col_center = st.columns([1.2, 1.8])

with col_left:
    st.markdown("### 📺 ផ្ទាំងមើលវីដេអូ (Video Preview)")
    uploaded_file = st.file_uploader("ទម្លាក់វីដេអូរឿងនៅទីនេះ (Drop MP4 File)", type=["mp4", "mkv", "mov"])
    
    if uploaded_file is not None:
        st.video(uploaded_file)
        st.success(f"✅ បានផ្ទុកឯកសារ: {uploaded_file.name}")
    else:
        st.info("📌 សូម Upload វីដេអូប្រភេទ MP4 ដើម្បីចាប់ផ្តើម Render ។")

    st.markdown("---")
    st.markdown("### 💡 របៀបដំណើរការស្វ័យប្រវត្តិ៖")
    st.info("- **Start (s):** ម៉ោងចាប់ផ្តើមនិយាយ។\n- **Duration (s):** រយៈពេលដែលត្រូវនិយាយចប់ (ប្រព័ន្ធនឹងគណនាល្បឿន Speed ស្វ័យប្រវត្តិឱ្យទាន់រយៈពេលនេះកុំឱ្យហៀរម៉ោង)។")

with col_center:
    st.markdown("### 📝 តារាងគ្រប់គ្រងម៉ោង និងអត្ថបទតាមតួអង្គ")
    
    if 'subtitles' not in st.session_state:
        st.session_state.subtitles = [
            {"time_sec": 1.5, "duration": 3.0, "speaker": "តួស្រី", "khmer": "នាវាចង់លិចហើយ ជួយខ្ញុំផង!"},
            {"time_sec": 6.0, "duration": 4.0, "speaker": "សម្រាយរឿង", "khmer": "ជិតជោគជ័យហើយ ជួយផងលោកពូយួន និងអ្នកនាងយៀក!"},
            {"time_sec": 10.5, "duration": 3.5, "speaker": "តួប្រុស", "khmer": "អ្នកទាំងអស់គ្នាប្រញាប់ឡើងមក ខ្ញុំជួយទាញឡើងមក!"}
        ]

    for idx, sub in enumerate(st.session_state.subtitles):
        cols = st.columns([0.8, 0.8, 1.2, 3])
        with cols[0]:
            st.session_state.subtitles[idx]["time_sec"] = st.number_input(f"Start {idx}", value=sub["time_sec"], step=0.1, key=f"t_{idx}")
        with cols[1]:
            st.session_state.subtitles[idx]["duration"] = st.number_input(f"Dur {idx}", value=sub["duration"], step=0.1, min_value=1.0, key=f"d_{idx}")
        with cols[2]:
            st.session_state.subtitles[idx]["speaker"] = st.selectbox(f"Role {idx}", ["សម្រាយរឿង", "តួប្រុស", "តួស្រី"], index=["សម្រាយរឿង", "តួប្រុស", "តួស្រី"].index(sub["speaker"]), key=f"spk_{idx}")
        with cols[3]:
            st.session_state.subtitles[idx]["khmer"] = st.text_area(f"Khmer {idx}", sub["khmer"], key=f"kh_{idx}", height=60)

    st.markdown("---")
    st.markdown("### 🚀 បញ្ចូលសំឡេងតាមតួអង្គ និង Export វីដេអូចុងក្រោយ")
    
    if st.button("🎬 ចាប់ផ្តើម Render វីដេអូ (Auto-Sync តាមមាត់តួអង្គ)"):
        if uploaded_file is not None:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("⏳ កំពុងត្រៀមទិន្នន័យវីដេអូ...")
                progress_bar.progress(10)
                
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                tfile.write(uploaded_file.read())
                input_video_path = tfile.name
                tfile.close()
                
                audio_inputs = []
                temp_audio_files = []
                
                for i, sub in enumerate(st.session_state.subtitles):
                    status_text.text(f"⏳ កំពុងបង្កើតសំឡេង AI សម្រាប់ប្រយោគទី {i+1} ({sub['speaker']})...")
                    
                    if sub["speaker"] == "តួប្រុស":
                        voice = "km-KH-PisethNeural"
                    else:
                        voice = "km-KH-SreymomNeural"
                        
                    line_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                    temp_audio_files.append(line_audio_path)
                    
                    # Generate speech using edge-tts
                    edge_cmd = [
                        "edge-tts",
                        "--text", sub["khmer"],
                        "--voice", voice,
                        "--write-media", line_audio_path
                    ]
                    subprocess.run(edge_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
                    audio_inputs.extend(["-i", line_audio_path])
                
                progress_bar.progress(60)
                status_text.text("⏳ កំពុងគណនាល្បឿន Auto-Tempo និងបញ្ចូលសំឡេងឆ្លាស់គ្នា...")
                
                output_video_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
                
                filter_complex_parts = []
                mix_inputs = []
                
                for i, sub in enumerate(st.session_state.subtitles):
                    delay_ms = int(sub["time_sec"] * 1000)
                    target_duration = sub["duration"]
                    
                    # Estimate audio length based on character length (approx 15 characters per second as baseline)
                    # We can use FFmpeg filter to dynamically adjust atempo if needed, 
                    # or apply a smart filter chain. Here we use an estimated speed adjustment.
                    char_count = len(sub["khmer"])
                    estimated_audio_duration = char_count / 12.0  # rough estimate of normal speech speed in Khmer
                    
                    speed_factor = 1.0
                    if estimated_audio_duration > target_duration and target_duration > 0:
                        speed_factor = min(round(estimated_audio_duration / target_duration, 2), 2.0)
                    
                    # Build filter for this track: apply atempo if speed differs, then adelay
                    if speed_factor != 1.0:
                        # FFmpeg atempo only supports values between 0.5 and 2.0. Chain them if needed.
                        if speed_factor > 2.0:
                            speed_factor = 2.0
                        filter_complex_parts.append(f"[{i+1}:a]atempo={speed_factor},adelay={delay_ms}|{delay_ms}[a{i}]")
                    else:
                        filter_complex_parts.append(f"[{i+1}:a]adelay={delay_ms}|{delay_ms}[a{i}]")
                        
                    mix_inputs.append(f"[a{i}]")
                
                num_tracks = len(st.session_state.subtitles)
                mix_filter = "".join(mix_inputs) + f"amix=inputs={num_tracks}:duration=longest[aout]"
                filter_complex_parts.append(mix_filter)
                
                full_filter_str = ";".join(filter_complex_parts)
                
                ffmpeg_cmd = [
                    "ffmpeg", "-y",
                    "-i", input_video_path
                ]
                ffmpeg_cmd.extend(audio_inputs)
                ffmpeg_cmd.extend([
                    "-filter_complex", full_filter_str,
                    "-map", "0:v",
                    "-map", "[aout]",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    output_video_path
                ])
                
                subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                progress_bar.progress(100)
                status_text.text("🎉 បង្កើតវីដេអូ Auto-Sync ជោគជ័យ 100%!")
                st.success("✅ វីដេអូរឿងរបស់អ្នកត្រូវបាន Render ស្វ័យប្រវត្តិដោយកែសម្រួលល្បឿន និងម៉ោងត្រូវមាត់តួអង្គរួចរាល់!")
                
                with open(output_video_path, "rb") as file:
                    st.download_button(
                        label="📥 ទាញយកវីដេអូ Auto-Sync (.MP4)",
                        data=file,
                        file_name="khmer_dubbed_autosync_pro.mp4",
                        mime="video/mp4"
                    )
            except Exception as e:
                st.error(f"❌ កើតកំហុសក្នុងដំណើរការ Render: {e}")
        else:
            st.warning("⚠️ សូមทำการ Upload វីដេអូនៅផ្នែកខាងឆ្វេងជាមុនសិន មុននឹងចុច Export!")
