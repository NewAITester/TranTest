// طرحهای گچی سرِ بخشهای صفحهٔ فهرست؛ برای هر بخش یک طرح، با رنگ همان بخش.
// هر ورودی، درون یک SVG با viewBox 0 0 600 180 است. در نسخهٔ فارسی، طرح در سمت چپ می‌نشیند،
// پس یک‌سومِ راست (x > 380) برای عنوان بخش خالی می‌ماند. کلاس‌ها در index.html تعریف شده‌اند:
//   d  خطی که وقتی بخش به دید می‌رسد کشیده می‌شود (--k ترتیب خط‌ها را می‌دهد)
//   t  متنی که محو ظاهر می‌شود
//   a  گچِ کم‌رنگ به‌جای رنگ بخش؛  faint  کم‌رنگ‌تر
// بعد از کشیده شدن، هر طرح یک حرکت کوچک و هم‌بسته با موضوع خود دارد: در index.html
// قاعده‌های .seen .unit-art .NAME و keyframes‌ها را ببینید (swap-a، hop، spin، breathe و ...).
'use strict';
(() => {
  let k = 0;
  const P = (d, cls = '', extra = '') => `<path class="d ${cls}" pathLength="1" style="--k:${k++}" d="${d}" ${extra}/>`;
  const Tx = (x, y, s, size = 24, cls = '', anchor = 'start') => `<text class="t ${cls}" style="--k:${k++}" x="${x}" y="${y}" font-size="${size}" text-anchor="${anchor}">${s}</text>`;
  const C = (cx, cy, r, cls = '') => `<circle class="d ${cls}" pathLength="1" style="--k:${k++}" cx="${cx}" cy="${cy}" r="${r}"/>`;
  const reset = s => { k = 0; return s; };
  // زگ‌زاگ مقاومت، افقی، وسط آن روی cx،cy
  const zig = (cx, cy, len = 120, h = 22, lead = 60) => {
    const half = len / 2, step = len / 6;
    let d = `M${cx - half - lead} ${cy}H${cx - half}`;
    for (let i = 0; i < 6; i++) d += `L${cx - half + step * (i + .5)} ${cy + (i % 2 ? h : -h)}`;
    return d + `L${cx + half} ${cy}`;
  };

  window.UNIT_ART = [
    // بخش ۱ — مدار: باتری، مقاومت و گرهی که فیزیکِ درس روی آن ساخته می‌شود.
    // ولتاژ روی دو سر مقاومت (پیکان‌های کهربایی) و باری که روی سیم حرکت می‌کند.
    reset(
      P('M60 120H240') + P(zig(240, 120)) + P('M360 120H560', 'a') +
      P('M60 92V148M74 92V148', 'a') +                       // باتری
      P('M212 62V96M268 62V96', '') +                        // پیکان‌های ولتاژ
      Tx(240, 40, 'V', 24, '', 'middle') +
      Tx(470, 96, 'I', 24, 'a', 'middle') +
      `<circle class="t ride" r="9" fill="currentColor" stroke="none" style="--k:${k++};offset-path:path('M120 120H540')"/>` +
      `<path class="t" d="M60 168H360" stroke="currentColor" stroke-width="1.6" opacity="0" style="--k:${k++}"/>`
    ),
  ];
})();
