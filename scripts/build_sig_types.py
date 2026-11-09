"""Template S — three more signature types, for patents with no process, device or sequence to animate.

  formula   compositions · extracts · functional materials   the components pour into a vessel in their stated shares
                                                             → each effect: control vs treated bars, values as stated
  lineage   plant varieties · selected strains               the cross (or the source) and the selection steps draw down
                                                             to the new variety → its traits beside the check variety
  claim     any patent (the fallback when no type fits)      the independent claim assembles element by element, each
                                                             tied to its marker on the figure (or a block) → the
                                                             characterizing part glows → the claim map of dependent claims
                                                             grows from it, one stated result of the examples at the end

Scenes plug into build_sig (SIG, narrative()); the data contract is in CONTENT_SPEC "시그니처 장면".
"""
import json

import build as A
from build import E, fit, rgba
from sigcheck import HEX

COMP = ["#7ee787", "#79c0ff", "#ffa657", "#ff9bce", "#f2cc60", "#d2a8ff"]


def comp_color(p, i):
    """A component's own colour only when it is '#RRGGBB'/'#RGB' (sigcheck reports anything else; a build that skipped
    validate must still not write CSS or a quote into fill/style), else the palette's."""
    v = p.get("color")
    return v if isinstance(v, str) and HEX.fullmatch(v) else COMP[i % len(COMP)]


def _sc():
    import build_sig  # late: build_sig imports this module
    return build_sig


def _num(v):
    return f"{v:g}" if isinstance(v, (int, float)) else str(v)


# ====================================================================== formula
def fx_mix(c, pal, d):
    """The components pour into the vessel one by one in their stated shares; each row lights with its layer."""
    B = _sc()
    a, b, cc = pal
    sg = c["signature"]
    comps = sg["components"][:6]
    n = len(comps)
    tot = sum(float(p["v"]) for p in comps) or 1.0
    # vessel interior: x 250..690, y 330..880 (rounded jar)
    vx0, vx1, vy0, vy1 = 250, 690, 330, 880
    H = vy1 - vy0
    bands, streams, y = "", "", vy1
    for i, p in enumerate(comps):
        h = max(14, H * float(p["v"]) / tot * 0.96)
        y -= h
        col = comp_color(p, i)
        bands += f'<rect class="fx-band" id="fx-b{i}" x="{vx0}" y="{y:.0f}" width="{vx1 - vx0}" height="{h + 1:.0f}" fill="{col}" opacity="0.85" />'
        streams += (f'<rect id="fx-s{i}" x="{(vx0 + vx1) / 2 - 9:.0f}" y="210" width="18" height="{y - 210:.0f}" rx="9" fill="{col}" opacity="0" />')
    vessel = (f'<path d="M{vx0 - 20} 300 L{vx1 + 20} 300 M{vx0} 300 L{vx0} {vy1 - 40} Q{vx0} {vy1 + 20} {vx0 + 60} {vy1 + 20} '
              f'L{vx1 - 60} {vy1 + 20} Q{vx1} {vy1 + 20} {vx1} {vy1 - 40} L{vx1} 300" fill="none" stroke="rgba(255,255,255,0.7)" stroke-width="6" stroke-linecap="round" />')
    clip = (f'<clipPath id="fx-clip"><path d="M{vx0} 300 L{vx0} {vy1 - 40} Q{vx0} {vy1 + 20} {vx0 + 60} {vy1 + 20} L{vx1 - 60} {vy1 + 20} '
            f'Q{vx1} {vy1 + 20} {vx1} {vy1 - 40} L{vx1} 300 Z" /></clipPath>')
    rows = ""
    top0 = 560 - n * 112 / 2 + 40
    for i, p in enumerate(comps):
        col = comp_color(p, i)
        val = _num(p["v"]) + p.get("u", "")
        rows += (f'<div class="fx-r" id="fx-r{i}" style="top: {top0 + i * 112:.0f}px"><i style="background: {col}"></i>'
                 f'<div class="tx"><div class="n" style="font-size: {fit(p["n"], 38, 520)}px">{E(p["n"])}</div><div class="s">{E(p.get("role", ""))}</div></div>'
                 f'<div class="v" id="fx-v{i}">{E(val)}</div></div>')
    body = B.heading("fx", sg.get("mix_eyebrow", "FORMULA"), sg.get("mix_title") or sg.get("title") or f'{c["sub"]}의 |배합',
                     f"left: -100px; top: 100px; background: radial-gradient(circle, {rgba(b, 0.26)} 0%, rgba(0,0,0,0) 65%)") + f"""
      <svg width="1920" height="1080" style="position: absolute; inset: 0" data-layout-ignore>
        <defs>{clip}</defs>{streams}<g clip-path="url(#fx-clip)">{bands}</g>{vessel}
      </svg>
      {rows}
      <div class="cap" style="position: absolute; left: 140px; top: 1004px; font-size: 28px; color: #8e8ea3">{E(sg.get("base_note", "배합 비율 · 명세서"))}</div>"""
    css = """    .fx-r { position: absolute; left: 960px; width: 820px; height: 96px; display: flex; align-items: center; gap: 26px; opacity: 0.3; }
    .fx-r i { width: 26px; height: 26px; border-radius: 8px; flex: none; }
    .fx-r .tx { flex: 1; min-width: 0; }
    .fx-r .n { font-weight: 700; white-space: nowrap; }
    .fx-r .s { font-size: 28px; color: #a8a8bc; margin-top: 2px; white-space: nowrap; }
    .fx-r .v { font-size: 46px; font-weight: 800; font-variant-numeric: tabular-nums; white-space: nowrap; }"""
    step = (d - 2.8) / n
    js = ['    tl.fromTo("#fx-in svg path", { opacity: 0 }, { opacity: 1, duration: 0.6 }, 0.4);']
    for i, p in enumerate(comps):
        t = 1.0 + i * step
        js += [f'    tl.fromTo("#fx-s{i}", {{ opacity: 0, scaleY: 0, transformOrigin: "50% 0%" }}, {{ opacity: 0.9, scaleY: 1, duration: 0.35, ease: "power2.in" }}, {t:.2f});',
               f'    tl.fromTo("#fx-b{i}", {{ scaleY: 0, transformOrigin: "50% 100%" }}, {{ scaleY: 1, duration: 0.7, ease: "power2.out" }}, {t + 0.3:.2f});',
               f'    tl.to("#fx-s{i}", {{ opacity: 0, duration: 0.3 }}, {t + 0.8:.2f});',
               f'    tl.to("#fx-r{i}", {{ opacity: 1, duration: 0.4 }}, {t + 0.3:.2f});',
               A.count_js(f"#fx-v{i}", _num(p["v"]) + p.get("u", ""), t + 0.3, 0.8, "expo.out")]
        if i:
            js.append(f'    tl.to("#fx-r{i - 1}", {{ opacity: 0.75, duration: 0.3 }}, {t + 0.3:.2f});')
    js.append(f'    tl.to(".fx-r", {{ opacity: 1, duration: 0.4 }}, {d - 1.4:.2f});')
    return B.sc("fx", pal, css, body, js, d)


def fx_effect(c, pal, d):
    """Each stated effect as a pair of bars: control first, then the treated group lands with its value."""
    B = _sc()
    a, b, cc = pal
    sg = c["signature"]
    eff = sg["effects"][:4]
    k = len(eff)
    gw = min(420, 1560 / k)
    x0 = 960 - gw * k / 2
    base, H = 820, 380
    groups, js = "", []
    cl, tl_ = sg.get("control_label", "대조군"), sg.get("treated_label", "처리군")
    for i, e in enumerate(eff):
        cx = x0 + gw * (i + 0.5)
        mx = max(abs(float(e["control"])), abs(float(e["treated"]))) or 1.0
        hc, ht = H * abs(float(e["control"])) / mx, H * abs(float(e["treated"])) / mx
        up = e.get("better", "up") == "up"
        u = e.get("unit", "")
        groups += (f'<div class="fe-bar c" id="fe-c{i}" style="left: {cx - 96:.0f}px; top: {base - hc:.0f}px; height: {hc:.0f}px"></div>'
                   f'<div class="fe-bar t" id="fe-t{i}" style="left: {cx + 12:.0f}px; top: {base - ht:.0f}px; height: {ht:.0f}px; background: linear-gradient(180deg, {b}, {a})"></div>'
                   f'<div class="fe-val" id="fe-vc{i}" style="left: {cx - 136:.0f}px; top: {base - hc - 56:.0f}px">{E(_num(e["control"]) + u)}</div>'
                   f'<div class="fe-val hi" id="fe-vt{i}" style="left: {cx - 28:.0f}px; top: {base - ht - 56:.0f}px">{E(_num(e["treated"]) + u)}</div>'
                   f'<div class="fe-x" style="left: {cx - 120:.0f}px; top: {base + 14}px"><span>{E(cl)}</span><span>{E(tl_)}</span></div>'
                   f'<div class="fe-l" id="fe-l{i}" style="left: {cx - gw / 2:.0f}px; width: {gw:.0f}px; top: {base + 64}px">'
                   f'<b style="font-size: {fit(e["l"], 36, gw - 30)}px">{E(e["l"])}</b><span>{"▲ 높을수록 좋음" if up else "▼ 낮을수록 좋음"}'
                   f'{" · " + E(e["note"]) if e.get("note") else ""}</span></div>')
        t = 0.9 + i * min(1.8, (d - 3.0) / k)
        js += [f'    tl.fromTo("#fe-c{i}", {{ scaleY: 0, transformOrigin: "50% 100%" }}, {{ scaleY: 1, duration: 0.8, ease: "power3.out" }}, {t:.2f});',
               f'    tl.fromTo("#fe-vc{i}", {{ opacity: 0, y: 10 }}, {{ opacity: 1, y: 0, duration: 0.4 }}, {t + 0.6:.2f});',
               f'    tl.fromTo("#fe-t{i}", {{ scaleY: 0, transformOrigin: "50% 100%" }}, {{ scaleY: 1, duration: 1.2, ease: "expo.out" }}, {t + 0.5:.2f});',
               f'    tl.fromTo("#fe-vt{i}", {{ opacity: 0, y: 10 }}, {{ opacity: 1, y: 0, duration: 0.4 }}, {t + 1.2:.2f});',
               f'    tl.fromTo("#fe-l{i}", {{ opacity: 0, y: 14 }}, {{ opacity: 1, y: 0, duration: 0.5, ease: "expo.out" }}, {t + 0.2:.2f});']
    body = B.heading("fe", sg.get("effects_eyebrow", "EFFECT"), sg.get("effects_title") or "효능을 |수치로",
                     f"left: 700px; top: -200px; background: radial-gradient(circle, {rgba(b, 0.26)} 0%, rgba(0,0,0,0) 65%)") + f"""
      <div style="position: absolute; left: 140px; right: 140px; top: {base}px; height: 2px; background: rgba(255,255,255,0.2)"></div>
      {groups}
      <div class="cap" style="position: absolute; left: 140px; top: 1004px; font-size: 28px; color: #8e8ea3">{E(sg.get("effects_note", "자료: 명세서 실시예"))}</div>"""
    css = """    .fe-bar { position: absolute; width: 84px; border-radius: 12px 12px 0 0; }
    .fe-bar.c { background: #4a4a5c; }
    .fe-val { position: absolute; width: 164px; text-align: center; font-size: 34px; font-weight: 800; color: #a8a8bc; white-space: nowrap; font-variant-numeric: tabular-nums; }
    .fe-val.hi { color: #fff; }
    .fe-x { position: absolute; width: 240px; display: flex; justify-content: space-between; font-size: 28px; color: #8e8ea3; }
    .fe-l { position: absolute; text-align: center; }
    .fe-l b { display: block; font-weight: 700; white-space: nowrap; }
    .fe-l span { display: block; font-size: 28px; color: #a8a8bc; margin-top: 4px; white-space: nowrap; }"""
    return B.sc("fe", pal, css, body, js, d)


# ====================================================================== lineage
def ln_tree(c, pal, d):
    """The cross (or the source) at the top, the selection steps drawing down to the new variety."""
    B = _sc()
    a, b, cc = pal
    sg = c["signature"]
    steps = sg["steps"][:6]
    n = len(steps)
    cx, ytop = 960, 300
    cross = sg.get("cross") or {}
    head_html, line_d = "", ""
    if cross.get("mother") and cross.get("father"):
        head_html = (f'<div class="ln-p" id="ln-pm" style="left: {cx - 560}px; top: {ytop - 38}px"><b>♀</b>{E(cross["mother"])}</div>'
                     f'<div class="ln-p" id="ln-pf" style="left: {cx + 140}px; top: {ytop - 38}px"><b>♂</b>{E(cross["father"])}</div>'
                     f'<div class="ln-x" id="ln-x" style="left: {cx - 30}px; top: {ytop + 50}px">×</div>')
        line_d = f'<path id="ln-cl" d="M{cx - 140} {ytop} L{cx} {ytop + 80} L{cx + 140} {ytop}" fill="none" stroke="{rgba(b, 0.8)}" stroke-width="4" pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="1" />'
        y0 = ytop + 140
    else:
        head_html = f'<div class="ln-p src" id="ln-pm" style="left: {cx - 260}px; width: 520px; top: {ytop - 38}px">{E(sg.get("source", "분리원"))}</div>'
        y0 = ytop + 90
    y1 = 960
    gap = (y1 - y0) / max(1, n - 1) if n > 1 else 0
    ys = [y0 + i * gap for i in range(n)]
    nodes = ""
    for i, s in enumerate(steps):
        last = i == n - 1
        nodes += (f'<div class="ln-g" id="ln-g{i}" style="top: {ys[i] - 24:.0f}px">{E(s["gen"])}{(" · " + E(s["year"])) if s.get("year") else ""}</div>'
                  f'<div class="ln-n{" k" if last else ""}" id="ln-n{i}" style="left: {cx - 18}px; top: {ys[i] - 18:.0f}px"></div>'
                  f'<div class="ln-d{" k" if last else ""}" id="ln-d{i}" style="top: {ys[i] - (34 if last else 22):.0f}px">{E(s["l"])}</div>')
    spine = f'<path id="ln-sp" d="M{cx} {ys[0] - (60 if cross.get("mother") else 30):.0f} L{cx} {ys[-1]:.0f}" fill="none" stroke="rgba(255,255,255,0.35)" stroke-width="4" pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="1" />'
    body = B.heading("ln", sg.get("tree_eyebrow", "PEDIGREE"), sg.get("tree_title") or sg.get("title") or f'{sg.get("variety", "신품종")}이 |나오기까지',
                     f"left: 600px; top: -200px; background: radial-gradient(circle, {rgba(b, 0.26)} 0%, rgba(0,0,0,0) 65%)") + f"""
      <svg width="1920" height="1080" style="position: absolute; inset: 0" data-layout-ignore>{line_d}{spine}</svg>
      {head_html}{nodes}"""
    css = f"""    .ln-p {{ position: absolute; width: 420px; height: 76px; border-radius: 38px; display: flex; align-items: center; justify-content: center; gap: 14px;
      font-size: 34px; font-weight: 700; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.2); white-space: nowrap; }}
    .ln-p b {{ color: {b}; }}
    .ln-x {{ position: absolute; width: 60px; height: 60px; border-radius: 50%; background: {rgba(b, 0.2)}; border: 2px solid {b}; color: #fff;
      font-size: 36px; font-weight: 800; display: flex; align-items: center; justify-content: center; }}
    .ln-g {{ position: absolute; right: {1920 - cx + 46}px; height: 48px; line-height: 48px; font-size: 28px; font-weight: 700; color: #a8a8bc; white-space: nowrap; }}
    .ln-n {{ position: absolute; width: 36px; height: 36px; border-radius: 50%; background: #1a1a24; border: 4px solid rgba(255,255,255,0.4); }}
    .ln-n.k {{ background: {b}; border-color: #fff; box-shadow: 0 0 30px {b}; }}
    .ln-d {{ position: absolute; left: {cx + 46}px; font-size: 34px; font-weight: 600; color: #d8d8e4; white-space: nowrap; }}
    .ln-d.k {{ font-size: 56px; font-weight: 800; background: linear-gradient(90deg, {a}, {cc}); -webkit-background-clip: text; background-clip: text; color: transparent; }}"""
    step = (d - 3.2) / n
    js = ['    tl.fromTo(".ln-p", { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.6, ease: "expo.out", stagger: 0.2 }, 0.5);']
    if cross.get("mother"):
        js += ['    tl.to("#ln-cl", { strokeDashoffset: 0, duration: 0.7, ease: "power2.inOut" }, 1.0);',
               '    tl.fromTo("#ln-x", { scale: 0 }, { scale: 1, duration: 0.45, ease: "back.out(1.7)" }, 1.5);']
    js.append(f'    tl.to("#ln-sp", {{ strokeDashoffset: 0, duration: {step * (n - 1) + 0.6:.2f}, ease: "none" }}, 1.7);')
    for i in range(n):
        t = 1.8 + i * step
        js += [f'    tl.fromTo("#ln-n{i}", {{ scale: 0 }}, {{ scale: 1, duration: 0.45, ease: "back.out(1.7)" }}, {t:.2f});',
               f'    tl.fromTo(["#ln-g{i}", "#ln-d{i}"], {{ opacity: 0, x: 16 }}, {{ opacity: 1, x: 0, duration: 0.5, ease: "expo.out", stagger: 0.08 }}, {t + 0.1:.2f});']
    js.append(f'    tl.fromTo("#ln-n{n - 1}", {{ boxShadow: "0 0 0px {b}" }}, {{ boxShadow: "0 0 46px {b}", duration: 0.5, yoyo: true, repeat: 1, immediateRender: false }}, {1.8 + (n - 1) * step + 0.5:.2f});')
    return B.sc("ln", pal, css, body, js, d)


def ln_traits(c, pal, d):
    """The new variety's traits beside the check variety, one row at a time, values as stated."""
    B = _sc()
    a, b, cc = pal
    sg = c["signature"]
    tr = sg["traits"][:5]
    n = len(tr)
    rh = min(150, 600 / n)
    top0 = 560 - n * rh / 2 + 60
    rows, js = "", []
    new_l, chk_l = sg.get("variety", "신품종"), sg.get("check", "대비 품종")
    for i, t in enumerate(tr):
        mx = max(abs(float(t["new"])), abs(float(t["check"]))) * 1.1 or 1.0
        wn, wc = 860 * abs(float(t["new"])) / mx, 860 * abs(float(t["check"])) / mx
        y = top0 + i * rh
        u = t.get("unit", "")
        up = t.get("better", "up") == "up"
        rows += (f'<div class="lt-l" style="top: {y:.0f}px"><b style="font-size: {fit(t["l"], 36, 340)}px">{E(t["l"])}</b>'
                 f'<span>{"▲ 높을수록 좋음" if up else "▼ 낮을수록 좋음"}</span></div>'
                 f'<div class="lt-b n" id="lt-n{i}" style="top: {y:.0f}px; width: {wn:.0f}px; background: linear-gradient(90deg, {a}, {b})"></div>'
                 f'<div class="lt-v hi" id="lt-vn{i}" style="top: {y - 6:.0f}px; left: {560 + wn + 18:.0f}px">{E(_num(t["new"]) + u)}</div>'
                 f'<div class="lt-b c" id="lt-c{i}" style="top: {y + 44:.0f}px; width: {wc:.0f}px"></div>'
                 f'<div class="lt-v" id="lt-vc{i}" style="top: {y + 38:.0f}px; left: {560 + wc + 18:.0f}px">{E(_num(t["check"]) + u)}</div>')
        t0 = 1.0 + i * min(1.6, (d - 3.0) / n)
        js += [f'    tl.fromTo("#lt-c{i}", {{ scaleX: 0, transformOrigin: "0% 50%" }}, {{ scaleX: 1, duration: 0.8, ease: "power3.out" }}, {t0:.2f});',
               f'    tl.fromTo("#lt-vc{i}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4 }}, {t0 + 0.6:.2f});',
               f'    tl.fromTo("#lt-n{i}", {{ scaleX: 0, transformOrigin: "0% 50%" }}, {{ scaleX: 1, duration: 1.2, ease: "expo.out" }}, {t0 + 0.35:.2f});',
               f'    tl.fromTo("#lt-vn{i}", {{ opacity: 0, x: -10 }}, {{ opacity: 1, x: 0, duration: 0.45 }}, {t0 + 1.0:.2f});']
    legend = (f'<div style="position: absolute; left: 560px; top: {top0 - 76:.0f}px; display: flex; gap: 40px; font-size: 28px; font-weight: 700">'
              f'<span><i style="display: inline-block; width: 26px; height: 14px; border-radius: 7px; background: {b}; margin-right: 10px"></i>{E(new_l)}</span>'
              f'<span style="color: #a8a8bc"><i style="display: inline-block; width: 26px; height: 14px; border-radius: 7px; background: #4a4a5c; margin-right: 10px"></i>{E(chk_l)}</span></div>')
    body = B.heading("lt", sg.get("traits_eyebrow", "TRAITS"), sg.get("traits_title") or f'{new_l}의 |특성',
                     f"left: 300px; top: -200px; background: radial-gradient(circle, {rgba(b, 0.26)} 0%, rgba(0,0,0,0) 65%)") + f"""
      {legend}{rows}
      <div class="cap" style="position: absolute; left: 140px; top: 1004px; font-size: 28px; color: #8e8ea3">{E(sg.get("traits_note", "자료: 명세서 특성 조사"))}</div>"""
    css = """    .lt-l { position: absolute; left: 140px; width: 400px; }
    .lt-l b { display: block; font-weight: 700; white-space: nowrap; }
    .lt-l span { display: block; font-size: 28px; color: #a8a8bc; margin-top: 2px; white-space: nowrap; }
    .lt-b { position: absolute; left: 560px; height: 34px; border-radius: 17px; }
    .lt-b.c { background: #4a4a5c; height: 26px; border-radius: 13px; }
    .lt-v { position: absolute; font-size: 34px; font-weight: 800; color: #a8a8bc; white-space: nowrap; font-variant-numeric: tabular-nums; }
    .lt-v.hi { color: #fff; }"""
    return B.sc("lt", pal, css, body, js, d)


# ====================================================================== claim (any patent)
def _label(e, i):
    """The marker/badge text of a claim element: its drawing numeral when it has one, else its place in the claim."""
    return str(e["ref"]) if e.get("ref") not in (None, "") else str(i + 1)


def cl_anatomy(c, pal, d):
    """The independent claim assembles element by element: each chip of the claim card draws a line to that element's
    marker on the spec figure (or to its block in an assembling block diagram); then the characterizing elements glow
    with a 특징부 tag while the others dim."""
    B = _sc()
    a, b, cc = pal
    sg = c["signature"]
    cl = sg["claim"]
    els = cl["elements"][:5]
    n = len(els)
    feat = [i for i in cl["feature"]["idx"] if 0 <= i < n]
    fig = sg.get("figure")
    # claim card on the right: header, one chip per element, the characterizing line under them
    cx0, cw = 1040, 740
    rh = min(124, 500 / n)
    chh = rh - 16
    top0 = 392
    yc = [top0 + i * rh + chh / 2 for i in range(n)]  # chip centres: the leader lines start here
    labs = [_label(e, i) for i, e in enumerate(els)]
    chips = ""
    for i, e in enumerate(els):
        chips += (f'<div class="cl-c" id="cl-c{i}" style="top: {top0 + i * rh:.0f}px; height: {chh:.0f}px">'
                  f'<b style="font-size: {fit(labs[i], 30, 44)}px; background: linear-gradient(135deg, {a}, {cc})">{E(labs[i])}</b>'
                  f'<div><div class="n" style="font-size: {fit(e["n"], 38 if chh >= 96 else 34, 560)}px">{E(e["n"])}</div>'
                  f'<div class="s" style="font-size: {fit(e.get("d", ""), 28, 600)}px">{E(e.get("d", ""))}</div></div>'
                  + (f'<span class="cl-tag" id="cl-t{i}">특징부</span>' if i in feat else "") + '</div>')
    yf = top0 + n * rh + 12
    pre = cl.get("preamble", "")
    card = (f'<div id="cl-h" style="position: absolute; left: {cx0}px; top: 258px; width: {cw}px">'
            f'<div class="cl-no">청구항 {E(str(cl["no"]))} · 독립항</div><div class="cl-pre" style="font-size: {fit(pre, 50, cw)}px">{E(pre)}</div></div>'
            f'{chips}<div id="cl-f" style="top: {yf:.0f}px"><span class="cl-fk">특징</span>'
            f'<span class="grad" style="font-size: {fit(cl["feature"]["l"], 36, cw - 150)}px">{E(cl["feature"]["l"])}</span></div>')
    left, lines, marks, js_el, cap = "", "", "", {}, ""
    if fig:  # the elements on the spec figure: chip → line → marker, as the loop parts scene does for callouts
        pl, m = B.plate(c, fig, "cl", 120, 230, 840, 760)
        sc_html, sc_js = B.scan("cl", 120, 230, 840, 760, b, 0.7)
        left = pl + sc_html
        for i, e in enumerate(els):
            if "x" not in e or "y" not in e:
                continue  # an element the drawing does not show: its chip lights alone
            px, py = m(e["x"], e["y"])
            w = max(46, 18 * len(labs[i]) + 22)
            marks += (f'<div class="cl-mk" id="cl-m{i}" style="left: {px - w / 2:.0f}px; top: {py - 23:.0f}px; width: {w}px; background: {b}">{E(labs[i])}</div>')
            ph, pj = B.ping("cl", i, px, py, b)
            marks += ph
            lines += (f'<path class="cl-ln" id="cl-l{i}" d="M{cx0} {yc[i]:.0f} C {cx0 - 120} {yc[i]:.0f}, {px + 180:.0f} {py:.0f}, {px + w / 2 + 2:.0f} {py:.0f}" '
                      f'fill="none" stroke="{b}" stroke-width="3" pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="1" opacity="0.85" />')
            js_el[i] = (lambda t, i=i, pj=pj: [f'    tl.fromTo("#cl-m{i}", {{ opacity: 0, scale: 0 }}, {{ opacity: 1, scale: 1, duration: 0.45, ease: "back.out(1.7)" }}, {t:.2f});', pj(t + 0.1)])
        js0 = ['    tl.fromTo(["#cl-plate", "#cl-img"], { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 0.8, ease: "expo.out" }, 0.3);',
               f'    tl.fromTo("#cl-img", {{ scale: 1.04 }}, {{ scale: 1, duration: {d - 0.5:.1f}, ease: "power1.out" }}, 0.3);', *sc_js]
        cap = f'{E(sg.get("figcap", "명세서 도면"))} · 표식은 청구항 구성'
    else:  # no drawing to point at: the claimed subject is a frame and the elements assemble inside it as blocks
        fx0, fx1, fy0, fy1 = 170, 910, 310, 950
        gap = 20
        bh = min(130, (fy1 - fy0 - 80 - gap * (n - 1)) / n)
        by0 = (fy0 + fy1) / 2 - (n * bh + gap * (n - 1)) / 2
        left = (f'<div id="cl-fr" style="left: {fx0}px; top: {fy0}px; width: {fx1 - fx0}px; height: {fy1 - fy0}px"></div>'
                f'<div id="cl-fl" style="left: {fx0 + 30}px; top: {fy0 - 24}px; font-size: {fit(pre, 34, fx1 - fx0 - 100)}px">{E(pre)}</div>')
        for i, e in enumerate(els):
            ybc = by0 + i * (bh + gap) + bh / 2
            left += (f'<div class="cl-bk" id="cl-b{i}" style="top: {ybc - bh / 2:.0f}px; height: {bh:.0f}px">'
                     f'<b style="font-size: {fit(labs[i], 28, 40)}px">{E(labs[i])}</b>'
                     f'<span style="font-size: {fit(e["n"], 40, 500)}px">{E(e["n"])}</span></div>')
            lines += (f'<path class="cl-ln" id="cl-l{i}" d="M{cx0} {yc[i]:.0f} C {cx0 - 90} {yc[i]:.0f}, {fx1 + 60} {ybc:.0f}, 862 {ybc:.0f}" '
                      f'fill="none" stroke="{b}" stroke-width="3" pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="1" opacity="0.85" />')
            js_el[i] = (lambda t, i=i: [f'    tl.fromTo("#cl-b{i}", {{ opacity: 0, x: -70 }}, {{ opacity: 1, x: 0, duration: 0.6, ease: "expo.out" }}, {t - 0.2:.2f});',
                                        f'    tl.fromTo("#cl-b{i}", {{ scale: 1.05 }}, {{ scale: 1, duration: 0.35, ease: "back.out(2)", immediateRender: false }}, {t + 0.35:.2f});'])
        js0 = ['    tl.fromTo(["#cl-fr", "#cl-fl"], { opacity: 0, scale: 0.96 }, { opacity: 1, scale: 1, duration: 0.7, ease: "expo.out", stagger: 0.1 }, 0.35);']
        cap = "구성도는 청구항 구성의 모식"
    body = B.heading("cl", sg.get("anatomy_eyebrow", f'CLAIM {cl["no"]}'), sg.get("anatomy_title") or f'청구항 {cl["no"]}의 |구성',
                     f"left: 900px; top: -300px; background: radial-gradient(circle, {rgba(b, 0.28)} 0%, rgba(0,0,0,0) 65%)") + f"""
      {left}
      <svg width="1920" height="1080" style="position: absolute; inset: 0" data-layout-ignore>{lines}</svg>
      {marks}{card}
      <div class="cap" style="left: 140px; top: 1004px">{cap}</div>"""
    css = B.FIG_CSS + f"""
    .cl-no {{ font-size: 28px; font-weight: 700; letter-spacing: 0.08em; color: {b}; white-space: nowrap; }}
    .cl-pre {{ font-weight: 800; letter-spacing: -0.02em; margin-top: 4px; white-space: nowrap; }}
    .cl-c {{ position: absolute; left: {cx0}px; width: {cw}px; display: grid; grid-template-columns: 74px 1fr; align-items: center; padding: 0 24px;
      box-sizing: border-box; border-radius: 22px; border: 1px solid rgba(255,255,255,0.12); background: rgba(255,255,255,0.04); opacity: 0; }}
    .cl-c b {{ width: 56px; height: 56px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #000; font-weight: 800; }}
    .cl-c .n {{ font-weight: 700; white-space: nowrap; }}
    .cl-c .s {{ color: #a8a8bc; white-space: nowrap; margin-top: 2px; }}
    .cl-tag {{ position: absolute; right: 18px; top: -20px; height: 40px; line-height: 40px; padding: 0 16px; border-radius: 20px; font-size: 28px; font-weight: 800;
      color: #000; background: linear-gradient(90deg, {a}, {cc}); white-space: nowrap; opacity: 0; }}
    #cl-f {{ position: absolute; left: {cx0}px; width: {cw}px; display: flex; align-items: baseline; gap: 18px; font-weight: 800; white-space: nowrap; opacity: 0; }}
    .cl-fk {{ font-size: 28px; font-weight: 700; color: #000; background: {b}; border-radius: 10px; padding: 2px 12px; }}
    .cl-mk {{ position: absolute; height: 46px; border-radius: 23px; border: 3px solid #fff; box-sizing: border-box; box-shadow: 0 6px 18px rgba(0,0,0,0.35);
      color: #000; font-size: 28px; font-weight: 800; line-height: 40px; text-align: center; white-space: nowrap; opacity: 0; }}
    #cl-fr {{ position: absolute; border-radius: 34px; border: 3px dashed rgba(255,255,255,0.32); opacity: 0; }}
    #cl-fl {{ position: absolute; padding: 0 16px; background: #000; font-weight: 800; color: #e8e8f0; white-space: nowrap; line-height: 48px; opacity: 0; }}
    .cl-bk {{ position: absolute; left: 220px; width: 640px; display: flex; align-items: center; gap: 22px; padding: 0 28px; box-sizing: border-box;
      border-radius: 20px; background: #15151d; border: 2px solid rgba(255,255,255,0.22); font-weight: 700; white-space: nowrap; opacity: 0; }}
    .cl-bk b {{ width: 52px; height: 52px; flex: none; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #000;
      background: linear-gradient(135deg, {a}, {cc}); font-weight: 800; }}"""
    step = (d - 3.6) / n
    js = js0 + ['    tl.fromTo("#cl-h", { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.6, ease: "expo.out" }, 0.6);']
    for i in range(n):
        t = 1.2 + i * step
        js.append(f'    tl.fromTo("#cl-c{i}", {{ opacity: 0, x: 24 }}, {{ opacity: 1, x: 0, background: "{rgba(b, 0.14)}", duration: 0.5, ease: "expo.out" }}, {t:.2f});')
        if i in js_el:
            js += [f'    tl.to("#cl-l{i}", {{ strokeDashoffset: 0, duration: 0.6, ease: "power2.inOut" }}, {t + 0.25:.2f});', *js_el[i](t + 0.75)]
        if i:
            js.append(f'    tl.to("#cl-c{i - 1}", {{ background: "rgba(255,255,255,0.04)", opacity: 0.8, duration: 0.4 }}, {t:.2f});')
            if i - 1 in js_el:
                js.append(f'    tl.to("#cl-l{i - 1}", {{ opacity: 0.4, duration: 0.4 }}, {t:.2f});')
    # the characterizing part: the feature elements light, the rest step back
    tf = 1.2 + n * step
    rest = [i for i in range(n) if i not in feat]
    js.append(f'    tl.to("#cl-c{n - 1}", {{ background: "rgba(255,255,255,0.04)", duration: 0.4 }}, {tf - 0.4:.2f});')
    if not fig:
        js.append(f'    tl.to("#cl-fr", {{ borderColor: "{rgba(b, 0.6)}", duration: 0.5 }}, {tf - 0.5:.2f});')
    if rest:
        dim = [f"#cl-c{i}" for i in rest] + [f"#cl-l{i}" for i in rest if i in js_el] + [f"#cl-{'m' if fig else 'b'}{i}" for i in rest if i in js_el]
        js.append(f'    tl.to({json.dumps(dim)}, {{ opacity: 0.45, duration: 0.5 }}, {tf:.2f});')
    for k, i in enumerate(feat):
        tk = tf + 0.1 + k * 0.15
        js += [f'    tl.to("#cl-c{i}", {{ opacity: 1, background: "{rgba(b, 0.2)}", borderColor: "{b}", boxShadow: "0 0 36px {rgba(b, 0.4)}", duration: 0.5 }}, {tk:.2f});',
               f'    tl.fromTo("#cl-t{i}", {{ opacity: 0, y: 12 }}, {{ opacity: 1, y: 0, duration: 0.4, ease: "back.out(2)" }}, {tk + 0.1:.2f});']
        if i in js_el:
            js.append(f'    tl.to("#cl-l{i}", {{ opacity: 1, duration: 0.4 }}, {tk:.2f});')
            if fig:
                js += [f'    tl.fromTo("#cl-m{i}", {{ scale: 1.35 }}, {{ scale: 1, duration: 0.5, ease: "back.out(2)", immediateRender: false }}, {tk:.2f});',
                       B.ping("cl", i, 0, 0, b)[1](tk)]
            else:
                js.append(f'    tl.to("#cl-b{i}", {{ borderColor: "{b}", background: "{B.over(b, 0.24, "#15151d")}", boxShadow: "0 0 40px {rgba(b, 0.45)}", duration: 0.5 }}, {tk:.2f});')
    js.append(f'    tl.fromTo("#cl-f", {{ opacity: 0, y: 16 }}, {{ opacity: 1, y: 0, duration: 0.6, ease: "expo.out" }}, {tf + 0.4:.2f});')
    return B.sc("cl", pal, css, body, js, d)


def _deps_tree(sg):
    """Rows of the claim map: (dep, parent row indices, depth). A dependent claim hangs from the earlier rows it cites
    (`of`); one that cites only the independent claim, or rows not shown, hangs from the root."""
    deps = sg["deps"][:5]
    nos = [str(x["no"]) for x in deps]
    out = []
    for i, dp in enumerate(deps):
        of = dp.get("of")
        of = of if isinstance(of, list) else ([] if of is None else [of])
        ps = [nos.index(str(p)) for p in of if str(p) in nos[:i]]
        depth = 1 + max((out[p][2] for p in ps), default=0)
        out.append((dp, ps, min(depth, 3)))
    return out


def ct_tree(c, pal, d):
    """The claim map: the independent claim as the root, the dependent claims growing from it as branches with their
    short labels (a claim citing another hangs from that row); then, when given, one result of the examples lands as a
    control-vs-treated pair."""
    B = _sc()
    a, b, cc = pal
    sg = c["signature"]
    cl = sg["claim"]
    rows = _deps_tree(sg)
    k = len(rows)
    ev = sg.get("evidence")
    xr = 1420 if ev else 1780
    cy = 610
    rh = min(130, 640 / k)
    h = min(96, rh - 18)
    yc = [cy + (i - (k - 1) / 2) * rh for i in range(k)]
    xs = [700 + (dep - 1) * 70 for _, _, dep in rows]
    pre = cl.get("preamble", "")
    root = (f'<div id="ct-root" style="top: {cy - 130}px"><div class="no">청구항 {E(str(cl["no"]))}</div>'
            f'<div class="pre" style="font-size: {fit(pre, 56, 380)}px">{E(pre)}</div>'
            f'<div class="sub">독립항 · 구성 {len(cl["elements"])}</div></div>')
    html, paths = "", ""
    for i, (dp, ps, dep) in enumerate(rows):
        x = xs[i]
        cite = ""
        if dp.get("of") is not None and str(dp.get("of")) != str(cl["no"]):
            of = dp["of"] if isinstance(dp["of"], list) else [dp["of"]]
            cite = " · ".join(str(p) for p in of) + "항 인용"
        wl = xr - x - 150 - 40  # the citation rides on the row's corner, not in the label's width
        html += (f'<div class="ct-r" id="ct-r{i}" style="left: {x}px; top: {yc[i] - h / 2:.0f}px; width: {xr - x}px; height: {h:.0f}px">'
                 f'<b>제{E(str(dp["no"]))}항</b><span class="l" style="font-size: {fit(dp["l"], 36, wl)}px">{E(dp["l"])}</span>'
                 + (f'<span class="ci">{E(cite)}</span>' if cite else "") + '</div>')
        if ps:  # elbow from the nearest cited row, down its left side into this row
            p = max(ps)
            px = xs[p] + 34
            paths += (f'<path class="ct-br" id="ct-b{i}" d="M{px} {yc[p] + h / 2:.0f} L{px} {yc[i]:.0f} L{x} {yc[i]:.0f}" fill="none" stroke="{rgba(b, 0.75)}" '
                      f'stroke-width="4" pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="1" />')
        else:
            paths += (f'<path class="ct-br" id="ct-b{i}" d="M580 {cy} C 650 {cy}, {x - 70} {yc[i]:.0f}, {x} {yc[i]:.0f}" fill="none" stroke="{rgba(b, 0.75)}" '
                      f'stroke-width="4" pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="1" />')
    panel, ev_js = "", []
    step = (d - 2.6 - (2.2 if ev else 0.4)) / k
    te = 1.3 + k * step
    if ev:  # one result of the examples: control first, then the treated value lands (values as stated)
        x0, base, H = 1470, 850, 330
        mx = max(abs(float(ev["control"])), abs(float(ev["treated"]))) or 1.0
        hc, ht = H * abs(float(ev["control"])) / mx, H * abs(float(ev["treated"])) / mx
        u = ev.get("u", "")
        clab, tlab = ev.get("control_label", "대조"), ev.get("treated_label", "이 기술")
        arrow = "▲" if ev.get("better", "up") == "up" else "▼"
        panel = (f'<div id="ct-ev" style="left: {x0}px; top: 290px; width: 320px; height: 680px"></div>'
                 f'<div id="ct-evh" style="left: {x0 + 24}px; top: 312px; width: 272px"><div class="k">실시예 결과</div>'
                 f'<div class="l" style="font-size: {fit(ev["l"], 34, 272)}px">{E(ev["l"])}</div></div>'
                 f'<div class="ct-bar c" id="ct-ec" style="left: {x0 + 40}px; top: {base - hc:.0f}px; height: {hc:.0f}px"></div>'
                 f'<div class="ct-bar t" id="ct-et" style="left: {x0 + 186}px; top: {base - ht:.0f}px; height: {ht:.0f}px; background: linear-gradient(180deg, {b}, {a})"></div>'
                 f'<div class="ct-v" id="ct-vc" style="left: {x0 + 12}px; top: {base - hc - 52:.0f}px">{E(_num(ev["control"]) + u)}</div>'
                 f'<div class="ct-v hi" id="ct-vt" style="left: {x0 + 158}px; top: {base - ht - 52:.0f}px">{arrow} {E(_num(ev["treated"]) + u)}</div>'
                 f'<div class="ct-x" style="left: {x0 + 12}px; top: {base + 14}px; font-size: {fit(clab, 28, 140)}px">{E(clab)}</div>'
                 f'<div class="ct-x hi" style="left: {x0 + 158}px; top: {base + 14}px; font-size: {fit(tlab, 28, 140)}px">{E(tlab)}</div>'
                 + (f'<div class="ct-x" style="left: {x0 + 24}px; width: 272px; text-align: left; top: {base + 62}px; font-size: {fit(ev["src"], 28, 272)}px">{E(ev["src"])}</div>' if ev.get("src") else ""))
        ev_js = [f'    tl.fromTo(["#ct-ev", "#ct-evh"], {{ opacity: 0, x: 30 }}, {{ opacity: 1, x: 0, duration: 0.6, ease: "expo.out", stagger: 0.1 }}, {te:.2f});',
                 f'    tl.fromTo(".ct-x", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4 }}, {te + 0.3:.2f});',
                 f'    tl.fromTo("#ct-ec", {{ scaleY: 0, transformOrigin: "50% 100%" }}, {{ scaleY: 1, duration: 0.8, ease: "power3.out" }}, {te + 0.3:.2f});',
                 f'    tl.fromTo("#ct-vc", {{ opacity: 0, y: 10 }}, {{ opacity: 1, y: 0, duration: 0.4 }}, {te + 0.9:.2f});',
                 f'    tl.fromTo("#ct-et", {{ scaleY: 0, transformOrigin: "50% 100%" }}, {{ scaleY: 1, duration: 1.1, ease: "expo.out" }}, {te + 0.8:.2f});',
                 f'    tl.fromTo("#ct-vt", {{ opacity: 0, y: 10 }}, {{ opacity: 1, y: 0, duration: 0.4 }}, {te + 1.5:.2f});']
    body = B.heading("ct", sg.get("tree_eyebrow", "CLAIM MAP"), sg.get("tree_title") or f'{pre or "청구항"}의 |권리 범위',
                     f"left: 300px; top: -250px; background: radial-gradient(circle, {rgba(b, 0.26)} 0%, rgba(0,0,0,0) 65%)") + f"""
      <svg width="1920" height="1080" style="position: absolute; inset: 0" data-layout-ignore>{paths}</svg>
      {root}{html}{panel}
      <div class="cap" style="position: absolute; left: 140px; top: 1004px; font-size: 28px; color: #8e8ea3">{E(sg.get("tree_note", "등록 청구범위 · 종속항은 요약"))}</div>"""
    css = f"""    #ct-root {{ position: absolute; left: 140px; width: 440px; height: 260px; box-sizing: border-box; padding: 36px 34px; border-radius: 30px;
      background: {B.over(b, 0.16, "#000000")}; border: 2px solid {b}; box-shadow: 0 0 60px {rgba(b, 0.3)}; }}
    #ct-root .no {{ font-size: 30px; font-weight: 700; color: {b}; letter-spacing: 0.06em; }}
    #ct-root .pre {{ font-weight: 800; letter-spacing: -0.02em; margin-top: 10px; white-space: nowrap; }}
    #ct-root .sub {{ font-size: 28px; color: #a8a8bc; margin-top: 14px; white-space: nowrap; }}
    .ct-r {{ position: absolute; display: flex; align-items: center; gap: 22px; padding: 0 22px; box-sizing: border-box; border-radius: 22px;
      background: #101016; border: 1px solid rgba(255,255,255,0.16); white-space: nowrap; opacity: 0; }}
    .ct-r b {{ flex: none; width: 128px; height: 50px; border-radius: 25px; display: flex; align-items: center; justify-content: center;
      font-size: 28px; font-weight: 800; color: #000; background: linear-gradient(135deg, {a}, {cc}); }}
    .ct-r .l {{ font-weight: 700; flex: 1; min-width: 0; }}
    .ct-r .ci {{ position: absolute; right: 18px; top: -18px; height: 36px; line-height: 36px; padding: 0 14px; border-radius: 18px; font-size: 28px;
      color: #c8c8d8; background: #2a2a36; }}
    #ct-ev {{ position: absolute; border-radius: 28px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.14); opacity: 0; }}
    #ct-evh {{ position: absolute; opacity: 0; }}
    #ct-evh .k {{ font-size: 28px; font-weight: 700; letter-spacing: 0.2em; color: #a8a8bc; }}
    #ct-evh .l {{ font-weight: 800; margin-top: 6px; white-space: nowrap; }}
    .ct-bar {{ position: absolute; width: 84px; border-radius: 12px 12px 0 0; }}
    .ct-bar.c {{ background: #4a4a5c; }}
    .ct-v {{ position: absolute; width: 140px; text-align: center; font-size: 34px; font-weight: 800; color: #a8a8bc; white-space: nowrap; font-variant-numeric: tabular-nums; opacity: 0; }}
    .ct-v.hi {{ color: #fff; }}
    .ct-x {{ position: absolute; width: 140px; text-align: center; color: #8e8ea3; white-space: nowrap; opacity: 0; }}
    .ct-x.hi {{ color: #e8e8f0; font-weight: 700; }}"""
    js = ['    tl.fromTo("#ct-root", { opacity: 0, scale: 0.9 }, { opacity: 1, scale: 1, duration: 0.7, ease: "back.out(1.5)" }, 0.5);']
    for i in range(k):
        t = 1.3 + i * step
        js += [f'    tl.to("#ct-b{i}", {{ strokeDashoffset: 0, duration: 0.5, ease: "power2.inOut" }}, {t:.2f});',
               f'    tl.fromTo("#ct-r{i}", {{ opacity: 0, x: -20 }}, {{ opacity: 1, x: 0, borderColor: "{rgba(b, 0.8)}", duration: 0.5, ease: "expo.out" }}, {t + 0.35:.2f});',
               f'    tl.fromTo("#ct-r{i} b", {{ scale: 0.6 }}, {{ scale: 1, duration: 0.45, ease: "back.out(2)" }}, {t + 0.4:.2f});']
        if i:
            js.append(f'    tl.to("#ct-r{i - 1}", {{ borderColor: "rgba(255,255,255,0.16)", duration: 0.4 }}, {t + 0.35:.2f});')
    js.append(f'    tl.to("#ct-r{k - 1}", {{ borderColor: "rgba(255,255,255,0.16)", duration: 0.4 }}, {te - 0.3:.2f});')
    if not ev:  # no example value: the whole map lights once as it closes
        js.append(f'    tl.to(".ct-r", {{ borderColor: "{rgba(b, 0.8)}", duration: 0.3, yoyo: true, repeat: 1, stagger: 0.08 }}, {te:.2f});')
    return B.sc("ct", pal, css, body, js + ev_js, d)


SCENES = {"fx-mix": fx_mix, "fe-effect": fx_effect, "ln-tree": ln_tree, "lt-traits": ln_traits, "cl-anatomy": cl_anatomy, "ct-tree": ct_tree}


def narrative_mid(sg):
    """Middle scenes for the new types (teaser and apps/outro are added by build_sig.narrative)."""
    if sg["type"] == "claim":
        return [("cl", "cl-anatomy", round(min(13.0, max(9.0, 3.0 + 1.8 * len(sg["claim"]["elements"]))), 1)),
                ("ct", "ct-tree", round(min(12.0, max(8.0, 3.0 + 1.4 * len(sg["deps"]) + (1.6 if sg.get("evidence") else 0))), 1)), ("s5", "s5-features", 7.0)]
    if sg["type"] == "formula":
        return [("fx", "fx-mix", round(min(13.0, max(9.0, 2.8 + 1.7 * len(sg["components"]))), 1)),
                ("fe", "fe-effect", round(min(12.0, max(8.5, 3.0 + 1.8 * len(sg["effects"]))), 1)), ("s5", "s5-features", 7.0)]
    return [("ln", "ln-tree", round(min(13.0, max(9.0, 3.2 + 1.6 * len(sg["steps"]))), 1)),
            ("lt", "lt-traits", round(min(12.0, max(8.5, 3.0 + 1.6 * len(sg["traits"]))), 1)), ("s5", "s5-features", 7.0)]
