"""More journey stage illustrations: milling, forming, inoculation, sterilising, coating, packing, concentrating, harvesting, extrusion.

Each key maps to (svg(a, b, cc) -> SVG 560×440 drawn in place, js(i, t) -> timeline lines for stage i that starts at t).
build_sig.material() and the journey animation look a key up here after their own keys.
"""
from build import rgba

V = 'fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.5)" stroke-width="5"'


def _mill(a, b, cc):
    """Grains drop into a hopper, two rollers turn, powder heaps up below."""
    grains = "".join(f'<ellipse class="mg" cx="{236 + (i % 4) * 30}" cy="{30 + (i // 4) * 24}" rx="11" ry="7" fill="#efe1c0" stroke="{a}" stroke-width="2" />' for i in range(8))
    rollers = "".join(f'<g class="mr" transform="translate({250 + k * 60} 214)"><circle r="28" fill="rgba(255,255,255,0.12)" stroke="#dfe6ee" stroke-width="5" />'
                      + "".join(f'<line x1="0" y1="0" x2="{22 * (1 if j % 2 else -1) * (j < 2) }" y2="{22 * (1 if j % 2 else -1) * (j >= 2)}" stroke="#dfe6ee" stroke-width="4" />' for j in range(4))
                      + '</g>' for k in range(2))
    dust = "".join(f'<circle class="md" cx="{256 + (i % 5) * 12}" cy="262" r="{3 + i % 2}" fill="#f3e9d2" opacity="0" />' for i in range(10))
    return (f'<path d="M190 100 L370 100 L310 180 L250 180 Z" {V} />{grains}{rollers}{dust}'
            f'<path d="M150 410 L410 410" stroke="rgba(255,255,255,0.4)" stroke-width="5" stroke-linecap="round" />'
            f'<path id="mh" class="mh" d="M170 408 Q280 300 390 408 Z" fill="#f3e9d2" stroke="{a}" stroke-width="2" />')


def _mill_js(i, t):
    return [f'    tl.fromTo("#jj-m{i} .mg", {{ y: 0, opacity: 1 }}, {{ y: 120, opacity: 0, duration: 0.7, ease: "power1.in", stagger: 0.1 }}, {t + 0.4:.2f});',
            f'    tl.to("#jj-m{i} .mr", {{ rotation: (k) => (k ? -360 : 360), svgOrigin: (k) => (k ? "310 214" : "250 214"), duration: 1.8, ease: "none" }}, {t + 0.4:.2f});',
            f'    tl.fromTo("#jj-m{i} .md", {{ y: 0, opacity: 0 }}, {{ y: 130, opacity: 1, duration: 0.6, ease: "power1.in", stagger: {{ each: 0.07, repeat: 1 }} }}, {t + 0.7:.2f});',
            f'    tl.fromTo("#jj-m{i} .mh", {{ scaleY: 0.08, transformOrigin: "50% 100%" }}, {{ scaleY: 1, duration: 1.6, ease: "power1.out" }}, {t + 0.8:.2f});']


def _form(a, b, cc):
    """A press comes down on a mould and the pieces stand up shaped."""
    cav = "".join(f'<rect x="{150 + k * 70}" y="330" width="54" height="50" rx="10" fill="rgba(0,0,0,0.25)" stroke="rgba(255,255,255,0.35)" stroke-width="3" />' for k in range(4))
    dough = f'<rect class="fd" x="140" y="300" width="290" height="34" rx="16" fill="#efe1c0" stroke="{a}" stroke-width="2" />'
    pieces = "".join(f'<rect class="fp" x="{152 + k * 70}" y="320" width="50" height="50" rx="12" fill="#efe1c0" stroke="{a}" stroke-width="3" opacity="0" />' for k in range(4))
    press = (f'<g class="fx"><rect x="130" y="80" width="310" height="40" rx="12" fill="{cc}" />'
             f'<rect x="270" y="20" width="30" height="64" rx="8" fill="#dfe6ee" />'
             + "".join(f'<rect x="{154 + k * 70}" y="118" width="46" height="18" rx="5" fill="#dfe6ee" />' for k in range(4)) + '</g>')
    return f'<rect x="120" y="320" width="330" height="80" rx="18" {V} />{cav}{dough}{pieces}{press}'


def _form_js(i, t):
    return [f'    tl.fromTo("#jj-m{i} .fx", {{ y: 0 }}, {{ y: 170, duration: 0.45, ease: "power3.in", yoyo: true, repeat: 1, repeatDelay: 0.25 }}, {t + 0.45:.2f});',
            f'    tl.to("#jj-m{i} .fd", {{ opacity: 0, duration: 0.15 }}, {t + 0.9:.2f});',
            f'    tl.fromTo("#jj-m{i} .fp", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: -24, duration: 0.5, ease: "back.out(2)", stagger: 0.1 }}, {t + 1.5:.2f});']


def _inoculate(a, b, cc):
    """Drops of culture fall from a pipette onto the medium and colonies spread from each."""
    xs = (190, 250, 310, 370)
    pip = (f'<g class="ip"><rect x="262" y="10" width="36" height="110" rx="12" fill="rgba(255,255,255,0.14)" stroke="#dfe6ee" stroke-width="4" />'
           f'<rect x="268" y="56" width="24" height="58" rx="8" fill="{rgba(b, 0.8)}" /><path d="M268 120 L292 120 L284 170 L276 170 Z" fill="#dfe6ee" /></g>')
    drops = "".join(f'<path class="id" d="M{x} 180 C {x - 8} 192, {x - 8} 202, {x} 206 C {x + 8} 202, {x + 8} 192, {x} 180 Z" fill="{b}" opacity="0" />' for x in xs)
    cols = "".join(f'<circle class="ic" cx="{x}" cy="{326 + (k % 2) * 22}" r="26" fill="{rgba(b, 0.55)}" stroke="{b}" stroke-width="3" opacity="0" />' for k, x in enumerate(xs))
    dish = (f'<ellipse cx="280" cy="340" rx="200" ry="70" {V} /><ellipse cx="280" cy="336" rx="178" ry="56" fill="{rgba(a, 0.32)}" />')
    return dish + cols + drops + pip


def _inoculate_js(i, t):
    return [f'    tl.fromTo("#jj-m{i} .ip", {{ x: -90 }}, {{ x: 90, duration: 1.6, ease: "none" }}, {t + 0.4:.2f});',
            f'    tl.fromTo("#jj-m{i} .id", {{ y: 0, opacity: 0 }}, {{ y: 130, opacity: 1, duration: 0.45, ease: "power2.in", stagger: 0.4 }}, {t + 0.45:.2f});',
            f'    tl.fromTo("#jj-m{i} .ic", {{ scale: 0.1, opacity: 0, transformOrigin: "50% 50%" }}, {{ scale: 1, opacity: 1, duration: 0.8, ease: "power2.out", stagger: 0.4 }}, {t + 0.9:.2f});']


def _sterilize(a, b, cc):
    """A sealed chamber under pressure: the gauge climbs, heat waves pass, a check mark lands."""
    jars = "".join(f'<rect x="{170 + k * 76}" y="250" width="56" height="110" rx="14" fill="{rgba(a, 0.45)}" stroke="rgba(255,255,255,0.6)" stroke-width="3" />' for k in range(3))
    waves = "".join(f'<path class="sw" d="M150 {230 + k * 50} q 26 -16 52 0 t 52 0 t 52 0 t 52 0 t 52 0" fill="none" stroke="#ff9a5c" stroke-width="4" stroke-linecap="round" opacity="0" />' for k in range(3))
    gauge = ('<g transform="translate(450 110)"><circle r="54" fill="rgba(0,0,0,0.3)" stroke="rgba(255,255,255,0.5)" stroke-width="6" />'
             '<path d="M -38 38 A 54 54 0 1 1 38 38" fill="none" stroke="url(#jj-lg)" stroke-width="8" stroke-linecap="round" />'
             '<line class="sn" x1="0" y1="0" x2="0" y2="-40" stroke="#fff" stroke-width="5" stroke-linecap="round" transform="rotate(-130)" /><circle r="7" fill="#fff" /></g>')
    check = f'<path class="sk" d="M236 210 L268 244 L330 176" fill="none" stroke="{b}" stroke-width="16" stroke-linecap="round" stroke-linejoin="round" opacity="0" />'
    return f'<rect x="120" y="160" width="300" height="240" rx="40" {V} /><rect x="104" y="150" width="332" height="26" rx="13" fill="rgba(255,255,255,0.35)" />{jars}{waves}{gauge}{check}'


def _sterilize_js(i, t):
    return [f'    tl.to("#jj-m{i} .sn", {{ rotation: 50, svgOrigin: "0 0", duration: 1.0, ease: "power2.out" }}, {t + 0.4:.2f});',
            f'    tl.fromTo("#jj-m{i} .sw", {{ x: -20, opacity: 0 }}, {{ x: 20, opacity: 0.9, duration: 0.6, ease: "sine.inOut", stagger: {{ each: 0.15, repeat: 1, yoyo: true }} }}, {t + 0.5:.2f});',
            f'    tl.fromTo("#jj-m{i} .sk", {{ opacity: 0, scale: 0.6, transformOrigin: "50% 50%" }}, {{ opacity: 1, scale: 1, duration: 0.5, ease: "back.out(2)" }}, {t + 1.7:.2f});']


def _coat(a, b, cc):
    """A nozzle sprays fine droplets over pieces on a belt and each piece takes on the coat."""
    pieces = "".join(f'<ellipse class="cp" cx="{170 + k * 74}" cy="330" rx="30" ry="18" fill="#efe1c0" stroke="rgba(255,255,255,0.4)" stroke-width="3" />' for k in range(4))
    spray = "".join(f'<circle class="cy" cx="{280 + (k % 5 - 2) * 14}" cy="{150 + (k // 5) * 10}" r="4" fill="{b}" opacity="0" />' for k in range(15))
    nozzle = f'<rect x="250" y="30" width="60" height="80" rx="12" fill="{cc}" /><path d="M262 110 L298 110 L290 136 L270 136 Z" fill="#dfe6ee" />'
    belt = '<rect x="110" y="356" width="340" height="24" rx="12" fill="rgba(255,255,255,0.14)" stroke="rgba(255,255,255,0.4)" stroke-width="3" />'
    return f'{belt}{pieces}{spray}{nozzle}'


def _coat_js(i, t):
    return [f'    tl.fromTo("#jj-m{i} .cp", {{ x: 36 }}, {{ x: -36, duration: 1.8, ease: "none" }}, {t + 0.4:.2f});',
            f'    tl.fromTo("#jj-m{i} .cy", {{ y: 0, opacity: 0 }}, {{ y: (k) => 150 + (k % 3) * 10, x: (k) => (k % 5 - 2) * 26, opacity: 0.9, duration: 0.55, ease: "power1.in", stagger: {{ each: 0.04, repeat: 2 }} }}, {t + 0.45:.2f});',
            f'    tl.to("#jj-m{i} .cp", {{ attr: {{ stroke: "{"#fff"}" }}, fill: "#e6b860", duration: 0.4, stagger: 0.25 }}, {t + 0.9:.2f});']


def _pack(a, b, cc):
    """Pieces drop into a pouch, then the sealing bar closes the top."""
    pouch = f'<path d="M170 140 L390 140 L400 410 Q280 424 160 410 Z" {V} />'
    items = "".join(f'<ellipse class="pi" cx="{210 + (k % 3) * 70}" cy="{360 - (k // 3) * 46}" rx="26" ry="16" fill="#efe1c0" stroke="{a}" stroke-width="2" opacity="0" />' for k in range(6))
    seal = (f'<g class="ps"><rect x="140" y="96" width="280" height="22" rx="8" fill="{cc}" /></g>'
            f'<rect class="pl" x="166" y="136" width="228" height="16" rx="6" fill="{b}" opacity="0" />')
    return pouch + items + seal


def _pack_js(i, t):
    return [f'    tl.fromTo("#jj-m{i} .pi", {{ y: -260, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.45, ease: "power2.in", stagger: 0.12 }}, {t + 0.4:.2f});',
            f'    tl.fromTo("#jj-m{i} .ps", {{ y: 0 }}, {{ y: 36, duration: 0.3, ease: "power3.in", yoyo: true, repeat: 1, repeatDelay: 0.3 }}, {t + 1.35:.2f});',
            f'    tl.fromTo("#jj-m{i} .pl", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.25 }}, {t + 1.65:.2f});']


def _concentrate(a, b, cc):
    """Liquid simmers off as steam; the level falls and the colour deepens."""
    steam = "".join(f'<path class="cs" d="M{200 + k * 80} 150 C {180 + k * 80} 120, {230 + k * 80} 100, {205 + k * 80} 60" fill="none" stroke="rgba(255,255,255,0.6)" stroke-width="5" stroke-linecap="round" opacity="0" />' for k in range(3))
    flame = "".join(f'<path class="cf" d="M{200 + k * 80} 432 C {184 + k * 80} 410, {204 + k * 80} 392, {200 + k * 80} 372 C {222 + k * 80} 394, {218 + k * 80} 414, {200 + k * 80} 432 Z" fill="#ff7a3c" />' for k in range(3))
    marks = "".join(f'<line x1="132" y1="{220 + k * 40}" x2="152" y2="{220 + k * 40}" stroke="rgba(255,255,255,0.5)" stroke-width="3" />' for k in range(4))
    return (f'<rect x="120" y="170" width="320" height="200" rx="30" {V} />'
            f'<rect class="cl" x="138" y="200" width="284" height="154" rx="20" fill="{rgba(a, 0.4)}" />{marks}{steam}{flame}')


def _concentrate_js(i, t):
    return [f'    tl.fromTo("#jj-m{i} .cs", {{ opacity: 0, y: 20 }}, {{ opacity: 1, y: -10, duration: 0.9, ease: "sine.out", stagger: {{ each: 0.2, repeat: 2, yoyo: true }} }}, {t + 0.45:.2f});',
            f'    tl.fromTo("#jj-m{i} .cl", {{ scaleY: 1, transformOrigin: "50% 100%" }}, {{ scaleY: 0.5, fillOpacity: 2.2, duration: 1.8, ease: "power1.inOut" }}, {t + 0.5:.2f});',
            f'    tl.fromTo("#jj-m{i} .cf", {{ scaleY: 0.7, transformOrigin: "50% 100%" }}, {{ scaleY: 1.15, duration: 0.3, ease: "sine.inOut", yoyo: true, repeat: 7, stagger: 0.1 }}, {t + 0.2:.2f});']


def _harvest(a, b, cc):
    """Fruit on the plant ripen, then drop into a basket."""
    stem = '<path d="M180 400 C 170 300, 200 200, 190 60" fill="none" stroke="#6fa34a" stroke-width="10" stroke-linecap="round" />'
    leaves = "".join(f'<path d="M{190 + (k % 2) * 4} {110 + k * 60} q {50 if k % 2 else -50} -20 {70 if k % 2 else -70} 10 q {-40 if k % 2 else 40} 20 {-70 if k % 2 else 70} -10 Z" fill="#7cbf52" />' for k in range(4))
    fruit = [(250, 140), (240, 220), (128, 180), (130, 280)]
    fr = "".join(f'<circle class="hf" cx="{x}" cy="{y}" r="22" fill="#9ccc65" stroke="#2e5a1c" stroke-width="2" />' for x, y in fruit)
    basket = (f'<path d="M300 330 L480 330 L460 410 L320 410 Z" fill="{rgba(cc, 0.5)}" stroke="rgba(255,255,255,0.6)" stroke-width="4" />'
              + "".join(f'<line x1="{320 + k * 30}" y1="334" x2="{328 + k * 26}" y2="406" stroke="rgba(255,255,255,0.3)" stroke-width="3" />' for k in range(6)))
    return stem + leaves + basket + fr


def _harvest_js(i, t):
    pts = [(250, 140), (240, 220), (128, 180), (130, 280)]
    js = [f'    tl.to("#jj-m{i} .hf", {{ fill: "#e0573a", duration: 0.7, stagger: 0.08 }}, {t + 0.3:.2f});']
    for k, (x, y) in enumerate(pts):  # each fruit lands at its own spot in the basket
        tx, ty = 340 + k * 34 - x, 310 - y
        js.append(f'    tl.to("#jj-m{i} .hf:nth-of-type({k + 1})", {{ x: {tx}, y: {ty}, duration: 0.5, ease: "power2.in" }}, {t + 0.9 + k * 0.12:.2f});')
    return js


def _extrude(a, b, cc):
    """A screw turns inside the barrel and the strand pushes out of the die."""
    flights = "".join(f'<path class="ef" d="M{150 + k * 36} 196 L{168 + k * 36} 244" stroke="#dfe6ee" stroke-width="6" stroke-linecap="round" />' for k in range(7))
    barrel = (f'<rect x="120" y="180" width="300" height="80" rx="20" {V} /><rect x="136" y="214" width="268" height="12" rx="6" fill="#dfe6ee" />{flights}'
              f'<path d="M150 180 L130 90 L230 90 L210 180 Z" {V} /><rect x="420" y="196" width="34" height="48" rx="8" fill="{cc}" />')
    feed = "".join(f'<ellipse class="eg" cx="{160 + k * 14}" cy="110" rx="9" ry="6" fill="#efe1c0" />' for k in range(4))
    strand = f'<rect class="es" x="454" y="208" width="96" height="24" rx="12" fill="#efe1c0" stroke="{a}" stroke-width="2" />'
    return barrel + feed + strand


def _extrude_js(i, t):
    return [f'    tl.fromTo("#jj-m{i} .ef", {{ x: 0 }}, {{ x: 36, duration: 0.4, ease: "none", repeat: 4 }}, {t + 0.4:.2f});',
            f'    tl.fromTo("#jj-m{i} .eg", {{ y: 0, opacity: 1 }}, {{ y: 90, opacity: 0, duration: 0.6, ease: "power1.in", stagger: 0.15 }}, {t + 0.4:.2f});',
            f'    tl.fromTo("#jj-m{i} .es", {{ scaleX: 0, transformOrigin: "0% 50%" }}, {{ scaleX: 1, duration: 1.6, ease: "power1.out" }}, {t + 0.7:.2f});']


ART = {"mill": (_mill, _mill_js), "form": (_form, _form_js), "inoculate": (_inoculate, _inoculate_js),
       "sterilize": (_sterilize, _sterilize_js), "coat": (_coat, _coat_js), "pack": (_pack, _pack_js),
       "concentrate": (_concentrate, _concentrate_js), "harvest": (_harvest, _harvest_js), "extrude": (_extrude, _extrude_js)}
