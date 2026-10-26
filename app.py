import streamlit as st
import streamlit.components.v1 as components

# កំណត់ទំព័រឱ្យលាតសន្ធឹងពេញអេក្រង់
st.set_page_config(page_title="Movie Time Studio Pro", layout="wide", initial_sidebar_state="collapsed")

# លាក់របារ Menu និង Footer របស់ Streamlit ដើម្បីឱ្យវាមើលទៅដូចកម្មវិធីពិតៗ
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.block-container {padding-top: 0rem; padding-bottom: 0rem; padding-left: 0rem; padding-right: 0rem;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ==========================================
# ដាក់កូដ HTML ទាំងអស់របស់អ្នកនៅទីនេះ (ចាប់ពី <!DOCTYPE html> ដល់ </html>)
# ==========================================
html_code = """
<!DOCTYPE html>
<html lang="km">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Movie Time Studio Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Battambang:wght@400;700&family=Kantumruy+Pro:ital,wght@0,300..700;1,300..700&family=Orbitron:wght@500;700;900&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">

    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        studio: { bg: '#07090E', card: '#0F1420', border: '#1E293B', hover: '#1B2436', accent: '#6366F1', cyan: '#06B6D4', magenta: '#EC4899', gold: '#F59E0B', green: '#10B981' }
                    },
                    fontFamily: {
                        khmer: ['Kantumruy Pro', 'Battambang', 'sans-serif'],
                        tech: ['Orbitron', 'sans-serif'],
                        sans: ['Plus Jakarta Sans', 'Kantumruy Pro', 'sans-serif']
                    }
                }
            }
        }
    </script>

    <style>
        body { background-color: #07090E; color: #E2E8F0; font-family: 'Plus Jakarta Sans', 'Kantumruy Pro', sans-serif; overflow-x: hidden; user-select: none; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #0B0F17; }
        ::-webkit-scrollbar-thumb { background: #1E293B; border-radius: 4px; }
        .glass-panel { background: rgba(15, 20, 32, 0.85); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
        .neon-glow-cyan { box-shadow: 0 0 15px rgba(6, 182, 212, 0.35); }
        input[type=range] { -webkit-appearance: none; background: #1E293B; border-radius: 6px; height: 6px; }
        input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; height: 16px; width: 16px; border-radius: 50%; background: #06B6D4; cursor: pointer; box-shadow: 0 0 8px #06B6D4; }
    </style>
</head>

<body class="h-screen flex flex-col font-khmer text-sm">
    <!-- HEADER -->
    <header class="h-14 glass-panel border-b border-slate-800/80 px-4 flex items-center justify-between shrink-0 z-20">
        <div class="flex items-center space-x-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-cyan-500 to-emerald-400 p-[2px] flex items-center justify-center neon-glow-cyan">
                <div class="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                    <i class="fa-solid fa-film text-cyan-400 text-lg"></i>
                </div>
            </div>
            <div>
                <h1 class="font-tech text-base font-bold tracking-wider bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 via-indigo-300 to-pink-400">
                    MOVIE TIME STUDIO PRO
                </h1>
                <p class="text-[11px] text-slate-400">ប្រព័ន្ធស្វ័យប្រវត្តិបកប្រែវីដេអូ និងបញ្ចូលសំឡេងរឿងភាគ</p>
            </div>
        </div>
    </header>

    <!-- MAIN WORKSPACE -->
    <div class="flex-1 flex overflow-hidden p-2 gap-2">
        <!-- LEFT PANEL -->
        <div class="w-full lg:w-[320px] xl:w-[380px] flex flex-col gap-2 shrink-0">
            <div class="glass-panel rounded-xl p-3 border border-slate-800 flex flex-col gap-2 relative">
                <div class="relative aspect-video bg-black rounded-lg overflow-hidden border border-slate-800 shadow-inner">
                    <video id="mainVideo" class="w-full h-full object-contain" poster="https://placehold.co/640x360/0b0f19/38bdf8?text=Movie+Time+Studio+Pro">
                        <source src="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4" type="video/mp4">
                    </video>
                </div>
                <div class="border-2 border-dashed border-slate-800 rounded-lg p-3 text-center bg-slate-950/40 cursor-pointer">
                    <input type="file" id="videoFileInput" accept="video/*" class="hidden" onchange="handleFileSelect(event)">
                    <div class="flex items-center justify-center space-x-2 text-cyan-400" onclick="document.getElementById('videoFileInput').click()">
                        <i class="fa-solid fa-cloud-arrow-up text-lg"></i>
                        <span class="text-xs font-semibold">ទម្លាក់វីដេអូ ឬ Audio នៅទីនេះ</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- CENTER PANEL -->
        <div class="flex-1 flex flex-col glass-panel rounded-xl border border-slate-800 overflow-hidden">
            <div class="p-2.5 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between">
                <button onclick="alert('មុខងារនេះត្រូវការភ្ជាប់ទៅ Python Backend')" class="px-3 py-1.5 rounded-lg bg-indigo-600 text-white font-semibold text-xs transition flex items-center space-x-1.5">
                    <i class="fa-solid fa-microphone-lines text-cyan-300"></i>
                    <span>ចាប់សំឡេង (Transcribe Speech)</span>
                </button>
                <button onclick="alert('មុខងារនេះត្រូវការភ្ជាប់ទៅ Python Backend')" class="px-3 py-1.5 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 text-white font-semibold text-xs transition flex items-center space-x-1.5">
                    <i class="fa-solid fa-language text-yellow-300"></i>
                    <span>បកប្រែស្វ័យប្រវត្តិជាខ្មែរ</span>
                </button>
            </div>

            <div class="grid grid-cols-12 gap-2 p-2 bg-slate-900/90 border-b border-slate-800 text-[11px] font-bold text-slate-400 uppercase">
                <div class="col-span-2 text-center">Time</div>
                <div class="col-span-2 text-center">Speaker</div>
                <div class="col-span-4">Original</div>
                <div class="col-span-4">Khmer Dub</div>
            </div>

            <div id="subtitleListContainer" class="flex-1 overflow-y-auto p-2 space-y-2">
                <!-- Subtitle Rows Rendered dynamically via JavaScript -->
            </div>
        </div>
    </div>

    <script>
        // ទិន្នន័យគំរូ
        let sampleSubtitles = [
            { id: 1, start: "00:00:01", end: "00:00:04", speaker: "narrator", orig: "全要成了 救命啊元叔月救命！", khmer: "ជិតជោគជ័យហើយ ជួយផងលោកពូយួន និងអ្នកនាងយៀក!" },
            { id: 2, start: "00:00:05", end: "00:00:09", speaker: "male", orig: "你們快上來 我拉你們上來 成大人！", khmer: "អ្នកទាំងអស់គ្នាប្រញាប់ឡើងមក ខ្ញុំជួយទាញឡើងមក លោកម្ចាស់ឆេង!" }
        ];

        function renderTable() {
            const container = document.getElementById('subtitleListContainer');
            container.innerHTML = '';
            sampleSubtitles.forEach((sub, index) => {
                const row = document.createElement('div');
                row.className = "grid grid-cols-12 gap-2 p-2 bg-slate-900/60 rounded-lg border border-slate-800 items-center text-xs";
                row.innerHTML = `
                    <div class="col-span-2 text-center font-mono text-[10px] text-cyan-400">#${index+1}</div>
                    <div class="col-span-2">
                        <select class="w-full bg-slate-950 text-slate-200 text-[11px] rounded p-1 border border-slate-700">
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
                `;
                container.appendChild(row);
            });
        }
        window.onload = renderTable;
    </script>
</body>
</html>
"""

# បង្ហាញ UI នៅក្នុង Streamlit (កម្ពស់ 1000px ដើម្បីឱ្យឃើញពេញលេញ)
components.html(html_code, height=1000, scrolling=True)
