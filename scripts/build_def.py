"""Templates D, E, F — redesigned from the user's reference films (attached zip), driven by the same content JSON.

D  Green-editorial   16:9, 60 s  mist ground + glass cards, sentence headlines, dark interludes (ref: patent-video skill)
E  Mono-contrast     16:9, 56.5 s  black / white / navy-grid scenes, centred Apple narrative, gradient hero number (ref: seed-film)
F  Vertical punch    9:16, 40.5 s  black / navy / white statement screens with one UI card each (ref: AgriIPSummary short)

Usage: python -I tools/build_def.py D|E|F data/content/<order>-<appno>.json [...]
"""
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import CONTACT, DISCLAIMER, E, MUSIC, PALETTES, ROOT, fit, rgba  # noqa: E402
from icons import icon  # noqa: E402
from visuals import add_transitions, copy_figures, fig_boxes, pick_figures, step_icon  # noqa: E402

FONT = """    @font-face { font-family: "Pretendard"; src: url("assets/fonts/pretendard/Pretendard-Medium.woff2") format("woff2"); font-weight: 500; }
    @font-face { font-family: "Pretendard"; src: url("assets/fonts/pretendard/Pretendard-SemiBold.woff2") format("woff2"); font-weight: 600; }
    @font-face { font-family: "Pretendard"; src: url("assets/fonts/pretendard/Pretendard-Bold.woff2") format("woff2"); font-weight: 700; }
    @font-face { font-family: "Pretendard"; src: url("assets/fonts/pretendard/Pretendard-ExtraBold.woff2") format("woff2"); font-weight: 800; }"""


def darken(hexc, f):
    h = hexc.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % (int(r * (1 - f)), int(g * (1 - f)), int(b * (1 - f)))


def grad_text(s, cls="gr"):
    """'plain|accent' -> html with the accent part in the gradient class."""
    if "|" in s:
        p, g = s.split("|", 1)
        return f'{E(p)}<span class="{cls}">{E(g)}</span>'
    return E(s)


def plain(s):
    return E(s.replace("|", ""))


def num_parts(big):
    """Return (prefix, number, decimals, suffix) when big is a plain number, else None."""
    m = re.fullmatch(r"([^0-9]*)([0-9][0-9,]*(?:\.[0-9]+)?)(.*)", big)
    if not m or any(ch.isdigit() for ch in m.group(3)):
        return None
    n = m.group(2).replace(",", "")
    return m.group(1), float(n), (len(n.split(".")[1]) if "." in n else 0), m.group(3)


def scene(sid, w, h, css, body, js, bg_cls, enter=True):
    return f"""<template>
  <style>
{FONT}
    #root {{ position: absolute; inset: 0; overflow: hidden; font-family: "Pretendard", "Outfit", sans-serif; word-break: keep-all; -webkit-font-smoothing: antialiased; }}
    #{sid}-in {{ position: absolute; inset: 0; }}
{css}
  </style>
  <div id="root" data-composition-id="{sid}" data-width="{w}" data-height="{h}">
    <div id="{sid}-in" class="{bg_cls}">{body}</div>
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    {f'tl.fromTo("#{sid}-in", {{ opacity: 0, filter: "blur(10px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.7, ease: "power2.out" }}, 0);' if enter else ""}
{js}
    window.__timelines["{sid}"] = tl;
  </script>
</template>
"""


def up(sel, t, stagger=0.0, d=0.9, dist=40):
    return (f'    tl.fromTo("{sel}", {{ opacity: 0, y: {dist} }}, {{ opacity: 1, y: 0, duration: {d}, ease: "expo.out"'
            + (f", stagger: {stagger}" if stagger else "") + f" }}, {t:.2f});")


def pop(sel, t, stagger=0.0):
    return (f'    tl.fromTo("{sel}", {{ opacity: 0, scale: 0.88 }}, {{ opacity: 1, scale: 1, duration: 0.7, ease: "expo.out"'
            + (f", stagger: {stagger}" if stagger else "") + f" }}, {t:.2f});")


def blurin(sel, t, d=1.2):
    return (f'    tl.fromTo("{sel}", {{ opacity: 0, filter: "blur(24px)", scale: 1.05 }}, '
            f'{{ opacity: 1, filter: "blur(0px)", scale: 1, duration: {d}, ease: "expo.out" }}, {t:.2f});')


def count(sel_id, big, t, d=1.4):
    np_ = num_parts(big)
    if not np_:
        return ""
    pre, val, dec, suf = np_
    return (f'    (() => {{ const el = document.querySelector("#{sel_id}"); const o = {{ v: 0 }}; '
            f'tl.to(o, {{ v: {val}, duration: {d}, ease: "power2.out", onUpdate: () => {{ el.textContent = "{E(pre)}" + o.v.toFixed({dec}) + "{E(suf)}"; }} }}, {t:.2f}); }})();')


def grad_defs(gid, a, b):
    return (f'<svg width="0" height="0" style="position: absolute" data-layout-ignore><defs><linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="{a}" /><stop offset="1" stop-color="{b}" /></linearGradient></defs></svg>')


# ======================================================================= D
D_SLOTS = [("d1", "d1-hero", 0.0, 6.5), ("d2", "d2-split", 6.0, 7.0), ("d3", "d3-timeline", 12.5, 9.5),
           ("d4", "d4-results", 21.5, 12.5), ("df", "df-figures", 33.5, 7.0), ("d5", "d5-tiles", 40.0, 7.0),
           ("d6", "d6-uses", 46.5, 7.0), ("d7", "d7-end", 53.0, 7.0)]


def d_css(pal):
    a1, a2, a3 = pal
    ae = darken(a2, 0.38)
    return f"""    .light {{ background: radial-gradient(1200px 700px at 85% 0%, rgba(120, 196, 156, 0.30), transparent 60%), radial-gradient(900px 600px at 0% 100%, {rgba(a3, 0.10)}, transparent 60%), #eef5f0; color: #13261c; }}
    .dark {{ background: radial-gradient(1100px 700px at 70% 20%, rgba(76, 168, 118, 0.30), transparent 60%), radial-gradient(800px 600px at 10% 100%, {rgba(a2, 0.12)}, transparent 65%), #08190f; color: #eef6f1; }}
    .gr {{ background: linear-gradient(100deg, {a1}, {a2} 55%, {a3}); -webkit-background-clip: text; background-clip: text; color: transparent; padding: 0 0.1em 0.08em 0.02em; margin: 0 -0.1em -0.08em -0.02em; }}
    .light .gr {{ background: linear-gradient(100deg, {darken(a1, 0.25)}, {darken(a2, 0.25)} 55%, {darken(a3, 0.2)}); -webkit-background-clip: text; background-clip: text; }}
    .eye {{ font-size: 30px; font-weight: 700; color: {ae}; }}
    .dark .eye {{ color: {a1}; }}
    .sub {{ font-size: 36px; font-weight: 500; color: #5d6862; line-height: 1.5; letter-spacing: -0.02em; }}
    .dark .sub {{ color: #a9b8ad; }}
    .card {{ background: rgba(255, 255, 255, 0.88); border: 1px solid rgba(255, 255, 255, 0.95); border-radius: 34px; box-shadow: 0 30px 80px rgba(20, 60, 30, 0.10); }}
    .h {{ font-weight: 700; letter-spacing: -0.035em; line-height: 1.14; }}
    .foot2 {{ position: absolute; left: 160px; bottom: 44px; font-size: 28px; color: #6b7570; }}
    .dark .foot2 {{ color: #8fa093; }}
    .ic {{ display: flex; align-items: center; justify-content: center; background: {rgba(a2, 0.16)}; }}
    .dark .ic {{ background: rgba(255, 255, 255, 0.06); border: 1px solid rgba(255, 255, 255, 0.14); }}"""


def d1(c, pal, d):
    a1, a2, a3 = pal
    body = f"""{grad_defs("d1-lg", a1, a3)}
      <div id="d1-art" style="position: absolute; left: 1180px; top: 190px" data-layout-ignore>{icon(c["hero"], 640, "url(#d1-lg)", 2.2)}</div>
      <div style="position: absolute; left: 160px; top: 230px; width: 1060px">
        <div class="eye" id="d1-e">{E(c["institute"])}</div>
        <div class="h" id="d1-t" style="margin-top: 26px; font-size: 112px; color: #fff">{E(c["sub"])}</div>
        <div class="sub" id="d1-b" style="margin-top: 34px">{plain(c["headline"])}</div>
        <div id="d1-chips" style="display: flex; gap: 16px; margin-top: 44px">
          <span class="chip">{E(c.get("patlabel", "등록특허"))} {E(c["regno"])}</span><span class="chip gname">{plain(c["name"])}</span></div>
      </div>"""
    css = d_css(pal) + f"""
    .chip {{ font-size: 28px; font-weight: 600; padding: 14px 26px; border-radius: 30px; background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.16); color: #e9f0ea; }}
    .gname {{ color: {a1}; font-family: Outfit, Pretendard; font-weight: 800; letter-spacing: 0.02em; }}"""
    js = "\n".join(['    tl.fromTo("#d1-art", { opacity: 0.35, filter: "blur(18px)" }, { opacity: 1, filter: "blur(0px)", duration: 1.8, ease: "expo.out" }, 0);', '    tl.fromTo("#d1-art .ic", { strokeDasharray: 1, strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 2.2, ease: "power2.inOut", stagger: 0.12 }, 0.2);',
                    '    tl.fromTo("#d1-art", { scale: 1.08 }, { scale: 1, duration: 6.5, ease: "none" }, 0);',
                    up("#d1-e", 0.3), '    tl.fromTo("#d1-t", { opacity: 0.35, filter: "blur(12px)" }, { opacity: 1, filter: "blur(0px)", duration: 1.2, ease: "expo.out" }, 0.1);', up("#d1-b", 1.6), up("#d1-chips .chip", 2.2, 0.15)])
    return scene("d1", 1920, 1080, css, body, js, "dark", enter=False)


def d2(c, pal, d):
    rows = "".join(f'<div class="row" id="d2-r{i}"><div class="ic" style="width: 72px; height: 72px; border-radius: 22px">{icon(c["hero"], 44, "url(#d2-lg)", 6)}</div>'
                   f'<div><b>{E(ch["v"])}<em>{E(ch.get("u", ""))}</em></b><small>{E(ch["k"])}</small></div></div>' for i, ch in enumerate(c["chips"][:4]))
    a1, a2, a3 = pal
    body = f"""{grad_defs("d2-lg", darken(a1, 0.3), darken(a3, 0.2))}
      <div style="position: absolute; left: 160px; top: 250px; width: 760px">
        <div class="eye" id="d2-e">발명 개요</div>
        <div class="h" id="d2-t" style="margin-top: 22px; font-size: 80px">{grad_text(c["headline"])}</div>
        <div class="sub" id="d2-b" style="margin-top: 30px">{E(c["process"].get("note", ""))}</div>
      </div>
      <div class="card" id="d2-card" style="position: absolute; left: 1010px; top: 200px; width: 750px; padding: 44px 50px">
        <div style="font-size: 30px; font-weight: 700; color: #5d6862; margin-bottom: 8px">핵심 사양</div>{rows}</div>"""
    css = d_css(pal) + """
    .row { display: flex; align-items: center; gap: 24px; padding: 22px 0; border-bottom: 1px solid #e3e8e1; }
    .row:last-child { border: 0; }
    .row b { display: block; font-size: 46px; font-weight: 800; letter-spacing: -0.03em; white-space: nowrap; }
    .row b em { font-style: normal; font-size: 28px; font-weight: 600; margin-left: 6px; color: #5d6862; }
    .row small { display: block; font-size: 28px; color: #5d6862; font-weight: 600; margin-top: 2px; }"""
    js = "\n".join([up("#d2-e", 0.3), up("#d2-t", 0.45), up("#d2-b", 1.1), pop("#d2-card", 0.6), up(".row", 1.1, 0.3, 0.7, 24), '    tl.to("#d2-in", { scale: 1.025, duration: 6.5, ease: "none" }, 1);'])
    return scene("d2", 1920, 1080, css, body, js, "light")


def d3(c, pal, d):
    steps = c["process"]["steps"][:6]
    n = len(steps)
    span = 1640 / n
    nodes = "".join(f'<div class="tn{" k" if i == n - 1 else ""}" id="d3-n{i}" style="left: {span * (i + 0.5):.0f}px; width: {span - 20:.0f}px; margin-left: -{(span - 20) / 2:.0f}px">'
                    f'<div class="y">{E(st["big"])}<small>{E(st.get("u", ""))}</small></div><div class="dt">{icon(step_icon(st["n"], c["hero"]), 40, "currentColor", 6)}</div>'
                    f'<div class="tt">{E(st["n"])}</div><div class="dd">{E(st["d"])}</div></div>'
                    for i, st in enumerate(steps))
    a1, a2, _ = pal
    body = f"""
      <div style="position: absolute; left: 0; right: 0; top: 150px; text-align: center">
        <div class="eye" id="d3-e">기술 핵심</div>
        <div class="h" id="d3-t" style="margin-top: 20px; font-size: 76px; color: #fff">{grad_text(c["process"]["title"])}</div>
      </div>
      <div style="position: absolute; left: 140px; top: 470px; width: 1640px; height: 420px">
        <div class="ln"><i id="d3-fill"></i></div>{nodes}</div>"""
    css = d_css(pal) + f"""
    .ln {{ position: absolute; left: 0; right: 0; top: 128px; height: 4px; border-radius: 2px; background: rgba(255, 255, 255, 0.12); overflow: hidden; }}
    .ln i {{ position: absolute; inset: 0; background: linear-gradient(90deg, {a1}, {a2}); transform-origin: 0% 50%; transform: scaleX(0); }}
    .tn {{ position: absolute; top: 0; text-align: center; }}
    .tn .y {{ height: 80px; font-family: Outfit, Pretendard; font-size: {fit(max((s["big"] for s in steps), key=len), 46, max(160, span - 40))}px; font-weight: 800; color: {a1}; white-space: nowrap; }}
    .tn .y small {{ font-size: 28px; margin-left: 4px; }}
    .tn .dt {{ width: 76px; height: 76px; border-radius: 50%; margin: 8px auto 0; background: #0c2216; border: 4px solid {a1}; color: {a1}; display: flex; align-items: center; justify-content: center; }}
    .tn.k .dt {{ background: {a1}; color: #08190f; box-shadow: 0 0 30px {a1}; }}
    .tn .tt {{ font-size: 34px; font-weight: 700; margin-top: 22px; letter-spacing: -0.03em; color: #fff; }}
    .tn .dd {{ font-size: 28px; color: #a9b8ad; margin-top: 12px; line-height: 1.45; }}"""
    T = [1.0 + i * (6.6 / n) for i in range(n)]
    js = [up("#d3-e", 0.3), up("#d3-t", 0.45), f'    tl.fromTo("#d3-fill", {{ scaleX: 0 }}, {{ scaleX: 1, duration: {T[-1] - 0.6:.2f}, ease: "none" }}, 0.9);']
    js += [up(f"#d3-n{i}", t, 0, 0.8, 30) for i, t in enumerate(T)]
    js += [f'    tl.fromTo("#d3-n{i} .ic", {{ strokeDasharray: 1, strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: 0.8, ease: "power2.out", stagger: 0.05 }}, {t + 0.15:.2f});' for i, t in enumerate(T)]
    return scene("d3", 1920, 1080, css, body, "\n".join(js), "dark")


def d4(c, pal, d):
    a1, a2, a3 = pal
    pr = c["proof"]
    css = d_css(pal) + f"""
    .bigstat {{ font-family: Outfit, Pretendard; font-size: 150px; font-weight: 800; letter-spacing: -0.05em; line-height: 1; white-space: nowrap; }}
    .crow {{ display: grid; grid-template-columns: 250px 1fr 170px; align-items: center; gap: 26px; margin: 22px 0; }}
    .crow .nm {{ font-size: 30px; font-weight: 700; letter-spacing: -0.02em; }}
    .crow .bar {{ height: 54px; border-radius: 16px; background: #eef2ec; position: relative; overflow: hidden; }}
    .crow .bar i {{ position: absolute; left: 0; top: 0; bottom: 0; width: 100%; border-radius: 16px; transform-origin: 0% 50%; transform: scaleX(0); background: #c9d3c6; }}
    .crow.hi .bar i {{ background: linear-gradient(90deg, {a1}, {a2}); }}
    .crow .v {{ font-family: Outfit, Pretendard; font-size: 44px; font-weight: 800; text-align: right; white-space: nowrap; }}
    .pl {{ display: flex; align-items: center; gap: 22px; padding: 18px 0; border-bottom: 1px solid #e3e8e1; }}
    .pl b {{ min-width: 64px; height: 56px; padding: 0 12px; border-radius: 28px; background: {darken(a2, 0.3)}; color: #fff; font-size: 28px; text-align: center; line-height: 56px; }}
    .pl b.dot {{ min-width: 20px; width: 20px; height: 20px; padding: 0; margin: 0 22px; background: linear-gradient(135deg, {a1}, {a3}); }}
    .pl .n {{ font-size: 36px; font-weight: 700; white-space: nowrap; }}
    .pl .s {{ font-size: 28px; color: #5d6862; white-space: nowrap; }}"""
    if pr.get("kind") == "anatomy":
        parts = "".join(f'<div class="pl" id="d4-p{i}">' + (f'<b>{E(str(p["ref"]))}</b>' if p.get("ref") else '<b class="dot"></b>')
                        + f'<div><div class="n">{E(p["n"])}</div><div class="s">{E(p["d"])}</div></div></div>' for i, p in enumerate(pr["parts"][:6]))
        body = f"""
      <div class="card" id="d4-ph" style="position: absolute; left: 140px; top: 140px; width: 760px; height: 800px; overflow: hidden; background: #fff">
        <img id="d4-img" src="assets/fig/{E(pr["figure"])}" alt="{E(pr.get("figcap", "도면"))}" style="position: absolute; left: 30px; top: 60px; width: 700px; height: 700px; object-fit: contain" />
        <div style="position: absolute; left: 30px; top: 26px; font-size: 28px; font-weight: 700; color: #5d6862">{E(pr.get("figcap", "대표 도면"))}</div></div>
      <div style="position: absolute; left: 990px; top: 150px; width: 800px">
        <div class="eye" id="d4-e">{E(pr.get("eyebrow", "ANATOMY"))}</div>
        <div class="h" id="d4-t" style="margin-top: 18px; font-size: 66px">{grad_text(pr.get("title", "핵심 |구성"))}</div>
        <div style="margin-top: 26px">{parts}</div></div>
      <div class="foot2" style="left: 990px">{E(c.get("source", ""))}</div>"""
        js = [pop("#d4-ph", 0.3), '    tl.fromTo("#d4-img", { scale: 1 }, { scale: 1.07, duration: 13, ease: "none" }, 0.4);',
              up("#d4-e", 0.5), up("#d4-t", 0.65), up(".pl", 1.4, 0.7, 0.7, 24)]
        return scene("d4", 1920, 1080, css, body, "\n".join(js), "light")
    items = pr["items"][:3]
    k = len(items)
    span = (d - 0.6) / k
    T = [round(0.4 + i * span, 2) for i in range(k)]
    blocks, js = "", []
    for i, it in enumerate(items):
        big = it["big"]
        bars = it.get("bars") or []
        if bars:
            mx = it.get("max") or max(x["v"] for x in bars) * 1.15
            rows = "".join(f'<div class="crow{" hi" if br.get("hi") else ""}"><div class="nm">{E(br["l"])}</div><div class="bar"><i id="d4-f{i}-{j}"></i></div><div class="v">{E(br.get("t", ""))}</div></div>'
                           for j, br in enumerate(bars[:4]))
            right = f'<div class="card" style="position: absolute; left: 980px; top: 230px; width: 800px; padding: 44px 50px">{rows}</div>'
            js += [f'    tl.fromTo("#d4-f{i}-{j}", {{ scaleX: 0 }}, {{ scaleX: {max(0.01, min(1, br["v"] / mx)):.4f}, duration: 1.4, ease: "expo.out" }}, {T[i] + 0.8 + j * 0.2:.2f});'
                   for j, br in enumerate(bars[:4])]
        else:
            right = f'<div class="card" style="position: absolute; left: 1080px; top: 250px; width: 600px; height: 560px; display: flex; align-items: center; justify-content: center">{icon(it.get("icon", c["hero"]), 320, "url(#d4-lg)", 3)}</div>'
        blocks += f"""
      <div class="blk" id="d4-k{i}">
        <div style="position: absolute; left: 160px; top: 230px; width: 760px">
          <div class="eye">{E(pr.get("eyebrow", "PERFORMANCE"))}</div>
          <div class="bigstat gr" style="margin-top: 18px; font-size: {fit(big + it.get("u", ""), 150, 760)}px"><span id="d4-n{i}">{E(big)}</span><span style="font-size: 0.4em">{E(it.get("u", ""))}</span></div>
          <div class="h" style="margin-top: 26px; font-size: 64px">{E(it["l"])}</div>
          <div class="sub" style="margin-top: 22px">{it.get("s", "")}</div>
        </div>{right}</div>"""
        if i > 0:
            js.append(f'    tl.to("#d4-k{i - 1}", {{ opacity: 0, duration: 0.4, ease: "power2.in" }}, {T[i] - 0.4:.2f});')
        js.append(f'    tl.fromTo("#d4-k{i}", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.8, ease: "expo.out" }}, {T[i]:.2f});')
        js.append(count(f"d4-n{i}", big, T[i] + 0.3))
        js.append(f'    tl.fromTo("#d4-k{i} .ic", {{ strokeDasharray: 1, strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: 1.4, ease: "power2.inOut" }}, {T[i] + 0.4:.2f});' if not bars else "")
    body = f"""{grad_defs("d4-lg", darken(a1, 0.3), darken(a3, 0.2))}{blocks}<div class="foot2">{E(c.get("source", ""))}</div>"""
    css += "\n    .blk { position: absolute; inset: 0; opacity: 0; }"
    return scene("d4", 1920, 1080, css, body, "\n".join(x for x in js if x), "light")


def df(c, pal, d):
    """Spec figures on mint glass cards; the card in focus lifts, the rest stay quiet. Steps as pictogram cards without figures."""
    a1, a2, a3 = pal
    figs = pick_figures(c, 4)
    boxes = fig_boxes(len(figs) or min(4, len(c["process"]["steps"])), 150, 340, 1620, 600, 26)
    if figs:
        cells = "".join(f'<div class="fg card" id="df-c{i}" style="left: {x:.0f}px; top: {y:.0f}px; width: {w:.0f}px; height: {h:.0f}px">'
                        f'<div class="im"><img src="assets/fig/{E(f["file"])}" alt="명세서 도면 {i + 1}" /></div><div class="cp"><b>도면 {i + 1}</b> · 명세서 {f["page"]}쪽</div></div>'
                        for i, (f, (x, y, w, h)) in enumerate(zip(figs, boxes)))
    else:
        cells = "".join(f'<div class="fg card" id="df-c{i}" style="left: {x:.0f}px; top: {y:.0f}px; width: {w:.0f}px; height: {h:.0f}px">'
                        f'<div class="im" style="display: flex; align-items: center; justify-content: center">{icon(step_icon(st["n"], c["hero"]), min(200, w * 0.5), "url(#df-lg)", 3)}</div>'
                        f'<div class="cp"><b>0{i + 1}</b> · {E(st["n"])}</div></div>' for i, (st, (x, y, w, h)) in enumerate(zip(c["process"]["steps"], boxes)))
    body = f"""{grad_defs("df-lg", darken(a1, 0.3), darken(a3, 0.2))}
      <div style="position: absolute; left: 0; right: 0; top: 140px; text-align: center">
        <div class="eye" id="df-e">{"FROM THE SPECIFICATION" if figs else "AT A GLANCE"}</div>
        <div class="h" id="df-t" style="margin-top: 18px; font-size: 72px">{'명세서 <span class="gr">도면</span>으로 보는 기술' if figs else '공정 <span class="gr">한눈에</span> 보기'}</div></div>{cells}"""
    css = d_css(pal) + """
    .fg { position: absolute; border-radius: 30px; }
    .fg .im { position: absolute; left: 18px; right: 18px; top: 18px; bottom: 66px; border-radius: 20px; background: #fff; overflow: hidden; }
    .fg img { position: absolute; inset: 12px; width: calc(100% - 24px); height: calc(100% - 24px); object-fit: contain; }
    .fg .cp { position: absolute; left: 28px; bottom: 18px; font-size: 28px; font-weight: 600; color: #4f5b55; white-space: nowrap; }
    .fg .cp b { color: #13261c; }"""
    k = len(boxes)
    step = (d - 2.6) / k
    js = [up("#df-e", 0.3), up("#df-t", 0.45), up(".fg", 0.8, 0.18, 0.9, 40),
          f'    tl.fromTo(".fg img", {{ scale: 1.1 }}, {{ scale: 1, duration: {d - 0.8:.1f}, ease: "power1.out" }}, 0.8);',
          '    tl.fromTo(".fg .ic", { strokeDasharray: 1, strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 1.2, ease: "power2.inOut", stagger: 0.04 }, 1.0);']
    for i in range(k):
        t = 1.9 + i * step
        js.append(f'    tl.to("#df-c{i}", {{ y: -16, boxShadow: "0 50px 110px rgba(20, 60, 30, 0.22)", duration: 0.5, ease: "expo.out" }}, {t:.2f});')
        if i < k - 1:
            js.append(f'    tl.to("#df-c{i}", {{ y: 0, boxShadow: "0 30px 80px rgba(20, 60, 30, 0.10)", duration: 0.5, ease: "expo.inOut" }}, {t + step - 0.05:.2f});')
    return scene("df", 1920, 1080, css, body, "\n".join(js), "light")


def d5(c, pal, d):
    f = c["features"]
    tiles = "".join(f'<div class="tile card" id="d5-t{i}"><small>{E(t["l"])}</small><b class="gr" style="font-size: {fit(t["v"], 60, 440)}px">{E(t["v"])}</b><span>{E(t["s"])}</span></div>'
                    for i, t in enumerate(f["tiles"][:6]))
    body = f"""
      <div style="position: absolute; left: 0; right: 0; top: 140px; text-align: center">
        <div class="eye" id="d5-e">HIGHLIGHTS</div>
        <div class="h" id="d5-t" style="margin-top: 18px; font-size: 76px">{grad_text(f.get("title", "핵심 |특장점"))}</div></div>
      <div style="position: absolute; left: 150px; top: 390px; width: 1620px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 26px">{tiles}</div>"""
    css = d_css(pal) + """
    .tile { padding: 34px 38px; border-radius: 30px; }
    .tile small { display: block; font-size: 30px; color: #5d6862; font-weight: 700; }
    .tile b { display: block; margin-top: 10px; font-family: Outfit, Pretendard; font-weight: 800; letter-spacing: -0.04em; white-space: nowrap; }
    .tile span { display: block; font-size: 28px; color: #5d6862; margin-top: 8px; white-space: nowrap; }"""
    js = "\n".join([up("#d5-e", 0.3), up("#d5-t", 0.45), up(".tile", 0.9, 0.22, 0.8, 30), '    tl.to("#d5-in", { scale: 1.02, duration: 6, ease: "none" }, 1);'])
    return scene("d5", 1920, 1080, css, body, js, "light")


def d6(c, pal, d):
    a1, a2, a3 = pal
    apps = c["apps"][:5]
    cards = "".join(f'<div class="uc card" id="d6-c{i}"><div class="ic" style="width: 96px; height: 96px; border-radius: 28px">{icon(ap["icon"], 58, "url(#d6-lg)", 5)}</div>'
                    f'<h4>{E(ap["n"])}</h4><p>{ap["s"]}</p>' + ('<em>특허 청구항</em>' if ap.get("claim") else "") + '</div>' for i, ap in enumerate(apps))
    body = f"""{grad_defs("d6-lg", darken(a1, 0.3), darken(a3, 0.2))}
      <div style="position: absolute; left: 0; right: 0; top: 140px; text-align: center">
        <div class="eye" id="d6-e">활용 분야</div>
        <div class="h" id="d6-t" style="margin-top: 18px; font-size: 76px">기술이전 시 <span class="gr">활용분야</span></div></div>
      <div style="position: absolute; left: 150px; top: 380px; width: 1620px; display: grid; grid-template-columns: repeat({len(apps)}, 1fr); gap: 24px">{cards}</div>"""
    css = d_css(pal) + f"""
    .uc {{ padding: 40px 34px; min-height: 440px; position: relative; }}
    .uc h4 {{ font-size: 38px; font-weight: 700; letter-spacing: -0.03em; margin-top: 30px; white-space: nowrap; }}
    .uc p {{ font-size: 28px; color: #5d6862; line-height: 1.5; margin-top: 14px; }}
    .uc em {{ position: absolute; left: 34px; bottom: 32px; font-style: normal; font-size: 28px; font-weight: 700; color: {darken(a2, 0.38)}; }}"""
    js = "\n".join([up("#d6-e", 0.3), up("#d6-t", 0.45), up(".uc", 0.9, 0.25, 0.8, 30),
                    '    tl.fromTo(".uc .ic path, .uc .ic circle, .uc .ic ellipse, .uc .ic rect, .uc .ic line", { strokeDasharray: 1, strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 1, ease: "power2.out", stagger: 0.04 }, 1.1);',
                    '    tl.to("#d6-in", { scale: 1.02, duration: 6.5, ease: "none" }, 1);'])
    return scene("d6", 1920, 1080, css, body, js, "light")


def d7(c, pal, d):
    a1, a2, a3 = pal
    chips = [("기술이전 문의", CONTACT), (c.get("patlabel", "등록특허"), c["regno"])]
    ch = "".join(f'<div class="pc" id="d7-c{i}"><span>{E(k)}</span><b>{E(v)}</b></div>' for i, (k, v) in enumerate(chips))
    body = f"""
      <div style="position: absolute; left: 0; right: 0; top: 200px; text-align: center">
        <div class="eye" id="d7-e">{E(c["institute"])}</div>
        <div class="h" id="d7-t" style="margin-top: 22px; font-size: 100px; color: #fff"><span class="gr" style="font-family: Outfit, Pretendard; font-weight: 800">{plain(c["name"])}</span></div>
        <div class="sub" id="d7-s" style="margin-top: 18px; font-size: 42px">{E(c["sub"])}</div>
        <div id="d7-chips" style="display: flex; justify-content: center; gap: 22px; margin-top: 56px">{ch}</div>
        <div id="d7-f" style="margin-top: 54px; font-size: 28px; color: #9fb0a3">{DISCLAIMER}</div></div>"""
    css = d_css(pal) + """
    .pc { padding: 28px 36px; border-radius: 28px; background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.16); color: #fff; min-width: 380px; text-align: left; }
    .pc span { display: block; font-size: 28px; color: #b7c7ba; }
    .pc b { display: block; font-size: 42px; font-weight: 800; letter-spacing: -0.03em; margin-top: 6px; white-space: nowrap; }"""
    js = "\n".join([up("#d7-e", 0.3), blurin("#d7-t", 0.5, 1.2), up("#d7-s", 1.1), up(".pc", 1.5, 0.2, 0.8, 30), up("#d7-f", 2.3)])
    return scene("d7", 1920, 1080, css, body, js, "dark")


# ======================================================================= E
E_SLOTS = [("e1", "e1-open", 0.0, 9.0), ("e3", "e3-flow", 8.5, 9.0), ("e4", "e4-proof", 17.0, 13.0),
           ("ef", "ef-figures", 29.5, 7.0), ("e5", "e5-effects", 36.0, 7.0), ("e6", "e6-outlook", 42.5, 7.5),
           ("e7", "e7-end", 49.5, 7.0)]


def e_css(pal):
    a, b, c = pal
    acc = darken(b, 0.35)
    return f"""    .dark {{ background: #000; color: #f5f5f7; }}
    .light {{ background: #fff; color: #1d1d1f; }}
    .mist {{ background: #f5f5f7; color: #1d1d1f; }}
    .navy {{ background: #121a2e; color: #f5f5f7; background-image: linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px); background-size: 64px 64px; }}
    .h {{ font-weight: 700; letter-spacing: -0.035em; line-height: 1.14; text-align: center; }}
    .sub {{ font-size: 40px; color: #6e6e73; text-align: center; line-height: 1.5; letter-spacing: -0.02em; }}
    .dark .sub, .navy .sub {{ color: #a4acba; }}
    .eye {{ display: flex; justify-content: center; align-items: center; gap: 16px; font-size: 32px; font-weight: 600; color: {acc}; }}
    .dark .eye, .navy .eye {{ color: {a}; }}
    .eye b {{ width: 52px; height: 52px; border-radius: 50%; background: {acc}; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 28px; }}
    .card {{ background: #fff; border-radius: 36px; box-shadow: 0 40px 100px rgba(0, 0, 0, 0.10), 0 2px 6px rgba(0, 0, 0, 0.04); }}
    .gr {{ background: linear-gradient(100deg, {a}, {b} 50%, {c}); -webkit-background-clip: text; background-clip: text; color: transparent; padding: 0 0.1em 0.06em 0.02em; margin: 0 -0.1em -0.06em -0.02em; }}
    .light .gr, .mist .gr {{ background: linear-gradient(100deg, {darken(a, 0.3)}, {darken(b, 0.3)} 50%, {darken(c, 0.25)}); -webkit-background-clip: text; background-clip: text; }}
    .tile {{ display: flex; align-items: center; justify-content: center; border-radius: 34px; background: {rgba(b, 0.14)}; }}
    .foot {{ position: absolute; left: 0; right: 0; bottom: 44px; text-align: center; font-size: 28px; color: #6e6e73; }}
    .dark .foot {{ color: #8a8f99; }}"""


def e1(c, pal, d):
    """One opening, two beats: the headline asks, then steps back to become the kicker of the title card."""
    a, b, cc = pal
    body = f"""{grad_defs("e1-lg", a, cc)}
      <div id="e1-grid" class="navy" style="position: absolute; inset: 0; opacity: 0" data-layout-ignore></div>
      <div id="e1-halo" style="position: absolute; left: 760px; top: 110px; width: 400px; height: 400px; border-radius: 50%; background: radial-gradient(circle, {rgba(b, 0.38)}, transparent 65%)" data-layout-ignore></div>
      <div id="e1-art" style="position: absolute; left: 830px; top: 180px" data-layout-ignore>{icon(c["hero"], 260, "url(#e1-lg)", 4)}</div>
      <div class="h" id="e1-t" style="position: absolute; left: 160px; right: 160px; top: 540px; font-size: 104px">{grad_text(c["headline"])}</div>
      <div class="sub" id="e1-s" style="position: absolute; left: 160px; right: 160px; top: 830px">{E(c["process"].get("note", ""))}</div>
      <div id="e1-mark" class="tile" style="position: absolute; left: 870px; top: 250px; width: 180px; height: 180px; opacity: 0; background: linear-gradient(135deg, {darken(b, 0.2)}, {darken(cc, 0.25)})">{icon(c["hero"], 110, "#ffffff", 5)}</div>
      <div id="e1-p" style="position: absolute; left: 0; right: 0; top: 480px; text-align: center; font-size: 32px; font-weight: 600; color: {a}; opacity: 0">{E(c.get("patlabel", "등록특허"))} {E(c["regno"])} · {E(c["institute"])}</div>
      <div class="h" id="e1-title" style="position: absolute; left: 140px; right: 140px; top: 545px; font-size: {fit(c["sub"], 124, 1640)}px; font-weight: 800; opacity: 0">{E(c["sub"])}</div>
      <div id="e1-n" class="gr" style="position: absolute; left: 0; right: 0; top: 780px; text-align: center; font-family: Outfit; font-size: 60px; font-weight: 800; letter-spacing: 0.04em; opacity: 0">{plain(c["name"])}</div>"""
    T = 3.8  # second beat
    js = "\n".join([
        blurin("#e1-art", 0.05, 1.6),
        '    tl.fromTo("#e1-art .ic", { strokeDasharray: 1, strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 1.8, ease: "power2.inOut", stagger: 0.1 }, 0.1);',
        '    tl.fromTo("#e1-halo", { opacity: 0.4, scale: 0.9 }, { opacity: 1, scale: 1.1, duration: 9, ease: "none" }, 0);',
        '    tl.fromTo("#e1-t", { opacity: 0.3, y: 30 }, { opacity: 1, y: 0, duration: 1.1, ease: "expo.out" }, 0.2);',
        up("#e1-s", 1.6),
        # beat 2: the question steps back to the top, the icon becomes the mark, the stage turns to the navy grid
        f'    tl.to("#e1-s", {{ opacity: 0, duration: 0.4, ease: "power2.in" }}, {T - 0.3});',
        f'    tl.to("#e1-t", {{ y: -440, scale: 0.42, transformOrigin: "50% 0%", opacity: 0.85, duration: 1.0, ease: "expo.inOut" }}, {T});',
        f'    tl.to("#e1-art", {{ opacity: 0, scale: 0.6, duration: 0.6, ease: "power3.in" }}, {T});',
        f'    tl.to("#e1-grid", {{ opacity: 1, duration: 1.0, ease: "power2.inOut" }}, {T});',
        f'    tl.fromTo("#e1-mark", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.8, ease: "expo.out" }}, {T + 0.4});',
        up("#e1-p", T + 0.8),
        f'    tl.fromTo("#e1-title", {{ opacity: 0, filter: "blur(24px)", scale: 1.05 }}, {{ opacity: 1, filter: "blur(0px)", scale: 1, duration: 1.2, ease: "expo.out" }}, {T + 1.0});',
        up("#e1-n", T + 1.8),
        f'    tl.to("#e1-mark", {{ rotation: 6, duration: 4, ease: "none" }}, {T + 1.0});',
    ])
    return scene("e1", 1920, 1080, e_css(pal), body, js, "dark", enter=False)


def e3(c, pal, d):
    a, b, cc = pal
    steps = c["process"]["steps"][:5]
    n = len(steps)
    w = min(330, int((1700 - (n - 1) * 60) / n))
    flow = ""
    for i, st in enumerate(steps):
        if i:
            flow += f'<div class="arrow" id="e3-a{i}">›</div>'
        flow += (f'<div class="fs card" id="e3-s{i}" style="width: {w}px"><div class="pg">{icon(step_icon(st["n"], c["hero"]), 64, darken(b, 0.3), 5)}</div><small>STEP {i + 1}</small><h4>{E(st["n"])}</h4>'
                 f'<div class="v gr" style="font-size: {fit(st["big"] + st.get("u", ""), 46, w - 50)}px">{E(st["big"])}<em>{E(st.get("u", ""))}</em></div><p>{E(st["d"])}</p></div>')
    body = f"""
      <div style="position: absolute; left: 0; right: 0; top: 120px">
        <div class="eye" id="e3-e">기술 핵심</div>
        <div class="h" id="e3-t" style="margin-top: 22px; font-size: 76px">{grad_text(c["process"]["title"])}</div>
        <div class="sub" id="e3-sb" style="margin-top: 22px; font-size: 36px">{E(c["process"].get("note", ""))}</div></div>
      <div style="position: absolute; left: 0; right: 0; top: 520px; display: flex; justify-content: center; align-items: stretch">{flow}</div>"""
    css = e_css(pal) + f"""
    .fs {{ padding: 38px 26px; text-align: center; min-height: 360px; }}
    .fs .pg {{ height: 64px; margin-bottom: 16px; }}
    .fs small {{ display: block; font-size: 28px; font-weight: 700; color: {darken(b, 0.35)}; }}
    .fs h4 {{ font-size: 36px; font-weight: 700; letter-spacing: -0.02em; margin-top: 14px; white-space: nowrap; }}
    .fs .v {{ font-family: Outfit, Pretendard; font-weight: 800; margin-top: 22px; white-space: nowrap; }}
    .fs .v em {{ font-style: normal; font-size: 28px; margin-left: 4px; }}
    .fs p {{ font-size: 28px; color: #6e6e73; margin-top: 16px; line-height: 1.4; }}
    .arrow {{ width: 60px; display: flex; align-items: center; justify-content: center; font-size: 56px; color: #76767c; }}"""
    js = [up("#e3-e", 0.2), up("#e3-t", 0.35), up("#e3-sb", 0.8)]
    for i in range(n):
        t = 1.3 + i * 0.55
        js.append(up(f"#e3-s{i}", t, 0, 0.8, 40))
        js.append(f'    tl.fromTo("#e3-s{i} .ic", {{ strokeDasharray: 1, strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: 0.9, ease: "power2.out", stagger: 0.05 }}, {t + 0.2:.2f});')
        if i:
            js.append(f'    tl.fromTo("#e3-a{i}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4 }}, {t - 0.2:.2f});')
    js.append('    tl.to("#e3-in", { scale: 1.02, duration: 8, ease: "none" }, 1);')
    return scene("e3", 1920, 1080, css, body, "\n".join(js), "light")


def e4(c, pal, d):
    a, b, cc = pal
    pr = c["proof"]
    if pr.get("kind") == "anatomy":
        parts = "".join(f'<div class="pl" id="e4-p{i}">' + (f'<b>{E(str(p["ref"]))}</b>' if p.get("ref") else '<b class="dot"></b>')
                        + f'<span>{E(p["n"])}</span><small>{E(p["d"])}</small></div>' for i, p in enumerate(pr["parts"][:6]))
        body = f"""
      <div class="card" id="e4-ph" style="position: absolute; left: 130px; top: 130px; width: 820px; height: 820px; overflow: hidden">
        <img id="e4-img" src="assets/fig/{E(pr["figure"])}" alt="{E(pr.get("figcap", "도면"))}" style="position: absolute; left: 40px; top: 40px; width: 740px; height: 740px; object-fit: contain" /></div>
      <div style="position: absolute; left: 1030px; top: 170px; width: 760px">
        <div class="eye" id="e4-e" style="justify-content: flex-start">{E(pr.get("eyebrow", "ANATOMY"))}</div>
        <div class="h" id="e4-t" style="text-align: left; margin-top: 16px; font-size: 68px">{grad_text(pr.get("title", "핵심 |구성"))}</div>
        <div style="margin-top: 30px">{parts}</div></div>
      <div class="foot" style="left: 1030px; right: auto; text-align: left">{E(c.get("source", ""))}</div>"""
        css = e_css(pal) + f"""
    .pl {{ display: grid; grid-template-columns: 90px 1fr; grid-template-rows: auto auto; column-gap: 20px; padding: 14px 0; border-bottom: 1px solid #e5e5ea; }}
    .pl b {{ grid-row: span 2; align-self: center; height: 56px; border-radius: 28px; background: {darken(b, 0.35)}; color: #fff; font-size: 28px; text-align: center; line-height: 56px; }}
    .pl b.dot {{ width: 20px; height: 20px; margin-left: 30px; background: linear-gradient(135deg, {a}, {cc}); }}
    .pl span {{ font-size: 36px; font-weight: 700; white-space: nowrap; }}
    .pl small {{ font-size: 28px; color: #6e6e73; white-space: nowrap; }}"""
        js = [pop("#e4-ph", 0.3), '    tl.fromTo("#e4-img", { scale: 1 }, { scale: 1.07, duration: 12, ease: "none" }, 0.4);', up("#e4-e", 0.5), up("#e4-t", 0.65), up(".pl", 1.3, 0.75, 0.7, 24)]
        return scene("e4", 1920, 1080, css, body, "\n".join(js), "mist")
    items = pr["items"][:3]
    k = len(items)
    span = (d - 0.6) / k
    T = [round(0.4 + i * span, 2) for i in range(k)]
    blocks, js = "", []
    for i, it in enumerate(items):
        big = it["big"]
        bars = it.get("bars") or []
        dark = i % 2 == 0
        fg = "#f5f5f7" if dark else "#1d1d1f"
        bg = "#000" if dark else "#f5f5f7"
        rows = ""
        if bars:
            mx = it.get("max") or max(x["v"] for x in bars) * 1.15
            for j, br in enumerate(bars[:4]):
                track = "rgba(255,255,255,0.12)" if dark else "#e8e8ed"
                fill = f"linear-gradient(90deg, {a}, {cc})" if br.get("hi") else ("#55565c" if dark else "#c7c7cc")
                rows += (f'<div class="br"><span>{E(br["l"])}</span><em>{E(br.get("t", ""))}</em><div class="tr" style="background: {track}">'
                         f'<i id="e4-f{i}-{j}" style="background: {fill}"></i></div></div>')
                js.append(f'    tl.fromTo("#e4-f{i}-{j}", {{ scaleX: 0 }}, {{ scaleX: {max(0.01, min(1, br["v"] / mx)):.4f}, duration: 1.3, ease: "expo.out" }}, {T[i] + 1.0 + j * 0.2:.2f});')
        blocks += f"""
      <div class="blk" id="e4-k{i}" style="background: {bg}; color: {fg}{"; opacity: 0" if i else ""}">
        <div class="eye" style="position: absolute; left: 0; right: 0; top: 110px; color: {a if dark else darken(b, 0.35)}">{E(pr.get("eyebrow", "PERFORMANCE"))}</div>
        <div class="huge gr" style="position: absolute; left: 0; right: 0; top: 170px; text-align: center; font-size: {fit(big + it.get("u", ""), 260, 1250)}px"><span id="e4-n{i}">{E(big)}</span><span style="font-size: 0.36em">{E(it.get("u", ""))}</span></div>
        <div class="h" style="position: absolute; left: 160px; right: 160px; top: {500 if bars else 560}px; font-size: 70px">{E(it["l"])}</div>
        <div class="sub" style="position: absolute; left: 160px; right: 160px; top: {600 if bars else 670}px; font-size: 34px">{it.get("s", "").replace("<br />", " · ")}</div>
        <div style="position: absolute; left: 460px; right: 460px; top: 700px">{rows}</div></div>"""
        if i > 0:
            js.append(f'    tl.fromTo("#e4-k{i}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.6, ease: "power2.out" }}, {T[i]:.2f});')
            js.append(f'    tl.set("#e4-k{i - 1}", {{ opacity: 0 }}, {T[i] + 0.6:.2f});')
        js.append(blurin(f"#e4-k{i} .huge", T[i] + 0.15, 1.0))
        js.append(count(f"e4-n{i}", big, T[i] + 0.2))
        js.append(up(f"#e4-k{i} .h, #e4-k{i} .sub", T[i] + 0.7, 0.2, 0.8, 30))
    body = blocks + f'<div class="foot" id="e4-src" style="color: #8a8f99; z-index: 3">{E(c.get("source", ""))}</div>'
    css = e_css(pal) + """
    .blk { position: absolute; inset: 0; }
    .huge { font-family: Outfit, Pretendard; font-weight: 800; letter-spacing: -0.06em; line-height: 1; white-space: nowrap; }
    .br { position: relative; height: 78px; margin-bottom: 6px; }
    .br span { position: absolute; left: 0; top: 0; font-size: 28px; font-weight: 700; white-space: nowrap; }
    .br em { position: absolute; right: 0; top: 0; font-style: normal; font-size: 28px; font-weight: 800; }
    .br .tr { position: absolute; left: 0; right: 0; top: 42px; height: 24px; border-radius: 12px; overflow: hidden; }
    .br .tr i { position: absolute; left: 0; top: 0; width: 100%; height: 100%; border-radius: 12px; transform-origin: 0% 50%; transform: scaleX(0); }"""
    return scene("e4", 1920, 1080, css, body, "\n".join(x for x in js if x), "dark")


def ef(c, pal, d):
    """Apple-style figure stage: one large figure at a time cross-fades in the centre, a thumbnail strip marks the current one."""
    a, b, cc = pal
    figs = pick_figures(c, 4)
    items = figs or [{"icon": step_icon(st["n"], c["hero"]), "n": st["n"]} for st in c["process"]["steps"][:4]]
    k = len(items)
    big, thumbs = "", ""
    for i, it in enumerate(items):
        inner = (f'<img src="assets/fig/{E(it["file"])}" alt="명세서 도면 {i + 1}" />' if figs else
                 f'<div style="position: absolute; inset: 0; display: flex; align-items: center; justify-content: center">{icon(it["icon"], 320, "url(#ef-lg)", 3)}</div>')
        cap = f"도면 {i + 1} · 명세서 {it['page']}쪽" if figs else f"STEP {i + 1} · {E(it['n'])}"
        big += f'<div class="eb" id="ef-b{i}">{inner}<div class="ec">{cap}</div></div>'
        tin = (f'<img src="assets/fig/{E(it["file"])}" alt="" />' if figs else f'<div style="display: flex; height: 100%; align-items: center; justify-content: center">{icon(it["icon"], 60, darken(b, 0.3), 5)}</div>')
        thumbs += f'<div class="et" id="ef-t{i}">{tin}</div>'
    body = f"""{grad_defs("ef-lg", a, cc)}
      <div style="position: absolute; left: 0; right: 0; top: 70px; text-align: center">
        <div class="eye" id="ef-e">{"FROM THE SPECIFICATION" if figs else "AT A GLANCE"}</div>
        <div class="h" id="ef-t" style="margin-top: 12px; font-size: 64px">{'명세서 <span class="gr">도면</span>으로 보는 기술' if figs else '공정 <span class="gr">한눈에</span> 보기'}</div></div>
      <div class="card" id="ef-stage" style="position: absolute; left: 400px; top: 250px; width: 1120px; height: 600px; overflow: hidden">{big}</div>
      <div style="position: absolute; left: 0; right: 0; top: 890px; display: flex; justify-content: center; gap: 22px">{thumbs}</div>"""
    css = e_css(pal) + f"""
    .eb {{ position: absolute; inset: 0; opacity: 0; }}
    .eb img {{ position: absolute; left: 40px; right: 40px; top: 30px; bottom: 80px; width: calc(100% - 80px); height: calc(100% - 110px); object-fit: contain; }}
    .ec {{ position: absolute; left: 0; right: 0; bottom: 26px; text-align: center; font-size: 30px; font-weight: 600; color: #6e6e73; }}
    .et {{ width: 170px; height: 110px; border-radius: 16px; background: #fff; overflow: hidden; border: 3px solid transparent; opacity: 0.5; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08); }}
    .et img {{ width: 100%; height: 100%; object-fit: contain; }}"""
    step = (d - 1.0) / k
    js = [up("#ef-e", 0.2), up("#ef-t", 0.35), pop("#ef-stage", 0.4), up(".et", 0.7, 0.1, 0.6, 20)]
    for i in range(k):
        t = 0.6 + i * step
        js.append(f'    tl.fromTo("#ef-b{i}", {{ opacity: 0, scale: 1.04 }}, {{ opacity: 1, scale: 1, duration: 0.8, ease: "power2.out" }}, {t:.2f});')
        js.append(f'    tl.to("#ef-t{i}", {{ opacity: 1, borderColor: "{darken(b, 0.2)}", duration: 0.4 }}, {t:.2f});')
        js.append(f'    tl.fromTo("#ef-b{i} img", {{ scale: 1 }}, {{ scale: 1.05, duration: {step + 0.6:.2f}, ease: "none" }}, {t:.2f});')
        if not figs:
            js.append(f'    tl.fromTo("#ef-b{i} .ic", {{ strokeDasharray: 1, strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: 1.1, ease: "power2.out", stagger: 0.04 }}, {t + 0.1:.2f});')
        if i < k - 1:
            js.append(f'    tl.to("#ef-b{i}", {{ opacity: 0, duration: 0.6, ease: "power2.in" }}, {t + step - 0.1:.2f});')
            js.append(f'    tl.to("#ef-t{i}", {{ opacity: 0.5, borderColor: "rgba(0,0,0,0)", duration: 0.4 }}, {t + step:.2f});')
    return scene("ef", 1920, 1080, css, body, "\n".join(js), "mist")


def e5(c, pal, d):
    a, b, cc = pal
    f = c["features"]
    effs = "".join(f'<div class="ef card" id="e5-c{i}"><h4 class="gr" style="font-size: {fit(t["v"], 56, 420)}px">{E(t["v"])}</h4><b>{E(t["l"])}</b><p>{E(t["s"])}</p></div>'
                   for i, t in enumerate(f["tiles"][:6]))
    body = f"""
      <div style="position: absolute; left: 0; right: 0; top: 110px">
        <div class="eye" id="e5-e">특장점</div>
        <div class="h" id="e5-t" style="margin-top: 20px; font-size: 76px">{grad_text(f.get("title", "핵심 |특장점"))}</div></div>
      <div style="position: absolute; left: 130px; top: 360px; width: 1660px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 26px">{effs}</div>"""
    css = e_css(pal) + """
    .ef { padding: 38px 44px; }
    .ef h4 { font-family: Outfit, Pretendard; font-weight: 800; letter-spacing: -0.03em; white-space: nowrap; }
    .ef b { display: block; font-size: 38px; font-weight: 700; margin-top: 10px; white-space: nowrap; }
    .ef p { font-size: 28px; color: #6e6e73; margin-top: 8px; white-space: nowrap; }"""
    js = "\n".join([up("#e5-e", 0.2), up("#e5-t", 0.35), up(".ef", 0.9, 0.22, 0.8, 40), '    tl.to("#e5-in", { scale: 1.02, duration: 6, ease: "none" }, 1);'])
    return scene("e5", 1920, 1080, css, body, js, "light")


def e6(c, pal, d):
    a, b, cc = pal
    apps = c["apps"][:5]
    cx, cy = 960, 600
    pos = [(960, 300), (1500, 470), (1380, 840), (540, 840), (420, 470)][:len(apps)]
    lines = "".join(f'<line class="nl" pathLength="1" x1="{cx}" y1="{cy}" x2="{x}" y2="{y}" />' for x, y in pos)
    nodes = "".join(f'<div class="node" id="e6-n{i}" style="left: {x}px; top: {y}px">{E(ap["n"])}<small>{E(ap["s"].replace("<br />", " "))}</small></div>'
                    for i, ((x, y), ap) in enumerate(zip(pos, apps)))
    body = f"""
      <div class="eye" id="e6-e" style="position: absolute; left: 0; right: 0; top: 70px">기술이전 시 활용분야</div>
      <svg style="position: absolute; left: 0; top: 0" width="1920" height="1080" viewBox="0 0 1920 1080" data-layout-ignore>{lines}</svg>
      <div class="node core" id="e6-core" style="left: {cx}px; top: {cy}px">{plain(c["name"])}</div>{nodes}"""
    css = e_css(pal) + f"""
    .nl {{ stroke: {b}; stroke-width: 3; opacity: 0.7; }}
    .node {{ position: absolute; transform: translate(-50%, -50%); padding: 24px 36px; border-radius: 30px; font-size: 36px; font-weight: 700; background: #1a2236; border: 1px solid #2e3a55; color: #f5f5f7; text-align: center; white-space: nowrap; }}
    .node small {{ display: block; font-size: 28px; font-weight: 500; color: #a4acba; margin-top: 6px; }}
    .node.core {{ background: linear-gradient(135deg, {darken(b, 0.15)}, {darken(cc, 0.2)}); border: 0; font-family: Outfit, Pretendard; font-size: 46px; font-weight: 800; padding: 30px 44px; }}"""
    js = [up("#e6-e", 0.2), pop("#e6-core", 0.4)]
    for i in range(len(apps)):
        t = 1.0 + i * 0.5
        js.append(f'    tl.fromTo(".nl:nth-of-type({i + 1})", {{ strokeDasharray: 1, strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: 0.6, ease: "power2.out" }}, {t:.2f});')
        js.append(f'    tl.fromTo("#e6-n{i}", {{ opacity: 0, scale: 0.8 }}, {{ opacity: 1, scale: 1, duration: 0.6, ease: "back.out(1.6)" }}, {t + 0.35:.2f});')
    js.append('    tl.to("#e6-in", { scale: 1.025, duration: 6.5, ease: "none" }, 1);')
    return scene("e6", 1920, 1080, css, body, "\n".join(js), "navy")


def e7(c, pal, d):
    a, b, cc = pal
    body = f"""
      <div id="e7-mark" class="tile" style="position: absolute; left: 900px; top: 150px; width: 120px; height: 120px; border-radius: 32px; background: linear-gradient(135deg, {darken(b, 0.15)}, {darken(cc, 0.2)})">{icon(c["hero"], 76, "#ffffff", 5)}</div>
      <div class="h" id="e7-t" style="position: absolute; left: 0; right: 0; top: 310px; font-family: Outfit, Pretendard; font-size: 112px; font-weight: 800"><span class="gr">{plain(c["name"])}</span></div>
      <div class="sub" id="e7-s" style="position: absolute; left: 0; right: 0; top: 460px">{E(c["sub"])}</div>
      <div id="e7-row" style="position: absolute; left: 0; right: 0; top: 590px; display: flex; justify-content: center; gap: 24px">
        <div class="pc"><span>기술이전 문의</span><b class="gr">{CONTACT}</b></div></div>
      <div id="e7-m" style="position: absolute; left: 0; right: 0; top: 820px; text-align: center; font-size: 28px; color: #a4acba">{E(c.get("patlabel", "등록특허"))} {E(c["regno"])} · 특허권자 대한민국 ({E(c["institute"])})</div>
      <div id="e7-d" style="position: absolute; left: 0; right: 0; top: 880px; text-align: center; font-size: 28px; color: #8a8f99">{DISCLAIMER}</div>"""
    css = e_css(pal) + """
    .pc { padding: 30px 44px; border-radius: 30px; background: #111317; border: 1px solid #2a2d33; min-width: 460px; }
    .pc span { display: block; font-size: 28px; color: #a4acba; }
    .pc b { display: block; font-size: 46px; font-weight: 800; margin-top: 6px; white-space: nowrap; }"""
    js = "\n".join([pop("#e7-mark", 0.2), blurin("#e7-t", 0.5), up("#e7-s", 1.1), up("#e7-row .pc", 1.5, 0.2, 0.8, 30), up("#e7-m", 2.1), up("#e7-d", 2.4)])
    return scene("e7", 1920, 1080, css, body, js, "dark")


# ======================================================================= F
F_SLOTS = [("f1", "f1-hook", 0.0, 4.5), ("f2", "f2-name", 4.0, 5.0), ("f3", "f3-steps", 8.5, 6.5),
           ("f4", "f4-proof", 14.5, 7.5), ("ff", "ff-figures", 21.5, 5.0), ("f5", "f5-points", 26.0, 5.5),
           ("f6", "f6-apps", 31.0, 4.5), ("f7", "f7-end", 35.0, 5.5)]


def f_css(pal):
    a, b, c = pal
    return f"""    .blk {{ background: #000; color: #fff; }}
    .nav {{ background: #131a2e; color: #fff; }}
    .wht {{ background: #f5f5f7; color: #111; }}
    .gry {{ background: #5f6066; color: #fff; }}
    .t {{ position: absolute; left: 80px; right: 80px; text-align: center; font-weight: 800; letter-spacing: -0.035em; line-height: 1.18; }}
    .s {{ position: absolute; left: 80px; right: 80px; text-align: center; font-size: 34px; font-weight: 600; line-height: 1.45; }}
    .acc {{ color: {a}; }}
    .wht .acc {{ color: {darken(b, 0.35)}; }}
    .card {{ position: absolute; left: 90px; right: 90px; background: #fff; color: #111; border-radius: 40px; box-shadow: 0 30px 80px rgba(0, 0, 0, 0.18); }}"""


def f1(c, pal, d):
    hl = c["headline"]
    body = f"""
      <div class="t" id="f1-t" style="top: 560px; font-size: 104px">{grad_text(hl, "acc")}</div>
      <div class="s" id="f1-s" style="top: 1000px; color: #b9b9c0">{E(c["sub"])}</div>"""
    js = "\n".join(['    tl.fromTo("#f1-t", { opacity: 0.3, scale: 1.06 }, { opacity: 1, scale: 1, duration: 0.6, ease: "expo.out" }, 0);', up("#f1-s", 1.4)])
    return scene("f1", 1080, 1920, f_css(pal), body, js, "blk", enter=False)


def f2(c, pal, d):
    a, b, cc = pal
    name = c["name"]
    na, nb = (name.split("|", 1) + [""])[:2] if "|" in name else (name, "")
    body = f"""
      <div id="f2-ic" style="position: absolute; left: 430px; top: 420px; width: 220px; height: 220px; border-radius: 56px; background: linear-gradient(135deg, {darken(b, 0.1)}, {darken(cc, 0.2)}); display: flex; align-items: center; justify-content: center">{icon(c["hero"], 130, "#ffffff", 5)}</div>
      <div class="t" id="f2-n" style="top: 720px; font-family: Outfit, Pretendard; font-size: {fit(na + nb, 150, 920)}px; line-height: 1.05">{E(na)}<br /><span class="acc">{E(nb)}</span></div>
      <div class="s" id="f2-s" style="top: 1120px; color: #b9c1d6">{E(c.get("patlabel", "등록특허"))} {E(c["regno"])}<br />{E(c["institute"])}</div>"""
    js = "\n".join([pop("#f2-ic", 0.35), '    tl.fromTo("#f2-ic .ic", { strokeDasharray: 1, strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 1, ease: "power2.out", stagger: 0.08 }, 0.5);',
                    up("#f2-n", 0.8), up("#f2-s", 1.5), '    tl.to("#f2-ic", { y: -16, duration: 4.5, ease: "none" }, 0.5);'])
    return scene("f2", 1080, 1920, f_css(pal), body, js, "nav")


def f3(c, pal, d):
    a, b, cc = pal
    steps = c["process"]["steps"][:5]
    rows = "".join(f'<div class="ck" id="f3-r{i}" style="top: {i * 130}px"><i id="f3-b{i}">{icon(step_icon(st["n"], c["hero"]), 52, "#ffffff", 6)}</i>'
                   f'<div><b>{E(st["n"])}</b><span>{E(st["big"])}{E(st.get("u", ""))} · {E(st["d"])}</span></div></div>' for i, st in enumerate(steps))
    body = f"""
      <div class="t" id="f3-t" style="top: 260px; font-size: 76px">{grad_text(c["process"]["title"], "acc")}</div>
      <div style="position: absolute; left: 110px; right: 90px; top: 520px; height: 680px">{rows}</div>"""
    css = f_css(pal) + f"""
    .ck {{ position: absolute; left: 0; right: 0; height: 110px; display: flex; align-items: center; gap: 30px; }}
    .ck i {{ width: 84px; height: 84px; flex: none; border-radius: 24px; background: #e4e4e8; display: flex; align-items: center; justify-content: center; }}
    .ck svg {{ opacity: 0; }}
    .ck b {{ display: block; font-size: 46px; font-weight: 800; letter-spacing: -0.03em; white-space: nowrap; }}
    .ck span {{ display: block; font-size: 30px; font-weight: 600; color: #6e6e73; white-space: nowrap; }}"""
    js = [up("#f3-t", 0.3)]
    for i in range(len(steps)):
        t = 0.8 + i * 0.95
        js.append(up(f"#f3-r{i}", t, 0, 0.6, 30))
        js.append(f'    tl.to("#f3-b{i}", {{ backgroundColor: "{darken(b, 0.25)}", duration: 0.3 }}, {t + 0.45:.2f});')
        js.append(f'    tl.to("#f3-b{i} svg", {{ opacity: 1, duration: 0.2 }}, {t + 0.5:.2f});')
    return scene("f3", 1080, 1920, css, body, "\n".join(js), "wht")


def f4(c, pal, d):
    a, b, cc = pal
    pr = c["proof"]
    if pr.get("kind") == "anatomy":
        parts = "".join(f'<div class="pr">' + (f'<b>{E(str(p["ref"]))}</b>' if p.get("ref") else '<b>•</b>') + f'{E(p["n"])}</div>' for p in pr["parts"][:6])
        body = f"""
      <div class="t" id="f4-t" style="top: 230px; font-size: 64px">{grad_text(pr.get("title", "핵심 |구성"), "acc")}</div>
      <div class="card" id="f4-c" style="top: 400px; height: 900px">
        <img id="f4-img" src="assets/fig/{E(pr["figure"])}" alt="{E(pr.get("figcap", "도면"))}" style="position: absolute; left: 40px; top: 36px; width: 820px; height: 480px; object-fit: contain" />
        <div style="position: absolute; left: 50px; right: 40px; top: 550px">{parts}</div></div>"""
        css = f_css(pal) + f"""
    .pr {{ display: flex; align-items: center; gap: 18px; height: 54px; font-size: 32px; font-weight: 800; white-space: nowrap; }}
    .pr b {{ min-width: 64px; height: 44px; padding: 0 10px; border-radius: 22px; background: {darken(b, 0.3)}; color: #fff; font-size: 28px; text-align: center; line-height: 44px; }}"""
        js = "\n".join([up("#f4-t", 0.3), pop("#f4-c", 0.5), '    tl.fromTo("#f4-img", { scale: 1 }, { scale: 1.06, duration: 7, ease: "none" }, 0.6);',
                        up(".pr", 1.0, 0.45, 0.5, 20)])
        return scene("f4", 1080, 1920, css, body, js, "gry")
    it = pr["items"][0]
    bars = it.get("bars") or []
    rows = ""
    js = []
    if bars:
        mx = it.get("max") or max(x["v"] for x in bars) * 1.15
        cols = [darken(b, 0.2), darken(cc, 0.15), darken(a, 0.25), "#9aa0a6"]
        for j, br in enumerate(bars[:4]):
            rows += (f'<div class="sr"><span>{E(br["l"])}</span><div class="tr"><i id="f4-f{j}" style="background: {cols[0] if br.get("hi") else "#b8bcc2"}"></i></div><em>{E(br.get("t", ""))}</em></div>')
            js.append(f'    tl.fromTo("#f4-f{j}", {{ scaleX: 0 }}, {{ scaleX: {max(0.01, min(1, br["v"] / mx)):.4f}, duration: 1, ease: "expo.out" }}, {1.6 + j * 0.2:.2f});')
    big = it["big"]
    body = f"""
      <div class="t" id="f4-t" style="top: 250px; font-size: 72px">{E(it["l"])}</div>
      <div class="card" id="f4-c" style="top: 470px; padding: 56px 56px 50px">
        <div style="display: flex; align-items: center; gap: 30px">
          <div id="f4-badge" style="min-width: 260px; height: 220px; padding: 0 30px; border-radius: 40px; background: {darken(b, 0.25)}; color: #fff; display: flex; align-items: center; justify-content: center; font-family: Outfit, Pretendard; font-weight: 800; font-size: {fit(big + it.get("u", ""), 110, 420)}px; white-space: nowrap"><span id="f4-n">{E(big)}</span><span style="font-size: 0.45em">{E(it.get("u", ""))}</span></div>
          <div style="font-size: 30px; font-weight: 600; color: #6e6e73; line-height: 1.45">{it.get("s", "")}</div></div>
        <div style="margin-top: 40px">{rows}</div>
        <div style="margin-top: 26px; font-size: 28px; color: #6e6e73">{E(c.get("source", ""))}</div></div>"""
    css = f_css(pal) + """
    .sr { display: grid; grid-template-columns: 300px 1fr 130px; align-items: center; gap: 20px; margin: 18px 0; }
    .sr span { font-size: 30px; font-weight: 700; white-space: nowrap; overflow: hidden; }
    .sr .tr { height: 22px; border-radius: 11px; background: #ececf0; overflow: hidden; position: relative; }
    .sr .tr i { position: absolute; left: 0; top: 0; width: 100%; height: 100%; border-radius: 11px; transform-origin: 0% 50%; transform: scaleX(0); }
    .sr em { font-style: normal; font-size: 32px; font-weight: 800; text-align: right; white-space: nowrap; }"""
    js = [up("#f4-t", 0.3), pop("#f4-c", 0.6), count("f4-n", big, 0.9, 1.2)] + js + ['    tl.to("#f4-c", { y: -12, duration: 6.5, ease: "none" }, 1);']
    return scene("f4", 1080, 1920, css, body, "\n".join(x for x in js if x), "gry")


def ff(c, pal, d):
    """Two spec figures stacked as cards on grey (pictogram cards when the spec has none)."""
    a, b, cc = pal
    figs = pick_figures(c, 2)
    items = figs or [{"icon": step_icon(st["n"], c["hero"]), "n": st["n"]} for st in c["process"]["steps"][:2]]
    cards = ""
    for i, it in enumerate(items):
        top = 430 + i * 440
        inner = (f'<img src="assets/fig/{E(it["file"])}" alt="명세서 도면 {i + 1}" style="position: absolute; left: 30px; right: 30px; top: 24px; bottom: 74px; width: calc(100% - 60px); height: calc(100% - 98px); object-fit: contain" />'
                 if figs else f'<div style="position: absolute; inset: 0 0 60px; display: flex; align-items: center; justify-content: center">{icon(it["icon"], 200, darken(b, 0.3), 4)}</div>')
        cap = f"도면 {i + 1} · 명세서 {it['page']}쪽" if figs else f"STEP {i + 1} · {E(it['n'])}"
        cards += f'<div class="card ffc" id="ff-c{i}" style="top: {top}px; height: {400 if len(items) > 1 else 840}px">{inner}<div class="cp">{cap}</div></div>'
    body = f"""
      <div class="t" id="ff-t" style="top: 250px; font-size: 76px">{'명세서 <span class="acc">도면</span>' if figs else '공정 <span class="acc">한눈에</span>'}</div>{cards}"""
    css = f_css(pal) + """
    .ffc { overflow: hidden; }
    .ffc .cp { position: absolute; left: 0; right: 0; bottom: 20px; text-align: center; font-size: 30px; font-weight: 700; color: #55555a; }"""
    js = "\n".join([up("#ff-t", 0.25), up(".ffc", 0.5, 0.3, 0.7, 50),
                    f'    tl.fromTo(".ffc img", {{ scale: 1.12 }}, {{ scale: 1, duration: {d - 0.5:.1f}, ease: "power1.out" }}, 0.5);',
                    '    tl.fromTo(".ffc .ic", { strokeDasharray: 1, strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 1.0, ease: "power2.out", stagger: 0.04 }, 0.7);'])
    return scene("ff", 1080, 1920, css, body, js, "gry")


def f5(c, pal, d):
    a, b, cc = pal
    tiles = c["features"]["tiles"][:6]
    chips = "".join(f'<div class="pt" id="f5-p{i}" style="left: {(i % 2) * 460}px; top: {(i // 2) * 250}px"><b style="font-size: {fit(t["v"], 64, 360)}px">{E(t["v"])}</b><span>{E(t["l"])}</span></div>'
                    for i, t in enumerate(tiles))
    body = f"""
      <div class="t" id="f5-t" style="top: 260px; font-size: 76px">{grad_text(c["features"].get("title", "핵심 |특장점"), "acc")}</div>
      <div style="position: absolute; left: 90px; top: 480px; width: 900px; height: 760px">{chips}</div>"""
    css = f_css(pal) + f"""
    .pt {{ position: absolute; width: 440px; height: 226px; border-radius: 34px; background: #fff; box-shadow: 0 16px 40px rgba(0, 0, 0, 0.06); padding: 32px 34px; }}
    .pt b {{ display: block; font-family: Outfit, Pretendard; font-weight: 800; color: {darken(b, 0.3)}; letter-spacing: -0.03em; white-space: nowrap; }}
    .pt span {{ display: block; font-size: 34px; font-weight: 700; margin-top: 14px; white-space: nowrap; }}"""
    js = "\n".join([up("#f5-t", 0.25), pop(".pt", 0.6, 0.35)])
    return scene("f5", 1080, 1920, css, body, js, "wht")


def f6(c, pal, d):
    a, b, cc = pal
    rows = "".join(f'<div class="ap" id="f6-a{i}" style="top: {i * 140}px"><i>{icon(ap["icon"], 56, a, 5)}</i><div><b>{E(ap["n"])}</b><span>{E(ap["s"].replace("<br />", " "))}</span></div></div>'
                   for i, ap in enumerate(c["apps"][:5]))
    body = f"""
      <div class="t" id="f6-t" style="top: 250px; font-size: 76px">기술이전 시<br /><span class="acc">활용분야</span></div>
      <div style="position: absolute; left: 100px; right: 90px; top: 560px; height: 720px">{rows}</div>"""
    css = f_css(pal) + """
    .ap { position: absolute; left: 0; right: 0; height: 120px; display: flex; align-items: center; gap: 28px; }
    .ap i { width: 96px; height: 96px; flex: none; border-radius: 28px; background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.16); display: flex; align-items: center; justify-content: center; }
    .ap b { display: block; font-size: 46px; font-weight: 800; white-space: nowrap; }
    .ap span { display: block; font-size: 30px; font-weight: 600; color: #b9c1d6; white-space: nowrap; }"""
    js = "\n".join([up("#f6-t", 0.25), up(".ap", 0.7, 0.4, 0.6, 30)])
    return scene("f6", 1080, 1920, css, body, js, "nav")


def f7(c, pal, d):
    a, b, cc = pal
    body = f"""
      <div class="t" id="f7-n" style="top: 300px; font-family: Outfit, Pretendard; font-size: {fit(plain(c["name"]), 120, 920)}px">{plain(c["name"])}</div>
      <div class="s" id="f7-s" style="top: 470px; font-size: 40px; font-weight: 700; color: #3a3a3f">{E(c["sub"])}</div>
      <div class="card" id="f7-c" style="top: 600px; padding: 20px 50px">
        <div class="rw" style="border: 0"><span>기술이전 문의</span><b class="acc">{CONTACT}</b></div></div>
      <div class="s" id="f7-m" style="top: 840px; font-size: 30px; color: #55555a">{E(c.get("patlabel", "등록특허"))} {E(c["regno"])}<br />특허권자 대한민국 ({E(c["institute"])})</div>
      <div class="s" id="f7-d" style="top: 1000px; font-size: 28px; font-weight: 500; color: #6e6e73">{DISCLAIMER}</div>"""
    css = f_css(pal) + """
    .rw { display: flex; justify-content: space-between; align-items: center; height: 120px; border-bottom: 1px solid #ececf0; }
    .rw span { font-size: 30px; font-weight: 700; color: #6e6e73; }
    .rw b { font-size: 44px; font-weight: 800; white-space: nowrap; }"""
    js = "\n".join([up("#f7-n", 0.25), up("#f7-s", 0.5), pop("#f7-c", 0.6), up("#f7-m", 0.8), up("#f7-d", 0.9)])
    return scene("f7", 1080, 1920, css, body, js, "wht")


TEMPLATES = {
    "D": (1920, 1080, 60.0, D_SLOTS, {"d1-hero": d1, "d2-split": d2, "d3-timeline": d3, "d4-results": d4, "df-figures": df, "d5-tiles": d5, "d6-uses": d6, "d7-end": d7}, "#08190f"),
    "E": (1920, 1080, 56.5, E_SLOTS, {"e1-open": e1, "e3-flow": e3, "e4-proof": e4, "ef-figures": ef, "e5-effects": e5, "e6-outlook": e6, "e7-end": e7}, "#000000"),
    "F": (1080, 1920, 40.5, F_SLOTS, {"f1-hook": f1, "f2-name": f2, "f3-steps": f3, "f4-proof": f4, "ff-figures": ff, "f5-points": f5, "f6-apps": f6, "f7-end": f7}, "#000000"),
}


def index(c, tpl):
    w, h, total, slots, _, bg = TEMPLATES[tpl]
    music = MUSIC[(int(c["order"]) - 1) % len(MUSIC)]
    hosts = "\n".join(
        f'      <div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{f}.html" data-start="{st}" data-duration="{du}" '
        f'data-track-index="{1 if i % 2 == 0 else 2}" data-track-kind="graphics" data-width="{w}" data-height="{h}" style="z-index: {i + 1}"></div>'
        for i, (sid, f, st, du) in enumerate(slots))
    sfx = "\n".join(
        f'      <audio id="sfx-{i}" class="clip" src="assets/sfx/whoosh-short.mp3" data-start="{st}" data-duration="0.55" data-track-index="{11 + i % 2}" data-volume="0.12"></audio>'
        for i, (_, _, st, _) in enumerate(slots) if i > 0)
    return f"""<!doctype html>
<html lang="ko">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={w}, height={h}" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
{FONT}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: {w}px; height: {h}px; overflow: hidden; background: {bg}; }}
      #root {{ position: relative; width: 100%; height: 100%; font-family: "Pretendard", "Outfit", sans-serif; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="{w}" data-height="{h}">
{hosts}
      <audio id="bgm" class="clip" src="assets/music/{music}" data-start="0" data-duration="{total}" data-track-index="10" data-volume="0.6" data-fade-in="0.4" data-fade-out="2.5"></audio>
{sfx}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
"""


def build(tpl, path):
    tpl = tpl.upper()
    w, h, total, slots, scenes, _ = TEMPLATES[tpl]
    c = json.load(open(path, encoding="utf-8"))
    pal = PALETTES.get(c.get("palette", "blue"), PALETTES["blue"])
    slug = f'{int(c["order"]):03d}-{c["appno"]}'
    out = os.path.join(ROOT, "videos_" + tpl.lower(), slug)
    os.makedirs(os.path.join(out, "compositions"), exist_ok=True)
    os.makedirs(os.path.join(out, "assets", "fig"), exist_ok=True)
    for sub in ("fonts", "sfx", "music"):
        dst = os.path.join(out, "assets", sub)
        if not os.path.exists(dst) and os.path.isdir(os.path.join(ROOT, "assets", sub)):
            shutil.copytree(os.path.join(ROOT, "assets", sub), dst)
    if c["proof"].get("kind") == "anatomy":
        shutil.copy(os.path.join(ROOT, "data", "patents", c["appno"], c["proof"]["figure"]), os.path.join(out, "assets", "fig", c["proof"]["figure"]))
    for fn in ("package.json", "hyperframes.json"):
        s = open(os.path.join(ROOT, "template", fn), encoding="utf-8").read().replace("__SLUG__", f"{slug}-{tpl.lower()}")
        open(os.path.join(out, fn), "w", encoding="utf-8").write(s)
    for sid, f, st, du in slots:
        open(os.path.join(out, "compositions", f + ".html"), "w", encoding="utf-8").write(scenes[f](c, pal, du))
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(index(c, tpl))
    copy_figures(c, out)
    if tpl in ("D", "E"):
        add_transitions(out, tpl, slots, total, w, h)
    print(slug, f"built ({tpl})")
    return out


if __name__ == "__main__":
    for p in sys.argv[2:]:
        build(sys.argv[1], p)
