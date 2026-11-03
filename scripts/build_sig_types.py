"""Template S — two more signature types, for patents with no process, device or sequence to animate.

  formula   compositions · extracts · functional materials   the components pour into a vessel in their stated shares
                                                             → each effect: control vs treated bars, values as stated
  lineage   plant varieties · selected strains               the cross (or the source) and the selection steps draw down
                                                             to the new variety → its traits beside the check variety

Scenes plug into build_sig (SIG, narrative()); the data contract is in CONTENT_SPEC "시그니처 장면".
"""
import build as A
from build import E, fit, rgba

COMP = ["#7ee787", "#79c0ff", "#ffa657", "#ff9bce", "#f2cc60", "#d2a8ff"]


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
        col = p.get("color") or COMP[i % len(COMP)]
        bands += f'<rect class="fx-band" id="fx-b{i}" x="{vx0}" y="{y:.0f}" width="{vx1 - vx0}" height="{h + 1:.0f}" fill="{col}" opacity="0.85" />'
        streams += (f'<rect id="fx-s{i}" x="{(vx0 + vx1) / 2 - 9:.0f}" y="210" width="18" height="{y - 210:.0f}" rx="9" fill="{col}" opacity="0" />')
    vessel = (f'<path d="M{vx0 - 20} 300 L{vx1 + 20} 300 M{vx0} 300 L{vx0} {vy1 - 40} Q{vx0} {vy1 + 20} {vx0 + 60} {vy1 + 20} '
              f'L{vx1 - 60} {vy1 + 20} Q{vx1} {vy1 + 20} {vx1} {vy1 - 40} L{vx1} 300" fill="none" stroke="rgba(255,255,255,0.7)" stroke-width="6" stroke-linecap="round" />')
    clip = (f'<clipPath id="fx-clip"><path d="M{vx0} 300 L{vx0} {vy1 - 40} Q{vx0} {vy1 + 20} {vx0 + 60} {vy1 + 20} L{vx1 - 60} {vy1 + 20} '
            f'Q{vx1} {vy1 + 20} {vx1} {vy1 - 40} L{vx1} 300 Z" /></clipPath>')
    rows = ""
    top0 = 560 - n * 112 / 2 + 40
    for i, p in enumerate(comps):
        col = p.get("color") or COMP[i % len(COMP)]
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


SCENES = {"fx-mix": fx_mix, "fe-effect": fx_effect, "ln-tree": ln_tree, "lt-traits": ln_traits}


def narrative_mid(sg):
    """Middle scenes for the new types (teaser and apps/outro are added by build_sig.narrative)."""
    if sg["type"] == "formula":
        return [("fx", "fx-mix", round(min(13.0, max(9.0, 2.8 + 1.7 * len(sg["components"]))), 1)),
                ("fe", "fe-effect", round(min(12.0, max(8.5, 3.0 + 1.8 * len(sg["effects"]))), 1)), ("s5", "s5-features", 7.0)]
    return [("ln", "ln-tree", round(min(13.0, max(9.0, 3.2 + 1.6 * len(sg["steps"]))), 1)),
            ("lt", "lt-traits", round(min(12.0, max(8.5, 3.0 + 1.6 * len(sg["traits"]))), 1)), ("s5", "s5-features", 7.0)]
