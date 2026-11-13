"""Build data/master.json (production order) from patent lists.

Usage: python -I -X utf8 tools/master_list.py <list.xlsx | numbers.txt | list.csv | 10-2019-0145266> [...]
- Excel: every sheet is scanned row by row, left to right; each 10-YYYY-NNNNNNN application number found
  becomes a patent, in reading order. Numbers written right after "제외" (an exclusion note) are skipped, and so are
  numbers that follow "원출원" / 모출원 / 우선권(주장) in their own cell, as in "(원출원 10-…)": they name the listed
  patent's parent, not another patent.
- Text file / CSV (UTF-8 or cp949) / bare arguments: application numbers in the given order. Save .xls as .xlsx first.
Any dash between the digits (en/em dash, minus, full-width, with spaces) is read as "-". A number whose year is not a
filing year is a registration number, not an application number, and is not added. A bare 13-digit number ending in
0000 (1020190010000) is application 10-2019-0010000 or 등록번호 10-2019001: beside the row's own application number it
is taken as the 등록번호, alone it is not added and is reported for the user to confirm (written as 10-2019-0010000,
or given as an argument, it is an application number). Rows that add no patent (a 등록번호 only, no number, …) and
rows that add several are printed for checking.
Duplicates keep their first position; later sources are appended to "sources".
Order decides the output file names, so do not re-run it after rendering.
"""
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAT = re.compile(r"(?<![0-9])(10-?[0-9]{4}-?[0-9]{7})(?![0-9])")  # 10-2019-0145266 or 1020190145266 (Excel numbers)
# Horizontal space only around the dash (thin, narrow, ideographic … spaces too): a row's cells are joined with "\n",
# and "5\n-\n10" must not become "5-10".
HSPACE = r"[^\S\n\r\v\f\x1c-\x1e\x85\u2028\u2029]*"
DASH = re.compile(rf"(?<=[0-9]){HSPACE}[\u2010-\u2015\u2212\ufe63\uff0d-]{HSPACE}(?=[0-9])")
WIDE = {0xFF10 + d: str(d) for d in range(10)}  # full-width digits ０-９
REGNO = re.compile(r"(?<![0-9])10-?[0-9]{7}(?:-?0000)?(?![0-9-])")  # 등록번호 10-2345678 / 1023456780000
# Only right before the number, in its own cell: a 구분 cell "원출원" (as opposed to 분할출원) beside the 출원번호 cell,
# or "10-… (원출원), 10-… (분할)", is about the listed patent itself.
PARENT = re.compile(r"(?:원출원|모출원|우선권(?:\s*주장)?)\s*(?:출원)?\s*(?:번호)?\s*[:：]?\s*$")
LAST_YEAR = time.localtime().tm_year + 1
TITLE = re.compile(r"(?:\[[^\]]*\]\s*)?([^\n()\[\]]{4,120}?)\s*\(\s*(?:출원\s*)?$")


def norm(text):
    return DASH.sub("-", str(text).translate(WIDE))


def app_numbers(text, one_row=False):
    """[(match, digits, why)] for each application-number-shaped string in a norm()ed text, in order.
    why is "" for a patent of the list, else the reason it is not one: "제외", "parent", "regno" (a 등록번호) or
    "ambiguous" (a bare 13-digit number ending in 0000 alone in its row: application number or 등록번호?).
    Each line of text is a row, or with one_row the whole text is (a sheet row, its cells joined by "\n")."""
    found = []
    for m in PAT.finditer(text):
        num = m.group(1).replace("-", "")
        if "제외" in text[max(0, m.start() - 8):m.start()]:  # may sit in the cell to the left, as it always could
            why = "제외"
        elif PARENT.search(text[text.rfind("\n", 0, m.start()) + 1:m.start()]):
            why = "parent"
        elif not 1948 <= int(num[2:6]) <= LAST_YEAR:
            why = "regno"  # e.g. 1023456780000 would read as 10-2345-6780000
        elif len(m.group(1)) == 13 and num.endswith("0000"):
            # application 10-2019-0010000 or 등록번호 10-2019001(-0000)? No serial range rules either out (PCT
            # national-phase serials are 7NNNNNN), so the row decides below
            why = "ambiguous"
        else:
            why = ""
        found.append([m, num, why])
    row = (lambda m: 0) if one_row else (lambda m: text.count("\n", 0, m.start()))
    has_app = {row(m) for m, _, why in found if not why}
    for f in found:
        if f[2] == "ambiguous" and row(f[0]) in has_app:  # beside the row's own application number: its 등록번호
            f[2] = "regno"
    return [tuple(f) for f in found]


def fmt(num):
    return f"{num[:2]}-{num[2:6]}-{num[6:]}"


items, seen, notes = [], {}, []
beside = {"regno": [], "parent": []}  # numbers not added from rows that did add their patent: summed up, not listed


def add(num, source, title="", context=""):
    if num in seen:
        if source not in items[seen[num]]["sources"]:
            items[seen[num]]["sources"].append(source)
        return
    seen[num] = len(items)
    items.append({"appno": num, "appno_fmt": fmt(num), "title": title, "status": "", "sources": [source], "item": context})


def scan_text(text, source, context="", one_row=False):
    """Add the application numbers in text (one sheet row with one_row, or a whole text file, a row per line).
    Returns {line index: [(why, digits)]}; why is "" for an added number (see app_numbers)."""
    text = norm(text)
    found = {}
    for m, num, why in app_numbers(text, one_row):
        found.setdefault(text.count("\n", 0, m.start()), []).append((why, num))
        if why:
            continue
        line_start = text.rfind("\n", 0, m.start()) + 1
        t = TITLE.search(text[line_start:m.start()])
        add(num, source, t.group(1).strip() if t else "", context)
    return found


def check_rows(rows, several=True):
    """rows: [(label, norm()ed text, [what was found])] of one sheet or text file. Note the rows that added no
    patent although they sit below the first numbered row or hold a 등록번호 (a patent may be missing), and rows
    that added several. A 등록번호 or 원출원 number beside the row's application number only goes into `beside`."""
    hit = [i for i, (_, _, f) in enumerate(rows) if f]
    for i, (label, text, f) in enumerate(rows):
        shown = " | ".join(text.split("\n"))[:100]
        added = len({num for why, num in f if not why})
        if added:
            if several and added > 1:
                notes.append(f"{label}: {added} application numbers in one row, each added as a patent: {shown}")
            for why, num in f:
                if why in beside:
                    beside[why].append(f"{label} {num}")
            continue
        for why, num in f:
            if why == "parent":
                notes.append(f"{label}: only a 원출원/우선권 number ({fmt(num)}), not added: {shown}")
            elif why == "regno":
                notes.append(f"{label}: {num} is not an application number (a registration number?), not added: {shown}")
            elif why == "ambiguous":  # ask, do not guess: the wrong guess drops a patent or makes a video of another
                notes.append(f"{label}: {num} = application number {fmt(num)} or 등록번호 {num[:2]}-{num[2:9]}? not added; "
                             f"ask the user, and if it is the application number write it as {fmt(num)} (or give that as "
                             f"an argument) and rerun: {shown}")
        if not f and (hit and i > hit[0] or REGNO.search(text)):
            notes.append(f"{label}: no application number: {shown}")


def read_text(path):
    raw = open(path, "rb").read()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):  # Excel's "유니코드 텍스트"
        return raw.decode("utf-16")
    for enc in ("utf-8-sig", "cp949"):  # cp949: Korean Excel's "CSV (쉼표로 분리)"
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", "replace")  # the numbers are ASCII and still match; titles may be garbled


if __name__ == "__main__":
    for f in (sys.stdout, sys.stderr):  # the notes quote cells (dashes, NBSP, •…); a Windows pipe would be strict cp949
        f.reconfigure(encoding="utf-8", errors="replace")
    for arg in sys.argv[1:]:  # bad inputs stop the run before anything is read: a list left out would shift the order
        if arg.lower().endswith((".xls", ".xlsb", ".ods")):
            sys.exit(f"{arg}: open it in Excel and save it as .xlsx (or CSV), then run again; data/master.json left unchanged")
        if arg.lower().endswith((".xlsx", ".xlsm", ".csv", ".txt", ".tsv")) and not os.path.isfile(arg):
            sys.exit(f"{arg}: no such file; data/master.json left unchanged")
    for arg in sys.argv[1:]:
        if arg.lower().endswith((".xlsx", ".xlsm")):
            import openpyxl
            try:
                wb = openpyxl.load_workbook(arg, read_only=True, data_only=True)
            except Exception as e:  # e.g. an .xls or a password-protected file under an .xlsx name
                sys.exit(f"{arg}: not readable as .xlsx ({type(e).__name__}: {e}); save it again as .xlsx in Excel "
                         "(without a password); data/master.json left unchanged")
            for ws in wb.worksheets:
                ws.reset_dimensions()  # read_only trusts the sheet's <dimension>, which some exporters write as just "A1"
                rows = []
                for r, row in enumerate(ws.iter_rows(values_only=True), 1):
                    cells = [str(int(v)) if isinstance(v, float) and v.is_integer() else str(v) for v in row if v not in (None, "")]
                    if cells:
                        src = f"{os.path.basename(arg)}:{ws.title}:{r}"
                        text = "\n".join(cells)
                        rows.append((src, norm(text), sum(scan_text(text, src, one_row=True).values(), [])))
                check_rows(rows)
        elif os.path.isfile(arg):
            text, name = read_text(arg), os.path.basename(arg)
            found = scan_text(text, name)
            check_rows([(f"{name}:{i + 1}", ln, found.get(i, [])) for i, ln in enumerate(norm(text).split("\n")) if ln.strip()],
                       several=name.lower().endswith(".csv"))  # a plain text list may hold several numbers per line
        else:  # numbers given as arguments (or a mistyped file name)
            # an argument is an application number by definition, so a bare 1020190010000 is not "ambiguous" there
            a = re.sub(r"(?<![0-9-])10[0-9]{11}(?![0-9-])", lambda m: fmt(m.group()), norm(arg))
            found = scan_text(a, "arg").get(0, [])
            check_rows([(f"argument {arg!r}", norm(arg), found)], several=False)
            if not found and not REGNO.search(norm(arg)):
                notes.append(f"argument {arg!r}: no such file, and no application number in it")

    for why, what in (("regno", "registration number(s)"), ("parent", "원출원/우선권 number(s)")):
        if beside[why]:  # e.g. a 등록번호 column next to the 출원번호 one: expected, so one line for all of them
            notes.append(f"{len(beside[why])} {what} beside an application number, not added: "
                         + ", ".join(beside[why][:3]) + (" …" if len(beside[why]) > 3 else ""))
    if not items:  # never replace an existing production order with an empty one
        for n in notes:
            print(n)
        sys.exit("no application numbers (10-YYYY-NNNNNNN) found; data/master.json left unchanged")
    for n, it in enumerate(items, 1):
        it["order"] = n
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    json.dump(items, open(os.path.join(ROOT, "data", "master.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(items), "patents ->", os.path.join(ROOT, "data", "master.json"))
    if notes:  # show these to the user: a patent may be missing, or a row may hold more than one
        print(f"to check ({len(notes)}):")
        print("\n".join("  " + n for n in notes[:40]) + (f"\n  … {len(notes) - 40} more" if len(notes) > 40 else ""))
