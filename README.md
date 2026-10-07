# TranTest — the Art of Electronics in Persian

Two things live here: a converter that turns the supplied PDF into a self-contained, fetchable
HTML edition, and a Persian *animated* companion book built with the
[Papermorph](https://github.com/DozenTwelve/Papermorph) skill.

```
01.pdf                   source: Chapter 1 (Foundations) of The Art of Electronics, 3rd ed.
01-fetchable.html        self-contained HTML edition of the whole PDF (text + page images)
tools/build_fetchable_html.py   builds 01-fetchable.html from 01.pdf

site/aoe/                the animated Persian book (static, no build step)
  index.html               cover + contents
  ch01/index.html          lesson 1: ولتاژ، جریان و توان (voltage, current, power)
  lib/engine.js, engine.css  lesson engine + Persian interface patch
  lib/fonts/                 Vazirmatn webfont (SIL OFL)
  ch01/audio/fa/             narration clips + timings.js
books/aoe/               private book state: BOOK.md, chapters.md, storyboards, page map
content/aoe/ch01/        narration script (narration.fa.json)
tools/aoe/               build and test helpers (see tools/aoe/README.md)
```

## Run the animated book

```sh
python3 -m http.server 8765 -d site
# open http://localhost:8765/aoe/
```

The cover opens the contents page; lesson 1 runs with narration, on-screen animation and
interactive checks (Space play/pause, ←/→ steps, `?` for the full key list).

## Where to look next

- `books/aoe/BOOK.md` — audience, conventions and the visual models for the whole book.
- `books/aoe/chapters.md` — the 16-lesson map of Chapter 1 with status.
- `books/aoe/chapters/ch01.md` — storyboard of lesson 1, the marks it uses, its verified answers.
- `tools/aoe/README.md` — how to rebuild narration, re-apply the Persian engine patch, run the
  interaction test, and preview.

The narration currently ships as silent clips of the right length (Edge TTS is unreachable from
the build environment); `python3 tools/aoe/tts_fa.py content/aoe/ch01/narration.fa.json
site/aoe/ch01/audio/fa` drops the real Persian voice in without touching the page.
