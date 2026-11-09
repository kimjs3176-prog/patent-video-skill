"""Narration: a spoken script per section, synthesised with edge-tts and laid onto a built project's scene timeline.

Script source: content["narration"] = {"hook", "overview", "process", "proof", "figures", "features", "apps", "outro"}
(1–2 spoken sentences each; see CONTENT_SPEC "narration"). Sections it leaves out get a plain line assembled from the content fields.

Each scene of the built project is matched to a section by its composition file name. Sections a template has no scene for
are merged into the previous scene (figures is dropped instead). The ending (outro) is never voiced: music only.
The voice is picked by default_voice(): Google Chirp 3 HD (ko-KR-Chirp3-HD-Aoede, much closer to a human narrator) when a
GOOGLE_TTS_API_KEY is set (environment or the project's .env), otherwise edge-tts 선희 (ko-KR-SunHiNeural); --voice overrides it
(check_voice(): a bare name maps to its Korean voice, Kore → ko-KR-Chirp3-HD-Kore, SunHi → ko-KR-SunHiNeural,
Hyunsu → ko-KR-HyunsuMultilingualNeural; any "…-Chirp3-HD-<name>" or "…-Chirp-HD-<x>" voice goes to Google, every other name to
edge-tts; an unknown voice stops the run once). Before synthesis each line goes through speak(),
which turns what the screen writes into what a narrator says ("50~90분" → "50에서 90분", "℃" → "도", "가열·가압" → "가열, 가압",
"41.5 cm²" → "41.5 제곱센티미터", "CO₂" → "이산화탄소", "10⁸" → "10의 8제곱"). A line that does not fit its scene is re-voiced faster
(natural pace first, then +6 %, +12 %, up to +18 %) and then shortened by whole sentences, so narration never runs into the next scene.

Captions of the voiced lines are burned in and written as narration.srt (captions.py); --no-captions leaves them out.

Usage: python -I tools/narration.py <project dir> <content.json> [--no-captions] [--voice ko-KR-Chirp3-HD-Aoede | ko-KR-SunHiNeural | Kore]
       python -I tools/narration.py --check data/content/<file>.json [...]   (template S: dry run, flags lines sped past +6 % or cut)
"""
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import ROOT, contact, contact_label  # noqa: E402
from visuals import pick_figures  # noqa: E402
# the titles template S puts on screen when a content leaves them out (l_run, l_path, q_ct/q_tubes/q_gel, q_problem): voiced
# the same, where '' + '.' used to voice a bare '.'
from build_sig import TITLES as SIG_TITLES, problem_title  # noqa: E402

EDGE_VOICE = "ko-KR-SunHiNeural"  # free house voice: 선희 (SunHi)
GOOGLE_VOICE = "ko-KR-Chirp3-HD-Aoede"  # natural narrator voice (female, calm) when a Google key is available
GOOGLE_TTS = "https://texttospeech.googleapis.com/v1/text:synthesize"
SILENT = {"outro"}  # the ending is never voiced (music only)
ORDER = ["hook", "overview", "process", "proof", "figures", "features", "apps", "outro"]
KEYS = {
    "hook": ("teaser", "cover", "hook", "hero", "open", "front"),
    "overview": ("reveal", "summary", "headline", "split", "brief", "name", "title"),
    "process": ("process", "timeline", "flow", "steps", "wave", "how"),
    "proof": ("proof", "results", "chart"),
    "figures": ("figures",),
    "features": ("features", "tiles", "effects", "points", "grid", "cards", "facts"),
    "apps": ("apps", "uses", "outlook", "network", "index"),
    "outro": ("outro", "end", "colophon"),
}
CACHE = os.path.join(ROOT, "data", "voice_cache")
UVX = "uvx.exe" if os.name == "nt" else "uvx"
EDGE_TTS = "edge-tts==7.3.1"  # pinned: the package is fetched from PyPI at run time
SYS_CERTS = "pip-system-certs==5.3"  # edge-tts trusts only certifi's roots; this makes it use the OS store (needs Python 3.10+)
CHIRP3_HD = ("Achernar", "Achird", "Algenib", "Algieba", "Alnilam", "Aoede", "Autonoe", "Callirrhoe", "Charon", "Despina", "Enceladus", "Erinome",
             "Fenrir", "Gacrux", "Iapetus", "Kore", "Laomedeia", "Leda", "Orus", "Puck", "Pulcherrima", "Rasalgethi", "Sadachbia", "Sadaltager",
             "Schedar", "Sulafat", "Umbriel", "Vindemiatrix", "Zephyr", "Zubenelgenubi")  # Google Chirp 3 HD: the same names in every language
EDGE_KO = {"SunHi": "ko-KR-SunHiNeural", "InJoon": "ko-KR-InJoonNeural", "Hyunsu": "ko-KR-HyunsuMultilingualNeural"}  # edge-tts --list-voices, ko-KR


def env_key(name):
    """An API key from the environment or the project's .env (NAME=value)."""
    if os.environ.get(name):
        return os.environ[name].strip()
    env = os.path.join(ROOT, ".env")
    if os.path.exists(env):
        with open(env, encoding="utf-8-sig") as f:  # -sig: Windows Notepad writes a BOM
            for line in f:
                if line.strip().startswith(name + "="):
                    return line.split("=", 1)[1].strip().strip('"\'') or None
    return None


def default_voice():
    return GOOGLE_VOICE if env_key("GOOGLE_TTS_API_KEY") else EDGE_VOICE


def check_voice(voice):
    """Full voice id for --voice, or ValueError for an unknown voice or a Google voice with no GOOGLE_TTS_API_KEY.
    produce.py calls this once at start, so a wrong voice stops the run with one clear message instead of a SKIP per video."""
    v = voice_id(voice)
    if ("Chirp3-HD" in v or "Chirp-HD" in v) and not env_key("GOOGLE_TTS_API_KEY"):
        raise ValueError(f"{v} is a Google voice and needs GOOGLE_TTS_API_KEY (environment or .env); or use --voice {EDGE_VOICE}")
    return v


def voice_id(voice):
    """Full voice id, or ValueError. A bare name maps to its Korean voice (Kore → ko-KR-Chirp3-HD-Kore, SunHi → ko-KR-SunHiNeural):
    sent as is, 'Kore' went to edge-tts and every video of the batch failed on 'Invalid voice'."""
    v = (voice or "").strip()
    known = {**{f"ko-KR-Chirp3-HD-{n}": (n, f"Chirp3-HD-{n}") for n in CHIRP3_HD},  # the …Neural spellings only for edge voices (not KoreNeural)
             **{full: (n, full.split("-", 2)[2], n + "Neural", f"ko-KR-{n}Neural") for n, full in EDGE_KO.items()}}
    for full, alias in known.items():  # any case, with or without the language: kore, Chirp3-HD-Kore, SunHiNeural, ko-KR-HyunsuNeural
        if v.lower() in {x.lower() for x in (full, *alias)}:
            return full
    m = re.fullmatch(r"([a-z]{2,3}-[A-Z]{2,})-(?:Chirp3-HD-(\w+)|(Chirp-HD-\w+)|\w+Neural)", v)
    # by shape: another language (its voice lists are not kept here) and Google's Chirp-HD voices (listing them needs the key);
    # the engine's own error names a wrong one. A ko-KR id outside the lists above is a typo (ko-KR-SunHeeNeural)
    if m and (m.group(3) or m.group(1) != "ko-KR" and (not m.group(2) or m.group(2) in CHIRP3_HD)):
        return v
    raise ValueError(f"unknown voice {voice!r}: use ko-KR-Chirp3-HD-<name> (Google, needs GOOGLE_TTS_API_KEY; <name> is one of {', '.join(CHIRP3_HD)}) "
                     f"or an edge-tts voice ({', '.join(EDGE_KO.values())}); a bare name such as Kore or SunHi also works")


VOICE = default_voice()


# ---------------------------------------------------------------- spoken text
_SUP, _SUB = "⁰¹²³⁴⁵⁶⁷⁸⁹", "₀₁₂₃₄₅₆₇₈₉"
ENDS = ".?!。…"  # a line or sentence that ends in one of these is ended: a trailing ellipsis gets no full stop, and splits like "..."


def _plain(ch):
    """², ₂, ⁸, ①, ８, ⑩ … → the ASCII digits they stand for; any other character unchanged."""
    if ch.isascii() or not ch.isnumeric():
        return ch
    nf = unicodedata.normalize("NFKC", ch)
    if nf.isascii() and nf.isdigit():
        return nf
    d = unicodedata.digit(ch, None)  # Arabic-Indic and other script digits, which NFKC leaves alone
    return ch if d is None else str(d)


# particles written after a symbol are re-picked for the word it is read as: 3 mL을 → 3 밀리리터를, H₂O를 → 물을
_PAIRS = {"을": "을를", "를": "을를", "이": "이가", "가": "이가", "은": "은는", "는": "은는", "과": "과와", "와": "과와", "으로": "으로로", "로": "으로로"}
_PART = r"(으로|을|를|이|가|은|는|과|와|로)(?![가-힣])"
# m², cm³, ㎡ …: 제곱/세제곱 + the length; ahead of the other units, or "cm" would take "cm²" and leave the voice a bare "²"
_LENGTH = {"km": "킬로미터", "cm": "센티미터", "mm": "밀리미터", "dm": "데시미터", "nm": "나노미터", "μm": "마이크로미터", "µm": "마이크로미터",
           "㎚": "나노미터", "㎛": "마이크로미터", "m": "미터"}  # "m" last: "nm²" must not be read n + 제곱미터
_POWER = {"2": "제곱", "3": "세제곱"}
AREA = [(u + p, _POWER[_plain(p)] + k) for u, k in _LENGTH.items() for p in "²³"] + [
    (ch, _POWER[nf[-1]] + _LENGTH[nf[:-1]]) for ch in "㎟㎠㎡㎢㎣㎤㎥㎦" for nf in [unicodedata.normalize("NFKC", ch)]]
# formulas a narrator reads by name; with plain digits too (CO2) only for three or more symbols, since N2 or O2 can label a plot
_CHEM = {"H₂O₂": "과산화수소", "CO₂": "이산화탄소", "H₂O": "물", "CH₄": "메탄", "NH₃": "암모니아", "N₂O": "아산화질소", "NO₂": "이산화질소",
         "SO₂": "이산화황", "O₂": "산소", "N₂": "질소", "H₂": "수소", "O₃": "오존"}
FORMULAS = [(re.sub(f"[{_SUB}]", lambda m: f"[{m.group()}{_plain(m.group())}]", f) if len(f) > 2 else f, k) for f, k in _CHEM.items()]
UNITS = AREA + [("MPa", "메가파스칼"), ("kPa", "킬로파스칼"), ("rpm", "알피엠"), ("mL", "밀리리터"), ("ml", "밀리리터"), ("μL", "마이크로리터"),
         ("µL", "마이크로리터"), ("mg", "밀리그램"), ("kg", "킬로그램"), ("μg", "마이크로그램"), ("µg", "마이크로그램"), ("μm", "마이크로미터"),
         ("µm", "마이크로미터"), ("㎛", "마이크로미터"), ("nm", "나노미터"), ("mm", "밀리미터"), ("cm", "센티미터"), ("bp", "염기쌍"),
         ("kDa", "킬로달톤"), ("kHz", "킬로헤르츠"), ("Hz", "헤르츠"), ("kW", "킬로와트"), ("W", "와트"), ("V", "볼트"), ("min", "분"),
         ("hr", "시간"), ("h", "시간"), ("g", "그램"), ("L", "리터"), ("M", "몰")]


def speak(text):
    """What the screen writes → what a narrator says. Authored lines already written for the ear pass through unchanged."""
    t = re.sub(r"<[^>]+>", " ", text.replace("|", "")).replace("−", "-")
    # ①, ８, ⑩ → 1, 8, 10, so the rules below see a number. Sub- and superscripts stay as written (Fe₂O₃, NH₄⁺, SO₄²⁻, 95%¹):
    # the voice reads them as before and the caption keeps them, where plain digits ran into one number (SO42⁻)
    t = "".join(ch if ch in _SUP + _SUB else _plain(ch) for ch in t)
    for f, k in FORMULAS:  # CO₂ → 이산화탄소, H₂O₂ → 과산화수소 (not inside a longer formula or word)
        # 이산화탄소(CO₂)를: the name once, not twice. Only the bare name: 부산물(H₂O) keeps its aside (부산물, 물)
        t = re.sub(rf"(?<![가-힣]){k}\s*\(\s*{f}\s*\)|(?<![A-Za-z0-9{_SUB}]){f}\s*\(\s*{k}\s*\)", k, t)
        t = re.sub(rf"(?<![A-Za-z0-9{_SUB}]){f}(?![A-Za-z0-9{_SUB}])(?:{_PART})?", lambda m, k=k: _say(k, m.group(1)), t)
    t = re.sub(r"(\d)\s*(?:℃|°C|° C)", r"\1도", t)
    t = re.sub(r"(\d)\s*%", r"\1퍼센트", t)
    t = re.sub(r"(\d)\s*×\s*(\d)", r"\1 곱하기 \2", t)
    t = re.sub(rf"(\d)(⁻?)([{_SUP}]+)(?:{_PART})?", lambda m: _say(  # 10⁸ → 10의 8제곱, 10⁻³ → 10의 마이너스 3제곱
        f'{m.group(1)}의 {"마이너스 " if m.group(2) else ""}{"".join(map(_plain, m.group(3)))}제곱', m.group(4)), t)
    t = re.sub(r"제곱(?=[A-Za-zμµ0-9])", "제곱 ", t)  # 10⁸CFU → 10의 8제곱 CFU
    for u, k in UNITS:  # a unit right after a number (or its exponent: 10⁻³ M → …3제곱 몰), not inside a word
        t = re.sub(rf"(\d|제곱)\s*{re.escape(u)}(?![A-Za-z])", rf"\1 {k}", t)
    for u, k in AREA:  # an area or volume with no number before it: kg/m², 주/㎡
        t = re.sub(rf"(?<![A-Za-zμµ]){re.escape(u)}(?![A-Za-z])", k, t)
    # particles written for the symbol now follow a spoken word: 3 mL을 → 3 밀리리터를
    spoken = "|".join(sorted({k for _, k in UNITS} | {"도", "퍼센트"}, key=len, reverse=True))
    t = re.sub(rf"((?:\d|제곱)\s*(?:{spoken})){_PART}", lambda m: josa(m.group(1), _PAIRS[m.group(2)]), t)
    # any other square or cube after a letter: R² → R 제곱, m/s² → m/s 제곱 (an ion charge such as Ca²⁺ stays as written)
    t = re.sub(rf"([A-Za-z])([²³])(?![{_SUP}⁺⁻])(?:{_PART})?", lambda m: _say(f"{m.group(1)} {_POWER[_plain(m.group(2))]}", m.group(3)), t)
    t = re.sub(r"제곱(?=[A-Za-z0-9])", "제곱 ", t)
    t = re.sub(r"(\d)\s*/\s*(분|시간|일|초)", r"\1 \2당", t)
    t = re.sub(r"(\d(?:\.\d+)?)\s*[~∼〜–—]\s*(-?\d)", r"\1에서 \2", t)  # ranges: 50~90분 → 50에서 90분
    t = re.sub(r"(\d(?:\.\d+)?)\s+-\s*(\d)", r"\1에서 \2", t)
    t = re.sub(r"(?<![\d.])-(\d+(?:\.\d+)?)도", r"영하 \1도", t)  # -40도 → 영하 40도
    t = re.sub(r"(?<![\d.])-(\d+(?:\.\d+)?)에서 (?=영하)", r"영하 \1에서 ", t)
    t = re.sub(r"\s*[·•ㆍ]\s*", ", ", t)  # 가열·가압 → 가열, 가압 (the voice breathes at the comma)
    t = re.sub(r"(\S+)\s+\+\s+", lambda m: josa(m.group(1), "과와") + " ", t)  # 팽화미 + 맥아 → 팽화미와 맥아
    t = re.sub(r"\s*[→⇒]\s*", ", 그다음 ", t)
    t = re.sub(r"[\"“”‘’'「」『』《》〈〉\[\]{}]", "", t)
    t = re.sub(r"\s*\(([^)]*)\)", r", \1,", t)  # asides in brackets become a short pause on each side
    t = re.sub(r",\s*([,.?!])", r"\1", t)
    t = re.sub(r"\s+([,.?!])", r"\1", t)
    # a full stop put after an end mark goes: '흡입한다..' → '흡입한다.', '어렵다?.' → '어렵다?'; an ellipsis ('...') is a pause and stays
    t = re.sub(r"(?<!\.)\.\.(?=\s|$)", ".", t)
    t = re.sub(r"([?!…])\.(?=\s|$)", r"\1", t)
    t = re.sub(r"\s{2,}", " ", t).strip()
    return t if not t or t[-1] in ENDS else t + "."


def _say(word, particle):
    return josa(word, _PAIRS[particle]) if particle else word


def has_words(text):
    """False for a line with nothing to voice ('.', '…', ''): sent to TTS it fails the video or burns a '.' caption."""
    return bool(re.search(r"[^\W_]", text or ""))


_DIGIT_CODA = {"0": True, "1": True, "2": False, "3": True, "4": False, "5": False, "6": True, "7": True, "8": True, "9": False}
_RIEUL = {"1", "7", "8"}


def josa(word, pair):
    """Korean particle after `word` as it is read aloud: pair is "은는", "이가", "을를", "과와" or "으로로"."""
    w = re.sub(r"[\s.,)\]]+$", "", word)
    ch = _plain(w[-1:])[-1:]  # ², ₂, ①, ８ count as the digit they stand for (looked up as they are, they raised KeyError)
    if re.search(r"(?:(?:[kcmdnμµ]?m|[㎚㎛])[²³]|[㎟-㎦])$", w):  # m², cm³, ㎡ are read …미터
        has, rieul = False, False
    elif re.search(rf"(?:\d⁻?[{_SUP}]+|[A-Za-z][²³])$", w):  # 10⁸ is read 10의 8제곱, R² R 제곱
        has, rieul = True, False
    elif "가" <= ch <= "힣":
        coda = (ord(ch) - 0xAC00) % 28
        has, rieul = coda != 0, coda == 8
    elif ch.isdigit():
        has, rieul = _DIGIT_CODA.get(ch, False), ch in _RIEUL
    elif ch.isalpha():
        has, rieul = ch.lower() in "lmnr", ch.lower() == "l"
    else:
        has, rieul = False, False
    if pair == "으로로":
        return word + ("로" if not has or rieul else "으로")
    return word + (pair[0] if has else pair[1:])


# template S: the signature scenes are voiced one by one (scene key → line), the frame scenes keep the section lines
SIG_SCENES = ("route", "journey", "parts", "run", "path", "problem", "primers", "probe", "result", "tubes", "gel", "mix", "effect", "tree", "traits",
              "anatomy")
SIG_FRAME = {"teaser": "hook", "proof": "proof", "features": "features", "apps": "apps", "outro": "outro"}


def scene_key(fname):
    return re.sub(r"^[a-z]+\d*-", "", os.path.basename(fname)[:-5])


def section_of(fname):
    key = scene_key(fname)
    return next((s for s, ks in KEYS.items() if key in ks), None)


def scenes(index_html):
    return [(m.group(1), m.group(2), float(m.group(3)), float(m.group(4))) for m in re.finditer(
        r'<div id="([^"]+)" data-composition-id="[^"]+" data-composition-src="(compositions/[^"]+)" data-start="([\d.]+)" data-duration="([\d.]+)"', index_html)
        if m.group(1) != "tx"]


def _clean(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", (s or "").replace("|", ""))).strip()


def _end(s):
    """s as one sentence: '' stays '' (nothing to voice), and a full stop is added only when s has no end mark (no '?.' or '..')."""
    s = _clean(s)
    return s if not s or s[-1] in ENDS else s + "."


def _seq(i, n):
    """Connective for item i of n, so a listed process is told as a flow."""
    if i == 0:
        return "먼저"
    if i == n - 1:
        return "마지막으로"
    return ("이어서", "다음으로", "그다음")[(i - 1) % 3]


def auto_script(c):
    """Fallback when the content has no authored narration: told as sentences, not read off the slide."""
    steps = c["process"]["steps"]
    pr = c["proof"]
    if pr.get("kind") == "anatomy":
        proof = f'{josa(_clean(pr.get("title", "핵심 구성")), "은는")} {", ".join(p["n"] for p in pr["parts"][:3])} 등으로 이루어집니다.'
    else:
        it = pr["items"][0]
        val = speak(f'{it["big"]}{it.get("u", "")}').rstrip(".")
        # a plain number is 'recorded'; '²'.isdigit() is True too, so the test is for ASCII digits only
        proof = f'그 결과 {josa(_clean(it["l"]), "은는")} {josa(val, "을를") + " 기록했습니다" if re.search(r"[0-9]$", val) else val + "입니다"}.'
    ft = c.get("features") or {}
    feats = [f.get("l") or f.get("t") or f.get("n") for f in (ft.get("tiles") or ft.get("items") or []) if isinstance(f, dict)]
    feats = [_clean(f) for f in feats if f][:2]
    return {
        "hook": f'{_clean(c["headline"])}.',
        "overview": f'{c["institute"]}{"에서" if c.get("institute") else ""} 개발한 {_clean(c["sub"])}입니다.',
        "process": f'공정은 {steps[0]["n"]}에서 시작해, {steps[-1]["n"]}까지 차례로 이어집니다.' if len(steps) > 1
                   else f'핵심 공정은 {steps[0]["n"]}입니다.',
        "proof": proof,
        "figures": "명세서 도면으로 구조를 살펴봅니다.",
        "features": (f'{feats[0]}, 그리고 {josa(feats[1], "이가")} 이 기술의 강점입니다.' if len(feats) > 1
                     else f'{josa(_clean(c["features"].get("title", "핵심 특장점")), "을를")} 정리했습니다.'),
        "apps": f'{", ".join(a["n"] for a in c["apps"][:3])} 같은 분야에 활용할 수 있습니다.',
        "outro": f'{josa(contact_label(c), "은는")} {contact(c)}입니다.',
    }


def auto_sig_script(c):
    """Per-scene lines for template S when the signature block has no authored narration."""
    sg = c["signature"]
    out = {}
    if sg.get("removed"):
        note = _clean(sg.get("removed_note", ""))
        out["route"] = f'기존 공정에서 {note + "하던 " if note else ""}{sg["removed"]} 단계가 빠집니다.'
    if sg.get("stages"):
        st = sg["stages"]
        lines = []
        for i, s_ in enumerate(st):
            lead = _seq(i, len(st))
            if s_.get("t"):
                lo, hi = s_["t"]
                temp = f"{lo}도에서" if lo == hi else f"{lo}에서 {hi}도 사이에서"
                end = ("진행합니다", "이뤄집니다")[len(lines) % 2]  # alternate the verb so the list does not drone
                lines.append(f'{lead} {josa(s_["n"], "은는")} {temp} {end}.')
            else:
                lines.append(f'{lead} {s_["n"]} 단계를 거칩니다.')
        if sg.get("product"):
            lines.append(f'그러면 {josa(sg["product"], "이가")} 완성됩니다.')
        out["journey"] = " ".join(lines)
    if sg.get("callouts"):
        out["parts"] = f'주요 구성은 {", ".join(p["n"] for p in sg["callouts"][:4])}입니다.'
    run = sg.get("run") or {}
    if run:
        rs_ = run.get("steps", [])[:3]
        out["run"] = " ".join(x for x in [_end(run.get("title", SIG_TITLES["run"]))] + [
            _end(f'{_seq(i, len(rs_))} {_clean(q["n"])}' + (f', {_clean(q["d"])}' if q.get("d") else "")) for i, q in enumerate(rs_)] if x)
    if sg.get("path"):
        out["path"] = _end(sg["path"].get("title", SIG_TITLES["path"]))
    if sg.get("problem"):
        out["problem"] = _end(problem_title(c))
    if sg.get("primers"):
        out["primers"] = f'{len(sg["primers"])}개의 프라이머가 {sg.get("target", "표적")}의 {len(sg.get("layout", []))}개 부위를 정확히 찾아 붙습니다.'
    if sg.get("probe"):
        out["probe"] = "여기에 프로브를 더하면, 비특이 신호는 사라지고 표적 신호만 남습니다."
    if sg.get("components"):
        out["mix"] = f'{josa(", ".join(p["n"] for p in sg["components"][:3]), "을를")} 정해진 비율로 배합합니다.'
    if sg.get("effects"):
        out["effect"] = " ".join(f'{josa(e["l"], "은는")} 대조군 {e["control"]}에서 {josa(str(e["treated"]) + e.get("unit", ""), "으로로")} 달라졌습니다.'
                                 for e in sg["effects"][:2])
    if sg.get("steps") and sg.get("type") == "lineage":
        out["tree"] = f'{josa(sg.get("variety", "신품종"), "은는")} {sg["steps"][0]["l"]}에서 출발해, {sg["steps"][-1]["l"]}까지 거쳐 선발했습니다.'
    if sg.get("type") == "claim":
        cl = sg["claim"]
        feat = ", ".join(cl["elements"][i]["n"] for i in cl["feature"]["idx"])
        out["anatomy"] = (f'청구항 {cl["no"]}의 {josa(cl["preamble"], "은는")} {josa(", ".join(e["n"] for e in cl["elements"][:4]), "으로로")} 이루어집니다. '
                          f'그중 핵심은 {feat}입니다.')
        out["tree"] = f'여기서 {", ".join(d["l"] for d in sg["deps"][:3])} 등으로 권리가 이어집니다.'
        ev = sg.get("evidence")
        if ev:
            out["tree"] += f' 실제로 {josa(ev["l"], "은는")} {ev["control"]}에서 {josa(str(ev["treated"]) + ev.get("u", ""), "으로로")} 달라졌습니다.'
    if sg.get("traits"):
        out["traits"] = " ".join(f'{josa(t["l"], "은는")} {t["new"]}{t.get("unit", "")}입니다.' for t in sg["traits"][:2])
    rs = sg.get("result") or {}
    if rs:
        out[{"ct": "result", "tubes": "tubes", "gel": "gel"}[rs["kind"]]] = " ".join(
            x for x in (_end(rs.get("title", SIG_TITLES[rs["kind"]])), _end(rs.get("note", ""))) if x)
    return out


def sig_script(c):
    """Scene key → line for template S: signature.narration first, then the content's section lines, then generated.
    A line of punctuation only ('.', '…') counts as not written. An empty signature.narration line ("run": "" or null) keeps that
    scene silent, as it always did; one still empty after the fallbacks leaves its scene unvoiced too."""
    base = auto_script(c)
    sec = {k: v for k, v in (c.get("narration") or {}).items() if has_words(v)}
    out = {k: sec.get(v) or base[v] for k, v in SIG_FRAME.items()}
    out.update(auto_sig_script(c))
    out.update({k: v for k, v in (c["signature"].get("narration") or {}).items() if not v or has_words(v)})
    return {k: v for k, v in out.items() if k not in SILENT and v and has_words(speak(v))}


def duration(path):
    # a busy machine can fail to start ffprobe at all (no output, no message); wait and try again before giving up
    for wait in (0, 2, 5, 15):
        time.sleep(wait)
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True)
        try:
            return float(r.stdout.strip())
        except ValueError:  # a 0 s clip would "fit" every scene and overlap the next line
            pass
    raise RuntimeError(f"ffprobe could not read {os.path.basename(path)} (exit {r.returncode}): {r.stderr.strip()[-200:]}")


def _google(text, voice, rate, dst):
    key = env_key("GOOGLE_TTS_API_KEY")
    if not key:
        raise RuntimeError(f"{voice} needs GOOGLE_TTS_API_KEY (environment or .env); or pass --voice {EDGE_VOICE}")
    body = {"input": {"text": text}, "voice": {"languageCode": "-".join(voice.split("-")[:2]), "name": voice},
            "audioConfig": {"audioEncoding": "MP3", "speakingRate": round(1 + int(rate.strip("%+")) / 100, 2), "sampleRateHertz": 24000}}
    req = urllib.request.Request(GOOGLE_TTS, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json; charset=utf-8", "X-Goog-Api-Key": key})
    for wait in (0, 2, 5, 15):  # quota bursts (429) and brief outages: back off, then give up loudly
        time.sleep(wait)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                audio = json.load(r)["audioContent"]
            break
        except urllib.error.HTTPError as e:
            err = f"Google TTS {e.code}: {e.read()[:300].decode('utf-8', 'replace')}"
            if e.code not in (429, 500, 502, 503, 504):
                raise RuntimeError(err) from None
        except OSError as e:
            err = f"Google TTS: {e}"
    else:
        raise RuntimeError(err)
    with open(dst, "wb") as f:
        f.write(base64.b64decode(audio))


def _edge(text, voice, rate, dst):
    # uv (PyPI fetch) and edge-tts (aiohttp, certifi only) each trust just their own bundled roots, so behind a TLS-inspecting proxy
    # (agency and company networks) every call failed. Both now use the OS store, which also holds a root CA pushed by the
    # organisation: pip-system-certs for edge-tts, native TLS for uv. uv's native TLS goes in by environment, not as --native-tls:
    # uv 0.11 already warns that flag will be removed, and an unknown flag would fail every call, while an unknown variable is ignored
    # (UV_NATIVE_TLS for older uv, UV_SYSTEM_CERTS for newer). A setting the user made is left as it is.
    env = dict(os.environ, PYTHONIOENCODING="utf-8")  # Windows: the error text would otherwise come back in cp949
    if "UV_NATIVE_TLS" not in env and "UV_SYSTEM_CERTS" not in env:
        env.update(UV_NATIVE_TLS="1", UV_SYSTEM_CERTS="1")
    cmd = [UVX, "--python", ">=3.10", "--from", EDGE_TTS, "--with", SYS_CERTS,  # pip-system-certs needs 3.10+: never resolve on an older Python
           "edge-tts", "--voice", voice, f"--rate={rate}", f"--text={text}", "--write-media", dst]
    # the free service now and then sends no audio for a valid line, in bursts (Hyunsu often, 2026-11: a later try works).
    # It answers a voice that does not exist the same way, so only the Korean voices known to exist get the retries
    # (0 + 2 + 5 + 15 s); another language's voice, which check_voice passes by its shape alone, fails at once.
    known = voice in EDGE_KO.values()
    for tries, wait in enumerate((0, 2, 5, 15) if known else (0,), 1):  # the same back-off as _google and duration
        time.sleep(wait)
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=300, env=env)
            return
        except subprocess.CalledProcessError as e:  # its str() is the whole command and 'exit status 1': the cause is the last stderr line
            err = [s.strip() for s in (e.stderr or b"").decode("utf-8", "replace").splitlines() if s.strip()]
            last = [s for s in err if not s.startswith(("warning:", "hint:"))][-1:] or err[-1:] or ["no error output"]  # uv's notes come around it
            # anything else (a certificate error, a bad option) is final
            if "NoAudioReceived" not in last[0] or not known or tries == 4:
                hint = "" if known or "NoAudioReceived" not in last[0] else " - is the voice right? (edge-tts --list-voices)"
                raise RuntimeError(f"edge-tts failed (exit {e.returncode}, voice {voice}): {last[0]}"[:300] + hint) from None
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"edge-tts timed out after 300 s (voice {voice})") from None


def synth(text, voice, rate):
    os.makedirs(CACHE, exist_ok=True)
    h = hashlib.sha1(f"{voice}|{rate}|{text}".encode("utf-8")).hexdigest()[:16]
    mp3 = os.path.join(CACHE, h + ".mp3")
    if not os.path.exists(mp3):
        tmp = f"{mp3}.{os.getpid()}.part.mp3"  # per process: two renderers may synthesize the same line at once
        try:
            if "Chirp3-HD" in voice or "Chirp-HD" in voice:
                _google(text, voice, rate, tmp)
            else:
                _edge(text, voice, rate, tmp)
            os.replace(tmp, mp3)
        finally:  # a failed call leaves a 0-byte or partial clip behind
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except OSError:  # Windows: still held open; never hide the real error behind this one
                    pass
    return mp3, duration(mp3)


def sentences(text):
    return [s for s in re.split(rf"(?<=[{ENDS}])\s+", text.strip()) if has_words(s)]


def fit(text, avail, voice):
    """Voice text so it lasts at most avail seconds: faster first, then drop trailing sentences."""
    parts = sentences(speak(text))
    while parts:
        t = " ".join(parts)
        for rate in ("+0%", "+6%", "+12%", "+18%"):  # natural pace first; speed up only as much as the scene needs
            mp3, dur = synth(t, voice, rate)
            if dur <= avail:
                return t, mp3, dur, rate
        parts = parts[:-1]
    return None


def assign(slots, script):
    have = {section_of(f) for _, f, _, _ in slots}
    texts = {}
    for sec in ORDER:
        line = (script.get(sec) or "").strip()
        if not has_words(speak(line)):
            continue
        if line[-1] not in ENDS:  # lines are joined below: unended, hook and overview ran into one sentence fit() could only drop whole
            line = line.rstrip(" ,;:") + "."
        if sec in have:
            texts[sec] = (texts.get(sec, "") + " " + line).strip()
            continue
        if sec == "figures":
            continue
        prev = next((p for p in reversed(ORDER[:ORDER.index(sec)]) if p in have), None)
        nxt = next((p for p in ORDER[ORDER.index(sec) + 1:] if p in have), None)
        tgt = prev or nxt
        if tgt:
            texts[tgt] = (texts.get(tgt, "") + " " + line).strip()
    return texts


def narrate(out, c, voice=VOICE, lead=0.45, tail=0.55, bgm_volume=0.22, captions=True):
    # a bare name (Kore) is voiced and recorded in narration.txt under its full id. The Google key is checked per clip, not here,
    # so lines already in the voice cache still work without it (produce.py checks it once with check_voice)
    voice = voice_id(voice)
    ip = os.path.join(out, "index.html")
    html = open(ip, encoding="utf-8").read()
    html = re.sub(r'\s*<audio id="nar-[^>]*></audio>', "", html)
    slots = scenes(html)
    if c.get("signature") and any(scene_key(f) in SIG_SCENES for _, f, _, _ in slots):
        texts, keyof = sig_script(c), scene_key
    else:
        authored = {k: v for k, v in (c.get("narration") or {}).items() if has_words(v)}  # '' or '.' falls back like a missing line
        script = {k: v for k, v in {**auto_script(c), **authored}.items() if k not in SILENT}  # unwritten sections fall back
        if not pick_figures(c):  # the figures scene falls back to step pictograms: no line about drawings
            script.pop("figures", None)
        texts, keyof = assign(slots, script), section_of
    vdir = os.path.join(out, "assets", "voice")
    os.makedirs(vdir, exist_ok=True)
    clips, report, voiced = [], [], []
    for i, (sid, f, st, du) in enumerate(slots):
        sec = keyof(f)
        if sec not in texts:
            continue
        nxt = slots[i + 1][2] if i + 1 < len(slots) else st + du
        start = st + (0.6 if st == 0 else lead)
        avail = max(1.0, nxt + 0.25 - start - tail)  # may run into the cross-fade, never past it
        got = fit(texts[sec], avail, voice)
        if not got:
            report.append(f"{sid}: no fit ({avail:.1f}s)")
            continue
        t, mp3, dur, rate = got
        name = f"{sid}.mp3"
        with open(mp3, "rb") as a, open(os.path.join(vdir, name), "wb") as b:
            b.write(a.read())
        clips.append(f'      <audio id="nar-{sid}" class="clip" src="assets/voice/{name}" data-start="{start:.2f}" data-duration="{dur:.2f}" '
                     f'data-track-index="{20 + len(clips) % 2}" data-volume="1"></audio>')
        voiced.append((start, dur, t))
        report.append(f"{sid} [{sec}] {start:.1f}s +{dur:.1f}s/{avail:.1f}s rate {rate}{'' if t == speak(texts[sec]) else ' (shortened)'}: {t}")
    html = re.sub(r'(<audio id="bgm"[^>]*data-volume=")[\d.]+(")', rf"\g<1>{bgm_volume}\2", html)
    block = "\n".join(clips)
    if '      <audio id="bgm"' in html:
        html = html.replace('      <audio id="bgm"', block + '\n      <audio id="bgm"', 1)
    elif clips:  # no music (postprocess dropped the bgm tag): close the voice clips into the main composition instead
        html, k = re.subn(r'(\n\s*</div>\s*\n\s*<script>)', lambda m: "\n" + block + m.group(1), html, count=1)
        if not k:
            raise RuntimeError("index.html: no place to mount the narration clips")
    open(ip, "w", encoding="utf-8").write(html)
    open(os.path.join(out, "narration.txt"), "w", encoding="utf-8").write("\n".join([f"voice: {voice}"] + report) + "\n")
    if captions:  # burned-in captions of exactly what was voiced, and narration.srt
        import captions as cap
        report.append(f"captions: {cap.mount(out, voiced)} cues")
    return report


def check(paths, voice=VOICE, lead=0.45, tail=0.55):
    """Dry run for template S contents (no build needed): voice each scene line and report the ones that would be sped up
    past +6 % or cut. Fills the voice cache, so the later render reuses the clips. Returns the number of cut lines."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import build_sig
    voice = voice_id(voice)
    cut = 0
    for p in paths:
        c = json.load(open(p, encoding="utf-8"))
        if not c.get("signature"):
            print(os.path.basename(p), "- no signature (S only)")
            continue
        slots, _ = build_sig.slots_for(c)
        texts = sig_script(c)
        for i, (sid, f, st, du) in enumerate(slots):
            key = scene_key(f + ".html")  # slots name the composition without its extension
            if key not in texts:
                continue
            nxt = slots[i + 1][2] if i + 1 < len(slots) else st + du
            start = st + (0.6 if st == 0 else lead)
            avail = max(1.0, nxt + 0.25 - start - tail)
            got = fit(texts[key], avail, voice)
            if not got:
                print(f"{os.path.basename(p)[:3]} {key:9s} NO FIT in {avail:.1f}s")
                cut += 1
                continue
            t, _, dur, rate = got
            shortened = t != speak(texts[key])
            cut += shortened
            flag = "  <-- cut: shorten the line" if shortened else ("  <-- sped up " + rate if rate not in ("+0%", "+6%") else "")
            print(f"{os.path.basename(p)[:3]} {key:9s} {dur:4.1f}/{avail:4.1f}s {rate}{flag}")
    return cut


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    try:
        v = check_voice(a[a.index("--voice") + 1] if "--voice" in a else VOICE)
    except ValueError as e:
        sys.exit(f"narration: {e}")
    if a and a[0] == "--check":  # python -I tools/narration.py --check data/content/<file>.json [...]
        sys.exit(1 if check([x for x in a[1:] if x.endswith(".json")], v) else 0)
    for line in narrate(a[0], json.load(open(a[1], encoding="utf-8")), v, captions="--no-captions" not in a):
        print(line)
