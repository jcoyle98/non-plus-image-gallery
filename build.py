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


from palettes import build_palette_page


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "images", OUT / "images")
    (OUT / ".nojekyll").touch()
    build_palette_page(PALETTES, OUT / "palettes")

    nav, body = [], []
    for key, label in SECTIONS.items():
        items = [i for i in IMAGES if i["section"] == key]
        if not items:
            continue
        nav.append(f'<a href="#{key}">{e(label)} <small>{len(items)}</small></a>')
        body.append(f'<h2 id="{key}">{e(label)}</h2><div class="grid">{"".join(tile(i) for i in items)}</div>')
    if PALETTES:
        nav.append(f'<a href="palettes/">Colour palettes <small>{len(PALETTES)}</small> →</a>')

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
