"""Help place parts on any patent's drawing: reference signs from the specification + a measuring grid over the figure.

For each content JSON (anatomy proof, or a loop / claim signature) this
  - reads "부호의 설명" from data/patents/<appno>/fulltext.txt into a sign → name table,
  - matches each listed part to its sign (by `ref`, or by name when `ref` is missing — printed as a suggestion),
  - writes data/fig_map/<appno>/<figure>_grid.png: the drawing with a 10 × 10 grid (bold every 5), so a model reading it
    can measure x/y as fractions (cell = 0.1) — see references/FIGURE_ANALYSIS.md,
  - and lists which parts still need x/y.
Nothing in the content file is changed; coordinates are written after looking at the grid image.

Usage: python -I tools/figmap.py data/content/<order>-<appno>.json [...]
       python -I tools/figmap.py data/content/<file>.json --figure fig-p11-IM42.jpg   (a figure not yet in the content)
With no anatomy proof and no loop signature yet, it grids every drawing of the patent so one can be chosen and measured.
A figure that is missing or cannot be read is reported and skipped (the other jobs and files still run); the exit
code is then 1.
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate import appno_ok, figure_ok  # noqa: E402  same file-name rules as the content check

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGN = re.compile(r"(?<![0-9A-Za-z])([0-9]{1,4}[a-z]?(?:[-_][0-9a-z]+)?|S[0-9]{2,4})\s*[:：.]\s*([^\n\[:：]+?)(?=\s{2,}|\s+[0-9]{1,4}[a-z]?\s*[:：]|\[|$)", re.M)


def ref_table(appno):
    """{sign: name} from the specification's 부호의 설명 section (empty when the section is missing)."""
    p = os.path.join(ROOT, "data", "patents", appno, "fulltext.txt")
    if not os.path.exists(p):
        return {}
    t = open(p, encoding="utf-8", errors="replace").read()
    i = t.find("부호의 설명")
    if i < 0:
        return {}
    sec = t[i + 6:i + 6 + 4000]
    for stop in ("【", "청구범위", "청구항", "요약서"):
        j = sec.find(stop)
        if j > 0:
            sec = sec[:j]
    out = {}
    for sign, name in SIGN.findall(sec):
        name = re.sub(r"\s+", " ", name).strip(" ,·;")
        if name and sign not in out and len(name) <= 30:
            out[sign] = name
    return out


def grid(appno, fn):
    """The figure with a 10 × 10 measuring grid; returns (image path, None), or (None, why) when ffmpeg fails."""
    src = os.path.join(ROOT, "data", "patents", appno, fn)
    out_dir = os.path.join(ROOT, "data", "fig_map", appno)
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, os.path.splitext(fn)[0] + "_grid.png")
    vf = ("scale='min(1400,iw)':-2,format=rgb24,"
          "drawgrid=w=iw/10:h=ih/10:t=1:c=0x1e90ff@0.55,drawgrid=w=iw/2:h=ih/2:t=3:c=0xff3b30@0.6")
    if os.path.exists(dst):  # never show an old grid for a figure that can no longer be read
        os.remove(dst)
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-vf", vf, "-frames:v", "1", dst],
                       capture_output=True, text=True, errors="replace")
    if r.returncode or not os.path.exists(dst):
        why = (r.stderr.strip().splitlines() or [f"ffmpeg exit {r.returncode}"])[0]  # the first line names the cause
        return None, re.sub(r"^\[[^\]]*\]\s*", "", why)[:200]
    return dst, None


def norm(s):
    return re.sub(r"[\s·()\-]", "", s or "")


def report(path, figure=None):
    """Print the sign table and grids for one content file; returns how many jobs were skipped."""
    try:
        c = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"== {os.path.basename(path)}  읽을 수 없음: {e} (건너뜀)")
        return 1
    if not appno_ok(c.get("appno")):
        print(f"== {os.path.basename(path)}  appno는 숫자 13자리: {c.get('appno')!r} (건너뜀)")
        return 1
    refs = ref_table(c["appno"])
    jobs, skipped = [], 0
    if figure:
        jobs.append(("figure", figure, []))
    if (c.get("proof") or {}).get("kind") == "anatomy":
        jobs.append(("proof.parts", c["proof"].get("figure"), c["proof"].get("parts", [])))
    sg = c.get("signature") or {}
    if sg.get("type") == "claim" and sg.get("figure"):  # claim elements marked on one drawing
        jobs.append(("signature.claim.elements", sg["figure"], (sg.get("claim") or {}).get("elements", [])))
    if sg.get("type") == "loop":
        jobs.append(("signature.callouts", sg.get("figure"), sg.get("callouts", [])))
        if (sg.get("run") or {}).get("figure") and sg["run"]["figure"] != sg.get("figure"):
            jobs.append(("signature.run", sg["run"]["figure"], []))
        if (sg.get("path") or {}).get("figure"):
            jobs.append(("signature.path.points", sg["path"]["figure"], sg["path"].get("points", [])))
    if not jobs:  # nothing placed yet: grid every drawing so one can be chosen and measured
        d = os.path.join(ROOT, "data", "patents", c["appno"])
        for fn in sorted(os.listdir(d)) if os.path.isdir(d) else []:
            if fn.startswith("fig-") and os.path.getsize(os.path.join(d, fn)) > 3000:
                jobs.append(("drawing", fn, []))
    print(f"== {os.path.basename(path)}  부호의 설명 {len(refs)}개")
    if refs:
        print("  " + " · ".join(f"{k} {v}" for k, v in list(refs.items())[:40]))
    for label, fn, parts in jobs:
        if not fn:
            continue
        if not figure_ok(fn):
            print(f"  {label}: 파일명 형식 오류 {fn!r} (건너뜀)")
            skipped += 1
            continue
        if not os.path.exists(os.path.join(ROOT, "data", "patents", c["appno"], fn)):
            print(f"  {label}: 도면 파일 없음 {fn!r} (격자 건너뜀; data/patents/{c['appno']}/의 fig-* 이름 확인)")
            skipped += 1
        else:
            g, why = grid(c["appno"], fn)
            if g:
                print(f"  {label} on {fn}  grid: {g}")
            else:
                print(f"  {label}: 격자 생성 실패 {fn!r}: {why} (건너뜀)")
                skipped += 1
        for i, p in enumerate(parts):  # the sign check needs only fulltext.txt, so it runs without the grid too
            ref = str(p.get("ref") or "")
            hint = ""
            if not ref:
                cand = [s for s, n in refs.items() if norm(n) and (norm(n) in norm(p["n"]) or norm(p["n"]) in norm(n))]
                hint = f"  ← 부호 후보: {', '.join(cand[:3])}" if cand else "  ← 부호 없음"
            elif ref in refs and norm(refs[ref]) not in norm(p["n"]) and norm(p["n"]) not in norm(refs[ref]):
                hint = f"  ← 명세서 {ref} = '{refs[ref]}' (이름 확인)"
            done = "x·y 있음" if "x" in p and "y" in p else "x·y 필요"
            print(f"    [{i}] {p['n']} ({ref or '-'}) {done}{hint}")
    return skipped


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = sys.argv[1:]
    fig = None
    if "--figure" in args:
        fig = args[args.index("--figure") + 1]
        args = [a for i, a in enumerate(args) if a != "--figure" and (i == 0 or args[i - 1] != "--figure")]
    skipped = sum(report(p, fig) for p in args)  # every file is processed; a skip only sets the exit code
    if skipped:
        sys.exit(f"{skipped}건 건너뜀 (위의 '건너뜀' 줄)")
