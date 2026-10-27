"""Build data/master.json (production order) from patent lists.

Usage: python -I tools/master_list.py <list.xlsx | numbers.txt | 10-2019-0145266> [...]
- Excel: every sheet is scanned row by row, left to right; each 10-YYYY-NNNNNNN application number found
  becomes a patent, in reading order. Numbers written right after "제외" (an exclusion note) are skipped.
- Text file / bare arguments: application numbers in the given order.
Duplicates keep their first position; later sources are appended to "sources".
Order decides the output file names and the background-music rotation, so do not re-run it after rendering.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAT = re.compile(r"(?<![0-9])(10-\d{4}-\d{7})(?![0-9])")
TITLE = re.compile(r"(?:\[[^\]]*\]\s*)?([^\n()\[\]]{4,120}?)\s*\(\s*(?:출원\s*)?$")

items, seen = [], {}


def add(appno, source, title="", context=""):
    num = appno.replace("-", "")
    if num in seen:
        if source not in items[seen[num]]["sources"]:
            items[seen[num]]["sources"].append(source)
        return
    seen[num] = len(items)
    items.append({"appno": num, "appno_fmt": appno, "title": title, "status": "", "sources": [source], "item": context})


def scan_text(text, source, context=""):
    for m in PAT.finditer(text):
        before = text[max(0, m.start() - 8):m.start()]
        if "제외" in before:
            continue
        line_start = text.rfind("\n", 0, m.start()) + 1
        t = TITLE.search(text[line_start:m.start()])
        add(m.group(1), source, t.group(1).strip() if t else "", context)


for arg in sys.argv[1:]:
    if arg.lower().endswith((".xlsx", ".xlsm")):
        import openpyxl
        wb = openpyxl.load_workbook(arg, read_only=True, data_only=True)
        for ws in wb.worksheets:
            for r, row in enumerate(ws.iter_rows(values_only=True), 1):
                cells = [str(v) for v in row if v not in (None, "")]
                if cells:
                    scan_text("\n".join(cells), f"{os.path.basename(arg)}:{ws.title}:{r}")
    elif os.path.exists(arg):
        scan_text(open(arg, encoding="utf-8").read(), os.path.basename(arg))
    else:
        scan_text(arg, "arg")

for n, it in enumerate(items, 1):
    it["order"] = n
os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
json.dump(items, open(os.path.join(ROOT, "data", "master.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(items), "patents ->", os.path.join(ROOT, "data", "master.json"))
