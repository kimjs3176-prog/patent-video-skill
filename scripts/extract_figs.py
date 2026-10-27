"""Extract 1-bit patent drawings (CCITT fax / Flate bilevel) from data/raw/<appno>.pdf as PNG.

The PDF fetcher only kept JPEG figures; most mechanical drawings are CCITT G4 or 1-bit Flate.
This wraps them in TIFF / PBM containers and lets ffmpeg decode them, so no extra Python packages.
Usage: python -I tools/extract_figs.py <appno> [...]   (or --all)
"""
import json
import os
import re
import struct
import subprocess
import sys
import zlib

import pypdf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def tiff_ccitt(data, w, h, k, black_is_1):
    comp = 4 if k < 0 else 3
    photometric = 0 if black_is_1 else 1  # TIFF 0 = WhiteIsZero
    entries = [(256, 4, 1, w), (257, 4, 1, h), (258, 3, 1, 1), (259, 3, 1, comp), (262, 3, 1, photometric),
               (273, 4, 1, 0), (277, 3, 1, 1), (278, 4, 1, h), (279, 4, 1, len(data))]
    if comp == 3:
        entries.append((292, 4, 1, 0))
    entries.sort()
    ifd_off = 8
    data_off = ifd_off + 2 + 12 * len(entries) + 4
    out = bytearray(b"II*\x00" + struct.pack("<I", ifd_off) + struct.pack("<H", len(entries)))
    for tag, typ, cnt, val in entries:
        if tag == 273:
            val = data_off
        out += struct.pack("<HHI", tag, typ, cnt) + (struct.pack("<HH", val, 0) if typ == 3 else struct.pack("<I", val))
    out += struct.pack("<I", 0) + data
    return bytes(out)


def pbm(raw, w, h, invert):
    row = (w + 7) // 8
    body = raw[: row * h]
    if invert:
        body = bytes(255 - b for b in body)
    return f"P4\n{w} {h}\n".encode() + body


def extract(appno):
    pdf = os.path.join(ROOT, "data", "raw", appno + ".pdf")
    outdir = os.path.join(ROOT, "data", "patents", appno)
    if not os.path.exists(pdf):
        return []
    made = []
    reader = pypdf.PdfReader(pdf)
    for i, page in enumerate(reader.pages):
        xo = page["/Resources"].get("/XObject")
        if not xo:
            continue
        for name, ref in xo.get_object().items():
            v = ref.get_object()
            w, h = int(v.get("/Width", 0)), int(v.get("/Height", 0))
            if w < 300 or int(v.get("/BitsPerComponent", 8)) != 1:
                continue
            filt = v.get("/Filter")
            filt = filt[0] if isinstance(filt, list) else filt
            decode = [float(x) for x in v.get("/Decode", [0, 1])]
            inverted = decode[0] == 1
            png = os.path.join(outdir, f"fig-p{i + 1}-{re.sub(r'[^A-Za-z0-9_-]', '_', name[1:])}.png")
            tmp = png[:-4] + (".tif" if filt == "/CCITTFaxDecode" else ".pbm")
            try:
                if filt == "/CCITTFaxDecode":
                    p = v.get("/DecodeParms") or {}
                    p = p[0] if isinstance(p, list) else p
                    k = int(p.get("/K", 0))
                    black1 = bool(p.get("/BlackIs1", False)) != inverted
                    open(tmp, "wb").write(tiff_ccitt(v._data, int(p.get("/Columns", w)), int(p.get("/Rows", h)), k, black1))
                elif filt == "/FlateDecode":
                    raw = zlib.decompress(v._data)
                    # PDF 1-bit gray: 0 = black; PBM: 1 = black
                    open(tmp, "wb").write(pbm(raw, w, h, invert=not inverted))
                else:
                    continue
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-vf", "format=gray", png], check=True)
                made.append(os.path.basename(png))
            except Exception as e:
                print(appno, name, "failed:", e)
            finally:
                if os.path.exists(tmp):
                    os.remove(tmp)
    return made


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--all"]:
        args = [m["appno"] for m in json.load(open(os.path.join(ROOT, "data", "master.json"), encoding="utf-8"))]
    for a in args:
        figs = extract(a)
        if figs:
            print(a, len(figs), "drawings")
