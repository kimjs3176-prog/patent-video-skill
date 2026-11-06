"""Burned-in captions for the narration, plus an .srt beside the video.

narration.narrate() hands over the voiced lines it placed (start, length, text). Each line is split into caption-sized
chunks (sentences first, then at commas, then at spaces), and each chunk gets a share of its clip's length by the number
of syllables it holds, plus a breath at sentence ends. The cues become compositions/captions.html, a layer above every
scene (and above the transitions), and narration.srt. Text uses the bundled Pretendard (OFL).

Usage: called by narration.py; python -I tools/captions.py <project dir> rebuilds the layer from the project's narration.srt.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import E  # noqa: E402

FONT = "assets/fonts/pretendard/Pretendard-SemiBold.woff2"
# Captions get a band of their own at the bottom: while they are on, every scene is moved up by BAND px (its top margin
# is empty in every template), or, for a template with a masthead at the very top (I), scaled down from the top centre
# so nothing of the scene is lost. The captions then never cover anything a scene shows.
BAND = {"wide": 64, "tall": 136}  # 9:16 holds two caption lines
SCALE_PREFIX = ("i",)  # scene files of template I: i1-front, i2-how, …


def _units(s):
    return len(re.sub(r"\s", "", s))


def chunks(text, maxlen):
    """Caption-sized pieces of one voiced line, in reading order."""
    out = []
    for sent in [x for x in re.split(r"(?<=[.!?])\s+", text.strip()) if x]:
        if _units(sent) <= maxlen:
            out.append(sent)
            continue
        parts, cur = [], ""
        for piece in re.split(r"(?<=,)\s+", sent):  # commas first: where the voice breathes
            if cur and _units(cur + " " + piece) > maxlen:
                parts.append(cur)
                cur = piece
            else:
                cur = (cur + " " + piece).strip()
        parts.append(cur)
        for p in parts:  # still too long: break at the space nearest the middle, repeatedly
            stack = [p]
            while stack:
                q = stack.pop(0)
                if _units(q) <= maxlen or " " not in q:
                    out.append(q)
                    continue
                words = q.split(" ")
                best = min(range(1, len(words)), key=lambda k: abs(_units(" ".join(words[:k])) - _units(q) / 2))
                stack[:0] = [" ".join(words[:best]), " ".join(words[best:])]
    merged = []  # no orphans: a scrap of a few syllables ("추출,") joins its neighbour when the pair still fits
    for piece in out:
        if merged and (_units(piece) < 6 or _units(merged[-1]) < 6) and _units(merged[-1] + piece) <= maxlen * 1.25 \
                and merged[-1].rstrip()[-1:] not in ".!?":
            merged[-1] = merged[-1] + " " + piece
        else:
            merged.append(piece)
    return merged


def cues(lines, maxlen):
    """[(start, end, text)] for voiced lines [(start, dur, text)]."""
    res = []
    for start, dur, text in lines:
        cs = chunks(text, maxlen)
        if not cs:
            continue
        w = [_units(c) + (3 if c.rstrip()[-1:] in ".!?" else 1) for c in cs]  # a breath after a sentence
        t, tot = start + 0.05, sum(w)
        span = max(0.5, dur - 0.1)
        for c, k in zip(cs, w):
            d = span * k / tot
            res.append((round(t, 2), round(t + d, 2), c))
            t += d
    return res


def srt(cs):
    def ts(x):
        h, r = divmod(x, 3600)
        m, s = divmod(r, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"
    return "\n".join(f"{i}\n{ts(a)} --> {ts(b)}\n{t}\n" for i, (a, b, t) in enumerate(cs, 1))


def read_srt(path):
    out = []
    for block in open(path, encoding="utf-8").read().strip().split("\n\n"):
        ln = block.strip().splitlines()
        if len(ln) < 3:
            continue
        a, b = [sum(float(x) * f for x, f in zip(p.replace(",", ".").split(":"), (3600, 60, 1))) for p in ln[1].split(" --> ")]
        out.append((a, b, " ".join(ln[2:])))
    return out


def composition(cs, w, h, total):
    vertical = h > w
    band = BAND["tall" if vertical else "wide"]
    size, maxw = (42, 960) if vertical else (34, 1800)
    divs = "\n".join(f'      <div class="ncap" id="ncap-{i}"><span>{E(t)}</span></div>' for i, (a, _, t) in enumerate(cs))
    js = "\n".join(f'    tl.fromTo("#ncap-{i}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.12, ease: "none" }}, {a:.2f});\n'
                   f'    tl.to("#ncap-{i}", {{ opacity: 0, duration: 0.12, ease: "none" }}, {max(a + 0.2, b - 0.12):.2f});'
                   for i, (a, b, _) in enumerate(cs))
    return f"""<template>
  <style>
    @font-face {{ font-family: "PretendardCap"; src: url("{FONT}") format("woff2"); font-weight: 600; }}
    #cap-root {{ position: absolute; inset: 0; pointer-events: none; }}
    #cap-band {{ position: absolute; left: 0; right: 0; bottom: 0; height: {band}px; background: #0b0b0f; }}
    .ncap {{ position: absolute; left: 0; right: 0; bottom: 0; height: {band}px; display: flex; align-items: center; justify-content: center; opacity: 0; }}
    .ncap span {{ max-width: {maxw}px;
      color: #ffffff; font-family: "PretendardCap", sans-serif; font-weight: 600; font-size: {size}px; line-height: 1.35;
      letter-spacing: -0.01em; text-align: center; word-break: keep-all; }}
  </style>
  <div id="root" data-composition-id="cap" data-width="{w}" data-height="{h}">
    <div id="cap-root" data-layout-ignore>
      <div id="cap-band"></div>
{divs}
    </div>
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{js}
    tl.set({{}}, {{}}, {total});
    window.__timelines["cap"] = tl;
  </script>
</template>
"""


LIFT_MARK = "<!-- captions: footer lift -->"


def lift_footers(out, on=False):
    """Remove the footer lift an earlier version injected into the scene compositions (the band replaces it)."""
    import glob
    for p in glob.glob(os.path.join(out, "compositions", "*.html")):
        s = open(p, encoding="utf-8").read()
        s2 = re.sub(re.escape(LIFT_MARK) + r"<style>[^<]*</style>", "", s)
        if s2 != s:
            open(p, "w", encoding="utf-8").write(s2)


def shift_scenes(html, band, w, h):
    """Move every scene host up by `band` px (or scale it from the top centre for templates with a top masthead);
    band 0 restores them. The transition and caption layers stay where they are."""
    def fix(m):
        tag, src = m.group(0), m.group(1)
        tag = re.sub(r' data-cap-shift="1" style="([^"]*?); transform: [^;"]*; transform-origin: [^;"]*"', r' style="\1"', tag)
        name = os.path.basename(src)
        if not band or name in ("tx.html", "captions.html"):
            return tag
        tf = (f"scale({(h - band) / h:.4f}); transform-origin: 50% 0" if name.startswith(SCALE_PREFIX)
              else f"translateY(-{band}px); transform-origin: 50% 0")
        return re.sub(r' style="([^"]*)"', lambda s: f' data-cap-shift="1" style="{s.group(1)}; transform: {tf}"', tag, count=1)
    return re.sub(r'<div id="[^"]+" data-composition-id="[^"]+" data-composition-src="(compositions/[^"]+)"[^>]*>', fix, html)


def mount(out, lines):
    """Write the captions layer and narration.srt for voiced lines [(start, dur, text)]; returns the cue count."""
    ip = os.path.join(out, "index.html")
    html = open(ip, encoding="utf-8").read()
    html = re.sub(r'\n?      <div id="cap" data-composition-id="cap"[^>]*></div>', "", html)
    m = re.search(r'id="root" data-composition-id="main" data-start="0" data-duration="([\d.]+)" data-width="(\d+)" data-height="(\d+)"', html)
    if not m:
        raise RuntimeError("index.html: main composition not found")
    total, w, h = float(m.group(1)), int(m.group(2)), int(m.group(3))
    cs = cues(lines, 24 if h > w else 26)  # 9:16: up to two lines of about 12
    open(os.path.join(out, "narration.srt"), "w", encoding="utf-8").write(srt(cs))
    cap = os.path.join(out, "compositions", "captions.html")
    lift_footers(out, on=False)  # older builds lifted footers instead; clean that up
    html = shift_scenes(html, BAND["tall" if h > w else "wide"] if cs else 0, w, h)
    if not cs:
        if os.path.exists(cap):
            os.remove(cap)
        open(ip, "w", encoding="utf-8").write(html)
        return 0
    open(cap, "w", encoding="utf-8").write(composition(cs, w, h, total))
    host = (f'      <div id="cap" data-composition-id="cap" data-composition-src="compositions/captions.html" data-start="0" '
            f'data-duration="{total}" data-track-index="4" data-track-kind="graphics" data-width="{w}" data-height="{h}" style="z-index: 60"></div>\n')
    anchor = '      <audio id="bgm"' if '      <audio id="bgm"' in html else '      <audio id="nar-'
    if anchor in html:
        html = html.replace(anchor, host + anchor, 1)
    else:
        html, k = re.subn(r'(\n\s*</div>\s*\n\s*<script>)', lambda mm: "\n" + host.rstrip("\n") + mm.group(1), html, count=1)
        if not k:
            raise RuntimeError("index.html: no place to mount the captions")
    open(ip, "w", encoding="utf-8").write(html)
    try:  # the captions' characters and the caption font must survive the per-video font subset
        from fontsub import subset_project
        subset_project(out)
    except ImportError:
        pass
    return len(cs)


if __name__ == "__main__":
    for d in sys.argv[1:]:
        cs = read_srt(os.path.join(d, "narration.srt"))
        print(d, mount(d, [(a, b - a, t) for a, b, t in cs]), "cues")
