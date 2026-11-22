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
# only the institutes of 농촌진흥청: 국립산림과학원, 국립종자원, 국립수산과학원 … belong to other ministries and are left alone
RDA = ("국립농업과학원", "국립식량과학원", "국립원예특작과학원", "국립축산과학원")
PAT = re.compile(r"(?:주관기관|과제수행기관명|과제수행기관|수행기관)\s*[:：]?\s*(" + "|".join(RDA) + r"|농촌진흥청)")

for path in sys.argv[1:]:
    try:
        c = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError) as e:  # one broken file must not stop the others
        print(os.path.basename(path), "읽을 수 없음:", e, "(건너뜀)")
        continue
    if not isinstance(c.get("appno"), str) or not appno_ok(c.get("appno")):
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
