"""The colour palettes page: _site/palettes/index.html, plus one downloadable SVG per palette."""

import html
from pathlib import Path


def rgb(hex_):
    return tuple(int(hex_[i:i + 2], 16) for i in (1, 3, 5))


def luminance(hex_):
    def ch(c):
        c /= 255
        return c / 12.92 if c <= .03928 else ((c + .055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb(hex_))
    return .2126 * r + .7152 * g + .0722 * b


def svg(pal):
    w = 200 * len(pal["colours"])   # palettes have two to five colours
    sw = "".join(f'<rect x="{i * 200}" y="0" width="200" height="200" fill="{c}"/>'
                 f'<text x="12" y="228" transform="translate({i * 200} 0)" font-family="Helvetica, Arial, sans-serif" font-size="18" fill="#222">{c}</text>'
                 for i, c in enumerate(pal["colours"]))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="250" viewBox="0 0 {w} 250">'
            f'<rect width="{w}" height="250" fill="#fff"/>{sw}</svg>\n')


def card(pal):
    n = pal["id"]
    sw = "".join(
        f'<button class="sw" style="background:{c};color:{"#fff" if luminance(c) < .22 else "#111"}" data-copy="{c}" title="Click to copy {c}">'
        f'<span class="hex">{c.upper()}</span><span class="rgb">{", ".join(map(str, rgb(c)))}</span></button>'
        for c in pal["colours"])
    css = ":root {\\n" + "".join(f"  --colour-{i}: {c};\\n" for i, c in enumerate(pal["colours"], 1)) + "}"
    return (f'<section class="pal" id="p{n}"><h2>{n:02d}</h2><div class="sws" style="grid-template-columns:repeat({len(pal["colours"])}, 1fr)">{sw}</div>'
            f'<div class="tools"><button class="btn" data-copy="{css}">Copy as CSS</button>'
            f'<a class="btn" href="palette-{n:02d}.svg" download="palette-{n:02d}.svg">Download SVG</a></div></section>')


def build_palette_page(palettes, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    for pal in palettes:
        (out / f'palette-{pal["id"]:02d}.svg').write_text(svg(pal), encoding="utf-8")
    credits = sorted({(p["credit"], p.get("source", "")) for p in palettes})
    name = lambda c: html.escape(c.replace("Palette by ", ""))
    credit = " and ".join(f'<a href="{html.escape(u)}" target="_blank" rel="noopener">{name(c)}</a>' if u else name(c) for c, u in credits)
    (out / "index.html").write_text(f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Non Plus colour palettes</title>
<style>
 * {{ box-sizing:border-box; }}
 body {{ margin:0; background:#121012; color:#e8e1ea; font:15px/1.45 -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif; }}
 header, main {{ max-width:1200px; margin:0 auto; padding:0 1.25rem; }}
 header {{ padding-top:2.5rem; }} h1 {{ margin:0 0 .4rem; }} header p {{ color:#9a909d; margin:.2rem 0; }}
 header a {{ color:inherit; }}
 main {{ padding-bottom:4rem; }}
 .pal {{ margin-top:3rem; }}
 .pal h2 {{ font:700 1rem ui-monospace, Menlo, monospace; color:#9a909d; margin:0 0 .6rem; }}
 .sws {{ display:grid; grid-template-columns:repeat(5, 1fr); border-radius:4px; overflow:hidden; }}
 .sw {{ border:0; height:11rem; padding:.8rem; text-align:left; cursor:pointer; display:flex; flex-direction:column; justify-content:flex-end; gap:.15rem; font:inherit; }}
 .sw .hex {{ font:700 1.05rem ui-monospace, Menlo, monospace; letter-spacing:.02em; }}
 .sw .rgb {{ font:.75rem ui-monospace, Menlo, monospace; opacity:.75; }}
 .sw:hover .hex::after {{ content:"  copy"; font-weight:400; opacity:.6; }}
 .tools {{ display:flex; gap:.7rem; margin:.8rem 0; flex-wrap:wrap; }}
 .btn {{ font:inherit; font-size:.85rem; padding:.35rem .8rem; border:1px solid #e8e1ea; border-radius:3px; background:none; color:#e8e1ea; cursor:pointer; text-decoration:none; }}
 .btn:hover {{ background:#e8e1ea; color:#121012; }}
 .toast {{ position:fixed; left:50%; bottom:1.5rem; transform:translateX(-50%); background:#e8e1ea; color:#121012; padding:.5rem .9rem; border-radius:4px; font-size:.85rem; opacity:0; transition:opacity .2s; pointer-events:none; }}
 .toast.on {{ opacity:1; }}
 @media (max-width:640px) {{ .sw {{ height:8rem; padding:.5rem; }} .sw .hex {{ font-size:.8rem; }} .sw .rgb {{ display:none; }} }}
</style></head><body>
<header><h1>Colour palettes</h1>
<p>{len(palettes)} palettes, by {credit}. Click any colour to copy its hex code.</p>
<p><a href="../">← Back to the image gallery</a></p></header>
<main>{"".join(card(p) for p in palettes)}</main>
<div class="toast" id="toast"></div>
<script>
 const toast = document.getElementById("toast");
 document.querySelectorAll("[data-copy]").forEach(el => el.addEventListener("click", async () => {{
   const text = el.dataset.copy.replace(/\\\\n/g, "\\n");
   try {{ await navigator.clipboard.writeText(text); }} catch (_) {{ return; }}
   toast.textContent = "Copied " + (text.startsWith(":root") ? "CSS" : text);
   toast.classList.add("on"); clearTimeout(toast.t); toast.t = setTimeout(() => toast.classList.remove("on"), 1300);
 }}));
</script>
</body></html>
''', encoding="utf-8")
