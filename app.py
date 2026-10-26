import streamlit as st
import os
import subprocess
import tempfile
import numpy as np
import scipy.io.wavfile as wav
import re
import time
import requests

# ប្រើ faster-whisper សម្រាប់ការស្តាប់សំឡេង
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    st.error("⚠️ សូមដំឡើង `faster-whisper` ជាមុនសិន៖ `pip install faster-whisper`")

st.set_page_config(
    page_title="Movie Time Studio Pro",
    page_icon="🎬", layout="wide", initial_sidebar_state="expanded"
)

# Custom CSS សម្រាប់រចនាប័ទ្មងងឹត
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
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="header-bar">
        <div class="brand-title">🎬 MOVIE TIME STUDIO PRO
            <span style="font-size:13px;font-weight:normal;color:#94A3B8;">| AI KHMER AUTO DUBBING</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# ============ មុខងារបកប្រែ (MyMemory API) ============
def translate_to_khmer(text):
    if not text or not text.strip(): return ""
    if re.search(r'[\u1780-\u17FF]', text): return text
    
    url = "https://api.mymemory.translated.net/get"
    params = {"q": text, "langpair": "en|km"} # ប្តូរទៅ zh|km បើចង់បកពីចិន
    
    for _ in range(3):
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("responseStatus") == 200:
                    translated = data["responseData"]["translatedText"]
                    if translated and translated.strip() != text:
                        return translated
        except Exception:
            time.sleep(1)
    return text

# ============ UI សម្រាប់ Upload និងកំណត់ ============
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown('<div class="card-panel">', unsafe_allow_html=True)
    st.markdown("### 📤 ទាញយកវីដេអូ (Upload Video)")
    uploaded_file = st.file_uploader("ជ្រើសរើសវីដេអូ ឬសំឡេង", type=["mp4", "mkv", "mov", "mp3", "wav"])
    
    if uploaded_file is not None:
        st.video(uploaded_file)
        st.success(f"📁 បានទាញយក: {uploaded_file.name}")
    else:
        st.info("📌 សូមទាញយកវីដេអូរបស់អ្នកនៅទីនេះ។")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card-panel">', unsafe_allow_html=True)
    st.markdown("### ⚙️ ការកំណត់សំឡេង និងការបកប្រែ")
    
    lang_source = st.selectbox("ភាសាដើម (Source Language):", ["ភាសាអង់គ្លេស (English)", "ភាសាចិន (Chinese)"])
    
    voice_male = st.selectbox("សំឡេងតួប្រុស:", ["km-KH-PisethNeural"])
    voice_female = st.selectbox("សំឡេងតួស្រី:", ["km-KH-SreymomNeural"])
    
    st.markdown("---")
    
    btn_process = st.button("🚀 ចាប់ផ្តើមបកប្រែ និងបង្កើតសំឡេង", use_container_width=True)
    
    if btn_process:
        if uploaded_file is None:
            st.warning("⚠️ សូមទាញយកវីដេអូជាមុនសិន!")
        elif not WHISPER_AVAILABLE:
            st.error("❌ សូមដំឡើង faster-whisper សិន៖ pip install faster-whisper")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            try:
                # 1. ទាញយកសំឡេងពីវីដេអូ
                status_text.text("⏳ កំពុងទាញយកសំឡេងពីវីដេអូ...")
                progress_bar.progress(20)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as raw_file:
                    raw_file.write(uploaded_file.read())
                    raw_video_path = raw_file.name
                
                audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.wav').name
                subprocess.run(["ffmpeg", "-y", "-i", raw_video_path, "-ar", "16000", "-ac", "1", audio_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # 2. ប្រើ Whisper ដើម្បីស្តាប់សំឡេង
                status_text.text("⏳ AI កំពុងស្តាប់សំឡេង...")
                progress_bar.progress(50)
                
                model = WhisperModel("small", device="cpu", compute_type="int8")
                segments, info = model.transcribe(audio_path, language=None, beam_size=5, vad_filter=True)
                
                # 3. បកប្រែ និងបង្កើតសំឡេង
                status_text.text("⏳ កំពុងបកប្រែជាភាសាខ្មែរ...")
                progress_bar.progress(70)
                
                st.session_state.subtitles = []
                for i, seg in enumerate(segments):
                    start = seg.start
                    end = seg.end
                    text = seg.text.strip()
                    
                    # បកប្រែជាខ្មែរ
                    khmer_text = translate_to_khmer(text)
                    
                    st.session_state.subtitles.append({
                        "id": i+1, "start": start, "end": end, "original": text, "khmer": khmer_text
                    })
                
                progress_bar.progress(100)
                status_text.text("✅ បកប្រែរួចរាល់!")
                st.success("✅ បានបកប្រែវីដេអូរបស់អ្នកដោយជោគជ័យ!")
                
            except Exception as e:
                st.error(f"❌ មានបញ្ហា: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

# ============ បង្ហាញតារាងអត្ថបទ និងបង្កើតសំឡេង ============
if 'subtitles' in st.session_state and st.session_state.subtitles:
    st.markdown("---")
    st.markdown("### 📝 តារាងកែសម្រួលអត្ថបទ (Subtitle Editor)")
    
    for idx, sub in enumerate(st.session_state.subtitles):
        with st.expander(f"ឃ្លាទី {sub['id']} | ចាប់ផ្តើម: {sub['start']:.2f}s - បញ្ចប់: {sub['end']:.2f}s"):
            col_a, col_b, col_c = st.columns([1, 2, 2])
            with col_a:
                st.write("**តួអង្គ:**")
                st.session_state.subtitles[idx]['role'] = st.selectbox(
                    f"តួអង្គសម្រាប់ឃ្លាទី {sub['id']}", 
                    ["male", "female", "narrator"], 
                    key=f"role_{idx}"
                )
            with col_b:
                st.write("**អត្ថបទដើម:**")
                st.text_area(f"Original {sub['id']}", sub['original'], key=f"orig_{idx}", height=100, disabled=True)
            with col_c:
                st.write("**អត្ថបទបកប្រែ (ខ្មែរ):**")
                st.session_state.subtitles[idx]['khmer'] = st.text_area(f"Khmer {sub['id']}", sub['khmer'], key=f"khmer_{idx}", height=100)
            
            # ប៊ូតុងបង្កើតសំឡេងសម្រាប់ឃ្លានេះ
            if st.button(f"🔊 ស្តាប់សំឡេង AI សម្រាប់ឃ្លាទី {sub['id']}", key=f"btn_audio_{idx}"):
                role = st.session_state.subtitles[idx]['role']
                voice = voice_male if role == 'male' else (voice_female if role == 'female' else voice_male)
                
                with st.spinner("កំពុងបង្កើតសំឡេង..."):
                    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                    subprocess.run(["edge-tts", "--text", sub['khmer'], "--voice", voice, "--write-media", temp_audio], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
                    if os.path.exists(temp_audio):
                        st.audio(temp_audio)
