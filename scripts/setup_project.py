"""Create a patent-video project folder from this skill.

Usage: python -I -X utf8 setup_project.py <project-dir>
Copies the pipeline scripts into <project>/tools, fonts into <project>/assets, render templates into <project>/template,
and the content spec, the figure-analysis guide (FIGURE_ANALYSIS.md) + examples into <project>/tools.

Videos carry no background music. Sound effects are not redistributed with the public skill: they are taken from this
skill's assets/sfx when present, else from the HyperFrames media-use skill (~/.claude/skills/media-use/audio/assets/sfx,
Pixabay Content License) when it is installed. Videos still build without them: the missing clips are simply left out.
Re-running updates tools/*.py; a file that differs from the skill (your edits, or the copy of an older skill version) is
first kept as tools/<name>.py.<YYYYmmdd-HHMMSS>.bak. A backup is never overwritten, so edits survive any number of updates.
branding.json (ending credits: 기술이전 문의처, 특허권자, 면책 문구) is written once with the defaults and never overwritten.
The KIPRIS key is NOT copied: write it to <project>/.env as KIPRIS_API_KEY=... (or set the env var).
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SFX_FALLBACK = os.path.join(os.path.expanduser("~"), ".claude", "skills", "media-use", "audio", "assets", "sfx")
sys.path.insert(0, os.path.join(SKILL, "scripts"))
from hfpin import HF  # noqa: E402  the HyperFrames pin produce.py checks and renders with
NODE_MIN = 22  # the pin's package.json: engines node >=22 (on 18/20 every video fails at its check, after build and narration)


def backup(have):
    """Keep the current tools file before it is replaced; returns the backup's name, or None when an identical backup exists.
    A timestamped name (never an existing one): a fixed .bak lost the user's edits at the second skill update."""
    data = open(have, "rb").read()
    for old in glob.glob(glob.escape(have) + ".*.bak"):
        if open(old, "rb").read() == data:  # already kept by an earlier update: one copy is enough
            return None
    stem, n = f"{have}.{time.strftime('%Y%m%d-%H%M%S')}", 1
    bak = stem + ".bak"
    while os.path.exists(bak):  # two updates within the same second
        n += 1
        bak = f"{stem}-{n}.bak"
    shutil.copy2(have, bak)
    return os.path.basename(bak)


def main(dst):
    os.makedirs(dst, exist_ok=True)
    tools = os.path.join(dst, "tools")
    os.makedirs(tools, exist_ok=True)
    kept = []
    for f in sorted(os.listdir(os.path.join(SKILL, "scripts"))):
        if f.endswith(".py") and f != "setup_project.py":
            src, have = os.path.join(SKILL, "scripts", f), os.path.join(tools, f)
            if os.path.exists(have) and open(have, "rb").read() != open(src, "rb").read():  # e.g. local edits to a builder
                bak = backup(have)
                kept.append(f"{f} -> {bak}" if bak else f"{f} (already kept in an earlier .bak)")
            shutil.copy(src, tools)
    if kept:  # one note: these files were replaced by the skill's version
        print(f"note: {len(kept)} tools file(s) differed from this skill version (your edits, or an older skill's copy) and were "
              "updated; the previous versions are kept in tools/ - merge your edits back from them:\n  " + "\n  ".join(kept))
    for doc in ("CONTENT_SPEC.md", "FIGURE_ANALYSIS.md"):  # read in the project as tools/<doc> (agents and sub-agents)
        shutil.copy(os.path.join(SKILL, "references", doc), tools)
    shutil.copytree(os.path.join(SKILL, "references", "examples"), os.path.join(tools, "examples"), dirs_exist_ok=True)
    for sub in ("fonts", "fonts_serif", "sfx"):
        src = os.path.join(SKILL, "assets", sub)
        if sub == "sfx" and not os.path.isdir(src) and os.path.isdir(SFX_FALLBACK):
            src = SFX_FALLBACK
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(dst, "assets", sub), dirs_exist_ok=True)
        else:
            have = os.path.join(dst, "assets", sub)
            os.makedirs(have, exist_ok=True)
            if any(f.lower().endswith((".mp3", ".wav", ".m4a")) for f in os.listdir(have)):
                continue  # a re-run (skill update) of a project that already has its sfx: nothing to say
            print(f"note: assets/{sub} is empty - install the HyperFrames media-use skill or add whoosh sfx")
    shutil.copytree(os.path.join(SKILL, "assets", "template"), os.path.join(dst, "template"), dirs_exist_ok=True)
    for d in ("data/content", "data/patents", "data/raw", "videos", "renders"):
        os.makedirs(os.path.join(dst, d), exist_ok=True)
    br = os.path.join(dst, "branding.json")
    if not os.path.exists(br):  # ending credits: edit this file to change the contact, holder or disclaimer for every video
        from build import BRANDING_DEFAULTS
        json.dump(BRANDING_DEFAULTS, open(br, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("note: branding.json written - edit it to change 기술이전 문의처 / 특허권자 / 면책 문구")
    gi = os.path.join(dst, ".gitignore")
    if not os.path.exists(gi):
        open(gi, "w", encoding="utf-8").write(".env\nrenders*/\nvideos*/\n.hyperframes/\ndata/raw/\ndata/voice_cache/\ndata/font_cache/\n")
    elif ".env" not in open(gi, encoding="utf-8", errors="replace").read().split():  # an existing .gitignore must still keep the API keys out
        with open(gi, "a", encoding="utf-8") as f:
            f.write("\n.env\n")
        print("note: .env added to the existing .gitignore (API keys)")
    print("project ready:", dst)
    doctor(dst)


def node_major():
    """Major version of the node on PATH, or None when it does not answer."""
    try:
        r = subprocess.run(["node", "--version"], capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    m = re.match(r"v?(\d+)\.", r.stdout.strip())
    return int(m.group(1)) if m else None


def has_key(dst, name):
    """name is set in the environment or the project's .env (as narration.env_key reads it)."""
    if os.environ.get(name, "").strip():
        return True
    env = os.path.join(dst, ".env")
    if os.path.exists(env):
        for line in open(env, encoding="utf-8-sig", errors="replace"):
            if line.strip().startswith(name + "=") and line.split("=", 1)[1].strip().strip("\"'"):
                return True
    return False


def doctor(dst):
    """Report missing prerequisites (nothing is installed automatically). produce.py checks the same at its start."""
    import importlib.util
    missing = [t for t in ("node", "npx", "ffmpeg", "ffprobe") if not shutil.which(t)]
    if "node" not in missing:
        v = node_major()
        if v is None or v < NODE_MIN:
            missing.append(f"Node.js {NODE_MIN}+ for {HF} (found {'a node that does not answer --version' if v is None else f'v{v}'})")
    # numpy: the drawings' pen strokes (figtrace.py); python -I sees no user-site packages
    missing += [f"python package {m}" for m in ("openpyxl", "pypdf", "fontTools", "brotli", "numpy") if importlib.util.find_spec(m) is None]
    if sys.version_info < (3, 10):
        missing.append("Python 3.10+")
    if not shutil.which("uvx") and not has_key(dst, "GOOGLE_TTS_API_KEY"):  # narration is on by default, with edge-tts through uvx
        missing.append("uv (uvx) for the default narration voice (edge-tts) - or GOOGLE_TTS_API_KEY in .env for the Google voice, "
                       "or produce.py --no-narrate")
    if missing:
        print("missing:", ", ".join(missing))
        print("  python -m pip install -r", os.path.join(SKILL, "requirements.txt"),
              f" / Node.js {NODE_MIN}+ (https://nodejs.org) / ffmpeg / uv (https://docs.astral.sh/uv/)")
    print(f"note: the first check downloads {HF} (~120 MB) and its Chrome (~330 MB) once, with no output for minutes; "
          f"to fetch them now: npx --yes {HF} browser ensure")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # the notes are partly Korean; a Windows pipe would get cp949
    if len(sys.argv) != 2:
        sys.exit("usage: python -I -X utf8 setup_project.py <project-dir>")
    main(os.path.abspath(sys.argv[1]))
