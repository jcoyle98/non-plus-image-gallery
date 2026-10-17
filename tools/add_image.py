#!/usr/bin/env python3
"""Add an image to the gallery: resize it, save it under images/<section>/, and add it to catalog.json.

From a Wikimedia Commons file (title, author, licence and source are filled in automatically):

    python3 tools/add_image.py --commons "File:Hurricane Gracie on radar scope in September 1959.jpg" --section radar

From a local file or URL (you supply the details):

    python3 tools/add_image.py path/or/url.jpg --section cells \\
        --title "Dividing cells" --artist "Jane Doe" \\
        --licence "CC BY 4.0" --licence-url https://creativecommons.org/licenses/by/4.0/ \\
        --source https://example.org/page --contributor "Jane Doe (sent by email, 2026-10-20)"

Then run `python3 build.py` to rebuild, and commit and push to publish.
"""

import argparse
import io
import json
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

from PIL import Image  # pip install pillow

ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "NonPlusImageGallery/1.0 (https://github.com/jcoyle98/non-plus-image-gallery)"}
OPEN_LICENCES = re.compile(r"^(public domain|cc0|cc by(-sa)?\b|cc-by|permission)", re.I)


def slug(text):
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:60] or "image"


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


def commons(title):
    title = title if title.startswith("File:") else "File:" + title
    q = urllib.parse.urlencode({"action": "query", "titles": title, "prop": "imageinfo",
                                "iiprop": "url|size|extmetadata", "iiurlwidth": 1600, "format": "json"})
    page = next(iter(json.loads(fetch("https://commons.wikimedia.org/w/api.php?" + q))["query"]["pages"].values()))
    if "imageinfo" not in page:
        sys.exit(f"Not found on Commons: {title}")
    ii = page["imageinfo"][0]
    m = ii.get("extmetadata", {})
    clean = lambda v: re.sub(r"\s+", " ", re.sub("<.*?>", "", v or "")).strip()
    return {
        "data": fetch(ii.get("thumburl") or ii["url"]),
        "title": re.sub(r"\s+", " ", title[5:].rsplit(".", 1)[0].replace("_", " ")),
        "artist": clean(m.get("Artist", {}).get("value"))[:160] or "Unknown",
        "licence": clean(m.get("LicenseShortName", {}).get("value")),
        "licence_url": m.get("LicenseUrl", {}).get("value", ""),
        "source": ii["descriptionurl"], "original": ii["url"], "original_size": [ii.get("width"), ii.get("height")],
        "contributor": "Wikimedia Commons",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image", nargs="?", help="local path or URL of the image (not needed with --commons)")
    ap.add_argument("--commons", help='a Wikimedia Commons file title, e.g. "File:Example.jpg"')
    ap.add_argument("--section", required=True)
    ap.add_argument("--title"); ap.add_argument("--artist"); ap.add_argument("--licence"); ap.add_argument("--licence-url", default="")
    ap.add_argument("--source", default=""); ap.add_argument("--original", default="")
    ap.add_argument("--contributor", help="who sent it, and how/when permission was given")
    a = ap.parse_args()

    cat_path = ROOT / "catalog.json"
    cat = json.loads(cat_path.read_text(encoding="utf-8"))
    if a.section not in cat["sections"]:
        sys.exit(f"Unknown section '{a.section}'. Use one of: {', '.join(cat['sections'])} "
                 f"(or add a new one to \"sections\" in catalog.json first).")

    if a.commons:
        info = commons(a.commons)
        for k in ("title", "artist", "licence", "licence_url", "source", "contributor"):  # let flags override
            v = getattr(a, k.replace("-", "_"), None)
            if v:
                info[k] = v
    else:
        if not a.image:
            sys.exit("Give an image path/URL, or --commons.")
        missing = [f for f in ("title", "artist", "licence", "contributor") if not getattr(a, f)]
        if missing:
            sys.exit("Missing: " + ", ".join("--" + m for m in missing) + ". Every image needs a title, an author, a licence and a contributor.")
        data = fetch(a.image) if re.match(r"https?://", a.image) else Path(a.image).read_bytes()
        info = {"data": data, "title": a.title, "artist": a.artist, "licence": a.licence, "licence_url": a.licence_url,
                "source": a.source or (a.image if a.image.startswith("http") else ""), "original": a.original,
                "original_size": None, "contributor": a.contributor}

    dupes = [i for i in cat["images"] if info.get("source") and i.get("source") == info["source"]]
    if dupes:
        sys.exit(f"Already in the gallery as #{dupes[0]['id']}: {dupes[0]['title']}")

    if not OPEN_LICENCES.search(info["licence"] or ""):
        sys.exit(f"Licence '{info['licence']}' is not public domain, CC0, CC BY/BY-SA, or 'Permission from ...'. "
                 "Only add images we're allowed to share and let others download.")

    im = Image.open(io.BytesIO(info.pop("data"))).convert("RGB")
    if not info.get("original_size"):
        info["original_size"] = list(im.size)
    im.thumbnail((1600, 1600))
    new_id = max((i["id"] for i in cat["images"]), default=0) + 1
    rel = f"images/{a.section}/{new_id:03d}-{slug(info['title'])}.jpg"
    (ROOT / rel).parent.mkdir(parents=True, exist_ok=True)
    im.save(ROOT / rel, "JPEG", quality=86, optimize=True, progressive=True)

    cat["images"].append({"id": new_id, "file": rel, "section": a.section, **info, "added": str(date.today())})
    cat_path.write_text(json.dumps(cat, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Added #{new_id}: {info['title']}  ->  {rel}")


if __name__ == "__main__":
    main()
