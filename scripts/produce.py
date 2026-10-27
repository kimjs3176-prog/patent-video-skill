"""Build, check and render every content JSON in production order. Resumable.

Usage: python -I -u tools/produce.py [--template A..I] [--narrate [--voice ko-KR-SunHiNeural]] [--no-render] [order ...]
Template A writes renders/<order>-<appno>.mp4; template X writes renders_x/... ; --narrate adds a voice-over and the suffix _nar.
One log line per video in renders*/produce.log.
"""
import glob
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import build as build_a  # noqa: E402
import build_b  # noqa: E402
import build_c  # noqa: E402
import build_def  # noqa: E402
import build_ghi  # noqa: E402
import build_sig  # noqa: E402
from validate import check as validate  # noqa: E402
import narration  # noqa: E402
import postprocess  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NPX = "npx.cmd" if os.name == "nt" else "npx"
ENV = dict(os.environ, HYPERFRAMES_SKIP_SKILLS="1")


TEMPLATE = "A"
NARRATE = False
VOICE = narration.VOICE
BUILDERS = {"A": build_a, "B": build_b.build, "C": build_c.build,
            "D": lambda p: build_def.build("D", p), "E": lambda p: build_def.build("E", p), "F": lambda p: build_def.build("F", p),
            "G": lambda p: build_ghi.build("G", p), "H": lambda p: build_ghi.build("H", p), "I": lambda p: build_ghi.build("I", p),
            "S": build_sig.build}


def render_dir():
    return os.path.join(ROOT, "renders" if TEMPLATE == "A" else "renders_" + TEMPLATE.lower())


def log(msg):
    os.makedirs(render_dir(), exist_ok=True)
    with open(os.path.join(render_dir(), "produce.log"), "a", encoding="utf-8") as f:
        f.write(time.strftime("%H:%M:%S ") + msg + "\n")
    print(msg, flush=True)


def check_project(out):
    subprocess.run([NPX, "hyperframes@0.8.207", "check", "--json"], cwd=out, env=ENV, capture_output=True, timeout=600)
    reports = glob.glob(os.path.join(out, ".hyperframes", "artifacts", "checks", "*.json"))
    d = json.load(open(max(reports, key=os.path.getmtime), encoding="utf-8"))
    errs = sum(v.get("errorCount", 0) for v in d.values() if isinstance(v, dict) and "ok" in v)
    warns = [f'{k}:{x.get("code")}' for k, v in d.items() if isinstance(v, dict) for x in v.get("findings", []) if x.get("severity") == "warning"]
    return errs, warns


def main():
    global TEMPLATE, NARRATE, VOICE
    args = sys.argv[1:]
    if "--voice" in args:
        VOICE = args[args.index("--voice") + 1]
        args = [a for i, a in enumerate(args) if a != "--voice" and (i == 0 or args[i - 1] != "--voice")]
    NARRATE = "--narrate" in args
    if "--template" in args:
        TEMPLATE = args[args.index("--template") + 1].upper()
        args = [a for i, a in enumerate(args) if a != "--template" and (i == 0 or args[i - 1] != "--template")]
    render = "--no-render" not in args
    want = {int(a) for a in args if a.isdigit()}
    done = set()
    while True:  # re-scan after each pass so contents written meanwhile are picked up
        files = [p for p in sorted(glob.glob(os.path.join(ROOT, "data", "content", "*.json")))
                 if (p, os.path.getmtime(p)) not in done]
        if not files:
            break
        for path in files:
            done.add((path, os.path.getmtime(path)))
            one(path, render, want)


def one(path, render, want):
    order = int(os.path.basename(path).split("-")[0])
    if want and order not in want:
        return
    slug = os.path.basename(path)[:-5]
    mp4 = os.path.join(render_dir(), slug + ("" if TEMPLATE == "A" else "_" + TEMPLATE.lower()) + ("_nar" if NARRATE else "") + ".mp4")
    # skip only if the render is newer than its content (edited content gets re-rendered)
    if render and os.path.exists(mp4) and os.path.getmtime(mp4) > os.path.getmtime(path):
        return
    v = validate(path)
    if v:
        log(f"{slug} SKIP content: {' / '.join(v)[:300]}")
        return
    out = BUILDERS[TEMPLATE](path)
    postprocess.run(out)  # continuous pen draw-ons + per-video font subsets
    if NARRATE:
        try:
            rep = narration.narrate(out, json.load(open(path, encoding="utf-8")), VOICE)
            log(f"{slug} narration " + " | ".join(r.split(":")[0] for r in rep))
        except Exception as e:  # network or TTS failure: keep the video, say why
            log(f"{slug} SKIP narration failed: {e}")
            return
    errs, warns = check_project(out)
    if errs:
        log(f"{slug} SKIP check errors={errs} {warns[:5]}")
        return
    if not render:
        log(f"{slug} built ok warnings={len(warns)} {sorted(set(warns))[:4]}")
        return
    t = time.time()
    r = subprocess.run([NPX, "hyperframes@0.8.207", "render", "-q", "delivery", "-o", mp4], cwd=out, env=ENV, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=1800)
    ok = r.returncode == 0 and os.path.exists(mp4)
    log(f"{slug} {'RENDERED' if ok else 'RENDER FAIL'} {time.time() - t:.0f}s warnings={len(warns)}" + ("" if ok else " " + r.stdout[-300:]))


if __name__ == "__main__":
    main()
