import streamlit as st
import streamlit.components.v1 as components
import os
import subprocess
import tempfile
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

st.set_page_config(page_title="Movie Time Studio Pro", layout="wide", initial_sidebar_state="collapsed")

# លាក់របារ Menu និង Footer របស់ Streamlit
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.block-container {padding-top: 1rem; padding-bottom: 1rem; padding-left: 1rem; padding-right: 1rem;}
</style>
""", unsafe_allow_html=True)

# ============ មុខងារ Backend ============
def translate_to_khmer(text):
    if not text or not text.strip(): return ""
    if re.search(r'[\u1780-\u17FF]', text): return text
    
    url = "https://api.mymemory.translated.net/get"
    params = {"q": text, "langpair": "en|km"}
    
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

def generate_voice(text, voice_type="male"):
    voice_map = {
        "male": "km-KH-PisethNeural",
        "female": "km-KH-SreymomNeural",
        "narrator": "km-KH-PisethNeural"
    }
    voice = voice_map.get(voice_type, "km-KH-PisethNeural")
    
    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
    cmd = ["edge-tts", "--text", text, "--voice", voice, "--write-media", temp_audio]
    
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return temp_audio
    except Exception:
        return None

# ============ រចនាប័ទ្ម ============
st.markdown("""
<style>
.stApp { background-color: #07090E !important; color: #E2E8F0; font-family: 'Kantumruy Pro', sans-serif; }
.header-bar { 
    display:flex; align-items:center; justify-content:space-between;
    background: linear-gradient(90deg, #0B101D 0%, #151D30 100%);
    padding:12px 20px; border-radius:12px; border:1px solid #1E293B;
    box-shadow:0 4px 20px rgba(0,0,0,0.6); margin-bottom:15px; 
}
.brand-title { 
    font-size:20px; font-weight:800;
    background: linear-gradient(135deg,#38BDF8 0%,#818CF8 50%,#C084FC 100%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    display:flex; align-items:center; gap:10px; 
}
.card-panel { 
    background:#0D121F; border:1px solid #1E293B; border-radius:12px;
    padding:18px; box-shadow:0 4px 12px rgba(0,0,0,0.4); margin-bottom:20px; 
}
.stButton > button { 
    background: linear-gradient(135deg,#0EA5E9 0%,#2563EB 100%) !important;
    color:#FFF !important; font-weight:700 !important; border:none !important;
    border-radius:8px !important; padding:8px 16px !important;
    transition:all 0.3s ease !important; box-shadow:0 0 10px rgba(14,165,233,0.3) !important; 
}
.stButton > button:hover { 
    background: linear-gradient(135deg,#0284C7 0%,#1D4ED8) !important;
    box-shadow:0 0 18px rgba(14,165,233,0.6) !important; transform:translateY(-2px); 
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="header-bar">
        <div class="brand-title">🎬 MOVIE TIME STUDIO PRO
            <span style="font-size:13px;font-weight:normal;color:#94A3B8;">| AI KHMER AUTO DUBBING</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# ============ UI ដែលដំណើរការពិត ============
col1, col2 = st.columns([1, 1.5])

with col1:
    st.markdown('<div class="card-panel">', unsafe_allow_html=True)
    st.markdown("### 📤 ទាញយកវីដេអូ (Upload Video)")
    uploaded_file = st.file_uploader("ជ្រើសរើសវីដេអូ", type=["mp4", "mkv", "mov"])
    
    if uploaded_file is not None:
        st.video(uploaded_file)
        st.success(f"📁 បានទាញយក: {uploaded_file.name}")
    else:
        st.info("📌 សូមទាញយកវីដេអូរបស់អ្នកនៅទីនេះ។")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card-panel">', unsafe_allow_html=True)
    st.markdown("### ⚙️ ការកំណត់ និងដំណើរការ")
    
    if uploaded_file is not None:
        if st.button("🚀 ចាប់ផ្តើមបកប្រែវីដេអូនេះ", use_container_width=True):
            if not WHISPER_AVAILABLE:
                st.error("សូមដំឡើង faster-whisper សិន៖ pip install faster-whisper")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Save video to temp
                status_text.text("⏳ កំពុងរក្សាទុកវីដេអូ...")
                progress_bar.progress(10)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tfile:
                    tfile.write(uploaded_file.read())
                    video_path = tfile.name
                
                # Extract Audio
                status_text.text("⏳ កំពុងទាញយកសំឡេង...")
                progress_bar.progress(30)
                audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.wav').name
                subprocess.run(["ffmpeg", "-y", "-i", video_path, "-ar", "16000", "-ac", "1", audio_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Whisper
                status_text.text("⏳ AI កំពុងស្តាប់សំឡេង...")
                progress_bar.progress(50)
                model = WhisperModel("small", device="cpu", compute_type="int8")
                segments, info = model.transcribe(audio_path, language=None, beam_size=5, vad_filter=True)
                
                # Translate
                status_text.text("⏳ កំពុងបកប្រែជាខ្មែរ...")
                progress_bar.progress(80)
                
                st.session_state.subtitles = []
                for i, seg in enumerate(segments):
                    khmer_text = translate_to_khmer(seg.text.strip())
                    st.session_state.subtitles.append({
                        "id": i+1, "start": seg.start, "end": seg.end, 
                        "original": seg.text.strip(), "khmer": khmer_text, "speaker": "male"
                    })
                
                progress_bar.progress(100)
                status_text.text("✅ បកប្រែរួចរាល់!")
                st.success("✅ បានបកប្រែវីដេអូរបស់អ្នកដោយជោគជ័យ!")
                st.rerun()
    else:
        st.warning("⚠️ សូមទាញយកវីដេអូជាមុនសិន!")
    st.markdown('</div>', unsafe_allow_html=True)

# ============ តារាងបង្ហាញលទ្ធផល ============
if 'subtitles' in st.session_state and st.session_state.subtitles:
    st.markdown("---")
    st.markdown("### 📝 តារាងកែសម្រួលអត្ថបទ (Subtitle Editor)")
    
    for idx, sub in enumerate(st.session_state.subtitles):
        with st.expander(f"ឃ្លាទី {sub['id']} | ចាប់ផ្តើម: {sub['start']:.2f}s - បញ្ចប់: {sub['end']:.2f}s"):
            col_a, col_b, col_c = st.columns([1, 2, 2])
            with col_a:
                st.write("**តួអង្គ:**")
                st.session_state.subtitles[idx]['speaker'] = st.selectbox(
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
            
            # ប៊ូតុងបង្កើតសំឡេង
            if st.button(f"🔊 ស្តាប់សំឡេង AI សម្រាប់ឃ្លាទី {sub['id']}", key=f"btn_audio_{idx}"):
                role = st.session_state.subtitles[idx]['speaker']
                with st.spinner("កំពុងបង្កើតសំឡេង..."):
                    temp_audio = generate_voice(sub['khmer'], role)
                    if temp_audio and os.path.exists(temp_audio):
                        st.audio(temp_audio)
