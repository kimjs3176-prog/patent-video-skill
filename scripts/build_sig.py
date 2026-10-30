"""Template S — signature scenes: the technology's own subject drives the motion (in the spirit of the hand-made PAJEIN film).

The content JSON carries a `signature` block whose `type` picks the narrative and its key scenes; the frame around
it (teaser, proof, features, applications, outro) is template A's black Unpacked stage. Optional parts of the block
(route edit, path figure, probe) add or drop scenes; see CONTENT_SPEC.md for the schema.

  journey   food / process patents   route edit (a step drops out of the conventional chain) → material journey
                                     (the material changes form at each stage while a thermograph draws the conditions)
  loop      device patents           callouts land on the spec figure → the device runs on that figure (air, heat,
                                     condensate) beside its control loop → the water's path through the product figure
  sequence  primer / gene patents    the problem in numbers → primers type out their real bases and dock on the
                                     target's regions → probe check (optional) → the readout: amplification curves from
                                     the Ct tables, reaction tubes changing colour, or a multiplex gel with real band sizes

Usage: python -I tools/build_sig.py data/content/<order>-<appno>.json [...]   (needs a `signature` block)
"""
import json
import math
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build as A  # noqa: E402
from build import E, PALETTES, ROOT, fit, gtext, rgba  # noqa: E402
from icons import icon  # noqa: E402
from visuals import _dims, add_transitions, copy_figures, step_icon  # noqa: E402

MONO = '@font-face {{ font-family: "PlexMono"; src: url("assets/fonts/ref/IBMPlexMono-500.woff2") format("woff2"); font-weight: 500; }}'


def josa(word, batchim, plain_):
    """Korean particle after `word`: batchim form (이/을/은) when the last syllable has a final consonant."""
    ch = word.strip()[-1:] if word.strip() else ""
    has = "가" <= ch <= "힣" and (ord(ch) - 0xAC00) % 28 != 0
    return word + (batchim if has else plain_)


def sc(sid, pal, css, body, js, d):
    """One scene on A's stage: head + css + body + timeline (js lines)."""
    return A.head(sid, pal) + f"""
    #{sid}-eyebrow {{ left: 140px; top: 96px; }}
    #{sid}-title {{ position: absolute; left: 136px; top: 136px; font-size: 66px; font-weight: 700; letter-spacing: -0.03em; white-space: nowrap; }}
{css}
  </style>
  <div id="root" data-composition-id="{sid}" data-width="1920" data-height="1080">
    <div id="{sid}-in">
      {A.grad_defs(sid + "-lg", pal)}
{body}
    </div>
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    {A.enter(sid)}
    tl.fromTo(["#{sid}-eyebrow", "#{sid}-title"], {{ opacity: 0, filter: "blur(12px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.7, ease: "expo.out", stagger: 0.1 }}, 0.2);
{chr(10).join(js)}
    tl.to("#{sid}-in", {{ scale: 1.018, duration: {max(1.0, d - 1.0):.1f}, ease: "none" }}, 0.8);
    tl.set({{}}, {{}}, {d});
    window.__timelines["{sid}"] = tl;
  </script>
</template>
"""


def heading(sid, eyebrow, title, glow_css=""):
    return (f'      <div class="glow" id="{sid}-glow" style="{glow_css}" data-layout-ignore></div>\n'
            f'      <div id="{sid}-eyebrow" class="eyebrow">{E(eyebrow)}</div>\n      <div id="{sid}-title">{gtext(title)}</div>')


def along(var, pts):
    """JS: a function placing element `var` at progress p along a polyline (pixel points)."""
    return (f"const P_{var} = {json.dumps([[round(x), round(y)] for x, y in pts])}; "
            f"const at_{var} = (p) => {{ const P = P_{var}; const L = []; let tot = 0; "
            f"for (let i = 1; i < P.length; i++) {{ const d = Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]); L.push(d); tot += d; }} "
            f"let s = p * tot; for (let i = 0; i < L.length; i++) {{ if (s <= L[i] || i === L.length - 1) {{ const r = Math.min(1, s / L[i]); "
            f"return [P[i][0] + (P[i + 1][0] - P[i][0]) * r, P[i][1] + (P[i + 1][1] - P[i][1]) * r]; }} s -= L[i]; }} return P[P.length - 1]; }};")


def figure_box(c, fn, x, y, w, h, pad=24):
    """Place a spec figure inside a box; return the image rect and a mapper from figure fractions to stage pixels."""
    fw, fh = _dims(os.path.join(ROOT, "data", "patents", c["appno"], fn))
    s = min((w - 2 * pad) / fw, (h - 2 * pad) / fh)
    iw, ih = fw * s, fh * s
    ix, iy = x + (w - iw) / 2, y + (h - ih) / 2
    return (ix, iy, iw, ih), (lambda fx, fy: (ix + fx * iw, iy + fy * ih))


# ====================================================================== journey (food process)
def j_route(c, pal, d):
    """The conventional chain is laid out, the removed step is struck and drops away, the chain closes up."""
    a, b, cc = pal
    sg = c["signature"]
    conv = sg["conventional"]
    rm = conv.index(sg["removed"])
    fs, pad, gap = 34, 30, 64

    def width(t):
        return A.em_width(t) * fs + 2 * pad
    ws = [width(t) for t in conv]

    def xs(items):
        tot = sum(ws[i] for i in items) + gap * (len(items) - 1)
        x, out = (1920 - tot) / 2, {}
        for i in items:
            out[i] = x
            x += ws[i] + gap
        return out
    before = xs(range(len(conv)))
    after = xs([i for i in range(len(conv)) if i != rm])
    y = 520
    pills = "".join(f'<div class="rp{" rm" if i == rm else ""}" id="jr-p{i}" style="left: {before[i]:.0f}px; top: {y}px; width: {ws[i]:.0f}px">{E(t)}</div>'
                    for i, t in enumerate(conv))
    arrows = "".join(f'<div class="ra" id="jr-a{i}" style="left: {before[i] + ws[i] + 14:.0f}px; top: {y + 18}px">→</div>' for i in range(len(conv) - 1))
    body = heading("jr", "WHAT CHANGED", f'기존 공정에서 |{sg["removed"]} 단계가 빠집니다',
                   f"left: 400px; top: -200px; background: radial-gradient(circle, {rgba(b, 0.30)} 0%, rgba(0,0,0,0) 65%)") + f"""
      <div id="jr-lab" class="rl" style="top: {y - 90}px">{E(sg.get("route_label", "기존 공정"))} · {len(conv)}단계</div>
      <div id="jr-lab2" class="rl grad" style="top: {y - 90}px; opacity: 0">이 기술 · {len(conv) - 1}단계 <span style="font-weight: 600">({E(sg.get("route_note", ""))})</span></div>
      {pills}{arrows}
      <svg id="jr-strike" width="1920" height="1080" style="position: absolute; inset: 0" data-layout-ignore>
        <line x1="{before[rm] - 10:.0f}" y1="{y + 36}" x2="{before[rm] + ws[rm] + 10:.0f}" y2="{y + 36}" stroke="#ff5a5a" stroke-width="6" stroke-linecap="butt" pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="1" /></svg>
      <div id="jr-note" style="position: absolute; left: {before[rm] + ws[rm] / 2 - 250:.0f}px; width: 500px; top: {y + 100}px; text-align: center; font-size: 30px; font-weight: 700; color: #ff8a8a; white-space: nowrap">{E(sg.get("removed_note", ""))} 생략</div>"""
    css = f"""    .rp {{ position: absolute; height: 76px; border-radius: 38px; display: flex; align-items: center; justify-content: center; font-size: {fs}px; font-weight: 700;
      background: rgba(255, 255, 255, 0.06); border: 1px solid rgba(255, 255, 255, 0.16); color: #e8e8f0; white-space: nowrap; }}
    .rp.rm {{ border-color: rgba(255, 90, 90, 0.7); color: #ffb4b4; }}
    .ra {{ position: absolute; font-size: 34px; color: #6e6e82; }}
    .rl {{ position: absolute; left: 0; right: 0; text-align: center; font-size: 34px; font-weight: 700; color: #a8a8bc; }}"""
    js = [f'    tl.fromTo(".rp", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.5, ease: "expo.out", stagger: 0.14 }}, 0.6);',
          f'    tl.fromTo(".ra", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3, stagger: 0.14 }}, 0.8);',
          '    tl.fromTo("#jr-lab", { opacity: 0 }, { opacity: 1, duration: 0.5 }, 0.5);',
          f'    tl.to("#jr-p{rm}", {{ scale: 1.12, boxShadow: "0 0 40px rgba(255,90,90,0.55)", duration: 0.4, ease: "back.out(2)" }}, 2.4);',
          '    tl.to("#jr-strike line", { strokeDashoffset: 0, duration: 0.5, ease: "power2.inOut" }, 2.9);',
          '    tl.fromTo("#jr-note", { opacity: 0, y: -10 }, { opacity: 1, y: 0, duration: 0.5 }, 3.0);',
          f'    tl.to(["#jr-p{rm}", "#jr-strike", "#jr-note"], {{ y: 160, opacity: 0, rotation: 4, duration: 0.7, ease: "power3.in" }}, 4.1);',
          f'    tl.to("#jr-a{rm}", {{ opacity: 0, duration: 0.3 }}, 4.1);']
    for i in range(len(conv)):
        if i == rm:
            continue
        dx = after[i] - before[i]
        js.append(f'    tl.to("#jr-p{i}", {{ x: {dx:.0f}, duration: 0.8, ease: "expo.inOut" }}, 4.6);')
        if i < len(conv) - 1:
            js.append(f'    tl.to("#jr-a{i}", {{ x: {dx:.0f}, duration: 0.8, ease: "expo.inOut" }}, 4.6);')
    js += ['    tl.to("#jr-lab", { opacity: 0, duration: 0.3 }, 4.7);', '    tl.to("#jr-lab2", { opacity: 1, duration: 0.5 }, 5.0);',
           f'    tl.to(".rp:not(.rm)", {{ borderColor: "{rgba(b, 0.8)}", background: "{rgba(b, 0.14)}", duration: 0.5, stagger: 0.06 }}, 5.2);']
    return sc("jr", pal, css, body, js, d)


def material(key, a, b, cc, name=""):
    """A small illustration of the material at one stage (SVG 560×440, drawn in place)."""
    if key == "puff":
        grains = "".join(f'<ellipse class="gr0" cx="{150 + (i % 6) * 52}" cy="{250 + (i // 6) * 46}" rx="16" ry="9" fill="#efe6d2" />' for i in range(18))
        puffs = "".join(f'<path class="gr1" transform="translate({150 + (i % 6) * 52} {250 + (i // 6) * 46})" d="M-22 4 C-26 -14 -10 -24 2 -18 C14 -26 28 -12 22 2 C30 14 12 26 0 18 C-12 26 -30 16 -22 4 Z" fill="#fff6e4" stroke="{a}" stroke-width="2" opacity="0" />' for i in range(18))
        gauge = (f'<g transform="translate(450 110)"><circle r="62" fill="none" stroke="rgba(255,255,255,0.18)" stroke-width="10" />'
                 f'<path d="M -44 44 A 62 62 0 1 1 44 44" fill="none" stroke="url(#jj-lg)" stroke-width="10" stroke-linecap="round" />'
                 f'<line id="jj-needle" x1="0" y1="0" x2="0" y2="-48" stroke="#fff" stroke-width="6" stroke-linecap="round" transform="rotate(-130)" /><circle r="8" fill="#fff" /></g>')
        return grains + puffs + gauge
    if key == "mash":
        bubbles = "".join(f'<circle class="bb" cx="{170 + i * 40}" cy="330" r="{6 + i % 3 * 2}" fill="none" stroke="rgba(255,255,255,0.7)" stroke-width="3" />' for i in range(6))
        malt = "".join(f'<ellipse class="ml" cx="{190 + i * 36}" cy="40" rx="11" ry="7" fill="{a}" />' for i in range(6))
        return (f'<path d="M110 150 L450 150 L420 400 Q280 430 140 400 Z" fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.5)" stroke-width="5" />'
                f'<path id="jj-liq" d="M128 230 Q200 210 280 230 T432 230 L418 392 Q280 420 142 392 Z" fill="{rgba(a, 0.55)}" />{bubbles}{malt}')
    if key == "boil":
        steam = "".join(f'<path class="st" d="M{200 + i * 70} 140 C {180 + i * 70} 110, {230 + i * 70} 90, {205 + i * 70} 50" fill="none" stroke="rgba(255,255,255,0.6)" stroke-width="5" stroke-linecap="round" />' for i in range(3))
        hop = ('<g id="jj-hop" transform="translate(280 60)">' + "".join(f'<ellipse cx="0" cy="{k * 14}" rx="{20 - k * 3}" ry="12" fill="#9ccc65" stroke="#2e5a1c" stroke-width="2" />' for k in range(5)) + '</g>')
        return (f'<rect x="120" y="170" width="320" height="230" rx="34" fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.5)" stroke-width="5" />'
                f'<rect x="138" y="230" width="284" height="152" rx="22" fill="{rgba(cc, 0.6)}" /><rect x="100" y="160" width="360" height="22" rx="11" fill="rgba(255,255,255,0.4)" />'
                f'<path d="M150 420 L410 420" stroke="#ff7a3c" stroke-width="10" stroke-linecap="round" />{steam}{hop}')
    if key == "ferment":
        bubbles = "".join(f'<circle class="co" cx="{220 + (i % 5) * 32}" cy="{380 - (i // 5) * 40}" r="{5 + i % 3 * 2}" fill="rgba(255,255,255,0.75)" />' for i in range(15))
        yeast = "".join(f'<circle class="ys" cx="{210 + (i * 37) % 150}" cy="{250 + (i * 53) % 120}" r="9" fill="{b}" />' for i in range(8))
        return (f'<rect x="180" y="60" width="200" height="360" rx="60" fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.5)" stroke-width="5" />'
                f'<rect x="196" y="150" width="168" height="254" rx="44" fill="{rgba(a, 0.45)}" />{yeast}{bubbles}'
                f'<path d="M280 60 L280 20 L330 20" fill="none" stroke="rgba(255,255,255,0.5)" stroke-width="6" />')
    if key == "cold":
        flakes = "".join(f'<g class="fl" transform="translate({150 + i * 64} {64 + (i % 2) * 20}) scale(0.8)">' + icon("snow", 46, "#bfe6ff", 6) + '</g>' for i in range(4))
        glass = ('<g id="jj-glass" transform="translate(360 150)" opacity="0"><path d="M0 0 L120 0 L104 250 Q60 262 16 250 Z" fill="rgba(255,255,255,0.08)" stroke="#fff" stroke-width="5" />'
                 f'<path id="jj-beer" d="M10 60 L110 60 L98 244 Q60 254 22 244 Z" fill="{a}" />'
                 '<path id="jj-foam" d="M4 30 Q20 10 40 26 Q60 6 80 24 Q100 8 116 30 L110 64 L10 64 Z" fill="#fffaf0" /></g>')
        return (f'<rect x="100" y="150" width="220" height="270" rx="30" fill="rgba(160,210,255,0.08)" stroke="rgba(190,225,255,0.7)" stroke-width="5" />'
                f'<rect x="118" y="210" width="184" height="192" rx="18" fill="{rgba(a, 0.5)}" />{flakes}{glass}')
    vessel = 'fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.5)" stroke-width="5"'
    flame = "".join(f'<path class="fm" d="M{200 + i * 80} 432 C {184 + i * 80} 410, {204 + i * 80} 392, {200 + i * 80} 372 C {222 + i * 80} 394, {218 + i * 80} 414, {200 + i * 80} 432 Z" fill="#ff7a3c" />' for i in range(3))
    if key == "soak":
        items = "".join(f'<ellipse class="sk" cx="{190 + i * 60}" cy="{300 + (i % 2) * 34}" rx="24" ry="13" fill="#efe1c0" stroke="{a}" stroke-width="2" />' for i in range(4))
        ripples = "".join(f'<ellipse class="rq" cx="{220 + i * 110}" cy="232" rx="40" ry="9" fill="none" stroke="rgba(255,255,255,0.6)" stroke-width="3" opacity="0" />' for i in range(2))
        return (f'<path d="M100 200 L460 200 Q450 400 280 410 Q110 400 100 200 Z" {vessel} />'
                f'<path d="M112 232 L448 232 Q436 390 280 398 Q124 390 112 232 Z" fill="{rgba(b, 0.42)}" />{items}{ripples}')
    if key == "cut":
        slices = "".join(f'<rect class="cs" x="{170 + i * 44}" y="250" width="38" height="96" rx="10" fill="#efe1c0" stroke="{a}" stroke-width="2" />' for i in range(5))
        return (f'<rect x="90" y="350" width="380" height="40" rx="14" fill="rgba(255,255,255,0.10)" stroke="rgba(255,255,255,0.4)" stroke-width="3" />{slices}'
                f'<g class="kn"><path d="M300 60 L320 60 L320 230 L300 250 Z" fill="#dfe6ee" /><rect x="296" y="10" width="28" height="56" rx="8" fill="{cc}" /></g>')
    if key == "steam":
        steam = "".join(f'<path class="st" d="M{200 + i * 80} 150 C {180 + i * 80} 120, {230 + i * 80} 100, {205 + i * 80} 60" fill="none" stroke="rgba(255,255,255,0.6)" stroke-width="5" stroke-linecap="round" />' for i in range(3))
        items = "".join(f'<ellipse class="si" cx="{190 + i * 60}" cy="228" rx="24" ry="13" fill="#efe1c0" stroke="{a}" stroke-width="2" />' for i in range(4))
        return (f'<rect x="120" y="300" width="320" height="100" rx="26" {vessel} /><rect x="138" y="330" width="284" height="56" rx="18" fill="{rgba(b, 0.4)}" />'
                f'<rect x="110" y="190" width="340" height="96" rx="20" {vessel} />'
                + "".join(f'<line x1="{150 + k * 40}" y1="270" x2="{150 + k * 40}" y2="286" stroke="rgba(255,255,255,0.4)" stroke-width="4" />' for k in range(7))
                + f'<path d="M110 180 Q280 120 450 180 Z" fill="rgba(255,255,255,0.18)" stroke="rgba(255,255,255,0.5)" stroke-width="4" />{items}{steam}')
    if key == "heat":
        bubbles = "".join(f'<circle class="hb" cx="{180 + i * 44}" cy="360" r="{6 + i % 3 * 2}" fill="none" stroke="rgba(255,255,255,0.7)" stroke-width="3" />' for i in range(6))
        return (f'<rect x="120" y="150" width="320" height="230" rx="34" {vessel} />'
                f'<rect x="138" y="210" width="284" height="152" rx="22" fill="{rgba(a, 0.5)}" /><rect x="100" y="140" width="360" height="22" rx="11" fill="rgba(255,255,255,0.4)" />'
                f'{bubbles}{flame}')
    if key == "dry":
        sl = "".join(f'<ellipse class="ds" cx="{170 + (i % 4) * 74}" cy="{220 + (i // 4) * 110}" rx="28" ry="16" fill="#e8cfa0" stroke="{a}" stroke-width="2" />' for i in range(8))
        waves = "".join(f'<path class="wv" d="M40 {176 + k * 110} q 22 -16 44 0 t 44 0 t 44 0" fill="none" stroke="#ff9a5c" stroke-width="4" stroke-linecap="round" opacity="0" />' for k in range(3))
        racks = "".join(f'<line x1="120" y1="{244 + k * 110}" x2="460" y2="{244 + k * 110}" stroke="rgba(255,255,255,0.45)" stroke-width="5" />' for k in range(2))
        return f'<rect x="110" y="140" width="360" height="270" rx="24" {vessel} />{racks}{sl}{waves}'
    if key == "roast":
        beans = "".join(f'<ellipse class="bn" cx="{200 + i * 40}" cy="{326 - (i % 2) * 10}" rx="16" ry="11" fill="#c98b4a" stroke="#6b3d16" stroke-width="2" />' for i in range(5))
        return (f'<path d="M120 300 Q280 400 440 300 Z" {vessel} /><line x1="440" y1="300" x2="540" y2="270" stroke="rgba(255,255,255,0.6)" stroke-width="12" stroke-linecap="round" />'
                f'{beans}{flame}')
    if key == "fry":
        bubbles = "".join(f'<circle class="ob" cx="{170 + i * 44}" cy="370" r="{5 + i % 3 * 2}" fill="rgba(255,240,180,0.85)" />' for i in range(7))
        strips = "".join(f'<rect class="fr" x="{200 + i * 40}" y="120" width="22" height="120" rx="6" fill="#f2cc60" stroke="#a8741a" stroke-width="2" />' for i in range(4))
        return (f'<rect x="110" y="180" width="340" height="220" rx="30" {vessel} />'
                f'<rect x="128" y="240" width="304" height="144" rx="20" fill="rgba(242,180,60,0.55)" />{strips}{bubbles}{flame}')
    if key == "freeze":
        flakes = "".join(f'<g transform="translate({140 + i * 80} {70 + (i % 2) * 24}) scale(0.8)"><g class="fl">' + icon("snow", 46, "#bfe6ff", 6) + '</g></g>' for i in range(4))
        items = "".join(f'<ellipse cx="{200 + i * 56}" cy="300" rx="22" ry="13" fill="#efe1c0" stroke="{a}" stroke-width="2" />' for i in range(4))
        return (f'<rect x="120" y="170" width="320" height="240" rx="28" fill="rgba(160,210,255,0.08)" stroke="rgba(190,225,255,0.7)" stroke-width="5" />'
                f'{items}<rect class="fo" x="134" y="184" width="292" height="212" rx="20" fill="rgba(190,230,255,0.5)" opacity="0" />{flakes}')
    if key == "mix":
        dots = "".join(f'<circle class="mp" cx="{280 + 90 * math.cos(i * 0.9):.0f}" cy="{310 + 34 * math.sin(i * 0.9):.0f}" r="9" fill="{b if i % 2 else cc}" />' for i in range(7))
        return (f'<path d="M100 220 L460 220 Q450 410 280 416 Q110 410 100 220 Z" {vessel} />'
                f'<path d="M114 250 L446 250 Q434 398 280 404 Q126 398 114 250 Z" fill="{rgba(a, 0.42)}" />{dots}'
                f'<g class="mx"><line x1="280" y1="40" x2="280" y2="300" stroke="#dfe6ee" stroke-width="8" stroke-linecap="round" /><ellipse cx="280" cy="300" rx="34" ry="14" fill="none" stroke="#dfe6ee" stroke-width="6" /></g>')
    if key in ("extract", "filter"):
        drops = "".join(f'<path class="dp" d="M280 262 C 272 274, 272 284, 280 288 C 288 284, 288 274, 280 262 Z" fill="{b}" opacity="0" />' for _ in range(4))
        return (f'<rect x="170" y="40" width="220" height="110" rx="18" {vessel} /><rect x="186" y="80" width="188" height="56" rx="12" fill="#c9a36a" />'
                f'<path d="M150 160 L410 160 L300 250 L260 250 Z" {vessel} /><line x1="170" y1="176" x2="390" y2="176" stroke="rgba(255,255,255,0.5)" stroke-width="3" stroke-dasharray="8 8" />'
                f'<rect x="190" y="300" width="180" height="120" rx="16" {vessel} /><rect class="lq" x="204" y="330" width="152" height="80" rx="10" fill="{rgba(b, 0.55)}" />{drops}')
    return f'<g transform="translate(130 70)">{icon(step_icon(name), 300, "url(#jj-lg)", 3)}</g>'


def trange(t):
    """[lo, hi] ℃ as text; '~' when a bound is negative so the dash does not read as a minus."""
    lo, hi = t
    if lo == hi:
        return f"{lo}℃"
    return f"{lo}~{hi}℃" if lo < 0 or hi < 0 else f"{lo}–{hi}℃"


def j_journey(c, pal, d):
    """The material changes form stage by stage; a thermograph of the stated temperature ranges draws underneath."""
    a, b, cc = pal
    sg = c["signature"]
    st = sg["stages"]
    n = len(st)
    T = [round(0.9 + i * ((d - 2.6) / n), 2) for i in range(n)]
    span = (d - 2.6) / n
    art = "".join(f'<svg class="jm" id="jj-m{i}" width="560" height="440" viewBox="0 0 560 440" style="position: absolute; left: 190px; top: 262px; width: 560px; height: 440px; opacity: 0">{material(s.get("key", ""), a, b, cc, s["n"])}</svg>'
                  for i, s in enumerate(st))
    # thermograph: bands for each stated range, a line through their middles
    x0, x1, yb, yt = 220, 1700, 945, 790
    cx = [x0 + (x1 - x0) * (i + 0.5) / n for i in range(n)]

    temps = [v for s in st if s.get("t") for v in s["t"]]
    lo_t, hi_t = min([0] + temps), max([100] + temps)
    pad_t = (hi_t - lo_t) * 0.08

    def ty(t):  # the stated range of this process onto the strip
        return yb - (yb - yt) * (t - lo_t + pad_t) / (hi_t - lo_t + 2 * pad_t)
    lw = min(260, (x1 - x0) / n - 12)
    bands, mids, labels = "", [], ""
    for i, s in enumerate(st):
        if s.get("t"):
            lo, hi = s["t"]
            bands += f'<rect class="tb" id="jj-b{i}" x="{cx[i] - 70:.0f}" y="{ty(hi):.0f}" width="140" height="{ty(lo) - ty(hi):.0f}" rx="10" fill="{rgba(b, 0.28)}" stroke="{rgba(b, 0.7)}" stroke-width="2" />'
            mids.append((cx[i], ty((lo + hi) / 2)))
            lab = trange(s["t"])
        else:
            mids.append((cx[i], ty(max(lo_t, min(hi_t, 25)))))
            lab = s.get("label", "")
        labels += f'<div class="tl" id="jj-l{i}" style="left: {cx[i] - lw / 2:.0f}px; width: {lw:.0f}px; top: {yb + 8:.0f}px">{E(s["n"])}<b>{E(lab)}</b></div>'
    path = "M" + " L".join(f"{x:.0f} {y:.0f}" for x, y in mids)
    vals = [trange(s["t"]) if s.get("t") else s.get("label", "") for s in st]
    cards = "".join(f'<div class="jc" id="jj-c{i}"><div class="k">STAGE {i + 1:02d} / {n:02d}</div><div class="n" style="font-size: {fit(s["n"], 60, 720)}px">{E(s["n"])}</div>'
                    f'<div class="v grad" style="font-size: {fit(vals[i], 120, 680)}px">{E(vals[i])}</div><div class="s">{E(s["cond"])}</div></div>'
                    for i, s in enumerate(st))
    body = heading("jj", "MATERIAL JOURNEY", sg.get("title") or f'원료가 |{josa(sg.get("product", "제품"), "이", "가")} 되기까지',
                   f"left: 0px; top: 0px; background: radial-gradient(circle, {rgba(a, 0.26)} 0%, rgba(0,0,0,0) 65%)") + f"""
      {art}
      <div id="jj-prod" class="grad" style="position: absolute; left: 190px; width: 560px; top: 708px; text-align: center; font-size: 40px; font-weight: 800; white-space: nowrap; opacity: 0">{E(sg.get("product", ""))} 완성</div>
      {cards}
      <svg width="1920" height="1080" style="position: absolute; inset: 0" data-layout-ignore>
        <line x1="{x0 - 40}" y1="{yb}" x2="{x1 + 40}" y2="{yb}" stroke="rgba(255,255,255,0.2)" stroke-width="2" />
        {bands}
        <path id="jj-line" d="{path}" fill="none" stroke="url(#jj-lg)" stroke-width="5" stroke-linecap="butt" stroke-linejoin="round" pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="1" />
      </svg>
      <div id="jj-dot" style="position: absolute; left: -14px; top: -14px; width: 28px; height: 28px; border-radius: 50%; background: #fff; box-shadow: 0 0 24px {a}" data-layout-ignore></div>
      {labels}
      <div style="position: absolute; right: {1920 - x1 - 40}px; top: {yt - 40}px; font-size: 28px; color: #8e8ea3">온도 조건(명세서) ℃</div>"""
    css = f"""    .jc {{ position: absolute; left: 1040px; top: 270px; width: 720px; opacity: 0; }}
    .jc .k {{ font-size: 28px; font-weight: 600; letter-spacing: 0.3em; color: #a8a8bc; }}
    .jc .n {{ font-size: 60px; font-weight: 800; margin-top: 16px; letter-spacing: -0.03em; white-space: nowrap; }}
    .jc .v {{ font-weight: 800; margin-top: 10px; line-height: 1.05; letter-spacing: -0.03em; white-space: nowrap; }}
    .jc .s {{ font-size: 34px; color: #a8a8bc; margin-top: 18px; line-height: 1.35; word-break: keep-all; }}
    .tl {{ position: absolute; text-align: center; font-size: 28px; color: #8e8ea3; white-space: nowrap; }}
    .tl b {{ display: block; color: #e8e8f0; font-weight: 700; }}"""
    js = [along("dot", mids), '    const dot = document.querySelector("#jj-dot"); const o = { p: 0 };',
          f'    const put = () => {{ const q = at_dot(o.p); dot.style.transform = "translate(" + q[0] + "px," + q[1] + "px)"; }}; put();',
          f'    tl.to("#jj-line", {{ strokeDashoffset: 0, duration: {T[-1] - T[0] + 0.6:.2f}, ease: "none" }}, {T[0]:.2f});',
          f'    tl.to(o, {{ p: 1, duration: {T[-1] - T[0] + 0.6:.2f}, ease: "none", onUpdate: put }}, {T[0]:.2f});',
          '    tl.fromTo("#jj-dot", { opacity: 0 }, { opacity: 1, duration: 0.3 }, ' + f'{T[0]:.2f});',
          '    tl.fromTo(".tl", { opacity: 0 }, { opacity: 0.45, duration: 0.4 }, 0.3);']
    for i, s in enumerate(st):
        t = T[i]
        js += [f'    tl.fromTo("#jj-m{i}", {{ opacity: 0, scale: 0.9 }}, {{ opacity: 1, scale: 1, duration: 0.6, ease: "expo.out" }}, {t:.2f});',
               f'    tl.fromTo("#jj-c{i}", {{ opacity: 0, x: 40 }}, {{ opacity: 1, x: 0, duration: 0.6, ease: "expo.out" }}, {t:.2f});',
               f'    tl.to("#jj-l{i}", {{ opacity: 1, duration: 0.3 }}, {t:.2f});']
        if s.get("t"):
            js.append(f'    tl.fromTo("#jj-b{i}", {{ scaleY: 0, transformOrigin: "50% 100%" }}, {{ scaleY: 1, duration: 0.6, ease: "expo.out" }}, {t:.2f});')
        if i < n - 1:
            js += [f'    tl.to("#jj-m{i}", {{ opacity: 0, scale: 1.08, duration: 0.45, ease: "power2.in" }}, {t + span - 0.35:.2f});',
                   f'    tl.to("#jj-c{i}", {{ opacity: 0, x: -30, duration: 0.35, ease: "power2.in" }}, {t + span - 0.3:.2f});',
                   f'    tl.to("#jj-l{i}", {{ opacity: 0.45, duration: 0.3 }}, {t + span - 0.1:.2f});']
        k = s.get("key", "")
        if k == "puff":
            js += [f'    tl.to("#jj-m{i} .gr0", {{ opacity: 0, scale: 0.4, transformOrigin: "50% 50%", duration: 0.4, stagger: 0.03 }}, {t + 1.0:.2f});',
                   f'    tl.fromTo("#jj-m{i} .gr1", {{ opacity: 0, scale: 0.3, transformOrigin: "50% 50%" }}, {{ opacity: 1, scale: 1, duration: 0.5, ease: "back.out(2.4)", stagger: 0.03 }}, {t + 1.05:.2f});',
                   f'    tl.to("#jj-needle", {{ rotation: 60, svgOrigin: "0 0", duration: 1.0, ease: "power2.out" }}, {t + 0.4:.2f});']
        elif k == "mash":
            js += [f'    tl.fromTo("#jj-m{i} .ml", {{ y: 0, opacity: 1 }}, {{ y: 220, opacity: 0, duration: 1.0, ease: "power1.in", stagger: 0.12 }}, {t + 0.3:.2f});',
                   f'    tl.fromTo("#jj-m{i} .bb", {{ y: 0, opacity: 0 }}, {{ y: -120, opacity: 1, duration: 1.2, ease: "none", stagger: {{ each: 0.18, repeat: 1 }} }}, {t + 0.8:.2f});']
        elif k == "boil":
            js += [f'    tl.fromTo("#jj-hop", {{ y: -60, opacity: 0 }}, {{ y: 130, opacity: 1, duration: 1.0, ease: "bounce.out" }}, {t + 0.4:.2f});',
                   f'    tl.fromTo("#jj-m{i} .st", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: -10, duration: 0.9, ease: "sine.out", stagger: {{ each: 0.2, repeat: 2, yoyo: true }} }}, {t + 0.3:.2f});']
        elif k == "ferment":
            js += [f'    tl.fromTo("#jj-m{i} .co", {{ y: 0, opacity: 0 }}, {{ y: -200, opacity: 1, duration: 1.4, ease: "none", stagger: {{ each: 0.08, repeat: 1 }} }}, {t + 0.3:.2f});',
                   f'    tl.to("#jj-m{i} .ys", {{ x: 6, duration: 0.4, ease: "sine.inOut", yoyo: true, repeat: 5, stagger: 0.05 }}, {t + 0.3:.2f});']
        elif k == "cold":
            js += [f'    tl.fromTo("#jj-m{i} .fl", {{ opacity: 0, y: -30 }}, {{ opacity: 1, y: 0, duration: 0.6, stagger: 0.15 }}, {t + 0.3:.2f});',
                   f'    tl.to("#jj-glass", {{ opacity: 1, duration: 0.5 }}, {t + 1.3:.2f});',
                   f'    tl.fromTo("#jj-beer", {{ scaleY: 0, transformOrigin: "50% 100%" }}, {{ scaleY: 1, duration: 1.0, ease: "power2.out" }}, {t + 1.4:.2f});',
                   f'    tl.fromTo("#jj-foam", {{ y: 180, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 1.0, ease: "power2.out" }}, {t + 1.5:.2f});',
]
        elif k == "soak":
            js += [f'    tl.fromTo("#jj-m{i} .sk", {{ y: -170, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.7, ease: "bounce.out", stagger: 0.18 }}, {t + 0.3:.2f});',
                   f'    tl.fromTo("#jj-m{i} .rq", {{ opacity: 0.8, scale: 0.4, transformOrigin: "50% 50%" }}, {{ opacity: 0, scale: 1.6, duration: 1.0, ease: "power1.out", stagger: {{ each: 0.35, repeat: 2 }} }}, {t + 0.6:.2f});']
        elif k == "cut":
            js += [f'    tl.fromTo("#jj-m{i} .kn", {{ y: -40 }}, {{ y: 30, duration: 0.25, ease: "power2.in", yoyo: true, repeat: 5 }}, {t + 0.3:.2f});',
                   f'    tl.fromTo("#jj-m{i} .cs", {{ x: 0 }}, {{ x: (k) => (k - 2) * 16, duration: 0.6, ease: "expo.out" }}, {t + 1.6:.2f});']
        elif k == "steam":
            js += [f'    tl.fromTo("#jj-m{i} .st", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: -10, duration: 0.9, ease: "sine.out", stagger: {{ each: 0.2, repeat: 2, yoyo: true }} }}, {t + 0.3:.2f});',
                   f'    tl.to("#jj-m{i} .si", {{ fill: "#d9a35c", duration: 1.6, stagger: 0.1 }}, {t + 0.6:.2f});']
        elif k == "heat":
            js += [f'    tl.fromTo("#jj-m{i} .fm", {{ scaleY: 0.7, transformOrigin: "50% 100%" }}, {{ scaleY: 1.15, duration: 0.3, ease: "sine.inOut", yoyo: true, repeat: 7, stagger: 0.1 }}, {t + 0.2:.2f});',
                   f'    tl.fromTo("#jj-m{i} .hb", {{ y: 0, opacity: 0 }}, {{ y: -130, opacity: 1, duration: 1.1, ease: "none", stagger: {{ each: 0.16, repeat: 1 }} }}, {t + 0.6:.2f});']
        elif k == "dry":
            js += [f'    tl.fromTo("#jj-m{i} .wv", {{ x: 0, opacity: 0 }}, {{ x: 330, opacity: 1, duration: 1.2, ease: "none", stagger: {{ each: 0.3, repeat: 1 }} }}, {t + 0.3:.2f});',
                   f'    tl.to("#jj-m{i} .ds", {{ scale: 0.82, fill: "#c99a5a", transformOrigin: "50% 50%", duration: 1.6, stagger: 0.05 }}, {t + 0.6:.2f});']
        elif k == "roast":
            js += [f'    tl.fromTo("#jj-m{i} .bn", {{ y: 0 }}, {{ y: -46, duration: 0.3, ease: "power1.out", yoyo: true, repeat: 5, stagger: 0.07 }}, {t + 0.3:.2f});',
                   f'    tl.to("#jj-m{i} .bn", {{ fill: "#7a4a22", duration: 1.6 }}, {t + 0.4:.2f});',
                   f'    tl.fromTo("#jj-m{i} .fm", {{ scaleY: 0.7, transformOrigin: "50% 100%" }}, {{ scaleY: 1.15, duration: 0.3, ease: "sine.inOut", yoyo: true, repeat: 7 }}, {t + 0.2:.2f});']
        elif k == "fry":
            js += [f'    tl.fromTo("#jj-m{i} .fr", {{ y: -40 }}, {{ y: 150, duration: 0.8, ease: "power2.out", stagger: 0.12 }}, {t + 0.3:.2f});',
                   f'    tl.to("#jj-m{i} .fr", {{ fill: "#d79a2a", duration: 1.2 }}, {t + 1.0:.2f});',
                   f'    tl.fromTo("#jj-m{i} .ob", {{ y: 0, opacity: 0 }}, {{ y: -110, opacity: 1, duration: 0.7, ease: "none", stagger: {{ each: 0.1, repeat: 2 }} }}, {t + 0.9:.2f});']
        elif k == "freeze":
            js += [f'    tl.fromTo("#jj-m{i} .fl", {{ opacity: 0, y: -30 }}, {{ opacity: 1, y: 0, duration: 0.6, stagger: 0.15 }}, {t + 0.3:.2f});',
                   f'    tl.to("#jj-m{i} .fo", {{ opacity: 1, duration: 1.4, ease: "power1.inOut" }}, {t + 0.8:.2f});']
        elif k == "mix":
            js += [f'    tl.fromTo("#jj-m{i} .mx", {{ rotation: -14, svgOrigin: "280 40" }}, {{ rotation: 14, svgOrigin: "280 40", duration: 0.35, ease: "sine.inOut", yoyo: true, repeat: 5 }}, {t + 0.3:.2f});',
                   f'    tl.to("#jj-m{i} .mp", {{ x: (k) => (k % 2 ? 30 : -30), y: (k) => (k % 3 - 1) * 12, duration: 0.5, ease: "sine.inOut", yoyo: true, repeat: 3, stagger: 0.05 }}, {t + 0.4:.2f});']
        elif k in ("extract", "filter"):
            js += [f'    tl.fromTo("#jj-m{i} .dp", {{ y: 0, opacity: 0 }}, {{ y: 70, opacity: 1, duration: 0.5, ease: "power2.in", stagger: {{ each: 0.3, repeat: 1 }} }}, {t + 0.4:.2f});',
                   f'    tl.fromTo("#jj-m{i} .lq", {{ scaleY: 0.3, transformOrigin: "50% 100%" }}, {{ scaleY: 1, duration: 2.0, ease: "power1.out" }}, {t + 0.5:.2f});']
        if i == n - 1:
            js.append(f'    tl.fromTo("#jj-prod", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.6 }}, {t + (2.2 if k == "cold" else 1.6):.2f});')
    return sc("jj", pal, css, body, js, d)


# ====================================================================== loop (device)
def plate(c, fn, sid, x, y, w, h):
    rect, m = figure_box(c, fn, x, y, w, h)
    ix, iy, iw, ih = rect
    html = (f'<div class="fp" id="{sid}-plate" style="left: {x}px; top: {y}px; width: {w}px; height: {h}px"></div>'
            f'<img id="{sid}-img" src="assets/fig/{E(fn)}" alt="명세서 도면" style="position: absolute; left: {ix:.0f}px; top: {iy:.0f}px; width: {iw:.0f}px; height: {ih:.0f}px" />')
    return html, m


FIG_CSS = """    .fp { position: absolute; border-radius: 28px; background: #fff; box-shadow: 0 30px 90px rgba(0, 0, 0, 0.5); }
    .cd { position: absolute; width: 30px; height: 30px; margin: -15px 0 0 -15px; border-radius: 50%; border: 5px solid #fff; box-shadow: 0 0 0 6px rgba(0,0,0,0.25); }
    .cr { position: absolute; display: grid; grid-template-columns: 74px 1fr; align-items: center; left: 1060px; width: 720px; height: 112px; border-radius: 22px; padding: 0 24px; opacity: 0.35; }
    .cr b { width: 58px; height: 58px; border-radius: 50%; font-size: 30px; display: flex; align-items: center; justify-content: center; color: #000; font-weight: 800; }
    .cr .n { font-size: 38px; font-weight: 700; white-space: nowrap; }
    .cr .s { font-size: 28px; color: #a8a8bc; white-space: nowrap; margin-top: 2px; }
    .cap { position: absolute; font-size: 28px; color: #8e8ea3; white-space: nowrap; }"""


def l_parts(c, pal, d):
    """Callouts land on the spec figure one by one; a leader line ties each to its row."""
    a, b, cc = pal
    sg = c["signature"]
    co = sg["callouts"]
    pl, m = plate(c, sg["figure"], "lp", 120, 230, 840, 760)
    n = len(co)
    rows, dots, lines = "", "", ""
    top0 = 560 - n * 124 / 2 + 60
    for i, p in enumerate(co):
        px, py = m(p["x"], p["y"])
        ry = top0 + i * 124
        rows += (f'<div class="cr" id="lp-r{i}" style="top: {ry:.0f}px"><b style="background: linear-gradient(135deg, {a}, {cc})">{E(p["ref"])}</b>'
                 f'<div><div class="n">{E(p["n"])}</div><div class="s">{E(p["d"])}</div></div></div>')
        dots += f'<div class="cd" id="lp-d{i}" style="left: {px:.0f}px; top: {py:.0f}px; background: {b}"></div>'
        lines += f'<path id="lp-l{i}" d="M{px:.0f} {py:.0f} C {px + 160:.0f} {py:.0f}, {1000:.0f} {ry + 56:.0f}, 1060 {ry + 56:.0f}" fill="none" stroke="{b}" stroke-width="3" pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="1" opacity="0.8" />'
    body = heading("lp", "ANATOMY", sg.get("parts_title") or f'{c["sub"]}의 |구성',
                   f"left: 900px; top: -300px; background: radial-gradient(circle, {rgba(b, 0.28)} 0%, rgba(0,0,0,0) 65%)") + f"""
      {pl}
      <svg width="1920" height="1080" style="position: absolute; inset: 0" data-layout-ignore>{lines}</svg>
      {dots}{rows}
      <div class="cap" style="left: 140px; top: 1004px">{E(sg.get("figcap", ""))} · 부호는 도면 번호</div>"""
    step = (d - 2.2) / n
    js = ['    tl.fromTo(["#lp-plate", "#lp-img"], { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 0.8, ease: "expo.out" }, 0.3);',
          f'    tl.fromTo("#lp-img", {{ scale: 1.04 }}, {{ scale: 1, duration: {d - 0.5:.1f}, ease: "power1.out" }}, 0.3);']
    for i in range(n):
        t = 1.1 + i * step
        js += [f'    tl.fromTo("#lp-d{i}", {{ scale: 0 }}, {{ scale: 1, duration: 0.5, ease: "back.out(3)" }}, {t:.2f});',
               f'    tl.to("#lp-l{i}", {{ strokeDashoffset: 0, duration: 0.6, ease: "power2.inOut" }}, {t + 0.15:.2f});',
               f'    tl.to("#lp-r{i}", {{ opacity: 1, background: "{rgba(b, 0.14)}", duration: 0.4 }}, {t + 0.45:.2f});']
        if i:
            js += [f'    tl.to("#lp-r{i - 1}", {{ background: "rgba(0,0,0,0)", opacity: 0.75, duration: 0.4 }}, {t + 0.45:.2f});',
                   f'    tl.to("#lp-l{i - 1}", {{ opacity: 0.25, duration: 0.4 }}, {t + 0.45:.2f});']
    return sc("lp", pal, FIG_CSS, body, js, d)


FLOW = {"air": "#5ccfff", "water": "#2aa7e6", "heat": "#ff8a4c", "cold": "#7fd6ff", "gas": "#7d8aa3", "uv": "#b388ff",
        "light": "#ffe066", "solid": "#d9b38c", "power": "#ffd23f"}
GLOW = {"air": "80,200,255", "water": "60,170,240", "heat": "255,120,60", "cold": "80,200,255", "gas": "190,200,215",
        "uv": "170,120,255", "light": "255,224,102", "solid": "220,180,140", "power": "255,210,63"}


def plen(pts):
    return sum(math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]) for i in range(1, len(pts)))


def l_run(c, pal, d):
    """The device runs on its own figure: particles of each medium travel their real path, active zones glow, and
    beside it either the control loop the claims describe or the steps of one cycle."""
    a, b, cc = pal
    sg = c["signature"]
    rn = sg["run"]
    pl, m = plate(c, rn.get("figure") or sg["figure"], "lr", 120, 230, 840, 760)
    flows = rn.get("flows", [])
    paths = [[m(x, y) for x, y in f["pts"]] for f in flows]
    per = 5
    parts, lines, glows = "", "", ""
    for fi, f in enumerate(flows):
        col = FLOW.get(f.get("color"), b)
        sz = 22 if f.get("color") in ("gas", "solid") else 16
        rad = "28%" if f.get("color") == "solid" else "50%"
        for k in range(per):
            parts += (f'<i class="pf" id="lr-f{fi}-{k}" style="left: {-sz / 2:.0f}px; top: {-sz / 2:.0f}px; width: {sz}px; height: {sz}px; '
                      f'border-radius: {rad}; background: {col}; border: 2px solid rgba(0,0,0,0.35); box-shadow: 0 0 14px {col}"></i>')
        lines += (f'<path class="lr-fl" d="M' + " L".join(f"{x:.0f} {y:.0f}" for x, y in paths[fi]) +
                  f'" fill="none" stroke="{col}" stroke-width="4" stroke-dasharray="3 12" stroke-linecap="round" opacity="0" />')
    for gi, g in enumerate(rn.get("glows", [])):
        if "ref" in g:
            cp = next((q for q in sg["callouts"] if q["ref"] == g["ref"]), sg["callouts"][0])
            gx, gy = m(cp["x"], cp["y"])
        elif "at_flow" in g:
            gx, gy = paths[g["at_flow"]][1]
        else:
            gx, gy = m(g["x"], g["y"])
        rgb = GLOW.get(g.get("color"), "255,255,255")
        glows += (f'<div class="lr-gl" id="lr-g{gi}" style="position: absolute; left: {gx - 170:.0f}px; top: {gy - 220:.0f}px; width: 340px; height: 440px; '
                  f'border-radius: 50%; background: radial-gradient(ellipse, rgba({rgb},0.5), rgba({rgb},0) 70%); opacity: 0" data-layout-ignore></div>')
    drips = 0
    if rn.get("drip"):
        dx, dy = m(*rn["drip"])
        drips = 4 * max(1, int((d - 3.6) / 5.2))
        for k in range(drips):
            parts += f'<i class="pd" id="lr-w{k}" style="left: {dx - 9:.0f}px; top: {dy:.0f}px"></i>'
    legend, seen = [], set()
    for f in flows:
        if f.get("legend", True) and f["label"] not in seen:
            seen.add(f["label"])
            legend.append(f'<span style="color: {FLOW.get(f.get("color"), b)}">●</span> {E(f["label"])}')
    if rn.get("drip"):
        legend.append(f'<span style="color: #8fd8ff">●</span> {E(rn.get("drip_label", "응축수"))}')
    side, side_js = "", []
    logic = rn.get("logic") or []
    if logic:
        cxl, cyl, R = 1430, 600, 285
        k = len(logic)
        ring = [(cxl + R * math.cos(-math.pi / 2 + i * 2 * math.pi / k), cyl + R * math.sin(-math.pi / 2 + i * 2 * math.pi / k)) for i in range(k + 1)]
        side += (f'<svg width="1920" height="1080" style="position: absolute; inset: 0" data-layout-ignore><circle id="lr-ring" cx="{cxl}" cy="{cyl}" r="{R}" fill="none" '
                 f'stroke="{rgba(b, 0.5)}" stroke-width="3" stroke-dasharray="6 10" /></svg>'
                 f'<div id="lr-pulse" style="position: absolute; left: -12px; top: -12px; width: 24px; height: 24px; border-radius: 50%; background: {b}; box-shadow: 0 0 20px {b}" data-layout-ignore></div>')
        side += "".join(f'<div class="ln" id="lr-n{i}" style="left: {ring[i][0] - 120:.0f}px; top: {ring[i][1] - 40:.0f}px; font-size: {fit(t, 30, 210)}px">{E(t)}</div>' for i, t in enumerate(logic))
        side += f'<div style="position: absolute; left: {cxl - 190}px; top: {cyl - 80}px; width: 380px">' + "".join(f'<div class="ru">{E(r)}</div>' for r in rn.get("rules", [])) + '</div>'
        side_js = [along("lp", ring),
                   '    tl.fromTo("#lr-ring", { opacity: 0, scale: 0.8, transformOrigin: "50% 50%" }, { opacity: 1, scale: 1, duration: 0.8, ease: "expo.out" }, 0.8);',
                   '    tl.fromTo(".ln", { opacity: 0, scale: 0.8 }, { opacity: 1, scale: 1, duration: 0.6, ease: "back.out(2)", stagger: 0.25 }, 1.0);',
                   '    tl.fromTo(".ru", { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: 0.6, stagger: 0.6 }, 3.2);',
                   '    const pul = document.querySelector("#lr-pulse"); const po = { p: 0 }; const pput = () => { const q = at_lp(po.p % 1); pul.style.transform = "translate(" + q[0] + "px," + q[1] + "px)"; }; pput();',
                   f'    tl.to(po, {{ p: 3, duration: {d - 2.6:.1f}, ease: "none", onUpdate: pput }}, 1.8);',
                   '    tl.fromTo("#lr-pulse", { opacity: 0 }, { opacity: 1, duration: 0.3 }, 1.8);']
        for i in range(k):
            side_js.append(f'    tl.to("#lr-n{i}", {{ borderColor: "{b}", background: "{rgba(b, 0.18)}", duration: 0.3, yoyo: true, repeat: 1 }}, {1.8 + i * (d - 2.6) / (3 * k):.2f});')
    else:
        steps = rn.get("steps", [])
        n = len(steps)
        top0 = 560 - n * 124 / 2 + 60
        for i, q in enumerate(steps):
            side += (f'<div class="cr" id="lr-r{i}" style="top: {top0 + i * 124:.0f}px"><b style="background: linear-gradient(135deg, {a}, {cc})">{i + 1}</b>'
                     f'<div><div class="n" style="font-size: {fit(q["n"], 38, 600)}px">{E(q["n"])}</div><div class="s">{E(q.get("d", ""))}</div></div></div>')
        step = (d - 2.4) / max(1, n)
        for i in range(n):
            t = 1.2 + i * step
            side_js.append(f'    tl.to("#lr-r{i}", {{ opacity: 1, background: "{rgba(b, 0.14)}", duration: 0.4 }}, {t:.2f});')
            if i:
                side_js.append(f'    tl.to("#lr-r{i - 1}", {{ background: "rgba(0,0,0,0)", opacity: 0.75, duration: 0.4 }}, {t:.2f});')
    body = heading("lr", rn.get("eyebrow", "HOW IT RUNS"), rn.get("title", "작동 |원리"),
                   f"left: 900px; top: -300px; background: radial-gradient(circle, {rgba(b, 0.28)} 0%, rgba(0,0,0,0) 65%)") + f"""
      {pl}
      {glows}
      <svg width="1920" height="1080" style="position: absolute; inset: 0" data-layout-ignore>{lines}</svg>
      {parts}
      {side}
      <div class="cap" style="left: 140px; top: 1004px">{" &nbsp; ".join(legend)}</div>"""
    css = FIG_CSS + f"""
    .pf {{ position: absolute; opacity: 0; }}
    .pd {{ position: absolute; width: 18px; height: 24px; border-radius: 50% 50% 50% 50% / 60% 60% 40% 40%; background: #8fd8ff; opacity: 0; }}
    .ln {{ position: absolute; width: 240px; height: 80px; border-radius: 40px; display: flex; align-items: center; justify-content: center; font-weight: 700;
      background: rgba(255, 255, 255, 0.06); border: 1px solid rgba(255, 255, 255, 0.18); white-space: nowrap; }}
    .ru {{ font-size: 27px; font-weight: 700; text-align: center; color: #d8f3ff; line-height: 1.35; margin: 10px 0; word-break: keep-all; }}"""
    js = ['    tl.fromTo(["#lr-plate", "#lr-img"], { opacity: 0.6 }, { opacity: 1, duration: 0.5 }, 0.2);',
          '    tl.to("#lr-img", { filter: "brightness(0.92) saturate(0.9)", duration: 1 }, 0.6);',
          '    tl.to(".lr-gl", { opacity: 1, duration: 1.2, stagger: 0.6 }, 1.0);',
          '    tl.to(".lr-fl", { opacity: 0.4, duration: 0.8, stagger: 0.2 }, 1.0);', f'    const DUR = {d};',
          '    const mover = (sel, fn, start, dur, count, every) => { for (let k = 0; k < count; k++) { const el = document.querySelector(sel + k); const o = { p: 0 };'
          ' const put = () => { const q = fn(o.p); el.style.transform = "translate(" + q[0] + "px," + q[1] + "px)"; }; put();'
          ' const reps = Math.max(1, Math.floor((DUR - start - k * every - 0.5) / dur)); for (let r = 0; r < reps; r++) { const t0 = start + k * every + r * dur; tl.set(o, { p: 0 }, t0); tl.to(o, { p: 1, duration: dur, ease: "power1.in", onUpdate: put }, t0);'
          ' tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: 0.2 }, t0); tl.to(el, { opacity: 0, duration: 0.2 }, t0 + dur - 0.2); } } };']
    for fi, pts in enumerate(paths):
        dur = max(1.4, min(3.0, plen(pts) / 380))
        js += [along(f"f{fi}", pts), f'    mover("#lr-f{fi}-", (p) => at_f{fi}(p), {1.2 + fi * 0.3:.1f}, {dur:.2f}, {per}, {dur / per:.2f});']
    for k in range(drips):
        t0 = 3.2 + k * 1.3
        js += [f'    tl.fromTo("#lr-w{k}", {{ opacity: 0, scale: 0.2, y: 0 }}, {{ opacity: 1, scale: 1, duration: 0.6, ease: "power2.out" }}, {t0:.2f});',
               f'    tl.to("#lr-w{k}", {{ y: 300, duration: 0.7, ease: "power2.in" }}, {t0 + 0.7:.2f});',
               f'    tl.to("#lr-w{k}", {{ opacity: 0, duration: 0.2 }}, {t0 + 1.25:.2f});']
    return sc("lr", pal, css, body, js + side_js, d)


def l_path(c, pal, d):
    """Something travels a second figure along the claimed route, each point lighting as it passes."""
    a, b, cc = pal
    pa = c["signature"]["path"]
    col = FLOW.get(pa.get("color"), "#2aa7e6")
    pl, m = plate(c, pa["figure"], "lw", 120, 230, 900, 760)
    pts = [m(p["x"], p["y"]) for p in pa["points"]]
    n = len(pts)
    rows, dots = "", ""
    top0 = 560 - n * 124 / 2 + 60
    for i, p in enumerate(pa["points"]):
        rows += (f'<div class="cr" id="lw-r{i}" style="top: {top0 + i * 124:.0f}px; left: 1100px; width: 680px"><b style="background: linear-gradient(135deg, {a}, {cc})">{i + 1}</b>'
                 f'<div><div class="n">{E(p["n"])} <span style="font-size: 28px; color: #8e8ea3">({E(p["ref"])})</span></div><div class="s">{E(p["d"])}</div></div></div>')
        dots += f'<div class="cd" id="lw-d{i}" style="left: {pts[i][0]:.0f}px; top: {pts[i][1]:.0f}px; background: {col}"></div>'
    path = "M" + " L".join(f"{x:.0f} {y:.0f}" for x, y in pts)
    shape = "border-radius: 50% 50% 50% 50% / 60% 60% 40% 40%; width: 26px; height: 34px; left: -13px; top: -18px" if pa.get("color", "water") == "water" else \
        "border-radius: 50%; width: 28px; height: 28px; left: -14px; top: -14px"
    body = heading("lw", pa.get("eyebrow", "THE PATH"), pa.get("title", "흐름을 |따라가면"),
                   f"left: 800px; top: -300px; background: radial-gradient(circle, {rgba(b, 0.28)} 0%, rgba(0,0,0,0) 65%)") + f"""
      {pl}
      <svg width="1920" height="1080" style="position: absolute; inset: 0" data-layout-ignore>
        <path id="lw-line" d="{path}" fill="none" stroke="{col}" stroke-width="5" stroke-dasharray="2 12" stroke-linecap="round" opacity="0" />
      </svg>
      {dots}
      <div id="lw-drop" style="position: absolute; {shape}; background: {col}; box-shadow: 0 0 18px {col}" data-layout-ignore></div>
      {rows}
      <div class="cap" style="left: 140px; top: 1004px">{E(pa.get("figcap", ""))} · 경로는 모식</div>"""
    step = (d - 2.4) / n
    js = ['    tl.fromTo(["#lw-plate", "#lw-img"], { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 0.8, ease: "expo.out" }, 0.3);',
          '    tl.to("#lw-line", { opacity: 0.9, duration: 0.6 }, 1.0);', along("w", pts),
          '    const dr = document.querySelector("#lw-drop"); const wo = { p: 0 }; const wput = () => { const q = at_w(wo.p); dr.style.transform = "translate(" + q[0] + "px," + q[1] + "px)"; }; wput();',
          '    tl.fromTo("#lw-drop", { opacity: 0, scale: 0.3 }, { opacity: 1, scale: 1, duration: 0.5 }, 1.0);',
          f'    tl.to(wo, {{ p: 1, duration: {step * (n - 1):.2f}, ease: "power1.inOut", onUpdate: wput }}, 1.4);']
    for i in range(n):
        t = 1.2 + i * step
        js += [f'    tl.fromTo("#lw-d{i}", {{ scale: 0 }}, {{ scale: 1, duration: 0.5, ease: "back.out(3)" }}, {t:.2f});',
               f'    tl.to("#lw-r{i}", {{ opacity: 1, background: "{rgba(b, 0.14)}", duration: 0.4 }}, {t:.2f});']
        if i:
            js.append(f'    tl.to("#lw-r{i - 1}", {{ background: "rgba(0,0,0,0)", opacity: 0.75, duration: 0.4 }}, {t:.2f});')
    return sc("lw", pal, FIG_CSS, body, js, d)


# ====================================================================== sequence (primers)
BASE = {"A": "#7ee787", "T": "#ff7b72", "G": "#f2cc60", "C": "#79c0ff"}
PCOL = {"F3": "#79c0ff", "FIP": "#a5d6ff", "LF": "#56d4dd", "B3": "#ffa657", "BIP": "#ffc680", "LB": "#ff9bce"}


RCOL = ["#79c0ff", "#ffa657", "#7ee787", "#ff9bce", "#f2cc60", "#56d4dd", "#d2a8ff", "#ff7b72"]


def q_problem(c, pal, d):
    pb = c["signature"]["problem"]
    k = len(pb["cards"])
    x0 = (1920 - (k * 520 + (k - 1) * 40)) / 2
    cards = ""
    for i, p in enumerate(pb["cards"]):
        cards += (f'<div class="qp glass" id="qp-c{i}" style="left: {x0 + i * 560:.0f}px"><div class="v grad" style="font-size: {fit(p["v"], 120, 440)}px">{E(p["v"])}</div>'
                  f'<div class="l">{E(p["l"])}</div><div class="s">{E(p.get("s", ""))}</div></div>')
    body = heading("qp", "THE PROBLEM", pb.get("title") or f'{c["sub"].split(" ")[0]} 피해, |빨리 찾아야 막는다',
                   "left: 400px; top: -300px; background: radial-gradient(circle, rgba(255,90,90,0.22) 0%, rgba(0,0,0,0) 65%)") + cards + \
        f'<div id="qp-src" class="cap" style="position: absolute; left: 140px; top: 900px; font-size: 28px; color: #8e8ea3">{E(pb.get("src", "자료: 명세서 배경기술"))}</div>'
    css = """    .qp { position: absolute; top: 360px; width: 520px; height: 420px; border-radius: 30px; padding: 50px 44px; }
    .qp .v { font-weight: 800; letter-spacing: -0.04em; line-height: 1; white-space: nowrap; }
    .qp .l { font-size: 34px; font-weight: 700; margin-top: 40px; line-height: 1.35; word-break: keep-all; }
    .qp .s { font-size: 28px; color: #a8a8bc; margin-top: 14px; word-break: keep-all; }"""
    js = ['    tl.fromTo(".qp", { opacity: 0, y: 50 }, { opacity: 1, y: 0, duration: 0.8, ease: "expo.out", stagger: 0.35 }, 0.6);',
          '    tl.fromTo("#qp-src", { opacity: 0 }, { opacity: 1, duration: 0.5 }, 1.8);']
    for i, p in enumerate(pb["cards"]):
        js.append(count_js(f"#qp-c{i} .v", p["v"], 0.8 + i * 0.35))
    return sc("qp", pal, css, body, js, d)


def count_js(sel, text, t):
    """Count up the number inside text (keeps its prefix/suffix and decimals)."""
    import re
    mt = re.match(r"([^0-9]*)([0-9][0-9,]*(?:\.[0-9]+)?)(.*)", text)
    if not mt or re.search(r"[0-9]", mt.group(3)):  # ranges like 75~100% stay as written
        return ""
    num = mt.group(2).replace(",", "")
    dec = len(num.split(".")[1]) if "." in num else 0
    return (f'    (() => {{ const el = document.querySelector("{sel}"); const o = {{ v: 0 }}; tl.to(o, {{ v: {float(num)}, duration: 1.4, ease: "power2.out", '
            f'onUpdate: () => {{ el.textContent = "{mt.group(1)}" + o.v.toFixed({dec}) + "{mt.group(3)}"; }} }}, {t:.2f}); }})();')


def q_primers(c, pal, d):
    """Six primers type out their real bases, then fly to the target and light the eight regions they recognise."""
    a, b, cc = pal
    sg = c["signature"]
    lay = sg["layout"]
    pr = sg["primers"]
    x0, x1, ys = 160, 1760, 330
    rh = min(86, 500 / len(pr))
    rw = (x1 - x0) / len(lay)
    rx = {r: x0 + i * rw for i, r in enumerate(lay)}
    regs = "".join(f'<div class="rg" id="qs-g{r}" style="left: {rx[r] + 8:.0f}px; width: {rw - 16:.0f}px; top: {ys - 34}px"><span>{r}</span></div>' for r in lay)
    ticks = "".join(f'<line x1="{x:.0f}" y1="{ys + 30}" x2="{x:.0f}" y2="{ys + 44}" stroke="rgba(255,255,255,0.25)" stroke-width="2" />' for x in range(x0, x1, 18))
    def pcol(p):
        return PCOL.get(p["id"]) or RCOL[lay.index(p["regions"][0]) % len(RCOL)]
    rows = ""
    for i, p in enumerate(pr):
        col = pcol(p)
        letters = "".join(f'<i style="color: {BASE.get(ch, "#fff")}">{ch}</i>' for ch in p["seq"])
        rows += (f'<div class="pr" id="qs-r{i}" style="top: {470 + i * rh:.0f}px; height: {rh - 10:.0f}px"><b style="background: {col}; width: {max(96, 22 * len(p["id"]) + 30)}px">{E(p["id"])}</b>'
                 f'<span class="sq">5′-{letters}-3′</span><em>{len(p["seq"])} nt</em></div>')
    body = heading("qs", "PRIMER DESIGN", sg.get("primers_title") or f'{len(pr)}개 프라이머가 |표적 {len(lay)}곳을 짚는다',
                   f"left: 300px; top: -300px; background: radial-gradient(circle, {rgba(b, 0.26)} 0%, rgba(0,0,0,0) 65%)") + f"""
      <div style="position: absolute; left: {x0}px; top: {ys - 92}px; font-size: 28px; color: #8e8ea3">{E(sg["target"])} · {E(sg.get("target_note", "특이 부위 (모식도)"))}</div>
      <svg width="1920" height="1080" style="position: absolute; inset: 0" data-layout-ignore>
        <line id="qs-dna1" x1="{x0}" y1="{ys + 30}" x2="{x1}" y2="{ys + 30}" stroke="#e8e8f0" stroke-width="6" stroke-linecap="butt" pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="1" />
        <line id="qs-dna2" x1="{x0}" y1="{ys + 58}" x2="{x1}" y2="{ys + 58}" stroke="rgba(232,232,240,0.45)" stroke-width="6" stroke-linecap="butt" pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="1" />
        {ticks}
      </svg>
      {regs}
      <div id="qs-cnt" style="position: absolute; right: 160px; top: 120px; text-align: right"><div class="grad" style="font-size: 96px; font-weight: 800; line-height: 1"><span id="qs-n">0</span>/{len(lay)}</div>
        <div style="font-size: 28px; color: #a8a8bc">인식 부위</div></div>
      {rows}
      <div class="cap" style="position: absolute; left: 160px; top: 1010px; font-size: 28px; color: #8e8ea3">{E(sg.get("primers_cap", ""))}</div>"""
    css = MONO + f"""
    .rg {{ position: absolute; height: 48px; border-radius: 10px; border: 2px dashed rgba(255,255,255,0.28); display: flex; align-items: center; justify-content: center; }}
    .rg span {{ font-size: 28px; font-weight: 800; color: #8e8ea3; }}
    .pr {{ position: absolute; left: 160px; right: 160px; display: flex; align-items: center; gap: 24px; opacity: 0.35; }}
    .pr b {{ height: 54px; border-radius: 27px; color: #04121f; font-size: 28px; display: flex; align-items: center; justify-content: center; flex: none; }}
    .pr .sq {{ font-family: "PlexMono", monospace; font-size: 29px; letter-spacing: 0.02em; white-space: nowrap; color: #6e6e82; }}
    .pr .sq i {{ font-style: normal; opacity: 0.12; }}
    .pr em {{ font-style: normal; font-size: 28px; color: #8e8ea3; margin-left: auto; }}"""
    step = (d - 2.4) / len(pr)
    js = ['    tl.to("#qs-dna1", { strokeDashoffset: 0, duration: 1.0, ease: "power2.inOut" }, 0.4);',
          '    tl.to("#qs-dna2", { strokeDashoffset: 0, duration: 1.0, ease: "power2.inOut" }, 0.55);',
          '    tl.fromTo(".rg", { opacity: 0 }, { opacity: 1, duration: 0.4, stagger: 0.06 }, 0.9);',
          '    const cnt = document.querySelector("#qs-n"); const lit = { v: 0 }; const show = () => { cnt.textContent = String(Math.round(lit.v)); };']
    lit, done = 0, set()
    for i, p in enumerate(pr):
        t = 1.4 + i * step
        col = pcol(p)
        js += [f'    tl.to("#qs-r{i}", {{ opacity: 1, duration: 0.3 }}, {t:.2f});',
               f'    tl.to("#qs-r{i} .sq", {{ color: "#c9d1d9", duration: 0.3 }}, {t:.2f});',
               f'    tl.to("#qs-r{i} .sq i", {{ opacity: 1, duration: 0.04, stagger: {min(0.03, (step * 0.55) / len(p["seq"])):.3f} }}, {t + 0.1:.2f});']
        for r in p["regions"]:
            if r not in done:
                done.add(r)
                lit += 1
            tr = t + step * 0.62 + 0.12 * p["regions"].index(r)
            js += [f'    tl.to("#qs-g{r}", {{ borderStyle: "solid", borderColor: "{col}", background: "{col}", duration: 0.3 }}, {tr:.2f});',
                   f'    tl.to("#qs-g{r} span", {{ color: "#04121f", duration: 0.3 }}, {tr:.2f});',
                   f'    tl.fromTo("#qs-g{r}", {{ scale: 1.25 }}, {{ scale: 1, duration: 0.5, ease: "back.out(3)" }}, {tr:.2f});',
                   f'    tl.to(lit, {{ v: {lit}, duration: 0.05, onUpdate: show }}, {tr:.2f});']
        js.append(f'    tl.to("#qs-r{i}", {{ opacity: 0.85, duration: 0.4 }}, {t + step - 0.1:.2f});')
    return sc("qs", pal, css, body, js, d)


def curve_path(ct, x0, y0, w, h, cycles, plateau=0.9):
    """A sigmoid amplification curve crossing the threshold (20 % of plateau) at cycle `ct`; flat when ct is None/off-axis."""
    pts = []
    for k in range(0, cycles * 4 + 1):
        cyc = k / 4
        if ct is None or ct > cycles:
            v = 0.02
        else:
            mid = ct + 2.2  # 20 % of a logistic with slope 1.6 sits ~2.2 cycles before its midpoint
            v = 0.02 + plateau / (1 + math.exp(-(cyc - mid) * 0.65))
        pts.append((x0 + w * cyc / cycles, y0 + h - h * v))
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)


def chart(sid, title, series, x0, y0, w, h, cycles, cutoff, note):
    grid = "".join(f'<line x1="{x0 + w * k / 4:.0f}" y1="{y0}" x2="{x0 + w * k / 4:.0f}" y2="{y0 + h}" stroke="rgba(255,255,255,0.08)" />'
                   f'<text x="{x0 + w * k / 4:.0f}" y="{y0 + h + 40}" fill="#8e8ea3" font-size="28" text-anchor="middle">{cycles * k // 4}</text>' for k in range(5))
    thr = y0 + h - h * (0.02 + 0.9 * 0.2)
    cx = x0 + w * cutoff / cycles
    paths = "".join(f'<path class="{sid}-cv" d="{curve_path(s["ct"], x0, y0, w, h, cycles)}" fill="none" stroke="{s["col"]}" stroke-width="5" stroke-linecap="butt" pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="1" />'
                    for s in series)
    legend = "".join(f'<div style="display: flex; align-items: center; gap: 12px; height: 40px; white-space: nowrap"><i style="width: 26px; height: 6px; border-radius: 3px; background: {s["col"]}"></i>'
                     f'<span style="font-size: 28px; color: #d8d8e4">{E(s["l"])}</span><b style="font-size: 28px; color: #a8a8bc; font-weight: 600; margin-left: 6px">{E(s["tag"])}</b></div>' for s in series)
    return (f'<svg width="1920" height="1080" style="position: absolute; inset: 0" data-layout-ignore>'
            f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.15)" />{grid}'
            f'<line x1="{x0}" y1="{thr:.0f}" x2="{x0 + w}" y2="{thr:.0f}" stroke="rgba(255,255,255,0.35)" stroke-dasharray="8 8" />'
            f'<line x1="{cx:.0f}" y1="{y0}" x2="{cx:.0f}" y2="{y0 + h}" stroke="rgba(255,120,120,0.55)" stroke-width="2" stroke-dasharray="6 8" />'
            f'<text x="{cx + 10:.0f}" y="{y0 + 34}" fill="#ff9b9b" font-size="28">Ct {cutoff}</text>{paths}</svg>'
            f'<div style="position: absolute; left: {x0}px; top: {y0 - 64}px; font-size: 34px; font-weight: 700; white-space: nowrap">{E(title)}</div>'
            f'<div style="position: absolute; left: {x0 + 20}px; top: {y0 + 14}px">{legend}</div>'
            f'<div style="position: absolute; left: {x0}px; top: {y0 + h + 58}px; font-size: 28px; color: #8e8ea3; white-space: nowrap">{E(note)}</div>')


def q_probe(c, pal, d):
    """Why the probe: with SYBR alone the no-template controls rise too; with the probe they stay flat."""
    a, b, cc = pal
    sg = c["signature"]
    cyc, cut = sg["cycles"], sg["cutoff"]
    pb = sg["probe"]
    left = [dict(pb["sybr_pos"], col="#ff6b6b", tag="양성")] + [{"l": f"NTC {i + 1}", "ct": ct, "col": "#3fb950", "tag": f"Ct {ct}"} for i, ct in enumerate(pb["sybr_ntc"])]
    right = [dict(q, col=["#ff6b6b", "#ffa657", "#56d4dd"][i % 3], tag="양성") for i, q in enumerate(pb["pos"])] + \
        [{"l": f'NTC ×{pb.get("ntc_n", 4)}', "ct": None, "col": "#4c6ef5", "tag": "N/A"}]
    letters = "".join(f'<i style="color: {BASE.get(ch, "#fff")}">{ch}</i>' for ch in sg["probe"]["seq"])
    body = heading("qb", "PROBE", '프로브가 |가짜 신호를 지운다',
                   f"left: 700px; top: -300px; background: radial-gradient(circle, {rgba(b, 0.26)} 0%, rgba(0,0,0,0) 65%)") + f"""
      <div id="qb-probe" style="position: absolute; left: 0; right: 0; top: 250px; text-align: center; white-space: nowrap">
        <span class="fam">{E(sg["probe"]["dye"])}</span><span class="sq">5′-{letters}-3′</span><span class="q">Q</span></div>
      <div id="qb-L">{chart("qbl", pb.get("left_title", "SYBR Green만"), left, 160, 470, 700, 380, cyc, cut, "NTC에서도 증폭 → 비특이 반응")}</div>
      <div id="qb-R">{chart("qbr", pb.get("right_title", "프로브 추가"), right, 1060, 470, 700, 380, cyc, cut, "NTC 전부 N/A → 표적만 신호")}</div>"""
    css = MONO + """
    #qb-probe .sq { font-family: "PlexMono", monospace; font-size: 30px; margin: 0 16px; }
    #qb-probe .sq i { font-style: normal; }
    #qb-probe .fam, #qb-probe .q { display: inline-block; width: 74px; height: 54px; line-height: 54px; border-radius: 27px; font-size: 28px; font-weight: 800; color: #04121f; }
    #qb-probe .fam { background: #3fb950; box-shadow: 0 0 30px #3fb950; }
    #qb-probe .q { background: #6e6e82; }"""
    js = ['    tl.fromTo("#qb-probe", { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.6 }, 0.5);',
          '    tl.fromTo("#qb-probe .sq i", { opacity: 0 }, { opacity: 1, duration: 0.03, stagger: 0.03 }, 0.6);',
          '    tl.fromTo("#qb-L", { opacity: 0 }, { opacity: 1, duration: 0.5 }, 1.4);',
          '    tl.to(".qbl-cv", { strokeDashoffset: 0, duration: 2.2, ease: "power1.inOut", stagger: 0.15 }, 1.6);',
          f'    tl.fromTo("#qb-R", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.5 }}, {d * 0.45:.2f});',
          f'    tl.to(".qbr-cv", {{ strokeDashoffset: 0, duration: 2.2, ease: "power1.inOut", stagger: 0.15 }}, {d * 0.45 + 0.2:.2f});',
          f'    tl.to("#qb-L", {{ opacity: 0.45, duration: 0.6 }}, {d * 0.45 + 0.4:.2f});']
    return sc("qb", pal, css, body, js, d)


def q_result(c, pal, d):
    """Sensitivity and specificity drawn from the specification's own Ct tables."""
    a, b, cc = pal
    sg = c["signature"]
    rs = sg["result"]
    cyc, cut = sg["cycles"], sg["cutoff"]
    scol = ["#ff6b6b", "#ffa657", "#56d4dd", "#4c6ef5"]
    sens = [{"l": s["l"], "ct": s["ct"], "col": scol[i % 4], "tag": "N/A" if s["ct"] > cut else f"Ct {s['ct']:.1f}"} for i, s in enumerate(rs["sensitivity"])]
    spec = [{"l": s["l"], "ct": s["ct"], "col": "#ff6b6b" if i == 0 else "#4c6ef5", "tag": f"Ct {s['ct']:.1f}" if s["ct"] else "N/A"} for i, s in enumerate(rs["specificity"])]
    body = heading("qr", rs.get("eyebrow", "RESULTS"), rs.get("title", "민감도와 |특이도"),
                   f"left: 300px; top: -300px; background: radial-gradient(circle, {rgba(b, 0.26)} 0%, rgba(0,0,0,0) 65%)") + f"""
      <div id="qr-L">{chart("qrl", rs.get("sens_title", "민감도"), sens, 160, 360, 700, 380, cyc, cut, rs.get("sens_note", ""))}</div>
      <div id="qr-R">{chart("qrr", rs.get("spec_title", "특이도"), spec, 1060, 360, 700, 380, cyc, cut, rs.get("spec_note", ""))}</div>
      {chips_html(sg, 920)[0]}"""
    css = chips_html(sg, 920)[1]
    js = ['    tl.fromTo("#qr-L", { opacity: 0 }, { opacity: 1, duration: 0.5 }, 0.5);',
          '    tl.to(".qrl-cv", { strokeDashoffset: 0, duration: 2.4, ease: "power1.inOut", stagger: 0.2 }, 0.7);',
          '    tl.fromTo("#qr-R", { opacity: 0 }, { opacity: 1, duration: 0.5 }, 2.6);',
          '    tl.to(".qrr-cv", { strokeDashoffset: 0, duration: 2.4, ease: "power1.inOut", stagger: 0.2 }, 2.8);',
          '    tl.fromTo(".fc", { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.6, ease: "expo.out", stagger: 0.2 }, 5.2);']
    return sc("qr", pal, css, body, js, d)


def chips_html(sg, top):
    chips = "".join(f'<div class="fc glass">{E(t)}</div>' for t in sg.get("field", []))
    return (f'<div id="qr-chips" style="position: absolute; left: 0; right: 0; top: {top}px; display: flex; justify-content: center; gap: 22px">{chips}</div>',
            """    .fc { height: 76px; padding: 0 34px; border-radius: 38px; display: flex; align-items: center; font-size: 32px; font-weight: 700; white-space: nowrap; }""")


def q_tubes(c, pal, d):
    """The visual readout: reaction tubes warm on the block, then the positives turn the colour the spec names."""
    a, b, cc = pal
    sg = c["signature"]
    rs = sg["result"]
    tb = rs["tubes"]
    n = len(tb)
    gap = min(260, 1500 / n)
    x0 = 960 - gap * (n - 1) / 2
    pos, neg = rs.get("pos_color", "#7ee787"), rs.get("neg_color", "#ff7b5a")
    tubes = ""
    for i, t in enumerate(tb):
        x = x0 + i * gap
        tubes += (f'<div class="tu" id="qv-t{i}" style="left: {x - 80:.0f}px"><svg width="160" height="380" viewBox="0 0 160 380">'
                  f'<rect x="34" y="6" width="92" height="40" rx="10" fill="rgba(255,255,255,0.25)" />'
                  f'<path d="M44 46 L116 46 L116 250 Q116 350 80 370 Q44 350 44 250 Z" fill="rgba(255,255,255,0.08)" stroke="rgba(255,255,255,0.6)" stroke-width="4" />'
                  f'<path class="lq{" ps" if t.get("pos") else ""}" d="M50 150 L110 150 L110 252 Q110 340 80 360 Q50 340 50 252 Z" fill="{neg}" /></svg>'
                  f'<div class="tg" style="color: {pos if t.get("pos") else neg}">{"+" if t.get("pos") else "−"}</div>'
                  f'<div class="tn">{E(t["l"])}</div></div>')
    chips, ccss = chips_html(sg, 930)
    body = heading("qv", rs.get("eyebrow", "READOUT"), rs.get("title", "색으로 |바로 읽는다"),
                   f"left: 500px; top: -300px; background: radial-gradient(circle, {rgba(b, 0.26)} 0%, rgba(0,0,0,0) 65%)") + f"""
      <div id="qv-blk" style="position: absolute; left: {x0 - gap / 2 - 20:.0f}px; width: {gap * n + 40:.0f}px; top: 600px; height: 70px; border-radius: 18px; background: linear-gradient(180deg, #3a3a48, #22222c)"></div>
      <div id="qv-heat" style="position: absolute; left: {x0 - gap / 2 - 20:.0f}px; width: {gap * n + 40:.0f}px; top: 560px; height: 150px; border-radius: 50%; background: radial-gradient(ellipse, rgba(255,140,60,0.5), rgba(255,140,60,0) 70%); opacity: 0" data-layout-ignore></div>
      {tubes}
      <div id="qv-note" class="cap" style="position: absolute; left: 0; right: 0; top: 850px; text-align: center; font-size: 30px; color: #c9d1d9">{E(rs.get("note", ""))}</div>
      {chips}
      <div class="cap" style="position: absolute; left: 140px; top: 1010px; font-size: 28px; color: #8e8ea3">{E(rs.get("cap", ""))}</div>"""
    css = ccss + """
    .tu { position: absolute; top: 300px; width: 160px; text-align: center; }
    .tu .tg { position: absolute; left: 0; right: 0; top: -60px; font-size: 54px; font-weight: 800; opacity: 0; }
    .tu .tn { font-size: 28px; font-weight: 700; color: #d8d8e4; margin-top: 24px; white-space: nowrap; }"""
    js = ['    tl.fromTo(".tu", { opacity: 0, y: -60 }, { opacity: 1, y: 0, duration: 0.6, ease: "expo.out", stagger: 0.12 }, 0.5);',
          '    tl.fromTo("#qv-blk", { opacity: 0 }, { opacity: 1, duration: 0.4 }, 0.4);',
          '    tl.to("#qv-heat", { opacity: 1, duration: 0.8, yoyo: true, repeat: 1 }, 1.6);',
          f'    tl.to(".lq.ps", {{ fill: "{pos}", duration: 1.0, ease: "power2.inOut", stagger: 0.15 }}, 3.4);',
          f'    tl.to(".tu .tg", {{ opacity: 1, duration: 0.4, stagger: 0.1 }}, 4.4);',
          '    tl.fromTo("#qv-note", { opacity: 0 }, { opacity: 1, duration: 0.5 }, 4.6);',
          f'    tl.fromTo(".fc", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.6, ease: "expo.out", stagger: 0.2 }}, {min(d - 2.4, 5.6):.2f});']
    for i, t in enumerate(tb):
        if t.get("pos"):
            js.append(f'    tl.to("#qv-t{i} svg", {{ filter: "drop-shadow(0 0 22px {pos})", duration: 0.8 }}, {3.6 + i * 0.15:.2f});')
    return sc("qv", pal, css, body, js, d)


def q_gel(c, pal, d):
    """The multiplex gel: every lane's products run down from the well and stop at their real sizes beside the ladder."""
    a, b, cc = pal
    sg = c["signature"]
    rs = sg["result"]
    lad, lanes = rs["ladder"], rs["lanes"]
    gx, gy, gw, gh = 300, 300, 1320, 560
    cols = len(lanes) + 1
    lw = gw / cols
    lo, hi = math.log10(min(lad) * 0.85), math.log10(max(lad) * 1.1)

    def by(bp):
        return gy + 60 + (gh - 90) * (hi - math.log10(bp)) / (hi - lo)
    wells = "".join(f'<rect x="{gx + k * lw + lw * 0.2:.0f}" y="{gy + 24}" width="{lw * 0.6:.0f}" height="14" rx="3" fill="#05050a" />' for k in range(cols))
    bands = "".join(f'<rect class="bd bl" x="{gx + lw * 0.2:.0f}" y="{by(v) - 4:.0f}" width="{lw * 0.6:.0f}" height="8" rx="3" fill="rgba(255,190,140,0.55)" />' for v in lad)
    labels = "".join(f'<text x="{gx - 16}" y="{by(v) + 9:.0f}" fill="#8e8ea3" font-size="26" text-anchor="end">{v}</text>' for v in lad if v in (min(lad), max(lad)) or v % 200 == 0 or len(lad) <= 6)
    tops = f'<div class="gn" style="left: {gx:.0f}px; width: {lw:.0f}px">M</div>'
    for k, ln in enumerate(lanes):
        x = gx + (k + 1) * lw
        col = RCOL[k % len(RCOL)] if len(ln["bands"]) == 1 else "#ffffff"
        tops += f'<div class="gn" style="left: {x:.0f}px; width: {lw:.0f}px; font-size: {fit(ln["l"], 28, lw - 8)}px">{E(ln["l"])}</div>'
        for v in ln["bands"]:
            bands += f'<rect class="bd b{k}" x="{x + lw * 0.16:.0f}" y="{by(v) - 6:.0f}" width="{lw * 0.68:.0f}" height="12" rx="4" fill="#ffe2c8" style="filter: drop-shadow(0 0 10px {col})" />'
            if len(ln["bands"]) == 1:
                bands += f'<text class="bt b{k}" x="{x + lw / 2:.0f}" y="{by(v) + 40:.0f}" fill="#c9d1d9" font-size="24" text-anchor="middle">{v} bp</text>'
    chips, ccss = chips_html(sg, 940)
    body = heading("qg", rs.get("eyebrow", "MULTIPLEX"), rs.get("title", "한 번에 |가린다"),
                   f"left: 500px; top: -300px; background: radial-gradient(circle, {rgba(b, 0.26)} 0%, rgba(0,0,0,0) 65%)") + f"""
      {tops}
      <svg id="qg-gel" width="1920" height="1080" style="position: absolute; inset: 0" data-layout-ignore>
        <rect x="{gx}" y="{gy}" width="{gw}" height="{gh}" rx="18" fill="#141a2e" stroke="rgba(255,255,255,0.15)" />{wells}{bands}{labels}
      </svg>
      <div class="cap" style="position: absolute; left: {gx}px; top: {gy + gh + 14}px; font-size: 28px; color: #8e8ea3">{E(rs.get("note", ""))} · {E(rs.get("cap", ""))}</div>
      {chips}"""
    css = ccss + """
    .gn { position: absolute; top: 250px; text-align: center; font-weight: 700; color: #d8d8e4; white-space: nowrap; font-size: 28px; }"""
    js = ['    tl.fromTo("#qg-gel", { opacity: 0 }, { opacity: 1, duration: 0.6 }, 0.4);',
          '    tl.fromTo(".gn", { opacity: 0, y: -10 }, { opacity: 1, y: 0, duration: 0.4, stagger: 0.08 }, 0.6);',
          f'    tl.fromTo(".bl", {{ y: (k, el) => {gy + 30} - el.getAttribute("y"), opacity: 0 }}, {{ y: 0, opacity: 1, duration: 1.6, ease: "power2.out" }}, 1.2);']
    for k in range(len(lanes)):
        js.append(f'    tl.fromTo(".bd.b{k}", {{ y: (i, el) => {gy + 30} - el.getAttribute("y"), opacity: 0 }}, {{ y: 0, opacity: 1, duration: 1.8, ease: "power2.out" }}, {1.4 + k * 0.35:.2f});')
        js.append(f'    tl.fromTo(".bt.b{k}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4 }}, {3.2 + k * 0.35:.2f});')
    js.append(f'    tl.fromTo(".fc", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: 0, duration: 0.6, ease: "expo.out", stagger: 0.2 }}, {min(d - 2.4, 4.0 + len(lanes) * 0.35):.2f});')
    return sc("qg", pal, css, body, js, d)


# ====================================================================== narratives
SIG = {"jr-route": j_route, "jj-journey": j_journey, "lp-parts": l_parts, "lr-run": l_run, "lw-path": l_path,
       "qp-problem": q_problem, "qs-primers": q_primers, "qb-probe": q_probe, "qr-result": q_result, "qv-tubes": q_tubes, "qg-gel": q_gel}


def narrative(c):
    """The scene list for this patent, sized to its own data (total stays under 60 s)."""
    sg = c["signature"]
    kind = sg["type"]
    head, tail = [("s1", "s1-teaser", 6.0)], [("s6", "s6-apps", 6.5), ("s7", "s7-outro", 6.5)]
    if kind == "journey":
        mid = [("jr", "jr-route", 7.5)] if sg.get("removed") else []
        mid.append(("jj", "jj-journey", round(max(14.0, 2.6 + 2.7 * len(sg["stages"])), 1)))
        mid.append(("s4", "s4-proof", 12.0))
        if not sg.get("removed"):
            mid.append(("s5", "s5-features", 7.0))
    elif kind == "loop":
        mid = [("lp", "lp-parts", round(max(8.0, 2.4 + 1.5 * len(sg["callouts"])), 1)), ("lr", "lr-run", 13.0)]
        mid += [("lw", "lw-path", 8.5)] if sg.get("path") else []
        mid.append(("s5", "s5-features", 7.0))
    else:
        rk = sg["result"]["kind"]
        mid = [("qp", "qp-problem", 6.0), ("qs", "qs-primers", round(min(16.0, max(12.0, 2.6 + 1.9 * len(sg["primers"]))), 1))]
        mid += [("qb", "qb-probe", 9.0)] if sg.get("probe") else []
        mid.append({"ct": ("qr", "qr-result", 9.5), "tubes": ("qv", "qv-tubes", 8.5), "gel": ("qg", "qg-gel", 9.5)}[rk])
        if not sg.get("probe"):
            mid.append(("s5", "s5-features", 7.0))
    return head + mid + tail


def slots_for(c):
    out, t = [], 0.0
    for sid, f, du in narrative(c):
        out.append((sid, f, round(t, 2), du))
        t += du - 0.5
    return out, round(t + 0.5, 2)


def build(path):
    c = json.load(open(path, encoding="utf-8"))
    kind = c["signature"]["type"]
    pal = PALETTES.get(c.get("palette", "blue"), PALETTES["blue"])
    slug = f'{int(c["order"]):03d}-{c["appno"]}'
    out = os.path.join(ROOT, "videos_s", slug)
    os.makedirs(os.path.join(out, "compositions"), exist_ok=True)
    os.makedirs(os.path.join(out, "assets", "fig"), exist_ok=True)
    for sub in ("fonts", "sfx", "music"):
        dst = os.path.join(out, "assets", sub)
        if not os.path.exists(dst) and os.path.isdir(os.path.join(ROOT, "assets", sub)):
            shutil.copytree(os.path.join(ROOT, "assets", sub), dst)
    sg = c["signature"]
    for fn in {sg.get("figure"), (sg.get("run") or {}).get("figure"), (sg.get("path") or {}).get("figure"),
               c["proof"].get("figure") if c["proof"].get("kind") == "anatomy" else None} - {None}:
        shutil.copy(os.path.join(ROOT, "data", "patents", c["appno"], fn), os.path.join(out, "assets", "fig", fn))
    copy_figures(c, out)
    for fn in ("package.json", "hyperframes.json"):
        s = open(os.path.join(ROOT, "template", fn), encoding="utf-8").read().replace("__SLUG__", slug + "-s")
        open(os.path.join(out, fn), "w", encoding="utf-8").write(s)
    slots, total = slots_for(c)
    A.DUR.update({sid: du for sid, _, _, du in slots})
    frame = {"s1-teaser": lambda: A.s1(c, pal), "s4-proof": lambda: A.s4_anatomy(c, pal) if c["proof"].get("kind") == "anatomy" else A.s4_stats(c, pal),
             "s5-features": lambda: A.s5(c, pal), "s6-apps": lambda: A.s6(c, pal), "s7-outro": lambda: A.s7(c, pal)}
    for sid, f, st, du in slots:
        html = frame[f]() if f in frame else SIG[f](c, pal, du)
        open(os.path.join(out, "compositions", f + ".html"), "w", encoding="utf-8").write(html)
    keep = (A.SLOTS, A.TOTAL)
    A.SLOTS, A.TOTAL = slots, total
    try:
        open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(A.index(c))
    finally:
        A.SLOTS, A.TOTAL = keep
    add_transitions(out, "A", slots, total, 1920, 1080)
    print(slug, f"built (S · {kind} · {total}s)")
    return out


if __name__ == "__main__":
    import postprocess
    for p in sys.argv[1:]:
        postprocess.run(build(p))
