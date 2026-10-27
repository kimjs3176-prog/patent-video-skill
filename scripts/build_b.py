"""Template B: vertical 9:16 card-news infographic (light ground, swipe carousel), 50 s.

Usage: python -I tools/build_b.py data/content/<order>-<appno>.json [...]
Output: videos_b/<slug>/ ; same content JSON as template A.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import CONTACT, DISCLAIMER, E, MUSIC, PALETTES, ROOT, fit, rgba  # noqa: E402
from icons import icon  # noqa: E402
from visuals import copy_figures, pick_figures, step_icon  # noqa: E402

W, H = 1080, 1920
SLOTS = [("b1", "b1-cover", 0.0, 5.0), ("b2", "b2-summary", 4.5, 6.5), ("b3", "b3-process", 10.5, 10.0),
         ("b4", "b4-proof", 20.0, 9.5), ("bf", "bf-figures", 29.0, 5.5), ("b5", "b5-features", 34.0, 6.0),
         ("b6", "b6-apps", 39.5, 5.0), ("b7", "b7-outro", 44.0, 6.0)]
TOTAL = 50.0
INK, SUB, MUTED, GROUND = "#111827", "#4b5563", "#6b7280", "#f3f4f7"


def darken(hexc, f):
    h = hexc.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % (int(r * (1 - f)), int(g * (1 - f)), int(b * (1 - f)))


def plain(s):
    return E(s.replace("|", ""))


def emph(s, acc):
    if "|" in s:
        p, g = s.split("|", 1)
        return f'{E(p)}<span style="color: {acc}">{E(g)}</span>'
    return E(s)


def head(sid, pal, idx):
    a, b, c = pal
    acc = darken(b, 0.28)
    dots = "".join(f'<i class="dot{" on" if i == idx else ""}"></i>' for i in range(len(SLOTS)))
    css = f"""<template>
  <style>
    @font-face {{ font-family: "NotoKR"; src: url("assets/fonts/NotoSansKR-VF.ttf") format("truetype"); font-weight: 100 900; }}
    #root {{ position: absolute; inset: 0; overflow: hidden; font-family: "NotoKR", "Outfit", sans-serif; color: {INK}; background: {GROUND}; word-break: keep-all; }}
    #{sid}-in {{ position: absolute; inset: 0; }}
    .deco {{ position: absolute; border-radius: 50%; }}
    .bar {{ position: absolute; left: 60px; right: 60px; top: 196px; height: 64px; display: flex; align-items: center; justify-content: space-between; }}
    .tag {{ height: 56px; padding: 0 26px; border-radius: 28px; background: {acc}; color: #fff; font-size: 28px; font-weight: 800; line-height: 56px; letter-spacing: 0.02em; }}
    .dots {{ display: flex; gap: 10px; }}
    .dot {{ width: 14px; height: 14px; border-radius: 7px; background: #d1d5db; }}
    .dot.on {{ width: 44px; background: {acc}; }}
    .prog {{ position: absolute; left: 60px; right: 60px; top: 272px; height: 6px; border-radius: 3px; background: #e3e5ea; overflow: hidden; }}
    .prog i {{ position: absolute; left: 0; top: 0; width: 100%; height: 6px; background: {acc}; transform-origin: 0% 50%; transform: scaleX(0); }}
    .card {{ position: absolute; left: 60px; top: 300px; width: 960px; height: 1010px; border-radius: 44px; background: #fff;
      box-shadow: 0 24px 60px rgba(17, 24, 39, 0.10); overflow: hidden; }}
    .eyebrow {{ position: absolute; left: 60px; top: 56px; font-size: 30px; font-weight: 800; color: {acc}; letter-spacing: 0.04em; }}
    .ttl {{ position: absolute; left: 60px; right: 60px; top: 104px; font-size: 60px; line-height: 1.2; font-weight: 900; letter-spacing: -0.03em; }}
    .tint {{ background: {rgba(b, 0.14)}; }}
  </style>"""
    top = f"""
      <div class="deco" style="left: -260px; top: 1420px; width: 760px; height: 760px; background: radial-gradient(circle, {rgba(a, 0.28)} 0%, {rgba(a, 0)} 70%)" data-layout-ignore></div>
      <div class="deco" style="left: 560px; top: 1480px; width: 700px; height: 700px; background: radial-gradient(circle, {rgba(c, 0.24)} 0%, {rgba(c, 0)} 70%)" data-layout-ignore></div>
      <div class="bar"><div class="tag">특허기술 카드</div><div class="dots">{dots}</div></div>
      <div class="prog"><i id="{sid}-prog"></i></div>"""
    return css, top


def wrap(sid, css, top, body, script, dur, extra_css=""):
    return f"""{css}
  <style>{extra_css}</style>
  <div id="root" data-composition-id="{sid}" data-width="{W}" data-height="{H}">
    <div id="{sid}-in">{top}
      <div class="card" id="{sid}-card">{body}</div>
    </div>
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    // swipe in from the right, swipe out to the left (card-news carousel)
    tl.fromTo("#{sid}-card", {{ x: {0 if sid == "b1" else 1080} }}, {{ x: 0, duration: 0.5, ease: "power3.out" }}, 0);
    tl.fromTo("#{sid}-prog", {{ scaleX: 0 }}, {{ scaleX: 1, duration: {dur:.2f}, ease: "none" }}, 0);
    {script}
    tl.to("#{sid}-card", {{ x: -1080, duration: 0.45, ease: "power3.in" }}, {dur - 0.45:.2f});
    window.__timelines["{sid}"] = tl;
  </script>
</template>
"""


def grad(gid, pal):
    a, b, c = pal
    return (f'<svg width="0" height="0" style="position: absolute" data-layout-ignore><defs><linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="{darken(a, 0.2)}" /><stop offset="1" stop-color="{darken(c, 0.2)}" /></linearGradient></defs></svg>')


def b1(c, pal, d):
    acc = darken(pal[1], 0.28)
    css, top = head("b1", pal, 0)
    name = c["name"].replace("|", "")
    body = f"""{grad("b1-lg", pal)}
        <div class="tint" id="b1-ic" style="position: absolute; left: 60px; top: 60px; width: 240px; height: 240px; border-radius: 48px">
          <div style="position: absolute; left: 40px; top: 40px">{icon(c["hero"], 160, "url(#b1-lg)", 5)}</div></div>
        <div id="b1-code" style="position: absolute; left: 60px; top: 360px; font-family: Outfit; font-size: {fit(name, 64, 840)}px; font-weight: 800; color: {acc}; white-space: nowrap">{E(name)}</div>
        <div id="b1-sub" style="position: absolute; left: 60px; right: 60px; top: 450px; font-size: 92px; line-height: 1.14; font-weight: 900; letter-spacing: -0.04em">{E(c["sub"])}</div>
        <div id="b1-meta" style="position: absolute; left: 60px; right: 60px; top: 880px; font-size: 30px; line-height: 1.5; font-weight: 600; color: {SUB}">{E(c["institute"])}<br />{E(c.get("patlabel", "등록특허"))} 제{E(c["regno"])}호</div>"""
    script = """
    tl.fromTo("#b1-ic", { scale: 0.6, opacity: 0.4 }, { scale: 1, opacity: 1, duration: 0.6, ease: "back.out(1.7)" }, 0.1);
    tl.fromTo("#b1-ic .ic", { strokeDasharray: 1, strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 1.0, ease: "power2.out", stagger: 0.08 }, 0.3);
    tl.fromTo(["#b1-code", "#b1-sub", "#b1-meta"], { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.6, ease: "power3.out", stagger: 0.18 }, 0.2);"""
    return wrap("b1", css, top, body, script, d)


def b2(c, pal, d):
    acc = darken(pal[1], 0.28)
    css, top = head("b2", pal, 1)
    tiles = ""
    for i, ch in enumerate(c["chips"][:4]):
        x, y = 60 + (i % 2) * 435, 330 + (i // 2) * 270
        vs = fit(ch["v"] + ch.get("u", ""), 72, 360)
        tiles += (f'<div class="b2-t tint" id="b2-t{i}" style="left: {x}px; top: {y}px"><div class="k">{E(ch["k"])}</div>'
                  f'<div class="v" style="font-size: {vs}px">{E(ch["v"])}<small>{E(ch.get("u", ""))}</small></div></div>')
    body = f"""<div class="eyebrow">핵심 요약</div><div class="ttl" id="b2-ttl">{emph(c["headline"], acc)}</div>{tiles}"""
    extra = f""".b2-t {{ position: absolute; width: 405px; height: 240px; border-radius: 32px; }}
    .b2-t .k {{ position: absolute; left: 32px; top: 30px; right: 24px; font-size: 30px; font-weight: 700; color: {SUB}; white-space: nowrap; }}
    .b2-t .v {{ position: absolute; left: 32px; bottom: 34px; font-weight: 900; color: {acc}; letter-spacing: -0.03em; white-space: nowrap; }}
    .b2-t .v small {{ font-size: 30px; margin-left: 4px; }}"""
    script = """
    tl.fromTo("#b2-ttl", { opacity: 0, y: 24 }, { opacity: 1, y: 0, duration: 0.6, ease: "power3.out" }, 0.35);
    tl.fromTo(".b2-t", { opacity: 0, scale: 0.9 }, { opacity: 1, scale: 1, duration: 0.5, ease: "back.out(1.6)", stagger: 0.22 }, 0.8);"""
    return wrap("b2", css, top, body, script, d, extra)


def b3(c, pal, d):
    acc = darken(pal[1], 0.28)
    css, top = head("b3", pal, 2)
    steps = c["process"]["steps"][:6]
    n = len(steps)
    rh = min(150, 740 // n)
    rows = ""
    for i, st in enumerate(steps):
        big = st["big"] + st.get("u", "")
        rows += (f'<div class="b3-r" id="b3-r{i}" style="top: {300 + i * rh}px"><i class="node">{icon(step_icon(st["n"], c["hero"]), 36, "#9ca3af", 7)}</i>'
                 f'<div class="n">{E(st["n"])}</div><div class="d">{E(st["d"])}</div>'
                 f'<div class="big" style="font-size: {fit(big, 46, 300)}px">{E(big)}</div></div>')
    T = [round(0.7 + i * ((d - 1.4) / n), 2) for i in range(n)]
    body = f"""<div class="eyebrow">HOW IT WORKS</div><div class="ttl">{emph(c["process"]["title"], acc)}</div>
        <div class="b3-line" style="top: {300 + 30}px; height: {(n - 1) * rh}px"><div id="b3-fill"></div></div>{rows}"""
    extra = f""".b3-line {{ position: absolute; left: 87px; width: 6px; border-radius: 3px; background: #e5e7eb; }}
    #b3-fill {{ position: absolute; left: 0; top: 0; width: 6px; height: 100%; border-radius: 3px; background: {acc}; transform-origin: 50% 0%; transform: scaleY(0); }}
    .b3-r {{ position: absolute; left: 60px; right: 60px; height: {rh}px; }}
    .b3-r .node {{ position: absolute; left: 0; top: 0; width: 60px; height: 60px; border-radius: 50%; background: #fff; border: 4px solid #d1d5db; display: flex; align-items: center; justify-content: center; }}
    .b3-r.on .node {{ border-color: {acc}; background: {acc}; }}
    .b3-r.on .node svg {{ stroke: #fff; }}
    .b3-r .n {{ position: absolute; left: 86px; top: 0; font-size: 40px; font-weight: 900; letter-spacing: -0.02em; white-space: nowrap; }}
    .b3-r .d {{ position: absolute; left: 86px; top: 58px; font-size: 28px; font-weight: 600; color: {SUB}; white-space: nowrap; }}
    .b3-r .big {{ position: absolute; right: 0; top: 0; font-family: Outfit, NotoKR; font-weight: 800; color: {acc}; white-space: nowrap; }}"""
    js = "\n".join(
        f'    tl.fromTo("#b3-r{i}", {{ opacity: 0, x: 40 }}, {{ opacity: 1, x: 0, duration: 0.5, ease: "power3.out" }}, {t});\n'
        f'    tl.set("#b3-r{i}", {{ className: "b3-r on" }}, {t + 0.2:.2f});'
        for i, t in enumerate(T))
    script = f"""
{js}
    tl.fromTo("#b3-fill", {{ scaleY: 0 }}, {{ scaleY: 1, duration: {T[-1] - T[0] + 0.3:.2f}, ease: "none" }}, {T[0]});"""
    return wrap("b3", css, top, body, script, d, extra)


def b4(c, pal, d):
    acc = darken(pal[1], 0.28)
    css, top = head("b4", pal, 3)
    pr = c["proof"]
    if pr.get("kind") == "anatomy":
        parts = pr["parts"][:6]
        cells = "".join(f'<div class="b4-p" id="b4-p{i}" style="left: {60 + (i % 2) * 430}px; top: {690 + (i // 2) * 74}px">'
                        + (f'<b>{E(str(p["ref"]))}</b>' if p.get("ref") else '<b class="dot"></b>')
                        + f'<span>{E(p["n"])}</span></div>' for i, p in enumerate(parts))
        body = f"""<div class="eyebrow">{E(pr.get("eyebrow", "ANATOMY"))}</div><div class="ttl">{emph(pr.get("title", "핵심 |구성"), acc)}</div>
        <div id="b4-fig"><img src="assets/fig/{E(pr["figure"])}" alt="{E(pr.get("figcap", "도면"))}" /></div>{cells}
        <div class="b4-src">{E(c.get("source", ""))}</div>"""
        extra = f"""#b4-fig {{ position: absolute; left: 60px; top: 220px; width: 840px; height: 440px; border-radius: 28px; background: #f7f7f9; overflow: hidden; }}
    #b4-fig img {{ position: absolute; left: 20px; top: 16px; width: 800px; height: 408px; object-fit: contain; }}
    .b4-p {{ position: absolute; width: 410px; height: 64px; display: flex; align-items: center; gap: 16px; font-size: 32px; font-weight: 800; white-space: nowrap; }}
    .b4-p b {{ min-width: 52px; height: 52px; padding: 0 10px; border-radius: 26px; background: {acc}; color: #fff; font-size: 28px; text-align: center; line-height: 52px; }}
    .b4-p b.dot {{ min-width: 20px; width: 20px; height: 20px; padding: 0; margin: 0 16px; }}
    .b4-src {{ position: absolute; left: 60px; right: 60px; bottom: 26px; font-size: 28px; color: {MUTED}; white-space: nowrap; overflow: hidden; }}"""
        script = """
    tl.fromTo("#b4-fig", { opacity: 0, scale: 0.94 }, { opacity: 1, scale: 1, duration: 0.6, ease: "power3.out" }, 0.4);
    tl.fromTo("#b4-fig img", { scale: 1 }, { scale: 1.06, duration: 9, ease: "none" }, 0.5);
    tl.fromTo(".b4-p", { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.45, ease: "power3.out", stagger: 0.45 }, 1.2);"""
        return wrap("b4", css, top, body, script, d, extra)
    items = pr["items"][:3]
    k = len(items)
    span = (d - 1.2) / k
    T = [round(0.5 + i * span, 2) for i in range(k)]
    blocks, js = "", []
    for i, it in enumerate(items):
        big = it["big"] + it.get("u", "")
        bars = it.get("bars") or []
        rows = ""
        if bars:
            mx = it.get("max") or max(x["v"] for x in bars) * 1.15
            for j, br in enumerate(bars[:4]):
                rows += (f'<div class="b4-row{" hi" if br.get("hi") else ""}" style="top: {560 + j * 92}px"><div class="lab">{E(br["l"])}</div>'
                         f'<div class="val">{E(br.get("t", ""))}</div><div class="trk"><div class="fill" id="b4-f{i}-{j}"></div></div></div>')
                js.append(f'tl.fromTo("#b4-f{i}-{j}", {{ scaleX: 0 }}, {{ scaleX: {max(0.004, min(1, br["v"] / mx)):.4f}, duration: 0.9, ease: "power3.out" }}, {T[i] + 0.4 + j * 0.15:.2f});')
        else:
            rows = f'<div style="position: absolute; left: 330px; top: 560px">{icon(it.get("icon", c["hero"]), 220, "url(#b4-lg)", 4)}</div>'
        blocks += (f'<div class="b4-it" id="b4-i{i}"><div class="big" style="font-size: {fit(big, 168, 840)}px">{E(it["big"])}<small>{E(it.get("u", ""))}</small></div>'
                   f'<div class="l">{E(it["l"])}</div><div class="s">{it.get("s", "")}</div>{rows}</div>')
        if i > 0:
            js.append(f'tl.to("#b4-i{i - 1}", {{ opacity: 0, x: -60, duration: 0.3, ease: "power2.in" }}, {T[i] - 0.3:.2f});')
        js.append(f'tl.fromTo("#b4-i{i}", {{ opacity: 0, x: 60 }}, {{ opacity: 1, x: 0, duration: 0.5, ease: "power3.out" }}, {T[i]:.2f});')
    body = f"""{grad("b4-lg", pal)}<div class="eyebrow">{E(pr.get("eyebrow", "PERFORMANCE"))}</div>{blocks}<div class="b4-src">{E(c.get("source", ""))}</div>"""
    extra = f""".b4-it {{ position: absolute; inset: 0; opacity: 0; }}
    .b4-it .big {{ position: absolute; left: 60px; top: 120px; font-family: Outfit, NotoKR; font-weight: 800; color: {acc}; line-height: 1; letter-spacing: -0.04em; white-space: nowrap; }}
    .b4-it .big small {{ font-size: 52px; margin-left: 6px; }}
    .b4-it .l {{ position: absolute; left: 60px; top: 330px; font-size: 52px; font-weight: 900; letter-spacing: -0.03em; }}
    .b4-it .s {{ position: absolute; left: 60px; right: 60px; top: 410px; font-size: 32px; line-height: 1.5; font-weight: 600; color: {SUB}; }}
    .b4-row {{ position: absolute; left: 60px; right: 60px; height: 84px; }}
    .b4-row .lab {{ position: absolute; left: 0; top: 0; font-size: 30px; font-weight: 700; color: {SUB}; white-space: nowrap; }}
    .b4-row .val {{ position: absolute; right: 0; top: 0; font-size: 30px; font-weight: 800; color: {SUB}; }}
    .b4-row .trk {{ position: absolute; left: 0; right: 0; top: 46px; height: 26px; border-radius: 13px; background: #eef0f3; overflow: hidden; }}
    .b4-row .fill {{ position: absolute; left: 0; top: 0; width: 100%; height: 100%; border-radius: 13px; background: #c7cbd3; transform-origin: 0% 50%; }}
    .b4-row.hi .fill {{ background: {acc}; }}
    .b4-row.hi .lab, .b4-row.hi .val {{ color: {INK}; }}
    .b4-src {{ position: absolute; left: 60px; right: 60px; bottom: 44px; font-size: 28px; color: {MUTED}; }}"""
    return wrap("b4", css, top, body, "\n    ".join([""] + js), d, extra)


def bf(c, pal, d):
    """One card of spec figures (two plates stacked); without figures, the process steps as pictogram tiles."""
    acc = darken(pal[1], 0.28)
    css, top = head("bf", pal, 4)
    figs = pick_figures(c, 2)
    if figs:
        hh = 330 if len(figs) == 2 else 690
        plates = "".join(f'<div class="bf-p" id="bf-p{i}" style="top: {250 + i * (hh + 80)}px; height: {hh}px"><img src="assets/fig/{E(f["file"])}" alt="명세서 도면 {i + 1}" /></div>'
                         f'<div class="bf-c" style="top: {250 + i * (hh + 80) + hh + 14}px"><b style="color: {acc}">도면 {i + 1}</b> 명세서 {f["page"]}쪽</div>'
                         for i, f in enumerate(figs))
    else:
        steps = c["process"]["steps"][:4]
        plates = "".join(f'<div class="bf-p tint" id="bf-p{i}" style="top: {250 + (i // 2) * 360}px; left: {60 + (i % 2) * 435}px; right: auto; width: 405px; height: 320px; '
                         f'display: flex; align-items: center; justify-content: center">{icon(step_icon(st["n"], c["hero"]), 150, acc, 5)}</div>'
                         f'<div class="bf-c" style="top: {250 + (i // 2) * 360 + 326}px; left: {60 + (i % 2) * 435}px">{E(st["n"])}</div>' for i, st in enumerate(steps))
    ttl = f'명세서 <span style="color: {acc}">도면</span>으로 보기' if figs else f'공정 <span style="color: {acc}">한눈에</span> 보기'
    body = f"""<div class="eyebrow">{"FROM THE SPECIFICATION" if figs else "AT A GLANCE"}</div><div class="ttl">{ttl}</div>{plates}"""
    extra = f""".bf-p {{ position: absolute; left: 60px; right: 60px; border-radius: 28px; background: #fff; border: 2px solid #eceef2; overflow: hidden; }}
    .bf-p img {{ position: absolute; inset: 14px; width: calc(100% - 28px); height: calc(100% - 28px); object-fit: contain; }}
    .bf-c {{ position: absolute; left: 64px; font-size: 28px; font-weight: 700; color: {SUB}; white-space: nowrap; }}"""
    script = f"""
    tl.fromTo(".bf-p", {{ opacity: 0, y: 40 }}, {{ opacity: 1, y: 0, duration: 0.6, ease: "power3.out", stagger: 0.25 }}, 0.45);
    tl.fromTo(".bf-c", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4, stagger: 0.25 }}, 0.8);
    tl.fromTo(".bf-p img", {{ scale: 1.12 }}, {{ scale: 1, duration: {d - 0.5:.1f}, ease: "power1.out" }}, 0.45);
    tl.fromTo(".bf-p .ic", {{ strokeDasharray: 1, strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: 1.0, ease: "power2.out", stagger: 0.05 }}, 0.7);"""
    return wrap("bf", css, top, body, script, d, extra)


def b5(c, pal, d):
    acc = darken(pal[1], 0.28)
    css, top = head("b5", pal, 5)
    f = c["features"]
    tiles = ""
    for i, t in enumerate(f["tiles"][:6]):
        x, y = 60 + (i % 2) * 435, 240 + (i // 2) * 250
        tiles += (f'<div class="b5-t tint" id="b5-t{i}" style="left: {x}px; top: {y}px"><div class="v" style="font-size: {fit(t["v"], 64, 345)}px">{E(t["v"])}</div>'
                  f'<div class="l">{E(t["l"])}</div><div class="s">{E(t["s"])}</div></div>')
    body = f"""<div class="eyebrow">HIGHLIGHTS</div><div class="ttl">{emph(f.get("title", "핵심 |특장점"), acc)}</div>{tiles}"""
    extra = f""".b5-t {{ position: absolute; width: 405px; height: 226px; border-radius: 30px; }}
    .b5-t .v {{ position: absolute; left: 30px; top: 26px; font-weight: 900; color: {acc}; letter-spacing: -0.03em; white-space: nowrap; }}
    .b5-t .l {{ position: absolute; left: 30px; top: 116px; font-size: 34px; font-weight: 800; white-space: nowrap; }}
    .b5-t .s {{ position: absolute; left: 30px; top: 166px; font-size: 28px; font-weight: 600; color: {SUB}; white-space: nowrap; }}"""
    script = """
    tl.fromTo(".b5-t", { opacity: 0, scale: 0.9 }, { opacity: 1, scale: 1, duration: 0.45, ease: "back.out(1.6)", stagger: 0.28 }, 0.5);"""
    return wrap("b5", css, top, body, script, d, extra)


def b6(c, pal, d):
    acc = darken(pal[1], 0.28)
    css, top = head("b6", pal, 6)
    rows = ""
    for i, ap in enumerate(c["apps"][:5]):
        tag = '<em>청구항</em>' if ap.get("claim") else ""
        rows += (f'<div class="b6-r" id="b6-r{i}" style="top: {230 + i * 150}px"><div class="ib tint">{icon(ap["icon"], 72, "url(#b6-lg)", 5)}</div>'
                 f'<div class="n">{E(ap["n"])}{tag}</div><div class="s">{E(ap["s"].replace("<br />", " "))}</div></div>')
    body = f"""{grad("b6-lg", pal)}<div class="eyebrow">APPLICATIONS</div><div class="ttl">기술이전 시 <span style="color: {acc}">활용분야</span></div>{rows}"""
    extra = f""".b6-r {{ position: absolute; left: 60px; right: 60px; height: 128px; }}
    .b6-r .ib {{ position: absolute; left: 0; top: 4px; width: 116px; height: 116px; border-radius: 28px; }}
    .b6-r .ib svg {{ position: absolute; left: 22px; top: 22px; }}
    .b6-r .n {{ position: absolute; left: 144px; top: 12px; font-size: 40px; font-weight: 900; white-space: nowrap; }}
    .b6-r .n em {{ font-style: normal; margin-left: 14px; padding: 4px 14px; border-radius: 18px; background: {acc}; color: #fff; font-size: 28px; font-weight: 800; vertical-align: 6px; }}
    .b6-r .s {{ position: absolute; left: 144px; top: 70px; font-size: 30px; font-weight: 600; color: {SUB}; white-space: nowrap; }}"""
    script = """
    tl.fromTo(".b6-r", { opacity: 0, x: 50 }, { opacity: 1, x: 0, duration: 0.45, ease: "power3.out", stagger: 0.32 }, 0.45);
    tl.fromTo(".b6-r .ic", { strokeDasharray: 1, strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 0.7, ease: "power2.out", stagger: 0.05 }, 0.6);"""
    return wrap("b6", css, top, body, script, d, extra)


def b7(c, pal, d):
    acc = darken(pal[1], 0.28)
    css, top = head("b7", pal, 7)
    name = c["name"].replace("|", "")
    body = f"""<div class="eyebrow">TECH TRANSFER</div>
        <div id="b7-code" style="position: absolute; left: 60px; top: 110px; font-family: Outfit; font-size: {fit(name, 96, 840)}px; font-weight: 800; color: {acc}; white-space: nowrap">{E(name)}</div>
        <div id="b7-sub" style="position: absolute; left: 60px; right: 60px; top: 240px; font-size: 52px; line-height: 1.2; font-weight: 900; letter-spacing: -0.03em">{E(c["sub"])}</div>
        <div class="b7-row tint" id="b7-r1" style="top: 460px"><span>기술이전 문의</span><b>{CONTACT}</b></div>
        <div id="b7-meta" style="position: absolute; left: 60px; right: 60px; top: 640px; font-size: 28px; line-height: 1.5; font-weight: 600; color: {SUB}">{E(c.get("patlabel", "등록특허"))} 제{E(c["regno"])}호 · 대한민국 ({E(c["institute"])})</div>
        <div id="b7-disc" style="position: absolute; left: 60px; right: 60px; top: 750px; font-size: 28px; line-height: 1.5; font-weight: 500; color: {MUTED}">{DISCLAIMER}</div>"""
    extra = f""".b7-row {{ position: absolute; left: 60px; right: 60px; height: 116px; border-radius: 28px; display: flex; align-items: center; justify-content: space-between; padding: 0 36px; }}
    .b7-row span {{ font-size: 30px; font-weight: 700; color: {SUB}; }}
    .b7-row b {{ font-size: 44px; font-weight: 900; color: {acc}; }}"""
    script = """
    tl.fromTo(["#b7-code", "#b7-sub", "#b7-r1", "#b7-meta", "#b7-disc"], { opacity: 0, y: 26 }, { opacity: 1, y: 0, duration: 0.5, ease: "power3.out", stagger: 0.12 }, 0.3);"""
    # the outro holds to the end: no swipe-out
    return wrap("b7", css, top, body, script, d + 1.0, extra)


SCENES = {"b1-cover": b1, "b2-summary": b2, "b3-process": b3, "b4-proof": b4, "bf-figures": bf, "b5-features": b5, "b6-apps": b6, "b7-outro": b7}


def index(c):
    music = MUSIC[(int(c["order"]) - 1) % len(MUSIC)]
    hosts = "\n".join(
        f'      <div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{f}.html" data-start="{st}" data-duration="{du}" '
        f'data-track-index="{1 if i % 2 == 0 else 2}" data-track-kind="graphics" data-width="{W}" data-height="{H}" style="z-index: {i + 1}"></div>'
        for i, (sid, f, st, du) in enumerate(SLOTS))
    sfx = "\n".join(
        f'      <audio id="sfx-{i}" class="clip" src="assets/sfx/whoosh-short.mp3" data-start="{st}" data-duration="0.55" data-track-index="{11 + i % 2}" data-volume="0.14"></audio>'
        for i, (_, _, st, _) in enumerate(SLOTS) if i > 0)
    return f"""<!doctype html>
<html lang="ko">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      @font-face {{ font-family: "NotoKR"; src: url("assets/fonts/NotoSansKR-VF.ttf") format("truetype"); font-weight: 100 900; }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: {W}px; height: {H}px; overflow: hidden; background: {GROUND}; }}
      #root {{ position: relative; width: 100%; height: 100%; font-family: "NotoKR", "Outfit", sans-serif; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="{W}" data-height="{H}">
{hosts}
      <audio id="bgm" class="clip" src="assets/music/{music}" data-start="0" data-duration="{TOTAL}" data-track-index="10" data-volume="0.6" data-fade-in="0.3" data-fade-out="2.5"></audio>
{sfx}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
"""


def build(path, out_root="videos_b"):
    c = json.load(open(path, encoding="utf-8"))
    pal = PALETTES.get(c.get("palette", "blue"), PALETTES["blue"])
    slug = f'{int(c["order"]):03d}-{c["appno"]}'
    out = os.path.join(ROOT, out_root, slug)
    os.makedirs(os.path.join(out, "compositions"), exist_ok=True)
    os.makedirs(os.path.join(out, "assets", "fig"), exist_ok=True)
    for sub in ("fonts", "sfx", "music"):
        dst = os.path.join(out, "assets", sub)
        if not os.path.exists(dst) and os.path.isdir(os.path.join(ROOT, "assets", sub)):
            shutil.copytree(os.path.join(ROOT, "assets", sub), dst)
    if c["proof"].get("kind") == "anatomy":
        shutil.copy(os.path.join(ROOT, "data", "patents", c["appno"], c["proof"]["figure"]), os.path.join(out, "assets", "fig", c["proof"]["figure"]))
    for fn in ("package.json", "hyperframes.json"):
        s = open(os.path.join(ROOT, "template", fn), encoding="utf-8").read().replace("__SLUG__", slug + "-b")
        open(os.path.join(out, fn), "w", encoding="utf-8").write(s)
    for sid, f, st, du in SLOTS:
        open(os.path.join(out, "compositions", f + ".html"), "w", encoding="utf-8").write(SCENES[f](c, pal, du))
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(index(c))
    copy_figures(c, out)
    print(slug, "built (B)")
    return out


if __name__ == "__main__":
    for p in sys.argv[1:]:
        build(p)
