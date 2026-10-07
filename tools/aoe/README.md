# tools/aoe — building and checking the Persian Art of Electronics book

Everything here works from the repository root. The book itself is static output in
`site/aoe/`; private sources and build state stay in `books/aoe/`, `content/aoe/` and here.

## Preview the book

```sh
python3 -m http.server 8765 -d site
# open http://localhost:8765/aoe/  (the cover; "شروع کتاب" opens the contents)
```

Audio needs a real HTTP server (not `file://`), and the page keeps reading progress in
`localStorage` under the book's own folder path.

## Rebuild pieces

| Task | Command |
| --- | --- |
| Page map of the source PDF -> `books/aoe/sections.json` (already written by hand from the section headings) | `/path/to/skill/scripts/split_pages.py 01.pdf --sections books/aoe/sections.json --out books/aoe/pages --text-only` |
| Real Persian narration (Edge TTS; needs network) | `python3 tools/aoe/tts_fa.py content/aoe/ch01/narration.fa.json site/aoe/ch01/audio/fa` |
| Silent placeholder clips of the right length (no network) | `python3 tools/aoe/tts_fa.py content/aoe/ch01/narration.fa.json site/aoe/ch01/audio/fa --placeholder` |
| Re-apply the Persian interface patch to the engine after copying a newer one from the skill | `python3 tools/aoe/localize_engine_fa.py` (then `node --check site/aoe/lib/engine.js`) |
| Interaction walk-through of the lesson (jsdom) | `npm i --prefix tools/aoe jsdom` once, then `node tools/aoe/e2e_ch01.mjs` |

`tools/aoe/tts_fa.py` needs `pip install edge-tts mutagen`; the placeholder writer needs
`imageio-ffmpeg` (or ffmpeg on PATH) and `--placeholder` also works as the automatic fallback
when the TTS service cannot be reached, so the lesson stays playable either way.

## What the scripts do

- **`localize_engine_fa.py`** — `site/aoe/lib/engine.js` and `engine.css` are the Papermorph
  skill's engine plus a Persian patch: interface strings and aria labels in Persian, Persian
  digits in counters and on the score card, Persian digits and the Persian decimal separator
  accepted in answer boxes, Vazirmatn in the font stack, RTL cards and captions. Every
  replacement must match exactly once, so a half-patched engine stops the script instead of
  shipping quietly.
- **`tts_fa.py`** — narration JSON in, `audio/fa/<beat>.mp3` plus `timings.js` out (`dur`,
  `marks`, one caption cue per sentence). Unchanged beats are reused from the cache
  `content/aoe/ch01/narration.fa.timings.json`; finished beats are written immediately, so a
  later failure never throws away work.
- **`make_placeholder_audio.py`** — same output shape with silence: clip lengths follow the text,
  marks spread across the clip. Used by `tts_fa.py --placeholder`.
- **`e2e_ch01.mjs`** — loads the real page in jsdom with a stubbed `<audio>` and drives every
  question the way a reader does (typed answers, number keys, Enter/Space, Show answer), checks
  that a wrong first try is recorded and that the finish card agrees, then rebuilds every beat
  with `seek()` and fails on any console error. It is the book's regression test for grading and
  replay; keep it passing when the engine or the questions change.
- **`package.json`** — only exists so `jsdom` can be installed next to the test.

## Reviewing frames without a browser

This sandbox has no Chromium, so the review pass uses two small helpers outside the repository
(`~/shot-tools` in the dev environment): a jsdom harness that dumps the real
`<svg id="stage">` for any beat and moment, and a Python renderer that reshapes the Persian text
(arabic-reshaper + python-bidi) and rasterises the frame with PyMuPDF for a visual check.
Ask for them if you want them moved into `tools/aoe/` — they are development aids, not part of
the book.
