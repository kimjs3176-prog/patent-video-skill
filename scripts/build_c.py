"""Template C: vertical 9:16 kinetic typography (full-bleed colour fields, giant type, beat cuts), 49.5 s.

Usage: python -I tools/build_c.py data/content/<order>-<appno>.json [...]
Output: videos_c/<slug>/ ; same content JSON as template A.
"""
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import CONTACT, DISCLAIMER, E, MUSIC, PALETTES, ROOT, fit  # noqa: E402
from icons import icon  # noqa: E402
from visuals import copy_figures, pick_figures, step_icon  # noqa: E402

W, H = 1080, 1920
DARK, PAPER = "#0d0d12", "#f3efe6"
SLOTS = [("c1", "c1-hook", 0.0, 5.0), ("c2", "c2-headline", 4.6, 4.4), ("c3", "c3-process", 8.6, 9.5),
         ("c4", "c4-proof", 17.7, 10.0), ("cf", "cf-figures", 27.3, 4.9), ("c5", "c5-features", 31.8, 8.0),
         ("c6", "c6-apps", 39.4, 4.8), ("c7", "c7-outro", 43.8, 5.7)]
TOTAL = 49.5


def fields(pal):
    a, b, c = pal
    return [DARK, a, PAPER, b, DARK, c, PAPER]


def ink(bg):
    return PAPER if bg == DARK else DARK


def page(sid, body, script, bg, extra_css=""):
    return f"""<template>
  <style>
    @font-face {{ font-family: "NotoKR"; src: url("assets/fonts/NotoSansKR-VF.ttf") format("truetype"); font-weight: 100 900; }}
    #root {{ position: absolute; inset: 0; overflow: hidden; font-family: "NotoKR", "Outfit", sans-serif; word-break: keep-all; }}
    #{sid}-in {{ position: absolute; inset: 0; background: {bg}; }}
    .beat {{ position: absolute; inset: 0; }}
    .ghost {{ position: absolute; left: -20px; right: -20px; top: 1380px; font-family: Outfit; font-weight: 800; font-size: 560px; line-height: 1;
      letter-spacing: -0.05em; color: transparent; -webkit-text-stroke: 3px currentColor; opacity: 0.22; white-space: nowrap; }}
    .k {{ position: absolute; left: 72px; right: 72px; font-weight: 900; letter-spacing: -0.04em; line-height: 1.08; }}
    .w {{ display: inline-block; }}
{extra_css}
  </style>
  <div id="root" data-composition-id="{sid}" data-width="{W}" data-height="{H}">
    <div id="{sid}-in">{body}</div>
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    // colour flood: the new field rises from the bottom edge
    {"" if sid == "c1" else 'tl.fromTo("#' + sid + '-in", { clipPath: "inset(100% 0% 0% 0%)" }, { clipPath: "inset(0% 0% 0% 0%)", duration: 0.38, ease: "power4.inOut" }, 0);'}
{script}
    window.__timelines["{sid}"] = tl;
  </script>
</template>
"""


def words(text, cls="w"):
    return " ".join(f'<span class="{cls}">{E(w)}</span>' for w in text.split())


def slam(sel, t, stagger=0.09):
    return (f'    tl.fromTo("{sel}", {{ opacity: 0, scale: 1.45, filter: "blur(10px)" }}, '
            f'{{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.32, ease: "expo.out", stagger: {stagger} }}, {t:.2f});')


def beats(sid, items, dur, start=0.35):
    """Evenly spaced hard-cut beats; each beat div is shown from its start (later beats sit on top)."""
    n = len(items)
    span = (dur - start) / n
    js = []
    for i in range(n):
        t = start + i * span
        if i > 0:
            js.append(f'    tl.fromTo("#{sid}-b{i}", {{ clipPath: "inset(0% 0% 100% 0%)" }}, {{ clipPath: "inset(0% 0% 0% 0%)", duration: 0.28, ease: "power4.inOut" }}, {t:.2f});')
        js.append(f'    tl.fromTo("#{sid}-b{i} .pop", {{ opacity: 0, scale: 1.35 }}, {{ opacity: 1, scale: 1, duration: 0.34, ease: "expo.out", stagger: 0.08 }}, {t + 0.12:.2f});')
        js.append(f'    tl.fromTo("#{sid}-b{i} .ghost", {{ x: 120 }}, {{ x: -80, duration: {span + 0.3:.2f}, ease: "none" }}, {t:.2f});')
    return [round(start + i * span, 2) for i in range(n)], js


def c1(c, pal, d):
    a = pal[0]
    name = c["name"].replace("|", "")
    size = fit(name, 210, 940)
    body = f"""
      <div class="ghost" style="color: {PAPER}" data-layout-ignore>PATENT</div>
      <div class="k" id="c1-eye" style="top: 300px; font-size: 34px; font-weight: 800; letter-spacing: 0.18em; color: {a}">TECH REVEAL</div>
      <div class="k" id="c1-sub" style="top: 380px; font-size: 104px; color: {PAPER}">{words(c["sub"])}</div>
      <div class="beat" id="c1-flood" style="background: {a}">
        <div class="ghost" style="color: {DARK}" data-layout-ignore>{E(name.split()[0])}</div>
        <div class="k" style="top: 520px; font-family: Outfit; font-weight: 800; font-size: {size}px; color: {DARK}; white-space: nowrap; letter-spacing: -0.03em">{"".join(f'<span class="ch">{E(ch) if ch != " " else "&nbsp;"}</span>' for ch in name)}</div>
        <div class="k" id="c1-meta" style="top: 1060px; font-size: 36px; font-weight: 800; color: {DARK}">{E(c.get("patlabel", "등록특허"))} 제{E(c["regno"])}호<br />{E(c["institute"])}</div>
      </div>"""
    js = ['    tl.fromTo("#c1-sub .w", { opacity: 0.35, scale: 1.25 }, { opacity: 1, scale: 1, duration: 0.32, ease: "expo.out", stagger: 0.1 }, 0.05);',
          '    tl.fromTo("#c1-flood", { clipPath: "inset(100% 0% 0% 0%)" }, { clipPath: "inset(0% 0% 0% 0%)", duration: 0.4, ease: "power4.inOut" }, 2.0);',
          '    tl.fromTo("#c1-flood .ch", { opacity: 0, y: 90 }, { opacity: 1, y: 0, duration: 0.36, ease: "expo.out", stagger: 0.03 }, 2.2);',
          '    tl.to(["#c1-eye", "#c1-sub"], { opacity: 0, duration: 0.18, ease: "power2.in" }, 1.85);',
          slam("#c1-meta", 2.7),
          '    tl.fromTo("#c1-flood .ghost", { x: 100 }, { x: -60, duration: 3.0, ease: "none" }, 2.0);']
    extra = "    .ch { display: inline-block; }\n    #c1-sub .w { margin-right: 0.18em; }"
    return page("c1", body, "\n".join(js), DARK, extra)


def c2(c, pal, d):
    b = pal[1]
    hl = c["headline"]
    p1, p2 = (hl.split("|", 1) + [""])[:2] if "|" in hl else (hl, "")
    body = f"""
      <div class="ghost" style="color: {DARK}" data-layout-ignore>WHY</div>
      <div class="k" id="c2-a" style="top: 420px; font-size: 96px; color: {DARK}">{words(p1)}</div>
      <div id="c2-band" style="position: absolute; left: 56px; right: 56px; top: 760px; padding: 26px 20px 34px; background: {DARK}">
        <div id="c2-b" style="font-size: {fit(p2 or ' ', 118, 900)}px; font-weight: 900; letter-spacing: -0.04em; line-height: 1.1; color: {PAPER}">{E(p2)}</div>
      </div>"""
    js = [slam("#c2-a .w", 0.3, 0.1),
          '    tl.fromTo("#c2-band", { scaleX: 0, transformOrigin: "0% 50%" }, { scaleX: 1, duration: 0.45, ease: "expo.inOut" }, 1.2);',
          slam("#c2-b", 1.55),
          '    tl.fromTo("#c2-in .ghost", { x: 140 }, { x: -120, duration: 4.4, ease: "none" }, 0);']
    if not p2:
        body = body.replace('id="c2-band"', 'id="c2-band" data-hidden')
    return page("c2", body, "\n".join(js), b, "    #c2-a .w { margin-right: 0.16em; }")


def c3(c, pal, d):
    steps = c["process"]["steps"][:6]
    fl = fields(pal)
    divs = []
    for i, st in enumerate(steps):
        bg = fl[(i + 1) % len(fl)]
        fg = ink(bg)
        big = st["big"] + st.get("u", "")
        divs.append(f"""
      <div class="beat" id="c3-b{i}" style="background: {bg}; color: {fg}">
        <div class="ghost" data-layout-ignore>{i + 1:02d}</div>
        <div class="pop" style="position: absolute; right: 72px; top: 250px">{icon(step_icon(st["n"], c["hero"]), 170, fg, 7)}</div>
        <div class="k pop" style="top: 300px; font-size: 34px; font-weight: 800; letter-spacing: 0.16em">STEP {i + 1:02d} / {len(steps):02d}</div>
        <div class="k pop" style="top: 370px; font-size: 76px">{E(st["n"])}</div>
        <div class="k pop" style="top: 560px; font-family: Outfit, NotoKR; font-weight: 800; font-size: {fit(big, 300, 940)}px; line-height: 1; white-space: nowrap">{E(st["big"])}<span style="font-size: 0.42em">{E(st.get("u", ""))}</span></div>
        <div class="k pop" style="top: 1000px; font-size: 44px; font-weight: 700">{E(st["d"])}</div>
      </div>""")
    T, js = beats("c3", steps, d)
    js += [f'    tl.fromTo("#c3-b{i} .ic", {{ strokeDasharray: 1, strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: 0.7, ease: "power2.out", stagger: 0.04 }}, {t + 0.15:.2f});'
           for i, t in enumerate(T)]
    return page("c3", "".join(divs), "\n".join(js), fl[1])


def c4(c, pal, d):
    pr = c["proof"]
    fl = fields(pal)
    if pr.get("kind") == "anatomy":
        parts = pr["parts"][:6]
        ticker = "".join(f'<div class="tk pop" style="top: {i * 58}px">' + (f'<b>{E(str(p["ref"]))}</b>' if p.get("ref") else '<b>•</b>') + f'{E(p["n"])}</div>'
                         for i, p in enumerate(parts))
        body = f"""
      <div class="beat" id="c4-b0" style="background: {PAPER}; color: {DARK}">
        <div class="k pop" style="top: 220px; font-size: 34px; font-weight: 800; letter-spacing: 0.16em">{E(pr.get("eyebrow", "ANATOMY"))}</div>
        <div class="k pop" style="top: 276px; font-size: 64px">{E(pr.get("title", "핵심 구성").replace("|", ""))}</div>
        <div id="c4-fig" class="pop" style="position: absolute; left: 72px; top: 400px; width: 936px; height: 470px; border: 6px solid {DARK}; background: #fff">
          <img src="assets/fig/{E(pr["figure"])}" alt="{E(pr.get("figcap", "도면"))}" style="position: absolute; left: 16px; top: 12px; width: 892px; height: 434px; object-fit: contain" /></div>
        <div class="k" style="top: 884px; font-size: 28px; font-weight: 600; line-height: 1.4">{E(c.get("source", ""))}</div>
        <div style="position: absolute; left: 72px; right: 72px; top: 984px; height: 350px">{ticker}</div>
      </div>"""
        js = ['    tl.fromTo("#c4-b0 .pop", { opacity: 0, x: 80 }, { opacity: 1, x: 0, duration: 0.35, ease: "expo.out", stagger: 0.55 }, 0.3);',
              '    tl.fromTo("#c4-fig img", { scale: 1 }, { scale: 1.08, duration: 10, ease: "none" }, 0.4);']
        extra = f"""    .tk {{ position: absolute; left: 0; right: 0; height: 52px; display: flex; align-items: center; gap: 16px; font-size: 34px; font-weight: 900; white-space: nowrap; }}
    .tk b {{ min-width: 60px; height: 46px; padding: 0 10px; background: {DARK}; color: {PAPER}; font-size: 28px; text-align: center; line-height: 46px; }}"""
        return page("c4", body, "\n".join(js), PAPER, extra)
    items = pr["items"][:3]
    divs, count_js = [], []
    T, js = beats("c4", items, d - 0.6)
    for i, it in enumerate(items):
        bg = [DARK, fl[1], PAPER][i % 3]
        fg = ink(bg)
        big = it["big"] + it.get("u", "")
        bars = it.get("bars") or []
        rows = ""
        if bars:
            mx = it.get("max") or max(x["v"] for x in bars) * 1.15
            for j, br in enumerate(bars[:3]):
                hi = br.get("hi")
                band_bg = (pal[0] if bg == DARK else DARK) if hi else ("rgba(255,255,255,0.18)" if bg == DARK else "rgba(13,13,18,0.14)")
                band_fg = DARK if (hi and bg == DARK) else (PAPER if hi else fg)
                track = "rgba(255,255,255,0.16)" if bg == DARK else "rgba(13,13,18,0.12)"
                rows += (f'<div class="band" style="top: {j * 104}px"><span>{E(br["l"])}</span><em>{E(br.get("t", ""))}</em>'
                         f'<div class="trk" style="background: {track}"><div class="fill" id="c4-f{i}-{j}" style="background: {band_bg}"></div></div></div>')
                js.append(f'    tl.fromTo("#c4-f{i}-{j}", {{ scaleX: 0 }}, {{ scaleX: {max(0.12, min(1, br["v"] / mx)):.4f}, duration: 0.6, ease: "expo.out" }}, {T[i] + 0.5 + j * 0.15:.2f});')
        num = re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", it["big"].replace(",", ""))
        divs.append(f"""
      <div class="beat" id="c4-b{i}" style="background: {bg}; color: {fg}">
        <div class="ghost" data-layout-ignore>{E(it["big"])}</div>
        <div class="k pop" style="top: 260px; font-size: 34px; font-weight: 800; letter-spacing: 0.16em">{E(pr.get("eyebrow", "PERFORMANCE"))}</div>
        <div class="k pop" style="top: 330px; font-family: Outfit, NotoKR; font-weight: 800; font-size: {fit(big, 280, 940)}px; line-height: 1; white-space: nowrap"><span id="c4-n{i}">{E(it["big"])}</span><span style="font-size: 0.4em">{E(it.get("u", ""))}</span></div>
        <div class="k pop" style="top: 650px; font-size: 64px">{E(it["l"])}</div>
        <div class="k pop" style="top: 750px; font-size: 38px; font-weight: 700; line-height: 1.45">{it.get("s", "")}</div>
        <div style="position: absolute; left: 72px; right: 72px; top: 890px; height: 320px">{rows}</div>
      </div>""")
        if num:
            dec = len(it["big"].split(".")[1]) if "." in it["big"] else 0
            count_js.append(f'    (() => {{ const el = document.querySelector("#c4-n{i}"); const o = {{ v: 0 }}; tl.to(o, {{ v: {float(it["big"].replace(",", ""))}, duration: 0.9, ease: "power2.out", onUpdate: () => {{ el.textContent = o.v.toFixed({dec}); }} }}, {T[i] + 0.15:.2f}); }})();')
    extra = f"""    .band {{ position: absolute; left: 0; right: 0; height: 96px; }}
    .band span {{ position: absolute; left: 0; top: 0; font-size: 32px; font-weight: 800; white-space: nowrap; }}
    .band em {{ position: absolute; right: 0; top: 0; font-style: normal; font-size: 32px; font-weight: 900; }}
    .band .trk {{ position: absolute; left: 0; right: 0; top: 50px; height: 38px; }}
    .band .fill {{ position: absolute; left: 0; top: 0; width: 100%; height: 38px; transform-origin: 0% 50%; }}"""
    src = f'<div class="k" style="top: 1226px; font-size: 28px; font-weight: 600; line-height: 1.4; color: {PAPER}; z-index: 5" id="c4-src">{E(c.get("source", ""))}</div>'
    # source line follows the field it sits on (beat 0 dark, then light fields)
    if len(T) > 1:
        js.append(f'    tl.to("#c4-src", {{ color: "{DARK}", duration: 0.01 }}, {T[1]});')
    return page("c4", "".join(divs) + src, "\n".join(js + count_js), DARK, extra)


def cf(c, pal, d):
    """Spec-figure montage: one figure per beat on alternating fields; without figures, step pictograms instead."""
    fl = fields(pal)
    figs = pick_figures(c, 3)
    items = figs or [{"icon": step_icon(st["n"], c["hero"]), "n": st["n"]} for st in c["process"]["steps"][:3]]
    divs = []
    for i, it in enumerate(items):
        bg = fl[(i + 2) % len(fl)]
        fg = ink(bg)
        if figs:
            art = (f'<div class="pop" style="position: absolute; left: 72px; right: 72px; top: 470px; height: 760px; background: #fff; border-radius: 12px; overflow: hidden">'
                   f'<img src="assets/fig/{E(it["file"])}" alt="명세서 도면 {i + 1}" style="position: absolute; inset: 24px; width: calc(100% - 48px); height: calc(100% - 48px); object-fit: contain" /></div>')
            cap = f"명세서 도면 · {it['page']}쪽"
        else:
            art = f'<div class="pop" style="position: absolute; left: 0; right: 0; top: 560px; text-align: center">{icon(it["icon"], 520, fg, 4)}</div>'
            cap = E(it["n"])
        divs.append(f"""
      <div class="beat" id="cf-b{i}" style="background: {bg}; color: {fg}">
        <div class="ghost" data-layout-ignore>FIG</div>
        <div class="k pop" style="top: 250px; font-size: 34px; font-weight: 800; letter-spacing: 0.16em">FIG {i + 1:02d} / {len(items):02d}</div>
        <div class="k pop" style="top: 310px; font-size: 76px">{"명세서 도면" if figs else "공정 한눈에"}</div>
        {art}
        <div class="k pop" style="top: 1250px; font-size: 40px; font-weight: 700">{cap}</div>
      </div>""")
    T, js = beats("cf", items, d)
    js += [f'    tl.fromTo("#cf-b{i} img", {{ scale: 1.15 }}, {{ scale: 1, duration: 1.6, ease: "power2.out" }}, {t:.2f});' for i, t in enumerate(T)]
    js += [f'    tl.fromTo("#cf-b{i} .ic", {{ strokeDasharray: 1, strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: 0.9, ease: "power2.out", stagger: 0.04 }}, {t + 0.1:.2f});'
           for i, t in enumerate(T)] if not figs else []
    return page("cf", "".join(divs), "\n".join(js), fl[2])


def c5(c, pal, d):
    fl = fields(pal)
    tiles = c["features"]["tiles"][:6]
    divs = []
    for i, t in enumerate(tiles):
        bg = fl[(i + 2) % len(fl)]
        fg = ink(bg)
        divs.append(f"""
      <div class="beat" id="c5-b{i}" style="background: {bg}; color: {fg}">
        <div class="ghost" data-layout-ignore>{i + 1:02d}</div>
        <div class="k pop" style="top: 300px; font-size: 34px; font-weight: 800; letter-spacing: 0.16em">HIGHLIGHT {i + 1:02d}</div>
        <div class="k pop" style="top: 470px; font-family: Outfit, NotoKR; font-weight: 800; font-size: {fit(t["v"], 250, 940)}px; line-height: 1.05; white-space: nowrap">{E(t["v"])}</div>
        <div class="k pop" style="top: 860px; font-size: 72px">{E(t["l"])}</div>
      </div>""")
    _, js = beats("c5", tiles, d, 0.3)
    return page("c5", "".join(divs), "\n".join(js), fl[2])


def c6(c, pal, d):
    a = pal[0]
    rows = "".join(f'<div class="ap" style="top: {i * 150}px"><span class="nm">{E(ap["n"])}</span>'
                   + (f'<em style="background: {a}">청구항</em>' if ap.get("claim") else "") + f'<div class="sb">{E(ap["s"].replace("<br />", " "))}</div></div>'
                   for i, ap in enumerate(c["apps"][:5]))
    body = f"""
      <div class="ghost" style="color: {PAPER}" data-layout-ignore>USE</div>
      <div class="k" id="c6-t" style="top: 250px; font-size: 34px; font-weight: 800; letter-spacing: 0.16em; color: {a}">기술이전 시 활용분야</div>
      <div style="position: absolute; left: 72px; right: 72px; top: 340px; height: 760px; color: {PAPER}">{rows}</div>"""
    js = [slam("#c6-t", 0.25),
          '    tl.fromTo(".ap", { opacity: 0, x: -120 }, { opacity: 1, x: 0, duration: 0.32, ease: "expo.out", stagger: 0.42 }, 0.5);',
          '    tl.fromTo("#c6-in .ghost", { x: 140 }, { x: -100, duration: 4.8, ease: "none" }, 0);']
    extra = f"""    .ap {{ position: absolute; left: 0; right: 0; height: 140px; }}
    .ap .nm {{ font-size: 70px; font-weight: 900; letter-spacing: -0.04em; white-space: nowrap; }}
    .ap em {{ font-style: normal; margin-left: 18px; padding: 6px 14px; color: {DARK}; font-size: 28px; font-weight: 900; vertical-align: 18px; }}
    .ap .sb {{ font-size: 32px; font-weight: 600; color: rgba(243, 239, 230, 0.75); white-space: nowrap; }}"""
    return page("c6", body, "\n".join(js), DARK, extra)


def c7(c, pal, d):
    a = pal[0]
    name = c["name"].replace("|", "")
    body = f"""
      <div class="k" id="c7-n" style="top: 260px; font-family: Outfit; font-weight: 800; font-size: {fit(name, 150, 940)}px; white-space: nowrap; color: {DARK}">{E(name)}</div>
      <div class="k" id="c7-s" style="top: 440px; font-size: 52px; color: {DARK}">{E(c["sub"])}</div>
      <div id="c7-r1" style="position: absolute; left: 72px; right: 72px; top: 600px; height: 150px; background: {DARK}; color: {PAPER}">
        <div style="position: absolute; left: 32px; top: 24px; font-size: 30px; font-weight: 700; opacity: 0.8">기술이전 문의</div>
        <div style="position: absolute; left: 32px; top: 66px; font-size: 60px; font-weight: 900; color: {a}">{CONTACT}</div></div>
      <div class="k" id="c7-m" style="top: 800px; font-size: 30px; font-weight: 700; line-height: 1.5; color: {DARK}">{E(c.get("patlabel", "등록특허"))} 제{E(c["regno"])}호 · 대한민국 ({E(c["institute"])})</div>
      <div class="k" id="c7-d" style="top: 930px; font-size: 28px; font-weight: 600; line-height: 1.5; color: #4a4a52">{DISCLAIMER}</div>"""
    js = ['    tl.fromTo(["#c7-n", "#c7-s", "#c7-r1", "#c7-m", "#c7-d"], { opacity: 0, x: -80 }, { opacity: 1, x: 0, duration: 0.34, ease: "expo.out", stagger: 0.12 }, 0.3);']
    return page("c7", body, "\n".join(js), PAPER)


SCENES = {"c1-hook": c1, "c2-headline": c2, "c3-process": c3, "c4-proof": c4, "cf-figures": cf, "c5-features": c5, "c6-apps": c6, "c7-outro": c7}


def index(c):
    music = MUSIC[(int(c["order"]) - 1) % len(MUSIC)]
    hosts = "\n".join(
        f'      <div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{f}.html" data-start="{st}" data-duration="{du}" '
        f'data-track-index="{1 if i % 2 == 0 else 2}" data-track-kind="graphics" data-width="{W}" data-height="{H}" style="z-index: {i + 1}"></div>'
        for i, (sid, f, st, du) in enumerate(SLOTS))
    sfx = "\n".join(
        f'      <audio id="sfx-{i}" class="clip" src="assets/sfx/whoosh-short.mp3" data-start="{st}" data-duration="0.55" data-track-index="{11 + i % 2}" data-volume="0.16"></audio>'
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
      html, body {{ margin: 0; width: {W}px; height: {H}px; overflow: hidden; background: {DARK}; }}
      #root {{ position: relative; width: 100%; height: 100%; font-family: "NotoKR", "Outfit", sans-serif; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="{W}" data-height="{H}">
{hosts}
      <audio id="bgm" class="clip" src="assets/music/{music}" data-start="0" data-duration="{TOTAL}" data-track-index="10" data-volume="0.65" data-fade-in="0.2" data-fade-out="2.5"></audio>
{sfx}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
"""


def build(path, out_root="videos_c"):
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
        s = open(os.path.join(ROOT, "template", fn), encoding="utf-8").read().replace("__SLUG__", slug + "-c")
        open(os.path.join(out, fn), "w", encoding="utf-8").write(s)
    for sid, f, st, du in SLOTS:
        open(os.path.join(out, "compositions", f + ".html"), "w", encoding="utf-8").write(SCENES[f](c, pal, du))
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(index(c))
    copy_figures(c, out)
    print(slug, "built (C)")
    return out


if __name__ == "__main__":
    for p in sys.argv[1:]:
        build(p)
