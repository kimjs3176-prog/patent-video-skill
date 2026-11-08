"""Build, check and render every content JSON in production order. Resumable.

Usage: python -I -u tools/produce.py [--template A..I|S] [--voice ko-KR-Chirp3-HD-Aoede | ko-KR-SunHiNeural] [--no-narrate] [--no-captions] [--no-render] [--no-music-gen] [order | N-M | N~M ...]
Orders pick contents by their file-name prefix (7 137 146); N-M or N~M is an inclusive range (1-100, 101~205), so two renderers
can split a batch. An unknown argument stops the run instead of being ignored. Needs Node.js 22+ (hyperframes@0.8.207).
Template A writes renders/<order>-<appno>.mp4; template X writes renders_x/... Every video gets a voice-over (suffix _nar)
unless --no-narrate; its narration.txt (voice + lines) is kept beside the mp4, and a different --voice re-renders.
Narrated videos carry burned-in captions (--no-captions to leave them out); the .srt goes beside the mp4 and to patents/,
and turning captions on or off re-renders (the .srt beside the mp4 records which way it was made).
Each successful render is also delivered as patents/{출원번호}.mp4 with a thumbnail patents/{출원번호}.jpg (tools/export.py).
One log line per video in renders*/produce.log; RENDERED lines carry [i/N] and the estimated time left. When assets/music is
empty, background music is made first (tools/music.py):
Google Lyria with GEMINI_API_KEY, otherwise composed by the pipeline itself (no key). A content's `music` block gives that
patent its own composed bed. --no-music-gen skips the automatic beds.
"""
import glob
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# python -I ignores PYTHONIOENCODING: keep progress output (Korean, CLI bars) printable on a cp949 console
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import music  # noqa: E402

FLAGS = {"--narrate", "--no-narrate", "--no-captions", "--no-render", "--no-music-gen"}


def die(msg):
    print("produce:", msg, file=sys.stderr, flush=True)
    sys.exit(2)


def options(argv):
    """Flags and the orders to make. Anything unknown stops the run: a typo ('--templte', '1–100') must not mean 'everything'."""
    o = {"template": "A", "voice": None, "flags": set(), "want": set()}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--template", "--voice"):
            if i + 1 >= len(argv) or argv[i + 1].startswith("-"):
                die(f"{a} needs a value")
            o[a[2:]] = argv[i + 1]
            i += 2
            continue
        m = re.fullmatch(r"(\d+)[-~](\d+)", a)
        if a in FLAGS:
            o["flags"].add(a)
        elif a.isdigit():
            o["want"].add(int(a))
        elif m and int(m.group(1)) <= int(m.group(2)):
            o["want"] |= set(range(int(m.group(1)), int(m.group(2)) + 1))
        else:
            die(f"unknown argument {a!r} (see the usage at the top of tools/produce.py)")
        i += 1
    o["template"] = o["template"].upper()
    if o["template"] not in tuple("ABCDEFGHIS"):  # the keys of BUILDERS
        die(f"--template {o['template']}: one of A-I or S")
    return o


def node_major():
    try:
        r = subprocess.run(["node", "--version"], capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    m = re.match(r"v?(\d+)\.", r.stdout.strip())
    return int(m.group(1)) if m else None


def preflight():
    """Stop before any work when no video could get through; otherwise every one fails on its own, an hour or more later."""
    v = node_major()
    if v is None or not shutil.which(music.NPX):
        die("Node.js (node and npx) not found on PATH - HyperFrames needs Node.js 22 or newer: https://nodejs.org")
    if v < 22:  # hyperframes@0.8.207 declares engines node >=22; on 18/20 every check fails after build and narration
        die(f"Node.js {v} found - {music.HF} needs Node.js 22 or newer: install the current LTS from https://nodejs.org")
    if importlib.util.find_spec("numpy") is None:  # music beds (compose.py) and the drawings' pen strokes (figtrace.py)
        die("python package numpy is missing for this Python (python -I does not see user-site packages): "
            "python -m pip install numpy  (or -r requirements.txt of the skill)")


if __name__ == "__main__":
    OPTS = options(sys.argv[1:])  # before music is made or anything is built
    preflight()
    if "--no-music-gen" not in OPTS["flags"]:
        music.ensure()  # before the builders load: they read the assets/music list when imported
from build import build as build_a  # noqa: E402
import build_b  # noqa: E402
import build_c  # noqa: E402
import build_def  # noqa: E402
import build_ghi  # noqa: E402
import build_sig  # noqa: E402
from validate import check as validate  # noqa: E402
from export import captions_of, export  # noqa: E402
import narration  # noqa: E402
import postprocess  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# --yes: npm otherwise asks before installing the pinned version, and with output captured a person never sees the prompt
HYPERFRAMES = [music.NPX, "--yes", music.HF]
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
        r = subprocess.run(HYPERFRAMES + ["check", "--json"], cwd=out, env=ENV, stdin=subprocess.DEVNULL, capture_output=True, text=True,
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


def order_of(path):
    name = os.path.basename(path)
    head = name.split("-")[0]
    return int(head) if head.isdigit() and "-" in name else None


def target(slug):
    return os.path.join(render_dir(), slug + ("" if TEMPLATE == "A" else "_" + TEMPLATE.lower()) + ("_nar" if NARRATE else "") + ".mp4")


def current(path, mp4):
    """mp4 is an up-to-date render of path: newer than its content (edited content gets re-rendered), with the requested voice
    and captions (the .srt beside a narrated render is there exactly when it was made with captions)."""
    return (os.path.exists(mp4) and os.path.getmtime(mp4) > os.path.getmtime(path)
            and (not NARRATE or (rendered_voice(mp4) == VOICE and bool(captions_of(mp4)) == CAPTIONS)))


def due(path, render, want):
    """one() will build this file (for the [i/N] count)."""
    try:
        order = order_of(path)
        return order is not None and (not want or order in want) and not (render and current(path, target(os.path.basename(path)[:-5])))
    except OSError:  # removed or renamed meanwhile
        return False


def progress(prog):
    """'[i/N ~1h05m left]': this video's place among those due in this run, and the rest at the pace so far."""
    i, n = prog["i"], max(prog["n"], prog["i"])
    s = (time.time() - prog["t0"]) / i * (n - i)
    left = "" if n == i else f" ~{int(s // 3600)}h{int(s % 3600 // 60):02d}m left" if s >= 3600 else f" ~{max(1, round(s / 60))}m left"
    return f"[{i}/{n}{left}]"


def voice_ready():
    """The voice can speak on this machine: say so once, here, instead of 'SKIP narration failed' for every video."""
    global VOICE
    if hasattr(narration, "check_voice"):  # bare names → full voice IDs, unknown voices, a Chirp voice without its key
        try:
            v = narration.check_voice(VOICE)
        except Exception as e:
            die(f"voice {VOICE}: {e}")
        if isinstance(v, str) and v:
            VOICE = v
    google = "Chirp3-HD" in VOICE or "Chirp-HD" in VOICE  # the same routing as narration.synth
    if not google and not shutil.which(getattr(narration, "UVX", "uvx")):
        die(f"narration with {VOICE} runs edge-tts through uv's uvx, which is not installed - install uv "
            "(https://docs.astral.sh/uv/ : 'pip install uv' or 'winget install astral-sh.uv'), "
            "or put GOOGLE_TTS_API_KEY in .env for the Google voice, or run with --no-narrate")


def main():
    global TEMPLATE, NARRATE, VOICE, CAPTIONS
    o = options(sys.argv[1:])
    TEMPLATE, VOICE = o["template"], o["voice"] or VOICE
    NARRATE = "--no-narrate" not in o["flags"]  # --narrate is the default (still accepted)
    CAPTIONS = "--no-captions" not in o["flags"]
    render, want = "--no-render" not in o["flags"], o["want"]
    if NARRATE:
        voice_ready()
    done, prog = set(), {"i": 0, "n": 0, "t0": time.time()}
    while True:  # re-scan after each pass so contents written meanwhile are picked up
        files = [p for p in sorted(glob.glob(os.path.join(ROOT, "data", "content", "*.json")))
                 if (p, os.path.getmtime(p)) not in done]
        if not files:
            break
        prog["n"] += sum(due(p, render, want) for p in files)
        for path in files:
            done.add((path, os.path.getmtime(path)))
            try:
                one(path, render, want, prog)
            except Exception as e:  # one bad content file must not stop the batch
                log(f"{os.path.basename(path)[:-5]} FAIL {type(e).__name__}: {str(e)[:300]}")


def one(path, render, want, prog):
    src_mtime = os.path.getmtime(path)  # before anything reads the content: an edit from here on is checked after the render
    order = order_of(path)
    if order is None:
        log(f"{os.path.basename(path)} SKIP file name is not <order>-<appno>.json")
        return
    if want and order not in want:
        return
    slug = os.path.basename(path)[:-5]
    appno = slug.split("-", 1)[1]
    mp4 = target(slug)
    if render and current(path, mp4):
        # re-deliver when an earlier export failed: patents/ files missing, or the older of them predates this render
        # (os.replace refused by a player holding the file on Windows, or the thumbnail failed after the mp4 was replaced)
        have = [os.path.join(ROOT, "patents", appno + x) for x in (".mp4", ".jpg")]
        if not all(map(os.path.exists, have)) or min(map(os.path.getmtime, have)) < os.path.getmtime(mp4):
            dst, jpg = export(mp4, appno)
            log(f"{slug} exported {os.path.relpath(dst, ROOT)} {os.path.relpath(jpg, ROOT)}")
        return
    prog["i"] += 1
    if TEMPLATE == "S" and "signature" not in json.load(open(path, encoding="utf-8")):
        log(f"{slug} SKIP template S needs a signature block (CONTENT_SPEC: 시그니처 장면)")
        return
    v = validate(path)
    if TEMPLATE != "S":  # sigcheck judges the S film only: for A-I its findings are a note, never a reason to skip
        sig = [e for e in v if e.startswith("signature: ")]
        v = [e for e in v if e not in sig]
        if sig:
            log(f"{slug} note: signature problems (template S only, not blocking {TEMPLATE}): {' / '.join(sig)[:300]}")
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
        except Exception as e:  # network or TTS failure: skip this video (no silent render), say why
            log(f"{slug} SKIP narration failed: {e}")
            return
        nofit = [r for r in rep if "no fit" in r]
        log(f"{slug} narration " + " | ".join(r.split(":")[0] for r in rep if r not in nofit))
        if nofit:  # the video still renders, but these scenes are silent: the line is too long for them even at full speed
            log(f"{slug} NO-FIT {' | '.join(nofit)} - silent scene; shorten its narration line (videos*/{slug}/narration.txt)")
    errs, warns = check_project(out)
    if errs:
        log(f"{slug} SKIP check errors={errs} {warns[:5]}")
        return
    if not render:
        log(f"{slug} built ok warnings={len(warns)} {sorted(set(warns))[:4]}")
        return
    t = time.time()
    try:  # -o relative to the project: npx.cmd goes through cmd.exe, which cuts an unquoted absolute path at '&' (D:\R&D\...)
        r = subprocess.run(HYPERFRAMES + ["render", "-q", "delivery", "-o", os.path.relpath(mp4, out)], cwd=out, env=ENV,
                           stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
    except subprocess.TimeoutExpired:
        log(f"{slug} RENDER FAIL timeout after {time.time() - t:.0f}s")
        return
    ok = r.returncode == 0 and os.path.exists(mp4) and os.path.getmtime(mp4) >= t - 1
    log(f"{slug} {'RENDERED' if ok else 'RENDER FAIL'} {progress(prog)} {time.time() - t:.0f}s warnings={len(warns)}"
        + ("" if ok else " " + ((r.stderr or "") + (r.stdout or ""))[-300:]))
    if not ok:
        return
    if NARRATE:  # remembers the voice of this render (see rendered_voice) and whether it has captions (see current)
        shutil.copyfile(os.path.join(out, "narration.txt"), mp4[:-4] + ".narration.txt")
        srt, side = os.path.join(out, "narration.srt"), mp4[:-4] + ".srt"
        if CAPTIONS and os.path.exists(srt):
            shutil.copyfile(srt, side)
        elif os.path.exists(side):
            os.remove(side)  # a render without captions: the old cues must not be delivered with it (export drops patents/*.srt)
    if os.path.getmtime(path) != src_mtime:  # edited while being built or rendered: this video shows the older content
        os.utime(mp4, (src_mtime, src_mtime))  # not newer than the edit, so this run's re-scan (or the next run) renders it again
        log(f"{slug} content changed during build/render - rendering again")
        return
    dst, jpg = export(mp4, appno)  # deliverable: patents/{출원번호}.mp4 + .jpg (+ .srt)
    log(f"{slug} exported {os.path.relpath(dst, ROOT)} {os.path.relpath(jpg, ROOT)}")


if __name__ == "__main__":
    main()
