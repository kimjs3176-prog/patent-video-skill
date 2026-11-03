"""Template S: structural checks on a content's `signature` block, and a batch report of how distinct the films are.

Each patent's film should move what that technology itself moves (CONTENT_SPEC "특징 구조화"): the material that changes,
the medium that flows through the device, the sequence that is recognised. `problems()` rejects blocks too thin to carry
that (validate.py calls it); the report flags films in a batch that would come out with the same structure.

Usage: python -I tools/sigcheck.py data/content/*.json      (writes nothing; prints the plan and the warnings)
"""
import collections
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYS = {"soak", "cut", "steam", "heat", "boil", "dry", "roast", "fry", "freeze", "ferment", "mix", "extract", "filter", "puff", "mash", "cold"}
MEDIA = {"air", "water", "heat", "cold", "gas", "uv", "light", "solid", "power"}
FRAME = {"teaser", "proof", "features", "apps", "outro"}
SCENES = {"journey": {"route", "journey"}, "loop": {"parts", "run", "path"},
          "sequence": {"problem", "primers", "probe", "result", "tubes", "gel"},
          "formula": {"mix", "effect"}, "lineage": {"tree", "traits"}}
BASES = re.compile(r"[ACGTURYKMSWBDHVNI]+")


def _frac(v):
    return isinstance(v, (int, float)) and 0 <= v <= 1


def _figure(c, fn, at, errs):
    if not fn:
        errs.append(f"{at}: 도면 파일 없음")
    elif not os.path.exists(os.path.join(ROOT, "data", "patents", c["appno"], fn)):
        errs.append(f"{at}: data/patents/{c['appno']}/{fn} 없음")


def _points(pts, at, errs, lo=3, hi=6, named=False):
    if not lo <= len(pts) <= hi:
        errs.append(f"{at}: {lo}~{hi}개 필요({len(pts)}개)")
    for i, p in enumerate(pts):
        if not isinstance(p, dict if named else (list, tuple)):
            errs.append(f"{at}[{i}]: " + ('{"x", "y", …} 객체' if named else "[x, y] 배열") + " 필요")
            continue
        x, y = (p.get("x"), p.get("y")) if named else (p[0], p[1]) if len(p) == 2 else (None, None)
        if not (_frac(x) and _frac(y)):
            errs.append(f"{at}[{i}]: 좌표는 도면 비율 0~1")


def problems(c):
    """Structural errors in c['signature'] (empty list when it can carry a distinctive film)."""
    try:
        return _problems(c)
    except (KeyError, TypeError, AttributeError, IndexError, ValueError) as e:  # malformed block: report, never crash
        return [f"signature 구조 오류: {type(e).__name__} {e}"]


def _problems(c):
    sg = c.get("signature")
    if not sg:
        return []
    errs = []
    kind = sg.get("type")
    if kind not in SCENES:
        return [f"signature.type은 journey·loop·sequence·formula·lineage 중 하나({kind})"]
    for k in (sg.get("narration") or {}):
        if k not in SCENES[kind] | FRAME:
            errs.append(f"signature.narration 알 수 없는 장면: {k} ({kind}에는 {', '.join(sorted(SCENES[kind] | FRAME))})")
    if kind == "journey":
        st = sg.get("stages") or []
        if not 4 <= len(st) <= 6:
            errs.append(f"stages 4~6개({len(st)}개)")
        for i, s in enumerate(st):
            if not s.get("n") or not s.get("cond"):
                errs.append(f"stages[{i}]: n·cond 필요")
            if s.get("key") not in KEYS:
                errs.append(f"stages[{i}].key '{s.get('key')}': {', '.join(sorted(KEYS))} 중 재료 변화에 맞는 것")
            t = s.get("t")
            if t is not None and not (isinstance(t, list) and len(t) == 2 and all(isinstance(v, (int, float)) for v in t) and t[0] <= t[1]):
                errs.append(f"stages[{i}].t는 [최저, 최고] 숫자")
            if t is None and not s.get("label"):
                errs.append(f"stages[{i}]: 온도 t가 없으면 label(시간·비율 등) 필요")
        if len({s.get("key") for s in st}) < 2:
            errs.append("모든 단계의 그림(key)이 같음: 재료가 바뀌는 모습이 보이지 않음")
        # fewer than two stated temperatures is fine: the stage rail and each stage's label carry the journey
        if sg.get("removed") and sg["removed"] not in (sg.get("conventional") or []):
            errs.append("removed는 conventional 안의 단계 이름이어야 함")
    elif kind == "loop":
        _figure(c, sg.get("figure"), "signature.figure", errs)
        _points(sg.get("callouts") or [], "callouts", errs, 3, 5, named=True)
        run = sg.get("run") or {}
        if not run:
            errs.append("run(작동 장면) 필요")
        else:
            if run.get("figure"):
                _figure(c, run["figure"], "run.figure", errs)
            flows = run.get("flows") or []
            if not 1 <= len(flows) <= 3:
                errs.append(f"run.flows 1~3개({len(flows)}개): 장치 안에서 실제로 움직이는 매질")
            for i, f in enumerate(flows):
                if f.get("color") not in MEDIA:
                    errs.append(f"run.flows[{i}].color: {', '.join(sorted(MEDIA))}")
                if not f.get("label"):
                    errs.append(f"run.flows[{i}].label 필요(범례에 쓰는 매질 이름)")
                _points(f.get("pts") or [], f"run.flows[{i}].pts", errs)
            for i, g in enumerate(run.get("glows") or []):
                if g.get("color") not in MEDIA:
                    errs.append(f"run.glows[{i}].color: {', '.join(sorted(MEDIA))}")
            logic, steps = run.get("logic"), run.get("steps")
            if bool(logic) == bool(steps):
                errs.append("run에는 logic(4단계 제어 루프)+rules 또는 steps(3~5) 중 하나만")
            elif logic and (len(logic) != 4 or not 1 <= len(run.get("rules") or []) <= 2):
                errs.append("run.logic은 4개, rules는 1~2개")
            elif steps and not 3 <= len(steps) <= 5:
                errs.append("run.steps 3~5개")
        if sg.get("path"):
            _figure(c, sg["path"].get("figure"), "path.figure", errs)
            _points(sg["path"].get("points") or [], "path.points", errs, 3, 5, named=True)
    elif kind == "formula":
        comps, eff = sg.get("components") or [], sg.get("effects") or []
        if not 2 <= len(comps) <= 6:
            errs.append(f"components 2~6개({len(comps)}개): 배합 성분과 비율")
        for i, p in enumerate(comps):
            if not p.get("n") or not isinstance(p.get("v"), (int, float)) or p["v"] <= 0:
                errs.append(f"components[{i}]: n과 양수 v(명세서의 비율·함량) 필요")
        if not 1 <= len(eff) <= 4:
            errs.append(f"effects 1~4개({len(eff)}개): 대조군 대비 효능 수치")
        for i, e in enumerate(eff):
            if not e.get("l") or not all(isinstance(e.get(k), (int, float)) for k in ("control", "treated")):
                errs.append(f"effects[{i}]: l과 숫자 control·treated(명세서 값 그대로) 필요")
            if e.get("better", "up") not in ("up", "down"):
                errs.append(f"effects[{i}].better는 up 또는 down")
    elif kind == "lineage":
        cross, steps, tr = sg.get("cross") or {}, sg.get("steps") or [], sg.get("traits") or []
        if not ((cross.get("mother") and cross.get("father")) or sg.get("source")):
            errs.append("cross{mother, father}(교배 품종) 또는 source(분리원·선발 모집단) 필요")
        if not 3 <= len(steps) <= 6 or any(not (s.get("gen") and s.get("l")) for s in steps):
            errs.append("steps 3~6개, 각 gen(세대·단계)·l 필요")
        if not sg.get("variety"):
            errs.append("variety(신품종·균주 이름) 필요")
        if not 1 <= len(tr) <= 5:
            errs.append(f"traits 1~5개({len(tr)}개): 대비 품종과 비교한 형질")
        for i, t in enumerate(tr):
            if not t.get("l") or not all(isinstance(t.get(k), (int, float)) for k in ("new", "check")):
                errs.append(f"traits[{i}]: l과 숫자 new·check(명세서 값 그대로) 필요")
            if t.get("better", "up") not in ("up", "down"):
                errs.append(f"traits[{i}].better는 up 또는 down")
        if not sg.get("check"):
            errs.append("check(대비 품종·대조 균주 이름) 필요")
    else:
        pb = sg.get("problem") or {}
        if not 2 <= len(pb.get("cards") or []) <= 3:
            errs.append("problem.cards 2~3개")
        lay = sg.get("layout") or []
        pr = sg.get("primers") or []
        if len(lay) < 2 or not 1 <= len(pr) <= 8:
            errs.append("layout 2곳 이상, primers 1~8개")
        for i, p in enumerate(pr):
            if not BASES.fullmatch(p.get("seq", "")):
                errs.append(f"primers[{i}].seq: 명세서 서열 그대로(대문자 염기)")
            if not set(p.get("regions") or []) or not set(p.get("regions") or []) <= set(lay):
                errs.append(f"primers[{i}].regions는 layout 안의 이름")
        rs = sg.get("result") or {}
        rk = rs.get("kind")
        if rk == "tubes":
            tb = rs.get("tubes") or []
            if not 3 <= len(tb) <= 6 or not any(t.get("pos") for t in tb) or all(t.get("pos") for t in tb):
                errs.append("result.tubes 3~6개, 양성·음성 모두 포함")
        elif rk == "gel":
            lad, lanes = rs.get("ladder") or [], rs.get("lanes") or []
            if len(lad) < 3 or not 3 <= len(lanes) <= 8:
                errs.append("result.ladder 3개 이상, lanes 3~8개")
            for ln in lanes:
                if any(not (min(lad, default=0) * 0.8 <= b <= max(lad, default=0) * 1.2) for b in ln.get("bands", [])):
                    errs.append(f"result.lanes '{ln.get('l')}': 밴드 크기가 래더 범위 밖")
        elif rk == "ct":
            if not rs.get("sensitivity") or not rs.get("specificity") or not sg.get("cycles") or not sg.get("cutoff"):
                errs.append("result(ct): sensitivity·specificity와 최상위 cycles·cutoff 필요")
        else:
            errs.append("result.kind는 ct·tubes·gel 중 하나")
        if not 2 <= len(sg.get("field") or []) <= 4:
            errs.append("field 칩 2~4개")
    return errs


def fingerprint(c):
    """What the viewer would perceive as the film's structure; equal fingerprints look like the same film."""
    sg = c["signature"]
    if sg["type"] == "journey":
        return ("journey", tuple(s.get("key") for s in sg["stages"]), bool(sg.get("removed")))
    if sg["type"] == "loop":
        run = sg["run"]
        return ("loop", tuple(sorted(f.get("color") for f in run.get("flows", []))), "logic" if run.get("logic") else "steps", bool(sg.get("path")))
    if sg["type"] == "formula":
        return ("formula", len(sg.get("components", [])), len(sg.get("effects", [])))
    if sg["type"] == "lineage":
        return ("lineage", bool(sg.get("cross")), len(sg.get("steps", [])), len(sg.get("traits", [])))
    return ("sequence", sg["result"]["kind"], bool(sg.get("probe")), len(sg.get("layout", [])))


def describe(c):
    sg = c["signature"]
    if sg["type"] == "journey":
        bits = " → ".join(f'{s["n"]}({s["key"]})' for s in sg["stages"])
        return ("공정 편집 + " if sg.get("removed") else "") + bits
    if sg["type"] == "loop":
        run = sg["run"]
        media = ", ".join(f'{f["label"]}({f["color"]})' for f in run.get("flows", []))
        side = "제어 루프" if run.get("logic") else f'단계 {len(run.get("steps", []))}'
        return f'부품 {len(sg["callouts"])} · 흐름 {media} · {side}' + (" · 두 번째 도면 경로" if sg.get("path") else "")
    if sg["type"] == "formula":
        return f'성분 {len(sg["components"])}(' + ", ".join(p["n"] for p in sg["components"][:3]) + f') → 효능 {len(sg["effects"])}'
    if sg["type"] == "lineage":
        top = "교배 " + " × ".join([sg["cross"]["mother"], sg["cross"]["father"]]) if sg.get("cross") else "분리 " + sg.get("source", "")
        return f'{top} → 단계 {len(sg["steps"])} → {sg.get("variety", "")} · 형질 {len(sg["traits"])}'
    rs = sg["result"]
    return f'프라이머 {len(sg["primers"])} → 부위 {len(sg["layout"])}' + (" · 프로브 비교" if sg.get("probe") else "") + f' · 판독 {rs["kind"]}'


def main(paths):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    groups, missing, bad = collections.defaultdict(list), [], 0
    for p in paths:
        slug = os.path.basename(p)[:-5]
        try:
            c = json.load(open(p, encoding="utf-8"))
        except (OSError, ValueError) as e:
            print(f"{slug} ✗ JSON 오류: {e}")
            bad += 1
            continue
        if "signature" not in c:
            missing.append(slug)
            continue
        errs = problems(c)
        bad += bool(errs)
        print(f'{slug} [{c["signature"].get("type")}] ' + ("(구조 오류)" if errs else describe(c)))
        for e in errs:
            print("   ✗", e)
        if not errs:
            groups[fingerprint(c)].append(slug)
    dup = [v for v in groups.values() if len(v) > 1]
    for v in dup:
        print("⚠ 같은 구성으로 보일 수 있음:", ", ".join(v), "→ 단계 그림·매질·판독 중 하나 이상을 그 특허만의 것으로")
    if missing:
        print(f"시그니처 없음 {len(missing)}건(템플릿 S에서 SKIP):", ", ".join(missing[:12]) + (" …" if len(missing) > 12 else ""))
    print(f"검사 {len(paths) - len(missing)}건 · 구조 오류 {bad}건 · 구성 중복 {sum(len(v) for v in dup)}건")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
