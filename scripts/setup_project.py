"""Create a patent-video project folder from this skill.

Usage: python -I setup_project.py <project-dir>
Copies the pipeline scripts into <project>/tools, fonts into <project>/assets, render templates into <project>/template,
and the content spec + examples into <project>/tools.

Sound effects and background music are not redistributed with the public skill:
- sfx: taken from this skill's assets/sfx when present, else from the HyperFrames media-use skill
  (~/.claude/skills/media-use/audio/assets/sfx, Pixabay Content License) when it is installed.
- music: put your own licensed mp3 files in <project>/assets/music (any names; they rotate in production order).
Videos still build without either — the missing audio clips are simply left out.
The KIPRIS key is NOT copied: write it to <project>/.env as KIPRIS_API_KEY=... (or set the env var).
"""
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
            shutil.copy(os.path.join(SKILL, "scripts", f), tools)
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
            print(f"note: assets/{sub} is empty - " + ("add your licensed background music (mp3)" if sub == "music" else "install the HyperFrames media-use skill or add whoosh sfx"))
    shutil.copytree(os.path.join(SKILL, "assets", "template"), os.path.join(dst, "template"), dirs_exist_ok=True)
    for d in ("data/content", "data/patents", "data/raw", "videos", "renders"):
        os.makedirs(os.path.join(dst, d), exist_ok=True)
    gi = os.path.join(dst, ".gitignore")
    if not os.path.exists(gi):
        open(gi, "w", encoding="utf-8").write(".env\nrenders*/\nvideos*/\n.hyperframes/\ndata/raw/\ndata/voice_cache/\ndata/font_cache/\n")
    print("project ready:", dst)


if __name__ == "__main__":
    main(os.path.abspath(sys.argv[1]))
