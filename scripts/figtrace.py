"""Turn a patent line drawing into vector strokes the videos can draw on (pen-style), for any patent.

Black-and-white mechanical drawings (the usual 도면) are decoded with ffmpeg, binarised, thinned to one-pixel lines
(Zhang–Suen, numpy) and walked into polylines, then simplified (Douglas–Peucker). Photos, colour renders and greyscale
plates are detected and skipped — only real line art is redrawn. Results are cached in data/fig_trace/<appno>/<figure>.json
as {"w", "h", "paths": [[[x, y], ...], ...]} in image-fraction coordinates (0–1), ordered left to right.

Usage: python -I tools/figtrace.py <appno> <figure-file> [...]      (prints a one-line summary per figure)
       python -I tools/figtrace.py --content data/content/*.json    (every anatomy figure)
"""
import json
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate import appno_ok, figure_ok  # noqa: E402  same file-name rules as the content check

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "fig_trace")
MAX_DIM = 900          # working resolution: enough for linework, small enough for a scene
MIN_LEN = 10           # px: shorter fragments are noise
MAX_PATHS = 700


def _dims(path):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from visuals import _dims as d
    return d(path)


def load_gray(path):
    w, h = _dims(path)
    s = min(1.0, MAX_DIM / max(w, h))
    W, H = max(2, int(w * s) // 2 * 2), max(2, int(h * s) // 2 * 2)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={W}:{H}:flags=area,format=gray", "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.uint8).reshape(H, W)


def is_line_art(g):
    """Mostly white paper with thin dark ink, few mid-tones (photos and shaded renders fail this)."""
    ink = (g < 128).mean()
    mid = ((g > 70) & (g < 190)).mean()
    return 0.004 < ink < 0.22 and mid < 0.12


def thin(b):
    """Zhang–Suen thinning on a boolean image (True = ink)."""
    img = np.pad(b.astype(np.uint8), 1)
    while True:
        changed = False
        for step in (0, 1):
            p = img
            P2, P3, P4 = p[:-2, 1:-1], p[:-2, 2:], p[1:-1, 2:]
            P5, P6, P7 = p[2:, 2:], p[2:, 1:-1], p[2:, :-2]
            P8, P9 = p[1:-1, :-2], p[:-2, :-2]
            nb = [P2, P3, P4, P5, P6, P7, P8, P9]
            B = sum(x.astype(np.int16) for x in nb)
            seq = nb + [P2]
            A = sum(((seq[k] == 0) & (seq[k + 1] == 1)).astype(np.int16) for k in range(8))
            c = p[1:-1, 1:-1] == 1
            if step == 0:
                m = c & (B >= 2) & (B <= 6) & (A == 1) & ((P2 * P4 * P6) == 0) & ((P4 * P6 * P8) == 0)
            else:
                m = c & (B >= 2) & (B <= 6) & (A == 1) & ((P2 * P4 * P8) == 0) & ((P2 * P6 * P8) == 0)
            if m.any():
                img[1:-1, 1:-1][m] = 0
                changed = True
        if not changed:
            return img[1:-1, 1:-1].astype(bool)


NB = [(-1, 0), (0, 1), (1, 0), (0, -1), (-1, 1), (1, 1), (1, -1), (-1, -1)]  # 4-neighbours first: cleaner walks


def walk(sk):
    """Polylines from a one-pixel skeleton: from endpoints first, then whatever loops remain.
    A diagonal step counts only when no 4-neighbour already links the two pixels, so staircases are not junctions."""
    H, W = sk.shape
    pts = set(zip(*np.nonzero(sk)))

    def nbrs(p):
        y, x = p
        out = [(y + dy, x + dx) for dy, dx in NB[:4] if (y + dy, x + dx) in pts]
        for dy, dx in NB[4:]:
            q = (y + dy, x + dx)
            if q in pts and (y + dy, x) not in pts and (y, x + dx) not in pts:
                out.append(q)
        return out
    adj = {p: nbrs(p) for p in pts}
    deg = {p: len(v) for p, v in adj.items()}
    seen_edge = set()
    paths = []

    def step_from(a, b):
        path = [a, b]
        prev, cur = a, b
        while True:
            if deg.get(cur, 0) != 2:
                return path
            nxt = next((q for q in adj[cur] if q != prev and frozenset((cur, q)) not in seen_edge), None)
            if nxt is None:
                return path
            seen_edge.add(frozenset((cur, nxt)))
            path.append(nxt)
            prev, cur = cur, nxt
            if cur == path[0]:
                return path

    starts = sorted((p for p in pts if deg[p] != 2), key=lambda p: (p[1], p[0]))
    for a in starts:
        for b in adj[a]:
            if frozenset((a, b)) not in seen_edge:
                seen_edge.add(frozenset((a, b)))
                paths.append(step_from(a, b))
    for a in sorted(pts, key=lambda p: (p[1], p[0])):  # closed loops (all degree 2)
        for b in adj[a]:
            if frozenset((a, b)) not in seen_edge:
                seen_edge.add(frozenset((a, b)))
                paths.append(step_from(a, b))
    return paths


def simplify(pl, eps=1.2):
    """Douglas–Peucker on [(y, x), ...]."""
    if len(pl) < 3:
        return pl
    a, b = np.array(pl[0], float), np.array(pl[-1], float)
    ab = b - a
    n = np.hypot(*ab) or 1.0
    d = [abs(ab[1] * (p[0] - a[0]) - ab[0] * (p[1] - a[1])) / n for p in pl]
    i = int(np.argmax(d))
    if d[i] <= eps:
        return [pl[0], pl[-1]]
    return simplify(pl[:i + 1], eps)[:-1] + simplify(pl[i:], eps)


def length(pl):
    return sum(np.hypot(pl[k][0] - pl[k - 1][0], pl[k][1] - pl[k - 1][1]) for k in range(1, len(pl)))


def trace(path):
    """Vector strokes for one figure, or None when it is not line art."""
    g = load_gray(path)
    if not is_line_art(g):
        return None
    sk = thin(g < 140)
    H, W = sk.shape
    lines = [simplify(p) for p in walk(sk)]
    lines = [p for p in lines if length(p) >= MIN_LEN]
    lines.sort(key=lambda p: (min(q[1] for q in p), min(q[0] for q in p)))
    if len(lines) > MAX_PATHS:  # keep the longest strokes, in drawing order
        keep = set(map(id, sorted(lines, key=length, reverse=True)[:MAX_PATHS]))
        lines = [p for p in lines if id(p) in keep]
    return {"w": W, "h": H, "paths": [[[round(x / W, 4), round(y / H, 4)] for y, x in p] for p in lines]}


def cached(appno, fn):
    """Trace from cache (or compute and cache). None for non-line-art; cached as {"skip": true}."""
    if not (appno_ok(appno) and figure_ok(fn)):  # both come from content JSON / argv and become paths
        return None
    out = os.path.join(CACHE, appno, fn + ".json")
    if os.path.exists(out):
        d = json.load(open(out, encoding="utf-8"))
        return None if d.get("skip") else d
    src = os.path.join(ROOT, "data", "patents", appno, fn)
    if not os.path.exists(src):
        return None
    try:
        d = trace(src)
    except Exception:  # an odd image must never break a build
        d = None
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(d or {"skip": True}, open(out, "w", encoding="utf-8"))
    return d


def main(args):
    sys.stdout.reconfigure(encoding="utf-8")
    jobs = []
    if args and args[0] == "--content":
        for p in args[1:]:
            c = json.load(open(p, encoding="utf-8"))
            if c["proof"].get("kind") == "anatomy" and c["proof"].get("figure"):
                jobs.append((c["appno"], c["proof"]["figure"]))
    else:
        jobs = list(zip(args[0::2], args[1::2]))
    for appno, fn in jobs:
        if not (appno_ok(appno) and figure_ok(fn)):
            print(appno, fn, "skip (appno must be 13 digits, figure a fig-p<N>-<name>.jpg|png file name)")
            continue
        d = cached(appno, fn)
        print(appno, fn, "skip (not line art)" if d is None else f'{len(d["paths"])} strokes · {d["w"]}x{d["h"]}')


if __name__ == "__main__":
    main(sys.argv[1:])
