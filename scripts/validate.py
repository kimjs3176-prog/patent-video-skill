"""Validate content JSON files against CONTENT_SPEC limits. Usage: python -I tools/validate.py data/content/*.json"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from icons import ICONS  # noqa: E402
from build import PALETTES, em_width  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def check(path):
    errs = []
    try:
        c = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        return [f"JSON 오류: {e}"]

    def lim(label, text, max_em):
        t = (text or "").replace("|", "").replace("<br />", "")
        if em_width(t) > max_em:
            errs.append(f"{label} 너무 김({em_width(t):.1f}em > {max_em}): {t}")

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
        if not os.path.exists(os.path.join(ROOT, "data", "patents", c["appno"], pr.get("figure", ""))):
            errs.append(f"figure 파일 없음: {pr.get('figure')}")
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
    if not re.fullmatch(r"\d{13}", str(c.get("appno", ""))):
        errs.append("appno는 숫자 13자리")
    sig = c.get("signature") or {}
    for at, fn in [("proof.figure", c["proof"].get("figure")), ("signature.figure", sig.get("figure")), ("signature.path_figure", sig.get("path_figure"))]:
        if fn is not None and not re.fullmatch(r"fig-p\d+-[A-Za-z0-9_-]+\.(jpg|png)", fn):
            errs.append(f"{at} 파일명 형식 오류: {fn}")
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
    bad = 0
    for p in sys.argv[1:]:
        e = check(p)
        if e:
            bad += 1
            print(os.path.basename(p))
            for x in e:
                print("   -", x)
    print(f"{len(sys.argv) - 1 - bad}/{len(sys.argv) - 1} OK")
