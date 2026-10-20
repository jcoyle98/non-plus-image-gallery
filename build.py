#!/usr/bin/env python3
"""Build the gallery into _site/. No dependencies beyond Python 3.

    python3 build.py           # build once
    python3 build.py --serve   # build and serve at http://localhost:8002

Everything comes from catalog.json; images live in images/<section>/.
To add an image, use tools/add_image.py (see README.md).
"""

import html
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "_site"
cat = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
SECTIONS, IMAGES, PALETTES = cat["sections"], cat["images"], cat.get("palettes", [])
e = html.escape


def credit(img):
    lic = f'<a href="{e(img["licence_url"])}" target="_blank" rel="noopener">{e(img["licence"])}</a>' if img.get("licence_url") else e(img["licence"])
    return f'{e(img["artist"])} · {lic} · <a href="{e(img["source"])}" target="_blank" rel="noopener">source</a>'


def tile(img):
    name = Path(img["file"]).name
    w, h = img.get("original_size") or (None, None)
    full = (f'<a href="{e(img["original"])}" target="_blank" rel="noopener">Full resolution{f" ({w}×{h})" if w else ""} ↗</a>'
            if img.get("original") else "")
    return (f'<figure id="{img["id"]}"><a href="{e(img["file"])}" target="_blank"><img loading="lazy" src="{e(img["file"])}" alt="{e(img["title"])}"></a>'
            f'<figcaption><b>{img["id"]}</b> {e(img["title"])}<br><span class="credit">{credit(img)}</span>'
            f'<span class="dl"><a class="btn" href="{e(img["file"])}" download="{e(name)}">Download</a>{full}</span></figcaption></figure>')


def palette_svg(pal):
    """A palette as a small vector file: five swatches with their hex codes. Opens in Illustrator."""
    sw = "".join(f'<rect x="{i * 200}" y="0" width="200" height="200" fill="{c}"/>'
                 f'<text x="{i * 200 + 12}" y="228" font-family="Helvetica, Arial, sans-serif" font-size="18" fill="#222">{c}</text>'
                 for i, c in enumerate(pal["colours"]))
    title = f'{pal["artist"]}, {pal["painting"]}' + (f' ({pal["date"]})' if pal["date"] else "")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="290" viewBox="0 0 1000 290">'
            f'<rect width="1000" height="290" fill="#fff"/>{sw}'
            f'<text x="12" y="270" font-family="Helvetica, Arial, sans-serif" font-size="16" fill="#555">{e(title)} · {e(pal["credit"])}</text></svg>\n')


def palette_card(pal):
    name = f'palette-{pal["id"]:02d}.svg'
    swatches = "".join(f'<button class="sw" style="background:{c}" data-hex="{c}" title="Copy {c}"><span>{c}</span></button>' for c in pal["colours"])
    date = f' ({e(pal["date"])})' if pal["date"] else ""
    return (f'<figure class="pal" id="palette-{pal["id"]}"><div class="sws">{swatches}</div>'
            f'<figcaption><b>{pal["id"]}</b> {e(pal["artist"])}, <i>{e(pal["painting"])}</i>{date}<br>'
            f'<span class="credit"><a href="{e(pal["source"])}" target="_blank" rel="noopener">{e(pal["credit"])}</a> · click a colour to copy its code</span>'
            f'<span class="dl"><a class="btn" href="palettes/{name}" download="{name}">Download</a></span></figcaption></figure>')


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "images", OUT / "images")
    (OUT / ".nojekyll").touch()
    (OUT / "palettes").mkdir()
    for pal in PALETTES:
        (OUT / "palettes" / f'palette-{pal["id"]:02d}.svg').write_text(palette_svg(pal), encoding="utf-8")

    nav, body = [], []
    for key, label in SECTIONS.items():
        items = [i for i in IMAGES if i["section"] == key]
        if not items:
            continue
        nav.append(f'<a href="#{key}">{e(label)} <small>{len(items)}</small></a>')
        body.append(f'<h2 id="{key}">{e(label)}</h2><div class="grid">{"".join(tile(i) for i in items)}</div>')
    if PALETTES:
        nav.append(f'<a href="#palettes">Colour palettes <small>{len(PALETTES)}</small></a>')
        body.append(f'<h2 id="palettes">Colour palettes</h2><div class="pgrid">{"".join(palette_card(p) for p in PALETTES)}</div>')

    (OUT / "index.html").write_text(f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Non Plus image gallery</title>
<meta name="description" content="Radar screens, particle tracks, cells and embryos: {len(IMAGES)} openly licensed images, free to download.">
<style>
 :root {{ --bg:#121012; --fg:#e8e1ea; --muted:#9a909d; --line:#2a252b; --accent:#8ec6ab; }}
 * {{ box-sizing:border-box; }}
 body {{ margin:0; background:var(--bg); color:var(--fg); font:15px/1.45 -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif; }}
 header, main, footer {{ max-width:1500px; margin:0 auto; padding:0 1.25rem; }}
 header {{ padding:2.5rem 1.25rem 1.2rem; }} h1 {{ margin:0 0 .4rem; font-weight:700; letter-spacing:-.01em; }}
 header p {{ color:var(--muted); margin:.2rem 0; max-width:46rem; }}
 nav {{ position:sticky; top:0; z-index:2; background:#121012ee; backdrop-filter:blur(6px); padding:.7rem 1.25rem; display:flex; flex-wrap:wrap; gap:1.2rem; justify-content:center; border-bottom:1px solid var(--line); }}
 nav a {{ color:var(--fg); text-decoration:none; }} nav small {{ color:var(--muted); }}
 h2 {{ margin:2.5rem 0 1rem; scroll-margin-top:4rem; }}
 .grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(250px, 1fr)); gap:1.6rem 1.2rem; }}
 figure {{ margin:0; }}
 figure img {{ width:100%; aspect-ratio:1; object-fit:cover; display:block; background:#000; }}
 figcaption {{ margin-top:.5rem; font-size:.82rem; color:#c9c0cc; }}
 figcaption b {{ color:#fff; font-size:1rem; margin-right:.25rem; }}
 .credit {{ color:var(--muted); }} .credit a {{ color:inherit; }}
 .dl {{ display:flex; gap:.8rem; align-items:center; margin-top:.5rem; flex-wrap:wrap; }}
 .dl a {{ color:var(--fg); }}
 .btn {{ padding:.3rem .7rem; border:1px solid var(--fg); border-radius:3px; text-decoration:none; }}
 .btn:hover {{ background:var(--fg); color:var(--bg) !important; }}
 footer {{ color:var(--muted); padding:3rem 1.25rem; font-size:.85rem; }}
 .pgrid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(340px, 1fr)); gap:2rem 1.6rem; }}
 .sws {{ display:flex; height:9rem; }}
 .sw {{ flex:1; border:0; padding:0; cursor:pointer; position:relative; font:inherit; }}
 .sw span {{ position:absolute; left:0; right:0; bottom:-1.6rem; font-size:.72rem; color:var(--muted); font-family:ui-monospace, Menlo, monospace; }}
 .sw.copied span {{ color:var(--accent); }}
 .pal figcaption {{ margin-top:2.2rem; }}
</style></head><body>
<header>
 <h1>Non Plus image gallery</h1>
 <p>{len(IMAGES)} images of radar screens, particle tracks, cells and embryos, collected for the Non Plus collective.
 Everything here is public domain or Creative Commons; each image lists its author and licence.</p>
 <p>Click <b>Download</b> to save an image, or follow <b>Full resolution</b> for the original at its source.
 If you use an image, credit it as its caption says.</p>
</header>
<nav>{"".join(nav)}</nav>
<main>{"".join(body)}</main>
<footer>Images from Wikimedia Commons and the Wellcome Collection, under the licences shown. Gallery maintained by the Non Plus collective.</footer>
<script>
 document.querySelectorAll(".sw").forEach(b => b.addEventListener("click", async () => {{
   try {{ await navigator.clipboard.writeText(b.dataset.hex); }} catch (_) {{ return; }}
   const s = b.querySelector("span"), t = s.textContent; b.classList.add("copied"); s.textContent = "copied";
   setTimeout(() => {{ b.classList.remove("copied"); s.textContent = t; }}, 1200);
 }}));
</script>
</body></html>
''', encoding="utf-8")
    print(f"Built {len(IMAGES)} images and {len(PALETTES)} palettes into _site/")


if __name__ == "__main__":
    build()
    if "--serve" in sys.argv:
        import functools
        import http.server
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
        print("Serving at http://localhost:8002  (Ctrl-C to stop)")
        http.server.ThreadingHTTPServer(("localhost", 8002), handler).serve_forever()
