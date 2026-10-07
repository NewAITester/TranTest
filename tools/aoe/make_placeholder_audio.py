#!/usr/bin/env python3
"""Write placeholder narration clips and timings for a book chapter.

    python3 tools/aoe/make_placeholder_audio.py content/aoe/ch01/narration.fa.json site/aoe/ch01/audio/fa

A freshly written chapter has no narration audio yet (that needs Edge TTS, which is not
always reachable). This tool fills `audio/<lang>/` with silent clips whose length follows
the narration text and a `timings.js` whose marks are spread over that length, so the page
plays, seeks and scores exactly like the finished lesson. Run `tools/aoe/tts_fa.py` later to
replace both with real speech. Existing clips are kept unless --overwrite is given.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

MARK = re.compile(r"\[\[(\w+)\]\]")
SENT = re.compile(r"[.?!؟]\s+")


def estimate(text: str) -> float:
    """Rough Persian speech length in seconds (Edge TTS fa-IR at -4% is about this pace)."""
    return max(2.6, len(text) / 13.5 + 1.1)


def mark_times(clean: str, marks: dict[str, int], dur: float) -> dict[str, float]:
    span = max(1.0, dur - .9)
    out, prev = {}, 0.3
    for name, pos in sorted(marks.items(), key=lambda kv: kv[1]):
        t = round(min(.3 + pos / max(1, len(clean)) * span, dur - .35), 3)
        t = round(max(t, prev + .3), 3)
        out[name], prev = t, t
    return out


def caption_cues(clean: str, dur: float) -> list[list]:
    cues, start = [], 0
    for m in list(SENT.finditer(clean)) + [None]:
        end = m.end() if m else len(clean)
        text = clean[start:end].strip()
        if text:
            cues.append([round(start / max(1, len(clean)) * dur, 3), text])
        start = end
    return cues


def silent_mp3(ffmpeg: str, path: Path, dur: float) -> None:
    subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
                    "anullsrc=r=24000:cl=mono", "-t", f"{dur:.3f}", "-b:a", "48k", "-y", str(path)],
                   check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("narration", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args()

    try:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit("pip install imageio-ffmpeg (or put ffmpeg on PATH) to write placeholder clips")

    spec = json.loads(a.narration.read_text(encoding="utf-8"))
    a.out_dir.mkdir(parents=True, exist_ok=True)
    timings, written = {}, 0
    for beat, raw in spec["beats"].items():
        clean, marks, pos = MARK.sub("", raw), {}, 0
        for i, part in enumerate(MARK.split(raw)):
            if i % 2:
                marks[part] = pos
            else:
                pos += len(part)
        dur = round(estimate(clean), 2)
        mp3 = a.out_dir / f"{beat}.mp3"
        if a.overwrite or not mp3.exists():
            silent_mp3(ffmpeg, mp3, dur)
            written += 1
        timings[beat] = {"dur": dur, "marks": mark_times(clean, marks, dur), "cues": caption_cues(clean, dur)}
    (a.out_dir / "timings.js").write_text("window.TIMINGS = " + json.dumps(timings, ensure_ascii=False, indent=1) + ";\n",
                                         encoding="utf-8")
    print(f"{len(timings)} beats: {written} placeholder clips written to {a.out_dir}, timings.js updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
