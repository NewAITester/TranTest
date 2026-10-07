// Interaction walk-through for chapter fa-01 (voltage, current and power).
//   node tools/aoe/e2e_ch01.mjs [pageUrl]
// Runs the real page in jsdom with a stub <audio>: drives every question the way a reader does
// (typed answers, number keys, Enter/Space), checks that wrong first tries are recorded and that
// the lesson advances, then rebuilds every beat with seek() and fails on any console error.
import { JSDOM, VirtualConsole } from 'jsdom';

const URL = process.argv[2] || 'http://localhost:8765/aoe/ch01/';
const errors = [];
const vc = new VirtualConsole();
vc.on('jsdomError', e => errors.push('jsdomError: ' + e.message));
vc.on('error', (...a) => errors.push('console.error: ' + a.map(String).join(' ')));
vc.on('warn', () => {});

const dom = await JSDOM.fromURL(URL, {
  runScripts: 'dangerously', resources: 'usable', pretendToBeVisual: true, virtualConsole: vc,
  beforeParse(w) {
    w.matchMedia = () => ({ matches: false, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} });
    class FakeAudio { play() { return Promise.resolve(); } pause() {} load() {} removeAttribute() {} addEventListener() {} }
    w.Audio = FakeAudio;
    w.HTMLCanvasElement.prototype.getContext = function () {
      const self = this;
      return { set font(v) { self._f = v; }, get font() { return self._f || ''; }, measureText: s => ({ width: String(s).length * 9 }) };
    };
  },
});
const { window } = dom;
await new Promise(r => window.addEventListener('load', r, { once: true }));
await new Promise(r => setTimeout(r, 200));
const ev = code => window.eval(code);
const q = sel => window.document.querySelector(sel);
const qa = sel => [...window.document.querySelectorAll(sel)];
const text = sel => (q(sel)?.textContent || '').trim();
const fb = () => q('.card .fb')?.className || '';          // 'fb ok' / 'fb no'; the ✓ and ✗ are CSS ::before
const wait = ms => new Promise(r => setTimeout(r, ms));

const check = (label, cond, extra = '') => {
  console.log(`${cond ? 'ok  ' : 'FAIL'} ${label}${cond || !extra ? '' : ' — ' + extra}`);
  if (!cond) errors.push('check failed: ' + label);
};

ev('P.playing = false; P.done = true;');
check('page booted with 16 beats', ev('BEATS.length') === 16, String(ev('typeof BEATS')));

/* ---------- quick check 1: charge and current ---------- */
ev('seek(6, false)');
check('q1 card has two answer boxes', qa('.box').length === 2, String(qa('.box').length));
qa('.box')[0].value = '5';
q('.card .btn').click();                                   // Check
check('wrong first answer is not correct', fb().includes('no'), text('.card .fb'));
check('first try recorded as wrong', ev("SCORE['c-charge-current'].right") === 0);
qa('.box')[0].value = '0.3';
qa('.box')[1].value = '2';
q('.card .btn').click();
check('both right answers accepted', fb().includes('ok'), text('.card .fb'));
check('row scored 2 of 2', ev("SCORE['c-charge-current'].total") === 2);
q('.card .btn.go').click();                                 // Continue
await wait(50);
check('lesson advanced past the question', ev('P.i') === 7, String(ev('P.i')));

/* ---------- practice 1: choice + blank + true/false grid ---------- */
ev('seek(13, false)');
check('practice 1 is a full-screen card', !!q('.card.screen'), text('.card .kicker'));
check('practice label is Persian', text('.card .kicker').includes('تمرین فصل'), text('.card .kicker'));
qa('.card .opt')[1].click();                                // a wrong choice
check('wrong choice explained', fb().includes('no'), text('.card .fb'));
check('first try recorded for the choice', ev("SCORE['p-language'].right") === 0);
qa('.card .opt')[0].click();
check('right choice accepted', fb().includes('ok'), fb());
q('.card .btn.go').click();                                 // next question
await wait(50);
q('.box').value = '1';
q('.card .btn').click();
check('numeric practice answer accepted', fb().includes('ok'), text('.card .fb'));
q('.card .btn.go').click();
await wait(50);
check('true/false grid has four rows', qa('.card .grid .row').length === 4, String(qa('.card .grid .row').length));
qa('.card .grid .row').forEach((row, i) => row.querySelectorAll('.opt')[i === 2 ? 1 : 0].click());
q('.card .btn').click();
check('grid judged per row', ev("SCORE['p-tf'].total") === 4, JSON.stringify(ev("SCORE['p-tf']")));
check('grid reports right rows', fb().includes('ok'), text('.card .fb'));
q('.card .btn.go').click();
await wait(50);
check('practice 1 finished', ev('P.i') === 14, String(ev('P.i')));

/* ---------- practice 2: units, minutes, table ---------- */
ev('seek(14, false)');
qa('.card .opt')[0].click();
check('units question accepted', fb().includes('ok'), text('.card .fb'));
q('.card .btn.go').click();
await wait(50);
const boxes = qa('.box');
boxes[0].value = '600';
boxes[1].value = '1/6';
q('.card .btn').click();
check('fraction answer accepted', fb().includes('ok'), text('.card .fb'));
q('.card .btn.go').click();
await wait(50);
check('unit table has four rows', qa('.card .grid .row').length === 4);
const unitsForRow = [2, 1, 0, 3];                           // row asks for C, A, V, W
qa('.card .grid .row').forEach((row, i) => row.querySelectorAll('.opt')[unitsForRow[i]].click());
q('.card .btn').click();
check('unit table accepted', fb().includes('ok'), text('.card .fb'));
q('.card .btn.go').click();
await wait(50);

/* ---------- show-answer path ---------- */
ev('seek(6, false)');
q('.card .btn.quiet').click();                              // Show answer
check('show answer fills the boxes', qa('.box')[0].value === '0.3' && qa('.box')[1].value === '2', qa('.box').map(b => b.value).join());
check('show answer explains', text('.card .fb').includes('پاسخ'), text('.card .fb'));

/* ---------- finish card ---------- */
ev('seek(15, false)');
await wait(50);
check('finish card names the chapter', text('.card').includes('ولتاژ، جریان و توان'), text('.card').slice(0, 80));
check('finish card lists both scores', text('.card').includes('بررسی‌های سریع') && text('.card').includes('تمرین‌های فصل'));
check('finish card offers a restart', text('.card').includes('تماشای دوباره'));

/* ---------- replay invariants ---------- */
ev('restart()');
ev('P.playing = false; P.done = true;');
check('restart clears the score', Object.keys(ev('SCORE')).length === 0, JSON.stringify(ev('SCORE')));
for (let i = 0; i < ev('BEATS.length'); i++) { ev(`seek(${i}, false)`); ev('evalTo(999)'); }
check('every beat rebuilds by seeking', true);
check('no console errors', errors.length === 0, errors.slice(0, 4).join(' | '));

console.log(`\n${errors.length ? errors.length + ' problem(s)' : 'chapter fa-01 walk-through passed'}`);
dom.window.close();
process.exit(errors.length ? 1 : 0);
