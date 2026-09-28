#!/usr/bin/env python3
"""Split a PDF into independently fetchable, visually faithful HTML pages.

Output layout:
  index.html, manifest.json, styles.css
  pages/page-001.html ...
  images/page-001.webp ...
  text/page-001.txt ...
  data/page-001.json ...

Each HTML response contains that page's extracted text in the response body (no
JavaScript needed). A lossless WebP render preserves every visual detail of the
source, including tables, figures, equations, footnotes, and printed page nums.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from io import BytesIO
from pathlib import Path

import pymupdf
from PIL import Image

CSS = """*{box-sizing:border-box}html{background:#e9e6e0;color:#201d19;font-family:system-ui,sans-serif}body{margin:0}header,main,footer{width:min(100% - 2rem,880px);margin:auto}header{display:flex;align-items:center;justify-content:space-between;gap:1rem;padding:1rem 0}.nav{display:flex;gap:.5rem}.nav a,.back{display:inline-block;padding:.55rem .8rem;border:1px solid #bbb3a8;border-radius:.5rem;background:#fff;color:#352f29;text-decoration:none}.nav a[aria-disabled=true]{opacity:.35;pointer-events:none}.meta{color:#6c645b;font-size:.82rem}.sheet{margin:0;background:#fff;box-shadow:0 14px 40px #3c33262b}.sheet img{display:block;width:100%;height:auto}.transcript{margin:1rem 0 2rem;background:#fff;border:1px solid #cec7be;border-radius:.65rem}.transcript summary{cursor:pointer;padding:.8rem 1rem;font-weight:650}.text{padding:0 1.2rem 1rem;font-family:Georgia,serif;line-height:1.65}.text p{margin:.85rem 0}footer{padding:0 0 2rem;color:#756d64;font-size:.78rem}@media print{@page{margin:0}header,.transcript,footer{display:none}main{width:100%}.sheet{box-shadow:none}.sheet img{width:100vw;height:100vh;object-fit:contain}}"""

INDEX_CSS = """*{box-sizing:border-box}html{background:#eeeae4;color:#211e1a;font-family:system-ui,sans-serif}body{width:min(100% - 2rem,1050px);margin:3rem auto}h1{font-family:Georgia,serif;font-size:clamp(2rem,6vw,4rem);margin-bottom:.4rem}p{color:#655e56;line-height:1.6}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(9rem,1fr));gap:.7rem;margin:2rem 0}.grid a{padding:1rem;border:1px solid #c9c1b7;border-radius:.65rem;background:#fff;color:#302a24;text-decoration:none}.grid a:hover{border-color:#a95d35;box-shadow:0 5px 20px #4a38231a}.grid small{display:block;color:#81776d;margin-top:.35rem}code{background:#fff;padding:.15rem .35rem;border-radius:.25rem}"""


def normalize(text: str) -> str:
    for a, b in (("ﬁ", "fi"), ("ﬂ", "fl"), ("ﬀ", "ff"), ("ﬃ", "ffi"), ("ﬄ", "ffl")):
        text = text.replace(a, b)
    text = re.sub(r"(?<=\w)-\s*\n\s*(?=[a-z])", "", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def blocks(page: pymupdf.Page) -> list[str]:
    return [value for item in page.get_text("blocks", sort=True) if (value := normalize(item[4]))]


def render(page: pymupdf.Page, scale: float) -> tuple[bytes, int, int]:
    pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False, colorspace=pymupdf.csRGB)
    image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    output = BytesIO()
    image.save(output, "WEBP", lossless=True, method=6)
    return output.getvalue(), pix.width, pix.height


def build(source: Path, output: Path, scale: float) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for name in ("pages", "images", "text", "data"):
        (output / name).mkdir(exist_ok=True)
    (output / "styles.css").write_text(CSS, encoding="utf-8")

    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    doc = pymupdf.open(source)
    count = len(doc)
    manifest_pages = []

    for number, page in enumerate(doc, 1):
        slug = f"page-{number:03d}"
        page_blocks = blocks(page)
        text = "\n\n".join(page_blocks)
        image, width, height = render(page, scale)
        (output / "images" / f"{slug}.webp").write_bytes(image)
        (output / "text" / f"{slug}.txt").write_text(text + "\n", encoding="utf-8")
        record = {
            "page": number, "pageCount": count, "source": source.name,
            "sourceSha256": source_hash, "width": width, "height": height,
            "html": f"pages/{slug}.html", "image": f"images/{slug}.webp",
            "text": f"text/{slug}.txt"
        }
        (output / "data" / f"{slug}.json").write_text(json.dumps({**record, "content": text}, ensure_ascii=False, indent=2), encoding="utf-8")
        manifest_pages.append(record)

        paragraphs = "".join(f"<p>{html.escape(part)}</p>" for part in page_blocks)
        prev_link = f"page-{number-1:03d}.html" if number > 1 else "#"
        next_link = f"page-{number+1:03d}.html" if number < count else "#"
        prev_disabled = ' aria-disabled="true"' if number == 1 else ""
        next_disabled = ' aria-disabled="true"' if number == count else ""
        document = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Page {number} of {count}</title><meta name="source-page" content="{number}"><link rel="stylesheet" href="../styles.css">
<link rel="prev" href="{prev_link}"><link rel="next" href="{next_link}"></head><body>
<header><div><a class="back" href="../index.html">All pages</a> <span class="meta">Source page {number} / {count}</span></div>
<nav class="nav" aria-label="Page navigation"><a href="{prev_link}"{prev_disabled}>Previous</a><a href="{next_link}"{next_disabled}>Next</a></nav></header>
<main><h1 class="meta">Page {number}</h1><figure class="sheet"><img src="../images/{slug}.webp" width="{width}" height="{height}" alt="Complete visual rendering of source PDF page {number}"></figure>
<details class="transcript" open><summary>Fetchable text — page {number}</summary><div class="text">{paragraphs}</div></details></main>
<footer>Visual layout, figures, tables, equations, footnotes, and original printed page number are preserved in the lossless page image. <a href="../text/{slug}.txt">Plain text</a> · <a href="../data/{slug}.json">JSON</a></footer>
</body></html>'''
        (output / "pages" / f"{slug}.html").write_text(document, encoding="utf-8")
        print(f"Built {number}/{count}")

    manifest = {"source": source.name, "sourceSha256": source_hash, "pageCount": count, "pages": manifest_pages}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    cards = "".join(f'<a href="pages/page-{n:03d}.html">Page {n}<small>HTML · TXT · JSON</small></a>' for n in range(1, count + 1))
    index = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fetchable PDF — {count} pages</title><style>{INDEX_CSS}</style></head><body>
<h1>Fetchable PDF pages</h1><p>All {count} source pages are separate URLs. Each HTML file includes server-delivered searchable text and a lossless visual rendering that preserves images, tables, equations, and printed page numbers. Machine-readable endpoints are listed in <a href="manifest.json"><code>manifest.json</code></a>.</p><main class="grid">{cards}</main><p>Source: <code>{html.escape(source.name)}</code> · SHA-256: <code>{source_hash}</code></p></body></html>'''
    (output / "index.html").write_text(index, encoding="utf-8")
    print(f"Wrote {output}: {count} independent pages")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path, default=Path("01.pdf"))
    parser.add_argument("output", nargs="?", type=Path, default=Path("fetchable-pages"))
    parser.add_argument("--scale", type=float, default=2.0)
    args = parser.parse_args()
    build(args.source, args.output, args.scale)
