"""
Movie Time Studio Pro - AI Khmer Auto Dubbing (Streamlit) - ឯកសារតែមួយ
"""
from __future__ import annotations


import asyncio
import hashlib
import json
import math
import re
import shutil
import subprocess
import time
import wave
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# ថេរ (constants)
# ---------------------------------------------------------------------------
SPEAKER_LABELS = {"male": "ប្រុស", "female": "ស្រី", "narrator": "អ្នកនាំរឿង"}
SPEAKER_KEYS = {v: k for k, v in SPEAKER_LABELS.items()}
DEFAULT_SPEAKER = SPEAKER_LABELS["narrator"]

COLUMNS = ["start", "end", "speaker", "original", "khmer"]

EDGE_VOICES = {
    "km-KH-PisethNeural": "ពិសិដ្ឋ (Piseth) - សំឡេងប្រុស",
    "km-KH-SreymomNeural": "ស្រីមុំ (Sreymom) - សំឡេងស្រី",
}

SOURCE_LANGS = {
    "ចិន (Chinese)": "Chinese",
    "អង់គ្លេស (English)": "English",
    "កូរ៉េ (Korean)": "Korean",
    "ជប៉ុន (Japanese)": "Japanese",
    "ថៃ (Thai)": "Thai",
    "ស្វ័យប្រវត្តិ (Auto-detect)": "the original language (detect it automatically)",
}

TTS_SR = 24000  # sample rate នៃបទសំឡេងខ្មែរ


# ---------------------------------------------------------------------------
# DataFrame helpers
# ---------------------------------------------------------------------------
def empty_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "start": pd.Series(dtype="float64"),
            "end": pd.Series(dtype="float64"),
            "speaker": pd.Series(dtype="object"),
            "original": pd.Series(dtype="object"),
            "khmer": pd.Series(dtype="object"),
        }
    )


def clean_df(df: Optional[pd.DataFrame]) -> pd.DataFrame:
    """ធ្វើឲ្យតារាងស្អាត: ប្រភេទទិន្នន័យត្រឹមត្រូវ, លុបជួរទទេ, តម្រៀបតាមពេលវេលា"""
    if df is None or len(df) == 0:
        return empty_df()
    d = df.copy()
    for c in COLUMNS:
        if c not in d.columns:
            d[c] = None
    d = d[COLUMNS]
    d["start"] = pd.to_numeric(d["start"], errors="coerce")
    d["end"] = pd.to_numeric(d["end"], errors="coerce")
    for c in ("original", "khmer"):
        d[c] = d[c].fillna("").astype(str).str.strip()
    d["speaker"] = d["speaker"].where(d["speaker"].isin(SPEAKER_KEYS), DEFAULT_SPEAKER)
    # ជួរដែលគ្មានអត្ថបទទាំងពីរ ត្រូវលុប
    d = d[(d["original"] != "") | (d["khmer"] != "")]
    d["start"] = d["start"].fillna(0.0).clip(lower=0.0)
    d["end"] = d["end"].fillna(d["start"] + 2.0)
    d["end"] = np.maximum(d["end"], d["start"] + 0.3)
    d = d.sort_values("start", kind="stable").reset_index(drop=True)
    return d


def demo_df() -> pd.DataFrame:
    rows = [
        (0.5, 3.5, "ប្រុស", "你好，你过得好吗？", "សួស្តី តើអ្នកសុខសប្បាយជាទេ?"),
        (4.0, 6.5, "ស្រី", "我很好，谢谢。", "ខ្ញុំសុខសប្បាយ អរគុណ។"),
        (7.0, 10.0, "អ្នកនាំរឿង", "我们一起去看电影吧！", "តោះទៅមើលរឿងជាមួយគ្នា!"),
    ]
    return clean_df(pd.DataFrame(rows, columns=COLUMNS))


# ---------------------------------------------------------------------------
# SRT
# ---------------------------------------------------------------------------
def fmt_srt_time(sec: float) -> str:
    ms = int(round(max(0.0, float(sec)) * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def fmt_clock(sec: float) -> str:
    sec = max(0.0, float(sec))
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


_SRT_TIME = re.compile(
    r"\s*(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)"
)


def _to_sec(h: str, m: str, s: str, frac: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(frac) / (10 ** len(frac))


def parse_srt(text: str) -> list[dict]:
    text = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("﻿")
    out: list[dict] = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = block.split("\n")
        idx = next((i for i, ln in enumerate(lines) if "-->" in ln), None)
        if idx is None:
            continue
        m = _SRT_TIME.match(lines[idx])
        if not m:
            continue
        g = m.groups()
        start = _to_sec(*g[0:4])
        end = _to_sec(*g[4:8])
        body = " ".join(ln.strip() for ln in lines[idx + 1:] if ln.strip())
        body = re.sub(r"<[^>]+>", "", body).strip()
        if body:
            out.append({"start": start, "end": end, "text": body})
    return out


def to_srt(df: pd.DataFrame, prefer: str = "khmer") -> str:
    d = clean_df(df)
    parts = []
    n = 0
    for _, r in d.iterrows():
        text = r[prefer] or r["original" if prefer == "khmer" else "khmer"]
        if not text:
            continue
        n += 1
        parts.append(
            f"{n}\n{fmt_srt_time(r['start'])} --> {fmt_srt_time(r['end'])}\n{text}\n"
        )
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# ffmpeg helpers
# ---------------------------------------------------------------------------
def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True)


def probe_duration(path: Path | str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True,
    )
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def _has_stream(path: Path | str, kind: str) -> bool:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", kind,
         "-show_entries", "stream=index", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    )
    return bool(r.stdout.strip())


def has_audio(path: Path | str) -> bool:
    return _has_stream(path, "a")


def has_video(path: Path | str) -> bool:
    # រូបភាពក្របមុខ (cover art) របស់ mp3 ក៏ជា video stream ដែរ ដូច្នេះពិនិត្យថា codec មិនមែន mjpeg/png
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
         "stream=codec_name", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    )
    codecs = [c.strip() for c in r.stdout.split() if c.strip()]
    return any(c not in ("mjpeg", "png", "bmp", "gif") for c in codecs)


def video_size(path: Path | str) -> str:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height", "-of", "csv=s=x:p=0", str(path)],
        capture_output=True, text=True,
    )
    return r.stdout.strip() or "-"


def extract_audio_chunk(src: Path, dst: Path, start: float, length: float) -> None:
    r = _run(
        ["ffmpeg", "-y", "-v", "error", "-ss", f"{start:.3f}", "-t", f"{length:.3f}",
         "-i", str(src), "-vn", "-ac", "1", "-ar", "16000", "-b:a", "48k", str(dst)]
    )
    if r.returncode != 0 or not dst.exists() or dst.stat().st_size == 0:
        raise RuntimeError("ទាញសំឡេងពីវីដេអូមិនបាន: " + r.stderr.decode(errors="ignore")[-400:])


# ---------------------------------------------------------------------------
# Gemini
# ---------------------------------------------------------------------------
TRANSCRIBE_PROMPT = """You are a professional subtitle translator and dubbing-script writer.
Listen to this audio. The spoken language is: {lang}.
Transcribe every spoken line, then translate it into natural, spoken Khmer that is suitable
for dubbing a movie or drama: short, conversational, keeping the emotion and meaning
(never translate word-for-word, and use polite pronouns that fit the characters).

Return ONLY a JSON array. Each item must have exactly these keys:
  "start": start time in seconds (number, relative to the beginning of THIS audio),
  "end": end time in seconds (number),
  "speaker": one of "male", "female", "narrator",
  "original": the transcript in the original language,
  "khmer": the Khmer translation.
Keep each line under about 12 seconds. Ignore music and noise that has no speech.
If there is no speech at all, return []."""

TRANSLATE_PROMPT = """Translate each of the following {lang} lines into natural, spoken Khmer
suitable for dubbing a movie or drama (short, conversational, keep the emotion; not word-for-word).
Return ONLY a JSON array of Khmer strings, in exactly the same order and with exactly {n} items.

Lines (JSON):
{lines}"""


def get_client(api_key: str):
    from google import genai  # នាំចូលពេលប្រើ ដើម្បីឲ្យ កម្មវិធីសាកល្បងបានដោយគ្មាន SDK

    return genai.Client(api_key=api_key)


def parse_json_loose(text: str):
    t = (text or "").strip()
    t = re.sub(r"^```(?:json)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    return json.loads(t)


def _wait_active(client, f, timeout: float = 180.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        f = client.files.get(name=f.name)
        state = getattr(getattr(f, "state", None), "name", None) or str(getattr(f, "state", ""))
        if state in ("", "None", "ACTIVE"):
            return f
        if state == "FAILED":
            raise RuntimeError("Gemini ដំណើរការឯកសារសំឡេងមិនបាន (FAILED)")
        time.sleep(2)
    raise RuntimeError("Gemini ដំណើរការឯកសារយូរពេក (timeout)")


def _normalize_items(items, offset: float) -> list[dict]:
    rows = []
    if isinstance(items, dict):
        items = items.get("lines") or items.get("segments") or []
    for it in items or []:
        if not isinstance(it, dict):
            continue
        try:
            s = float(it.get("start", 0)) + offset
            e = float(it.get("end", s + 2)) + offset
        except (TypeError, ValueError):
            continue
        spk = str(it.get("speaker", "narrator")).strip().lower()
        rows.append(
            {
                "start": s,
                "end": max(e, s + 0.3),
                "speaker": SPEAKER_LABELS.get(spk, DEFAULT_SPEAKER),
                "original": str(it.get("original", "") or "").strip(),
                "khmer": str(it.get("khmer", "") or "").strip(),
            }
        )
    return rows


def transcribe_translate(
    client,
    model: str,
    media: Path,
    lang_name: str,
    workdir: Path,
    chunk_seconds: int = 600,
    progress: Optional[Callable[[float, str], None]] = None,
) -> pd.DataFrame:
    from google.genai import types

    total = probe_duration(media)
    if total <= 0:
        raise RuntimeError("អានរយៈពេលឯកសារមិនបាន")
    n = max(1, math.ceil(total / chunk_seconds))
    rows: list[dict] = []
    for i in range(n):
        off = i * chunk_seconds
        if progress:
            progress(i / n, f"កំពុងចាប់សំឡេង និងបកប្រែ ផ្នែក {i + 1}/{n}")
        chunk = workdir / f"chunk_{i}.mp3"
        extract_audio_chunk(media, chunk, off, chunk_seconds)
        uploaded = client.files.upload(file=str(chunk))
        try:
            uploaded = _wait_active(client, uploaded)
            last_err: Exception | None = None
            items = None
            for attempt in range(3):
                try:
                    resp = client.models.generate_content(
                        model=model,
                        contents=[uploaded, TRANSCRIBE_PROMPT.format(lang=lang_name)],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json", temperature=0.3
                        ),
                    )
                    items = parse_json_loose(resp.text)
                    break
                except Exception as e:  # JSON មិនត្រឹមត្រូវ ឬ API កំហុសបណ្តោះអាសន្ន
                    last_err = e
                    time.sleep(2 * (attempt + 1))
            if items is None:
                raise RuntimeError(f"Gemini មិនឆ្លើយត្រឹមត្រូវ: {last_err}")
            rows.extend(_normalize_items(items, off))
        finally:
            try:
                client.files.delete(name=uploaded.name)
            except Exception:
                pass
    if progress:
        progress(1.0, "ចាប់សំឡេង និងបកប្រែរួចរាល់")
    return clean_df(pd.DataFrame(rows, columns=COLUMNS))


def translate_lines(
    client,
    model: str,
    lines: list[str],
    lang_name: str,
    batch: int = 40,
    progress: Optional[Callable[[float, str], None]] = None,
) -> list[str]:
    from google.genai import types

    out: list[str] = []
    for b in range(0, len(lines), batch):
        part = lines[b:b + batch]
        if progress:
            progress(b / max(1, len(lines)), f"កំពុងបកប្រែ {b + 1}-{b + len(part)} / {len(lines)}")
        prompt = TRANSLATE_PROMPT.format(
            lang=lang_name, n=len(part), lines=json.dumps(part, ensure_ascii=False)
        )
        result = None
        last_err: Exception | None = None
        for attempt in range(3):
            try:
                resp = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json", temperature=0.3
                    ),
                )
                data = parse_json_loose(resp.text)
                if isinstance(data, list) and len(data) == len(part):
                    result = [str(x) for x in data]
                    break
                last_err = ValueError(f"ចំនួនឃ្លាមិនត្រូវគ្នា ({len(data)} ≠ {len(part)})")
            except Exception as e:
                last_err = e
            time.sleep(2 * (attempt + 1))
        if result is None:
            raise RuntimeError(f"បកប្រែមិនបាន: {last_err}")
        out.extend(result)
    if progress:
        progress(1.0, "បកប្រែរួចរាល់")
    return out


# ---------------------------------------------------------------------------
# TTS
# ---------------------------------------------------------------------------
def _run_async(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(1) as ex:
        return ex.submit(asyncio.run, coro).result()


async def _edge_save(text: str, voice: str, rate: str, pitch: str, out: str) -> None:
    import edge_tts

    await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(out)


def tts_clip(
    text: str, voice: str, rate_pct: int, pitch_hz: int, cache_dir: Path
) -> Path:
    """បង្កើតឯកសារសំឡេង mp3 សម្រាប់ឃ្លាមួយ (មាន cache)"""
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(f"{voice}|{rate_pct}|{pitch_hz}|{text}".encode()).hexdigest()
    out = cache_dir / f"{key}.mp3"
    if out.exists() and out.stat().st_size > 0:
        return out
    rate = f"{int(rate_pct):+d}%"
    pitch = f"{int(pitch_hz):+d}Hz"
    edge_err: Exception | None = None
    for attempt in range(2):
        try:
            _run_async(_edge_save(text, voice, rate, pitch, str(out)))
            if out.exists() and out.stat().st_size > 0:
                return out
        except Exception as e:
            edge_err = e
            time.sleep(1.5)
    # ផ្លូវបម្រុង: Google TTS (សំឡេងតែមួយ មិនអាចជ្រើសប្រុស/ស្រី)
    try:
        from gtts import gTTS

        gTTS(text=text, lang="km").save(str(out))
        if out.exists() and out.stat().st_size > 0:
            return out
    except Exception as e:
        raise RuntimeError(
            f"បង្កើតសំឡេងខ្មែរមិនបាន។ Edge TTS: {edge_err} | gTTS: {e}"
        ) from e
    raise RuntimeError(f"បង្កើតសំឡេងខ្មែរមិនបាន: {edge_err}")


def decode_clip(path: Path, tempo: float = 1.0, sr: int = TTS_SR) -> np.ndarray:
    cmd = ["ffmpeg", "-v", "error", "-i", str(path)]
    if abs(tempo - 1.0) > 0.01:
        cmd += ["-af", f"atempo={min(max(tempo, 0.5), 2.0):.3f}"]
    cmd += ["-ac", "1", "-ar", str(sr), "-f", "s16le", "-"]
    r = _run(cmd)
    if r.returncode != 0 or not r.stdout:
        raise RuntimeError("ឌីកូដសំឡេងមិនបាន: " + r.stderr.decode(errors="ignore")[-300:])
    return np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32) / 32768.0


def write_wav(path: Path, samples: np.ndarray, sr: int = TTS_SR) -> None:
    pcm = (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def build_dub_track(
    df: pd.DataFrame,
    out_wav: Path,
    cache_dir: Path,
    voices: dict[str, str],
    rate_pct: int,
    narrator_pitch: int,
    max_speedup: float,
    total_seconds: float,
    clip_fn: Callable[[str, str, int, int, Path], Path] = tts_clip,
    progress: Optional[Callable[[float, str], None]] = None,
) -> int:
    """
    បង្កើតបទសំឡេងខ្មែរមួយ (wav) ដោយដាក់ឃ្លានីមួយៗតាមពេលចាប់ផ្តើមរបស់វា។
    ប្រសិនបើសំឡេងវែងជាងចន្លោះដែលមាន នឹងបង្កើនល្បឿន (atempo) រហូតដល់ max_speedup។
    ត្រឡប់ចំនួនឃ្លាដែលបានដាក់។
    """
    d = clean_df(df)
    d = d[d["khmer"] != ""].reset_index(drop=True)
    if d.empty:
        raise RuntimeError("មិនមានអត្ថបទខ្មែរសម្រាប់បង្កើតសំឡេងទេ")

    last_end = float(d["end"].max())
    track = np.zeros(int((max(total_seconds, last_end) + 5) * TTS_SR), dtype=np.float32)
    max_pos = 0  # ចុងសំឡេងបំផុត (sample) ដើម្បីកាត់ស្ងាត់ដែលលើសចេញ

    for i, r in d.iterrows():
        if progress:
            progress(i / len(d), f"កំពុងបង្កើតសំឡេងខ្មែរ {i + 1}/{len(d)}")
        key = SPEAKER_KEYS.get(r["speaker"], "narrator")
        pitch = narrator_pitch if key == "narrator" else 0
        clip = clip_fn(r["khmer"], voices[key], rate_pct, pitch, cache_dir)
        audio = decode_clip(clip)
        dur = len(audio) / TTS_SR

        start = float(r["start"])
        slot = max(float(r["end"]) - start, 0.3)
        if i + 1 < len(d):
            available = max(slot, float(d.loc[i + 1, "start"]) - start - 0.05)
        else:
            available = slot + 2.0
        if dur > available:
            tempo = min(dur / available, max_speedup)
            if tempo > 1.01:
                audio = decode_clip(clip, tempo=tempo)

        pos = int(start * TTS_SR)
        end_pos = pos + len(audio)
        if end_pos > len(track):
            track = np.concatenate([track, np.zeros(end_pos - len(track) + TTS_SR, np.float32)])
        track[pos:end_pos] += audio
        max_pos = max(max_pos, end_pos)

    keep = max(int(total_seconds * TTS_SR), max_pos)
    track = track[:keep]
    peak = float(np.max(np.abs(track)))
    if peak > 1.0:
        track = track / peak
    write_wav(out_wav, track)
    if progress:
        progress(1.0, "បង្កើតសំឡេងខ្មែររួចរាល់")
    return len(d)


# ---------------------------------------------------------------------------
# Mux: លាយសំឡេងខ្មែរចូលវីដេអូ
# ---------------------------------------------------------------------------
def mux_dub(
    media: Path,
    dub_wav: Path,
    out_path: Path,
    orig_volume: float,
) -> Path:
    """
    media មានរូបភាព  -> out_path (.mp4) រូបភាពដើម + សំឡេងដើម (ស្រាល) + សំឡេងខ្មែរ
    media ជា audio  -> out_path (.m4a)
    """
    keep_orig = orig_volume > 0.0 and has_audio(media)
    video = has_video(media)

    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(media), "-i", str(dub_wav)]
    if keep_orig:
        fc = (
            f"[0:a]volume={orig_volume:.2f}[o];"
            "[1:a]volume=1.0[d];"
            "[o][d]amix=inputs=2:duration=longest:normalize=0[a]"
        )
        cmd += ["-filter_complex", fc, "-map", "[a]"]
    else:
        cmd += ["-map", "1:a"]

    if video:
        base = cmd + ["-map", "0:v:0"]
        attempt1 = base + ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                           "-movflags", "+faststart", str(out_path)]
        r = _run(attempt1)
        if r.returncode != 0:
            attempt2 = base + ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                               "-shortest", "-movflags", "+faststart", str(out_path)]
            r = _run(attempt2)
    else:
        r = _run(cmd + ["-c:a", "aac", "-b:a", "192k", str(out_path)])

    if r.returncode != 0 or not out_path.exists():
        raise RuntimeError("Export មិនបាន: " + r.stderr.decode(errors="ignore")[-500:])
    return out_path


# ===========================================================================
# ផ្នែក UI (Streamlit)
# ===========================================================================

import os
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st


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
    "df": empty_df(),
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

    src_label = st.selectbox("ភាសាដើមក្នុងវីដេអូ", list(SOURCE_LANGS.keys()))
    src_lang = SOURCE_LANGS[src_label]

    st.divider()
    st.markdown("### 🎙️ សំឡេងខ្មែរ (Edge TTS)")
    voice_map = {
        "male": st.selectbox(
            "♂ តួប្រុស", list(EDGE_VOICES), index=0,
            format_func=lambda v: EDGE_VOICES[v], key="v_male",
        ),
        "female": st.selectbox(
            "♀ តួស្រី", list(EDGE_VOICES), index=1,
            format_func=lambda v: EDGE_VOICES[v], key="v_female",
        ),
        "narrator": st.selectbox(
            "🎤 អ្នកនាំរឿង", list(EDGE_VOICES), index=0,
            format_func=lambda v: EDGE_VOICES[v], key="v_narr",
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
if not ffmpeg_available():
    problems.append("រកមិនឃើញ ffmpeg (ត្រូវដាក់ `ffmpeg` ក្នុងឯកសារ packages.txt)")
pills = [
    f'<span class="pill {"" if api_key else "warn"}">Gemini key: <b>{"បានដាក់" if api_key else "មិនទាន់មាន"}</b></span>',
    f'<span class="pill">ម៉ូដែល: <b>{model}</b></span>',
    f'<span class="pill">ffmpeg: <b>{"OK" if ffmpeg_available() else "មិនមាន"}</b></span>',
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
            st.session_state.duration = probe_duration(dst)
            st.session_state.is_video = has_video(dst)
            st.session_state.size = video_size(dst) if st.session_state.is_video else "-"
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
រយៈពេលសរុប: <span>{fmt_clock(st.session_state.duration)}</span><br>
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
                 disabled=not (media and api_key and ffmpeg_available())):
        bar = st.progress(0.0, text="កំពុងចាប់ផ្តើម...")
        try:
            client = get_client(api_key)
            df = transcribe_translate(
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
        d = clean_df(st.session_state.df)
        todo = d.index[d["original"] != ""].tolist()
        if not todo:
            st.warning("មិនមានអត្ថបទដើមសម្រាប់បកប្រែទេ។")
        else:
            bar = st.progress(0.0, text="កំពុងចាប់ផ្តើម...")
            try:
                client = get_client(api_key)
                res = translate_lines(
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
        items = parse_srt(txt)
        if not items:
            st.error("អាចអានឯកសារ SRT មិនបាន។")
        else:
            as_khmer = any("ក" <= ch <= "៿" for it in items[:5] for ch in it["text"])
            rows = [
                {
                    "start": it["start"], "end": it["end"], "speaker": DEFAULT_SPEAKER,
                    "original": "" if as_khmer else it["text"],
                    "khmer": it["text"] if as_khmer else "",
                }
                for it in items
            ]
            st.session_state.df = clean_df(pd.DataFrame(rows, columns=COLUMNS))
            st.session_state.editor_rev += 1
            st.success(f"បាននាំចូល {len(items)} ឃ្លា "
                       f"({'ខ្មែរ' if as_khmer else 'ភាសាដើម → សូមចុច បកប្រែឡើងវិញ'})")

    if b4.button("🧹 សម្អាតតារាង", use_container_width=True):
        st.session_state.df = empty_df()
        st.session_state.editor_rev += 1
        st.rerun()

    if len(st.session_state.df) == 0:
        if st.button("➕ ដាក់ឧទាហរណ៍ 3 ឃ្លា (សាកល្បងសំឡេង)"):
            st.session_state.df = demo_df()
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
                "តួអង្គ", options=list(SPEAKER_KEYS), required=True, width="small"),
            "original": st.column_config.TextColumn("អត្ថបទដើម", width="medium"),
            "khmer": st.column_config.TextColumn("អត្ថបទបកប្រែខ្មែរ (ស្គ្រីបសំឡេង)", width="large"),
        },
    )
    cur = clean_df(edited)
    st.session_state.df = cur
    st.caption(f"សរុប **{len(cur)}** ឃ្លា")

    d1, d2, d3 = st.columns(3)
    d1.download_button(
        "⬇️ SRT ខ្មែរ", to_srt(cur, "khmer").encode("utf-8-sig"),
        file_name="khmer.srt", mime="application/x-subrip", use_container_width=True,
        disabled=cur.empty,
    )
    d2.download_button(
        "⬇️ SRT ភាសាដើម", to_srt(cur, "original").encode("utf-8-sig"),
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
    key = SPEAKER_KEYS.get(r["speaker"], "narrator")
    left_pct = r["start"] / total * 100
    width_pct = max((r["end"] - r["start"]) / total * 100, 0.6)
    txt = (r["khmer"][:40]).replace("<", "&lt;").replace(">", "&gt;")
    segs.append(
        f'<div class="seg {key}" style="left:{left_pct:.2f}%;width:{width_pct:.2f}%" '
        f'title="{r["start"]:.1f}s - {r["end"]:.1f}s">{txt}</div>'
    )
st.markdown(
    f"""<div class="track">
<div class="lbl">Khmer AI Dub · 0:00 → {fmt_clock(total)}  (ត្នោត = ប្រុស, ផ្កាឈូក = ស្រី, បៃតង = អ្នកនាំរឿង)</div>
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
            key = SPEAKER_KEYS.get(first["speaker"], "narrator")
            clip = tts_clip(
                first["khmer"], voice_map[key], rate_pct,
                narrator_pitch if key == "narrator" else 0, WORK / "tts_cache",
            )
            st.audio(str(clip))
        except Exception as e:
            st.error(f"{e}")

can_export = bool(media and media.exists() and (cur["khmer"] != "").any() and ffmpeg_available()) if len(cur) else False

with ex2:
    if st.button("🚀 បង្កើតសំឡេងខ្មែរ និង Export (MP4)", type="primary",
                 use_container_width=True, disabled=not can_export):
        bar = st.progress(0.0, text="កំពុងចាប់ផ្តើម...")
        try:
            dub = WORK / "khmer_dub.wav"
            n = build_dub_track(
                cur, dub, WORK / "tts_cache", voice_map, rate_pct, narrator_pitch,
                max_speedup, st.session_state.duration,
                progress=lambda p, t: bar.progress(min(p * 0.85, 0.85), text=t),
            )
            bar.progress(0.9, text="កំពុងលាយសំឡេងចូលវីដេអូ...")
            ext = ".mp4" if st.session_state.is_video else ".m4a"
            out = WORK / f"movie_khmer_dub{ext}"
            mux_dub(media, dub, out, orig_vol)
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
