"""Background music: one of the tracks in assets/music under each video, quiet enough that the narration stays in front.

The track is picked from the application number (the same patent always gets the same track; across a batch the tracks
are spread about evenly), cut to the video's length, looped if the video is longer, faded in and out, and brought to a
bed level (BED_LUFS, about 12 dB under the voice) with ffmpeg. The result is the project's assets/music/bgm.mp3, mounted
in index.html as one audio clip; produce.py --no-music leaves it out.

Usage: python -I tools/music.py videos/<order>-<appno>/ [...]
"""
import hashlib
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BED_LUFS = -27  # the narration sits near -15 LUFS: the music stays a bed under it
FADE_IN, FADE_OUT = 0.6, 2.5
MARK = "      <!-- audio -->"  # build.AUDIO_MARK (not imported: this file also runs without the builders)


def tracks(root=ROOT):
    d = os.path.join(root, "assets", "music")
    return sorted(f for f in os.listdir(d) if f.lower().endswith(".mp3")) if os.path.isdir(d) else []


def pick(appno, names):
    """The track for a patent: fixed by its application number, spread evenly over a batch."""
    if not names:
        return None
    return names[int(hashlib.sha1(str(appno).encode()).hexdigest(), 16) % len(names)]


def total_of(html):
    m = re.search(r'id="root" data-composition-id="main"[^>]*data-duration="([\d.]+)"', html)
    return float(m.group(1)) if m else None


def mount(out, appno, root=ROOT):
    """Make assets/music/bgm.mp3 for the built project and mount it; returns the track name, or None (no tracks)."""
    name = pick(appno, tracks(root))
    ip = os.path.join(out, "index.html")
    html = open(ip, encoding="utf-8").read()
    html = re.sub(r'\n\s*<audio id="bgm"[^>]*></audio>', "", html)  # built again: one bed only
    total = total_of(html)
    if not name or not total or MARK not in html:
        open(ip, "w", encoding="utf-8").write(html)
        return None
    dst = os.path.join(out, "assets", "music", "bgm.mp3")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    part = f"{dst}.{os.getpid()}.part.mp3"
    af = (f"afade=t=in:d={FADE_IN},afade=t=out:st={max(0.0, total - FADE_OUT):.2f}:d={FADE_OUT},"
          f"loudnorm=I={BED_LUFS}:TP=-3:LRA=11")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-stream_loop", "-1", "-i", os.path.join(root, "assets", "music", name),
                    "-t", f"{total:.2f}", "-af", af, "-ar", "48000", "-ac", "2", "-b:a", "160k", part], check=True)
    os.replace(part, dst)
    tag = (f'      <audio id="bgm" class="clip" src="assets/music/bgm.mp3" data-start="0" data-duration="{total:.2f}" '
           f'data-track-index="10" data-volume="1"></audio>')
    open(ip, "w", encoding="utf-8").write(html.replace(MARK, tag + "\n" + MARK, 1))
    return name


if __name__ == "__main__":
    for d in sys.argv[1:]:
        slug = os.path.basename(os.path.normpath(d))
        print(d, mount(d, slug.split("-", 1)[-1]))
