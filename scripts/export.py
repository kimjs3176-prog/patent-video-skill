"""Deliverables: copy a rendered video to patents/{출원번호}.mp4, save its thumbnail as patents/{출원번호}.jpg, and copy its
captions (the .srt beside the mp4, when narrated) to patents/{출원번호}.srt.

produce.py calls this after every successful render; the latest render of a patent (any template) is its deliverable.
Usage (for videos rendered earlier): python -I tools/export.py renders_s/116-1020200177685_s_nar.mp4 [...]
"""
import contextlib
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "patents")
THUMB_AT = 3.0  # every template has its title fully on screen by 3 s


def appno_of(mp4):
    m = re.match(r"\d+-(\d{13})", os.path.basename(mp4))
    if not m:
        raise ValueError(f"no 13-digit application number in {mp4}")
    return m.group(1)


def captions_of(mp4):
    """The .srt beside a render when it belongs to that render, else None. produce.py copies it right after the render, so a
    sidecar older than the mp4 is left over from an earlier render (old cues and timings over new audio).
    produce.py's skip test reads the same: a narrated render counts as captioned only when this finds its .srt."""
    srt = mp4[:-4] + ".srt"
    return srt if os.path.exists(srt) and os.path.getmtime(srt) >= os.path.getmtime(mp4) - 1 else None  # 1 s: coarse file times


def export(mp4, appno=None):
    appno = appno or appno_of(mp4)
    os.makedirs(OUT, exist_ok=True)
    dst, jpg = os.path.join(OUT, appno + ".mp4"), os.path.join(OUT, appno + ".jpg")
    try:
        shutil.copyfile(mp4, dst + ".part")
        os.replace(dst + ".part", dst)
    finally:  # copy or replace failed (disk full, the old file open in a player on Windows): leave no .part behind
        with contextlib.suppress(OSError):
            os.remove(dst + ".part")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(THUMB_AT), "-i", dst, "-frames:v", "1", "-q:v", "2", jpg], check=True)
    srt, out_srt = captions_of(mp4), os.path.join(OUT, appno + ".srt")
    if srt:  # captions of the narrated render (YouTube / accessibility upload)
        shutil.copyfile(srt, out_srt)
    elif os.path.exists(out_srt):
        os.remove(out_srt)  # a later render without captions: do not leave a stale file
    return dst, jpg


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(*export(p))
