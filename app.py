import streamlit as st
import subprocess
import tempfile
import os
import re
import time
import requests
import numpy as np
import scipy.io.wavfile as wav
from faster_whisper import WhisperModel

# ================= CONFIGURATION =================
st.set_page_config(
    page_title="Movie Time Studio Pro",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ================= BACKEND FUNCTIONS =================
def translate_to_khmer(text):
    """បកប្រែអត្ថបទជាភាសាខ្មែរតាមរយៈ MyMemory API"""
    if not text or not text.strip(): return ""
    if re.search(r'[\u1780-\u17FF]', text): return text # បើជាខ្មែររួចហើយ
    
    url = "https://api.mymemory.translated.net/get"
    params = {"q": text, "langpair": "en|km"} # ប្តូរទៅ zh|km បើចង់បកពីចិន
    
    for _ in range(3):
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("responseStatus") == 200:
                    return data["responseData"]["translatedText"]
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

# ================= FRONTEND (HTML/JS) =================
html_content = """
<!DOCTYPE html>
<html lang="km">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
        body { background-color: #07090E; color: #E2E8F0; font-family: 'Plus Jakarta Sans', 'Kantumruy Pro', sans-serif; }
        .glass-panel { background: rgba(15, 20, 32, 0.85); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
        .neon-glow-cyan { box-shadow: 0 0 15px rgba(6, 182, 212, 0.35); }
    </style>
</head>
<body class="h-screen flex flex-col font-khmer text-sm">
    <header class="h-14 glass-panel border-b border-slate-800/80 px-4 flex items-center justify-between shrink-0">
        <div class="flex items-center space-x-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-cyan-500 to-emerald-400 p-[2px] flex items-center justify-center neon-glow-cyan">
                <div class="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                    <i class="fa-solid fa-film text-cyan-400 text-lg"></i>
                </div>
            </div>
            <div>
                <h1 class="font-tech text-base font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-pink-400">MOVIE TIME STUDIO PRO</h1>
                <p class="text-[11px] text-slate-400">ប្រព័ន្ធស្វ័យប្រវត្តិបកប្រែវីដេអូ</p>
            </div>
        </div>
    </header>

    <div class="flex-1 p-2">
        <div class="glass-panel rounded-xl p-4 border border-slate-800 h-full flex flex-col">
            <button onclick="window.parent.postMessage({type: 'TRANSLATE_ACTION'}, '*')" class="px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-500 w-max mb-4">
                <i class="fa-solid fa-language"></i> បកប្រែស្វ័យប្រវត្តិជាខ្មែរ
            </button>
            <div id="subtitleList" class="flex-1 overflow-y-auto space-y-2">
                <!-- Subtitle rows injected here -->
            </div>
        </div>
    </div>

    <script>
        // ទទួលទិន្នន័យពី Python (Streamlit)
        let subtitleData = [];

        function renderSubtitles() {
            const container = document.getElementById('subtitleList');
            container.innerHTML = '';
            subtitleData.forEach((sub, index) => {
                const row = document.createElement('div');
                row.className = "grid grid-cols-12 gap-2 p-2 bg-slate-900/60 rounded-lg border border-slate-800 items-center text-xs";
                row.innerHTML = `
                    <div class="col-span-2 text-center font-mono text-[10px] text-cyan-400">#${index+1}</div>
                    <div class="col-span-2 text-center">
                        <select class="w-full bg-slate-950 text-slate-200 text-[11px] rounded p-1 border border-slate-700">
                            <option value="male" ${sub.speaker === 'male' ? 'selected' : ''}>👨 ប្រុស</option>
                            <option value="female" ${sub.speaker === 'female' ? 'selected' : ''}>👩 ស្រី</option>
                            <option value="narrator" ${sub.speaker === 'narrator' ? 'selected' : ''}>🎙️ សម្រាយ</option>
                        </select>
                    </div>
                    <div class="col-span-4">
                        <textarea rows="2" class="w-full bg-slate-950 text-amber-300 rounded p-1 text-xs">${sub.original}</textarea>
                    </div>
                    <div class="col-span-3">
                        <textarea rows="2" class="w-full bg-slate-950 text-emerald-400 rounded p-1 text-xs">${sub.khmer}</textarea>
                    </div>
                    <div class="col-span-1 flex justify-center">
                        <button onclick="window.parent.postMessage({type: 'PLAY_AUDIO', text: '${sub.khmer}', speaker: '${sub.speaker}'}, '*')" class="w-7 h-7 bg-indigo-900 hover:bg-indigo-600 text-white rounded flex items-center justify-center">
                            <i class="fa-solid fa-volume-high"></i>
                        </button>
                    </div>
                `;
                container.appendChild(row);
            });
        }

        // ស្តាប់សារពី Python ដើម្បី Update ទិន្នន័យ
        window.addEventListener("message", (event) => {
            if (event.data.type === "UPDATE_SUBTITLES") {
                subtitleData = event.data.data;
                renderSubtitles();
            }
        });
    </script>
</body>
</html>
"""

# ================= STREAMLIT APP LOGIC =================
# គ្រប់គ្រង State
if 'subtitles' not in st.session_state:
    st.session_state.subtitles = [
        {"id": 1, "original": "Hello, how are you?", "khmer": "សួស្តី អ្នកសុខសប្បាយទេ?", "speaker": "male"},
        {"id": 2, "original": "I am fine, thank you.", "khmer": "ខ្ញុំសុខសប្បាយ អរគុណ។", "speaker": "female"}
    ]

if 'trigger_translate' not in st.session_state:
    st.session_state.trigger_translate = False

# បង្ហាញ UI (HTML)
st.components.v1.html(html_content, height=600, scrolling=True)

# បញ្ជូនទិន្នន័យទៅ HTML ដំបូង
st.components.v1.html(
    f"<script>window.parent.postMessage({{type: 'UPDATE_SUBTITLES', data: {st.session_state.subtitles}}}, '*');</script>",
    height=0
)

# បង្កើតប៊ូតុងសម្រាប់ចាប់យក Action ពី HTML
# (ដោយសារ Streamlit មិនអាចចាប់យក JS event ដោយផ្ទាល់បាន យើងប្រើប៊ូតុងក្រោម UI)
st.markdown("---")
if st.button("🔄 ធ្វើបច្ចុប្បន្នភាព និងបកប្រែពិតប្រាកដ (Real Translation)", use_container_width=True):
    for sub in st.session_state.subtitles:
        if not re.search(r'[\u1780-\u17FF]', sub['khmer']): # បើអត់ទាន់បក
            sub['khmer'] = translate_to_khmer(sub['original'])
    st.success("✅ បកប្រែរួចរាល់!")
    st.rerun()

if st.button("🔊 បង្កើតសំឡេង AI ពិតប្រាកដ (Real AI Voice)", use_container_width=True):
    for sub in st.session_state.subtitles:
        audio_file = generate_voice(sub['khmer'], sub['speaker'])
        if audio_file:
            st.audio(audio_file)
    st.success("✅ បង្កើតសំឡេងរួចរាល់!")
