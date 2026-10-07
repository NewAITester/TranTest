#!/usr/bin/env python3
"""Generate the Persian narration clips and word-mark timings for a chapter with Edge TTS.

    python3 tools/aoe/tts_fa.py content/aoe/ch01/narration.fa.json site/aoe/ch01/audio/fa

It reads the narration JSON (`voice`, `rate`, `beats` with `[[mark]]` tags), synthesises one
MP3 per beat while recording word boundaries, and writes `audio/<lang>/timings.js` with each
clip's duration, the start time of every mark and one caption cue per sentence — the format
the lesson engine expects. Beats whose spoken text did not change are reused from the cache
(`content/<book>/chNN/narration.<lang>.timings.json`, kept out of the site).

Needs: `pip install edge-tts mutagen` and network access to the Edge TTS service. If the
service is unreachable, `--placeholder` writes silent clips of the right length instead
(`tools/aoe/make_placeholder_audio.py`) so the lesson still plays while you wait.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

MARK = re.compile(r"\[\[(\w+)\]\]")


def split_marks(raw: str) -> tuple[str, dict[str, int]]:
    marks, clean, pos = {}, [], 0
    for i, part in enumerate(MARK.split(raw)):
        if i % 2:
            if part in marks:
                raise SystemExit(f"duplicate mark {part!r} in one beat")
            marks[part] = pos
        else:
            clean.append(part)
            pos += len(part)
    return "".join(clean), marks


def time_at(clean: str, words: list[tuple[float, str]]):
    cursor, located = 0, []
    for t, w in words:
        i = clean.find(w, cursor)
        if i < 0:
            continue
        located.append((i, t))
        cursor = i + len(w)
    return lambda pos: next((round(t, 3) for i, t in located if i >= pos), None)


def mark_times(clean: str, marks: dict[str, int], words) -> dict[str, float]:
    at, out = time_at(clean, words), {}
    for name, pos in marks.items():
        out[name] = at(pos)
        if out[name] is None:
            raise SystemExit(f"mark {name!r} not matched to a spoken word")
    return out


def caption_cues(clean: str, words) -> list[list]:
    at, cues, start = time_at(clean, words), [], 0
    for m in list(re.finditer(r"[.?!؟]\s+", clean)) + [None]:
        end = m.end() if m else len(clean)
        text = clean[start:end].strip()
        if text:
            cues.append([at(start) or 0, text])
        start = end
    return cues


def duration(mp3: Path) -> float:
    try:                                         # mutagen reads MP3 headers directly
        from mutagen.mp3 import MP3
        return round(MP3(mp3).info.length, 3)
    except Exception:
        pass
    try:                                         # otherwise ask ffmpeg (from imageio-ffmpeg)
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        exe = "ffmpeg"
    r = subprocess.run([exe, "-i", str(mp3)], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
    if not m:
        raise SystemExit(f"could not read the duration of {mp3}")
    return round(int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]), 3)


async def synth(text: str, voice: str, rate: str, mp3: Path) -> list[tuple[float, str]]:
    import edge_tts
    words: list[tuple[float, str]] = []
    comm = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    with open(mp3, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append((chunk["offset"] / 1e7, chunk["text"]))
    return words


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}-", delete=False) as f:
        tmp = Path(f.name)
    try:
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def write_timings(out_dir: Path, result: dict) -> None:
    js = {b: {k: v[k] for k in ("dur", "marks", "cues")} for b, v in result.items()}
    write_atomic(out_dir / "timings.js", "window.TIMINGS = " + json.dumps(js, ensure_ascii=False, indent=1) + ";\n")


async def main(src: Path, out_dir: Path) -> None:
    spec = json.loads(src.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_path = src.with_suffix(".timings.json")
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    voice, rate = spec["voice"], spec["rate"]
    result: dict = {}
    for beat, raw in spec["beats"].items():
        clean, marks = split_marks(raw)
        mp3 = out_dir / f"{beat}.mp3"
        key = hashlib.sha1(f"{voice}|{rate}|{clean}".encode()).hexdigest()
        old = cache.get(beat)
        if old and old.get("key") == key and "words" in old and mp3.exists() and mp3.stat().st_size:
            entry = old                                   # spoken text unchanged: reuse the clip
        else:
            tmp = out_dir / f".{beat}.tmp.mp3"
            try:
                words = await synth(clean, voice, rate, tmp)
            finally:
                pass
            entry = {"key": key, "words": words}
            tmp.replace(mp3)
            print(f"{beat}: synthesized")
        entry["dur"] = duration(mp3)
        entry["marks"] = mark_times(clean, marks, entry["words"])
        entry["cues"] = caption_cues(clean, entry["words"])
        result[beat] = entry
        cache[beat] = entry
        write_atomic(cache_path, json.dumps(cache, ensure_ascii=False, indent=1))   # keep finished beats
        write_timings(out_dir, result)                   # even if a later beat fails
    write_timings(out_dir, result)
    total = sum(v["dur"] for v in result.values())
    print(f"{len(result)} beats, {total / 60:.1f} minutes of narration -> {out_dir}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("narration", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--placeholder", action="store_true",
                    help="skip the network and write silent clips of the right length instead")
    a = ap.parse_args()
    if a.placeholder:
        sys.exit(subprocess.call([sys.executable, str(Path(__file__).with_name("make_placeholder_audio.py")),
                                  str(a.narration), str(a.out_dir), "--overwrite"]))
    try:
        asyncio.run(main(a.narration, a.out_dir))
    except Exception as e:                                # network down: keep the lesson playable
        print(f"Edge TTS failed ({type(e).__name__}: {e}).", file=sys.stderr)
        print("Writing placeholder clips instead; rerun this command when the service is reachable.", file=sys.stderr)
        sys.exit(subprocess.call([sys.executable, str(Path(__file__).with_name("make_placeholder_audio.py")),
                                  str(a.narration), str(a.out_dir)]))
