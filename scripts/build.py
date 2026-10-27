"""Build one Unpacked-style HyperFrames project per patent from data/content/<order>-<appno>.json.

Usage: python -I tools/build.py data/content/001-1020190145266.json [...]
Output: videos/<order>-<appno>/ (index.html, compositions/, assets -> shared fonts, sfx, music)
"""
import html
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from icons import icon  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# background music: whatever mp3s sit in assets/music, assigned in production order (1→2→3→4→1…)
_MD = os.path.join(ROOT, "assets", "music")
MUSIC = sorted(f for f in os.listdir(_MD) if f.lower().endswith(".mp3")) if os.path.isdir(_MD) else []
MUSIC = MUSIC or ["m1-untitled.mp3"]  # placeholder name; postprocess drops the tag when the file is absent
PALETTES = {
    "amber": ("#ffd36e", "#ff9f43", "#ff6b6b"),
    "violet": ("#c77dff", "#8e6bff", "#5b8cff"),
    "aqua": ("#5ee7ff", "#4f9bff", "#7b7cff"),
    "green": ("#9bf26b", "#34e0a1", "#2fb8ff"),
    "rose": ("#ff9bc2", "#ff6b9a", "#b46bff"),
    "blue": ("#34e0c8", "#5b8cff", "#9a6bff"),
}
CONTACT = "한국농업기술진흥원"
DISCLAIMER = "※ 본 영상은 특허 명세서를 기반으로 제작되었으며, 실제 연구 및 사업화 내용과는 상이할 수 있습니다."

# scene slots: id, file, start, duration
SLOTS = [("s1", "s1-teaser", 0.0, 6.0), ("s2", "s2-reveal", 5.5, 8.0), ("s3", "s3-process", 13.0, 10.5),
         ("s4", "s4-proof", 23.0, 12.0), ("sf", "sf-figures", 34.5, 7.0), ("s5", "s5-features", 41.0, 7.0),
         ("s6", "s6-apps", 47.5, 6.5), ("s7", "s7-outro", 53.5, 6.5)]
TOTAL = 60.0
DUR = {sid: du for sid, _, _, du in SLOTS}

E = html.escape


def rgba(hexc, a):
    h = hexc.lstrip("#")
    return f"rgba({int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)}, {a})"


def head(sid, pal):
    a, b, c = pal
    return f"""<template>
  <style>
    @font-face {{ font-family: "NotoKR"; src: url("assets/fonts/NotoSansKR-VF.ttf") format("truetype"); font-weight: 100 900; }}
    #root {{ position: absolute; inset: 0; overflow: hidden; font-family: "Outfit", "NotoKR", sans-serif; color: #fff; }}
    #{sid}-in {{ position: absolute; inset: 0; background: #000; }}
    .grad {{ background: linear-gradient(100deg, {a} 0%, {b} 50%, {c} 100%); -webkit-background-clip: text; background-clip: text; color: transparent; }}
    .glow {{ position: absolute; width: 1100px; height: 1100px; border-radius: 50%; }}
    .eyebrow {{ position: absolute; font-size: 28px; font-weight: 600; letter-spacing: 0.36em; color: #a8a8bc; }}
    .glass {{ background: rgba(255, 255, 255, 0.06); border: 1px solid rgba(255, 255, 255, 0.14); }}
"""


def grad_defs(gid, pal):
    a, b, c = pal
    return (f'<svg width="0" height="0" style="position: absolute" data-layout-ignore><defs><linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="{a}" /><stop offset="0.55" stop-color="{b}" /><stop offset="1" stop-color="{c}" /></linearGradient></defs></svg>')


def enter(sid):
    return (f'tl.fromTo("#{sid}-in", {{ opacity: 0, scale: 1.08, filter: "blur(30px)" }}, '
            f'{{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.7, ease: "expo.out" }}, 0);')


def em_width(text):
    """Approximate rendered width in em for Outfit/Noto KR bold."""
    w = 0.0
    for ch in text:
        o = ord(ch)
        if 0xAC00 <= o <= 0xD7A3 or 0x3130 <= o <= 0x318F or 0x4E00 <= o <= 0x9FFF:
            w += 0.98
        elif ch.isupper():
            w += 0.7
        elif ch.isdigit():
            w += 0.6
        elif ch in " ·.,:–-/":
            w += 0.32
        else:
            w += 0.56
    return max(w, 0.5)


def fit(text, max_px, width, k=None):
    return int(min(max_px, width / em_width(text)))


def gtext(s):
    """'plain|grad' -> html with the part after | in the gradient."""
    if "|" in s:
        p, g = s.split("|", 1)
        return f'{E(p)}<span class="grad">{E(g)}</span>'
    return E(s)


# ---------------------------------------------------------------- scenes
def s1(c, pal):
    a, b, cc = pal
    name = c["name"]
    na, nb = (name.split("|", 1) + [""])[:2] if "|" in name else (name, "")
    size = fit(na + nb, 230, 1600)
    chars = "".join(f'<span class="c">{E(ch) if ch != " " else "&nbsp;"}</span>' for ch in na)
    chars += "".join(f'<span class="c grad">{E(ch) if ch != " " else "&nbsp;"}</span>' for ch in nb)
    return head("s1", pal) + f"""
    #s1-in {{ background: #000; }}
    #s1-g1 {{ left: 80px; top: -120px; background: radial-gradient(circle, {rgba(b, 0.45)} 0%, {rgba(b, 0)} 65%); }}
    #s1-g2 {{ left: 820px; top: 120px; background: radial-gradient(circle, {rgba(cc, 0.36)} 0%, {rgba(cc, 0)} 65%); }}
    #s1-ribbon {{ position: absolute; left: -300px; top: 520px; width: 2600px; height: 10px; border-radius: 10px;
      background: linear-gradient(90deg, rgba(255,255,255,0) 0%, {a} 35%, #ffffff 50%, {cc} 65%, rgba(255,255,255,0) 100%); }}
    #s1-eyebrow {{ left: 0; right: 0; top: 330px; text-align: center; letter-spacing: 0.42em; font-size: 30px; color: #b4b4c8; }}
    #s1-name {{ position: absolute; left: 0; right: 0; top: {470 - size * 0.55:.0f}px; text-align: center; font-size: {size}px; font-weight: 800; letter-spacing: -0.02em; line-height: 1.1; white-space: nowrap; }}
    #s1-name .c {{ display: inline-block; }}
    #s1-sub {{ position: absolute; left: 0; right: 0; top: 660px; text-align: center; font-size: 46px; font-weight: 700; letter-spacing: -0.02em; color: #e6e6f0; }}
    #s1-meta {{ position: absolute; left: 0; right: 0; top: 740px; text-align: center; font-size: 28px; font-weight: 500; color: #8e8ea3; }}
  </style>
  <div id="root" data-composition-id="s1" data-width="1920" data-height="1080">
    <div id="s1-in">
      <div class="glow" id="s1-g1" data-layout-ignore></div>
      <div class="glow" id="s1-g2" data-layout-ignore></div>
      <div id="s1-ribbon" data-layout-ignore></div>
      <div id="s1-eyebrow" class="eyebrow">2026 TECH REVEAL</div>
      <div id="s1-name" aria-label="{E(na + nb)}">{chars}</div>
      <div id="s1-sub">{E(c["sub"])}</div>
      <div id="s1-meta">{E(c["institute"])} · {E(c.get("patlabel", "등록특허"))} 제{E(c["regno"])}호</div>
    </div>
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    tl.fromTo("#s1-g1", {{ x: -60, opacity: 0.6 }}, {{ x: 140, opacity: 1, duration: 6, ease: "none" }}, 0);
    tl.fromTo("#s1-g2", {{ x: 80, opacity: 0.5 }}, {{ x: -120, opacity: 1, duration: 6, ease: "none" }}, 0);
    tl.fromTo("#s1-ribbon", {{ xPercent: -95, rotation: -9 }}, {{ xPercent: 95, rotation: -9, duration: 1.3, ease: "power3.inOut" }}, 0.15);
    tl.fromTo("#s1-eyebrow", {{ opacity: 0.25, filter: "blur(10px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.7, ease: "expo.out" }}, 0);
    tl.fromTo("#s1-name .c", {{ opacity: 0, filter: "blur(24px)", scale: 1.25 }}, {{ opacity: 1, filter: "blur(0px)", scale: 1, duration: 0.7, ease: "expo.out", stagger: 0.05 }}, 1.1);
    tl.fromTo("#s1-sub", {{ opacity: 0, filter: "blur(12px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.7, ease: "expo.out" }}, 2.5);
    tl.fromTo("#s1-meta", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.7, ease: "expo.out" }}, 3.2);
    window.__timelines["s1"] = tl;
  </script>
</template>
"""


def s2(c, pal):
    a, b, cc = pal
    chips = c["chips"][:4]
    pos = [(110, 200, "L"), (1430, 200, "R"), (110, 600, "L"), (1430, 600, "R")]
    lines, chip_html = [], []
    for i, ch in enumerate(chips):
        x, y, side = pos[i]
        if side == "L":
            d = f"M490,{y + 66} L600,{y + 66} L{700},{430 if y < 400 else 600}"
        else:
            d = f"M1430,{y + 66} L1320,{y + 66} L{1220},{430 if y < 400 else 600}"
        lines.append(f'<path class="s2-line" id="s2-l{i}" pathLength="1" d="{d}" />')
        vs = fit(ch["v"] + ch.get("u", ""), 50, 320)
        chip_html.append(
            f'<div class="s2-chip glass" id="s2-c{i}" style="left: {x}px; top: {y}px"><div class="k">{E(ch["k"])}</div>'
            f'<div class="v{" grad" if i % 2 == 1 else ""}" style="font-size: {vs}px">{E(ch["v"])}<small>{E(ch.get("u", ""))}</small></div></div>')
    return head("s2", pal) + f"""
    #s2-glow {{ left: 410px; top: -70px; background: radial-gradient(circle, {rgba(b, 0.42)} 0%, {rgba(cc, 0.16)} 42%, rgba(0,0,0,0) 66%); }}
    #s2-ring {{ position: absolute; left: 640px; top: 190px; width: 640px; height: 640px; border-radius: 50%;
      background: conic-gradient(from 0deg, {rgba(a, 0)}, {a}, {b}, {cc}, {rgba(cc, 0)});
      -webkit-mask: radial-gradient(circle, transparent 312px, #000 314px, #000 319px, transparent 321px);
      mask: radial-gradient(circle, transparent 312px, #000 314px, #000 319px, transparent 321px); }}
    #s2-hero {{ position: absolute; left: 750px; top: 300px; }}
    #s2-lines {{ position: absolute; left: 0; top: 0; }}
    .s2-line {{ fill: none; stroke: url(#s2-lg); stroke-width: 2.5; }}
    .s2-chip {{ position: absolute; width: 380px; padding: 24px 30px 26px; border-radius: 28px; }}
    .s2-chip .k {{ font-size: 28px; font-weight: 600; color: #a8a8bc; white-space: nowrap; }}
    .s2-chip .v {{ margin-top: 4px; font-weight: 700; letter-spacing: -0.02em; white-space: nowrap; }}
    .s2-chip .v small {{ font-size: 28px; font-weight: 600; margin-left: 4px; }}
    #s2-title {{ position: absolute; left: 0; right: 0; top: 880px; text-align: center; font-size: 60px; font-weight: 700; letter-spacing: -0.03em; }}
  </style>
  <div id="root" data-composition-id="s2" data-width="1920" data-height="1080">
    <div id="s2-in">
      {grad_defs("s2-lg", pal)}
      <div class="glow" id="s2-glow" data-layout-ignore></div>
      <div id="s2-ring" data-layout-ignore></div>
      <div id="s2-hero" data-layout-ignore>{icon(c["hero"], 420, "url(#s2-lg)", 3)}</div>
      <svg id="s2-lines" width="1920" height="1080" viewBox="0 0 1920 1080" data-layout-ignore>{"".join(lines)}</svg>
      {"".join(chip_html)}
      <div id="s2-title">{gtext(c["headline"])}</div>
    </div>
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    {enter("s2")}
    tl.fromTo("#s2-glow", {{ scale: 0.85, opacity: 0.5 }}, {{ scale: 1.05, opacity: 1, duration: 8, ease: "none" }}, 0);
    tl.fromTo("#s2-ring", {{ rotation: 0, scale: 0.8, opacity: 0 }}, {{ rotation: 120, scale: 1, opacity: 1, duration: 8, ease: "none" }}, 0.2);
    tl.fromTo("#s2-hero .ic", {{ strokeDasharray: 1, strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: 1.4, ease: "power2.inOut", stagger: 0.12 }}, 0.3);
    tl.fromTo("#s2-hero", {{ scale: 0.92 }}, {{ scale: 1.04, duration: 7.5, ease: "none" }}, 0.3);
    const ORDER = [0, 1, 2, 3];
    ORDER.forEach((n, i) => {{
      const t = 1.7 + i * 0.4;
      tl.fromTo("#s2-l" + n, {{ strokeDasharray: 1, strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: 0.5, ease: "power2.out" }}, t);
      tl.fromTo("#s2-c" + n, {{ opacity: 0, scale: 0.9, filter: "blur(10px)" }}, {{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.6, ease: "back.out(1.4)" }}, t + 0.1);
    }});
    tl.fromTo("#s2-title", {{ opacity: 0, filter: "blur(14px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.7, ease: "expo.out" }}, 3.6);
    window.__timelines["s2"] = tl;
  </script>
</template>
"""


def s3(c, pal):
    a, b, cc = pal
    p = c["process"]
    steps = p["steps"][:6]
    n = len(steps)
    row_h = 84
    top = 560 - (n * row_h) // 2 + 40
    rows = []
    from visuals import step_icon
    for i, st in enumerate(steps):
        rows.append(f'<div class="s3-row" id="s3-r{i}" style="top: {i * row_h}px"><span class="n">{icon(step_icon(st["n"], c["hero"]), 44, "url(#s3-lg)", 6)}{E(st["n"])}</span>'
                    f'<span class="d">{E(st["d"])}</span></div>')
    bigs = []
    for i, st in enumerate(steps):
        txt = st["big"] + st.get("u", "")
        size = fit(txt, 170, 400)
        bigs.append(f'<div class="s3-big" id="s3-b{i}"><div class="v grad" style="font-size: {size}px">{E(st["big"])}<small style="font-size: {max(40, size // 2)}px">{E(st.get("u", ""))}</small></div>'
                    f'<div class="k">STEP {i + 1:02d}</div></div>')
    r = 230
    circ = 2 * 3.14159 * r
    T = [0.9 + i * ((DUR["s3"] - 2.8) / n) for i in range(n)]
    return head("s3", pal) + f"""
    #s3-glow {{ left: -50px; top: 40px; background: radial-gradient(circle, {rgba(b, 0.34)} 0%, {rgba(cc, 0.12)} 42%, rgba(0,0,0,0) 66%); }}
    #s3-eyebrow {{ left: 140px; top: 96px; }}
    #s3-title {{ position: absolute; left: 136px; top: 136px; font-size: 66px; font-weight: 700; letter-spacing: -0.03em; white-space: nowrap; }}
    #s3-dial {{ position: absolute; left: 260px; top: 330px; }}
    .s3-big {{ position: absolute; left: 260px; top: 330px; width: 520px; height: 520px; text-align: center; }}
    .s3-big .v {{ position: absolute; left: 0; right: 0; top: 190px; font-weight: 700; line-height: 1; letter-spacing: -0.03em; white-space: nowrap; }}
    .s3-big .v small {{ margin-left: 6px; letter-spacing: -0.01em; }}
    .s3-big .k {{ position: absolute; left: 0; right: 0; top: 140px; font-size: 28px; font-weight: 600; letter-spacing: 0.3em; color: #a8a8bc; }}
    #s3-list {{ position: absolute; left: 960px; top: {top}px; width: 840px; height: {n * row_h}px; }}
    #s3-sel {{ position: absolute; left: 0; top: 0; width: 840px; height: 76px; border-radius: 20px;
      background: linear-gradient(100deg, {rgba(a, 0.26)}, {rgba(b, 0.22)}, {rgba(cc, 0.2)}); border: 1px solid {rgba(b, 0.6)}; }}
    .s3-row {{ position: absolute; left: 0; width: 840px; height: 76px; display: flex; align-items: center; justify-content: space-between; padding: 0 28px; gap: 20px; color: #5e5e72; }}
    .s3-row .n {{ font-size: 34px; font-weight: 700; white-space: nowrap; display: flex; align-items: center; gap: 18px; }}
    .s3-row .d {{ font-size: 28px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    #s3-note {{ position: absolute; left: 140px; top: 930px; font-size: 28px; font-weight: 500; color: #9a9aae; }}
  </style>
  <div id="root" data-composition-id="s3" data-width="1920" data-height="1080">
    <div id="s3-in">
      {grad_defs("s3-lg", pal)}
      <div class="glow" id="s3-glow" data-layout-ignore></div>
      <div id="s3-eyebrow" class="eyebrow">HOW IT WORKS</div>
      <div id="s3-title">{gtext(p["title"])}</div>
      <svg id="s3-dial" width="520" height="520" viewBox="0 0 520 520" data-layout-ignore>
        <circle cx="260" cy="260" r="{r}" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="14" />
        <circle id="s3-arc" cx="260" cy="260" r="{r}" fill="none" stroke="url(#s3-lg)" stroke-width="14" stroke-linecap="round"
          stroke-dasharray="{circ:.1f}" stroke-dashoffset="{circ:.1f}" transform="rotate(-90 260 260)" />
      </svg>
      {"".join(bigs)}
      <div id="s3-list"><div id="s3-sel"></div>{"".join(rows)}</div>
      <div id="s3-note">{E(p.get("note", ""))}</div>
    </div>
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    {enter("s3")}
    const T = {json.dumps([round(t, 2) for t in T])};
    const CIRC = {circ:.1f};
    tl.fromTo("#s3-glow", {{ x: -40 }}, {{ x: 120, duration: {DUR["s3"]}, ease: "none" }}, 0);
    tl.fromTo(".s3-row .ic", {{ strokeDasharray: 1, strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: 0.8, ease: "power2.out", stagger: 0.05 }}, 0.6);
    tl.fromTo(["#s3-eyebrow", "#s3-title"], {{ opacity: 0, filter: "blur(12px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.7, ease: "expo.out", stagger: 0.1 }}, 0.2);
    tl.fromTo(".s3-row", {{ opacity: 0, x: 30 }}, {{ opacity: 1, x: 0, duration: 0.6, ease: "expo.out", stagger: 0.06 }}, 0.4);
    tl.fromTo("#s3-sel", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.5, ease: "expo.out" }}, T[0]);
    tl.fromTo("#s3-dial", {{ opacity: 0, scale: 0.9 }}, {{ opacity: 1, scale: 1, duration: 0.8, ease: "expo.out" }}, 0.4);
    gsap.set(".s3-big", {{ opacity: 0 }});
    T.forEach((t, i) => {{
      if (i > 0) {{
        tl.to("#s3-sel", {{ y: i * {row_h}, duration: 0.6, ease: "expo.inOut" }}, t - 0.1);
        tl.to("#s3-r" + (i - 1), {{ color: "#9a9aae", duration: 0.4 }}, t);
        tl.to("#s3-b" + (i - 1), {{ opacity: 0, filter: "blur(12px)", duration: 0.3, ease: "power3.in" }}, t - 0.3);
      }}
      tl.to("#s3-r" + i, {{ color: "#ffffff", duration: 0.4 }}, t + 0.1);
      tl.fromTo("#s3-b" + i, {{ opacity: 0, filter: "blur(16px)", scale: 0.94 }}, {{ opacity: 1, filter: "blur(0px)", scale: 1, duration: 0.7, ease: "expo.out" }}, t);
      tl.to("#s3-arc", {{ strokeDashoffset: CIRC * (1 - (i + 1) / T.length), duration: 0.8, ease: "expo.inOut" }}, t);
    }});
    tl.fromTo("#s3-note", {{ opacity: 0, filter: "blur(8px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.7, ease: "expo.out" }}, T[T.length - 1] + 0.4);
    window.__timelines["s3"] = tl;
  </script>
</template>
"""


def s4_stats(c, pal):
    a, b, cc = pal
    pr = c["proof"]
    items = pr["items"][:3]
    k = len(items)
    span = (DUR["s4"] - 0.9) / k
    T = [round(0.7 + i * span, 2) for i in range(k)]
    stats, groups, bar_js = [], [], []
    for i, it in enumerate(items):
        big = it["big"]
        size = fit(big + it.get("u", ""), 200, 720)
        stats.append(f'<div class="s4-stat" id="s4-a{i}"><div class="big grad" style="font-size: {size}px">{E(big)}<small>{E(it.get("u", ""))}</small></div>'
                     f'<div class="l">{E(it["l"])}</div><div class="s">{it.get("s", "")}</div></div>')
        bars = it.get("bars") or []
        if bars:
            mx = it.get("max") or max(x["v"] for x in bars) * 1.15
            n = len(bars)
            rh = 104 if n <= 3 else 86
            top = 560 - (n * rh) // 2
            rows = []
            for j, br in enumerate(bars):
                cls = "s4-row hi" if br.get("hi") else "s4-row"
                rows.append(f'<div class="{cls}" style="height: {rh}px"><div class="lab">{E(br["l"])}</div><div class="val">{E(br.get("t", ""))}</div>'
                            f'<div class="trk"><div class="bar" id="s4-b{i}-{j}"></div></div></div>')
                bar_js.append(f'tl.to("#s4-b{i}-{j}", {{ scaleX: {max(0.004, min(1, br["v"] / mx)):.4f}, duration: 1.1, ease: "expo.out" }}, {T[i] + 0.3 + j * 0.15:.2f});')
            groups.append(f'<div class="s4-bars" id="s4-g{i}" style="top: {top}px">{"".join(rows)}</div>')
        else:
            groups.append(f'<div class="s4-bars" id="s4-g{i}" style="top: 440px">{icon(it.get("icon", c["hero"]), 260, "url(#s4-lg)", 3, f"class=s4-icon id=s4-ic{i}")}</div>')
    swap = []
    for i in range(k):
        if i > 0:
            swap.append(f'tl.to(["#s4-a{i - 1}", "#s4-g{i - 1}"], {{ opacity: 0, filter: "blur(12px)", duration: 0.35, ease: "power3.in" }}, {T[i] - 0.35:.2f});')
        swap.append(f'tl.fromTo(["#s4-a{i}", "#s4-g{i}"], {{ opacity: 0, filter: "blur(14px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.7, ease: "expo.out" }}, {T[i]:.2f});')
        if not items[i].get("bars"):
            swap.append(f'tl.fromTo("#s4-g{i} .ic", {{ strokeDasharray: 1, strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: 1.2, ease: "power2.inOut", stagger: 0.1 }}, {T[i] + 0.2:.2f});')
    return head("s4", pal) + f"""
    #s4-glow {{ left: -200px; top: 100px; background: radial-gradient(circle, {rgba(b, 0.3)} 0%, {rgba(cc, 0.12)} 42%, rgba(0,0,0,0) 66%); }}
    #s4-eyebrow {{ left: 140px; top: 150px; }}
    .s4-stat {{ position: absolute; left: 140px; top: 250px; width: 740px; }}
    .s4-stat .big {{ font-weight: 700; line-height: 1.05; letter-spacing: -0.04em; white-space: nowrap; }}
    .s4-stat .big small {{ font-size: 60px; letter-spacing: -0.01em; margin-left: 6px; }}
    .s4-stat .l {{ margin-top: 26px; font-size: 50px; font-weight: 700; letter-spacing: -0.03em; }}
    .s4-stat .s {{ margin-top: 12px; font-size: 30px; line-height: 1.5; font-weight: 500; color: #9a9aae; }}
    .s4-bars {{ position: absolute; left: 960px; width: 840px; }}
    .s4-icon {{ position: absolute; left: 290px; top: 0; }}
    .s4-row {{ position: relative; }}
    .s4-row .lab {{ position: absolute; left: 0; top: 0; font-size: 30px; font-weight: 600; color: #b4b4c8; white-space: nowrap; }}
    .s4-row .val {{ position: absolute; right: 0; top: 0; font-size: 30px; font-weight: 700; color: #b4b4c8; }}
    .s4-row .trk {{ position: absolute; left: 0; top: 46px; width: 840px; height: 28px; border-radius: 14px; background: rgba(255,255,255,0.07); }}
    .s4-row .bar {{ position: absolute; left: 0; top: 0; width: 840px; height: 28px; border-radius: 14px; background: #4a4a5c; transform-origin: 0% 50%; transform: scaleX(0); }}
    .s4-row.hi .bar {{ background: linear-gradient(90deg, {a}, {b} 55%, {cc}); }}
    .s4-row.hi .lab, .s4-row.hi .val {{ color: #fff; }}
    #s4-src {{ position: absolute; left: 140px; top: 952px; font-size: 28px; font-weight: 500; color: #6e6e82; }}
  </style>
  <div id="root" data-composition-id="s4" data-width="1920" data-height="1080">
    <div id="s4-in" data-hold>
      {grad_defs("s4-lg", pal)}
      <div class="glow" id="s4-glow" data-layout-ignore></div>
      <div id="s4-eyebrow" class="eyebrow">{E(pr.get("eyebrow", "PERFORMANCE"))}</div>
      {"".join(stats)}
      {"".join(groups)}
      <div id="s4-src">{E(c.get("source", ""))}</div>
    </div>
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    {enter("s4")}
    tl.fromTo("#s4-glow", {{ x: -40 }}, {{ x: 160, duration: {DUR["s4"]}, ease: "none" }}, 0);
    tl.fromTo(["#s4-eyebrow", "#s4-src"], {{ opacity: 0 }}, {{ opacity: 1, duration: 0.6, ease: "expo.out" }}, 0.3);
    gsap.set([".s4-stat", ".s4-bars"], {{ opacity: 0 }});
    tl.fromTo([".s4-stat", ".s4-bars"], {{ scale: 1 }}, {{ scale: 1.03, duration: {DUR["s4"]}, ease: "none" }}, 0);
    {chr(10).join("    " + s for s in swap)}
    {chr(10).join("    " + s for s in bar_js)}
    window.__timelines["s4"] = tl;
  </script>
</template>
"""


def s4_anatomy(c, pal):
    a, b, cc = pal
    pr = c["proof"]
    parts = pr["parts"][:6]
    n = len(parts)
    rh = 112
    top = 560 - (n * rh) // 2 + 20
    # show the drawing's own reference number when known, otherwise a neutral dot (never an invented 1..N)
    rows = "".join(f'<div class="s4-part" id="s4-p{i}" style="top: {i * rh}px">'
                   + (f'<b>{E(str(p["ref"]))}</b>' if p.get("ref") else '<b class="dot"></b>')
                   + f'<div><div class="n">{E(p["n"])}</div><div class="d">{E(p["d"])}</div></div></div>'
                   for i, p in enumerate(parts))
    return head("s4", pal) + f"""
    #s4-glow {{ left: -100px; top: 60px; background: radial-gradient(circle, {rgba(b, 0.3)} 0%, {rgba(cc, 0.12)} 42%, rgba(0,0,0,0) 66%); }}
    #s4-eyebrow {{ left: 140px; top: 110px; }}
    #s4-title {{ position: absolute; left: 136px; top: 150px; font-size: 62px; font-weight: 700; letter-spacing: -0.03em; white-space: nowrap; }}
    #s4-card {{ position: absolute; left: 140px; top: 270px; width: 700px; height: 660px; border-radius: 32px; background: #f4f4f7; overflow: hidden; }}
    #s4-card img {{ position: absolute; left: 30px; top: 30px; width: 640px; height: 600px; object-fit: contain; }}
    #s4-list {{ position: absolute; left: 940px; top: {top}px; width: 860px; height: {n * rh}px; }}
    .s4-part {{ position: absolute; left: 0; width: 860px; height: 100px; display: flex; align-items: center; gap: 26px; }}
    .s4-part b {{ min-width: 56px; height: 56px; padding: 0 10px; flex: none; border-radius: 28px; border: 2px solid {b}; color: #fff; text-align: center; line-height: 52px; font-size: 28px; }}
    .s4-part b.dot {{ min-width: 18px; width: 18px; height: 18px; padding: 0; margin: 0 19px; border: none; background: linear-gradient(135deg, {a}, {cc}); }}
    .s4-part .n {{ font-size: 36px; font-weight: 700; letter-spacing: -0.02em; white-space: nowrap; }}
    .s4-part .d {{ margin-top: 4px; font-size: 28px; font-weight: 500; color: #9a9aae; white-space: nowrap; }}
    #s4-src {{ position: absolute; left: 140px; top: 952px; font-size: 28px; font-weight: 500; color: #6e6e82; }}
  </style>
  <div id="root" data-composition-id="s4" data-width="1920" data-height="1080">
    <div id="s4-in" data-hold>
      <div class="glow" id="s4-glow" data-layout-ignore></div>
      <div id="s4-eyebrow" class="eyebrow">{E(pr.get("eyebrow", "ANATOMY"))}</div>
      <div id="s4-title">{gtext(pr.get("title", "핵심 |구성"))}</div>
      <div id="s4-card" data-layout-allow-overflow><img id="s4-img" src="assets/fig/{E(pr["figure"])}" alt="{E(pr.get("figcap", "대표 도면"))}" /></div>
      <div id="s4-list">{rows}</div>
      <div id="s4-src">{E(c.get("source", ""))}</div>
    </div>
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    {enter("s4")}
    tl.fromTo("#s4-glow", {{ x: -40 }}, {{ x: 160, duration: {DUR["s4"]}, ease: "none" }}, 0);
    tl.fromTo(["#s4-eyebrow", "#s4-title", "#s4-src"], {{ opacity: 0, filter: "blur(12px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.7, ease: "expo.out", stagger: 0.1 }}, 0.2);
    tl.fromTo("#s4-card", {{ opacity: 0, scale: 0.94, filter: "blur(14px)" }}, {{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.9, ease: "expo.out" }}, 0.5);
    tl.fromTo("#s4-img", {{ scale: 1 }}, {{ scale: 1.08, duration: {DUR["s4"] - 1}, ease: "none" }}, 0.8);
    tl.fromTo(".s4-part", {{ opacity: 0, x: 40, filter: "blur(10px)" }}, {{ opacity: 1, x: 0, filter: "blur(0px)", duration: 0.7, ease: "expo.out", stagger: {min(1.6, 9.5 / max(1, n)):.2f} }}, 1.2);
    window.__timelines["s4"] = tl;
  </script>
</template>
"""


def s5(c, pal):
    a, b, cc = pal
    f = c["features"]
    tiles = f["tiles"][:6]
    xs = [600, 1006, 1412]
    th = []
    for i, t in enumerate(tiles):
        x = xs[i % 3]
        y = 236 if i < 3 else 598
        vs = fit(t["v"], 84, 320)
        th.append(f'<div class="s5-tile glass" id="s5-t{i + 1}" style="left: {x}px; top: {y}px"><div class="v grad" style="font-size: {vs}px">{E(t["v"])}</div>'
                  f'<div class="l">{E(t["l"])}</div><div class="s">{E(t["s"])}</div></div>')
    big = f["big"]
    return head("s5", pal) + f"""
    #s5-eyebrow {{ left: 122px; top: 92px; }}
    #s5-head {{ position: absolute; left: 120px; top: 134px; font-size: 66px; font-weight: 700; letter-spacing: -0.035em; white-space: nowrap; }}
    .s5-tile {{ position: absolute; width: 386px; height: 342px; border-radius: 28px; overflow: hidden; }}
    .s5-tile .v {{ position: absolute; left: 36px; top: 34px; line-height: 1.15; font-weight: 700; letter-spacing: -0.04em; white-space: nowrap; }}
    .s5-tile .l {{ position: absolute; left: 36px; bottom: 86px; font-size: 36px; font-weight: 700; letter-spacing: -0.025em; white-space: nowrap; }}
    .s5-tile .s {{ position: absolute; left: 36px; bottom: 40px; font-size: 28px; font-weight: 500; color: #8e8ea3; white-space: nowrap; }}
    #s5-big {{ left: 120px; top: 236px; width: 460px; height: 704px; background: radial-gradient(circle at 50% 35%, {rgba(b, 0.28)} 0%, rgba(255,255,255,0.05) 60%); }}
    #s5-big svg {{ position: absolute; left: 90px; top: 70px; }}
    #s5-big .l {{ bottom: 112px; font-size: 44px; white-space: normal; right: 30px; }}
    #s5-big .s {{ bottom: 50px; font-size: 30px; font-weight: 700; }}
  </style>
  <div id="root" data-composition-id="s5" data-width="1920" data-height="1080">
    <div id="s5-in">
      {grad_defs("s5-lg", pal)}
      <div id="s5-eyebrow" class="eyebrow">HIGHLIGHTS</div>
      <div id="s5-head">{gtext(f.get("title", "핵심 |특장점"))}</div>
      <div class="s5-tile glass" id="s5-big">{icon(c["hero"], 280, "url(#s5-lg)", 3)}<div class="l">{E(big["l"])}</div><div class="s grad">{E(big["s"])}</div></div>
      {"".join(th)}
    </div>
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    {enter("s5")}
    tl.fromTo(["#s5-eyebrow", "#s5-head"], {{ opacity: 0, filter: "blur(12px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.7, ease: "expo.out", stagger: 0.1 }}, 0.3);
    tl.fromTo(".s5-tile", {{ opacity: 0, scale: 0.94, filter: "blur(10px)" }}, {{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.8, ease: "power3.out", stagger: 0.14 }}, 0.9);
    tl.fromTo("#s5-big .ic", {{ strokeDasharray: 1, strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: 1.4, ease: "power2.inOut", stagger: 0.1 }}, 1.1);
    tl.to("#s5-in", {{ scale: 1.025, duration: {DUR["s5"] - 0.8}, ease: "none" }}, 0.8);
    window.__timelines["s5"] = tl;
  </script>
</template>
"""


def sf(c, pal):
    """Spec figures on the black stage: white plates like lit product screens, a gradient frame spotlights each in turn."""
    from visuals import fig_boxes, pick_figures, step_icon
    a, b, cc = pal
    d = DUR["sf"]
    figs = pick_figures(c, 4)
    if figs:
        boxes = fig_boxes(len(figs), 140, 300, 1640, 640, 28)
        cells = "".join(f'<div class="sf-c" id="sf-c{i}" style="left: {x:.0f}px; top: {y:.0f}px; width: {w:.0f}px; height: {h:.0f}px">'
                        f'<div class="pl"><img src="assets/fig/{E(f["file"])}" alt="명세서 도면 {i + 1}" /></div>'
                        f'<div class="cp"><b class="grad">FIG {i + 1:02d}</b> 명세서 도면 · {f["page"]}쪽</div></div>'
                        for i, (f, (x, y, w, h)) in enumerate(zip(figs, boxes)))
    else:  # no usable figure: the process steps as pictogram plates
        steps = c["process"]["steps"][:5]
        boxes = fig_boxes(len(steps), 140, 300, 1640, 640, 28)
        cells = "".join(f'<div class="sf-c" id="sf-c{i}" style="left: {x:.0f}px; top: {y:.0f}px; width: {w:.0f}px; height: {h:.0f}px">'
                        f'<div class="pl dark">{icon(step_icon(st["n"], c["hero"]), min(220, w * 0.55), "url(#sf-lg)", 3)}</div>'
                        f'<div class="cp"><b class="grad">0{i + 1}</b> {E(st["n"])}</div></div>'
                        for i, (st, (x, y, w, h)) in enumerate(zip(steps, boxes)))
    k = len(boxes)
    step = (d - 2.6) / k
    spots = "\n".join(f'    tl.to("#sf-c{i}", {{ scale: 1.03, duration: 0.5, ease: "expo.out" }}, {1.8 + i * step:.2f});\n'
                      f'    tl.to("#sf-c{i} .ring", {{ opacity: 1, duration: 0.4 }}, {1.8 + i * step:.2f});\n'
                      + (f'    tl.to("#sf-c{i}", {{ scale: 1, duration: 0.5, ease: "expo.inOut" }}, {1.8 + (i + 1) * step - 0.1:.2f});\n'
                         f'    tl.to("#sf-c{i} .ring", {{ opacity: 0, duration: 0.4 }}, {1.8 + (i + 1) * step - 0.1:.2f});' if i < k - 1 else "")
                      for i in range(k))
    cells = cells.replace('<div class="pl', '<div class="ring" data-layout-ignore></div><div class="pl')
    return head("sf", pal) + f"""
    #sf-glow {{ left: 400px; top: -300px; background: radial-gradient(circle, {rgba(b, 0.30)} 0%, {rgba(cc, 0.10)} 45%, rgba(0,0,0,0) 68%); }}
    #sf-eyebrow {{ left: 140px; top: 96px; }}
    #sf-title {{ position: absolute; left: 136px; top: 136px; font-size: 66px; font-weight: 700; letter-spacing: -0.03em; white-space: nowrap; }}
    .sf-c {{ position: absolute; }}
    .sf-c .ring {{ position: absolute; inset: -6px; bottom: 50px; border-radius: 30px; background: linear-gradient(120deg, {a}, {b}, {cc}); opacity: 0; }}
    .sf-c .pl {{ position: absolute; left: 0; right: 0; top: 0; bottom: 56px; border-radius: 24px; background: #fff; overflow: hidden; box-shadow: 0 30px 80px {rgba(b, 0.22)}; }}
    .sf-c .pl.dark {{ background: #111116; border: 1px solid rgba(255, 255, 255, 0.14); display: flex; align-items: center; justify-content: center; }}
    .sf-c img {{ position: absolute; inset: 16px; width: calc(100% - 32px); height: calc(100% - 32px); object-fit: contain; }}
    .sf-c .cp {{ position: absolute; left: 6px; bottom: 6px; font-size: 28px; font-weight: 600; color: #a8a8bc; white-space: nowrap; }}
    .sf-c .cp b {{ font-weight: 800; margin-right: 8px; }}
  </style>
  <div id="root" data-composition-id="sf" data-width="1920" data-height="1080">
    <div id="sf-in">
      {grad_defs("sf-lg", pal)}
      <div class="glow" id="sf-glow" data-layout-ignore></div>
      <div id="sf-eyebrow" class="eyebrow">{"FROM THE SPECIFICATION" if figs else "AT A GLANCE"}</div>
      <div id="sf-title">{'명세서 <span class="grad">도면</span>으로 보는 기술' if figs else '공정 <span class="grad">한눈에</span> 보기'}</div>
      {cells}
    </div>
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    {enter("sf")}
    tl.fromTo("#sf-glow", {{ x: -120 }}, {{ x: 120, duration: {d}, ease: "none" }}, 0);
    tl.fromTo(["#sf-eyebrow", "#sf-title"], {{ opacity: 0, filter: "blur(12px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.7, ease: "expo.out", stagger: 0.1 }}, 0.2);
    tl.fromTo(".sf-c", {{ opacity: 0, y: 60, rotationX: 18, transformPerspective: 1400 }}, {{ opacity: 1, y: 0, rotationX: 0, duration: 1.0, ease: "expo.out", stagger: 0.16 }}, 0.5);
    tl.fromTo(".sf-c img", {{ scale: 1.1 }}, {{ scale: 1, duration: {d - 0.6:.1f}, ease: "power1.out" }}, 0.5);
    tl.fromTo(".sf-c .ic", {{ strokeDasharray: 1, strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: 1.2, ease: "power2.inOut", stagger: 0.04 }}, 0.9);
{spots}
    window.__timelines["sf"] = tl;
  </script>
</template>
"""


def s6(c, pal):
    a, b, cc = pal
    apps = c["apps"][:5]
    n = len(apps)
    w, gap = 316, 25
    x0 = (1920 - (n * w + (n - 1) * gap)) // 2
    tiles = []
    for i, ap in enumerate(apps):
        tag = '<div class="tag grad">특허 청구항</div>' if ap.get("claim") else ""
        tiles.append(f'<div class="s6-tile glass" id="s6-t{i}" style="left: {x0 + i * (w + gap)}px">{icon(ap["icon"], 120, "url(#s6-lg)", 4)}'
                     f'<div class="n">{E(ap["n"])}</div><div class="s">{ap["s"]}</div>{tag}</div>')
    return head("s6", pal) + f"""
    #s6-glow {{ left: 410px; top: 300px; background: radial-gradient(circle, {rgba(b, 0.3)} 0%, {rgba(cc, 0.1)} 42%, rgba(0,0,0,0) 66%); }}
    #s6-eyebrow {{ left: 0; right: 0; top: 120px; text-align: center; }}
    #s6-title {{ position: absolute; left: 0; right: 0; top: 162px; text-align: center; font-size: 68px; font-weight: 700; letter-spacing: -0.03em; }}
    .s6-tile {{ position: absolute; top: 380px; width: {w}px; height: 440px; border-radius: 28px; }}
    .s6-tile svg {{ position: absolute; left: 98px; top: 50px; }}
    .s6-tile .n {{ position: absolute; left: 20px; right: 20px; top: 214px; text-align: center; font-size: 36px; font-weight: 700; letter-spacing: -0.025em; white-space: nowrap; }}
    .s6-tile .s {{ position: absolute; left: 20px; right: 20px; top: 274px; text-align: center; font-size: 28px; line-height: 1.5; font-weight: 500; color: #9a9aae; }}
    .s6-tile .tag {{ position: absolute; left: 0; right: 0; bottom: 30px; text-align: center; font-size: 28px; font-weight: 700; }}
  </style>
  <div id="root" data-composition-id="s6" data-width="1920" data-height="1080">
    <div id="s6-in">
      {grad_defs("s6-lg", pal)}
      <div class="glow" id="s6-glow" data-layout-ignore></div>
      <div id="s6-eyebrow" class="eyebrow">APPLICATIONS</div>
      <div id="s6-title">기술이전 시 <span class="grad">활용분야</span></div>
      {"".join(tiles)}
    </div>
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    {enter("s6")}
    tl.fromTo("#s6-glow", {{ x: -80 }}, {{ x: 80, duration: {DUR["s6"]}, ease: "none" }}, 0);
    tl.fromTo(["#s6-eyebrow", "#s6-title"], {{ opacity: 0, filter: "blur(12px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.7, ease: "expo.out", stagger: 0.1 }}, 0.2);
    tl.to("#s6-in", {{ scale: 1.03, duration: {DUR["s6"] - 0.7}, ease: "none" }}, 0.7);
    for (let i = 0; i < {n}; i++) {{
      const t = 0.8 + i * 0.45;
      tl.fromTo("#s6-t" + i, {{ opacity: 0, y: 40, scale: 0.94 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.6, ease: "back.out(1.4)" }}, t);
      tl.fromTo("#s6-t" + i + " .ic", {{ strokeDasharray: 1, strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: 0.8, ease: "power2.out", stagger: 0.08 }}, t + 0.25);
    }}
    window.__timelines["s6"] = tl;
  </script>
</template>
"""


def s7(c, pal):
    a, b, cc = pal
    name = c["name"]
    na, nb = (name.split("|", 1) + [""])[:2] if "|" in name else (name, "")
    size = fit(na + nb, 180, 1500)
    return head("s7", pal) + f"""
    #s7-g1 {{ left: 60px; top: -60px; background: radial-gradient(circle, {rgba(b, 0.42)} 0%, {rgba(b, 0)} 65%); }}
    #s7-g2 {{ left: 840px; top: 40px; background: radial-gradient(circle, {rgba(cc, 0.32)} 0%, {rgba(cc, 0)} 65%); }}
    #s7-ribbon {{ position: absolute; left: -300px; top: 440px; width: 2600px; height: 8px; border-radius: 8px;
      background: linear-gradient(90deg, rgba(255,255,255,0) 0%, {a} 35%, #ffffff 50%, {cc} 65%, rgba(255,255,255,0) 100%); }}
    #s7-name {{ position: absolute; left: 0; right: 0; top: {330 - size * 0.55:.0f}px; text-align: center; font-size: {size}px; font-weight: 800; letter-spacing: -0.02em; line-height: 1.1; white-space: nowrap; }}
    #s7-sub {{ position: absolute; left: 0; right: 0; top: 470px; text-align: center; font-size: 44px; font-weight: 700; letter-spacing: -0.02em; color: #e6e6f0; }}
    #s7-card {{ position: absolute; left: 460px; top: 600px; width: 1000px; height: 100px; border-radius: 32px; }}
    .s7-row {{ position: absolute; left: 60px; right: 60px; height: 100px; display: flex; align-items: center; justify-content: space-between; }}
    .s7-row .k {{ font-size: 32px; font-weight: 600; color: #a8a8bc; }}
    .s7-row .v {{ font-size: 44px; font-weight: 700; letter-spacing: -0.02em; }}
    #s7-meta {{ position: absolute; left: 0; right: 0; top: 830px; text-align: center; font-size: 28px; font-weight: 500; color: #8e8ea3; }}
    #s7-disc {{ position: absolute; left: 0; right: 0; top: 910px; text-align: center; font-size: 28px; font-weight: 500; color: #6e6e82; }}
  </style>
  <div id="root" data-composition-id="s7" data-width="1920" data-height="1080">
    <div id="s7-in">
      <div class="glow" id="s7-g1" data-layout-ignore></div>
      <div class="glow" id="s7-g2" data-layout-ignore></div>
      <div id="s7-ribbon" data-layout-ignore></div>
      <div id="s7-name">{E(na)}<span class="grad">{E(nb)}</span></div>
      <div id="s7-sub">{E(c["sub"])}</div>
      <div id="s7-card" class="glass">
        <div class="s7-row" style="top: 0"><span class="k">기술이전 문의</span><span class="v grad">{CONTACT}</span></div>
      </div>
      <div id="s7-meta">{E(c.get("patlabel", "등록특허"))} 제{E(c["regno"])}호 · 특허권자 대한민국 ({E(c["institute"])})</div>
      <div id="s7-disc">{DISCLAIMER}</div>
    </div>
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    {enter("s7")}
    tl.fromTo("#s7-g1", {{ x: -60 }}, {{ x: 120, duration: {DUR["s7"]}, ease: "none" }}, 0);
    tl.fromTo("#s7-g2", {{ x: 60 }}, {{ x: -120, duration: {DUR["s7"]}, ease: "none" }}, 0);
    tl.fromTo("#s7-ribbon", {{ xPercent: -95, rotation: 8 }}, {{ xPercent: 95, rotation: 8, duration: 1.2, ease: "power3.inOut" }}, 0.2);
    tl.fromTo("#s7-name", {{ opacity: 0, scale: 1.15, filter: "blur(24px)" }}, {{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.9, ease: "expo.out" }}, 0.7);
    tl.fromTo("#s7-sub", {{ opacity: 0, filter: "blur(12px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.7, ease: "expo.out" }}, 1.2);
    tl.fromTo("#s7-card", {{ opacity: 0, scale: 0.92 }}, {{ opacity: 1, scale: 1, duration: 0.7, ease: "back.out(1.4)" }}, 1.7);
    tl.fromTo(".s7-row", {{ opacity: 0, x: -20 }}, {{ opacity: 1, x: 0, duration: 0.6, ease: "expo.out", stagger: 0.2 }}, 2.0);
    tl.fromTo("#s7-meta", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.7, ease: "expo.out" }}, 2.6);
    tl.fromTo("#s7-disc", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.7, ease: "expo.out" }}, 2.9);
    window.__timelines["s7"] = tl;
  </script>
</template>
"""


def index(c):
    music = MUSIC[(int(c["order"]) - 1) % len(MUSIC)]
    hosts = "\n".join(
        f'      <div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{f}.html" data-start="{st}" data-duration="{du}" '
        f'data-track-index="{1 if i % 2 == 0 else 2}" data-track-kind="graphics" data-width="1920" data-height="1080" style="z-index: {i + 1}"></div>'
        for i, (sid, f, st, du) in enumerate(SLOTS))
    sfx = [(st, "whoosh-short.mp3" if i % 2 else "whoosh-cinematic.mp3", 0.55 if i % 2 else 5.52) for i, (_, _, st, _) in enumerate(SLOTS)]
    sfx_html = "\n".join(
        f'      <audio id="sfx-{i}" class="clip" src="assets/sfx/{f}" data-start="{st}" data-duration="{d}" data-track-index="{11 + i % 2}" data-volume="0.16"></audio>'
        for i, (st, f, d) in enumerate(sfx))
    return f"""<!doctype html>
<html lang="ko">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      @font-face {{ font-family: "NotoKR"; src: url("assets/fonts/NotoSansKR-VF.ttf") format("truetype"); font-weight: 100 900; }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: #000; }}
      #root {{ position: relative; width: 100%; height: 100%; font-family: "Outfit", "NotoKR", sans-serif; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1920" data-height="1080">
{hosts}

      <!-- Background music: one track per video, assigned in production order -->
      <audio id="bgm" class="clip" src="assets/music/{music}" data-start="0" data-duration="{TOTAL}" data-track-index="10" data-volume="0.6" data-fade-in="0.4" data-fade-out="2.5"></audio>
{sfx_html}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
"""


def build(path):
    c = json.load(open(path, encoding="utf-8"))
    pal = PALETTES.get(c.get("palette", "blue"), PALETTES["blue"])
    slug = f'{int(c["order"]):03d}-{c["appno"]}'
    out = os.path.join(ROOT, "videos", slug)
    os.makedirs(os.path.join(out, "compositions"), exist_ok=True)
    os.makedirs(os.path.join(out, "assets", "fig"), exist_ok=True)
    for sub in ("fonts", "sfx", "music"):
        dst = os.path.join(out, "assets", sub)
        if not os.path.exists(dst) and os.path.isdir(os.path.join(ROOT, "assets", sub)):
            shutil.copytree(os.path.join(ROOT, "assets", sub), dst)
    if c["proof"].get("kind") == "anatomy":
        src = os.path.join(ROOT, "data", "patents", c["appno"], c["proof"]["figure"])
        shutil.copy(src, os.path.join(out, "assets", "fig", c["proof"]["figure"]))
    for fn in ("package.json", "hyperframes.json"):
        s = open(os.path.join(ROOT, "template", fn), encoding="utf-8").read().replace("__SLUG__", slug)
        open(os.path.join(out, fn), "w", encoding="utf-8").write(s)
    scenes = {"s1-teaser": s1(c, pal), "s2-reveal": s2(c, pal), "s3-process": s3(c, pal),
              "s4-proof": s4_anatomy(c, pal) if c["proof"].get("kind") == "anatomy" else s4_stats(c, pal),
              "sf-figures": sf(c, pal), "s5-features": s5(c, pal), "s6-apps": s6(c, pal), "s7-outro": s7(c, pal)}
    for name, body in scenes.items():
        open(os.path.join(out, "compositions", name + ".html"), "w", encoding="utf-8").write(body)
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(index(c))
    from visuals import add_transitions, copy_figures
    copy_figures(c, out)
    add_transitions(out, "A", SLOTS, TOTAL, 1920, 1080)
    print(slug, "built", "music:", MUSIC[(int(c["order"]) - 1) % len(MUSIC)])
    return out


if __name__ == "__main__":
    for p in sys.argv[1:]:
        build(p)
