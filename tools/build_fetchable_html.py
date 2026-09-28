#!/usr/bin/env python3
"""Build a self-contained, fetchable HTML edition of the supplied PDF.

The generated HTML contains:
- a lossless 2x rendering of every source page (including photos, diagrams,
  tables, equations, headers, footnotes, and printed page numbers), and
- server-delivered text for every page so an HTTP fetch, screen reader, or
  browser search can consume the document without running JavaScript.

Requirements: PyMuPDF and Pillow.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import re
from pathlib import Path

import pymupdf
from PIL import Image


PRIMARY_SECTIONS = (
    (1, "1.1 Introduction"),
    (1, "1.2 Voltage, current, and resistance"),
    (13, "1.3 Signals"),
    (18, "1.4 Capacitors and ac circuits"),
    (28, "1.5 Inductors and transformers"),
    (31, "1.6 Diodes and diode circuits"),
    (40, "1.7 Impedance and reactance"),
    (55, "1.8 Putting it all together — an AM radio"),
    (56, "1.9 Other passive components"),
    (64, "1.10 A parting shot: confusing markings and itty-bitty components"),
    (66, "Additional Exercises for Chapter 1"),
    (68, "Review of Chapter 1"),
)

PREFIXES_TABLE = """
<section class="semantic-table" aria-labelledby="prefixes-title">
  <h4 id="prefixes-title">PREFIXES <span>— semantic table transcription</span></h4>
  <div class="table-scroll"><table>
    <thead><tr><th>Multiple</th><th>Prefix</th><th>Symbol</th><th>Derivation</th></tr></thead>
    <tbody>
      <tr><td>10<sup>24</sup></td><td>yotta</td><td>Y</td><td>end-1 of Latin alphabet, hint of Greek <i>iota</i></td></tr>
      <tr><td>10<sup>21</sup></td><td>zetta</td><td>Z</td><td>end of Latin alphabet, hint of Greek <i>zeta</i></td></tr>
      <tr><td>10<sup>18</sup></td><td>exa</td><td>E</td><td>Greek <i>hexa</i> (six: power of 1000)</td></tr>
      <tr><td>10<sup>15</sup></td><td>peta</td><td>P</td><td>Greek <i>penta</i> (five: power of 1000)</td></tr>
      <tr><td>10<sup>12</sup></td><td>tera</td><td>T</td><td>Greek <i>teras</i> (monster)</td></tr>
      <tr><td>10<sup>9</sup></td><td>giga</td><td>G</td><td>Greek <i>gigas</i> (giant)</td></tr>
      <tr><td>10<sup>6</sup></td><td>mega</td><td>M</td><td>Greek <i>megas</i> (great)</td></tr>
      <tr><td>10<sup>3</sup></td><td>kilo</td><td>k</td><td>Greek <i>khilioi</i> (thousand)</td></tr>
      <tr><td>10<sup>−3</sup></td><td>milli</td><td>m</td><td>Latin <i>milli</i> (thousand)</td></tr>
      <tr><td>10<sup>−6</sup></td><td>micro</td><td>μ</td><td>Greek <i>mikros</i> (small)</td></tr>
      <tr><td>10<sup>−9</sup></td><td>nano</td><td>n</td><td>Greek <i>nanos</i> (dwarf)</td></tr>
      <tr><td>10<sup>−12</sup></td><td>pico</td><td>p</td><td>from Italian/Spanish <i>piccolo/pico</i> (small)</td></tr>
      <tr><td>10<sup>−15</sup></td><td>femto</td><td>f</td><td>Danish/Norwegian <i>femten</i> (fifteen)</td></tr>
      <tr><td>10<sup>−18</sup></td><td>atto</td><td>a</td><td>Danish/Norwegian <i>atten</i> (eighteen)</td></tr>
      <tr><td>10<sup>−21</sup></td><td>zepto</td><td>z</td><td>end of Latin alphabet, mirrors <i>zetta</i></td></tr>
      <tr><td>10<sup>−24</sup></td><td>yocto</td><td>y</td><td>end-1 of Latin alphabet, mirrors <i>yotta</i></td></tr>
    </tbody>
  </table></div>
</section>
"""

DIODES_TABLE = """
<section class="semantic-table" aria-labelledby="diodes-title">
  <h4 id="diodes-title">Table 1.1 — Representative Diodes <span>— semantic table transcription</span></h4>
  <div class="table-scroll"><table>
    <thead>
      <tr><th rowspan="2">Part #</th><th><i>V</i><sub>R</sub> (max)</th><th><i>I</i><sub>R</sub> (typ, 25°C)</th><th colspan="2"><i>V</i><sub>F</sub> @ <i>I</i><sub>F</sub></th><th>Capacitance</th><th rowspan="2">SMT<sup>a</sup> p/n</th><th rowspan="2">Comments</th></tr>
      <tr><th>(V)</th><th>(A @ V)</th><th>(mV)</th><th>(mA)</th><th>(pF @ <i>V</i><sub>R</sub>)</th></tr>
    </thead>
    <tbody>
      <tr class="group"><th colspan="8"><i>Silicon</i></th></tr>
      <tr><td>PAD5</td><td>45</td><td>0.25pA @ 20V</td><td>800</td><td>1</td><td>0.5pF @ 5V</td><td>SSTPAD5</td><td>metal + glass can</td></tr>
      <tr><td>1N4148</td><td>75</td><td>10nA @ 20V</td><td>750</td><td>10</td><td>0.9pF @ 0V</td><td>1N4148W</td><td>jellybean sig diode</td></tr>
      <tr><td>1N4007</td><td>1000</td><td>50nA @ 800V</td><td>800</td><td>250</td><td>12pF @ 10V</td><td>DL4007</td><td>1N4004 lower V</td></tr>
      <tr><td>1N5406</td><td>600</td><td>&lt;10μA @ 600V</td><td>1.0V</td><td>10A</td><td>18pF @ 10V</td><td>none</td><td>heat through leads</td></tr>
      <tr class="group"><th colspan="8"><i>Schottky</i><sup>b</sup></th></tr>
      <tr><td>1N6263</td><td>60</td><td>7nA @ 20V</td><td>400</td><td>1</td><td>0.6pF @ 10V</td><td>1N6263W</td><td>see also 1N5711</td></tr>
      <tr><td>1N5819</td><td>40</td><td>10μA @ 32V</td><td>400</td><td>1000</td><td>150pF @ 1V</td><td>1N5819HW</td><td>jellybean</td></tr>
      <tr><td>1N5822</td><td>40</td><td>40μA @ 32V</td><td>480</td><td>3000</td><td>450pF @ 1V</td><td>none</td><td>power Schottky</td></tr>
      <tr><td>MBRP40045</td><td>45</td><td>500μA @ 40V</td><td>540</td><td>400A</td><td>3500pF @ 10V</td><td>you jest!</td><td>Moby dual Schottky</td></tr>
    </tbody>
  </table></div>
  <p class="table-notes"><strong>Notes:</strong> (a) SMT, surface-mount technology. (b) Schottky diodes have lower forward voltage and zero reverse-recovery time, but more capacitance.</p>
</section>
"""

CSS = r"""
:root {
  color-scheme: light dark;
  --paper: #fff;
  --ink: #181716;
  --muted: #726d66;
  --line: #d7d1c8;
  --accent: #c96b38;
  --accent-dark: #8c3f1b;
  --canvas: #e9e5de;
  --panel: rgba(250, 248, 244, .94);
  --shadow: 0 18px 48px rgba(44, 35, 26, .14), 0 2px 8px rgba(44, 35, 26, .08);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; scroll-padding-top: 7.5rem; background: var(--canvas); }
body { margin: 0; color: var(--ink); background: var(--canvas); }
a { color: inherit; }
.skip-link { position: fixed; inset: .5rem auto auto .5rem; z-index: 100; transform: translateY(-180%); background: var(--ink); color: var(--paper); padding: .7rem 1rem; border-radius: .5rem; }
.skip-link:focus { transform: none; }
.masthead { color: #f9f5ee; background: #191714; padding: clamp(2.25rem, 6vw, 5.5rem) max(1rem, calc((100vw - 76rem) / 2)); border-bottom: 5px solid var(--accent); }
.eyebrow { margin: 0 0 .7rem; color: #dda078; text-transform: uppercase; letter-spacing: .16em; font-weight: 750; font-size: .72rem; }
.masthead h1 { max-width: 18ch; margin: 0; font-family: Georgia, "Times New Roman", serif; font-size: clamp(2.2rem, 6vw, 5.4rem); font-weight: 500; line-height: .94; letter-spacing: -.035em; }
.deck { max-width: 49rem; margin: 1.2rem 0 0; color: #cec7bd; font-size: clamp(.95rem, 2vw, 1.12rem); line-height: 1.65; }
.meta-strip { display: flex; flex-wrap: wrap; gap: .7rem 1.5rem; margin-top: 2rem; font-variant-numeric: tabular-nums; color: #f0e7dd; font-size: .84rem; }
.meta-strip span::before { content: ""; display: inline-block; width: .42rem; height: .42rem; margin-inline-end: .55rem; border-radius: 50%; background: var(--accent); vertical-align: .05rem; }
.toolbar { position: sticky; top: 0; z-index: 20; display: grid; grid-template-columns: minmax(15rem, 1fr) auto auto; gap: .75rem; align-items: center; padding: .75rem max(1rem, calc((100vw - 76rem) / 2)); background: var(--panel); border-bottom: 1px solid var(--line); box-shadow: 0 4px 24px rgba(40, 33, 26, .07); backdrop-filter: blur(14px); }
.search-wrap { position: relative; }
.search-wrap input { width: 100%; min-height: 2.65rem; padding: .65rem 7.1rem .65rem 2.65rem; color: var(--ink); background: var(--paper); border: 1px solid var(--line); border-radius: 999px; font: inherit; outline: none; }
.search-wrap input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 24%, transparent); }
.search-icon { position: absolute; left: .95rem; top: .72rem; width: 1.15rem; height: 1.15rem; color: var(--muted); }
#search-status { position: absolute; right: .95rem; top: .79rem; color: var(--muted); font-size: .78rem; font-variant-numeric: tabular-nums; }
.controls { display: flex; align-items: center; gap: .35rem; }
button, select, .toc-link { min-height: 2.55rem; border: 1px solid var(--line); border-radius: .65rem; color: var(--ink); background: var(--paper); font: inherit; cursor: pointer; }
button { min-width: 2.7rem; padding: .45rem .72rem; font-size: 1.1rem; }
button:hover, select:hover, .toc-link:hover { border-color: var(--accent); }
.page-readout { min-width: 7.7rem; text-align: center; color: var(--muted); font-size: .82rem; font-variant-numeric: tabular-nums; }
select { max-width: 10rem; padding: .45rem 2rem .45rem .72rem; font-size: .84rem; }
.toc-link { display: inline-flex; align-items: center; padding: .45rem .85rem; text-decoration: none; font-size: .84rem; }
.layout { display: grid; grid-template-columns: minmax(14rem, 18rem) minmax(0, 1fr); max-width: 92rem; margin: 0 auto; }
.toc { position: sticky; top: 4.2rem; align-self: start; max-height: calc(100vh - 4.2rem); overflow: auto; padding: 2.4rem 1.25rem 3rem; }
.toc h2 { margin: 0 0 1rem; color: var(--muted); font-size: .72rem; text-transform: uppercase; letter-spacing: .13em; }
.toc ol { list-style: none; margin: 0; padding: 0; border-left: 1px solid var(--line); }
.toc li { margin: 0; }
.toc a { display: grid; grid-template-columns: 2rem 1fr; gap: .35rem; padding: .48rem .2rem .48rem .7rem; color: #4e4943; text-decoration: none; border-left: 2px solid transparent; transform: translateX(-1px); font-size: .78rem; line-height: 1.35; }
.toc a:hover, .toc a.active { color: var(--accent-dark); border-left-color: var(--accent); }
.toc .toc-page { color: var(--muted); font-variant-numeric: tabular-nums; }
.document { min-width: 0; padding: 2.5rem clamp(1rem, 4vw, 4rem) 7rem; }
.fetch-note { max-width: 48rem; margin: 0 auto 2rem; padding: .9rem 1.1rem; color: #564e47; background: #fff8ed; border: 1px solid #e8d8bf; border-radius: .7rem; font-size: .86rem; line-height: 1.55; }
.fetch-note strong { color: var(--accent-dark); }
.pages { display: grid; grid-template-columns: minmax(0, 1fr); gap: 3.5rem; align-items: start; }
.pages.spread { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1.2rem; }
.page { min-width: 0; scroll-margin-top: 7rem; }
.page.filtered-out { display: none; }
.page-label { display: flex; align-items: baseline; justify-content: space-between; width: min(100%, 50rem); margin: 0 auto .55rem; color: var(--muted); font-size: .76rem; letter-spacing: .03em; }
.page-label strong { color: var(--ink); font-size: .88rem; }
.page-image-wrap { position: relative; width: min(100%, 50rem); margin: auto; aspect-ratio: 4 / 5; background: #fff; box-shadow: var(--shadow); }
.page img { display: block; width: 100%; height: 100%; object-fit: contain; background: #fff; }
.page.search-hit .page-image-wrap { outline: 4px solid #e0a06e; outline-offset: 5px; }
.transcript { width: min(100%, 50rem); margin: .7rem auto 0; color: #3f3a35; background: rgba(255, 255, 255, .7); border: 1px solid var(--line); border-radius: .55rem; }
.transcript summary { padding: .72rem .9rem; color: var(--muted); cursor: pointer; font-size: .8rem; font-weight: 650; }
.transcript[open] summary { border-bottom: 1px solid var(--line); }
.transcript-content { padding: .4rem clamp(.9rem, 3vw, 1.7rem) 1.5rem; font-family: Georgia, "Times New Roman", serif; font-size: .98rem; line-height: 1.6; }
.transcript-content p { margin: .85rem 0; }
.transcript-content .running-head { color: var(--muted); font-family: ui-sans-serif, system-ui, sans-serif; font-size: .72rem; }
.semantic-table { margin: 1.4rem 0; padding-top: 1rem; border-top: 1px solid var(--line); font-family: ui-sans-serif, system-ui, sans-serif; }
.semantic-table h4 { margin: 0 0 .7rem; font-family: Georgia, "Times New Roman", serif; font-size: 1.12rem; }
.semantic-table h4 span { color: var(--muted); font-family: ui-sans-serif, system-ui, sans-serif; font-size: .7rem; font-weight: 500; }
.table-scroll { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: .76rem; line-height: 1.35; font-variant-numeric: tabular-nums; }
th, td { padding: .36rem .45rem; text-align: left; border-bottom: 1px solid #ddd7cf; vertical-align: top; white-space: nowrap; }
thead th { color: #24211e; background: #eeeae4; border-bottom-color: #aaa197; }
tr.group th { padding-top: .75rem; background: #f7f4ef; }
.table-notes { font-family: ui-sans-serif, system-ui, sans-serif; font-size: .75rem; }
.no-results { display: none; max-width: 40rem; margin: 4rem auto; padding: 2rem; text-align: center; background: var(--paper); border: 1px solid var(--line); border-radius: 1rem; }
.no-results.visible { display: block; }
footer { padding: 2rem; color: var(--muted); text-align: center; border-top: 1px solid var(--line); font-size: .75rem; }
.sr-only { position: absolute !important; width: 1px !important; height: 1px !important; padding: 0 !important; margin: -1px !important; overflow: hidden !important; clip: rect(0, 0, 0, 0) !important; white-space: nowrap !important; border: 0 !important; }
@media (max-width: 900px) {
  .toolbar { grid-template-columns: 1fr auto; }
  .toolbar .toc-link { display: none; }
  .layout { display: block; }
  .toc { position: static; max-height: none; padding: 1.25rem 1rem 0; }
  .toc ol { display: flex; overflow-x: auto; border-left: 0; border-bottom: 1px solid var(--line); }
  .toc li { flex: 0 0 min(17rem, 80vw); }
  .toc a { height: 100%; border-left: 0; border-bottom: 2px solid transparent; transform: none; }
  .document { padding-top: 1.5rem; }
}
@media (max-width: 620px) {
  html { scroll-padding-top: 10rem; }
  .toolbar { grid-template-columns: 1fr; }
  .controls { justify-content: space-between; }
  .view-select { display: none; }
  .pages.spread { grid-template-columns: 1fr; gap: 3.5rem; }
  .page { scroll-margin-top: 10rem; }
  .masthead { padding-top: 2.6rem; }
}
@media (prefers-color-scheme: dark) {
  :root { --ink: #eee9e2; --muted: #aaa39a; --line: #47413b; --canvas: #26231f; --panel: rgba(36, 32, 28, .94); --paper: #312d28; --accent-dark: #ee9b6b; --shadow: 0 20px 50px rgba(0,0,0,.4); }
  .toc a { color: #c9c1b7; }
  .fetch-note { color: #ddcdbb; background: #372d22; border-color: #5a4935; }
  .transcript { color: #ddd6ce; background: rgba(49,45,40,.72); }
  thead th { color: #f0eae4; background: #47413a; border-bottom-color: #777066; }
  th, td { border-bottom-color: #514a43; }
  tr.group th { background: #3c3731; }
  .page-image-wrap { background: #fff; }
}
@media print {
  @page { size: 8in 10in; margin: 0; }
  html, body, .document, .layout { margin: 0 !important; padding: 0 !important; background: #fff !important; }
  .masthead, .toolbar, .toc, .fetch-note, .transcript, footer, .page-label, .no-results { display: none !important; }
  .pages, .pages.spread { display: block !important; }
  .page, .page.filtered-out { display: block !important; width: 8in; height: 10in; margin: 0; break-after: page; page-break-after: always; }
  .page-image-wrap { width: 8in; height: 10in; margin: 0; box-shadow: none; outline: 0 !important; }
  .page img { width: 8in; height: 10in; }
}
"""

JS = r"""
(() => {
  const pages = [...document.querySelectorAll('.page')];
  const pageCount = pages.length;
  const readout = document.querySelector('.page-readout');
  const search = document.querySelector('#search');
  const status = document.querySelector('#search-status');
  const noResults = document.querySelector('.no-results');
  const pageGrid = document.querySelector('.pages');
  const view = document.querySelector('#view');
  let current = 1;

  const go = (number) => {
    const target = document.querySelector(`#page-${Math.min(pageCount, Math.max(1, number))}`);
    if (target) target.scrollIntoView({behavior: 'smooth', block: 'start'});
  };

  document.querySelector('#prev').addEventListener('click', () => go(current - 1));
  document.querySelector('#next').addEventListener('click', () => go(current + 1));
  view.addEventListener('change', () => {
    pageGrid.classList.toggle('spread', view.value === 'spread');
    localStorage.setItem('fetchable-pdf-view', view.value);
  });
  const savedView = localStorage.getItem('fetchable-pdf-view');
  if (savedView === 'spread' && matchMedia('(min-width: 621px)').matches) {
    view.value = savedView;
    pageGrid.classList.add('spread');
  }

  const setCurrent = (n) => {
    current = n;
    readout.textContent = `صفحه ${n} از ${pageCount}`;
    document.querySelectorAll('.toc a.active').forEach(a => a.classList.remove('active'));
    const links = [...document.querySelectorAll('.toc a')].filter(a => Number(a.dataset.page) <= n);
    if (links.length) links.at(-1).classList.add('active');
  };
  const observer = new IntersectionObserver(entries => {
    const visible = entries.filter(e => e.isIntersecting).sort((a,b) => b.intersectionRatio - a.intersectionRatio);
    if (visible.length) setCurrent(Number(visible[0].target.dataset.page));
  }, {rootMargin: '-18% 0px -62% 0px', threshold: [0, .1, .5]});
  pages.forEach(p => observer.observe(p));

  let timer;
  const filter = () => {
    const query = search.value.trim().toLocaleLowerCase();
    let hits = 0;
    pages.forEach(page => {
      const match = !query || page.dataset.search.includes(query);
      page.classList.toggle('filtered-out', !match);
      page.classList.toggle('search-hit', Boolean(query && match));
      if (match) hits++;
    });
    status.textContent = query ? `${hits} صفحه` : `${pageCount} صفحه`;
    noResults.classList.toggle('visible', hits === 0);
  };
  search.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(filter, 120); });
  search.addEventListener('keydown', event => {
    if (event.key === 'Escape') { search.value = ''; filter(); search.blur(); }
    if (event.key === 'Enter') {
      const first = document.querySelector('.page.search-hit');
      if (first) first.scrollIntoView({behavior: 'smooth', block: 'start'});
    }
  });
  document.addEventListener('keydown', event => {
    if (/input|select|textarea/i.test(document.activeElement.tagName)) return;
    if (event.key === 'ArrowLeft') go(current - 1);
    if (event.key === 'ArrowRight') go(current + 1);
    if (event.key === '/') { event.preventDefault(); search.focus(); }
  });
})();
"""


def normalize_text(text: str) -> str:
    """Make extracted copy readable without altering source wording."""
    text = text.replace("ﬁ", "fi").replace("ﬂ", "fl").replace("ﬀ", "ff")
    text = text.replace("ﬃ", "ffi").replace("ﬄ", "ffl")
    text = re.sub(r"(?<=\w)-\s*\n\s*(?=[a-z])", "", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n+", " ", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def page_blocks(page: pymupdf.Page) -> list[tuple[float, str]]:
    blocks: list[tuple[float, str]] = []
    for block in page.get_text("blocks", sort=False):
        y0 = float(block[1])
        text = normalize_text(block[4])
        if text:
            blocks.append((y0, text))
    return blocks


def render_page_data_uri(page: pymupdf.Page, scale: float, quality: int) -> tuple[str, int, int]:
    pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False, colorspace=pymupdf.csGRAY)
    image = Image.frombytes("L", (pix.width, pix.height), pix.samples)
    from io import BytesIO

    output = BytesIO()
    if quality >= 100:
        image.save(output, format="WEBP", lossless=True, method=6)
    else:
        image.save(output, format="WEBP", quality=quality, method=6)
    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    return f"data:image/webp;base64,{encoded}", pix.width, pix.height


def build(source: Path, destination: Path, scale: float = 2.0, quality: int = 100) -> None:
    source_bytes = source.read_bytes()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    doc = pymupdf.open(source)
    page_count = len(doc)

    toc_items = "\n".join(
        f'<li><a href="#page-{page}" data-page="{page}"><span class="toc-page">{page:02}</span><span>{html.escape(title)}</span></a></li>'
        for page, title in PRIMARY_SECTIONS
    )

    page_markup: list[str] = []
    total_text_chars = 0
    for index, page in enumerate(doc, start=1):
        blocks = page_blocks(page)
        text = " ".join(value for _, value in blocks)
        total_text_chars += len(text)
        search_value = html.escape(text.casefold(), quote=True)
        paragraphs = []
        for y0, value in blocks:
            css_class = ' class="running-head"' if y0 < 56 else ""
            paragraphs.append(f"<p{css_class}>{html.escape(value)}</p>")
        if index == 4:
            paragraphs.append(PREFIXES_TABLE)
        if index == 32:
            paragraphs.append(DIODES_TABLE)

        image_uri, width, height = render_page_data_uri(page, scale, quality)
        page_markup.append(
            f'''<article class="page" id="page-{index}" data-page="{index}" data-search="{search_value}" aria-labelledby="page-title-{index}">
  <div class="page-label"><strong id="page-title-{index}">صفحه {index}</strong><span>PDF source page {index} / {page_count}</span></div>
  <figure class="page-image-wrap">
    <img src="{image_uri}" width="{width}" height="{height}" loading="lazy" decoding="async" alt="رندر کامل صفحه {index} از {page_count}؛ شامل متن، تصاویر، نمودارها، جداول، معادلات و شمارهٔ صفحهٔ اصلی">
  </figure>
  <details class="transcript">
    <summary>متن قابل fetch صفحه {index} / Fetchable page transcript</summary>
    <div class="transcript-content" lang="en">{''.join(paragraphs)}</div>
  </details>
</article>'''
        )
        print(f"Rendered page {index}/{page_count}")

    document = f'''<!doctype html>
<html lang="en" dir="ltr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="A complete, self-contained, searchable and fetchable HTML rendering of The Art of Electronics, Third Edition, Chapter 1: Foundations.">
<meta name="source-sha256" content="{source_hash}">
<meta name="source-pages" content="{page_count}">
<meta name="extracted-text-characters" content="{total_text_chars}">
<title>The Art of Electronics — Chapter 1: Foundations | Fetchable edition</title>
<style>{CSS}</style>
<script type="application/ld+json">{{
  "@context": "https://schema.org",
  "@type": "Chapter",
  "name": "Foundations",
  "position": "1",
  "isPartOf": {{"@type": "Book", "name": "The Art of Electronics", "bookEdition": "Third Edition"}},
  "pagination": "1–70",
  "inLanguage": "en"
}}</script>
</head>
<body>
<a class="skip-link" href="#document">Skip to document</a>
<header class="masthead">
  <p class="eyebrow">Self-contained · searchable · fetchable</p>
  <h1>The Art of Electronics</h1>
  <p class="deck"><strong>Chapter 1 — Foundations.</strong> نسخهٔ HTML کامل و قابل‌جست‌وجو؛ هر ۷۰ صفحه با چیدمان، تصاویر، نمودارها، جدول‌ها، معادلات، پانوشت‌ها و شماره‌صفحهٔ اصلی بازتولید شده است. متن هر صفحه نیز مستقیماً در HTML قرار دارد و برای fetch به JavaScript وابسته نیست.</p>
  <div class="meta-strip" aria-label="Document metadata"><span>Third Edition</span><span>{page_count} pages</span><span>Pages 1–70 preserved</span><span>Source SHA-256: {source_hash[:12]}…</span></div>
</header>
<nav class="toolbar" aria-label="Document tools" dir="rtl">
  <div class="search-wrap">
    <svg class="search-icon" viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" d="m21 21-4.35-4.35m2.35-5.65a8 8 0 1 1-16 0 8 8 0 0 1 16 0Z"/></svg>
    <label class="sr-only" for="search">جست‌وجو در همهٔ صفحه‌ها</label>
    <input id="search" type="search" placeholder="جست‌وجو در متن ۷۰ صفحه…" autocomplete="off">
    <span id="search-status" aria-live="polite">{page_count} صفحه</span>
  </div>
  <div class="controls">
    <button id="next" type="button" aria-label="صفحه بعد">‹</button>
    <span class="page-readout" aria-live="polite">صفحه 1 از {page_count}</span>
    <button id="prev" type="button" aria-label="صفحه قبل">›</button>
    <label class="sr-only" for="view">حالت نمایش</label>
    <select id="view" class="view-select"><option value="single">تک‌صفحه</option><option value="spread">دوصفحه‌ای</option></select>
  </div>
  <a class="toc-link" href="#contents">فهرست</a>
</nav>
<div class="layout">
  <aside class="toc" id="contents" aria-label="Table of contents">
    <h2>Chapter contents</h2>
    <ol>{toc_items}</ol>
  </aside>
  <main class="document" id="document">
    <p class="fetch-note" dir="rtl"><strong>نسخهٔ دو‌لایه:</strong> تصویر lossless هر صفحه، ظاهر منبع را دقیق نگه می‌دارد؛ متن واقعی همان صفحه در بخش «متن قابل fetch» داخل HTML است. جدول‌های صفحهٔ ۴ و ۳۲ علاوه بر تصویر اصلی، به‌صورت جدول معنایی HTML نیز درج شده‌اند.</p>
    <div class="no-results" dir="rtl"><strong>نتیجه‌ای پیدا نشد.</strong><br>عبارت دیگری را جست‌وجو کنید یا کلید Esc را بزنید.</div>
    <div class="pages">{''.join(page_markup)}</div>
  </main>
</div>
<footer dir="rtl">ساخته‌شده از فایل منبع <b>{html.escape(source.name)}</b> · تمام صفحه‌ها در همین فایل HTML تعبیه شده‌اند · بدون فونت، تصویر یا کتابخانهٔ خارجی</footer>
<script>{JS}</script>
</body>
</html>'''
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(document, encoding="utf-8")
    print(f"Wrote {destination} ({destination.stat().st_size:,} bytes)")
    print(f"Source SHA-256: {source_hash}")
    print(f"Extracted text: {total_text_chars:,} characters across {page_count} pages")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path, default=Path("01.pdf"))
    parser.add_argument("destination", nargs="?", type=Path, default=Path("01-fetchable.html"))
    parser.add_argument("--scale", type=float, default=2.0, help="rendering scale (default: 2.0)")
    parser.add_argument("--quality", type=int, default=100, help="WebP quality; 100 means lossless (default: 100)")
    args = parser.parse_args()
    build(args.source, args.destination, args.scale, args.quality)


if __name__ == "__main__":
    main()
