import streamlit as st
import streamlit.components.v1 as components
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

st.set_page_config(page_title="Movie Time Studio Pro", layout="wide", initial_sidebar_state="collapsed")

# លាក់របារ Menu និង Footer របស់ Streamlit
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.block-container {padding-top: 0rem; padding-bottom: 0rem; padding-left: 0rem; padding-right: 0rem;}
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

# ============ UI ស្អាតៗ (HTML) ============
html_code = """
<!DOCTYPE html>
<html lang="km">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Battambang:wght@400;700&family=Kantumruy+Pro:ital,wght@0,300..700;1,300..700&family=Orbitron:wght@500;700;900&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: { studio: { bg: '#07090E', card: '#0F1420', border: '#1E293B', accent: '#6366F1', cyan: '#06B6D4', magenta: '#EC4899', gold: '#F59E0B', green: '#10B981' } },
                    fontFamily: { khmer: ['Kantumruy Pro', 'Battambang', 'sans-serif'], tech: ['Orbitron', 'sans-serif'], sans: ['Plus Jakarta Sans', 'sans-serif'] }
                }
            }
        }
    </script>
    <style>
        body { background-color: #07090E; color: #E2E8F0; font-family: 'Plus Jakarta Sans', 'Kantumruy Pro', sans-serif; user-select: none; }
        .glass-panel { background: rgba(15, 20, 32, 0.85); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
        .neon-glow-cyan { box-shadow: 0 0 15px rgba(6, 182, 212, 0.35); }
        input[type=range] { -webkit-appearance: none; background: #1E293B; border-radius: 6px; height: 6px; }
        input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; height: 16px; width: 16px; border-radius: 50%; background: #06B6D4; cursor: pointer; box-shadow: 0 0 8px #06B6D4; }
    </style>
</head>
<body class="h-screen flex flex-col p-2">
    <header class="h-14 glass-panel rounded-xl mb-2 px-4 flex items-center justify-between shrink-0">
        <div class="flex items-center space-x-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-cyan-500 to-emerald-400 p-[2px] flex items-center justify-center neon-glow-cyan">
                <div class="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                    <i class="fa-solid fa-film text-cyan-400 text-lg"></i>
                </div>
            </div>
            <div>
                <h1 class="font-tech text-base font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-pink-400">MOVIE TIME STUDIO PRO</h1>
                <p class="text-[11px] text-slate-400">AI Auto Khmer Dubbing</p>
            </div>
        </div>
    </header>

    <div class="flex-1 flex gap-2 overflow-hidden">
        <div class="w-[320px] glass-panel rounded-xl p-3 flex flex-col gap-2">
            <video id="mainVideo" class="w-full aspect-video bg-black rounded-lg" controls>
                <source src="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4" type="video/mp4">
            </video>
            <div class="border-2 border-dashed border-slate-700 rounded-lg p-3 text-center cursor-pointer">
                <input type="file" id="videoInput" accept="video/*" class="hidden" onchange="handleVideoUpload(event)">
                <div onclick="document.getElementById('videoInput').click()">
                    <i class="fa-solid fa-cloud-arrow-up text-cyan-400 text-lg"></i>
                    <p class="text-xs text-slate-400 mt-1">ចុចទីនេះដើម្បី Upload វីដេអូ</p>
                </div>
            </div>
        </div>

        <div class="flex-1 glass-panel rounded-xl flex flex-col overflow-hidden">
            <div class="p-2 border-b border-slate-700 flex justify-between bg-slate-900/50">
                <button onclick="window.parent.postMessage({type: 'TRANSLATE'}, '*')" class="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-xs">
                    <i class="fa-solid fa-language"></i> បកប្រែជាខ្មែរ
                </button>
            </div>
            <div id="subList" class="flex-1 overflow-y-auto p-2 space-y-2">
                <!-- Rows injected here -->
            </div>
        </div>
    </div>

    <script>
        let subs = [];

        function renderTable() {
            const container = document.getElementById('subList');
            container.innerHTML = '';
            subs.forEach((s, i) => {
                let row = document.createElement('div');
                row.className = "grid grid-cols-12 gap-2 p-2 bg-slate-900/60 rounded border border-slate-800 text-xs items-center";
                row.innerHTML = `
                    <div class="col-span-2 text-cyan-400 text-center">#${s.id}</div>
                    <div class="col-span-4 text-amber-300">${s.original}</div>
                    <div class="col-span-4 text-emerald-400 font-bold">${s.khmer}</div>
                    <div class="col-span-2 text-center">
                        <button onclick="playAudio('${s.khmer}', '${s.speaker}')" class="px-2 py-1 bg-indigo-600 rounded text-white text-[10px]">🔊 ស្តាប់</button>
                    </div>
                `;
                container.appendChild(row);
            });
        }

        function playAudio(text, speaker) {
            window.parent.postMessage({type: 'PLAY_AUDIO', text: text, speaker: speaker}, '*');
        }

        function handleVideoUpload(event) {
            const file = event.target.files[0];
            if (file) {
                document.getElementById('mainVideo').src = URL.createObjectURL(file);
                window.parent.postMessage({type: 'VIDEO_UPLOADED', name: file.name}, '*');
            }
        }

        window.addEventListener("message", (event) => {
            if (event.data.type === "UPDATE_SUBS") {
                subs = event.data.data;
                renderTable();
            }
        });

        window.onload = renderTable;
    </script>
</body>
</html>
"""

# បង្ហាញ UI
components.html(html_code, height=700, scrolling=False)

# ============ BACKEND CONTROL PANEL ============
st.markdown("---")
st.markdown("### 🛠️ ផ្ទាំងគ្រប់គ្រងពិតប្រាកដ (Real Backend Control)")

col1, col2 = st.columns(2)
with col1:
    uploaded_file = st.file_uploader("1. Upload វីដេអូ (MP4)", type=["mp4"])
    if uploaded_file:
        st.success(f"✅ បានទាញយក: {uploaded_file.name}")
        if st.button("🪄 ចាប់ផ្តើមបកប្រែវីដេអូនេះ", use_container_width=True):
            with st.spinner("កំពុងដំណើរការ Whisper និងបកប្រែ..."):
                # Save uploaded file to temp
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tfile:
                    tfile.write(uploaded_file.read())
                    video_path = tfile.name
                
                # Process
                subs = process_video(video_path)
                st.session_state.subtitles = subs
                st.success(f"✅ បកប្រែរួចរាល់! ចំនួនឃ្លា: {len(subs)}")
                st.rerun()

with col2:
    st.markdown("**ជម្រើសបន្ថែម:**")
    if st.button("🔄 បកប្រែអត្ថបទដែលមានស្រាប់ (Real Translate)", use_container_width=True):
        if st.session_state.subtitles:
            for sub in st.session_state.subtitles:
                if not re.search(r'[\u1780-\u17FF]', sub['khmer']):
                    sub['khmer'] = translate_to_khmer(sub['original'])
            st.success("✅ បកប្រែរួចរាល់!")
            st.rerun()
        else:
            st.warning("មិនមានអត្ថបទសម្រាប់បកប្រែទេ។")

    if st.button("🔊 បង្កើតសំឡេង AI ពិតប្រាកដ", use_container_width=True):
        if st.session_state.subtitles:
            for sub in st.session_state.subtitles:
                audio_file = generate_voice(sub['khmer'], sub['speaker'])
                if audio_file:
                    st.audio(audio_file)
            st.success("✅ បង្កើតសំឡេងរួចរាល់!")
        else:
            st.warning("មិនមានអត្ថបទសម្រាប់បង្កើតសំឡេងទេ។")

# បញ្ជូនទិន្នន័យទៅ HTML
if st.session_state.subtitles:
    components.html(
        f"<script>window.parent.postMessage({{type: 'UPDATE_SUBS', data: {st.session_state.subtitles}}}, '*');</script>",
        height=0
    )
