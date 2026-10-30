"""Deliverables: copy a rendered video to patents/{출원번호}.mp4 and save its thumbnail as patents/{출원번호}.jpg.

produce.py calls this after every successful render; the latest render of a patent (any template) is its deliverable.
Usage (for videos rendered earlier): python -I tools/export.py renders_s/116-1020200177685_s_nar.mp4 [...]
"""
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


def export(mp4, appno=None):
    appno = appno or appno_of(mp4)
    os.makedirs(OUT, exist_ok=True)
    dst, jpg = os.path.join(OUT, appno + ".mp4"), os.path.join(OUT, appno + ".jpg")
    shutil.copyfile(mp4, dst + ".part")
    os.replace(dst + ".part", dst)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(THUMB_AT), "-i", dst, "-frames:v", "1", "-q:v", "2", jpg], check=True)
    return dst, jpg


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(*export(p))
