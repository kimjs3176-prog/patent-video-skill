"""Write copies of the source Excel lists with a last column naming each row's video file(s).

Usage: python -I tools/annotate_lists.py [--template A..I|S] <list.xlsx> [...]
The column lists the deliverable patents/{출원번호}.mp4 (see tools/export.py); --template X lists that template's
renders_* file name instead.
Copies are saved next to the originals as <name>_영상파일명.xlsx; originals are never modified.
The header row of each sheet is the row just above the first row that mentions a patent;
the new column goes right after the sheet's last used column (past any merged cell of the rows it writes) and copies
its style. A sheet that already has the column (an annotated copy given again) gets it refilled, not a second one.
Patent numbers are read as master_list.py reads them (dashes, 원출원 notes, 등록번호).
"""
import copy
import json
import os
import sys

import openpyxl
from openpyxl.cell.cell import MergedCell
from openpyxl.styles import Alignment

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from master_list import app_numbers, norm  # noqa: E402  the same numbers as the production order

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABEL = "기술소개 영상 파일"

args = sys.argv[1:]
tpl = None
if "--template" in args:
    tpl = args[args.index("--template") + 1].upper()
    args = [a for i, a in enumerate(args) if a != "--template" and (i == 0 or args[i - 1] != "--template")]
master = json.load(open(os.path.join(ROOT, "data", "master.json"), encoding="utf-8"))
if tpl:  # the working copy produce.py wrote: renders[_x]/<order>-<appno>[_x][_nar].mp4 (narrated one preferred)
    d = "renders" if tpl == "A" else f"renders_{tpl.lower()}"
    suffix = "" if tpl == "A" else f"_{tpl.lower()}"
    SLUG = {}
    for m in master:
        base = f'{d}/{m["order"]:03d}-{m["appno"]}{suffix}'
        SLUG[m["appno"]] = next((f for f in (base + "_nar.mp4", base + ".mp4") if os.path.exists(os.path.join(ROOT, f))), None)
else:
    SLUG = {m["appno"]: f'patents/{m["appno"]}.mp4' for m in master}
missing = sorted(a for a, f in SLUG.items() if not f or not os.path.exists(os.path.join(ROOT, f)))
SLUG = {a: f for a, f in SLUG.items() if a not in missing}  # only videos that exist (SKIPped patents get no file name)
if missing:
    print(f"no video yet for {len(missing)} patent(s), left blank:", ", ".join(missing[:10]) + (" …" if len(missing) > 10 else ""))


LISTED = {m["appno"] for m in master}


def numbers_in(values):
    """The listed patents a row mentions, its cells read as one text (as master_list.py reads a row)."""
    cells = [str(int(v)) if isinstance(v, float) and v.is_integer() else str(v) for v in values if v not in (None, "")]
    return [num for _, num, why in app_numbers(norm("\n".join(cells))) if not why and num in LISTED]


def free_col(ws, col, rows):
    """The first column from col on that no merged range covers in any of rows (a merged cell cannot be written).
    Merges elsewhere, e.g. a title above the header, do not move the column."""
    spans = [m for m in ws.merged_cells.ranges if any(m.min_row <= r <= m.max_row for r in rows)]
    while any(m.min_col <= col <= m.max_col for m in spans):
        col += 1
    return col


def annotate(path):
    wb = openpyxl.load_workbook(path)
    for ws in wb.worksheets:
        used = [(c.row, c.column) for row in ws.iter_rows() for c in row if c.value not in (None, "")]
        old = next((c for r, c in used if ws.cell(r, c).value == LABEL), None)  # this list was annotated before
        used = [(r, c) for r, c in used if c != old]
        if not used:
            continue
        last_row = max(r for r, _ in used)
        last_col = max(c for _, c in used)
        rows = {r: numbers_in(ws.cell(r, c).value for c in range(1, last_col + 1) if c != old) for r in range(1, last_row + 1)}
        first = next((r for r in rows if rows[r]), None)
        if first is None:
            continue
        header = max(1, first - 1)
        files = {r: [f for f in dict.fromkeys(SLUG.get(a) for a in rows[r]) if f] for r in range(first, last_row + 1)}
        if not any(files.values()):  # no video yet for any patent of this sheet
            continue
        col = old or free_col(ws, last_col + 1, [header] + [r for r in files if files[r]])
        if old:  # refilling: clear the earlier run's names first
            for r in range(header + 1, last_row + 1):
                if not isinstance(ws.cell(r, col), MergedCell):
                    ws.cell(r, col).value = None
        h = ws.cell(header, col, LABEL)
        h._style = copy.copy(ws.cell(header, last_col)._style)
        n = 0
        for r, fs in files.items():
            if fs:
                c = ws.cell(r, col, "\n".join(fs))
                c._style = copy.copy(ws.cell(r, last_col)._style)
                c.alignment = Alignment(wrap_text=True, vertical="top")
                n += 1
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 30
        print(os.path.basename(path), ws.title, "->", n, "rows" + (" (column refilled)" if old else ""))
    out = path[: path.rfind(".")] + "_영상파일명.xlsx"
    wb.save(out)
    print("saved", out)


failed = 0
for path in args:  # one bad list must not keep the others from being annotated
    try:
        annotate(path)
    except Exception as e:
        print(f"{os.path.basename(path)}: not annotated, {type(e).__name__}: {e}", flush=True)
        failed += 1
if failed:
    sys.exit(f"{failed} of {len(args)} list(s) not annotated")
