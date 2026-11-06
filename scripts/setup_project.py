"""Create a patent-video project folder from this skill.

Usage: python -I setup_project.py <project-dir>
Copies the pipeline scripts into <project>/tools, fonts into <project>/assets, render templates into <project>/template,
and the content spec + examples into <project>/tools.

Sound effects and background music are not redistributed with the public skill:
- sfx: taken from this skill's assets/sfx when present, else from the HyperFrames media-use skill
  (~/.claude/skills/media-use/audio/assets/sfx, Pixabay Content License) when it is installed.
- music: produce.py composes beds itself when <project>/assets/music is empty (compose.py, no key); or put your own
  licensed mp3 files there (any names; they rotate in production order).
Videos still build without either — the missing audio clips are simply left out.
Re-running updates tools/*.py; a file that differs from the skill (your edits) is first saved as tools/<name>.py.bak.
branding.json (ending credits: 기술이전 문의처, 특허권자, 면책 문구) is written once with the defaults and never overwritten.
The KIPRIS key is NOT copied: write it to <project>/.env as KIPRIS_API_KEY=... (or set the env var).
"""
import json
import os
import shutil
import sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SFX_FALLBACK = os.path.join(os.path.expanduser("~"), ".claude", "skills", "media-use", "audio", "assets", "sfx")


def main(dst):
    os.makedirs(dst, exist_ok=True)
    tools = os.path.join(dst, "tools")
    os.makedirs(tools, exist_ok=True)
    for f in os.listdir(os.path.join(SKILL, "scripts")):
        if f.endswith(".py") and f != "setup_project.py":
            src, have = os.path.join(SKILL, "scripts", f), os.path.join(tools, f)
            if os.path.exists(have) and open(have, "rb").read() != open(src, "rb").read():  # e.g. local edits to a builder
                shutil.copy2(have, have + ".bak")
                print(f"note: tools/{f} differed from the skill (your edits or an older copy) - updated; previous version kept as tools/{f}.bak")
            shutil.copy(src, tools)
    shutil.copy(os.path.join(SKILL, "references", "CONTENT_SPEC.md"), tools)
    shutil.copytree(os.path.join(SKILL, "references", "examples"), os.path.join(tools, "examples"), dirs_exist_ok=True)
    for sub in ("fonts", "fonts_serif", "sfx", "music"):
        src = os.path.join(SKILL, "assets", sub)
        if sub == "sfx" and not os.path.isdir(src) and os.path.isdir(SFX_FALLBACK):
            src = SFX_FALLBACK
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(dst, "assets", sub), dirs_exist_ok=True)
        else:
            os.makedirs(os.path.join(dst, "assets", sub), exist_ok=True)
            print(f"note: assets/{sub} is empty - " + ("produce.py composes 4 beds on its own (no key); or add licensed mp3s" if sub == "music" else "install the HyperFrames media-use skill or add whoosh sfx"))
    shutil.copytree(os.path.join(SKILL, "assets", "template"), os.path.join(dst, "template"), dirs_exist_ok=True)
    for d in ("data/content", "data/patents", "data/raw", "videos", "renders"):
        os.makedirs(os.path.join(dst, d), exist_ok=True)
    br = os.path.join(dst, "branding.json")
    if not os.path.exists(br):  # ending credits: edit this file to change the contact, holder or disclaimer for every video
        sys.path.insert(0, os.path.join(SKILL, "scripts"))
        from build import BRANDING_DEFAULTS
        json.dump(BRANDING_DEFAULTS, open(br, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("note: branding.json written - edit it to change 기술이전 문의처 / 특허권자 / 면책 문구")
    gi = os.path.join(dst, ".gitignore")
    if not os.path.exists(gi):
        open(gi, "w", encoding="utf-8").write(".env\nrenders*/\nvideos*/\n.hyperframes/\ndata/raw/\ndata/voice_cache/\ndata/font_cache/\n")
    print("project ready:", dst)
    doctor()


def doctor():
    """Report missing prerequisites (nothing is installed automatically)."""
    import importlib.util
    missing = [t for t in ("node", "npx", "ffmpeg", "ffprobe") if not shutil.which(t)]
    missing += [f"python package {m}" for m in ("openpyxl", "pypdf", "fontTools", "brotli", "numpy") if importlib.util.find_spec(m) is None]
    if sys.version_info < (3, 10):
        missing.append("Python 3.10+")
    if missing:
        print("missing:", ", ".join(missing))
        print("  python -m pip install -r", os.path.join(SKILL, "requirements.txt"), " / Node.js 18+ / ffmpeg")
    if not shutil.which("uvx"):
        print("optional: uv (uvx) for narration (--narrate) is not installed")


if __name__ == "__main__":
    main(os.path.abspath(sys.argv[1]))
