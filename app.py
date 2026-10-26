import streamlit as st
import streamlit.components.v1 as components
import os
import subprocess
import tempfile
import re
import time
import requests
import json

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

    <!-- MAIN STUDIO WORKSPACE -->
    <div class="flex-1 flex overflow-hidden gap-2">
        
        <!-- LEFT PANEL -->
        <div class="w-full lg:w-[320px] flex flex-col gap-2 shrink-0">
            <div class="glass-panel rounded-xl p-3 border border-slate-800 flex flex-col gap-2">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-semibold text-slate-300"><i class="fa-solid fa-tv text-cyan-400"></i> ផ្ទាំងមើលវីដេអូ (Video Preview)</span>
                </div>
                <div class="relative aspect-video bg-black rounded-lg overflow-hidden border border-slate-800 group shadow-inner">
                    <video id="mainVideo" class="w-full h-full object-contain" controls>
                        <source src="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4" type="video/mp4">
                    </video>
                </div>
                <div class="border-2 border-dashed border-slate-800 hover:border-cyan-500/50 rounded-lg p-3 text-center transition bg-slate-950/40 cursor-pointer">
                    <input type="file" id="videoFileInput" accept="video/*,audio/*" class="hidden" onchange="handleFileSelect(event)">
                    <div class="flex items-center justify-center space-x-2 text-cyan-400" onclick="document.getElementById('videoFileInput').click()">
                        <i class="fa-solid fa-cloud-arrow-up text-lg"></i>
                        <span class="text-xs font-semibold">ទម្លាក់វីដេអូ ឬ Audio នៅទីនេះ</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- CENTER PANEL (SUBTITLES) -->
        <div class="flex-1 flex flex-col glass-panel rounded-xl border border-slate-800 overflow-hidden">
            <div class="p-2.5 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between">
                <button onclick="runAutoTranslate()" id="btnTranslate" class="px-3 py-1.5 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 text-white font-semibold text-xs transition flex items-center space-x-1.5">
                    <i class="fa-solid fa-language text-yellow-300"></i>
                    <span>បកប្រែស្វ័យប្រវត្តិជាខ្មែរ</span>
                </button>
            </div>
            
            <div class="grid grid-cols-12 gap-2 p-2 bg-slate-900/90 border-b border-slate-800 text-[11px] font-bold text-slate-400 uppercase">
                <div class="col-span-1 text-center">#</div>
                <div class="col-span-2 text-center">តួអង្គ</div>
                <div class="col-span-4">អត្ថបទដើម</div>
                <div class="col-span-4">អត្ថបទបកប្រែ</div>
                <div class="col-span-1 text-center">សកម្មភាព</div>
            </div>

            <div id="subtitleListContainer" class="flex-1 overflow-y-auto p-2 space-y-2">
                <!-- Dynamic Rows -->
            </div>
        </div>
    </div>

    <script>
        let subtitles = [
            { id: 1, speaker: "narrator", orig: "全要成了 救命啊元叔月救命！", khmer: "ជិតជោគជ័យហើយ ជួយផងលោកពូយួន និងអ្នកនាងយៀក!" },
            { id: 2, speaker: "male", orig: "你們快上來 我拉你們上來 成大人！", khmer: "អ្នកទាំងអស់គ្នាប្រញាប់ឡើងមក ខ្ញុំជួយទាញឡើងមក លោកម្ចាស់ឆេង!" }
        ];

        function renderTable() {
            const container = document.getElementById('subtitleListContainer');
            container.innerHTML = '';
            subtitles.forEach((sub, index) => {
                const row = document.createElement('div');
                row.className = "grid grid-cols-12 gap-2 p-2 bg-slate-900/60 rounded-lg border border-slate-800 items-center text-xs";
                row.innerHTML = `
                    <div class="col-span-1 text-center font-mono text-cyan-400">#${sub.id}</div>
                    <div class="col-span-2">
                        <select class="w-full bg-slate-950 text-slate-200 rounded p-1 border border-slate-700">
                            <option value="male" ${sub.speaker === 'male' ? 'selected' : ''}>👨 ប្រុស</option>
                            <option value="female" ${sub.speaker === 'female' ? 'selected' : ''}>👩 ស្រី</option>
                            <option value="narrator" ${sub.speaker === 'narrator' ? 'selected' : ''}>🎙️ សម្រាយ</option>
                        </select>
                    </div>
                    <div class="col-span-4">
                        <textarea rows="2" class="w-full bg-slate-950 text-amber-300 rounded p-1 text-xs">${sub.orig}</textarea>
                    </div>
                    <div class="col-span-4">
                        <textarea rows="2" class="w-full bg-slate-950 text-emerald-400 rounded p-1 text-xs font-khmer font-semibold">${sub.khmer}</textarea>
                    </div>
                    <div class="col-span-1 flex justify-center space-x-1">
                        <button onclick="previewVoice('${sub.khmer}', '${sub.speaker}')" class="w-7 h-7 bg-indigo-900 hover:bg-indigo-600 text-white rounded flex items-center justify-center">
                            <i class="fa-solid fa-volume-high text-[10px]"></i>
                        </button>
                    </div>
                `;
                container.appendChild(row);
            });
        }

        function previewVoice(text, speaker) {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                const utterance = new SpeechSynthesisUtterance(text);
                const voices = window.speechSynthesis.getVoices();
                const khmerVoice = voices.find(v => v.lang.includes('km'));
                if (khmerVoice) utterance.voice = khmerVoice;
                if (speaker === 'female') utterance.pitch = 1.3;
                else if (speaker === 'male') utterance.pitch = 0.9;
                else utterance.pitch = 0.7;
                window.speechSynthesis.speak(utterance);
            }
        }

        function runAutoTranslate() {
            window.parent.postMessage({type: 'TRANSLATE_ALL'}, '*');
        }

        function handleFileSelect(e) {
            const file = e.target.files[0];
            if (file) {
                const url = URL.createObjectURL(file);
                document.getElementById('mainVideo').src = url;
            }
        }

        window.onload = renderTable;
    </script>
</body>
</html>
"""

# បង្ហាញ UI
components.html(html_code, height=800, scrolling=True)

# បង្ហាញប៊ូតុង Python សម្រាប់ការបកប្រែពិត
st.markdown("---")
if st.button("🔄 បកប្រែពិតប្រាកដ (Real Translate)", use_container_width=True):
    st.success("✅ កំពុងដំណើរការបកប្រែ...")
    # នៅទីនេះអ្នកអាចបន្ថែមកូដសម្រាប់ការបកប្រែពិត
