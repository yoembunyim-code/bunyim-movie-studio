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
                MOVIE TIME STUDIO PRO - AI KHMER DUBBING
            </h2>
            <p style="margin: 0; font-size: 12px; color: #94A3B8;">ប្រព័ន្ធស្វ័យប្រវត្តិបកប្រែវីដេអូ និងបញ្ចូលសំឡេងខ្មែរ AI (Edge-TTS & FFmpeg Pro)</p>
        </div>
        <div>
            <span style="background-color: #064E3B; color: #34D399; padding: 5px 10px; border-radius: 6px; font-size: 11px; font-weight: bold;">● Edge-TTS & FFmpeg Active</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# Layout Columns
col_left, col_center = st.columns([1.2, 1.8])

with col_left:
    st.markdown("### 📺 ផ្ទាំងមើលវីដេអូ (Video Preview)")
    uploaded_file = st.file_uploader("ទម្លាក់វីដេអូរឿង ឬ Audio នៅទីនេះ (Drop File)", type=["mp4", "mkv", "mov"])
    
    if uploaded_file is not None:
        st.video(uploaded_file)
        st.success(f"✅ បានផ្ទុកឯកសារ: {uploaded_file.name}")
    else:
        st.info("📌 សូម Upload វីដេអូប្រភេទ MP4 ដើម្បីចាប់ផ្តើម Render ។")

    st.markdown("---")
    st.markdown("### 🎛️ ការកំណត់សំឡេង AI (Voice Engine)")
    voice_choice = st.selectbox(
        "🎙️ រើសសំឡេង AI (Voice)", 
        ["km-KH-SreymomNeural (ស្រី - ធម្មជាតិ)", "km-KH-PisethNeural (ប្រុស - រឹងមាំ)"]
    )
    speed_rate = st.slider("ល្បឿននិយាយ (Speed)", 0.5, 2.0, 1.0, 0.05)
    orig_audio_vol = st.slider("កម្រិតសំឡេងដើមវីដេអូ (Original Audio Ducking %)", 0, 100, 15)

with col_center:
    st.markdown("### 📝 តារាងកែសម្រួលអត្ថបទសន្ទនា និងបកប្រែខ្មែរ (Subtitle Script)")
    
    if 'subtitles' not in st.session_state:
        st.session_state.subtitles = [
            {"time": "00:01 - 00:04", "speaker": "សម្រាយរឿង", "khmer": "ជិតជោគជ័យហើយ ជួយផងលោកពូយួន និងអ្នកនាងយៀក!"},
            {"time": "00:05 - 00:09", "speaker": "តួប្រុស", "khmer": "អ្នកទាំងអស់គ្នាប្រញាប់ឡើងមក ខ្ញុំជួយទាញឡើងមក លោកម្ចាស់ឆេង!"},
            {"time": "00:10 - 00:15", "speaker": "តួស្រី", "khmer": "បើកូនស្រីឡើងទៅលើបាន អ្នកត្រូវតែតោងឱ្យជាប់ ខ្សែពួរជិតដាច់ហើយ!"}
        ]

    for idx, sub in enumerate(st.session_state.subtitles):
        cols = st.columns([1, 1.2, 3])
        with cols[0]:
            st.text(sub["time"])
        with cols[1]:
            st.session_state.subtitles[idx]["speaker"] = st.selectbox(f"Role {idx}", ["សម្រាយរឿង", "តួប្រុស", "តួស្រី"], index=["សម្រាយរឿង", "តួប្រុស", "តួស្រី"].index(sub["speaker"]), key=f"spk_{idx}")
        with cols[2]:
            st.session_state.subtitles[idx]["khmer"] = st.text_area(f"Khmer {idx}", sub["khmer"], key=f"kh_{idx}", height=60)

    st.markdown("---")
    st.markdown("### 🚀 បញ្ចូលសំឡេង និង Export វីដេអូចុងក្រោយ")
    
    if st.button("🎬 ចាប់ផ្តើម Render និង Export វីដេអូ MP4 ជាមួយសំឡេង AI ខ្មែរ"):
        if uploaded_file is not None:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("⏳ កំពុងត្រៀមទិន្នន័យវីដេអូ...")
                progress_bar.progress(20)
                
                # Save uploaded video to temp file
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                tfile.write(uploaded_file.read())
                input_video_path = tfile.name
                tfile.close()
                
                # Combine all Khmer texts into one script for TTS synthesis
                full_khmer_text = " ".join([sub["khmer"] for sub in st.session_state.subtitles])
                
                status_text.text("⏳ កំពុងបង្កើតសំឡេង AI ភាសាខ្មែរ (Edge-TTS)...")
                progress_bar.progress(50)
                
                # Select voice mapping
                selected_voice = "km-KH-SreymomNeural" if "ស្រី" in voice_choice else "km-KH-PisethNeural"
                tts_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                
                # Use edge-tts command line via subprocess (Reliable & No Event Loop Error)
                edge_cmd = [
                    "edge-tts",
                    "--text", full_khmer_text,
                    "--voice", selected_voice,
                    "--write-media", tts_audio_path
                ]
                subprocess.run(edge_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                status_text.text("⏳ កំពុងប្រើប្រាស់ FFmpeg ដើម្បីបញ្ចូលសំឡេង AI ខ្មែរ និងវីដេអូ...")
                progress_bar.progress(80)
                
                output_video_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
                vol_scale = orig_audio_vol / 100.0
                
                # FFmpeg command to mix original video audio (ducked) with generated Khmer AI voice
                ffmpeg_cmd = [
                    "ffmpeg", "-y",
                    "-i", input_video_path,
                    "-i", tts_audio_path,
                    "-filter_complex", f"[0:a]volume={vol_scale}[a0];[1:a]volume=1.0[a1];[a0][a1]amix=inputs=2:duration=first[aout]",
                    "-map", "0:v",
                    "-map", "[aout]",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    output_video_path
                ]
                
                subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                progress_bar.progress(100)
                status_text.text("🎉 បង្កើតវីដេអូបញ្ចូលសំឡេងខ្មែរ AI ជោគជ័យ 100%!")
                st.success("✅ វីដេអូរឿងរបស់អ្នកត្រូវបាន Render ជាមួយសំឡេងខ្មែរ AI និង FFmpeg រួចរាល់ដោយជោគជ័យ!")
                
                # Download button
                with open(output_video_path, "rb") as file:
                    st.download_button(
                        label="📥 ទាញយកវីដេអូបញ្ចូលសំឡេងខ្មែរ AI (.MP4)",
                        data=file,
                        file_name="khmer_dubbed_video_pro.mp4",
                        mime="video/mp4"
                    )
            except Exception as e:
                st.error(f"❌ កើតកំហុសក្នុងដំណើរការ Render: {e}")
        else:
            st.warning("⚠️ សូមทำการ Upload វីដេអូនៅផ្នែកខាងឆ្វេងជាមុនសិន មុននឹងចុច Export!")
