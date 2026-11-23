"""Pronunciation check: listen to each narration clip with a local speech recogniser and compare it with the line it was
meant to say. A clip that reads a number differently (50배 heard as 5배) or sounds unlike its line is reported, so a person
listens to that one scene instead of the whole batch. Nothing is changed and nothing blocks the render.

Recogniser: faster-whisper (MIT) with the Whisper "small" model (MIT, about 480 MB, downloaded once to the Hugging Face
cache on first use), on the CPU. About 15 s to load and 2 s per clip. Without the package the check is skipped with a note.

Usage: python -I tools/pronounce.py videos/<slug>/ [...]   (reads narration.txt and assets/voice/*.mp3 of each project)
"""
import difflib
import os
import re
import subprocess
import sys

MODEL = "small"  # base misheard about one word per line in Korean (50배 → 신배); small heard the test lines all but exactly
MIN_RATIO = 0.7  # similarity below which a line is reported: the recogniser itself mishears names (쌀맥주 → 삶액죽) above it
_model = None


def available():
    import importlib.util
    return importlib.util.find_spec("faster_whisper") is not None  # optional: without it the check is skipped


def _pcm(path):
    """16 kHz mono samples via ffmpeg (already required). faster-whisper's own decoder needs a matching PyAV release."""
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def _letters(s):
    s = s.replace("%", "퍼센트").replace("℃", "도").replace("°C", "도")
    return re.sub(r"[^0-9A-Za-z가-힣]", "", s)


_NATIVE = {"한": 1, "하나": 1, "두": 2, "둘": 2, "세": 3, "셋": 3, "네": 4, "넷": 4, "다섯": 5, "여섯": 6, "일곱": 7, "여덟": 8,
           "아홉": 9, "열": 10}
_COUNTER = r"(?=\s*(?:단계|가지|개|번|배|명|마리|곳|종|시간|살|차례))"
_DIG = dict(zip("일이삼사오육칠팔구", range(1, 10)))


def _sino_value(w):
    """오십 → 50, 백이십 → 120, 만이천 → 12000."""
    total, part, d = 0, 0, 0
    for ch in w:
        if ch in _DIG:
            d = _DIG[ch]
        elif ch in "십백천":
            part += (d or 1) * {"십": 10, "백": 100, "천": 1000}[ch]
            d = 0
        elif ch == "만":
            total += (part + d or 1) * 10000
            part, d = 0, 0
    return total + part + d


def _numbers(s):
    """The figures a line says, written in digits whichever way they were said (다섯 단계, 오십 배, 50배 → 5, 50, 50)."""
    s = re.sub(r"(?<![가-힣])(" + "|".join(sorted(_NATIVE, key=len, reverse=True)) + r")" + _COUNTER,
               lambda m: str(_NATIVE[m.group(1)]), s)
    s = re.sub(r"(?<![가-힣])([일이삼사오육칠팔구십백천만]{2,})" + _COUNTER, lambda m: str(_sino_value(m.group(1))), s)
    return re.findall(r"\d+(?:\.\d+)?", s.replace(",", ""))


def lines_of(out):
    """{scene id: voiced text} from a project's narration.txt."""
    p = os.path.join(out, "narration.txt")
    got = {}
    if os.path.exists(p):
        for ln in open(p, encoding="utf-8"):
            m = re.match(r"(\S+) \[[^\]]+\] .*?: (.*)$", ln.strip())
            if m:
                got[m.group(1)] = m.group(2)
    return got


def check(out):
    """[(scene id, meant, heard, reason)] for the clips that do not sound like their line; writes pronounce.txt."""
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel(MODEL, device="cpu", compute_type="int8")
    found, report = [], []
    for sid, meant in lines_of(out).items():
        mp3 = os.path.join(out, "assets", "voice", sid + ".mp3")
        if not os.path.exists(mp3):
            continue
        segs, _ = _model.transcribe(_pcm(mp3), language="ko", beam_size=5)
        heard = " ".join(s.text.strip() for s in segs).strip()
        ratio = difflib.SequenceMatcher(None, _letters(meant), _letters(heard)).ratio()
        why = []
        if _numbers(meant) != _numbers(heard):
            why.append(f"numbers {_numbers(meant)} heard {_numbers(heard)}")
        if ratio < MIN_RATIO:
            why.append(f"similarity {ratio:.2f}")
        report.append(f"{sid} {ratio:.2f}{' CHECK ' + '; '.join(why) if why else ''}\n  meant {meant}\n  heard {heard}")
        if why:
            found.append((sid, meant, heard, "; ".join(why)))
    open(os.path.join(out, "pronounce.txt"), "w", encoding="utf-8").write("\n".join(report) + "\n")
    return found


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if not available():
        sys.exit("faster-whisper is not installed: python -m pip install faster-whisper==1.2.1")
    bad = 0
    for d in sys.argv[1:]:
        for sid, meant, heard, why in check(d):
            bad += 1
            print(f"{os.path.basename(os.path.normpath(d))} {sid}: {why}\n  meant {meant}\n  heard {heard}")
    print(f"{bad} clip(s) to listen to" if bad else "all clips sound like their lines")
