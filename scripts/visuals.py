"""Shared visual helpers: spec figures, step pictograms, ambient layers, scene-boundary transitions.

pick_figures(c, n)  -> up to n distinct, usable figures from data/patents/<appno>/ (page order, front-page drawing first)
step_icon(text, hero) -> line-icon name for a process step, by keyword
"""
import hashlib
import os
import re
import struct

from build import ROOT

STEP_ICONS = [
    (("동결", "냉동", "냉각", "저온", "식힘", "응결", "해동", "냉장"), "snow"),
    (("발효", "접종", "종균", "배양", "효모", "초산", "유산균", "젖산", "균주", "균사", "제국", "입국", "종초", "계대"), "cell"),
    (("추출", "여과", "농축", "분획", "흡착", "정제", "원심", "효소", "분해", "증폭", "검출", "분석", "검증", "평가"), "flask"),
    (("열풍", "송풍", "대류"), "fan"),
    (("건조", "증발", "탈수"), "sun"),
    (("가열", "볶", "로스팅", "증숙", "찌기", "증자", "취반", "조리", "살균", "승온", "호화", "팽화", "액화", "당화", "열처리", "취사"), "thermo"),
    (("혼합", "배합", "블렌딩", "반죽", "교반", "첨가", "조정", "가수"), "bowl"),
    (("분쇄", "분말", "파쇄", "도정", "압출", "성형", "사출", "제면", "압착", "절단", "코팅", "방사", "가공"), "gear"),
    (("수침", "침지", "세척", "수세", "급수", "관수", "착즙", "당침"), "water"),
    (("숙성", "저장", "보관", "포장", "적재", "완성", "제품화", "소재화", "마감"), "box"),
    (("측정", "센서", "감지", "모니터"), "sensor"),
    (("입력", "출력", "비교", "판정", "모드", "코드", "토픽", "데이터", "정보", "표시", "알람", "결정", "학습", "연동"), "chip"),
    (("재배", "발아", "파종", "육묘", "체세포", "교배", "생육", "잎", "채취"), "sprout"),
    (("투여", "섭취", "복용"), "capsule"),
    (("수확", "이송"), "tractor"),
]


def step_icon(text, hero="spark"):
    for keys, name in STEP_ICONS:
        if any(k in text for k in keys):
            return name
    return hero


def _dims(path):
    with open(path, "rb") as f:
        head = f.read(26)
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", head[16:24])
        if head[:2] != b"\xff\xd8":
            return None
        f.seek(2)
        while True:
            b = f.read(1)
            while b and b != b"\xff":
                b = f.read(1)
            while b == b"\xff":
                b = f.read(1)
            if not b:
                return None
            m = b[0]
            if m in (0xD8, 0x01) or 0xD0 <= m <= 0xD7:
                continue
            ln = struct.unpack(">H", f.read(2))[0]
            if m in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                h, w = struct.unpack(">xHH", f.read(5))
                return w, h
            f.seek(ln - 2, 1)


def _page(fn):
    m = re.match(r"fig-p(\d+)-", fn)
    return int(m.group(1)) if m else 999


def pick_figures(c, n=4):
    """Distinct figures worth showing, front-page drawing first, then spread evenly over the spec."""
    d = os.path.join(ROOT, "data", "patents", c["appno"])
    if not os.path.isdir(d):
        return []
    skip = c["proof"].get("figure") if c["proof"].get("kind") == "anatomy" else None
    seen, out = set(), []
    if skip and os.path.exists(os.path.join(d, skip)):
        seen.add(hashlib.md5(open(os.path.join(d, skip), "rb").read()).hexdigest())  # the anatomy scene already shows it
    for fn in sorted((f for f in os.listdir(d) if f.startswith("fig-")), key=lambda f: (_page(f), f)):
        p = os.path.join(d, fn)
        if os.path.getsize(p) < 6000:
            continue
        h = hashlib.md5(open(p, "rb").read()).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        if fn == skip:
            continue
        wh = _dims(p)
        if not wh or min(wh) < 220 or max(wh) / min(wh) > 3.6:
            continue
        out.append({"file": fn, "page": _page(fn), "w": wh[0], "h": wh[1]})
    if len(out) <= n:
        return out
    idx = sorted({round(i * (len(out) - 1) / (n - 1)) for i in range(n)}) if n > 1 else [0]
    return [out[i] for i in idx]


def copy_figures(c, out, n=4):
    """Copy the figures pick_figures() chooses into <out>/assets/fig and return them."""
    import shutil
    figs = pick_figures(c, n)
    os.makedirs(os.path.join(out, "assets", "fig"), exist_ok=True)
    for f in figs:
        shutil.copy(os.path.join(ROOT, "data", "patents", c["appno"], f["file"]), os.path.join(out, "assets", "fig", f["file"]))
    return figs


def fig_boxes(k, x0, y0, W, H, gap=20):
    """Frame rectangles for k figures: one wide, two or three columns, or a 2×2 grid."""
    if k == 4:
        w, h = (W - gap) / 2, (H - gap) / 2
        return [(x0 + (i % 2) * (w + gap), y0 + (i // 2) * (h + gap), w, h) for i in range(4)]
    w = (W - (k - 1) * gap) / max(1, k)
    return [(x0 + i * (w + gap), y0, w, H) for i in range(k)]


def add_transitions(out, style, slots, total, w, h, pal=None):
    """Write compositions/tx.html and mount it above every scene in index.html."""
    open(os.path.join(out, "compositions", "tx.html"), "w", encoding="utf-8").write(transitions(style, slots, total, w, h, pal))
    ip = os.path.join(out, "index.html")
    idx = open(ip, encoding="utf-8").read()
    if 'id="tx"' not in idx:
        host = (f'      <div id="tx" data-composition-id="tx" data-composition-src="compositions/tx.html" data-start="0" data-duration="{total}" '
                f'data-track-index="3" data-track-kind="graphics" data-width="{w}" data-height="{h}" style="z-index: 50"></div>\n')
        open(ip, "w", encoding="utf-8").write(idx.replace('      <audio id="bgm"', host + '      <audio id="bgm"', 1))


def grain(opacity=0.07):
    """Static paper-grain layer (SVG turbulence), sits above the ground and below content."""
    svg = ("<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/>"
           "<feColorMatrix values='0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.9 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>")
    return (f'<div style="position: absolute; inset: 0; pointer-events: none; opacity: {opacity}; '
            f'background-image: url(&quot;data:image/svg+xml;utf8,{svg}&quot;)" data-layout-ignore></div>')


def _alpha(rgba_s, k):
    """Scale the alpha of an 'rgba(r, g, b, a)' string by k."""
    head, a = rgba_s.rsplit(",", 1)
    return f"{head}, {float(a.strip(' )')) * k:.3f})"


def blobs(sid, colors, d, seed=1):
    """Soft colour fields drifting slowly across the scene (finite tweens). Pure gradients, no CSS blur filter (costly per frame)."""
    import random
    rnd = random.Random(seed)
    html, js = "", []
    for i, col in enumerate(colors):
        x, y, s = rnd.randint(-200, 1500), rnd.randint(-200, 700), rnd.randint(520, 760)
        html += (f'<div class="{sid}-blob" id="{sid}-bl{i}" style="position: absolute; left: {x}px; top: {y}px; width: {s}px; height: {s}px; border-radius: 50%; '
                 f'background: radial-gradient(circle, {col} 0%, {_alpha(col, 0.4)} 40%, transparent 70%)" data-layout-ignore></div>')
        js.append(f'    tl.to("#{sid}-bl{i}", {{ x: {rnd.randint(-260, 260)}, y: {rnd.randint(-160, 160)}, scale: {rnd.uniform(0.85, 1.2):.2f}, duration: {d:.1f}, ease: "sine.inOut" }}, 0);')
    return html, js


def motes(sid, color, d, n=16, seed=7):
    """Small particles rising slowly — deterministic positions."""
    import random
    rnd = random.Random(seed)
    html, js = "", []
    for i in range(n):
        x, y, s = rnd.randint(60, 1860), rnd.randint(200, 1060), rnd.choice((6, 8, 10, 12))
        html += (f'<i class="{sid}-mt" id="{sid}-mt{i}" style="position: absolute; left: {x}px; top: {y}px; width: {s}px; height: {s}px; border-radius: 50%; '
                 f'background: {color}; opacity: {rnd.uniform(0.25, 0.6):.2f}" data-layout-ignore></i>')
        js.append(f'    tl.to("#{sid}-mt{i}", {{ y: -{rnd.randint(80, 220)}, x: {rnd.randint(-40, 40)}, duration: {d:.1f}, ease: "none" }}, 0);')
    return html, js


def particle_text(sel, t0, dur=2.6, color="#ffffff", cap=1700, spread=0.32):
    """JS for a scene timeline: the one-line text in `sel` (display: inline-block) assembles from a seeded particle cloud
    while the crisp DOM line wipes in behind the arriving front (technique from the registry's particle-text-dissolve).
    Targets are sampled from a raster of the element's own computed font, lazily once fonts are loaded; every frame is a
    pure function of timeline time, painted from the timeline's onUpdate."""
    return f"""    (() => {{
      const el = document.querySelector("{sel}"); const root = el.closest("[data-composition-id]");
      const cv = document.createElement("canvas"); cv.width = root.clientWidth || 1920; cv.height = root.clientHeight || 1080;
      cv.style.cssText = "position:absolute;left:0;top:0;width:100%;height:100%;pointer-events:none;z-index:40";
      cv.setAttribute("data-layout-ignore", ""); root.appendChild(cv);
      const ctx = cv.getContext("2d"); let rows = null; let builtReady = false;
      const ready = () => !document.fonts || document.fonts.status === "loaded";
      const build = () => {{
        builtReady = ready(); rows = [];
        const cs = getComputedStyle(el); let x = 0, y = 0, n = el;
        while (n && n !== root) {{ x += n.offsetLeft; y += n.offsetTop; n = n.offsetParent; }}
        const off = document.createElement("canvas"); off.width = cv.width; off.height = cv.height;
        const oc = off.getContext("2d", {{ willReadFrequently: true }});
        oc.font = cs.fontStyle + " " + cs.fontWeight + " " + cs.fontSize + " " + cs.fontFamily;
        try {{ oc.letterSpacing = cs.letterSpacing === "normal" ? "0px" : cs.letterSpacing; }} catch (e) {{}}
        const m = oc.measureText(el.textContent); const asc = m.fontBoundingBoxAscent || parseFloat(cs.fontSize) * 0.8;
        const desc = m.fontBoundingBoxDescent || parseFloat(cs.fontSize) * 0.2;
        const left = x + (parseFloat(cs.paddingLeft) || 0) + Math.max(0, (el.clientWidth - (parseFloat(cs.paddingLeft) || 0) - (parseFloat(cs.paddingRight) || 0) - m.width) * (cs.textAlign === "center" ? 0.5 : 0));
        const base = y + (el.offsetHeight - asc - desc) / 2 + asc;
        oc.textBaseline = "alphabetic"; oc.fillStyle = "#fff"; oc.fillText(el.textContent, left, base);
        const bx = Math.max(0, Math.floor(left - 20)), by = Math.max(0, Math.floor(y - 30));
        const bw = Math.min(cv.width - bx, Math.ceil(m.width + 40)), bh = Math.min(cv.height - by, Math.ceil(el.offsetHeight + 60));
        if (bw <= 0 || bh <= 0) return;
        const data = oc.getImageData(bx, by, bw, bh).data; const step = Math.max(3, Math.round(parseFloat(cs.fontSize) / 30));
        const cells = [];
        for (let yy = 0; yy < bh; yy += step) for (let xx = 0; xx < bw; xx += step) if (data[(yy * bw + xx) * 4 + 3] > 127) cells.push([bx + xx, by + yy]);
        let st = 0x9d1550f7; const rnd = () => {{ st = (Math.imul(1664525, st) + 1013904223) >>> 0; return st / 4294967296; }};
        const keep = cells.length > {cap} ? {cap} / cells.length : 1; const minD = Math.min(cv.width, cv.height);
        const x0 = bx, span = Math.max(1, bw);
        for (const [tx, ty] of cells) {{
          if (rnd() >= keep) continue;
          const at = Math.min(0.9, 0.2 + 0.62 * (tx - x0) / span + 0.05 * rnd()); const a = rnd() * Math.PI * 2;
          rows.push({{ tx, ty, at, travel: 0.18 + 0.1 * rnd(), fade: 0.05 + 0.04 * rnd(), off: (0.1 + {spread} * rnd()) * minD,
                       ox: Math.cos(a), oy: Math.sin(a), r: step * (0.35 + 0.4 * rnd()), dim: 0.55 + 0.45 * rnd() }});
        }}
      }};
      const clamp = (v) => (v < 0 ? 0 : v > 1 ? 1 : v);
      const paint = () => {{
        const p = clamp((tl.time() - {t0}) / {dur});
        ctx.clearRect(0, 0, cv.width, cv.height);
        if (p <= 0 || p >= 1) return;
        if (!rows || (!builtReady && ready())) {{ if (!el.getClientRects().length || !el.offsetWidth) return; build(); }}
        const endC = clamp((1 - p) / 0.04); ctx.fillStyle = "{color}";
        for (const r of rows) {{
          const birth = Math.max(0, r.at - r.travel); const u = clamp((p - birth) / (r.at - birth)); if (u <= 0) continue;
          const alpha = clamp(u / 0.16) * (1 - clamp((p - r.at) / r.fade)) * r.dim * endC; if (alpha <= 0.002) continue;
          const dd = r.off * Math.pow(1 - u, 3); ctx.globalAlpha = alpha * 0.92;
          ctx.beginPath(); ctx.arc(r.tx + r.ox * dd, r.ty + r.oy * dd, r.r, 0, Math.PI * 2); ctx.fill();
        }}
        ctx.globalAlpha = 1;
      }};
      const prev = tl.eventCallback("onUpdate"); tl.eventCallback("onUpdate", () => {{ if (prev) prev(); paint(); }});
      tl.fromTo(el, {{ opacity: 0 }}, {{ opacity: 1, duration: {dur * 0.3:.2f}, ease: "power2.out" }}, {t0 + dur * 0.16:.2f});
      tl.fromTo(el, {{ clipPath: "inset(-30% 100% -30% 0%)" }}, {{ clipPath: "inset(-30% 0% -30% 0%)", duration: {dur * 0.76:.2f}, ease: "power1.inOut" }}, {t0 + dur * 0.18:.2f});
      tl.to({{}}, {{ duration: {dur:.2f} }}, {t0:.2f});
    }})();"""


def transitions(style, slots, total, w=1920, h=1080, pal=None):
    """Overlay composition that covers each scene boundary with a styled wipe."""
    cuts = [st for _, _, st, _ in slots][1:]
    if style == "G":
        body = ('<div id="tx-a" style="position: absolute; top: 0; bottom: 0; left: 0; width: 100%; background: #0e0e0e"></div>'
                '<div id="tx-b" style="position: absolute; top: 0; bottom: 0; left: 0; width: 100%; background: #d62f3a"></div>')
        js = ['    tl.set("#tx-a, #tx-b", { xPercent: -101 }, 0);']
        for t in cuts:
            js += [f'    tl.set("#tx-a, #tx-b", {{ xPercent: -101 }}, {t - 0.1:.2f});',
                   f'    tl.to("#tx-b", {{ xPercent: 0, duration: 0.28, ease: "power3.in" }}, {t - 0.08:.2f});',
                   f'    tl.to("#tx-a", {{ xPercent: 0, duration: 0.28, ease: "power3.in" }}, {t + 0.0:.2f});',
                   f'    tl.to("#tx-b", {{ xPercent: 101, duration: 0.01 }}, {t + 0.29:.2f});',
                   f'    tl.to("#tx-a", {{ xPercent: 101, duration: 0.42, ease: "expo.out" }}, {t + 0.3:.2f});']
    elif style == "H":
        core, node = pal
        body = (f'<div id="tx-c" style="position: absolute; left: {w / 2 - 1300}px; top: {h / 2 - 1300}px; width: 2600px; height: 2600px; border-radius: 50%; '
                f'background: radial-gradient(circle, #f4efe6 55%, {node} 62%, transparent 64%)"></div>')
        js = ['    tl.set("#tx-c", { scale: 0, opacity: 1 }, 0);']
        for t in cuts:
            js += [f'    tl.set("#tx-c", {{ scale: 0, opacity: 1 }}, {t - 0.14:.2f});',
                   f'    tl.to("#tx-c", {{ scale: 1, duration: 0.42, ease: "power2.in" }}, {t - 0.12:.2f});',
                   f'    tl.to("#tx-c", {{ opacity: 0, duration: 0.45, ease: "power2.out" }}, {t + 0.32:.2f});']
    elif style == "A":  # keynote light sweep: a soft white band crosses the cut
        body = ('<div id="tx-s" style="position: absolute; top: -20%; bottom: -20%; left: 0; width: 70%; '
                'background: linear-gradient(100deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.22) 45%, rgba(255,255,255,0.5) 50%, rgba(255,255,255,0.22) 55%, rgba(255,255,255,0) 100%)"></div>')
        js = ['    tl.set("#tx-s", { xPercent: -160, rotation: 8 }, 0);']
        for t in cuts:
            js += [f'    tl.set("#tx-s", {{ xPercent: -160 }}, {t - 0.3:.2f});',
                   f'    tl.to("#tx-s", {{ xPercent: 260, duration: 0.85, ease: "power2.inOut" }}, {t - 0.28:.2f});']
    elif style == "D":  # mint wash: a pale panel rises with a rounded edge, then lifts away
        body = ('<div id="tx-m" style="position: absolute; left: -5%; right: -5%; top: 0; height: 115%; background: #e8f3ec; border-radius: 0 0 50% 50% / 0 0 12% 12%"></div>')
        js = ['    tl.set("#tx-m", { yPercent: 101 }, 0);']
        for t in cuts:
            js += [f'    tl.set("#tx-m", {{ yPercent: 101 }}, {t - 0.12:.2f});',
                   f'    tl.to("#tx-m", {{ yPercent: -8, duration: 0.36, ease: "power3.in" }}, {t - 0.1:.2f});',
                   f'    tl.to("#tx-m", {{ yPercent: -115, duration: 0.5, ease: "power3.out" }}, {t + 0.28:.2f});']
    elif style == "E":  # Apple-style dip: brief fade through black
        body = '<div id="tx-k" style="position: absolute; inset: 0; background: #000"></div>'
        js = ['    tl.set("#tx-k", { opacity: 0 }, 0);']
        for t in cuts:
            js += [f'    tl.to("#tx-k", {{ opacity: 1, duration: 0.22, ease: "power1.in" }}, {t - 0.02:.2f});',
                   f'    tl.to("#tx-k", {{ opacity: 0, duration: 0.4, ease: "power1.out" }}, {t + 0.22:.2f});']
    else:  # I
        body = ('<div id="tx-p" style="position: absolute; left: 0; right: 0; top: 0; height: 100%; background: #f7f4ec">'
                '<div style="position: absolute; left: 0; right: 0; top: 0; height: 9px; border-top: 4px solid #121212; border-bottom: 1px solid #121212"></div></div>')
        js = ['    tl.set("#tx-p", { yPercent: 101 }, 0);']
        for t in cuts:
            js += [f'    tl.set("#tx-p", {{ yPercent: 101 }}, {t - 0.08:.2f});',
                   f'    tl.to("#tx-p", {{ yPercent: 0, duration: 0.32, ease: "power3.in" }}, {t - 0.06:.2f});',
                   f'    tl.to("#tx-p", {{ yPercent: -101, duration: 0.45, ease: "expo.out" }}, {t + 0.3:.2f});']
    return f"""<template>
  <style>
    #tx-root {{ position: absolute; inset: 0; overflow: hidden; pointer-events: none; }}
  </style>
  <div id="tx-root" data-composition-id="tx" data-width="{w}" data-height="{h}">{body}</div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
    tl.set({{}}, {{}}, {total});
    window.__timelines["tx"] = tl;
  </script>
</template>
"""
