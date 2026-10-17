# Notes for Claude

This repo is a public image gallery that people download from. When asked to add images, follow
**"Adding images" in README.md** exactly. In short:

1. **Rights first.** Only public domain, CC0, CC BY / CC BY-SA, or explicit permission from the creator.
   If the source or permission is unclear, ask before adding anything. Never add NC/ND or unknown-rights images.
2. Use `tools/add_image.py`. Prefer `--commons "File:..."` for Wikimedia Commons images; for anything else,
   pass `--title`, `--artist`, `--licence`, `--contributor` (who sent it and how permission was given) and `--source`.
3. Run `python3 build.py`, check the new entry renders, then commit (`Add image NNN: <title>`) and push to `main`.
4. Never renumber or reuse image IDs. People refer to images by number.
