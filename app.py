import streamlit as st
import os
import subprocess
import tempfile
import whisper
from googletrans import Translator

# Set page configuration
st.set_page_config(
    page_title="Movie Time Studio Pro - AI Auto Dubbing Pro",
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
                MOVIE TIME STUDIO PRO - AI AUTO TRANSLATE & DUBBING
            </h2>
            <p style="margin: 0; font-size: 12px; color: #94A3B8;">ប្រព័ន្ធទាញយកសម្លេង បកប្រែ និងបញ្ចូលសម្លេងខ្មែរស្វ័យប្រវត្តិ (Whisper + Google Translate + Edge-TTS)</p>
        </div>
        <div>
            <span style="background-color: #064E3B; color: #34D399; padding: 5px 10px; border-radius: 6px; font-size: 11px; font-weight: bold;">● Auto-AI Active</span>
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
        st.info("📌 សូម Upload វីដេអូប្រភេទ MP4 ដើម្បីចាប់ផ្តើម Auto-Extract ។")

    st.markdown("---")
    st.markdown("### 🤖 ប្រព័ន្ធ AI ស្វ័យប្រវត្តិ៖")
    st.info("មុខងារថ្មីនេះនឹងធ្វើការ៖\n1. ទាញយកសម្លេងពីវីដេអូដោយស្វ័យប្រវត្តិ។\n2. ប្រើប្រាស់ **Whisper AI** ដើម្បីចាប់យកឃ្លានិយាយ។\n3. បកប្រែជាភាសាខ្មែរដោយ **Google Translate** ភ្លាមៗ។")

with col_center:
    st.markdown("### 📝 តារាងអត្ថបទបកប្រែស្វ័យប្រវត្តិ (Auto-Generated Script)")
    
    if 'auto_subtitles' not in st.session_state:
        st.session_state.auto_subtitles = []

    # Button to trigger AI Auto Transcription & Translation
    if st.button("🪄 ចាប់ផ្តើមទាញ និងបកប្រែអត្ថបទតាមវីដេអូស្វ័យប្រវត្តិ"):
        if uploaded_file is not None:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("⏳ កំពុងរក្សាទុកវីដេអូក្នុងថេមបូរ៉ារី...")
                progress_bar.progress(15)
                
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                tfile.write(uploaded_file.read())
                input_video_path = tfile.name
                tfile.close()
                
                status_text.text("⏳ កំពុងទាញយកសម្លេងចេញពីវីដេអូ (Extracting Audio)...")
                progress_bar.progress(30)
                
                audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                extract_cmd = ["ffmpeg", "-y", "-i", input_video_path, "-q:a", "0", "-map", "a", audio_path]
                subprocess.run(extract_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                status_text.text("⏳ កំពុងដំណើរការ Whisper AI ដើម្បីស្គាល់សម្លេងនិយាយ (Transcribing)...")
                progress_bar.progress(60)
                
                # Load tiny or base whisper model for fast cloud processing
                model = whisper.load_model("base")
                result = model.transcribe(audio_path)
                
                translator = Translator()
                st.session_state.auto_subtitles = []
                
                status_text.text("⏳ កំពុងបកប្រែអត្ថបទទៅជាភាសាខ្មែរ (Translating to Khmer)...")
                progress_bar.progress(85)
                
                for segment in result["segments"]:
                    start_time = segment["start"]
                    end_time = segment["end"]
                    duration = end_time - start_time
                    original_text = segment["text"]
                    
                    # Translate to Khmer
                    try:
                        translated = translator.translate(original_text, dest='km')
                        khmer_text = translated.text
                    except:
                        translated = translator.translate(original_text, dest='en')
                        khmer_text = translated.text # Fallback
                        
                    st.session_state.auto_subtitles.append({
                        "time_sec": round(start_time, 2),
                        "duration": round(duration, 2),
                        "speaker": "សម្រាយរឿង",
                        "khmer": khmer_text
                    })
                
                progress_bar.progress(100)
                status_text.text("🎉 ទាញយក និងបកប្រែអត្ថបទស្វ័យប្រវត្តិជោគជ័យ 100%!")
                st.success("✅ អត្ថបទត្រូវបានទាញយក និងបកប្រែរួចរាល់! អ្នកអាចពិនិត្យមើលក្នុងតារាងខាងក្រោម។")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ កើតកំហុសក្នុងដំណើរការ Auto-AI: {e}")
        else:
            st.warning("⚠️ សូមทำการ Upload វីដេអូនៅផ្នែកខាងឆ្វេងជាមុនសិន!")

    # Display dynamic table of auto-generated subtitles
    if st.session_state.auto_subtitles:
        for idx, sub in enumerate(st.session_state.auto_subtitles):
            cols = st.columns([0.8, 0.8, 1.2, 3])
            with cols[0]:
                st.session_state.auto_subtitles[idx]["time_sec"] = st.number_input(f"Start {idx}", value=sub["time_sec"], step=0.1, key=f"at_{idx}")
            with cols[1]:
                st.session_state.auto_subtitles[idx]["duration"] = st.number_input(f"Dur {idx}", value=sub["duration"], step=0.1, key=f"ad_{idx}")
            with cols[2]:
                st.session_state.auto_subtitles[idx]["speaker"] = st.selectbox(f"Role {idx}", ["សម្រាយរឿង", "តួប្រុស", "តួស្រី"], index=["សម្រាយរឿង", "តួប្រុស", "តួស្រី"].index(sub["speaker"]) if sub["speaker"] in ["សម្រាយរឿង", "តួប្រុស", "តួស្រី"] else 0, key=f"aspk_{idx}")
            with cols[3]:
                st.session_state.auto_subtitles[idx]["khmer"] = st.text_area(f"Khmer {idx}", sub["khmer"], key=f"akh_{idx}", height=60)
                
        st.markdown("---")
        st.markdown("### 🚀 បញ្ចូលសំឡេង AI ខ្មែរ និង Export វីដេអូចុងក្រោយ")
        
        if st.button("🎬 ចាប់ផ្តើម Render វីដេអូបញ្ចូលសម្លេងខ្មែរស្វ័យប្រវត្តិ"):
            if uploaded_file is not None:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    status_text.text("⏳ កំពុងត្រៀមទិន្នន័យសម្រាប់ Render...")
                    progress_bar.progress(10)
                    
                    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                    tfile.write(uploaded_file.read())
                    input_video_path = tfile.name
                    tfile.close()
                    
                    audio_inputs = []
                    
                    for i, sub in enumerate(st.session_state.auto_subtitles):
                        if not sub["khmer"].strip():
                            continue
                            
                        status_text.text(f"⏳ កំពុងបង្កើតសម្លេង AI សម្រាប់ឃ្លាទី {i+1}...")
                        
                        voice = "km-KH-PisethNeural" if sub["speaker"] == "តួប្រុស" else "km-KH-SreymomNeural"
                        line_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                        
                        edge_cmd = [
                            "edge-tts",
                            "--text", sub["khmer"],
                            "--voice", voice,
                            "--write-media", line_audio_path
                        ]
                        subprocess.run(edge_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        audio_inputs.extend(["-i", line_audio_path])
                    
                    progress_bar.progress(60)
                    status_text.text("⏳ កំពុងប្រើប្រាស់ FFmpeg ដើម្បីលុបសម្លេងដើម និងផ្គុំសម្លេង AI...")
                    
                    output_video_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
                    
                    filter_complex_parts = []
                    mix_inputs = []
                    active_sub_count = 0
                    
                    for i, sub in enumerate(st.session_state.auto_subtitles):
                        if not sub["khmer"].strip():
                            continue
                            
                        delay_ms = int(sub["time_sec"] * 1000)
                        target_duration = sub["duration"]
                        char_count = len(sub["khmer"])
                        estimated_audio_duration = char_count / 12.0
                        
                        speed_factor = 1.0
                        if estimated_audio_duration > target_duration and target_duration > 0:
                            speed_factor = min(round(estimated_audio_duration / target_duration, 2), 2.0)
                        
                        if speed_factor != 1.0:
                            filter_complex_parts.append(f"[{active_sub_count+1}:a]atempo={speed_factor},adelay={delay_ms}|{delay_ms}[a{active_sub_count}]")
                        else:
                            filter_complex_parts.append(f"[{active_sub_count+1}:a]adelay={delay_ms}|{delay_ms}[a{active_sub_count}]")
                            
                        mix_inputs.append(f"[a{active_sub_count}]")
                        active_sub_count += 1
                    
                    mix_filter = "".join(mix_inputs) + f"amix=inputs={active_sub_count}:duration=longest[aout]"
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
                    status_text.text("🎉 បង្កើតវីដេអូបញ្ចូលសម្លេងខ្មែរស្វ័យប្រវត្តិជោគជ័យ 100%!")
                    st.success("✅ វីដេអូរឿងរបស់អ្នកត្រូវបាន Render ស្វ័យប្រវត្តិដោយជោគជ័យ!")
                    
                    with open(output_video_path, "rb") as file:
                        st.download_button(
                            label="📥 ទាញយកវីដេអូចុងក្រោយ (.MP4)",
                            data=file,
                            file_name="auto_khmer_dubbed_movie.mp4",
                            mime="video/mp4"
                        )
                except Exception as e:
                    st.error(f"❌ កើតកំហុសក្នុងដំណើរការ Render: {e}")
    else:
        st.info("👆 សូមចុចប៊ូតុង **'🪄 ចាប់ផ្តើមទាញ និងបកប្រែអត្ថបទតាមវីដេអូស្វ័យប្រវត្តិ'** ខាងលើដើម្បីឱ្យ AI អាននិងបកប្រែវីដេអូរបស់អ្នក។")
