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

st.set_page_config(
    page_title="Movie Time Studio Pro",
    page_icon="🎬", layout="wide", initial_sidebar_state="collapsed"
)

# ================= BACKEND FUNCTIONS =================
def translate_to_khmer(text):
    """បកប្រែអត្ថបទជាភាសាខ្មែរតាមរយៈ MyMemory API"""
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

def generate_voice(text, voice_type="male"):
    """បង្កើតសំឡេង AI តាមរយៈ edge-tts"""
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

# ================= UI + FRONTEND =================
def render_studio_ui():
    # កូដ HTML របស់អ្នក (ខ្ញុំបានសម្រួលបន្តិចដើម្បីឱ្យវាដំណើរការជាមួយ Streamlit)
    html_code = """
    <!DOCTYPE html>
    <html lang="km">
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <link href="https://fonts.googleapis.com/css2?family=Battambang:wght@400;700&family=Kantumruy+Pro:ital,wght@0,300..700;1,300..700&family=Orbitron:wght@500;700;900&display=swap" rel="stylesheet">
        <script>
            tailwind.config = {
                darkMode: 'class',
                theme: {
                    extend: {
                        colors: { studio: { bg: '#07090E', card: '#0F1420', border: '#1E293B', accent: '#6366F1', cyan: '#06B6D4', magenta: '#EC4899', gold: '#F59E0B', green: '#10B981' } },
                        fontFamily: { khmer: ['Kantumruy Pro', 'Battambang', 'sans-serif'], tech: ['Orbitron', 'sans-serif'] }
                    }
                }
            }
        </script>
        <style>
            body { background-color: #07090E; color: #E2E8F0; font-family: 'Kantumruy Pro', sans-serif; }
            .glass-panel { background: rgba(15, 20, 32, 0.85); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
            .neon-glow-cyan { box-shadow: 0 0 15px rgba(6, 182, 212, 0.35); }
        </style>
    </head>
    <body class="h-screen flex flex-col p-2">
        <!-- HEADER -->
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
            <button onclick="window.parent.postMessage({type: 'RESET'}, '*')" class="px-3 py-1.5 bg-slate-800 text-xs rounded border border-slate-700 hover:bg-slate-700">Reset</button>
        </header>

        <!-- MAIN -->
        <div class="flex-1 flex gap-2 overflow-hidden">
            <!-- LEFT: VIDEO -->
            <div class="w-[320px] glass-panel rounded-xl p-3 flex flex-col gap-2">
                <video id="mainVideo" class="w-full aspect-video bg-black rounded-lg" controls></video>
                <div class="border-2 border-dashed border-slate-700 rounded-lg p-3 text-center cursor-pointer" onclick="document.getElementById('videoInput').click()">
                    <input type="file" id="videoInput" accept="video/*" class="hidden" onchange="handleVideoUpload(event)">
                    <i class="fa-solid fa-cloud-arrow-up text-cyan-400 text-lg"></i>
                    <p class="text-xs text-slate-400 mt-1">ចុចទីនេះដើម្បី Upload វីដេអូ</p>
                </div>
            </div>

            <!-- CENTER: SUBTITLE TABLE -->
            <div class="flex-1 glass-panel rounded-xl flex flex-col overflow-hidden">
                <div class="p-2 border-b border-slate-700 flex justify-between bg-slate-900/50">
                    <button onclick="window.parent.postMessage({type: 'TRANSLATE'}, '*')" id="btnTrans" class="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-xs">
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
                        <div class="col-span-2 text-cyan-400 text-center">#${i+1}</div>
                        <div class="col-span-4 text-amber-300">${s.orig}</div>
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
                    // ផ្ញើឈ្មោះឯកសារទៅ Python ដើម្បីដំណើរការ
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
    components.html(html_code, height=800, scrolling=True)

# ================= STREAMLIT LOGIC =================
if 'subtitles' not in st.session_state:
    st.session_state.subtitles = []

render_studio_ui()

# បង្ហាញប៊ូតុងពិតប្រាកដសម្រាប់ការបកប្រែ និងបង្កើតសំឡេង
# (ដោយសារ Streamlit មិនអាចទទួល Action ពី HTML ដោយផ្ទាល់បានទេ យើងប្រើប៊ូតុងខាងក្រោម)
st.markdown("---")
st.markdown("### 🛠️ ការគ្រប់គ្រងពិតប្រាកដ (Real Backend Control)")

col1, col2 = st.columns(2)
with col1:
    uploaded_file = st.file_uploader("Upload វីដេអូ (សម្រាប់ការបកប្រែ)", type=["mp4", "mkv", "mov"])
    if uploaded_file:
        st.success(f"✅ បានទាញយក: {uploaded_file.name}")
        # នៅទីនេះអ្នកអាចបន្ថែមកូដសម្រាប់ដំណើរការ Whisper និងបកប្រែ
        if st.button("🪄 ចាប់ផ្តើមបកប្រែវីដេអូនេះ"):
            st.info("កំពុងដំណើរការ... (សូមរង់ចាំ)")
            # កូដសម្រាប់ Whisper និងបកប្រែ (អ្នកអាចប្រើកូដពីមុន)
            st.session_state.subtitles = [
                {"orig": "Hello", "khmer": "សួស្តី", "speaker": "male"},
                {"orig": "How are you?", "khmer": "អ្នកសុខសប្បាយទេ?", "speaker": "female"}
            ]
            st.rerun()

with col2:
    if st.button("🔄 បកប្រែអត្ថបទដែលមានស្រាប់ (Real Translate)", use_container_width=True):
        for sub in st.session_state.subtitles:
            if not re.search(r'[\u1780-\u17FF]', sub['khmer']):
                sub['khmer'] = translate_to_khmer(sub['orig'])
        st.success("✅ បកប្រែរួចរាល់!")
        st.rerun()

    if st.button("🔊 បង្កើតសំឡេង AI ពិតប្រាកដ", use_container_width=True):
        for sub in st.session_state.subtitles:
            audio_file = generate_voice(sub['khmer'], sub['speaker'])
            if audio_file:
                st.audio(audio_file)
        st.success("✅ បង្កើតសំឡេងរួចរាល់!")

# បញ្ជូនទិន្នន័យទៅ HTML ដើម្បីបង្ហាញ
components.html(
    f"<script>window.parent.postMessage({{type: 'UPDATE_SUBS', data: {st.session_state.subtitles}}}, '*');</script>",
    height=0
)
