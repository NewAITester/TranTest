#!/usr/bin/env python3
"""Apply the Persian (fa) UI patch to this book's copy of the Papermorph engine.

Usage (from the repository root):

    python3 tools/aoe/localize_engine_fa.py

The book keeps its own engine copy at ``site/aoe/lib/engine.js`` and
``site/aoe/lib/engine.css`` (see ``books/aoe/BOOK.md``). When the upstream
skill engine is refreshed, re-copy those two files and run this script again to
re-apply the Persian interface strings and the RTL/font styles.

The script only rewrites literal UI text, aria labels and the font stack; the
engine's logic, animation API and replay behaviour are untouched. Every
replacement must match exactly once (or be already applied), otherwise the
script stops with an error instead of half-patching the engine.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE_JS = ROOT / "site/aoe/lib/engine.js"
ENGINE_CSS = ROOT / "site/aoe/lib/engine.css"

# Engine font stack (JS constant) - Persian text first, then the engine's sans.
FA_STACK = 'Vazirmatn,"Avenir Next","Segoe UI","Helvetica Neue",Arial,sans-serif'
OLD_STACK = '"Avenir Next","Segoe UI","Helvetica Neue",Arial,sans-serif'

# The helper that renders Latin digits as Persian digits in the interface.
DIGIT_HELPER = (
    "\n// Persian digits for interface numbers (this book's UI language is Persian).\n"
    "const fa = s => String(s).replace(/\\d/g, d => '\u06f0\u06f1\u06f2\u06f3\u06f4\u06f5\u06f6\u06f7\u06f8\u06f9'[d]);\n"
)

JS_PATCHES: list[tuple[str, str]] = [
    # ---- answer boxes accept Persian digits (a Persian reader types ۰٫۳, not 0.3) --
    ("  const t = String(str).trim().replace(/^[\u2212\u2013]/, '-').replace(/\\s+/g, ' ');",
     "  const t = String(str).trim().replace(/^[\u2212\u2013]/, '-')\n"
     "    .replace(/[\u06f0-\u06f9]/g, d => '\u06f0\u06f1\u06f2\u06f3\u06f4\u06f5\u06f6\u06f7\u06f8\u06f9'.indexOf(d))\n"
     "    .replace(/[\u0660-\u0669]/g, d => '\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669'.indexOf(d))\n"
     "    .replace(/[\u066b\u00b7]/g, '.').replace(/[\u066c\u060c]/g, '').replace(/\\s+/g, ' ');"),
    # ---- fonts -----------------------------------------------------------------
    (OLD_STACK, FA_STACK),
    # ---- injected stage UI -----------------------------------------------------
    ('<rect width="1600" height="900" fill="#1d2b27" />',
     '<rect width="1600" height="900" fill="#1d2b27" />'),
    ('aria-label="Lesson animation"', 'aria-label="\u0627\u0646\u06cc\u0645\u06cc\u0634\u0646 \u062f\u0631\u0633"'),
    ('<div class="paused-mark"><div>Paused. Press space or click to continue.</div></div>',
     '<div class="paused-mark"><div>\u0645\u062a\u0648\u0642\u0641 \u0634\u062f. \u0628\u0631\u0627\u06cc \u0627\u062f\u0627\u0645\u0647 \u06a9\u0644\u06cc\u062f \u0641\u0627\u0635\u0644\u0647 \u0631\u0627 \u0628\u0632\u0646\u06cc\u062f \u06cc\u0627 \u06a9\u0644\u06cc\u06a9 \u06a9\u0646\u06cc\u062f.</div></div>'),
    # ---- help overlay ----------------------------------------------------------
    ('<h2>Keyboard shortcuts</h2>', '<h2>\u06a9\u0644\u06cc\u062f\u0647\u0627\u06cc \u0645\u06cc\u0627\u0646\u0628\u0631</h2>'),
    ('<div><h3>Lesson</h3><dl>', '<div><h3>\u062f\u0631\u0633</h3><dl>'),
    ('<dd>Play or pause</dd>', '<dd>\u067e\u062e\u0634 \u06cc\u0627 \u062a\u0648\u0642\u0641</dd>'),
    ('<dd>Previous or next step</dd>', '<dd>\u06af\u0627\u0645 \u067e\u06cc\u0634\u06cc\u0646 \u06cc\u0627 \u0628\u0639\u062f\u06cc</dd>'),
    ('<dd>Change step during a question</dd>', '<dd>\u062a\u063a\u06cc\u06cc\u0631 \u06af\u0627\u0645 \u0647\u0646\u06af\u0627\u0645 \u067e\u0631\u0633\u0634</dd>'),
    ('<dd>Start over</dd>', '<dd>\u0634\u0631\u0648\u0639 \u062f\u0648\u0628\u0627\u0631\u0647 \u0627\u0632 \u0627\u0628\u062a\u062f\u0627</dd>'),
    ('<dd>Captions on or off</dd>', '<dd>\u0631\u0648\u0634\u0646/\u062e\u0627\u0645\u0648\u0634 \u06a9\u0631\u062f\u0646 \u0632\u06cc\u0631\u0646\u0648\u06cc\u0633</dd>'),
    ('<dd>Full screen</dd>', '<dd>\u062a\u0645\u0627\u0645\u200c\u0635\u0641\u062d\u0647</dd>'),
    ('<dd>Show this list</dd>', '<dd>\u0646\u0645\u0627\u06cc\u0634 \u0627\u06cc\u0646 \u0641\u0647\u0631\u0633\u062a</dd>'),
    ('<div><h3>Questions</h3><dl>', '<div><h3>\u067e\u0631\u0633\u0634\u200c\u0647\u0627</h3><dl>'),
    ('<dd>Choose an answer or a ring</dd>', '<dd>\u0627\u0646\u062a\u062e\u0627\u0628 \u067e\u0627\u0633\u062e \u06cc\u0627 \u0645\u0646\u0637\u0642\u0647</dd>'),
    ('<dd>True or false</dd>', '<dd>\u062f\u0631\u0633\u062a \u06cc\u0627 \u0646\u0627\u062f\u0631\u0633\u062a</dd>'),
    ('<dd>Move between rows</dd>', '<dd>\u062d\u0631\u06a9\u062a \u0628\u06cc\u0646 \u0633\u0637\u0631\u0647\u0627</dd>'),
    ('<dd>Move along the number line, or pick a number to sort</dd>',
     '<dd>\u062d\u0631\u06a9\u062a \u0631\u0648\u06cc \u0645\u062d\u0648\u0631 \u06cc\u0627 \u0627\u0646\u062a\u062e\u0627\u0628 \u0639\u062f\u062f \u0628\u0631\u0627\u06cc \u062f\u0633\u062a\u0647\u200c\u0628\u0646\u062f\u06cc</dd>'),
    ('<dd>Check, then continue</dd>', '<dd>\u0628\u0631\u0631\u0633\u06cc\u060c \u0633\u067e\u0633 \u0627\u062f\u0627\u0645\u0647</dd>'),
    ('<dd>Show the answer</dd>', '<dd>\u0646\u0645\u0627\u06cc\u0634 \u067e\u0627\u0633\u062e</dd>'),
    ('<dd>Leave an answer box</dd>', '<dd>\u062e\u0631\u0648\u062c \u0627\u0632 \u062c\u0639\u0628\u0647\u0654 \u067e\u0627\u0633\u062e</dd>'),
    ('<p class="help-close">Press <kbd>Esc</kbd> to close.</p>',
     '<p class="help-close">\u0628\u0631\u0627\u06cc \u0628\u0633\u062a\u0646 <kbd>Esc</kbd> \u0631\u0627 \u0628\u0632\u0646\u06cc\u062f.</p>'),
    # ---- cover, sound note, controls -------------------------------------------
    ('<p class="sound-note" id="soundNote" hidden>Sound could not play. The lesson continues with the on-screen text.</p>',
     '<p class="sound-note" id="soundNote" hidden>\u0635\u062f\u0627 \u067e\u062e\u0634 \u0646\u0634\u062f. \u062f\u0631\u0633 \u0628\u0627 \u0645\u062a\u0646 \u0631\u0648\u06cc \u0635\u0641\u062d\u0647 \u0627\u062f\u0627\u0645\u0647 \u0645\u06cc\u200c\u06cc\u0627\u0628\u062f.</p>'),
    ('Start lesson', '\u0634\u0631\u0648\u0639 \u062f\u0631\u0633'),
    ('Press <kbd>Space</kbd> to start, <kbd>?</kbd> for shortcuts.',
     '\u0628\u0631\u0627\u06cc \u0634\u0631\u0648\u0639 <kbd>Space</kbd> \u0631\u0627 \u0628\u0632\u0646\u06cc\u062f \u0648 \u0628\u0631\u0627\u06cc \u0641\u0647\u0631\u0633\u062a \u06a9\u0644\u06cc\u062f\u0647\u0627 <kbd>?</kbd> \u0631\u0627.'),
    ('aria-label="All chapters" title="All chapters"', 'aria-label="\u0647\u0645\u0647\u0654 \u0641\u0635\u0644\u200c\u0647\u0627" title="\u0647\u0645\u0647\u0654 \u0641\u0635\u0644\u200c\u0647\u0627"'),
    ('aria-label="Play or pause (space)"', 'aria-label="\u067e\u062e\u0634 \u06cc\u0627 \u062a\u0648\u0642\u0641 (\u0641\u0627\u0635\u0644\u0647)"'),
    ('aria-label="Previous step (left arrow)"', 'aria-label="\u06af\u0627\u0645 \u067e\u06cc\u0634\u06cc\u0646 (\u06a9\u0644\u06cc\u062f \u06af\u0627\u0645)"'),
    ('aria-label="Restart lesson"', 'aria-label="\u0634\u0631\u0648\u0639 \u062f\u0648\u0628\u0627\u0631\u0647\u0654 \u062f\u0631\u0633"'),
    ('aria-label="Adjust volume" aria-controls="volume" title="Volume (0 = muted)"',
     'aria-label="\u062a\u0646\u0637\u06cc\u0645 \u0635\u062f\u0627" aria-controls="volume" title="\u0635\u062f\u0627 (۰ = \u0628\u06cc\u200c\u0635\u062f\u0627)"'),
    ('aria-label="Volume">', 'aria-label="\u0635\u062f\u0627">'),
    ('aria-label="Keyboard shortcuts (?)" title="Keyboard shortcuts (?)"',
     'aria-label="\u06a9\u0644\u06cc\u062f\u0647\u0627\u06cc \u0645\u06cc\u0627\u0646\u0628\u0631 (؟)" title="\u06a9\u0644\u06cc\u062f\u0647\u0627\u06cc \u0645\u06cc\u0627\u0646\u0628\u0631 (؟)"'),
    ('aria-label="Captions (C)" title="Captions (C)"', 'aria-label="\u0632\u06cc\u0631\u0646\u0648\u06cc\u0633 (C)" title="\u0632\u06cc\u0631\u0646\u0648\u06cc\u0633 (C)"'),
    ('aria-label="Full screen">', 'aria-label="\u062a\u0645\u0627\u0645\u200c\u0635\u0641\u062d\u0647">'),
    ("b.setAttribute('aria-label', 'Answer');", "b.setAttribute('aria-label', '\u067e\u0627\u0633\u062e');"),
    ('`Lesson animation: ${CHAPTER.title}`', '`\u0627\u0646\u06cc\u0645\u06cc\u0634\u0646 \u062f\u0631\u0633: ${CHAPTER.title}`'),
    # ---- quiz chrome -----------------------------------------------------------
    ("function quiz(pos, qs, done, label = 'Quick check') {", "function quiz(pos, qs, done, label = '\u0628\u0631\u0631\u0633\u06cc \u0633\u0631\u06cc\u0639') {"),
    ("const bCheck = h('button', 'btn', ['Check', kbd('Enter')]), bShow = h('button', 'btn quiet', ['Show answer', kbd('S')]);",
     "const bCheck = h('button', 'btn', ['\u0628\u0631\u0631\u0633\u06cc', kbd('Enter')]), bShow = h('button', 'btn quiet', ['\u0646\u0645\u0627\u06cc\u0634 \u067e\u0627\u0633\u062e', kbd('S')]);"),
    ("const bNext = h('button', 'btn go', [k < qs.length - 1 ? 'Next question' : 'Continue', kbd('Enter')]);",
     "const bNext = h('button', 'btn go', [k < qs.length - 1 ? '\u067e\u0631\u0633\u0634 \u0628\u0639\u062f\u06cc' : '\u0627\u062f\u0627\u0645\u0647', kbd('Enter')]);"),
    ("say(ok ? 'ok' : 'no', [ok ? 'Correct. ' : 'Not quite. ', ...[].concat(msg || [])]);",
     "say(ok ? 'ok' : 'no', [ok ? '\u0622\u0641\u0631\u06cc\u0646. ' : '\u0646\u0647 \u062f\u0642\u06cc\u0642\u0627\u064b. ', ...[].concat(msg || [])]);"),
    ("bShow.onclick = () => { say('', ['Answer: ', ...[].concat(ctl.reveal())]); resolve(); };",
     "bShow.onclick = () => { say('', ['\u067e\u0627\u0633\u062e: ', ...[].concat(ctl.reveal())]); resolve(); };"),
    ("if (ctl.hint) head.append(h('p', 'keys', ['Keys: ', ...ctl.hint]));",
     "if (ctl.hint) head.append(h('p', 'keys', ['\u06a9\u0644\u06cc\u062f\u0647\u0627: ', ...ctl.hint]));"),
    ("const kick = label + (qs.length > 1 ? `   ${k + 1} of ${qs.length}` : '');",
     "const kick = label + (qs.length > 1 ? `   ${fa(k + 1)} \u0627\u0632 ${fa(qs.length)}` : '');"),
    # ---- question builder hints -------------------------------------------------
    ("hint: [kbd('\u2190'), kbd('\u2192'), ' move along the line, ', kbd('Enter'), ' choose'],",
     "hint: [kbd('\u2190'), kbd('\u2192'), ' \u062d\u0631\u06a9\u062a \u0631\u0648\u06cc \u062e\u0637\u060c ', kbd('Enter'), ' \u0627\u0646\u062a\u062e\u0627\u0628'],"),
    ("hint: [kbd('\u2190'), kbd('\u2192'), ' move, ', kbd('Enter'), ' choose'],",
     "hint: [kbd('\u2190'), kbd('\u2192'), ' \u062d\u0631\u06a9\u062a\u060c ', kbd('Enter'), ' \u0627\u0646\u062a\u062e\u0627\u0628'],"),
    ("hint: [kbd('\u2190'), kbd('\u2192'), ' move, ', kbd('Enter'), ' choose, or click'],",
     "hint: [kbd('\u2190'), kbd('\u2192'), ' \u062d\u0631\u06a9\u062a\u060c ', kbd('Enter'), ' \u0627\u0646\u062a\u062e\u0627\u0628\u060c \u06cc\u0627 \u06a9\u0644\u06cc\u06a9'],"),
    ("hint: [...(single ? [] : [kbd('\u2191'), kbd('\u2193'), ' row, ']), ...(/\\d/.test(hot[0]) ? [kbd(hot[0]), '\u2013', kbd(hot[hot.length - 1])] : hot.map(kbd)), ' choose'],",
     "hint: [...(single ? [] : [kbd('\u2191'), kbd('\u2193'), ' \u0633\u0637\u0631\u060c ']), ...(/\\d/.test(hot[0]) ? [kbd(hot[0]), '\u2013', kbd(hot[hot.length - 1])] : hot.map(kbd)), ' \u0627\u0646\u062a\u062e\u0627\u0628'],"),
    ("const msg = single ? (done ? rows[0].it.why : rows[0].it.hint ?? rows[0].it.why)\n        : done ? [] : [`${right} of ${rows.length} right. Fix the rows marked \u2717 and check again.`];",
     "const msg = single ? (done ? rows[0].it.why : rows[0].it.hint ?? rows[0].it.why)\n        : done ? [] : [`${fa(right)} \u0627\u0632 ${fa(rows.length)} \u062f\u0631\u0633\u062a. \u0633\u0637\u0631\u0647\u0627\u06cc \u2717 \u0631\u0627 \u062f\u0631\u0633\u062a \u06a9\u0646\u06cc\u062f \u0648 \u062f\u0648\u0628\u0627\u0631\u0647 \u0628\u0631\u0631\u0633\u06cc \u06a9\u0646\u06cc\u062f.`];"),
    ("return single ? rows[0].it.why : 'the correct numbers are filled in.';",
     "return single ? rows[0].it.why : '\u0639\u062f\u062f\u0647\u0627\u06cc \u062f\u0631\u0633\u062a \u0646\u0648\u0634\u062a\u0647 \u0634\u062f\u0646\u062f.';"),
    ("return single ? rows[0].it.why : 'the correct choices are now selected.';",
     "return single ? rows[0].it.why : '\u06af\u0632\u06cc\u0646\u0647\u200c\u0647\u0627\u06cc \u062f\u0631\u0633\u062a \u0627\u0646\u062a\u062e\u0627\u0628 \u0634\u062f\u0646\u062f.';"),
    ("hint: [all.some(b => b.dataset.ans.includes('/')) ? 'type numbers like 3/4 or \u22122 1/4, ' : 'type the number, ', kbd('Tab'), ' next box, ', kbd('Enter'), ' check, ', kbd('Esc'), ' leave the box'],",
     "hint: [all.some(b => b.dataset.ans.includes('/')) ? '\u0639\u062f\u062f\u06cc \u0645\u0627\u0646\u0646\u062f 3/4 \u06cc\u0627 \u22122 1/4 \u0628\u0646\u0648\u06cc\u0633\u06cc\u062f\u060c ' : '\u0639\u062f\u062f \u0631\u0627 \u0628\u0646\u0648\u06cc\u0633\u06cc\u062f\u060c ', kbd('Tab'), ' \u062c\u0639\u0628\u0647\u0654 \u0628\u0639\u062f\u06cc\u060c ', kbd('Enter'), ' \u0628\u0631\u0631\u0633\u06cc\u060c ', kbd('Esc'), ' \u062e\u0631\u0648\u062c \u0627\u0632 \u062c\u0639\u0628\u0647'],"),
    ("api.grade(all, single ? rows[0].it.why : all ? [] : [`${right} of ${rows.length} right. Fix the rows marked \u2717 and check again.`], { right, total: rows.length });",
     "api.grade(all, single ? rows[0].it.why : all ? [] : [`${fa(right)} \u0627\u0632 ${fa(rows.length)} \u062f\u0631\u0633\u062a. \u0633\u0637\u0631\u0647\u0627\u06cc \u2717 \u0631\u0627 \u062f\u0631\u0633\u062a \u06a9\u0646\u06cc\u062f \u0648 \u062f\u0648\u0628\u0627\u0631\u0647 \u0628\u0631\u0631\u0633\u06cc \u06a9\u0646\u06cc\u062f.`], { right, total: rows.length });"),
    # ---- finish card -----------------------------------------------------------
    ("const line = (name, [r, t]) => h('p', 'fb', t ? `${name}: ${r} of ${t} right on the first try.` : `${name}: not attempted.`);",
     "const line = (name, [r, t]) => h('p', 'fb', t ? `${name}: ${fa(r)} \u0627\u0632 ${fa(t)} \u062f\u0631 \u062a\u0644\u0627\u0634 \u0627\u0648\u0644 \u062f\u0631\u0633\u062a.` : `${name}: \u0627\u0646\u062c\u0627\u0645 \u0646\u0634\u062f.`);"),
    ("const home = h('a', 'btn quiet', 'All chapters');", "const home = h('a', 'btn quiet', '\u0647\u0645\u0647\u0654 \u0641\u0635\u0644\u200c\u0647\u0627');"),
    ("const again = h('button', 'btn' + (CHAPTER.next ? ' quiet' : ' go'), ['Watch again', kbd(CHAPTER.next ? 'R' : 'Enter')]);",
     "const again = h('button', 'btn' + (CHAPTER.next ? ' quiet' : ' go'), ['\u062a\u0645\u0627\u0634\u0627\u06cc \u062f\u0648\u0628\u0627\u0631\u0647', kbd(CHAPTER.next ? 'R' : 'Enter')]);"),
    ("const next = CHAPTER.next && h('button', 'btn go', ['Next chapter', kbd('Enter')]);",
     "const next = CHAPTER.next && h('button', 'btn go', ['\u0641\u0635\u0644 \u0628\u0639\u062f', kbd('Enter')]);"),
    ("c.append(h('div', 'finwrap', [guide, h('p', 'kicker', `Chapter ${CHAPTER.number} complete`), h('p', 'prompt', CHAPTER.title),\n    line('Quick checks', sum('c-')), line('Chapter practice', sum('p-')),",
     "c.append(h('div', 'finwrap', [guide, h('p', 'kicker', `\u067e\u0627\u06cc\u0627\u0646 \u0641\u0635\u0644 ${fa(CHAPTER.number)}`), h('p', 'prompt', CHAPTER.title),\n    line('\u0628\u0631\u0631\u0633\u06cc\u200c\u0647\u0627\u06cc \u0633\u0631\u06cc\u0639', sum('c-')), line('\u062a\u0645\u0631\u06cc\u0646\u200c\u0647\u0627\u06cc \u0641\u0635\u0644', sum('p-')),"),
    # ---- cover meta and step counter -------------------------------------------
    ("$('coverMeta').textContent = `About ${CHAPTER.minutes} minutes, with sound and quick checks.`;",
     "$('coverMeta').textContent = `\u062d\u062f\u0648\u062f ${fa(CHAPTER.minutes)} \u062f\u0642\u06cc\u0642\u0647\u060c \u0628\u0627 \u0635\u062f\u0627 \u0648 \u0628\u0631\u0631\u0633\u06cc\u200c\u0647\u0627\u06cc \u06a9\u0648\u062a\u0627\u0647.`;"),
    ("$('stepName').textContent = `${P.i + 1} / ${BEATS.length}   ${BEATS[P.i].title}`;",
     "$('stepName').textContent = `${fa(P.i + 1)} / ${fa(BEATS.length)}   ${BEATS[P.i].title}`;"),
    # ---- keyboard help line used by the cover ----------------------------------
    ("<small><span id=\"coverMeta\"></span>", "<small><span id=\"coverMeta\"></span>"),
]

CSS_APPENDIX = """
/* ============================================================================
   Persian (fa) edition overrides for this book - applied by
   tools/aoe/localize_engine_fa.py together with the engine.js patch.
   The engine's layout and animation stay as they are; this block adds the
   Persian text face, the RTL reading direction for cards and captions, and
   per-element bidi handling for SVG labels (Persian labels read right to left,
   Latin formulas keep their own order).
   ========================================================================== */
@font-face { font-family: Vazirmatn; font-weight: 400; font-display: swap;
  src: url(fonts/Vazirmatn-Regular.woff2) format('woff2'); }
@font-face { font-family: Vazirmatn; font-weight: 500; font-display: swap;
  src: url(fonts/Vazirmatn-Medium.woff2) format('woff2'); }
@font-face { font-family: Vazirmatn; font-weight: 600; font-display: swap;
  src: url(fonts/Vazirmatn-SemiBold.woff2) format('woff2'); }
@font-face { font-family: Vazirmatn; font-weight: 700; font-display: swap;
  src: url(fonts/Vazirmatn-Bold.woff2) format('woff2'); }

:root { --ui: Vazirmatn, "Avenir Next", "Segoe UI", "Helvetica Neue", Arial, sans-serif; }

/* Each SVG label is its own bidi paragraph: Persian labels lay out right to
   left, Latin formulas keep left-to-right order. */
#stage text, svg.m text { unicode-bidi: plaintext; }

/* Cards, captions and overlays read right to left. */
.card, .caption, .sound-note, .cover, .help-box, .fin .finwrap { direction: rtl; }
.card .head, .card .fb, .card .body { text-align: right; }
.card .body { margin-top: 6px; }
.kicker { letter-spacing: 0; }
.grid .row { grid-template-columns: 200px minmax(0, 1fr) 34px; }
.grid.text .row { grid-template-columns: minmax(0, 1fr) auto 34px; }
.grid .num { justify-content: flex-start; font-size: 24px; }
.grid .why { padding-left: 0; padding-right: 216px; color: var(--dim); }
.grid.text .why { padding-right: 0; }
.blanks .bline { white-space: normal; }
.blanks .box { font-family: Vazirmatn, "STIX Two Text", "Cambria Math", Georgia, serif; font-size: 28px; }
.blanks .why, .side .fb { direction: rtl; }
.step { direction: rtl; text-align: left; font-family: Vazirmatn, "Avenir Next", Arial, sans-serif; }
.help dd, .help dt { direction: rtl; }
.help dt { text-align: right; padding-right: 0; }
.help dd { padding-right: 12px; }
/* Persian serif face for the two display type settings the engine keeps in a book face. */
.cover-t, .fin .prompt { font-family: Vazirmatn, "Iowan Old Style", Palatino, Georgia, serif; letter-spacing: 0; }
.cover small, .cover-k, .fin .kicker { font-family: var(--ui); }
"""


def patch_js(text: str) -> str:
    if "const fa = s => String(s)" not in text:
        anchor = "const COL = {"
        if anchor not in text:
            raise SystemExit("engine.js: cannot find the COL palette to insert the digit helper")
        text = text.replace(anchor, DIGIT_HELPER.lstrip("\n") + anchor, 1)
    for old, new in JS_PATCHES:
        if old == new:
            continue
        if new in text:
            continue  # already applied
        if text.count(old) != 1:
            raise SystemExit(f"engine.js: expected exactly one match for {old[:70]!r}, found {text.count(old)}")
        text = text.replace(old, new, 1)
    return text


def patch_css(text: str) -> str:
    marker = "Persian (fa) edition overrides for this book"
    if marker in text:
        return text
    return text.rstrip("\n") + "\n" + CSS_APPENDIX


def main() -> int:
    js = ENGINE_JS.read_text(encoding="utf-8")
    ENGINE_JS.write_text(patch_js(js), encoding="utf-8")
    css = ENGINE_CSS.read_text(encoding="utf-8")
    ENGINE_CSS.write_text(patch_css(css), encoding="utf-8")
    print(f"patched {ENGINE_JS.relative_to(ROOT)} and {ENGINE_CSS.relative_to(ROOT)} for Persian")
    return 0


if __name__ == "__main__":
    sys.exit(main())
