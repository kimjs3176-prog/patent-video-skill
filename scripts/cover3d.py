"""A three.js layer behind every template's cover: particles shaped after the patent's field swirling around the title
(and, on dark covers, two glowing rings). Added by postprocess after the build; produce.py --no-3d leaves it out.

The layer is a transparent WebGL canvas, the first child of the cover's <div id="<scene>-in">, so the template's own
background shows through and every word stays on top. It is driven by the cover's GSAP timeline (a tween's onUpdate
draws the frame for that time), never by requestAnimationFrame, and the particles come from a fixed seed: the same
content renders the same frames, and HyperFrames can seek to any frame. Costs: about +0.2-0.3 s per cover frame on a
CPU-only renderer (a 5-6 s cover adds roughly half a minute to a video).
"""
import json
import os
import re

THREE = "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js"  # pinned, like GSAP; UMD build (window.THREE)
GSAP_TAG = '<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>'
MARK = "/* cover3d */"
DARK = {"A", "C", "D", "E", "F", "S"}  # covers on a dark ground: rings and light particles; the rest get soft dark particles
COUNT = 380  # particles: fewer than the 650 of the pilot, nearly the same look, less time per frame
SCALE = 0.75  # the canvas draws at 3/4 size and is shown full size (soft particles lose nothing, the GPU-less render gains)

# particle shape by the patent's hero pictogram (CONTENT_SPEC 'hero'); anything else is a small faceted crystal
SHAPES = {
    "grain": ("rice", "seed", "beer", "bowl", "cookpot", "cup", "fork", "tractor"),
    "cell": ("cell", "flask", "dna", "capsule", "shield", "bee", "animal", "fish", "mushroom"),
    "drop": ("water", "drop", "pot", "bottle", "snow"),
    "leaf": ("leaf", "sprout", "sun", "globe", "home"),
}


def shape_of(c):
    hero = (c.get("hero") or "").lower()
    return next((s for s, names in SHAPES.items() if hero in names), "crystal")


def colors_of(c):
    from build import PALETTES
    return list(PALETTES.get(c.get("palette", "blue"), PALETTES["blue"]))


def script(w, h, dur, dark, colors, shape, n=COUNT):
    """The JS that builds the scene inside a cover composition (uses that composition's `tl`)."""
    cfg = json.dumps({"w": w, "h": h, "dur": dur, "dark": dark, "colors": colors, "shape": shape, "n": n, "scale": SCALE})
    return MARK + """
    (function () {
      const C = """ + cfg + """;
      const T = window.THREE, cv = document.getElementById("cover3d");
      if (!T || !cv) return;  // no three.js (offline render): the cover simply has no 3D layer
      const r = new T.WebGLRenderer({ canvas: cv, antialias: true, alpha: true, preserveDrawingBuffer: true });
      r.setPixelRatio(1); r.setSize(Math.round(C.w * C.scale), Math.round(C.h * C.scale), false); r.setClearColor(0x000000, 0);
      r.outputColorSpace = T.SRGBColorSpace; r.toneMapping = T.ACESFilmicToneMapping; r.toneMappingExposure = C.dark ? 1.15 : 1.0;
      const sc = new T.Scene(), tall = C.h > C.w;
      const cam = new T.PerspectiveCamera(tall ? 58 : 38, C.w / C.h, 0.1, 100);
      const col = C.colors.map((x) => new T.Color(x));
      sc.add(new T.AmbientLight(0xffffff, C.dark ? 0.3 : 0.9));
      const l1 = new T.PointLight(col[0], 60, 40); l1.position.set(-6, 4, 6); sc.add(l1);
      const l2 = new T.PointLight(col[2], 50, 40); l2.position.set(7, -3, 4); sc.add(l2);
      const key = new T.DirectionalLight(0xffffff, 1.2); key.position.set(2, 6, 8); sc.add(key);
      const rings = [];
      if (C.dark) {  // two thin glowing rings under the title
        [[5.2, 0.04, 1, -0.9, 0], [6.3, 0.02, 0, -1.1, 0.18]].forEach(([R, t, k, y, ry]) => {
          const m = new T.Mesh(new T.TorusGeometry(R, t, 16, 220),
            new T.MeshStandardMaterial({ color: col[k], emissive: col[k], emissiveIntensity: 2, metalness: 0.3, roughness: 0.3 }));
          m.rotation.x = 1.3; m.rotation.y = ry; m.position.y = y; sc.add(m); rings.push(m);
        });
      }
      const geo = {
        grain: () => new T.CapsuleGeometry(0.04, 0.1, 4, 10),
        cell: () => new T.SphereGeometry(0.07, 16, 12),
        drop: () => new T.SphereGeometry(0.06, 16, 12),
        leaf: () => new T.SphereGeometry(0.08, 14, 10),
        crystal: () => new T.OctahedronGeometry(0.07, 0),
      }[C.shape]();
      if (C.shape === "leaf") geo.scale(1, 0.22, 0.55);
      if (C.shape === "drop") geo.scale(0.8, 1.25, 0.8);
      const base = C.dark ? new T.Color(0xffffff) : new T.Color(0x1d1d24);
      const mat = new T.MeshStandardMaterial({ metalness: 0.1, roughness: C.shape === "drop" ? 0.12 : 0.35,
        transparent: !C.dark, opacity: C.dark ? 1 : 0.55, emissive: C.dark ? 0x2a1a10 : 0x000000 });
      const inst = new T.InstancedMesh(geo, mat, C.n); sc.add(inst);
      let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
      const P = [], o = new T.Object3D(), q = new T.Color();
      for (let i = 0; i < C.n; i++) {
        P.push({ rad: 5.6 + rnd() * 4.5, ang: rnd() * Math.PI * 2, h: (rnd() - 0.5) * 2.4 * (0.4 + rnd()),
          sp: 0.25 + rnd() * 0.5, rx: rnd() * 6, ry: rnd() * 6, s: 0.7 + rnd() * 0.9 });
        inst.setColorAt(i, q.copy(col[i % 3]).lerp(base, C.dark ? 0.55 + rnd() * 0.4 : 0.35 + rnd() * 0.3));
      }
      const yb = tall ? -3.2 : -1.9;  // the swirl lies below the title (lower still on 9:16)
      const draw = (t) => {
        const e = 1 - Math.pow(1 - Math.min(1, t / Math.max(1, C.dur)), 3);
        cam.position.set(Math.sin(t * 0.12) * 1.6, 2.4 - e * 0.8, (tall ? 21 : 17) - e * 3.5); cam.lookAt(0, tall ? -1.2 : 0, 0);
        for (let i = 0; i < C.n; i++) {
          const p = P[i], a = p.ang + t * p.sp * (3.2 / p.rad), rr = p.rad * (1.35 - 0.35 * e);
          o.position.set(Math.cos(a) * rr * (tall ? 0.62 : 1), p.h * 0.7 * (0.8 + 0.2 * Math.sin(t + i)) + yb, Math.sin(a) * rr * 0.55 - 1.5);
          o.rotation.set(p.rx + t * 0.8, p.ry + t * 0.6, a); o.scale.setScalar(p.s * Math.min(1, 0.2 + t * 0.8));
          o.updateMatrix(); inst.setMatrixAt(i, o.matrix);
        }
        inst.instanceMatrix.needsUpdate = true;
        rings.forEach((m, k) => { m.rotation.z = (k ? -0.22 : 0.35) * t; m.material.emissiveIntensity = 2 * Math.min(1, t / 1.2); });
        r.render(sc, cam);
      };
      const st = { t: 0 }; draw(0);
      tl.to(st, { t: C.dur, duration: C.dur, ease: "none", onUpdate: () => draw(st.t) }, 0);
    })();
"""


def inject(out, c, template):
    """Add the 3D layer to the built project's cover. Returns the cover file name, or None when there is nothing to do."""
    ip = os.path.join(out, "index.html")
    html = open(ip, encoding="utf-8").read()
    m = re.search(r'id="root" data-composition-id="main"[^>]*data-width="(\d+)" data-height="(\d+)"', html)
    first = re.search(r'<div id="([^"]+)" data-composition-id="[^"]+" data-composition-src="compositions/([^"]+)" data-start="([\d.]+)" '
                      r'data-duration="([\d.]+)"', html)
    if not m or not first:
        return None
    w, h = int(m.group(1)), int(m.group(2))
    sid, fname, dur = first.group(1), first.group(2), float(first.group(4))
    cp = os.path.join(out, "compositions", fname)
    s = open(cp, encoding="utf-8").read()
    if MARK in s:  # already there (postprocess ran twice)
        return fname
    inner, reg = f'<div id="{sid}-in">', f'    window.__timelines["{sid}"] = tl;'
    if inner not in s or reg not in s:
        return None  # a cover built another way: leave it as it is
    canvas = (f'{inner}\n      <canvas id="cover3d" width="{round(w * SCALE)}" height="{round(h * SCALE)}" '
              f'style="position: absolute; left: 0; top: 0; width: {w}px; height: {h}px; pointer-events: none"></canvas>')
    s = s.replace(inner, canvas, 1).replace(reg, "    " + script(w, h, dur, template.upper() in DARK, colors_of(c), shape_of(c)) + reg, 1)
    open(cp, "w", encoding="utf-8").write(s)
    if THREE not in html and GSAP_TAG in html:
        open(ip, "w", encoding="utf-8").write(html.replace(GSAP_TAG, GSAP_TAG + f'\n    <script src="{THREE}"></script>', 1))
    return fname
