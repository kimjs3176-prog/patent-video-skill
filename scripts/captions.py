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
# 16:9: captions sit in the bottom band (y ≈ 1010–1064). Small footer lines that live there (sources, running heads,
# page marks) are lifted above it while captions are on; a scene whose own content fills that band gets its captions higher.
FOOT_LIFT = 58
FOOT_SEL = '.foot, .foot2, .ft, #h3-src, .cap[style*="top: 1004px"]'
RAISE = {"g1-open": 150}  # bottom px for scenes with a bottom bar of key figures


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
    return out


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


def composition(cs, w, h, total, scene_of=lambda t: None):
    vertical = h > w
    size, bottom, maxw = (46, 330, 900) if vertical else (36, 18, 1500)

    def pos(a):
        b = RAISE.get(scene_of(a)) if not vertical else None
        return f' style="bottom: {b}px"' if b else ""
    divs = "\n".join(f'      <div class="ncap" id="ncap-{i}"{pos(a)}><span>{E(t)}</span></div>' for i, (a, _, t) in enumerate(cs))
    js = "\n".join(f'    tl.fromTo("#ncap-{i}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.12, ease: "none" }}, {a:.2f});\n'
                   f'    tl.to("#ncap-{i}", {{ opacity: 0, duration: 0.12, ease: "none" }}, {max(a + 0.2, b - 0.12):.2f});'
                   for i, (a, b, _) in enumerate(cs))
    return f"""<template>
  <style>
    @font-face {{ font-family: "PretendardCap"; src: url("{FONT}") format("woff2"); font-weight: 600; }}
    #cap-root {{ position: absolute; inset: 0; pointer-events: none; }}
    .ncap {{ position: absolute; left: 0; right: 0; bottom: {bottom}px; display: flex; justify-content: center; opacity: 0; }}
    .ncap span {{ max-width: {maxw}px; padding: 8px 24px 10px; border-radius: 14px; background: rgba(8, 8, 12, 0.66);
      color: #ffffff; font-family: "PretendardCap", sans-serif; font-weight: 600; font-size: {size}px; line-height: 1.35;
      letter-spacing: -0.01em; text-align: center; word-break: keep-all; }}
  </style>
  <div id="root" data-composition-id="cap" data-width="{w}" data-height="{h}">
    <div id="cap-root" data-layout-ignore>
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


def lift_footers(out, on):
    """Add (or remove) the footer lift in every scene composition."""
    import glob
    css = f"{LIFT_MARK}<style>{FOOT_SEL} {{ translate: 0 -{FOOT_LIFT}px; }}</style>"
    for p in glob.glob(os.path.join(out, "compositions", "*.html")):
        if p.endswith(("tx.html", "captions.html")):
            continue
        s = open(p, encoding="utf-8").read()
        s2 = re.sub(re.escape(LIFT_MARK) + r"<style>[^<]*</style>", "", s)
        if on:
            s2 = s2.replace("<template>", "<template>" + css, 1)
        if s2 != s:
            open(p, "w", encoding="utf-8").write(s2)


def mount(out, lines):
    """Write the captions layer and narration.srt for voiced lines [(start, dur, text)]; returns the cue count."""
    ip = os.path.join(out, "index.html")
    html = open(ip, encoding="utf-8").read()
    html = re.sub(r'\n?      <div id="cap" data-composition-id="cap"[^>]*></div>', "", html)
    m = re.search(r'id="root" data-composition-id="main" data-start="0" data-duration="([\d.]+)" data-width="(\d+)" data-height="(\d+)"', html)
    if not m:
        raise RuntimeError("index.html: main composition not found")
    total, w, h = float(m.group(1)), int(m.group(2)), int(m.group(3))
    cs = cues(lines, 15 if h > w else 26)
    open(os.path.join(out, "narration.srt"), "w", encoding="utf-8").write(srt(cs))
    cap = os.path.join(out, "compositions", "captions.html")
    lift_footers(out, on=bool(cs) and w > h)
    if not cs:
        if os.path.exists(cap):
            os.remove(cap)
        open(ip, "w", encoding="utf-8").write(html)
        return 0
    scenes = [(float(a), float(a) + float(d), os.path.basename(f)[:-5]) for f, a, d in re.findall(
        r'data-composition-src="(compositions/[^"]+)" data-start="([\d.]+)" data-duration="([\d.]+)"', html) if not f.endswith(("tx.html", "captions.html"))]

    def scene_of(t):  # the scene on top at time t (later scenes overlap earlier ones in the cross-fade)
        hit = [n for a, b, n in scenes if a <= t < b]
        return hit[-1] if hit else None
    open(cap, "w", encoding="utf-8").write(composition(cs, w, h, total, scene_of))
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
