"""Per-video font subsetting: keep only the glyphs a built project actually uses.

Every project used to copy all fonts (10–37 MB: Noto Sans KR VF, Noto Serif KR VF, Pretendard ×4 …) and the renderer loaded them
in every composition. subset_project(out) scans the project's HTML, subsets each referenced font from ROOT/assets to the
characters present (+ printable ASCII, digits for count-ups), writes it in place and deletes fonts nobody references.
Results are cached in data/font_cache by (font, charset).

Usage: python -I tools/fontsub.py <project dir> [...]
"""
import glob
import hashlib
import os
import re
import shutil
import sys

from fontTools import subset

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import ROOT  # noqa: E402

CACHE = os.path.join(ROOT, "data", "font_cache")
SOURCES = {"assets/fonts/serif/": os.path.join(ROOT, "assets", "fonts_serif")}
EXTRA = "".join(chr(c) for c in range(0x20, 0x7F)) + "–—·…“”‘’%℃°×→←↑↓▲▼◀▶※•○●■□"


def source_of(rel):
    for pre, d in SOURCES.items():
        if rel.startswith(pre):
            return os.path.join(d, rel[len(pre):])
    return os.path.join(ROOT, rel.replace("/", os.sep))


def subset_project(out):
    html = [open(p, encoding="utf-8").read() for p in [os.path.join(out, "index.html")] + glob.glob(os.path.join(out, "compositions", "*.html"))]
    text = "".join(html)
    used = sorted(set(re.findall(r'url\("(assets/fonts/[^"]+)"\)', text)))
    chars = "".join(sorted(set(text) | set(EXTRA)))
    key = hashlib.sha1(chars.encode("utf-8")).hexdigest()[:12]
    os.makedirs(CACHE, exist_ok=True)
    saved = 0
    for rel in used:
        src, dst = source_of(rel), os.path.join(out, rel.replace("/", os.sep))
        if not os.path.exists(src):
            continue
        cached = os.path.join(CACHE, f"{hashlib.sha1(rel.encode()).hexdigest()[:8]}-{key}-{os.path.basename(rel)}")
        if not os.path.exists(cached):
            opts = subset.Options()
            opts.layout_features = ["*"]
            opts.name_IDs = ["*"]
            opts.notdef_outline = True
            opts.flavor = "woff2" if rel.endswith(".woff2") else None
            font = subset.load_font(src, opts)
            sub = subset.Subsetter(opts)
            sub.populate(text=chars)
            sub.subset(font)
            subset.save_font(font, cached + ".part", opts)
            os.replace(cached + ".part", cached)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(cached, dst)
        saved += os.path.getsize(src) - os.path.getsize(dst)
    keep = {os.path.normpath(os.path.join(out, r.replace("/", os.sep))) for r in used}
    for p in glob.glob(os.path.join(out, "assets", "fonts", "**", "*.*"), recursive=True):
        if p.lower().endswith((".ttf", ".otf", ".woff", ".woff2")) and os.path.normpath(p) not in keep:
            os.remove(p)
    return len(used), saved


if __name__ == "__main__":
    for d in sys.argv[1:]:
        n, saved = subset_project(d)
        print(d, f"{n} fonts, saved {saved / 1e6:.1f} MB")
