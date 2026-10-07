# هنر الکترونیک (The Art of Electronics) — کتاب فارسی — book plan

Read this compact current state for chapter work. The chapter map/status lives in `chapters.md`; storyboards, errata and feedback live in `chapters/chNN.md`.

## Intake
- Readers: self-learners and students who want an intuitive, visual first pass at electronics; no prior electronics needed. · Tone: plain, warm, teacherly, never childish. · Narration language: Persian (fa-IR), voice `fa-IR-FaridNeural`.
- Slug: `aoe` · Primary language code: `fa` · Asset approach: code/SVG only (no images, no external assets except the Vazirmatn text face).
- Guide character: the engine's infinity guide (kept).
- Source: `01.pdf` (Chapter 1: Foundations of *The Art of Electronics*, 3rd ed., 70 pages, Chapter-1 excerpt of 128 pages) · Page map: `sections.json` (9 sections, `books/aoe/pages/*/text.md` are the extracted private references) · 16 lessons planned, 1 written.
- Deliverable scope: the whole of Chapter 1, section by section, one lesson per section group. This is an educational translation — the lessons re-write the explanations, examples and drawings in Persian rather than reproducing the book's text.

## Conventions (approved in the pilot; later chapters follow them)
- Look: the engine's chalkboard (board `#1d2b27`, chalk `#ece8dc`). One colour, one meaning: voltage/task amber `COL.task`, current blue `COL.whole`, charge green `COL.good`, power coral `COL.bad`, construction lines `COL.faint`/`COL.dim`.
- Type: Persian text uses Vazirmatn (bundled in `site/aoe/lib/fonts/`); formulas use the engine's serif (`M()`), units stay plain text in `T()` so they are never italicised.
- Direction: the interface, captions and cards are RTL (`dir="rtl"`); stage labels are per-element bidi (`unicode-bidi: plaintext` in `lib/engine.css`) so Persian labels read right to left and formulas keep their order.
- Narration: `fa-IR-FaridNeural`, rate `-4%`. Numbers are spoken in Persian words ("شش ضربدر ده به توان هجده") while the screen shows symbols and Latin numerals.
- Questions: prompt in Persian, short; answers typed in Latin digits (`0.3`, `1/6`); the Persian digits ۰-۹ and the Persian decimal separator are also accepted (`‎٫` is normalised in `rat()`). Feedback names the mistake, then Show answer.
- Layout: helper functions in `site/aoe/ch01/index.html` are chapter-local for now (`aoeWire`, `aoeRes`, `aoeBattery`, `aoeBatteryV`, `aoeArrow`, `aoeLabel`, `aoeBox`, `aoeFormula`, `aoePacket`, `aoeBrace`, `aoeLamp`). Move one into `lib/engine.js` when a second chapter needs it.
- Persian prose writes mathematical expressions inside RTL text as `علت (۱٫۵)`-style parentheses; avoid mixing a Latin formula into a Persian sentence without parentheses.

## Visual models / available helpers
- Battery + resistor loop ("the canonical circuit"): `why`, `ah`, `kcl`; helper `aoeBatteryV`/`aoeRes`.
- Potential rails with a charge sliding downhill: `voltage`; inline `prog()`.
- Charge packets marching past a cross-section: `current`; helper `aoePacket`.
- Node with in/out arrows: `kcl`; two-path A→B loop: `kvl`.
- Formula frame: `aoeFormula` (rect behind `M()` parts); label helper: `aoeLabel`.
- Unit sketch on the contents page: `site/aoe/unit-art.js` (loop on the board, one travelling charge).

## Persian edition of the engine
`site/aoe/lib/engine.js` and `engine.css` are the skill's engine plus the Persian interface patch
(`tools/aoe/localize_engine_fa.py`: UI strings, aria labels, Persian digits in counters, Persian
digits accepted in answer boxes, Vazirmatn font stack, RTL cards). Re-run that script after
copying a newer engine from the skill. Logic, animation API and replay behaviour are untouched.

## Current decisions
- Chapter 1 is cut into 16 lessons along the book's own section headings (see `chapters.md`). Lesson 1 (`ch01`) covers 1.1 Introduction and 1.2's definitions: charge, current, voltage, KCL, KVL, power — PDF pages 1-12.
- The lesson opens on the subject, one new thing per beat, and every claim is checked in the frame (the animation is the argument).
- Narration audio currently ships as silent placeholders of the correct length (`tools/aoe/make_placeholder_audio.py`) because this environment cannot reach Edge TTS; run `tools/aoe/tts_fa.py` to drop the real Persian voice in — beat ids, marks and timings stay the same shape.
