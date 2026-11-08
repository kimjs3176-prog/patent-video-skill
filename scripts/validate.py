"""Validate content JSON files against CONTENT_SPEC limits.

Usage: python -I tools/validate.py [--template A..I|S] data/content/*.json
Errors (-) block the video; warnings (~) do not. Without --template every check is an error, signature included (authoring);
with --template A..I the signature block's problems (template S only) are warnings. Exit code 1 when any file has an error.
"""
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from icons import ICONS  # noqa: E402
from build import PALETTES, contact, contact_label, em_width, holder_line  # noqa: E402
import sigcheck  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPNO = re.compile(r"\d{13}")
FIGURE = re.compile(r"fig-p\d+-[A-Za-z0-9_-]+\.(jpg|png)")  # a bare file name in data/patents/<appno>/
TEMPLATES = tuple("ABCDEFGHIS")
# word-break: keep-all never wraps inside a space-free word, so a long compound (바이러스명) runs off the frame, or with
# overflow-wrap: anywhere is cut at whatever syllable meets the edge. The tightest boxes (the 9:16 covers C c1-sub, B b1-sub,
# F f1-t) hold 10 Hangul syllables and cut 11; 9em (10 syllables by em_width) leaves room for its estimate of Latin capitals.
LONG_WORD = 9.0
# where Chromium still wraps under keep-all besides spaces: next to punctuation that touches a Hangul syllable (· - / ( . ~ ...)
# and after a hyphen or dash. Hangul, Latin and digits run together, and 'ㆍ' (a jamo) or '·' '/' between Latin never break.
BREAKS = re.compile(r"\s+|(?<=[가-힣])(?=[^\w\s])|(?<=[^\w\s])(?=[가-힣])|(?<=[-–])")


def appno_ok(appno):
    return bool(APPNO.fullmatch(str(appno or "")))


def figure_ok(fn):
    return isinstance(fn, str) and bool(FIGURE.fullmatch(fn))


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def check(path, template=None, warns=None):
    """Problems in one content JSON (empty list when it is ready to build); never raises on malformed content.
    template: the template being made (A-I, S). None checks everything as for S (content authoring); for A-I the
    signature block's problems become warnings, since only S reads it. warns: a list that collects the non-blocking notes."""
    w = [] if warns is None else warns
    try:
        return _check(path, (template or "S").upper(), w)
    except (KeyError, TypeError, AttributeError, IndexError, ValueError) as e:
        return [f"구조 오류(필드 형식·누락): {type(e).__name__} {e}"]


def _check_music(m, errs, warn):
    """The content's own bed (compose.py) against what compose.spec_of/render actually perform. A value compose would
    ignore or misread (pad 'string', perc 'pulses', seed 'abc', bpm '120', key 'Em') must not quietly swap the
    arrangement, drop the percussion or the whole bed. Keep this in step with compose.py when the engine changes."""
    if not isinstance(m, dict):
        errs.append("music는 객체여야 함")
        return
    try:
        import compose  # numpy; only needed when a content carries its own bed
    except ImportError as e:
        warn.append(f"music 블록을 검사하지 못함({e}): python -m pip install numpy")
        return
    voices = (*compose.VOICE, "none")
    enum = {"mood": tuple(compose.PRESETS), "keys": voices, "arp": voices, "lead": voices,
            "pad": ("pad", "strings", "none"), "perc": ("none", "light", "pulse")}  # pad/perc: the branches of render()
    known = (*enum, "bpm", "key", "progression", "chord_bars", "seed")
    n = len(errs)
    for k, v in m.items():
        if k not in known:  # spec_of keeps it, render never reads it: a typo ('tempo', 'perc ') would just vanish
            errs.append(f"music 알 수 없는 항목: {k} ({', '.join(known)})")
        elif v is None:  # spec_of drops null: the preset's value
            continue
        elif k in enum:
            if not isinstance(v, str) or v not in enum[k]:
                errs.append(f"music.{k} 없음: {v!r} ({', '.join(enum[k])})")
        elif k == "bpm":
            if not _num(v):
                errs.append(f"music.bpm은 숫자: {v!r}")
            elif not 70 <= v <= 160:  # spec_of clamps, so the piece plays at the nearer end
                warn.append(f"music.bpm {v:g}: 70~160 밖이라 {min(160, max(70, v)):g}에 맞춰 연주됨")
        elif k == "key":  # transpose() reads only a root and moves the preset's major progression there
            if not (isinstance(v, str) and re.fullmatch(r"[A-G][#b]?", v)):
                errs.append(f"music.key는 으뜸음만(C · F# · Bb …, 장조로 옮김): {v!r}")
            elif m.get("progression"):
                warn.append(f"music.key {v}: progression이 있으면 쓰이지 않음(key는 프리셋 진행을 옮길 때만)")
        elif k == "progression":
            if not (isinstance(v, list) and v and all(isinstance(x, str) and x.strip() for x in v)):
                errs.append("music.progression은 화음 이름 목록(마디당 하나, 1개 이상)")
        elif k == "chord_bars":  # render: max(1, int(...)), so 0 and 1.5 would play as something else
            if not (_num(v) and v >= 1 and v == int(v)):
                errs.append(f"music.chord_bars는 1 이상의 정수: {v!r}")
        elif k == "seed":  # numpy's default_rng takes a non-negative integer
            if not (_num(v) and v >= 0 and v == int(v)):
                errs.append(f"music.seed는 0 이상의 정수: {v!r}")
    if len(errs) == n:  # types are sound: now the chords themselves, as compose will play them (key applied)
        try:
            [compose.chord(x) for x in compose.spec_of(m)["progression"]]
        except ValueError as e:
            errs.append(f"music: {e}")


def _check(path, template, warn):
    errs = []
    try:
        c = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        return [f"JSON 오류: {e}"]

    def lim(label, text, max_em):
        t = (text or "").replace("|", "").replace("<br />", "")
        if em_width(t) > max_em:
            errs.append(f"{label} 너무 김({em_width(t):.1f}em > {max_em}): {t}")

    def unbroken(label, text):  # a warning: overflow-wrap still keeps it inside the box, but breaks it at any syllable
        for wd in BREAKS.split(re.sub(r"<br\s*/?>", " ", (text or "").replace("|", ""))):
            if em_width(wd) > LONG_WORD:
                warn.append(f"{label} 띄어쓰기 없는 낱말이 김({em_width(wd):.1f}em > {LONG_WORD}): {wd} → "
                            "읽는 자리에서 한 칸 띄우거나('오이녹반모자이크 바이러스') 약어로(CGMMV)")

    for k in ("order", "appno", "regno", "title", "name", "sub", "institute", "palette", "hero", "headline", "chips", "process", "proof", "features", "apps", "source"):
        if k not in c:
            errs.append(f"필드 누락: {k}")
    if errs:
        return errs
    if c["palette"] not in PALETTES:
        errs.append(f"palette 잘못됨: {c['palette']}")
    icons = [c["hero"]] + [a["icon"] for a in c["apps"]] + [i.get("icon") for i in c["proof"].get("items", []) if i.get("icon")]
    for ic in icons:
        if ic not in ICONS:
            errs.append(f"없는 아이콘: {ic}")
    lim("name", c["name"], 8.6)
    lim("sub", c["sub"], 20)
    lim("headline", c["headline"], 26)
    # the big keep-all titles (covers, scene heads); name is nowrap + fit and already under 9em
    for label, text in (("sub", c["sub"]), ("headline", c["headline"]), ("process.title", c["process"].get("title")),
                        ("proof.title", c["proof"].get("title")), ("features.title", c["features"].get("title"))):
        unbroken(label, text)
    if c.get("music") is not None:  # the patent's own composed bed (compose.py)
        _check_music(c["music"], errs, warn)
    # ending credits (branding.json or the content's own "branding"): the 9:16 endings are the narrowest
    lim("contact(기술이전 문의처)", contact(c), 14)
    lim("contact_label", contact_label(c), 8)
    lim("holder(특허권자 줄)", holder_line(c), 34)
    if len(c["chips"]) != 4:
        errs.append("chips는 4개")
    for ch in c["chips"]:
        lim("chip.k", ch["k"], 11)
        lim("chip.v", ch["v"] + ch.get("u", ""), 9.5)
    st = c["process"]["steps"]
    if not 3 <= len(st) <= 6:
        errs.append("process.steps 3~6개")
    lim("process.title", c["process"]["title"], 22)
    lim("process.note", c["process"].get("note", ""), 44)
    for s in st:
        lim("step.n", s["n"], 9)
        lim("step.d", s["d"], 16)
        lim("step.big", s["big"] + s.get("u", ""), 7.5)
    pr = c["proof"]
    if pr.get("kind") == "anatomy":
        fn = pr.get("figure")
        if not fn:  # every builder reads proof.figure for anatomy (a missing key used to pass as the patent folder itself)
            errs.append("proof.figure 필요(anatomy: 부호가 보이는 도면 파일명)")
        elif figure_ok(fn) and appno_ok(c["appno"]) and not os.path.isfile(
                os.path.join(ROOT, "data", "patents", str(c["appno"]), fn)):  # a bad name or appno is reported below
            errs.append(f"figure 파일 없음: {fn}")
        for p in pr.get("parts", []):
            lim("part.n", p["n"], 11)
            lim("part.d", p["d"], 21)
        lim("proof.title", pr.get("title", ""), 22)
    else:
        items = pr.get("items", [])
        if not 1 <= len(items) <= 3:
            errs.append("proof.items 1~3개")
        for it in items:
            lim("item.big", it["big"] + it.get("u", ""), 7)
            lim("item.l", it["l"], 12)
            for line in it.get("s", "").split("<br />"):
                lim("item.s 줄", line, 22)
            for b in it.get("bars") or []:
                lim("bar.l", b["l"], 18)
                if not isinstance(b.get("v"), (int, float)):
                    errs.append(f"bar.v 숫자 아님: {b}")
    lim("source", c["source"], 48)
    f = c["features"]
    lim("features.title", f.get("title", ""), 22)
    lim("big.l", f["big"]["l"], 12)
    lim("big.s", f["big"]["s"], 13)
    if len(f["tiles"]) != 6:
        errs.append("features.tiles는 6개")
    for t in f["tiles"]:
        lim("tile.v", t["v"], 5.6)
        lim("tile.l", t["l"], 8.8)
        lim("tile.s", t["s"], 11.5)
    if len(c["apps"]) != 5:
        errs.append("apps는 5개")
    for a in c["apps"]:
        lim("app.n", a["n"], 8)
        for line in a["s"].split("<br />"):
            lim("app.s 줄", line, 9.5)
    def strings(x, at=""):
        if isinstance(x, str):
            yield at, x
        elif isinstance(x, dict):
            for k, v in x.items():
                yield from strings(v, f"{at}.{k}" if at else k)
        elif isinstance(x, list):
            for i, v in enumerate(x):
                yield from strings(v, f"{at}[{i}]")
    for at, v in strings(c):
        if re.search(r"<(?!br />)[A-Za-z/!?]", v.replace("<br/>", "<br />")):  # tags only; '<4%' is text
            errs.append(f"허용되지 않은 마크업({at}): <br /> 외 태그 금지")
    if not appno_ok(c.get("appno")):
        errs.append("appno는 숫자 13자리")
    sig = c.get("signature") or {}
    for at, fn in [("proof.figure", c["proof"].get("figure")), ("signature.figure", sig.get("figure")),
                   ("signature.run.figure", (sig.get("run") or {}).get("figure")), ("signature.path.figure", (sig.get("path") or {}).get("figure"))]:
        if fn is not None and not figure_ok(fn):
            errs.append(f"{at} 파일명 형식 오류: {fn}")
    for i, part in enumerate(c["proof"].get("parts", [])):  # markers on the drawing: fractions of the figure image
        if ("x" in part) != ("y" in part) or any(not (isinstance(part.get(k), (int, float)) and 0 <= part[k] <= 1) for k in ("x", "y") if k in part):
            errs.append(f"proof.parts[{i}]: x·y는 함께, 도면 비율 0~1")
    # template S: is the technology's own structure there? Only S reads the signature block, so for A-I its problems
    # (a missing second drawing, a typo in the S-only data) are notes to fix before an S run, not a reason to skip.
    # The file-name and markup checks above stay errors for every template: they guard what goes into any page.
    sig = [f"signature: {e}" for e in sigcheck.problems(c)]
    if template == "S":
        errs += sig
    else:
        warn += sig
    nar = c.get("narration") or {}
    budget = {"hook": 30, "overview": 30, "process": 45, "proof": 50, "figures": 25, "features": 30, "apps": 30, "outro": 25}
    for k, v in nar.items():
        if k not in budget:
            errs.append(f"narration 알 수 없는 항목: {k}")
            continue
        n = sum(1 for ch in v if 0xAC00 <= ord(ch) <= 0xD7A3 or ch.isalnum())
        if n > budget[k] * 1.25:
            errs.append(f"narration.{k} 너무 김({n}음절 > {budget[k]})")
    return errs


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Korean messages on a legacy console code page
    args, tpl = sys.argv[1:], None
    if "--template" in args:  # the template about to be made: A-I turn signature problems into warnings
        i = args.index("--template")
        tpl = (args[i + 1:i + 2] or [""])[0].upper()
        args = args[:i] + args[i + 2:]
        if tpl not in TEMPLATES:
            sys.exit(f"validate: --template {tpl or '?'}: one of A-I or S")
    bad = nw = 0
    for p in args:
        w = []
        e = check(p, tpl, w)
        bad, nw = bad + bool(e), nw + len(w)
        if e or w:
            print(os.path.basename(p))
            for x in e:
                print("   -", x)
            for x in w:
                print("   ~ 경고:", x)
    print(f"{len(args) - bad}/{len(args)} OK" + (f" (경고 {nw}건)" if nw else ""))
    sys.exit(1 if bad else 0)  # scripts can rely on the exit code; warnings never fail it
