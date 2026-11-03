"""Set content.institute from the spec's 주관기관 / 과제수행기관명 / 과제수행기관 line when it names an RDA institute.

Usage: python -I tools/fix_institute.py data/content/*.json
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate import appno_ok  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAT = re.compile(r"(?:주관기관|과제수행기관명|과제수행기관|수행기관)\s*[:：]?\s*(국립[가-힣]+원|농촌진흥청)")

for path in sys.argv[1:]:
    c = json.load(open(path, encoding="utf-8"))
    if not appno_ok(c.get("appno")):
        print(os.path.basename(path), "appno는 숫자 13자리:", repr(c.get("appno")), "(건너뜀)")
        continue
    ft = os.path.join(ROOT, "data", "patents", c["appno"], "fulltext.txt")
    if not os.path.exists(ft):
        continue
    m = PAT.search(open(ft, encoding="utf-8").read())
    if not m:
        continue
    inst = m.group(1)
    new = "농촌진흥청" if inst == "농촌진흥청" else f"농촌진흥청 {inst}"
    if c.get("institute") != new:
        print(os.path.basename(path), c.get("institute"), "->", new)
        c["institute"] = new
        json.dump(c, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
