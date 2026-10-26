"""
Movie Time Studio Pro - AI Khmer Auto Dubbing (Streamlit)

ដំណើរការ:  streamlit run app.py
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

import core

st.set_page_config(
    page_title="Movie Time Studio Pro",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# រចនាប័ទ្ម (ងងឹត + neon ដូចក្នុងរូប)
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Kantumruy+Pro:wght@300;400;600;700&family=Orbitron:wght@600;800&display=swap');
html, body, [class*="css"], .stApp { font-family: 'Kantumruy Pro', sans-serif; }
.stApp { background: #07090E; }
section[data-testid="stSidebar"] { background: #0B0F17; border-right: 1px solid #1E293B; }
.brand { display:flex; align-items:center; gap:14px; padding:6px 0 14px 0; }
.brand .logo { width:46px; height:46px; border-radius:12px; padding:2px;
  background:linear-gradient(135deg,#6366F1,#06B6D4,#34D399); box-shadow:0 0 16px rgba(6,182,212,.4); }
.brand .logo div { width:100%; height:100%; border-radius:10px; background:#020617;
  display:flex; align-items:center; justify-content:center; font-size:22px; }
.brand h1 { font-family:'Orbitron',sans-serif; font-size:22px; margin:0; letter-spacing:1px;
  background:linear-gradient(90deg,#22D3EE,#A5B4FC,#F472B6); -webkit-background-clip:text; color:transparent; }
.brand p { margin:0; font-size:12px; color:#94A3B8; }
.badge { display:inline-block; font-family:'Orbitron',sans-serif; font-size:10px; font-weight:800;
  padding:2px 9px; border-radius:99px; color:#000; background:linear-gradient(90deg,#F59E0B,#F43F5E); margin-left:8px; }
.panel { background:rgba(15,20,32,.85); border:1px solid #1E293B; border-radius:14px; padding:14px 16px; margin-bottom:10px; }
.pill { display:inline-block; padding:3px 10px; border-radius:8px; font-size:12px; margin-right:6px;
  background:#0F172A; border:1px solid #1E293B; color:#CBD5E1; }
.pill b { color:#34D399; }
.pill.warn b { color:#FBBF24; }
.meta { font-family:ui-monospace,monospace; font-size:12px; color:#94A3B8; line-height:1.9; }
.meta span { color:#E2E8F0; }
.stButton > button, .stDownloadButton > button { border-radius:10px; font-weight:600; }
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
  background:linear-gradient(90deg,#10B981,#0D9488); border:1px solid #34D399; color:#00110B; }
div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] { border:1px solid #1E293B; border-radius:10px; }
.track { background:#0B0F17; border:1px solid #1E293B; border-radius:10px; padding:10px 12px; }
.track .row { position:relative; height:30px; margin:6px 0; background:#0F1420; border-radius:6px; }
.track .lbl { font-size:11px; color:#94A3B8; margin-top:4px; }
.track .seg { position:absolute; top:3px; height:24px; border-radius:5px; overflow:hidden; white-space:nowrap;
  font-size:10px; line-height:24px; padding:0 4px; color:#fff; border:1px solid rgba(255,255,255,.25); }
.seg.male { background:#92400E; } .seg.female { background:#9D174D; } .seg.narrator { background:#065F46; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
if "workdir" not in st.session_state:
    st.session_state.workdir = tempfile.mkdtemp(prefix="movie_studio_")
WORK = Path(st.session_state.workdir)

DEFAULTS = {
    "df": core.empty_df(),
    "media_path": None,
    "media_name": None,
    "media_sig": None,
    "duration": 0.0,
    "is_video": False,
    "size": "-",
    "export_path": None,
    "editor_rev": 0,
}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)


def get_secret(name: str) -> str:
    try:
        return st.secrets.get(name, "") or ""
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Sidebar: ការកំណត់
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ ការកំណត់")
    api_key = st.text_input(
        "Gemini API Key",
        type="password",
        value=os.environ.get("GEMINI_API_KEY", "") or get_secret("GEMINI_API_KEY"),
        help="យកមកដោយឥតគិតថ្លៃនៅ aistudio.google.com/apikey  (ឬដាក់ក្នុង Streamlit Secrets ឈ្មោះ GEMINI_API_KEY)",
    )
    model = st.selectbox(
        "ម៉ូដែល Gemini",
        ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"],
        help="ប្រសិនបើម៉ូដែលណាមួយមិនដំណើរការ សូមសាកម៉ូដែលផ្សេង ឬវាយឈ្មោះម៉ូដែលថ្មីខាងក្រោម",
    )
    custom_model = st.text_input("ឈ្មោះម៉ូដែលផ្ទាល់ខ្លួន (ជម្រើស)", value="")
    if custom_model.strip():
        model = custom_model.strip()

    src_label = st.selectbox("ភាសាដើមក្នុងវីដេអូ", list(core.SOURCE_LANGS.keys()))
    src_lang = core.SOURCE_LANGS[src_label]

    st.divider()
    st.markdown("### 🎙️ សំឡេងខ្មែរ (Edge TTS)")
    voice_map = {
        "male": st.selectbox(
            "♂ តួប្រុស", list(core.EDGE_VOICES), index=0,
            format_func=lambda v: core.EDGE_VOICES[v], key="v_male",
        ),
        "female": st.selectbox(
            "♀ តួស្រី", list(core.EDGE_VOICES), index=1,
            format_func=lambda v: core.EDGE_VOICES[v], key="v_female",
        ),
        "narrator": st.selectbox(
            "🎤 អ្នកនាំរឿង", list(core.EDGE_VOICES), index=0,
            format_func=lambda v: core.EDGE_VOICES[v], key="v_narr",
        ),
    }
    rate_pct = st.slider("ល្បឿននិយាយ", -30, 50, 0, 5, format="%d%%")
    narrator_pitch = st.slider("កម្រិតសំឡេងអ្នកនាំរឿង (Pitch)", -30, 30, -10, 5, format="%dHz")
    max_speedup = st.slider("បង្កើនល្បឿនអតិបរមា ពេលឃ្លាវែងពេក", 1.0, 2.0, 1.4, 0.05, format="%.2fx")
    orig_vol = st.slider("សំឡេងដើម (ខាងក្រោយ)", 0.0, 1.0, 0.12, 0.02,
                         help="0 = បិទសំឡេងដើមទាំងស្រុង")
    st.caption("💡 Edge TTS ត្រូវការអ៊ីនធឺណិត។ បើវាមិនដំណើរការ កម្មវិធីនឹងប្រើ Google TTS (សំឡេងតែមួយ) ជំនួស។")

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
<div class="brand">
  <div class="logo"><div>🎬</div></div>
  <div>
    <h1>MOVIE TIME STUDIO PRO <span class="badge">AI DUBBING</span></h1>
    <p>ប្រព័ន្ធស្វ័យប្រវត្តិបកប្រែវីដេអូ និងបញ្ចូលសំឡេងរឿងភាគជាភាសាខ្មែរ</p>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

problems = []
if not core.ffmpeg_available():
    problems.append("រកមិនឃើញ ffmpeg (ត្រូវដាក់ `ffmpeg` ក្នុងឯកសារ packages.txt)")
pills = [
    f'<span class="pill {"" if api_key else "warn"}">Gemini key: <b>{"បានដាក់" if api_key else "មិនទាន់មាន"}</b></span>',
    f'<span class="pill">ម៉ូដែល: <b>{model}</b></span>',
    f'<span class="pill">ffmpeg: <b>{"OK" if core.ffmpeg_available() else "មិនមាន"}</b></span>',
]
st.markdown("".join(pills), unsafe_allow_html=True)
for p in problems:
    st.error(p)

# ---------------------------------------------------------------------------
# ផ្ទុកឯកសារ
# ---------------------------------------------------------------------------
left, right = st.columns([1, 2], gap="large")

with left:
    st.markdown("##### 📺 វីដេអូ")
    up = st.file_uploader(
        "ទម្លាក់វីដេអូ ឬ Audio នៅទីនេះ",
        type=["mp4", "mkv", "mov", "ts", "avi", "webm", "mp3", "wav", "m4a", "aac", "ogg"],
        label_visibility="collapsed",
    )
    if up is not None:
        sig = (up.name, up.size)
        if st.session_state.media_sig != sig:
            suffix = Path(up.name).suffix.lower() or ".mp4"
            dst = WORK / f"input{suffix}"
            with open(dst, "wb") as f:
                while True:
                    buf = up.read(8 * 1024 * 1024)
                    if not buf:
                        break
                    f.write(buf)
            st.session_state.media_path = str(dst)
            st.session_state.media_name = up.name
            st.session_state.media_sig = sig
            st.session_state.duration = core.probe_duration(dst)
            st.session_state.is_video = core.has_video(dst)
            st.session_state.size = core.video_size(dst) if st.session_state.is_video else "-"
            st.session_state.export_path = None

    media = Path(st.session_state.media_path) if st.session_state.media_path else None
    if media and media.exists():
        if st.session_state.is_video:
            st.video(str(media))
        else:
            st.audio(str(media))
        st.markdown(
            f"""
<div class="panel meta">
ឈ្មោះឯកសារ: <span>{st.session_state.media_name}</span><br>
រយៈពេលសរុប: <span>{core.fmt_clock(st.session_state.duration)}</span><br>
កម្រិតរូបភាព: <span>{st.session_state.size}</span><br>
ចំនួនឃ្លាសន្ទនា: <span>{len(st.session_state.df)} ឃ្លា</span>
</div>""",
            unsafe_allow_html=True,
        )
    else:
        st.info("សូមផ្ទុកវីដេអូ ឬ Audio ជាមុនសិន ឬបើកឯកសារ SRT នៅខាងស្តាំ។")

# ---------------------------------------------------------------------------
# Script editor
# ---------------------------------------------------------------------------
with right:
    st.markdown("##### 📝 ស្គ្រីបបកប្រែ (កែប្រែបានដោយផ្ទាល់ក្នុងតារាង)")

    b1, b2, b3, b4 = st.columns(4)

    if b1.button("🎤 ចាប់សំឡេង + បកប្រែខ្មែរ", type="primary", use_container_width=True,
                 disabled=not (media and api_key and core.ffmpeg_available())):
        bar = st.progress(0.0, text="កំពុងចាប់ផ្តើម...")
        try:
            client = core.get_client(api_key)
            df = core.transcribe_translate(
                client, model, media, src_lang, WORK,
                progress=lambda p, t: bar.progress(min(p, 1.0), text=t),
            )
            if df.empty:
                st.warning("រកមិនឃើញសំឡេងនិយាយក្នុងឯកសារនេះទេ។")
            else:
                st.session_state.df = df
                st.session_state.editor_rev += 1
                st.success(f"បានចាប់ {len(df)} ឃ្លា។ សូមពិនិត្យ និងកែក្នុងតារាងខាងក្រោម។")
        except Exception as e:
            st.error(f"មានបញ្ហា: {e}")
        finally:
            bar.empty()

    if b2.button("🌐 បកប្រែឡើងវិញ (ពីអត្ថបទដើម)", use_container_width=True,
                 disabled=not (api_key and len(st.session_state.df) > 0)):
        d = core.clean_df(st.session_state.df)
        todo = d.index[d["original"] != ""].tolist()
        if not todo:
            st.warning("មិនមានអត្ថបទដើមសម្រាប់បកប្រែទេ។")
        else:
            bar = st.progress(0.0, text="កំពុងចាប់ផ្តើម...")
            try:
                client = core.get_client(api_key)
                res = core.translate_lines(
                    client, model, d.loc[todo, "original"].tolist(), src_lang,
                    progress=lambda p, t: bar.progress(min(p, 1.0), text=t),
                )
                d.loc[todo, "khmer"] = res
                st.session_state.df = d
                st.session_state.editor_rev += 1
                st.success("បកប្រែរួចរាល់។")
            except Exception as e:
                st.error(f"មានបញ្ហា: {e}")
            finally:
                bar.empty()

    srt_up = b3.file_uploader("បើក SRT", type=["srt"], label_visibility="collapsed", key="srt_up")
    if srt_up is not None and st.session_state.get("srt_sig") != (srt_up.name, srt_up.size):
        st.session_state.srt_sig = (srt_up.name, srt_up.size)
        raw = srt_up.getvalue()
        for enc in ("utf-8-sig", "utf-16", "gb18030", "latin-1"):
            try:
                txt = raw.decode(enc)
                break
            except Exception:
                continue
        items = core.parse_srt(txt)
        if not items:
            st.error("អាចអានឯកសារ SRT មិនបាន។")
        else:
            as_khmer = any("ក" <= ch <= "៿" for it in items[:5] for ch in it["text"])
            rows = [
                {
                    "start": it["start"], "end": it["end"], "speaker": core.DEFAULT_SPEAKER,
                    "original": "" if as_khmer else it["text"],
                    "khmer": it["text"] if as_khmer else "",
                }
                for it in items
            ]
            st.session_state.df = core.clean_df(pd.DataFrame(rows, columns=core.COLUMNS))
            st.session_state.editor_rev += 1
            st.success(f"បាននាំចូល {len(items)} ឃ្លា "
                       f"({'ខ្មែរ' if as_khmer else 'ភាសាដើម → សូមចុច បកប្រែឡើងវិញ'})")

    if b4.button("🧹 សម្អាតតារាង", use_container_width=True):
        st.session_state.df = core.empty_df()
        st.session_state.editor_rev += 1
        st.rerun()

    if len(st.session_state.df) == 0:
        if st.button("➕ ដាក់ឧទាហរណ៍ 3 ឃ្លា (សាកល្បងសំឡេង)"):
            st.session_state.df = core.demo_df()
            st.session_state.editor_rev += 1
            st.rerun()

    edited = st.data_editor(
        st.session_state.df,
        key=f"editor_{st.session_state.editor_rev}",
        num_rows="dynamic",
        use_container_width=True,
        height=380,
        hide_index=True,
        column_config={
            "start": st.column_config.NumberColumn("ចាប់ផ្តើម (វិ)", format="%.2f", min_value=0.0, step=0.1, width="small"),
            "end": st.column_config.NumberColumn("បញ្ចប់ (វិ)", format="%.2f", min_value=0.0, step=0.1, width="small"),
            "speaker": st.column_config.SelectboxColumn(
                "តួអង្គ", options=list(core.SPEAKER_KEYS), required=True, width="small"),
            "original": st.column_config.TextColumn("អត្ថបទដើម", width="medium"),
            "khmer": st.column_config.TextColumn("អត្ថបទបកប្រែខ្មែរ (ស្គ្រីបសំឡេង)", width="large"),
        },
    )
    cur = core.clean_df(edited)
    st.session_state.df = cur
    st.caption(f"សរុប **{len(cur)}** ឃ្លា")

    d1, d2, d3 = st.columns(3)
    d1.download_button(
        "⬇️ SRT ខ្មែរ", core.to_srt(cur, "khmer").encode("utf-8-sig"),
        file_name="khmer.srt", mime="application/x-subrip", use_container_width=True,
        disabled=cur.empty,
    )
    d2.download_button(
        "⬇️ SRT ភាសាដើម", core.to_srt(cur, "original").encode("utf-8-sig"),
        file_name="original.srt", mime="application/x-subrip", use_container_width=True,
        disabled=cur.empty,
    )
    d3.download_button(
        "💾 Project (CSV)", cur.to_csv(index=False).encode("utf-8-sig"),
        file_name="project.csv", mime="text/csv", use_container_width=True,
        disabled=cur.empty,
    )

# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------
st.markdown("##### 🎞️ Timeline សំឡេងខ្មែរ")
cur = st.session_state.df
total = max(st.session_state.duration, float(cur["end"].max()) if len(cur) else 0.0, 1.0)
segs = []
for _, r in cur.iterrows():
    if not r["khmer"]:
        continue
    key = core.SPEAKER_KEYS.get(r["speaker"], "narrator")
    left_pct = r["start"] / total * 100
    width_pct = max((r["end"] - r["start"]) / total * 100, 0.6)
    txt = (r["khmer"][:40]).replace("<", "&lt;").replace(">", "&gt;")
    segs.append(
        f'<div class="seg {key}" style="left:{left_pct:.2f}%;width:{width_pct:.2f}%" '
        f'title="{r["start"]:.1f}s - {r["end"]:.1f}s">{txt}</div>'
    )
st.markdown(
    f"""<div class="track">
<div class="lbl">Khmer AI Dub · 0:00 → {core.fmt_clock(total)}  (ត្នោត = ប្រុស, ផ្កាឈូក = ស្រី, បៃតង = អ្នកនាំរឿង)</div>
<div class="row">{''.join(segs)}</div></div>""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
st.markdown("##### 🎬 Export វីដេអូចុងក្រោយ")
ex1, ex2 = st.columns([1, 2])

with ex1:
    # សាកល្បងសំឡេងឃ្លាដំបូង
    if st.button("🔊 សាកល្បងសំឡេង (ឃ្លាដំបូង)", use_container_width=True,
                 disabled=not (cur["khmer"] != "").any() if len(cur) else True):
        try:
            first = cur[cur["khmer"] != ""].iloc[0]
            key = core.SPEAKER_KEYS.get(first["speaker"], "narrator")
            clip = core.tts_clip(
                first["khmer"], voice_map[key], rate_pct,
                narrator_pitch if key == "narrator" else 0, WORK / "tts_cache",
            )
            st.audio(str(clip))
        except Exception as e:
            st.error(f"{e}")

can_export = bool(media and media.exists() and (cur["khmer"] != "").any() and core.ffmpeg_available()) if len(cur) else False

with ex2:
    if st.button("🚀 បង្កើតសំឡេងខ្មែរ និង Export (MP4)", type="primary",
                 use_container_width=True, disabled=not can_export):
        bar = st.progress(0.0, text="កំពុងចាប់ផ្តើម...")
        try:
            dub = WORK / "khmer_dub.wav"
            n = core.build_dub_track(
                cur, dub, WORK / "tts_cache", voice_map, rate_pct, narrator_pitch,
                max_speedup, st.session_state.duration,
                progress=lambda p, t: bar.progress(min(p * 0.85, 0.85), text=t),
            )
            bar.progress(0.9, text="កំពុងលាយសំឡេងចូលវីដេអូ...")
            ext = ".mp4" if st.session_state.is_video else ".m4a"
            out = WORK / f"movie_khmer_dub{ext}"
            core.mux_dub(media, dub, out, orig_vol)
            st.session_state.export_path = str(out)
            bar.progress(1.0, text="រួចរាល់!")
            st.success(f"បានដាក់សំឡេងខ្មែរ {n} ឃ្លា។")
        except Exception as e:
            st.error(f"មានបញ្ហា: {e}")
        finally:
            bar.empty()

    if not can_export:
        st.caption("ត្រូវការ៖ ឯកសារវីដេអូ/សំឡេង + អត្ថបទខ្មែរយ៉ាងហោចណាស់ ១ ឃ្លា")

ep = Path(st.session_state.export_path) if st.session_state.export_path else None
if ep and ep.exists():
    if st.session_state.is_video:
        st.video(str(ep))
    else:
        st.audio(str(ep))
    with open(ep, "rb") as f:
        st.download_button(
            "⬇️ ទាញយកលទ្ធផល", f, file_name=ep.name,
            mime="video/mp4" if ep.suffix == ".mp4" else "audio/mp4",
            type="primary",
        )
    dub_wav = WORK / "khmer_dub.wav"
    if dub_wav.exists():
        with open(dub_wav, "rb") as f:
            st.download_button("⬇️ ទាញយកតែសំឡេងខ្មែរ (WAV)", f, file_name="khmer_dub.wav", mime="audio/wav")
