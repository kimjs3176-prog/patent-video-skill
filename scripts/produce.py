"""Build, check and render every content JSON in production order. Resumable.

Usage: python -I -u tools/produce.py [--template A..I|S] [--voice ko-KR-Chirp3-HD-Aoede | ko-KR-SunHiNeural] [--no-narrate] [--no-captions] [--no-render] [--no-music-gen] [order ...]
Template A writes renders/<order>-<appno>.mp4; template X writes renders_x/... Every video gets a voice-over (suffix _nar)
unless --no-narrate; its narration.txt (voice + lines) is kept beside the mp4, and a different --voice re-renders.
Narrated videos carry burned-in captions (--no-captions to leave them out); the .srt goes beside the mp4 and to patents/.
Each successful render is also delivered as patents/{출원번호}.mp4 with a thumbnail patents/{출원번호}.jpg (tools/export.py).
One log line per video in renders*/produce.log. When assets/music is empty, background music is made first (tools/music.py):
Google Lyria with GEMINI_API_KEY, otherwise composed by the pipeline itself (no key). A content's `music` block gives that
patent its own composed bed. --no-music-gen skips the automatic beds.
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# python -I ignores PYTHONIOENCODING: keep progress output (Korean, CLI bars) printable on a cp949 console
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import music  # noqa: E402
if __name__ == "__main__" and "--no-music-gen" not in sys.argv:
    music.ensure()  # before the builders load: they read the assets/music list when imported
from build import build as build_a  # noqa: E402
import build_b  # noqa: E402
import build_c  # noqa: E402
import build_def  # noqa: E402
import build_ghi  # noqa: E402
import build_sig  # noqa: E402
from validate import check as validate  # noqa: E402
from export import export  # noqa: E402
import narration  # noqa: E402
import postprocess  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NPX = "npx.cmd" if os.name == "nt" else "npx"
ENV = dict(os.environ, HYPERFRAMES_SKIP_SKILLS="1")


TEMPLATE = "A"
NARRATE = True
CAPTIONS = True
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
    """(error count, warning codes) from `hyperframes check`; a check that did not run counts as an error."""
    t0 = time.time()
    try:
        r = subprocess.run([NPX, "hyperframes@0.8.207", "check", "--json"], cwd=out, env=ENV, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=600)
    except subprocess.TimeoutExpired:
        return 1, ["check:timeout"]
    # only a report written by this run (an older clean report must not pass a project whose check crashed)
    reports = [p for p in glob.glob(os.path.join(out, ".hyperframes", "artifacts", "checks", "*.json")) if os.path.getmtime(p) >= t0 - 1]
    if not reports:
        return 1, [f"check:no-report rc={r.returncode} {(r.stderr or r.stdout or '').strip()[-200:]}"]
    d = json.load(open(max(reports, key=os.path.getmtime), encoding="utf-8"))
    errs = sum(v.get("errorCount", 0) for v in d.values() if isinstance(v, dict) and "ok" in v)
    warns = [f'{k}:{x.get("code")}' for k, v in d.items() if isinstance(v, dict) for x in v.get("findings", []) if x.get("severity") == "warning"]
    return errs, warns


def rendered_voice(mp4):
    """Voice of an earlier narrated render, from the narration.txt copied beside it (house voice when it predates the copy)."""
    try:
        line = open(mp4[:-4] + ".narration.txt", encoding="utf-8").readline()
    except OSError:
        return narration.VOICE
    return line[len("voice: "):].strip() if line.startswith("voice: ") else narration.VOICE


def main():
    global TEMPLATE, NARRATE, VOICE, CAPTIONS
    args = sys.argv[1:]
    if "--voice" in args:
        VOICE = args[args.index("--voice") + 1]
        args = [a for i, a in enumerate(args) if a != "--voice" and (i == 0 or args[i - 1] != "--voice")]
    NARRATE = "--no-narrate" not in args  # --narrate is the default (still accepted)
    if "--template" in args:
        TEMPLATE = args[args.index("--template") + 1].upper()
        args = [a for i, a in enumerate(args) if a != "--template" and (i == 0 or args[i - 1] != "--template")]
    CAPTIONS = "--no-captions" not in args
    args = [a for a in args if a not in ("--no-music-gen", "--no-captions")]
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
            try:
                one(path, render, want)
            except Exception as e:  # one bad content file must not stop the batch
                log(f"{os.path.basename(path)[:-5]} FAIL {type(e).__name__}: {str(e)[:300]}")


def one(path, render, want):
    head = os.path.basename(path).split("-")[0]
    if not head.isdigit() or "-" not in os.path.basename(path):
        log(f"{os.path.basename(path)} SKIP file name is not <order>-<appno>.json")
        return
    order = int(head)
    if want and order not in want:
        return
    slug = os.path.basename(path)[:-5]
    mp4 = os.path.join(render_dir(), slug + ("" if TEMPLATE == "A" else "_" + TEMPLATE.lower()) + ("_nar" if NARRATE else "") + ".mp4")
    # skip only if the render is newer than its content (edited content gets re-rendered) and has the requested voice
    if render and os.path.exists(mp4) and os.path.getmtime(mp4) > os.path.getmtime(path) and (not NARRATE or rendered_voice(mp4) == VOICE):
        deliver = os.path.join(ROOT, "patents", slug.split("-", 1)[1])
        if not (os.path.exists(deliver + ".mp4") and os.path.exists(deliver + ".jpg")):  # an earlier export failed
            dst, jpg = export(mp4, slug.split("-", 1)[1])
            log(f"{slug} exported {os.path.relpath(dst, ROOT)} {os.path.relpath(jpg, ROOT)}")
        return
    if TEMPLATE == "S" and "signature" not in json.load(open(path, encoding="utf-8")):
        log(f"{slug} SKIP template S needs a signature block (CONTENT_SPEC: 시그니처 장면)")
        return
    v = validate(path)
    if v:
        log(f"{slug} SKIP content: {' / '.join(v)[:300]}")
        return
    try:  # the patent's own bed, when its content carries a `music` block (composed once, kept in data/music)
        import compose
        own = compose.ensure_track(json.load(open(path, encoding="utf-8")))
        if own:
            log(f"{slug} music {own}")
    except Exception as e:  # music is optional: fall back to the rotation
        log(f"{slug} music block skipped: {e}")
    try:  # the ending's holder line comes from the gazette; say so when it cannot (no biblio / full text fetched yet)
        from build import gazette_holder
        if not gazette_holder(json.load(open(path, encoding="utf-8")))[0]:
            log(f"{slug} holder: no gazette data (data/patents/<appno>) - the ending uses branding.json's holder")
    except Exception:
        pass
    out = BUILDERS[TEMPLATE](path)
    postprocess.run(out)  # continuous pen draw-ons + per-video font subsets
    if NARRATE:
        try:
            rep = narration.narrate(out, json.load(open(path, encoding="utf-8")), VOICE, captions=CAPTIONS)
            log(f"{slug} narration " + " | ".join(r.split(":")[0] for r in rep))
        except Exception as e:  # network or TTS failure: skip this video (no silent render), say why
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
    try:
        r = subprocess.run([NPX, "hyperframes@0.8.207", "render", "-q", "delivery", "-o", mp4], cwd=out, env=ENV, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=1800)
    except subprocess.TimeoutExpired:
        log(f"{slug} RENDER FAIL timeout after {time.time() - t:.0f}s")
        return
    ok = r.returncode == 0 and os.path.exists(mp4) and os.path.getmtime(mp4) >= t - 1
    log(f"{slug} {'RENDERED' if ok else 'RENDER FAIL'} {time.time() - t:.0f}s warnings={len(warns)}" + ("" if ok else " " + ((r.stderr or "") + (r.stdout or ""))[-300:]))
    if ok:
        if NARRATE:  # remembers the voice of this render (see rendered_voice)
            shutil.copyfile(os.path.join(out, "narration.txt"), mp4[:-4] + ".narration.txt")
            srt = os.path.join(out, "narration.srt")
            if CAPTIONS and os.path.exists(srt):
                shutil.copyfile(srt, mp4[:-4] + ".srt")
        dst, jpg = export(mp4, slug.split("-", 1)[1])  # deliverable: patents/{출원번호}.mp4 + .jpg (+ .srt)
        log(f"{slug} exported {os.path.relpath(dst, ROOT)} {os.path.relpath(jpg, ROOT)}")


if __name__ == "__main__":
    main()
