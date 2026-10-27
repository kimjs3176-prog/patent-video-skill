"""Templates G, H, I — 16:9 styles adapted from the HyperFrames registry examples (via nexu-io/open-design, Apache-2.0),
driven by the same content JSON as A–F.

G  Swiss grid       16:9, 56 s    paper + hairline grid, giant Archivo numerals, one red accent, black data bar (ref: frame-swiss-grid / frame-pentagram-stat)
H  Organic soft-tech 16:9, 52.5 s beige ground, frosted cards, radial node graphs, wave timeline (ref: frame-takram-organic)
I  Newsroom editorial 16:9, 51.5 s cream paper, serif headlines, ruled tables, axis bar charts, colophon (ref: frame-nyt-graph / frame-data-chart-nyt)

Usage: python -I tools/build_ghi.py G|H|I data/content/<order>-<appno>.json [...]
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_def  # noqa: E402
from build import CONTACT, DISCLAIMER, E, fit, rgba  # noqa: E402
from build_def import count, darken, grad_text, plain, pop, scene, up  # noqa: E402
from icons import icon  # noqa: E402
from visuals import add_transitions, blobs, copy_figures, fig_boxes, grain, particle_text, pick_figures, step_icon  # noqa: E402


def oneline(s):
    return s.replace("<br />", " ").replace("<br/>", " ").replace("<br>", " ")


def accent(s, cls):
    """'plain|accent' -> html with the accent part in cls (solid colour, no gradient)."""
    return grad_text(s, cls)


def items_of(pr, d):
    items = pr["items"][:3]
    span = (d - 0.6) / len(items)
    return items, [round(0.4 + i * span, 2) for i in range(len(items))]


def swap(js, sid, i, T):
    if i > 0:
        js.append(f'    tl.to("#{sid}-k{i - 1}", {{ opacity: 0, duration: 0.4, ease: "power2.in" }}, {T[i] - 0.4:.2f});')
    js.append(f'    tl.fromTo("#{sid}-k{i}", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.8, ease: "expo.out" }}, {T[i]:.2f});')


def draw(sel, t, d=1.4, stagger=0.0):
    return (f'    tl.fromTo("{sel}", {{ strokeDasharray: 1, strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: {d}, ease: "power2.inOut"'
            + (f", stagger: {stagger}" if stagger else "") + f" }}, {t:.2f});")


# ======================================================================= G  Swiss grid
RED = "#d62f3a"
G_SLOTS = [("g1", "g1-open", 0.0, 8.0), ("g2", "g2-brief", 7.5, 6.5), ("g3", "g3-steps", 13.5, 9.0),
           ("g4", "g4-proof", 22.0, 13.0), ("gf", "gf-figures", 34.5, 7.5), ("g5", "g5-grid", 41.5, 6.5),
           ("g6", "g6-uses", 47.5, 6.5), ("g7", "g7-end", 53.5, 6.5)]


def g_css():
    return f"""    @font-face {{ font-family: "Archivo"; src: url("assets/fonts/ref/Archivo-latin-var.woff2") format("woff2"); font-weight: 100 900; unicode-range: U+0000-00FF, U+2000-206F; }}
    .paper {{ background: #f3f3f1; color: #0e0e0e; }}
    .ink {{ background: #0e0e0e; color: #f3f3f1; }}
    .ar {{ font-family: "Archivo", "Pretendard", sans-serif; }}
    .red {{ color: {RED}; }}
    .lab {{ font-size: 30px; font-weight: 700; color: {RED}; letter-spacing: 0.04em; }}
    .lab .ar {{ letter-spacing: 0.12em; }}
    .h {{ font-weight: 800; letter-spacing: -0.04em; line-height: 1.14; }}
    .sub {{ font-size: 34px; font-weight: 500; color: #5c5c5c; line-height: 1.5; letter-spacing: -0.02em; }}
    .vr {{ position: absolute; top: 0; bottom: 0; width: 1px; background: rgba(0, 0, 0, 0.13); transform-origin: 50% 0%; }}
    .hr {{ position: absolute; left: 120px; right: 120px; height: 1px; background: rgba(0, 0, 0, 0.13); transform-origin: 0% 50%; }}
    .ink .vr, .ink .hr {{ background: rgba(255, 255, 255, 0.14); }}
    .foot {{ position: absolute; left: 120px; right: 120px; bottom: 38px; display: flex; justify-content: space-between; font-size: 28px; font-weight: 600; color: #686868; white-space: nowrap; }}"""


def g_grid(sid, hrs=(120, 960)):
    html = "".join(f'<div class="vr" style="left: {x}px" data-layout-ignore></div>' for x in (120, 960, 1800))
    html += "".join(f'<div class="hr" style="top: {y}px" data-layout-ignore></div>' for y in hrs)
    js = [f'    tl.fromTo("#{sid}-in .vr", {{ scaleY: 0 }}, {{ scaleY: 1, duration: 1.0, ease: "expo.out", stagger: 0.08 }}, 0);',
          f'    tl.fromTo("#{sid}-in .hr", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 1.0, ease: "expo.out", stagger: 0.1 }}, 0.1);']
    return html, js


def g_foot(sid, c, n, label):
    return (f'<div class="foot" id="{sid}-ft"><span><span class="ar" style="font-weight: 800; color: #0e0e0e">{plain(c["name"])}</span>'
            f'&nbsp;&nbsp;0{n} / 08 · {E(label)}</span><span>{E(c.get("patlabel", "등록특허"))} {E(c["regno"])}</span></div>')


def g1(c, pal, d):
    name = plain(c["name"])
    ghost = name.split()[0] if name.split() else name
    cells = ""
    for i, ch in enumerate(c["chips"][:3]):
        fs = fit(ch["v"] + ch.get("u", ""), 46, 300)
        cells += (f'<div class="gc"><b class="ar" style="font-size: {fs}px">{E(ch["v"])}<small>{E(ch.get("u", ""))}</small></b>'
                  f'<span>{E(ch["k"])}</span></div>')
    grid, gjs = g_grid("g1", (120,))
    body = f"""{grid}
      <div id="g1-ghost" class="ar" style="position: absolute; right: -60px; top: 60px; font-size: 760px; font-weight: 900; line-height: 0.82; letter-spacing: -0.05em; color: #0e0e0e; opacity: 0.06; white-space: nowrap" data-layout-ignore>{ghost}</div>
      <div class="lab" id="g1-l" style="position: absolute; left: 160px; top: 190px"><span class="ar">{E(c.get("patlabel", "등록특허"))} {E(c["regno"])}</span> · {E(c["institute"])}</div>
      <div style="position: absolute; left: 150px; top: 250px; width: 1640px; overflow: hidden; padding-bottom: 20px">
        <div id="g1-n" class="ar" style="display: inline-block; font-size: {fit(name + '.', 200, 1560)}px; font-weight: 900; line-height: 0.95; letter-spacing: -0.045em; white-space: nowrap">{name}<span class="red">.</span></div></div>
      <div id="g1-rule" style="position: absolute; left: 160px; top: 510px; width: 420px; height: 8px; background: {RED}; transform-origin: 0% 50%"></div>
      <div class="h" id="g1-s" style="position: absolute; left: 160px; top: 560px; font-size: {fit(c["sub"], 84, 1560)}px">{E(c["sub"])}</div>
      <div class="sub" id="g1-b" style="position: absolute; left: 160px; top: {560 + fit(c["sub"], 84, 1560) + 44}px; width: 1500px">{plain(c["headline"])}</div>
      <div id="g1-bar" style="position: absolute; left: 0; right: 0; bottom: 0; height: 132px; background: #0e0e0e; display: flex; align-items: center; gap: 72px; padding: 0 160px">{cells}</div>"""
    css = g_css() + f"""
    .gc {{ display: flex; align-items: baseline; gap: 16px; white-space: nowrap; }}
    .gc b {{ color: {RED}; font-weight: 800; letter-spacing: -0.02em; }}
    .gc b small {{ font-size: 28px; margin-left: 4px; }}
    .gc span {{ font-size: 28px; font-weight: 600; color: rgba(255, 255, 255, 0.74); }}"""
    js = gjs + ['    tl.fromTo("#g1-ghost", { opacity: 0, yPercent: 8 }, { opacity: 0.06, yPercent: 0, duration: 1.4, ease: "expo.out" }, 0.2);',
                '    tl.to("#g1-ghost", { x: -90, duration: 8, ease: "none" }, 0);',
                up("#g1-l", 0.4),
                particle_text("#g1-n", 0.3, 2.6, RED),
                '    tl.fromTo("#g1-rule", { scaleX: 0 }, { scaleX: 1, duration: 0.9, ease: "expo.out" }, 1.3);',
                up("#g1-s", 1.5), up("#g1-b", 2.0),
                '    tl.fromTo("#g1-bar", { yPercent: 100 }, { yPercent: 0, duration: 0.8, ease: "expo.out" }, 2.5);',
                up(".gc", 2.9, 0.2, 0.7, 20),
                '    tl.fromTo("#g1-s, #g1-b, #g1-rule, #g1-l", { x: 0 }, { x: -36, duration: 5, ease: "none" }, 3.0);']
    return scene("g1", 1920, 1080, css, body, "\n".join(js), "paper", enter=False)


def g2(c, pal, d):
    rows = ""
    for i, ch in enumerate(c["chips"][:4]):
        rows += (f'<div class="sr" id="g2-r{i}"><span>{E(ch["k"])}</span>'
                 f'<b class="ar" style="font-size: {fit(ch["v"] + ch.get("u", ""), 72, 500)}px">{E(ch["v"])}<small>{E(ch.get("u", ""))}</small></b></div>')
    grid, gjs = g_grid("g2")
    body = f"""{grid}
      <div style="position: absolute; left: 160px; top: 170px; width: 740px">
        <div class="lab" id="g2-l"><span class="ar">01</span> — 발명 개요</div>
        <div class="h" id="g2-t" style="margin-top: 30px; font-size: {min(70, fit(plain(c["headline"]), 70, 2000))}px">{accent(c["headline"], "red")}</div>
        <div class="sub" id="g2-b" style="margin-top: 34px">{E(c["process"].get("note", ""))}</div></div>
      <div style="position: absolute; left: 1000px; top: 190px; width: 760px">
        <div id="g2-top" style="height: 8px; background: #0e0e0e; transform-origin: 0% 50%"></div>{rows}</div>
      {g_foot("g2", c, 2, "발명 개요")}"""
    css = g_css() + """
    .sr { display: flex; justify-content: space-between; align-items: baseline; height: 150px; padding-top: 44px; border-bottom: 1px solid rgba(0, 0, 0, 0.18); white-space: nowrap; }
    .sr span { font-size: 32px; font-weight: 700; color: #5c5c5c; }
    .sr b { font-weight: 800; letter-spacing: -0.03em; }
    .sr b small { font-size: 30px; margin-left: 6px; color: #5c5c5c; }"""
    js = gjs + [up("#g2-l", 0.3), up("#g2-t", 0.45), up("#g2-b", 1.2),
                '    tl.fromTo("#g2-top", { scaleX: 0 }, { scaleX: 1, duration: 0.9, ease: "expo.out" }, 0.6);',
                up(".sr", 0.9, 0.35, 0.7, 24), up("#g2-ft", 1.0),
                '    tl.fromTo("#g2-in > div:not(.vr):not(.hr)", { x: 0 }, { x: -18, duration: 5, ease: "none" }, 1.5);']
    return scene("g2", 1920, 1080, css, body, "\n".join(js), "paper")


def g3(c, pal, d):
    steps = c["process"]["steps"][:6]
    n = len(steps)
    cw = 1680 / n
    cols = ""
    for i, st in enumerate(steps):
        x = 120 + i * cw
        cols += (f'<div class="col" id="g3-c{i}" style="left: {x:.0f}px; width: {cw:.0f}px">'
                 f'<div class="ix ar">0{i + 1}</div><div class="pg">{icon(step_icon(st["n"], c["hero"]), 84, "#0e0e0e", 4)}</div>'
                 f'<div class="bg ar" style="font-size: {fit(st["big"] + st.get("u", ""), 76, cw - 56)}px">{E(st["big"])}<small>{E(st.get("u", ""))}</small></div>'
                 f'<div class="nm" style="font-size: {fit(st["n"], 38, cw - 56)}px">{E(st["n"])}</div><div class="ds">{E(st["d"])}</div></div>')
    grid, gjs = g_grid("g3", (120,))
    body = f"""{grid}
      <div style="position: absolute; left: 160px; top: 160px; width: 1600px">
        <div class="lab" id="g3-l"><span class="ar">02</span> — 작동 원리</div>
        <div class="h" id="g3-t" style="margin-top: 24px; font-size: {fit(plain(c["process"]["title"]), 66, 1600)}px">{accent(c["process"]["title"], "red")}</div></div>
      <div id="g3-line" style="position: absolute; left: 120px; right: 120px; top: 420px; height: 2px; background: #0e0e0e; transform-origin: 0% 50%"></div>
      <div id="g3-mk" style="position: absolute; left: 120px; top: 409px; width: 24px; height: 24px; background: {RED}"></div>
      {cols}
      {g_foot("g3", c, 3, "작동 원리")}"""
    css = g_css() + """
    .col { position: absolute; top: 420px; height: 520px; padding: 46px 28px 0; border-left: 1px solid rgba(0, 0, 0, 0.16); }
    .col .ix { font-size: 30px; font-weight: 700; color: #d62f3a; letter-spacing: 0.08em; }
    .col .pg { margin-top: 22px; height: 84px; }
    .col .bg { margin-top: 22px; font-weight: 800; letter-spacing: -0.035em; white-space: nowrap; line-height: 1; }
    .col .bg small { font-size: 30px; margin-left: 4px; color: #5c5c5c; }
    .col .nm { margin-top: 34px; font-weight: 800; letter-spacing: -0.03em; white-space: nowrap; }
    .col .ds { margin-top: 14px; font-size: 28px; font-weight: 500; color: #5c5c5c; line-height: 1.45; }"""
    T = [1.0 + i * (6.4 / n) for i in range(n)]
    js = gjs + [up("#g3-l", 0.3), up("#g3-t", 0.45),
                '    tl.fromTo("#g3-line", { scaleX: 0 }, { scaleX: 1, duration: 1.1, ease: "expo.out" }, 0.6);',
                pop("#g3-mk", 0.8)]
    for i, t in enumerate(T):
        js.append(up(f"#g3-c{i}", t, 0, 0.8, 34))
        js.append(draw(f"#g3-c{i} .ic", t + 0.1, 1.1, 0.06))
        if i:
            js.append(f'    tl.to("#g3-mk", {{ x: {i * cw:.0f}, duration: 0.6, ease: "expo.inOut" }}, {t - 0.1:.2f});')
    js.append(up("#g3-ft", 1.0))
    return scene("g3", 1920, 1080, css, body, "\n".join(js), "paper")


def g4(c, pal, d):
    pr = c["proof"]
    grid, gjs = g_grid("g4", (120,))
    css = g_css() + f"""
    .blk {{ position: absolute; inset: 0; opacity: 0; }}
    .big {{ font-weight: 900; letter-spacing: -0.05em; line-height: 0.9; white-space: nowrap; }}
    .big small {{ font-size: 0.36em; color: {RED}; margin-left: 8px; letter-spacing: -0.02em; }}
    .vb {{ position: absolute; bottom: 0; transform-origin: 50% 100%; background: rgba(14, 14, 14, 0.16); }}
    .vb.hi {{ background: {RED}; }}
    .vv {{ position: absolute; font-size: 36px; font-weight: 800; text-align: center; white-space: nowrap; }}
    .vl {{ position: absolute; top: 584px; font-size: 28px; font-weight: 600; color: #4f4f4f; text-align: center; line-height: 1.35; }}
    .pr {{ display: grid; grid-template-columns: 96px 1fr; align-items: center; border-top: 1px solid rgba(0, 0, 0, 0.16); height: 104px; }}
    .pr b {{ font-size: 44px; font-weight: 800; color: {RED}; }}
    .pr i {{ display: block; width: 22px; height: 22px; background: {RED}; margin-left: 8px; }}
    .pr .n {{ font-size: 36px; font-weight: 800; letter-spacing: -0.03em; white-space: nowrap; }}
    .pr .s {{ font-size: 28px; color: #5c5c5c; white-space: nowrap; margin-top: 2px; }}"""
    foot = (f'<div class="foot" id="g4-ft"><span>{E(c.get("source", ""))}</span>'
            f'<span>{E(c.get("patlabel", "등록특허"))} {E(c["regno"])}</span></div>')
    if pr.get("kind") == "anatomy":
        parts = "".join(f'<div class="pr" id="g4-p{i}">' + (f'<b class="ar">{E(str(p["ref"]))}</b>' if p.get("ref") else "<i></i>")
                        + f'<div><div class="n">{E(p["n"])}</div><div class="s">{E(p["d"])}</div></div></div>' for i, p in enumerate(pr["parts"][:6]))
        body = f"""{grid}
      <div id="g4-ph" style="position: absolute; left: 160px; top: 160px; width: 740px; height: 740px; background: #fff; border: 2px solid #0e0e0e; overflow: hidden">
        <img id="g4-img" src="assets/fig/{E(pr["figure"])}" alt="{E(pr.get("figcap", "도면"))}" style="position: absolute; inset: 30px; width: 676px; height: 676px; object-fit: contain" /></div>
      <div id="g4-cap" style="position: absolute; left: 160px; top: 920px; font-size: 28px; font-weight: 600; color: #5c5c5c">{E(pr.get("figcap", "대표 도면"))}</div>
      <div style="position: absolute; left: 1000px; top: 160px; width: 780px">
        <div class="lab" id="g4-l"><span class="ar">03</span> — 핵심 구성</div>
        <div class="h" id="g4-t" style="margin-top: 22px; margin-bottom: 34px; font-size: {fit(plain(pr.get("title", "핵심 구성")), 60, 780)}px">{accent(pr.get("title", "핵심 |구성"), "red")}</div>{parts}</div>
      {foot}"""
        js = gjs + [pop("#g4-ph", 0.3), '    tl.fromTo("#g4-img", { scale: 1 }, { scale: 1.06, duration: 13, ease: "none" }, 0.4);', up("#g4-cap", 0.9),
                    up("#g4-l", 0.5), up("#g4-t", 0.65), up(".pr", 1.4, 0.7, 0.7, 24), up("#g4-ft", 1.2)]
        return scene("g4", 1920, 1080, css, body, "\n".join(js), "paper")
    items, T = items_of(pr, d)
    blocks, js = "", list(gjs)
    for i, it in enumerate(items):
        big, u = it["big"], it.get("u", "")
        bars = (it.get("bars") or [])[:4]
        ghost = "".join(ch for ch in big if ch.isdigit())[:2] or big[:2]
        if bars:
            mx = it.get("max") or max(x["v"] for x in bars) * 1.15
            slot = 760 / len(bars)
            bw = min(150, slot * 0.55)
            vis = ""
            for j, br in enumerate(bars):
                h = max(6, 500 * min(1, br["v"] / mx))
                cx = slot * j + slot / 2
                vis += (f'<div class="vb{" hi" if br.get("hi") else ""}" id="g4-b{i}-{j}" style="left: {cx - bw / 2:.0f}px; width: {bw:.0f}px; height: {h:.0f}px"></div>'
                        f'<div class="vv ar" id="g4-v{i}-{j}" style="left: {cx - slot / 2:.0f}px; width: {slot:.0f}px; bottom: {h + 14:.0f}px{"; color: " + RED if br.get("hi") else ""}">{E(br.get("t", ""))}</div>'
                        f'<div class="vl" style="left: {cx - slot / 2 + 6:.0f}px; width: {slot - 12:.0f}px">{E(br["l"])}</div>')
            right = (f'<div style="position: absolute; left: 1020px; top: 300px; width: 760px; height: 560px">'
                     f'<div style="position: absolute; left: 0; right: 0; top: 0; height: 560px">{vis}</div>'
                     f'<div style="position: absolute; left: 0; right: 0; top: 560px; height: 3px; background: #0e0e0e"></div></div>')
            for j, br in enumerate(bars):
                js.append(f'    tl.fromTo("#g4-b{i}-{j}", {{ scaleY: 0 }}, {{ scaleY: 1, duration: 1.2, ease: "expo.out" }}, {T[i] + 0.7 + j * 0.18:.2f});')
                js.append(f'    tl.fromTo("#g4-v{i}-{j}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.5 }}, {T[i] + 1.3 + j * 0.18:.2f});')
        else:
            right = (f'<div style="position: absolute; left: 1120px; top: 240px; width: 560px; height: 560px; border: 2px solid #0e0e0e; display: flex; align-items: center; justify-content: center">'
                     f'<div style="position: absolute; right: -2px; top: -2px; width: 90px; height: 90px; background: {RED}"></div>{icon(it.get("icon", c["hero"]), 320, "#0e0e0e", 3)}</div>')
            js.append(draw(f"#g4-k{i} .ic", T[i] + 0.4))
        blocks += f"""
      <div class="blk" id="g4-k{i}">
        <div class="ar" style="position: absolute; right: -40px; top: 80px; font-size: 900px; font-weight: 900; line-height: 0.8; letter-spacing: -0.06em; color: #0e0e0e; opacity: 0.05; white-space: nowrap" data-layout-ignore>{E(ghost)}</div>
        <div style="position: absolute; left: 160px; top: 170px; width: 800px">
          <div class="lab"><span class="ar">03</span> — {E(pr.get("eyebrow", "PERFORMANCE"))}</div>
          <div class="big ar" style="margin-top: 40px; font-size: {fit(big + u, 250, 780)}px"><span id="g4-n{i}">{E(big)}</span><small>{E(u)}</small></div>
          <div class="h" style="margin-top: 44px; font-size: 56px">{E(it["l"])}</div>
          <div class="sub" style="margin-top: 20px">{it.get("s", "")}</div>
        </div>{right}</div>"""
        swap(js, "g4", i, T)
        js.append(count(f"g4-n{i}", big, T[i] + 0.3))
    js.append(up("#g4-ft", 1.0))
    body = grid + blocks + foot
    return scene("g4", 1920, 1080, css, body, "\n".join(x for x in js if x), "paper")


def gf(c, pal, d):
    figs = pick_figures(c, 4)
    grid, gjs = g_grid("gf", (120,))
    head = f"""
      <div style="position: absolute; left: 160px; top: 150px; width: 1600px">
        <div class="lab" id="gf-l"><span class="ar">04</span> — {"명세서 도면" if figs else "공정 한눈에"}</div>
        <div class="h" id="gf-t" style="margin-top: 22px; font-size: 60px">{"도면으로 보는" if figs else "한눈에 보는"} <span class="red">{E(c["sub"])}</span></div></div>"""
    css = g_css() + f"""
    .fr {{ position: absolute; background: #fff; border: 2px solid #0e0e0e; overflow: hidden; }}
    .fr .im {{ position: absolute; left: 0; right: 0; top: 0; bottom: 56px; overflow: hidden; }}
    .fr img {{ position: absolute; inset: 18px; width: calc(100% - 36px); height: calc(100% - 36px); object-fit: contain; }}
    .fr .cp {{ position: absolute; left: 0; right: 0; bottom: 0; height: 56px; border-top: 1px solid rgba(0, 0, 0, 0.16); padding: 0 20px; display: flex; align-items: center; gap: 14px; font-size: 28px; font-weight: 600; color: #4f4f4f; white-space: nowrap; }}
    .fr .cp b {{ color: {RED}; font-weight: 800; }}
    .sel {{ position: absolute; border: 6px solid {RED}; opacity: 0; }}"""
    if not figs:
        steps = c["process"]["steps"][:6]
        boxes = fig_boxes(len(steps), 120, 340, 1680, 560)
        cells = "".join(f'<div class="fr" id="gf-f{i}" style="left: {x:.0f}px; top: {y:.0f}px; width: {w:.0f}px; height: {h:.0f}px">'
                        f'<div class="im" style="display: flex; align-items: center; justify-content: center">{icon(step_icon(st["n"], c["hero"]), min(220, w * 0.6), "#0e0e0e", 3)}</div>'
                        f'<div class="cp"><b class="ar">0{i + 1}</b>{E(st["n"])}</div></div>' for i, (st, (x, y, w, h)) in enumerate(zip(steps, boxes)))
        js = gjs + [up("#gf-l", 0.3), up("#gf-t", 0.45), up(".fr", 0.8, 0.25, 0.8, 30), draw(".fr .ic", 1.0, 1.4, 0.04)]
        return scene("gf", 1920, 1080, css, grid + head + cells + g_foot("gf", c, 5, "도면"), "\n".join(js), "paper")
    boxes = fig_boxes(len(figs), 120, 340, 1680, 600)
    cells = "".join(f'<div class="fr" id="gf-f{i}" style="left: {x:.0f}px; top: {y:.0f}px; width: {w:.0f}px; height: {h:.0f}px">'
                    f'<div class="im"><img src="assets/fig/{E(f["file"])}" alt="명세서 도면 {i + 1}" /></div>'
                    f'<div class="cp"><b class="ar">FIG {i + 1:02d}</b>명세서 도면 · {f["page"]}쪽</div></div>' for i, (f, (x, y, w, h)) in enumerate(zip(figs, boxes)))
    sel = "".join(f'<div class="sel" id="gf-s{i}" style="left: {x - 10:.0f}px; top: {y - 10:.0f}px; width: {w + 20:.0f}px; height: {h + 20:.0f}px" data-layout-ignore></div>'
                  for i, (x, y, w, h) in enumerate(boxes))
    js = gjs + [up("#gf-l", 0.3), up("#gf-t", 0.45),
                '    tl.fromTo(".fr", { clipPath: "inset(0 100% 0 0)" }, { clipPath: "inset(0 0% 0 0)", duration: 0.9, ease: "expo.inOut", stagger: 0.3 }, 0.7);',
                f'    tl.fromTo(".fr img", {{ scale: 1.14 }}, {{ scale: 1, duration: {d - 0.8:.1f}, ease: "power1.out" }}, 0.7);',
                ]
    step = (d - 3.0) / max(1, len(figs))
    for i in range(len(boxes)):
        t = 2.0 + i * step
        js.append(f'    tl.fromTo("#gf-s{i}", {{ opacity: 0, scale: 1.04 }}, {{ opacity: 1, scale: 1, duration: 0.45, ease: "expo.out" }}, {t:.2f});')
        if i < len(boxes) - 1:
            js.append(f'    tl.to("#gf-s{i}", {{ opacity: 0, duration: 0.3 }}, {t + step - 0.05:.2f});')
    js.append(up("#gf-ft", 1.0))
    return scene("gf", 1920, 1080, css, grid + head + cells + sel + g_foot("gf", c, 5, "도면"), "\n".join(js), "paper")


def g5(c, pal, d):
    f = c["features"]
    cells = ""
    for i, t in enumerate(f["tiles"][:6]):
        cells += (f'<div class="cl" id="g5-t{i}"><i></i><div class="ix ar">0{i + 1}</div>'
                  f'<b class="ar" style="font-size: {fit(t["v"], 80, 470)}px">{E(t["v"])}</b><h5>{E(t["l"])}</h5><span>{E(t["s"])}</span></div>')
    grid, gjs = g_grid("g5", (120,))
    body = f"""{grid}
      <div style="position: absolute; left: 160px; top: 150px; width: 1600px">
        <div class="lab" id="g5-l"><span class="ar">05</span> — 특장점</div>
        <div class="h" id="g5-t" style="margin-top: 22px; font-size: {fit(plain(f.get("title", "핵심 특장점")), 66, 1600)}px">{accent(f.get("title", "핵심 |특장점"), "red")}</div></div>
      <div style="position: absolute; left: 120px; top: 340px; width: 1680px; display: grid; grid-template-columns: repeat(3, 1fr); border-top: 2px solid #0e0e0e">{cells}</div>
      {g_foot("g5", c, 6, "특장점")}"""
    css = g_css() + f"""
    .cl {{ position: relative; height: 310px; padding: 36px 40px 0; border-right: 1px solid rgba(0, 0, 0, 0.16); border-bottom: 1px solid rgba(0, 0, 0, 0.16); }}
    .cl:nth-child(3n) {{ border-right: 0; }}
    .cl i {{ position: absolute; left: 0; top: -2px; width: 100%; height: 6px; background: {RED}; transform-origin: 0% 50%; transform: scaleX(0); }}
    .cl .ix {{ font-size: 28px; font-weight: 700; color: {RED}; letter-spacing: 0.08em; }}
    .cl b {{ display: block; margin-top: 18px; font-weight: 800; letter-spacing: -0.04em; white-space: nowrap; line-height: 1.05; }}
    .cl h5 {{ font-size: 34px; font-weight: 800; margin-top: 18px; letter-spacing: -0.03em; white-space: nowrap; }}
    .cl span {{ display: block; font-size: 28px; color: #5c5c5c; margin-top: 8px; white-space: nowrap; }}"""
    js = gjs + [up("#g5-l", 0.3), up("#g5-t", 0.45),
                '    tl.fromTo(".cl i", { scaleX: 0 }, { scaleX: 1, duration: 0.6, ease: "expo.out", stagger: 0.22 }, 0.8);',
                '    tl.to(".cl i", { scaleX: 0, transformOrigin: "100% 50%", duration: 0.5, ease: "expo.in", stagger: 0.22 }, 1.5);',
                up(".cl > div, .cl b, .cl h5, .cl span", 0.95, 0.055, 0.7, 24), up("#g5-ft", 1.0)]
    return scene("g5", 1920, 1080, css, body, "\n".join(js), "paper")


def g6(c, pal, d):
    apps = c["apps"][:5]
    rows = "".join(f'<div class="ur" id="g6-r{i}"><div class="ix ar">0{i + 1}</div><div>{icon(ap["icon"], 60, "#0e0e0e", 5)}</div>'
                   f'<b style="font-size: {fit(ap["n"], 42, 420)}px">{E(ap["n"])}</b><span>{oneline(ap["s"])}</span>'
                   + ('<em>특허 청구항</em>' if ap.get("claim") else "<em style=\"border: 0\"></em>") + '</div>' for i, ap in enumerate(apps))
    grid, gjs = g_grid("g6", (120,))
    body = f"""{grid}
      <div style="position: absolute; left: 160px; top: 150px; width: 1600px">
        <div class="lab" id="g6-l"><span class="ar">06</span> — 활용분야</div>
        <div class="h" id="g6-t" style="margin-top: 22px; font-size: 66px">기술이전 시 <span class="red">활용분야</span></div></div>
      <div style="position: absolute; left: 120px; top: 340px; width: 1680px; border-top: 2px solid #0e0e0e">{rows}</div>
      {g_foot("g6", c, 7, "활용분야")}"""
    css = g_css() + f"""
    .ur {{ display: grid; grid-template-columns: 110px 100px 460px 1fr 200px; align-items: center; height: 120px; border-bottom: 1px solid rgba(0, 0, 0, 0.16); padding-left: 40px; }}
    .ur .ix {{ font-size: 30px; font-weight: 700; color: {RED}; letter-spacing: 0.08em; }}
    .ur b {{ font-weight: 800; letter-spacing: -0.03em; white-space: nowrap; }}
    .ur span {{ font-size: 30px; color: #5c5c5c; line-height: 1.35; }}
    .ur em {{ font-style: normal; justify-self: end; margin-right: 30px; font-size: 28px; font-weight: 700; color: {RED}; border: 2px solid {RED}; padding: 6px 14px; white-space: nowrap; }}"""
    js = gjs + [up("#g6-l", 0.3), up("#g6-t", 0.45), up(".ur", 0.9, 0.3, 0.7, 24), draw(".ur .ic", 1.1, 1.0, 0.05), up("#g6-ft", 1.0)]
    return scene("g6", 1920, 1080, css, body, "\n".join(js), "paper")


def g7(c, pal, d):
    name = plain(c["name"])
    cells = [("기술이전 문의", CONTACT), (c.get("patlabel", "등록특허"), c["regno"])]
    ch = "".join(f'<div class="ec" id="g7-c{i}"><span>{E(k)}</span><b>{E(v)}</b></div>' for i, (k, v) in enumerate(cells))
    grid, gjs = g_grid("g7", (120,))
    body = f"""{grid}
      <div style="position: absolute; left: 160px; top: 190px; width: 1600px; overflow: hidden; padding-bottom: 16px">
        <div id="g7-n" class="ar" style="display: inline-block; font-size: {fit(name + '.', 170, 1560)}px; font-weight: 900; line-height: 0.95; letter-spacing: -0.045em; white-space: nowrap">{name}<span class="red">.</span></div></div>
      <div class="h" id="g7-s" style="position: absolute; left: 160px; top: 400px; font-size: 48px">{E(c["sub"])}</div>
      <div style="position: absolute; left: 120px; top: 540px; width: 1680px; display: grid; grid-template-columns: repeat(2, 1fr); border-top: 2px solid {RED}">{ch}</div>
      <div id="g7-m" style="position: absolute; left: 160px; top: 760px; font-size: 30px; font-weight: 600; color: #b5b5b5">특허권자 대한민국 ({E(c["institute"])})</div>
      <div id="g7-d" style="position: absolute; left: 160px; top: 830px; width: 1600px; font-size: 28px; font-weight: 500; color: #9a9a9a; line-height: 1.5">{DISCLAIMER}</div>"""
    css = g_css() + f"""
    .ec {{ padding: 34px 40px 0; height: 170px; border-right: 1px solid rgba(255, 255, 255, 0.14); }}
    .ec:last-child {{ border: 0; }}
    .ec span {{ display: block; font-size: 28px; font-weight: 700; color: #f2737b; }}
    .ec b {{ display: block; margin-top: 12px; font-size: 46px; font-weight: 800; letter-spacing: -0.03em; white-space: nowrap; }}"""
    js = gjs + ['    tl.fromTo("#g7-n", { yPercent: 105 }, { yPercent: 0, duration: 1.1, ease: "expo.out" }, 0.3);',
                up("#g7-s", 0.9), up(".ec", 1.3, 0.2, 0.7, 24), up("#g7-m", 2.0), up("#g7-d", 2.3)]
    return scene("g7", 1920, 1080, css, body, "\n".join(js), "ink")


# ======================================================================= H  Organic soft-tech
SOFT = {"amber": "#c4834f", "green": "#5f8f63", "violet": "#8a6fb0", "aqua": "#4f8f99", "rose": "#b86a77", "blue": "#5b7bb0"}
SAGE = "#7d9b84"
H_SLOTS = [("h1", "h1-open", 0.0, 9.0), ("h2", "h2-wave", 8.5, 9.5), ("h3", "h3-proof", 17.5, 12.5),
           ("hf", "hf-figures", 29.5, 7.5), ("h4", "h4-cards", 36.5, 6.5), ("h5", "h5-network", 42.5, 8.5),
           ("h6", "h6-end", 50.5, 7.0)]


def h_cols(c):
    core = SOFT.get(c.get("palette", "blue"), SOFT["blue"])
    node = "#c4834f" if c.get("palette") == "green" else SAGE
    return core, darken(core, 0.24), node


def h_css(c):
    core, ct, node = h_cols(c)
    return f"""    @font-face {{ font-family: "Manrope"; src: url("assets/fonts/ref/Manrope-latin-var.woff2") format("woff2"); font-weight: 200 800; unicode-range: U+0000-00FF, U+2000-206F; }}
    .beige {{ background: radial-gradient(900px 700px at 78% 40%, {rgba(node, 0.16)}, transparent 70%), radial-gradient(800px 600px at 10% 90%, {rgba(core, 0.10)}, transparent 70%), #ebe6dd; color: #2a2722; }}
    .mr {{ font-family: "Manrope", "Pretendard", sans-serif; }}
    .ct {{ color: {ct}; }}
    .eye {{ font-size: 28px; font-weight: 700; color: #6c675d; letter-spacing: 0.06em; }}
    .eye .mr {{ letter-spacing: 0.22em; }}
    .h {{ font-weight: 800; letter-spacing: -0.035em; line-height: 1.16; }}
    .sub {{ font-size: 32px; font-weight: 500; color: #6c675d; line-height: 1.5; letter-spacing: -0.02em; }}
    .card {{ background: rgba(250, 247, 241, 0.92); border: 1px solid rgba(255, 255, 255, 0.9); border-radius: 40px; box-shadow: 0 40px 90px rgba(80, 64, 40, 0.13), 0 2px 0 rgba(255, 255, 255, 0.6) inset; }}
    .pill {{ background: rgba(250, 247, 241, 0.92); border-radius: 999px; box-shadow: 0 18px 40px rgba(80, 64, 40, 0.10); }}"""


def radial(cx, cy, rx, ry, angles, r_core, curve=0.18):
    """Return node centres and curved link paths from the core to each node."""
    pts, paths = [], []
    for a in angles:
        t = math.radians(a)
        x, y = cx + rx * math.cos(t), cy + ry * math.sin(t)
        sx, sy = cx + r_core * math.cos(t), cy + r_core * math.sin(t)
        mx, my = (sx + x) / 2, (sy + y) / 2
        nx, ny = -(y - sy), (x - sx)
        qx, qy = mx + nx * curve, my + ny * curve
        pts.append((x, y))
        paths.append(f"M{sx:.0f} {sy:.0f} Q{qx:.0f} {qy:.0f} {x:.0f} {y:.0f}")
    return pts, paths


def hscene(sid, c, d, css, body, js, enter=True):
    """Scene on the beige ground with slowly drifting colour fields behind the content."""
    core, ct, node = h_cols(c)
    bh, bj = blobs(sid, [rgba(node, 0.30), rgba(core, 0.22), rgba(node, 0.18)], d, sum(map(ord, sid)))
    return scene(sid, 1920, 1080, css, bh + body, "\n".join(bj + [js]), "beige", enter=enter)


def h1(c, pal, d):
    core, ct, node = h_cols(c)
    cx, cy = 1330, 450
    pts, paths = radial(cx, cy, 250, 250, [i * 45 - 90 for i in range(8)], 80)
    links = "".join(f'<path class="lk" d="{p}" pathLength="1" />' for p in paths)
    dots = "".join(f'<div class="nd" style="left: {x - 20:.0f}px; top: {y - 20:.0f}px"></div>' for x, y in pts)
    chips = "".join(f'<div class="cp pill"><b class="mr">{E(ch["v"])}<small>{E(ch.get("u", ""))}</small></b><span>{E(ch["k"])}</span></div>'
                    for ch in c["chips"][:4])
    hl = c["headline"]
    body = f"""
      <svg width="1920" height="1080" style="position: absolute; inset: 0" data-layout-ignore><g fill="none" stroke="{node}" stroke-width="3" stroke-linecap="round">{links}</g>
        <circle id="h1-ring" cx="{cx}" cy="{cy}" r="250" fill="none" stroke="{rgba(node, 0.35)}" stroke-width="2" stroke-dasharray="4 12" /></svg>
      <div id="h1-dots" data-layout-ignore>{dots}</div>
      <div id="h1-core" style="position: absolute; left: {cx - 80}px; top: {cy - 80}px; width: 160px; height: 160px; border-radius: 50%; background: {core}; box-shadow: 0 20px 60px {rgba(core, 0.45)}; display: flex; align-items: center; justify-content: center">{icon(c["hero"], 90, "#ffffff", 6)}</div>
      <div class="card" id="h1-card" style="position: absolute; left: 120px; top: 120px; width: 760px; height: 840px; padding: 60px 64px">
        <div class="eye" id="h1-e"><span class="mr">{E(c.get("patlabel", "등록특허"))} {E(c["regno"])}</span></div>
        <div class="eye" id="h1-i" style="margin-top: 10px; letter-spacing: 0">{E(c["institute"])}</div>
        <div class="h" id="h1-t" style="margin-top: 48px; font-size: 68px">{accent(hl, "ct")}<span style="color: {ct}">.</span></div>
        <div class="sub" id="h1-s" style="margin-top: 34px">{E(c["sub"])}</div>
        <div id="h1-n" class="mr ct" style="position: absolute; display: inline-block; left: 64px; bottom: 56px; font-size: {fit(plain(c["name"]), 52, 630)}px; font-weight: 800; letter-spacing: -0.01em; white-space: nowrap">{plain(c["name"])}</div></div>
      <div style="position: absolute; left: 960px; top: 780px; width: 840px; display: grid; grid-template-columns: 1fr 1fr; gap: 18px 20px">{chips}</div>"""
    css = h_css(c) + f"""
    .nd {{ position: absolute; width: 40px; height: 40px; border-radius: 50%; background: {node}; box-shadow: 0 8px 20px {rgba(node, 0.35)}; }}
    .cp {{ height: 84px; display: flex; align-items: center; gap: 16px; padding: 0 30px; white-space: nowrap; }}
    .cp b {{ font-size: 36px; font-weight: 800; color: {ct}; }}
    .cp b small {{ font-size: 28px; margin-left: 4px; }}
    .cp span {{ font-size: 28px; font-weight: 600; color: #6c675d; }}"""
    js = [pop("#h1-card", 0.1), up("#h1-e", 0.4), up("#h1-i", 0.55),
          '    tl.fromTo("#h1-t", { opacity: 0.3, y: 30 }, { opacity: 1, y: 0, duration: 1.1, ease: "expo.out" }, 0.3);',
          up("#h1-s", 1.4), particle_text("#h1-n", 1.6, 2.6, core),
          '    tl.fromTo("#h1-core", { scale: 0 }, { scale: 1, duration: 1.0, ease: "back.out(1.6)" }, 0.5);',
          draw(".lk", 0.9, 1.0, 0.07),
          '    tl.fromTo("#h1-ring", { opacity: 0, scale: 0.8, transformOrigin: "50% 50%" }, { opacity: 1, scale: 1, duration: 1.4, ease: "expo.out" }, 0.8);',
          '    tl.fromTo(".nd", { scale: 0 }, { scale: 1, duration: 0.6, ease: "back.out(2)", stagger: 0.07 }, 1.5);',
          '    tl.to(".nd", { y: -10, duration: 1.6, ease: "sine.inOut", yoyo: true, repeat: 3, stagger: 0.15 }, 2.3);',
          '    tl.to("#h1-core", { scale: 1.06, duration: 2, ease: "sine.inOut", yoyo: true, repeat: 2 }, 2.5);',
          up(".cp", 2.6, 0.15, 0.7, 24)]
    return hscene("h1", c, d, css, body, "\n".join(js), enter=False)


def h2(c, pal, d):
    core, ct, node = h_cols(c)
    steps = c["process"]["steps"][:6]
    n = len(steps)
    x0, x1, y0, amp = 160, 1760, 520, 46

    def wy(t):
        return y0 + amp * math.sin(2 * math.pi * 1.25 * t)
    pts = [(x0 + (x1 - x0) * k / 79, wy(k / 79)) for k in range(80)]
    path = "M" + " L".join(f"{x:.0f} {y:.0f}" for x, y in pts)
    span = (x1 - x0) / n
    cw = min(300, span - 22)
    nodes, cards = "", ""
    for i, st in enumerate(steps):
        t = (i + 0.5) / n
        x, y = x0 + (x1 - x0) * t, wy(t)
        last = i == n - 1
        nodes += (f'<div class="wn" id="h2-n{i}" style="left: {x - 48:.0f}px; top: {y - 48:.0f}px; border-color: {core if last else node}">{icon(step_icon(st["n"], c["hero"]), 56, ct, 5)}</div>'
                  f'<div class="wv mr" id="h2-v{i}" style="left: {x - span / 2:.0f}px; width: {span:.0f}px; top: {y - 150:.0f}px; font-size: {fit(st["big"] + st.get("u", ""), 46, span - 30)}px">{E(st["big"])}<small>{E(st.get("u", ""))}</small></div>')
        cards += (f'<div class="wc card" id="h2-c{i}" style="left: {x - cw / 2:.0f}px; width: {cw:.0f}px; top: 640px">'
                  f'<div class="ix mr">STEP 0{i + 1}</div><b style="font-size: {fit(st["n"], 36, cw - 48)}px">{E(st["n"])}</b><span>{E(st["d"])}</span></div>')
    js_pts = ",".join(f"[{x:.0f},{y:.0f}]" for x, y in pts)
    body = f"""
      <div style="position: absolute; left: 0; right: 0; top: 130px; text-align: center">
        <div class="eye" id="h2-e"><span class="mr">HOW IT WORKS</span></div>
        <div class="h" id="h2-t" style="margin-top: 18px; font-size: {fit(plain(c["process"]["title"]), 64, 1500)}px">{accent(c["process"]["title"], "ct")}</div></div>
      <svg width="1920" height="1080" style="position: absolute; inset: 0" data-layout-ignore>
        <path d="{path}" fill="none" stroke="{rgba(node, 0.25)}" stroke-width="14" stroke-linecap="round" />
        <path id="h2-path" d="{path}" pathLength="1" fill="none" stroke="{node}" stroke-width="4" stroke-linecap="round" /></svg>
      {nodes}
      <div id="h2-dot" style="position: absolute; left: -16px; top: -16px; width: 32px; height: 32px; border-radius: 50%; background: {core}; box-shadow: 0 0 0 10px {rgba(core, 0.18)}" data-layout-ignore></div>
      {cards}"""
    css = h_css(c) + f"""
    .wn {{ position: absolute; width: 96px; height: 96px; border-radius: 50%; background: #f7f3ec; border: 5px solid; display: flex; align-items: center; justify-content: center; box-shadow: 0 12px 28px rgba(80, 64, 40, 0.18); }}
    .wv {{ position: absolute; text-align: center; font-weight: 800; color: {ct}; white-space: nowrap; letter-spacing: -0.02em; }}
    .wv small {{ font-size: 28px; margin-left: 3px; }}
    .wc {{ position: absolute; padding: 30px 24px 32px; border-radius: 30px; text-align: center; }}
    .wc .ix {{ font-size: 28px; font-weight: 700; color: #6c675d; letter-spacing: 0.14em; }}
    .wc b {{ display: block; margin-top: 12px; font-weight: 800; letter-spacing: -0.03em; white-space: nowrap; }}
    .wc span {{ display: block; margin-top: 10px; font-size: 28px; color: #6c675d; line-height: 1.45; }}"""
    D = 6.6
    T = [1.0 + D * (i + 0.5) / n for i in range(n)]
    js = [up("#h2-e", 0.25), up("#h2-t", 0.4),
          f'    tl.fromTo("#h2-path", {{ strokeDasharray: 1, strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: {D}, ease: "none" }}, 1.0);',
          f'    (() => {{ const P = [{js_pts}]; const el = document.querySelector("#h2-dot"); const o = {{ t: 0 }}; '
          f'const put = () => {{ const f = o.t * (P.length - 1); const k = Math.min(P.length - 2, Math.floor(f)); const r = f - k; '
          f'el.style.transform = "translate(" + (P[k][0] + (P[k + 1][0] - P[k][0]) * r) + "px," + (P[k][1] + (P[k + 1][1] - P[k][1]) * r) + "px)"; }}; '
          f'put(); tl.to(o, {{ t: 1, duration: {D}, ease: "none", onUpdate: put }}, 1.0); }})();']
    for i, t in enumerate(T):
        js += [f'    tl.fromTo("#h2-n{i}", {{ scale: 0 }}, {{ scale: 1, duration: 0.6, ease: "back.out(2)" }}, {t - 0.15:.2f});',
               draw(f"#h2-n{i} .ic", t, 1.0, 0.05), up(f"#h2-v{i}", t, 0, 0.7, 20), up(f"#h2-c{i}", t + 0.1, 0, 0.8, 30)]
    return hscene("h2", c, d, css, body, "\n".join(js))


def h3(c, pal, d):
    core, ct, node = h_cols(c)
    pr = c["proof"]
    css = h_css(c) + f"""
    .blk {{ position: absolute; inset: 0; opacity: 0; }}
    .big {{ font-weight: 800; letter-spacing: -0.045em; line-height: 1; white-space: nowrap; color: {ct}; }}
    .big small {{ font-size: 0.38em; margin-left: 6px; }}
    .hb {{ margin: 0 0 44px; }}
    .hb .nm {{ font-size: 32px; font-weight: 700; display: flex; justify-content: space-between; white-space: nowrap; }}
    .hb .nm b {{ font-family: "Manrope", "Pretendard"; font-size: 38px; font-weight: 800; }}
    .hb .tr {{ margin-top: 14px; height: 60px; border-radius: 30px; background: #e2dbcd; overflow: hidden; }}
    .hb .tr i {{ display: block; height: 100%; width: 100%; border-radius: 30px; background: {rgba(node, 0.75)}; transform-origin: 0% 50%; transform: scaleX(0); }}
    .hb.hi .tr i {{ background: linear-gradient(90deg, {core}, {darken(core, 0.12)}); }}
    .hb.hi .nm b {{ color: {ct}; }}
    .pp {{ display: flex; align-items: center; gap: 22px; height: 100px; padding: 0 30px; margin-bottom: 16px; border-radius: 50px; }}
    .pp b {{ flex: none; width: 60px; height: 60px; border-radius: 50%; background: {core}; color: #fff; font-size: 28px; font-weight: 800; display: flex; align-items: center; justify-content: center; }}
    .pp .n {{ font-size: 34px; font-weight: 800; white-space: nowrap; }}
    .pp .s {{ font-size: 28px; color: #6c675d; white-space: nowrap; }}
    .src {{ position: absolute; left: 120px; bottom: 40px; font-size: 28px; color: #6c675d; }}"""
    src = f'<div class="src" id="h3-src">{E(c.get("source", ""))}</div>'
    if pr.get("kind") == "anatomy":
        parts = "".join(f'<div class="pp pill" id="h3-p{i}"><b class="mr">{E(str(p["ref"])) if p.get("ref") else "•"}</b>'
                        f'<div><div class="n">{E(p["n"])}</div><div class="s">{E(p["d"])}</div></div></div>' for i, p in enumerate(pr["parts"][:6]))
        body = f"""
      <div class="card" id="h3-ph" style="position: absolute; left: 120px; top: 110px; width: 800px; height: 840px; overflow: hidden; background: #fffdf9">
        <img id="h3-img" src="assets/fig/{E(pr["figure"])}" alt="{E(pr.get("figcap", "도면"))}" style="position: absolute; left: 50px; top: 90px; width: 700px; height: 700px; object-fit: contain" />
        <div class="eye" style="position: absolute; left: 50px; top: 40px; letter-spacing: 0">{E(pr.get("figcap", "대표 도면"))}</div></div>
      <div style="position: absolute; left: 1000px; top: 120px; width: 800px">
        <div class="eye" id="h3-e"><span class="mr">ANATOMY</span></div>
        <div class="h" id="h3-t" style="margin: 16px 0 34px; font-size: {fit(plain(pr.get("title", "핵심 구성")), 60, 800)}px">{accent(pr.get("title", "핵심 |구성"), "ct")}</div>{parts}</div>
      {src}"""
        js = [pop("#h3-ph", 0.3), '    tl.fromTo("#h3-img", { scale: 1 }, { scale: 1.06, duration: 13, ease: "none" }, 0.4);',
              up("#h3-e", 0.5), up("#h3-t", 0.65), up(".pp", 1.4, 0.7, 0.7, 24), up("#h3-src", 1.0)]
        return hscene("h3", c, d, css, body, "\n".join(js))
    items, T = items_of(pr, d)
    blocks, js = "", []
    for i, it in enumerate(items):
        big, u = it["big"], it.get("u", "")
        bars = (it.get("bars") or [])[:4]
        if bars:
            mx = it.get("max") or max(x["v"] for x in bars) * 1.15
            rows = "".join(f'<div class="hb{" hi" if br.get("hi") else ""}"><div class="nm"><span>{E(br["l"])}</span><b>{E(br.get("t", ""))}</b></div>'
                           f'<div class="tr"><i id="h3-f{i}-{j}"></i></div></div>' for j, br in enumerate(bars))
            right = f'<div class="card" style="position: absolute; left: 1000px; top: 220px; width: 800px; padding: 60px 60px 16px">{rows}</div>'
            js += [f'    tl.fromTo("#h3-f{i}-{j}", {{ scaleX: 0 }}, {{ scaleX: {max(0.02, min(1, br["v"] / mx)):.4f}, duration: 1.5, ease: "expo.out" }}, {T[i] + 0.8 + j * 0.2:.2f});'
                   for j, br in enumerate(bars)]
        else:
            right = (f'<div style="position: absolute; left: 1100px; top: 210px; width: 600px; height: 600px; border-radius: 50%; background: {rgba(node, 0.16)}; display: flex; align-items: center; justify-content: center">'
                     f'<div class="card" style="width: 400px; height: 400px; border-radius: 50%; display: flex; align-items: center; justify-content: center">{icon(it.get("icon", c["hero"]), 220, ct, 4)}</div></div>')
            js.append(draw(f"#h3-k{i} .ic", T[i] + 0.4))
        blocks += f"""
      <div class="blk" id="h3-k{i}">
        <div class="card" style="position: absolute; left: 120px; top: 180px; width: 800px; height: 680px; padding: 64px">
          <div class="eye"><span class="mr">{E(pr.get("eyebrow", "PERFORMANCE"))}</span></div>
          <div class="big mr" style="margin-top: 36px; font-size: {fit(big + u, 200, 672)}px"><span id="h3-n{i}">{E(big)}</span><small>{E(u)}</small></div>
          <div class="h" style="margin-top: 36px; font-size: 54px">{E(it["l"])}</div>
          <div class="sub" style="margin-top: 18px">{it.get("s", "")}</div></div>{right}</div>"""
        swap(js, "h3", i, T)
        js.append(count(f"h3-n{i}", big, T[i] + 0.3))
    js.append(up("#h3-src", 1.0))
    return hscene("h3", c, d, css, blocks + src, "\n".join(x for x in js if x))


def hf(c, pal, d):
    core, ct, node = h_cols(c)
    figs = pick_figures(c, 4)
    head = f"""
      <div style="position: absolute; left: 0; right: 0; top: 110px; text-align: center">
        <div class="eye" id="hf-e"><span class="mr">{"FROM THE SPECIFICATION" if figs else "AT A GLANCE"}</span></div>
        <div class="h" id="hf-t" style="margin-top: 16px; font-size: 60px">{'명세서 <span class="ct">도면</span>으로 보는 기술' if figs else '공정 <span class="ct">한눈에</span> 보기'}</div></div>"""
    css = h_css(c) + """
    .fc2 { position: absolute; padding: 20px 20px 0; border-radius: 30px; }
    .fc2 .im { position: absolute; left: 20px; right: 20px; top: 20px; bottom: 70px; border-radius: 18px; overflow: hidden; background: #fff; }
    .fc2 img { width: 100%; height: 100%; object-fit: contain; }
    .fc2 .cp { position: absolute; left: 28px; right: 28px; bottom: 18px; font-size: 28px; font-weight: 600; color: #6c675d; white-space: nowrap; }"""
    if not figs:
        items = [(step_icon(st["n"], c["hero"]), st["n"]) for st in c["process"]["steps"][:5]]
    else:
        items = None
    k = len(figs) if figs else len(items)
    w, h = {1: (980, 640), 2: (760, 560)}.get(k, (560, 470) if k == 3 else (470, 420))
    gap = (1680 - w) / max(1, k - 1) if k > 1 else 0
    gap = min(gap, w + 40)
    x0 = 960 - (gap * (k - 1) + w) / 2
    rots = [-4, 3, -2, 4, -3]
    cards, js = "", [up("#hf-e", 0.25), up("#hf-t", 0.4)]
    for i in range(k):
        x, y = x0 + i * gap, 330 + (18 if i % 2 else 0)
        if figs:
            inner = (f'<div class="im"><img src="assets/fig/{E(figs[i]["file"])}" alt="명세서 도면 {i + 1}" /></div>'
                     f'<div class="cp"><b class="ct mr">0{i + 1}</b>&nbsp; 명세서 도면 · {figs[i]["page"]}쪽</div>')
        else:
            inner = (f'<div class="im" style="display: flex; align-items: center; justify-content: center">{icon(items[i][0], min(200, w * 0.45), ct, 4)}</div>'
                     f'<div class="cp"><b class="ct mr">0{i + 1}</b>&nbsp; {E(items[i][1])}</div>')
        cards += f'<div class="fc2 card" id="hf-c{i}" style="left: {x:.0f}px; top: {y:.0f}px; width: {w}px; height: {h}px; z-index: {i + 1}">{inner}</div>'
        js.append(f'    tl.fromTo("#hf-c{i}", {{ opacity: 0, y: 260, rotation: 0 }}, {{ opacity: 1, y: 0, rotation: {rots[i]}, duration: 1.0, ease: "back.out(1.3)" }}, {0.7 + i * 0.22:.2f});')
    js.append(f'    tl.fromTo(".fc2 img", {{ scale: 1.1 }}, {{ scale: 1, duration: {d - 0.8:.1f}, ease: "power1.out" }}, 0.7);')
    if not figs:
        js.append(draw(".fc2 .ic", 1.0, 1.3, 0.03))
    step = (d - 2.9) / k
    for i in range(k):
        t = 2.0 + i * step
        js += [f'    tl.set("#hf-c{i}", {{ zIndex: 20 }}, {t:.2f});',
               f'    tl.to("#hf-c{i}", {{ scale: 1.08, y: -26, rotation: 0, duration: 0.6, ease: "expo.out" }}, {t:.2f});',
               f'    tl.to("#hf-c{i}", {{ scale: 1, y: 0, rotation: {rots[i]}, duration: 0.6, ease: "expo.inOut" }}, {t + step - 0.1:.2f});',
               f'    tl.set("#hf-c{i}", {{ zIndex: {i + 1} }}, {t + step + 0.5:.2f});']
    return hscene("hf", c, d, css, head + cards, "\n".join(js))


def h4(c, pal, d):
    core, ct, node = h_cols(c)
    f = c["features"]
    cards = "".join(f'<div class="fc card" id="h4-c{i}"><i style="background: {core if i == 0 else node}"></i>'
                    f'<b class="mr" style="font-size: {fit(t["v"], 70, 440)}px">{E(t["v"])}</b><h5>{E(t["l"])}</h5><span>{E(t["s"])}</span></div>'
                    for i, t in enumerate(f["tiles"][:6]))
    body = f"""
      <div style="position: absolute; left: 0; right: 0; top: 120px; text-align: center">
        <div class="eye" id="h4-e"><span class="mr">HIGHLIGHTS</span></div>
        <div class="h" id="h4-t" style="margin-top: 18px; font-size: {fit(plain(f.get("title", "핵심 특장점")), 64, 1500)}px">{accent(f.get("title", "핵심 |특장점"), "ct")}</div></div>
      <div style="position: absolute; left: 150px; top: 350px; width: 1620px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 30px">{cards}</div>"""
    css = h_css(c) + f"""
    .fc {{ position: relative; height: 300px; padding: 44px 44px 0; border-radius: 36px; }}
    .fc i {{ position: absolute; right: 40px; top: 44px; width: 26px; height: 26px; border-radius: 50%; }}
    .fc b {{ display: block; font-weight: 800; letter-spacing: -0.035em; white-space: nowrap; color: {ct}; line-height: 1.05; }}
    .fc h5 {{ font-size: 34px; font-weight: 800; margin-top: 20px; white-space: nowrap; }}
    .fc span {{ display: block; font-size: 28px; color: #6c675d; margin-top: 8px; white-space: nowrap; }}"""
    js = "\n".join([up("#h4-e", 0.25), up("#h4-t", 0.4), up(".fc", 0.9, 0.18, 0.9, 40),
                    '    tl.fromTo(".fc i", { scale: 0 }, { scale: 1, duration: 0.5, ease: "back.out(2)", stagger: 0.18 }, 1.3);',
                    '    tl.to(".fc", { y: -8, duration: 1.8, ease: "sine.inOut", yoyo: true, repeat: 2, stagger: 0.2 }, 2.4);'])
    return hscene("h4", c, d, css, body, js)


def h5(c, pal, d):
    core, ct, node = h_cols(c)
    apps = c["apps"][:5]
    k = len(apps)
    cx, cy = 960, 560
    angles = [-90 + 360 / k * i for i in range(k)]
    pts, paths = radial(cx, cy, 560, 290, angles, 110, 0.14)
    links = "".join(f'<path class="lk" d="{p}" pathLength="1" />' for p in paths)
    nodes = ""
    for i, ((x, y), ap) in enumerate(zip(pts, apps)):
        nodes += (f'<div class="an" id="h5-n{i}" style="left: {x - 180:.0f}px; top: {y - 52:.0f}px">'
                  f'<div class="ab" style="border-color: {node}">{icon(ap["icon"], 58, ct, 5)}</div>'
                  f'<b>{E(ap["n"])}</b><span>{oneline(ap["s"])}</span>' + ('<em>특허 청구항</em>' if ap.get("claim") else "") + '</div>')
    name = plain(c["name"])
    body = f"""
      <div style="position: absolute; left: 120px; top: 110px">
        <div class="eye" id="h5-e"><span class="mr">APPLICATIONS</span></div>
        <div class="h" id="h5-t" style="margin-top: 14px; font-size: 60px">기술이전 시 <span class="ct">활용분야</span></div></div>
      <svg width="1920" height="1080" style="position: absolute; inset: 0" data-layout-ignore><g fill="none" stroke="{node}" stroke-width="3" stroke-linecap="round">{links}</g></svg>
      <div id="h5-core" style="position: absolute; left: {cx - 110}px; top: {cy - 110}px; width: 220px; height: 220px; border-radius: 50%; background: {core}; box-shadow: 0 0 0 26px {rgba(core, 0.14)}, 0 30px 70px {rgba(core, 0.4)}; display: flex; align-items: center; justify-content: center">{icon(c["hero"], 110, "#ffffff", 5)}</div>
      <div id="h5-name" class="mr ct" style="position: absolute; left: {cx - 400}px; width: 800px; top: {cy + 140}px; text-align: center; white-space: nowrap"><span class="pill" style="display: inline-block; padding: 12px 30px; font-size: {fit(name, 38, 640)}px; font-weight: 800">{name}</span></div>
      {nodes}"""
    css = h_css(c) + f"""
    .an {{ position: absolute; width: 360px; text-align: center; }}
    .ab {{ width: 104px; height: 104px; margin: 0 auto; border-radius: 50%; background: #f7f3ec; border: 4px solid; display: flex; align-items: center; justify-content: center; box-shadow: 0 16px 36px rgba(80, 64, 40, 0.16); }}
    .an b {{ display: block; margin-top: 16px; font-size: 34px; font-weight: 800; white-space: nowrap; }}
    .an span {{ display: block; margin-top: 4px; font-size: 28px; color: #6c675d; white-space: nowrap; }}
    .an em {{ display: inline-block; margin-top: 8px; font-style: normal; font-size: 28px; font-weight: 700; color: {ct}; }}"""
    js = [up("#h5-e", 0.25), up("#h5-t", 0.4),
          '    tl.fromTo("#h5-core", { scale: 0 }, { scale: 1, duration: 1.0, ease: "back.out(1.6)" }, 0.4);', up("#h5-name", 0.9),
          draw(".lk", 0.9, 0.9, 0.15),
          '    tl.fromTo(".an", { opacity: 0, scale: 0.7 }, { opacity: 1, scale: 1, duration: 0.8, ease: "back.out(1.7)", stagger: 0.18 }, 1.4);',
          draw(".ab .ic", 1.6, 1.0, 0.03),
          '    tl.to(".an", { y: -10, duration: 1.8, ease: "sine.inOut", yoyo: true, repeat: 2, stagger: 0.2 }, 3.0);']
    return hscene("h5", c, d, css, body, "\n".join(js))


def h6(c, pal, d):
    core, ct, node = h_cols(c)
    name = plain(c["name"])
    cells = [("기술이전 문의", CONTACT), (c.get("patlabel", "등록특허"), c["regno"])]
    ch = "".join(f'<div class="ep pill" id="h6-c{i}"><span>{E(k)}</span><b>{E(v)}</b></div>' for i, (k, v) in enumerate(cells))
    body = f"""
      <div class="card" id="h6-card" style="position: absolute; left: 260px; top: 170px; width: 1400px; padding: 70px 80px 64px; text-align: center">
        <div class="eye" id="h6-e" style="letter-spacing: 0">{E(c["institute"])}</div>
        <div id="h6-n" class="mr ct" style="display: inline-block; margin-top: 20px; font-size: {fit(name, 104, 1200)}px; font-weight: 800; letter-spacing: -0.02em; white-space: nowrap">{name}</div>
        <div class="h" id="h6-s" style="margin-top: 10px; font-size: 44px">{E(c["sub"])}</div>
        <div style="display: flex; justify-content: center; gap: 20px; margin-top: 50px">{ch}</div></div>
      <div id="h6-m" style="position: absolute; left: 0; right: 0; top: 820px; text-align: center; font-size: 30px; font-weight: 600; color: #6c675d">특허권자 대한민국 ({E(c["institute"])})</div>
      <div id="h6-d" style="position: absolute; left: 160px; right: 160px; top: 880px; text-align: center; font-size: 28px; color: #6c675d; line-height: 1.5">{DISCLAIMER}</div>"""
    css = h_css(c) + """
    .ep { padding: 24px 36px; text-align: left; background: #efe9de; box-shadow: none; }
    .ep span { display: block; font-size: 28px; font-weight: 600; color: #6c675d; }
    .ep b { display: block; margin-top: 4px; font-size: 40px; font-weight: 800; white-space: nowrap; }"""
    js = "\n".join([pop("#h6-card", 0.2), up("#h6-e", 0.5), up("#h6-n", 0.65), up("#h6-s", 1.0), up(".ep", 1.4, 0.18, 0.7, 24),
                    up("#h6-m", 2.0), up("#h6-d", 2.3), '    tl.to("#h6-card", { scale: 1.015, duration: 4.5, ease: "none" }, 2.0);'])
    return hscene("h6", c, d, css, body, js)


# ======================================================================= I  Newsroom editorial
NEWS_RED = "#a4161a"
I_SLOTS = [("i1", "i1-front", 0.0, 8.5), ("i2", "i2-how", 8.0, 9.0), ("i3", "i3-chart", 16.5, 13.0),
           ("if", "if-figures", 29.0, 7.5), ("i4", "i4-facts", 36.0, 7.0), ("i5", "i5-index", 42.5, 7.0),
           ("i6", "i6-colophon", 49.0, 7.0)]


def i_css():
    return f"""    @font-face {{ font-family: "SrcSerif"; src: url("assets/fonts/ref/SourceSerif-400.woff2") format("woff2"); font-weight: 400; unicode-range: U+0000-00FF, U+2000-206F; }}
    @font-face {{ font-family: "SrcSerif"; src: url("assets/fonts/ref/SourceSerif-600.woff2") format("woff2"); font-weight: 600 900; unicode-range: U+0000-00FF, U+2000-206F; }}
    @font-face {{ font-family: "SrcSerif"; src: url("assets/fonts/ref/SourceSerif-400i.woff2") format("woff2"); font-weight: 400; font-style: italic; unicode-range: U+0000-00FF, U+2000-206F; }}
    @font-face {{ font-family: "NotoSerifKR"; src: url("assets/fonts/serif/NotoSerifKR-VF.ttf") format("truetype"); font-weight: 200 900; }}
    @font-face {{ font-family: "PlexMono"; src: url("assets/fonts/ref/IBMPlexMono-500.woff2") format("woff2"); font-weight: 500; unicode-range: U+0000-00FF, U+2000-206F; }}
    .news {{ background: #f7f4ec; color: #121212; }}
    .serif {{ font-family: "SrcSerif", "NotoSerifKR", serif; }}
    .mono {{ font-family: "PlexMono", "Pretendard", monospace; }}
    .kick {{ font-family: "PlexMono", "Pretendard", monospace; font-size: 28px; font-weight: 500; color: {NEWS_RED}; letter-spacing: 0.08em; }}
    .acc {{ color: {NEWS_RED}; }}
    .hd {{ font-family: "SrcSerif", "NotoSerifKR", serif; font-weight: 700; letter-spacing: -0.02em; line-height: 1.22; }}
    .dek {{ font-size: 34px; font-weight: 500; color: #4d4d4d; line-height: 1.5; letter-spacing: -0.02em; }}
    .mast {{ position: absolute; left: 120px; right: 120px; top: 40px; display: flex; justify-content: space-between; font-family: "PlexMono", "Pretendard", monospace; font-size: 28px; color: #555; white-space: nowrap; }}
    .r2 {{ position: absolute; left: 120px; right: 120px; top: 96px; height: 7px; border-top: 3px solid #121212; border-bottom: 1px solid #121212; transform-origin: 0% 50%; }}
    .ft span:first-child {{ overflow: hidden; text-overflow: ellipsis; max-width: 1380px; }}
    .ft {{ position: absolute; left: 120px; right: 120px; bottom: 36px; padding-top: 16px; border-top: 1px solid #cfc9bb; display: flex; justify-content: space-between; font-size: 28px; color: #555; white-space: nowrap; }}"""


def i_frame(sid, c, section):
    html = (f'<div class="mast" id="{sid}-mh"><span>TECH TRANSFER BRIEF · {E(section)}</span><span>{E(c.get("patlabel", "등록특허"))} {E(c["regno"])}</span></div>'
            f'<div class="r2" id="{sid}-r2"></div>')
    js = [f'    tl.fromTo("#{sid}-r2", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 1.0, ease: "expo.out" }}, 0);', up(f"#{sid}-mh", 0.15, 0, 0.6, 14)]
    return html, js


def i_foot(sid, c, left=None):
    return (f'<div class="ft" id="{sid}-ft"><span>{E(left if left is not None else c.get("source", ""))}</span>'
            f'<span class="mono">{plain(c["name"])}</span></div>')


def iscene(sid, css, body, js, enter=True):
    return scene(sid, 1920, 1080, css, grain(0.08) + body, js, "news", enter=enter)


def i1(c, pal, d):
    fr, fjs = i_frame("i1", c, "기술 소개")
    hl = plain(c["headline"])
    figs = pick_figures(c, 4)
    plate = (f'<img src="assets/fig/{E(figs[0]["file"])}" alt="대표 도면" style="position: absolute; inset: 24px; width: 490px; height: 610px; object-fit: contain" />'
             if figs else icon(c["hero"], 360, "#121212", 2.6))
    capt = f"{E(c['sub'])} — 명세서 대표 도면 ({figs[0]['page']}쪽)" if figs else f"{E(c['sub'])} 개념도"
    body = f"""{fr}
      <div style="position: absolute; left: 120px; top: 170px; width: 1020px">
        <div class="kick" id="i1-k">AGRI-TECH · {E(c["institute"])}</div>
        <div class="hd" id="i1-t" style="margin-top: 30px; font-size: {min(96, fit(hl, 96, 3000))}px">{accent(c["headline"], "acc")}</div>
        <div class="dek" id="i1-s" style="margin-top: 34px"><b style="color: #121212">{E(c["sub"])}</b> — {E(c["process"].get("note", ""))}</div>
        <div id="i1-by" class="mono" style="margin-top: 40px; padding-top: 18px; border-top: 1px solid #121212; width: 560px; font-size: 28px; color: #333; white-space: nowrap">{plain(c["name"])}</div></div>
      <div id="i1-vr" style="position: absolute; left: 1200px; top: 170px; width: 1px; height: 760px; background: #cfc9bb; transform-origin: 50% 0%"></div>
      <div id="i1-pl" style="position: absolute; left: 1260px; top: 170px; width: 540px; height: 660px; background: #efeadf; border: 1px solid #d8d3c7; display: flex; align-items: center; justify-content: center; overflow: hidden">{plate}</div>
      <div id="i1-cap" class="serif" style="position: absolute; left: 1260px; top: 850px; width: 540px; font-size: 28px; color: #4d4d4d; line-height: 1.45"><b class="acc" style="font-weight: 700">그림 1.</b> {capt}</div>
      {i_foot("i1", c, "발명의 명칭 · " + c.get("title", c["sub"]))}"""
    css = i_css()
    js = fjs + [up("#i1-k", 0.35),
                '    tl.fromTo("#i1-t", { opacity: 0.25, y: 24 }, { opacity: 1, y: 0, duration: 1.1, ease: "expo.out" }, 0.3);',
                up("#i1-s", 1.4), up("#i1-by", 2.0),
                '    tl.fromTo("#i1-vr", { scaleY: 0 }, { scaleY: 1, duration: 1.2, ease: "expo.out" }, 0.4);',
                '    tl.fromTo("#i1-pl", { opacity: 0, clipPath: "inset(0 0 100% 0)" }, { opacity: 1, clipPath: "inset(0 0 0% 0)", duration: 1.2, ease: "expo.out" }, 0.6);',
                draw("#i1-pl .ic", 1.0, 2.4, 0.1) if not figs else "", up("#i1-cap", 1.8),
                up("#i1-ft", 2.4),
                '    tl.fromTo("#i1-pl svg, #i1-pl img", { scale: 1 }, { scale: 1.06, duration: 8, ease: "none" }, 0);']
    return iscene("i1", css, body, "\n".join(js), enter=False)


def i2(c, pal, d):
    fr, fjs = i_frame("i2", c, "작동 원리")
    steps = c["process"]["steps"][:6]
    n = len(steps)
    rh = min(110, 560 / n)
    rows = "".join(f'<div class="tr" id="i2-r{i}" style="height: {rh:.0f}px"><span class="no serif">{i + 1}</span><span class="pg">{icon(step_icon(st["n"], c["hero"]), min(64, rh - 30), "#121212", 5)}</span><b>{E(st["n"])}</b>'
                   f'<span class="cv serif" style="font-size: {fit(st["big"] + st.get("u", ""), 44, 300)}px">{E(st["big"])}<small> {E(st.get("u", ""))}</small></span><span class="ds">{E(st["d"])}</span></div>'
                   for i, st in enumerate(steps))
    body = f"""{fr}
      <div style="position: absolute; left: 120px; top: 150px; width: 1680px">
        <div class="kick" id="i2-k">HOW IT WORKS</div>
        <div class="hd" id="i2-t" style="margin-top: 16px; font-size: {fit(plain(c["process"]["title"]), 64, 1680)}px">{accent(c["process"]["title"], "acc")}</div></div>
      <div style="position: absolute; left: 120px; top: 340px; width: 1680px">
        <div class="th mono" id="i2-h"><span>단계</span><span></span><span>공정</span><span>조건</span><span>내용</span></div>
        <div id="i2-hl" style="position: absolute; left: 0; right: 0; top: 64px; height: {rh:.0f}px; background: rgba(164, 22, 26, 0.07); opacity: 0" data-layout-ignore></div>
        {rows}</div>
      {i_foot("i2", c, c["process"].get("note", ""))}"""
    css = i_css() + f"""
    .th {{ display: grid; grid-template-columns: 120px 100px 400px 360px 1fr; height: 64px; align-items: center; font-size: 28px; color: #555; border-bottom: 2px solid #121212; }}
    .tr {{ position: relative; display: grid; grid-template-columns: 120px 100px 400px 360px 1fr; align-items: center; border-bottom: 1px solid #cfc9bb; }}
    .tr .no {{ font-size: 44px; font-weight: 700; color: {NEWS_RED}; padding-left: 14px; }}
    .tr b {{ font-size: 36px; font-weight: 800; letter-spacing: -0.03em; white-space: nowrap; }}
    .tr .cv {{ font-weight: 700; white-space: nowrap; }}
    .tr .cv small {{ font-size: 28px; color: #4d4d4d; font-weight: 400; }}
    .tr .ds {{ font-size: 30px; color: #4d4d4d; white-space: nowrap; }}"""
    T = [1.1 + i * (6.6 / n) for i in range(n)]
    js = fjs + [up("#i2-k", 0.3), up("#i2-t", 0.45), up("#i2-h", 0.8, 0, 0.6, 14), up("#i2-ft", 1.2)]
    for i, t in enumerate(T):
        js.append(f'    tl.fromTo("#i2-r{i}", {{ opacity: 0, x: -24 }}, {{ opacity: 1, x: 0, duration: 0.7, ease: "expo.out" }}, {t:.2f});')
        js.append(draw(f"#i2-r{i} .ic", t + 0.1, 0.9, 0.05))
        js.append(f'    tl.to("#i2-hl", {{ opacity: 1, y: {i * rh:.0f}, duration: 0.5, ease: "expo.inOut" }}, {t - 0.05:.2f});')
    return iscene("i2", css, body, "\n".join(js))


def _ticks(mx):
    """Three axis ticks (0, half, max) formatted with a sensible number of decimals."""
    dec = 0 if mx >= 10 else (1 if mx >= 1 else (2 if mx >= 0.1 else 3))
    return [f"{v:.{dec}f}" for v in (0, mx / 2, mx)]


def i3(c, pal, d):
    fr, fjs = i_frame("i3", c, "성과")
    pr = c["proof"]
    css = i_css() + f"""
    .blk {{ position: absolute; inset: 0; opacity: 0; }}
    .big {{ font-family: "SrcSerif", "NotoSerifKR", serif; font-weight: 700; letter-spacing: -0.03em; line-height: 1; white-space: nowrap; }}
    .big small {{ font-size: 0.38em; margin-left: 6px; color: {NEWS_RED}; }}
    .gl {{ position: absolute; top: 0; bottom: 0; width: 1px; background: #cfc9bb; }}
    .tk {{ position: absolute; top: -48px; width: 160px; margin-left: -80px; text-align: center; font-size: 28px; color: #555; }}
    .br {{ position: absolute; left: 0; height: 120px; }}
    .br .lb {{ position: absolute; right: calc(100% + 24px); top: 0; height: 120px; width: 270px; display: flex; align-items: center; justify-content: flex-end; text-align: right; font-size: 28px; font-weight: 600; line-height: 1.3; }}
    .br .fl {{ position: absolute; left: 0; top: 34px; height: 52px; background: #a9a296; transform-origin: 0% 50%; }}
    .br.hi .fl {{ background: {NEWS_RED}; }}
    .br .vl {{ position: absolute; top: 34px; height: 52px; display: flex; align-items: center; font-size: 30px; white-space: nowrap; }}
    .br.hi .vl {{ color: {NEWS_RED}; font-weight: 700; }}
    .lg {{ display: grid; grid-template-columns: 76px 1fr; align-items: center; border-top: 1px solid #cfc9bb; height: 100px; }}
    .lg b {{ font-family: "SrcSerif", "NotoSerifKR", serif; font-size: 40px; font-weight: 700; color: {NEWS_RED}; }}
    .lg .n {{ font-size: 34px; font-weight: 800; white-space: nowrap; }}
    .lg .s {{ font-size: 28px; color: #4d4d4d; white-space: nowrap; }}"""
    if pr.get("kind") == "anatomy":
        parts = "".join(f'<div class="lg" id="i3-p{i}"><b>{E(str(p["ref"])) if p.get("ref") else "•"}</b>'
                        f'<div><div class="n">{E(p["n"])}</div><div class="s">{E(p["d"])}</div></div></div>' for i, p in enumerate(pr["parts"][:6]))
        body = f"""{fr}
      <div id="i3-ph" style="position: absolute; left: 120px; top: 150px; width: 820px; height: 720px; background: #fff; border: 1px solid #d8d3c7; overflow: hidden">
        <img id="i3-img" src="assets/fig/{E(pr["figure"])}" alt="{E(pr.get("figcap", "도면"))}" style="position: absolute; inset: 30px; width: 760px; height: 660px; object-fit: contain" /></div>
      <div id="i3-cap" class="serif" style="position: absolute; left: 120px; top: 888px; width: 820px; font-size: 28px; color: #4d4d4d"><b class="acc">그림 2.</b> {E(pr.get("figcap", "대표 도면"))}</div>
      <div style="position: absolute; left: 1020px; top: 150px; width: 780px">
        <div class="kick" id="i3-k">ANATOMY</div>
        <div class="hd" id="i3-t" style="margin: 14px 0 30px; font-size: {fit(plain(pr.get("title", "핵심 구성")), 58, 780)}px">{accent(pr.get("title", "핵심 |구성"), "acc")}</div>{parts}</div>
      {i_foot("i3", c)}"""
        js = fjs + [pop("#i3-ph", 0.3), '    tl.fromTo("#i3-img", { scale: 1 }, { scale: 1.06, duration: 13, ease: "none" }, 0.4);', up("#i3-cap", 0.9),
                    up("#i3-k", 0.5), up("#i3-t", 0.65), up(".lg", 1.4, 0.7, 0.7, 24), up("#i3-ft", 1.0)]
        return iscene("i3", css, body, "\n".join(js))
    items, T = items_of(pr, d)
    blocks, js = "", list(fjs)
    for i, it in enumerate(items):
        big, u = it["big"], it.get("u", "")
        bars = (it.get("bars") or [])[:4]
        if bars:
            mx = it.get("max") or max(x["v"] for x in bars) * 1.15
            W = 470
            grid = "".join(f'<div class="gl" style="left: {W * f:.0f}px"></div><div class="tk mono" style="left: {W * f:.0f}px">{t}</div>'
                           for f, t in zip((0, 0.5, 1), _ticks(mx)))
            rows = ""
            for j, br in enumerate(bars):
                w = W * max(0.01, min(1, br["v"] / mx))
                rows += (f'<div class="br{" hi" if br.get("hi") else ""}" style="top: {j * 130:.0f}px; width: {W}px"><div class="lb">{E(br["l"])}</div>'
                         f'<div class="fl" id="i3-f{i}-{j}" style="width: {w:.0f}px"></div>'
                         f'<div class="vl mono" id="i3-v{i}-{j}" style="left: {w + 16:.0f}px">{E(br.get("t", ""))}{" ◀ 본 특허" if br.get("hi") else ""}</div></div>')
                js.append(f'    tl.fromTo("#i3-f{i}-{j}", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 1.3, ease: "expo.out" }}, {T[i] + 0.8 + j * 0.2:.2f});')
                js.append(f'    tl.fromTo("#i3-v{i}-{j}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.5 }}, {T[i] + 1.4 + j * 0.2:.2f});')
            right = (f'<div style="position: absolute; left: 1000px; top: 200px; width: 800px">'
                     f'<div style="font-size: 30px; font-weight: 800">{E(it["l"])}</div>'
                     f'<div style="font-size: 28px; color: #555; margin-top: 4px">항목별 비교 · 명세서 수치</div></div>'
                     f'<div style="position: absolute; left: 1290px; top: 400px; width: {W}px; height: {len(bars) * 130 - 10}px">{grid}{rows}</div>')
        else:
            right = (f'<div style="position: absolute; left: 1140px; top: 200px; width: 560px; height: 620px; background: #efeadf; border: 1px solid #d8d3c7; display: flex; align-items: center; justify-content: center">'
                     f'{icon(it.get("icon", c["hero"]), 300, "#121212", 2.6)}</div>')
            js.append(draw(f"#i3-k{i} .ic", T[i] + 0.4))
        blocks += f"""
      <div class="blk" id="i3-k{i}">
        <div style="position: absolute; left: 120px; top: 170px; width: 800px">
          <div class="kick">{E(pr.get("eyebrow", "PERFORMANCE"))} · {i + 1}/{len(items)}</div>
          <div class="big" style="margin-top: 36px; font-size: {fit(big + u, 210, 780)}px"><span id="i3-n{i}">{E(big)}</span><small>{E(u)}</small></div>
          <div style="margin-top: 36px; font-size: 52px; font-weight: 800; letter-spacing: -0.03em">{E(it["l"])}</div>
          <div class="dek" style="margin-top: 18px">{it.get("s", "")}</div></div>
        <div style="position: absolute; left: 960px; top: 170px; width: 1px; height: 760px; background: #cfc9bb"></div>{right}</div>"""
        swap(js, "i3", i, T)
        js.append(count(f"i3-n{i}", big, T[i] + 0.3))
    js.append(up("#i3-ft", 1.0))
    return iscene("i3", css, fr + blocks + i_foot("i3", c), "\n".join(x for x in js if x))


def i_fig(c, pal, d):
    fr, fjs = i_frame("if", c, "명세서 도면")
    figs = pick_figures(c, 4)
    figs = figs[1:] if len(figs) > 1 else figs
    css = i_css() + """
    .pl { position: absolute; background: #fff; border: 1px solid #d8d3c7; overflow: hidden; }
    .pl img { position: absolute; inset: 20px; width: calc(100% - 40px); height: calc(100% - 40px); object-fit: contain; }
    .cap { position: absolute; font-size: 28px; color: #4d4d4d; white-space: nowrap; }"""
    head = f"""
      <div style="position: absolute; left: 120px; top: 150px; width: 1680px">
        <div class="kick" id="if-k">{"FROM THE SPECIFICATION" if figs else "AT A GLANCE"}</div>
        <div class="hd" id="if-t" style="margin-top: 16px; font-size: 60px">{'명세서 <span class="acc">도면</span>으로 본 기술' if figs else '공정 <span class="acc">한눈에</span> 보기'}</div></div>"""
    if not figs:
        steps = c["process"]["steps"][:5]
        boxes = [(120 + i * (1680 / len(steps)), 330, 1680 / len(steps) - 24, 520) for i in range(len(steps))]
        plates = "".join(f'<div class="pl" id="if-p{i}" style="left: {x:.0f}px; top: {y}px; width: {w:.0f}px; height: {h}px; display: flex; align-items: center; justify-content: center">'
                         f'{icon(step_icon(st["n"], c["hero"]), min(220, w * 0.6), "#121212", 3)}</div>'
                         f'<div class="cap serif" style="left: {x:.0f}px; top: {y + h + 14}px"><b class="acc">{i + 1}.</b> {E(st["n"])}</div>' for i, (st, (x, y, w, h)) in enumerate(zip(steps, boxes)))
        js = fjs + [up("#if-k", 0.3), up("#if-t", 0.45), up(".pl", 0.8, 0.2, 0.8, 30), draw(".pl .ic", 1.0, 1.3, 0.03), up(".cap", 1.4, 0.2, 0.6, 14)]
        return iscene("if", css, fr + head + plates + i_foot("if", c), "\n".join(js))
    k = len(figs)
    if k == 1:
        boxes = [(360, 320, 1200, 560)]
    elif k == 2:
        boxes = [(120, 320, 820, 560), (980, 320, 820, 560)]
    else:
        boxes = [(120, 320, 1000, 600), (1180, 320, 620, 250), (1180, 670, 620, 250)]
    n0 = 2 if len(pick_figures(c, 4)) > 1 else 1
    plates = "".join(f'<div class="pl" id="if-p{i}" style="left: {x}px; top: {y}px; width: {w}px; height: {h}px"><img src="assets/fig/{E(f["file"])}" alt="그림 {n0 + i}" /></div>'
                     f'<div class="cap serif" id="if-c{i}" style="left: {x}px; top: {y + h + 12}px"><b class="acc">그림 {n0 + i}.</b> 명세서 도면 ({f["page"]}쪽)</div>'
                     for i, (f, (x, y, w, h)) in enumerate(zip(figs, boxes)))
    js = fjs + [up("#if-k", 0.3), up("#if-t", 0.45),
                '    tl.fromTo(".pl", { clipPath: "inset(0 0 100% 0)" }, { clipPath: "inset(0 0 0% 0)", duration: 1.0, ease: "expo.inOut", stagger: 0.45 }, 0.7);',
                f'    tl.fromTo(".pl img", {{ scale: 1.12, x: -16 }}, {{ scale: 1, x: 16, duration: {d - 0.7:.1f}, ease: "none" }}, 0.7);',
                up(".cap", 1.4, 0.45, 0.6, 14), up("#if-ft", 1.0)]
    return iscene("if", css, fr + head + plates + i_foot("if", c, f"출처: {c.get('patlabel', '등록특허')} 제{c['regno']}호 명세서"), "\n".join(js))


def i4(c, pal, d):
    fr, fjs = i_frame("i4", c, "특장점")
    f = c["features"]
    facts = "".join(f'<div class="fx" id="i4-f{i}"><b class="serif" style="font-size: {fit(t["v"], 64, 330)}px">{E(t["v"])}</b>'
                    f'<div><h5>{E(t["l"])}</h5><span>{E(t["s"])}</span></div></div>' for i, t in enumerate(f["tiles"][:6]))
    body = f"""{fr}
      <div style="position: absolute; left: 120px; top: 150px; width: 1680px">
        <div class="kick" id="i4-k">KEY FACTS</div>
        <div class="hd" id="i4-t" style="margin-top: 16px; font-size: {fit(plain(f.get("title", "핵심 특장점")), 64, 1680)}px">{accent(f.get("title", "핵심 |특장점"), "acc")}</div></div>
      <div style="position: absolute; left: 120px; top: 350px; width: 1680px; display: grid; grid-template-columns: 1fr 1fr; column-gap: 80px; border-top: 2px solid #121212">{facts}</div>
      {i_foot("i4", c)}"""
    css = i_css() + f"""
    .fx {{ display: grid; grid-template-columns: 360px 1fr; align-items: center; height: 180px; border-bottom: 1px solid #cfc9bb; }}
    .fx b {{ font-weight: 700; color: {NEWS_RED}; letter-spacing: -0.02em; white-space: nowrap; }}
    .fx h5 {{ font-size: 36px; font-weight: 800; letter-spacing: -0.03em; white-space: nowrap; }}
    .fx span {{ display: block; margin-top: 6px; font-size: 28px; color: #4d4d4d; white-space: nowrap; }}"""
    js = fjs + [up("#i4-k", 0.3), up("#i4-t", 0.45), up(".fx", 0.9, 0.3, 0.7, 24), up("#i4-ft", 1.0),
                '    tl.fromTo(".fx b", { x: 0 }, { x: 14, duration: 4.5, ease: "none" }, 2.5);']
    return iscene("i4", css, body, "\n".join(js))


def i5(c, pal, d):
    fr, fjs = i_frame("i5", c, "활용분야")
    apps = c["apps"][:5]
    rows = "".join(f'<div class="ix" id="i5-r{i}"><span class="no serif">{i + 1}</span><b>{E(ap["n"])}</b><i></i>'
                   f'<span class="ds">{oneline(ap["s"])}</span>' + ('<em class="mono">청구항</em>' if ap.get("claim") else '<em class="mono" style="opacity: 0">—</em>') + '</div>'
                   for i, ap in enumerate(apps))
    body = f"""{fr}
      <div style="position: absolute; left: 120px; top: 150px; width: 1680px">
        <div class="kick" id="i5-k">INDEX OF APPLICATIONS</div>
        <div class="hd" id="i5-t" style="margin-top: 16px; font-size: 64px">기술이전 시 <span class="acc">활용분야</span></div></div>
      <div style="position: absolute; left: 120px; top: 360px; width: 1680px; border-top: 2px solid #121212">{rows}</div>
      {i_foot("i5", c, "※ 청구항: 등록 청구범위에 명시된 용도")}"""
    css = i_css() + f"""
    .ix {{ display: flex; align-items: center; gap: 28px; height: 118px; border-bottom: 1px solid #cfc9bb; white-space: nowrap; }}
    .ix .no {{ width: 60px; font-size: 44px; font-weight: 700; color: {NEWS_RED}; text-align: center; }}
    .ix b {{ font-size: 40px; font-weight: 800; letter-spacing: -0.03em; }}
    .ix i {{ flex: 1; height: 0; border-bottom: 3px dotted #a9a296; transform-origin: 0% 50%; }}
    .ix .ds {{ font-size: 30px; color: #4d4d4d; }}
    .ix em {{ font-style: normal; width: 130px; text-align: center; font-size: 28px; color: {NEWS_RED}; border: 2px solid {NEWS_RED}; padding: 4px 0; }}"""
    js = fjs + [up("#i5-k", 0.3), up("#i5-t", 0.45), up(".ix", 0.9, 0.3, 0.7, 20),
                '    tl.fromTo(".ix i", { scaleX: 0 }, { scaleX: 1, duration: 0.8, ease: "expo.out", stagger: 0.3 }, 1.1);', up("#i5-ft", 1.0),
                '    tl.fromTo(".ix .no", { scale: 1 }, { scale: 1.12, duration: 0.5, ease: "sine.inOut", stagger: 0.6, yoyo: true, repeat: 1 }, 3.0);']
    return iscene("i5", css, body, "\n".join(js))


def i6(c, pal, d):
    name = plain(c["name"])
    cells = [("기술이전 문의", CONTACT), (c.get("patlabel", "등록특허"), c["regno"])]
    ch = "".join(f'<div class="cc" id="i6-c{i}"><span>{E(k)}</span><b>{E(v)}</b></div>' for i, (k, v) in enumerate(cells))
    body = f"""
      <div id="i6-top" style="position: absolute; left: 260px; right: 260px; top: 170px; height: 9px; border-top: 4px solid #121212; border-bottom: 1px solid #121212; transform-origin: 50% 50%"></div>
      <div style="position: absolute; left: 0; right: 0; top: 220px; text-align: center">
        <div class="kick" id="i6-k">{E(c["institute"])}</div>
        <div id="i6-n" class="serif" style="display: inline-block; margin-top: 20px; font-size: {fit(name, 120, 1300)}px; font-weight: 700; letter-spacing: -0.02em; white-space: nowrap">{name}</div>
        <div id="i6-s" class="serif" style="margin-top: 6px; font-size: 44px; font-weight: 600">{E(c["sub"])}</div></div>
      <div style="position: absolute; left: 260px; right: 260px; top: 560px; display: grid; grid-template-columns: repeat(2, 1fr); border-top: 1px solid #121212; border-bottom: 1px solid #121212">{ch}</div>
      <div id="i6-m" style="position: absolute; left: 0; right: 0; top: 790px; text-align: center; font-size: 30px; font-weight: 600; color: #4d4d4d">특허권자 대한민국 ({E(c["institute"])})</div>
      <div id="i6-d" style="position: absolute; left: 200px; right: 200px; top: 850px; text-align: center; font-size: 28px; color: #555; line-height: 1.5">{DISCLAIMER}</div>"""
    css = i_css() + """
    .cc { padding: 30px 0 34px; text-align: center; border-right: 1px solid #cfc9bb; }
    .cc:last-child { border: 0; }
    .cc span { display: block; font-size: 28px; color: #555; }
    .cc b { display: block; margin-top: 10px; font-size: 44px; font-weight: 800; letter-spacing: -0.03em; white-space: nowrap; }"""
    js = "\n".join(['    tl.fromTo("#i6-top", { scaleX: 0 }, { scaleX: 1, duration: 1.0, ease: "expo.out" }, 0.1);', up("#i6-k", 0.4),
                    '    tl.fromTo("#i6-n", { opacity: 0.2, y: 24 }, { opacity: 1, y: 0, duration: 1.1, ease: "expo.out" }, 0.5);',
                    up("#i6-s", 1.0), up(".cc", 1.4, 0.2, 0.7, 20), up("#i6-m", 2.0), up("#i6-d", 2.3)])
    return iscene("i6", css, body, js)


build_def.TEMPLATES.update({
    "G": (1920, 1080, 60.0, G_SLOTS, {"g1-open": g1, "g2-brief": g2, "g3-steps": g3, "g4-proof": g4, "gf-figures": gf, "g5-grid": g5, "g6-uses": g6, "g7-end": g7}, "#f3f3f1"),
    "H": (1920, 1080, 57.5, H_SLOTS, {"h1-open": h1, "h2-wave": h2, "h3-proof": h3, "hf-figures": hf, "h4-cards": h4, "h5-network": h5, "h6-end": h6}, "#ebe6dd"),
    "I": (1920, 1080, 56.0, I_SLOTS, {"i1-front": i1, "i2-how": i2, "i3-chart": i3, "if-figures": i_fig, "i4-facts": i4, "i5-index": i5, "i6-colophon": i6}, "#f7f4ec"),
})


def build(tpl, path):
    tpl = tpl.upper()
    out = build_def.build(tpl, path)
    c = json.load(open(path, encoding="utf-8"))
    copy_figures(c, out)
    w, h, total, slots, _, _ = build_def.TEMPLATES[tpl]
    core, _, node = h_cols(c)
    add_transitions(out, tpl, slots, total, w, h, (core, node))
    return out  # fonts (incl. the I serif, from assets/fonts_serif) are subset in by postprocess.run


if __name__ == "__main__":
    import postprocess
    for p in sys.argv[2:]:
        postprocess.run(build(sys.argv[1], p))
