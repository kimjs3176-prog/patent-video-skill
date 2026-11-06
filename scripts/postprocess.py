"""Post-build passes shared by every template (run by produce.py after each build).

1. pen_draw: line-icon / connector draw-ons were one stroke-dashoffset tween per path with a stagger, so every short path
   accelerated, stopped and the next one started — it read as choppy, and the round caps of not-yet-drawn paths showed as dots.
   Each such tween is rewritten to penDraw(): one eased progress per icon drives all of its paths in sequence, each path
   taking time in proportion to its real length (getTotalLength, measured once at mount), so the pen never stops; paths stay
   invisible until the pen reaches them. Several icons in one selector draw one after another with a short overlap.
   Linear draws (ease none, e.g. a path a dot travels along) are left alone.
2. fonts: per-video subsetting (fontsub.py).

Usage: python -I tools/postprocess.py <project dir> [...]
"""
import glob
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fontsub import subset_project  # noqa: E402
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PEN = """    const penDraw = (sel, at, dur, gap) => {
      const els = Array.from(document.querySelectorAll(sel)); const groups = new Map();
      for (const el of els) { const svg = el.ownerSVGElement || el; if (!groups.has(svg)) groups.set(svg, []); groups.get(svg).push(el); }
      let k = 0;
      for (const list of groups.values()) {
        const len = list.map((el) => { try { return Math.max(1, el.getTotalLength()); } catch (e) { return 40; } });
        const total = len.reduce((a, b) => a + b, 0); const start = []; let acc = 0;
        for (const l of len) { start.push(acc); acc += l; }
        const put = (p) => { const pos = p * total;
          list.forEach((el, i) => { const u = Math.min(1, Math.max(0, (pos - start[i]) / len[i]));
            el.style.strokeDasharray = "1 1"; el.style.strokeDashoffset = String(1 - u); el.style.opacity = u > 0 ? "" : "0"; }); };
        put(0); const o = { p: 0 };
        tl.to(o, { p: 1, duration: dur, ease: "power1.inOut", onUpdate: () => put(o.p) }, at + k * gap); k += 1;
      }
    };
"""
CALL = re.compile(r'tl\.fromTo\((?P<sel>[^;]*?), \{ ?strokeDasharray: 1, strokeDashoffset: 1 ?\}, \{ ?strokeDashoffset: 0, duration: (?P<d>[\d.]+), '
                  r'ease: "(?!none")[^"]+"(?:, stagger: (?P<s>[\d.]+))? ?\}, (?P<t>[^;]+?)\);')


def pen_draw(out):
    n = 0
    for p in glob.glob(os.path.join(out, "compositions", "*.html")):
        s = open(p, encoding="utf-8").read()
        if "strokeDashoffset: 1" not in s:
            continue

        def sub(m):
            d, st = float(m.group("d")), float(m.group("s") or 0)
            dur = round(min(2.6, d + 2.5 * st), 2)
            gap = round(max(0.12, 3 * st), 2)
            return f'penDraw({m.group("sel")}, {m.group("t")}, {dur}, {gap});'
        s2, k = CALL.subn(sub, s)
        if k:
            # after the timeline is created, whatever its options (some templates set defaults)
            s2 = re.sub(r"(const tl = gsap\.timeline\([^;]*\);)", lambda m: m.group(1) + "\n" + PEN, s2, count=1)
            open(p, "w", encoding="utf-8").write(s2)
            n += k
    return n


def drop_missing_audio(out):
    """Remove <audio> clips whose file is not in the project (music / sfx are optional assets)."""
    ip = os.path.join(out, "index.html")
    s = open(ip, encoding="utf-8").read()
    gone = []

    def keep(m):
        dst = os.path.join(out, m.group(1).replace("/", os.sep))
        own = os.path.join(ROOT, "data", "music", os.path.basename(dst))  # a patent's own bed (compose.py), copied on demand
        if not os.path.exists(dst) and m.group(1).startswith("assets/music/") and os.path.exists(own):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(own, dst)
        if os.path.exists(dst):
            return m.group(0)
        gone.append(m.group(1))
        return ""
    s2 = re.sub(r'\n?\s*<audio [^>]*src="(assets/[^"]+)"[^>]*></audio>', keep, s)
    if gone:
        open(ip, "w", encoding="utf-8").write(s2)
    return gone


# pathLength="1" lets a builder write dash draw-ons as 0→1, but Chrome maps that unit unevenly when the offset is tweened
# through CSS (the stroke stays hidden, then appears all at once). Swap it for the element's real length before the
# timeline is built, so every draw-on advances smoothly with its ease.
REAL_LENGTH = ('    document.querySelectorAll(\'[pathLength="1"]\').forEach((el) => { const L = el.getTotalLength(); el.removeAttribute("pathLength");'
               ' const da = el.getAttribute("stroke-dasharray"); if (da === "1 1") el.setAttribute("stroke-dasharray", L + " " + L);'
               ' const off = parseFloat(el.getAttribute("stroke-dashoffset") || "0"); el.setAttribute("stroke-dashoffset", String(off * L)); });\n')


def real_lengths(out):
    n = 0
    for fn in glob.glob(os.path.join(out, "compositions", "*.html")):
        s = open(fn, encoding="utf-8").read()
        if 'pathLength="1"' not in s or "getTotalLength(); el.removeAttribute" in s:
            continue
        i = s.find("    const tl = gsap.timeline")
        if i < 0:
            continue
        open(fn, "w", encoding="utf-8").write(s[:i] + REAL_LENGTH + s[i:])
        n += 1
    return n


def run(out):
    gone = drop_missing_audio(out)
    real_lengths(out)
    k = pen_draw(out)
    f, saved = subset_project(out)
    return f"pen-draw {k}, fonts {f} (-{saved / 1e6:.1f} MB)" + (f", missing audio dropped: {len(gone)}" if gone else "")


if __name__ == "__main__":
    for d in sys.argv[1:]:
        print(d, run(d))
