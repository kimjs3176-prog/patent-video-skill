"""Fetch patent specifications from the KIPRIS Plus Open API.

Usage: python -I tools/kipris.py <application-number> [...] | --all
       python -I tools/kipris.py --pdf <application-number> [...]   (no key: uses data/raw/<appno>.pdf downloaded by hand)
Writes data/raw/<appno>.xml and data/patents/<appno>/biblio.json, fulltext.txt and fig-*.jpg.
The service key is read from the KIPRIS_API_KEY env var or the project's .env file.
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice/getBibliographyDetailInfoSearch"
PDF_HOSTS = (".kipris.or.kr",)  # the full-text path the API returns must point back to KIPRIS


def service_key():
    key = os.environ.get("KIPRIS_API_KEY")
    if key:
        return key
    with open(os.path.join(ROOT, ".env"), encoding="utf-8") as f:
        for line in f:
            if line.startswith("KIPRIS_API_KEY="):
                return line.split("=", 1)[1].strip()
    raise SystemExit("KIPRIS_API_KEY not set")


def fetch(appno):
    num = re.sub(r"\D", "", appno)
    url = BASE + "?" + urllib.parse.urlencode({"applicationNumber": num, "ServiceKey": service_key()})
    with urllib.request.urlopen(url, timeout=30) as r:
        raw = r.read()
    os.makedirs(os.path.join(ROOT, "data", "raw"), exist_ok=True)
    with open(os.path.join(ROOT, "data", "raw", num + ".xml"), "wb") as f:
        f.write(raw)
    return num, ET.fromstring(raw)


def text(el, path):
    n = el.find(path)
    return (n.text or "").strip() if n is not None and n.text else ""


def parse(root):
    item = root.find(".//item")
    if item is None:
        msg = text(root, ".//resultMsg") or text(root, ".//errMsg") or ET.tostring(root, encoding="unicode")[:300]
        raise RuntimeError(msg)
    b = item.find("biblioSummaryInfoArray/biblioSummaryInfo")
    info = {k: text(b, k) for k in (
        "inventionTitle", "inventionTitleEng", "applicationNumber", "applicationDate", "registerNumber",
        "registerDate", "openNumber", "openDate", "publicationNumber", "publicationDate", "registerStatus",
        "claimCount", "originalApplicationKind")} if b is not None else {}
    info["ipc"] = [text(i, "ipcNumber") for i in item.findall("ipcInfoArray/ipcInfo")]
    info["applicants"] = [text(a, "name") for a in item.findall("applicantInfoArray/applicantInfo")]
    info["inventors"] = [text(a, "name") for a in item.findall("inventorInfoArray/inventorInfo")]
    info["abstract"] = text(item, "abstractInfoArray/abstractInfo/astrtCont")
    info["claims"] = [text(c, "claim") for c in item.findall("claimInfoArray/claimInfo")]
    info["images"] = [{k: text(p, k) for k in ("largePath", "path")} for p in item.findall("imagePathInfo")]
    info["rnd"] = [{k: text(r, k) for k in ("rndDepartmentName", "rndProjectName", "rndSpecialInstitutionName", "rndTaskName")}
                   for r in item.findall("rndInfoArray/rndInfo")]
    return info


def fulltext(num, outdir):
    """Download the registered (else published) full-text PDF; extract its text and figure images."""
    for op in ("getPubFullTextInfoSearch", "getAnnFullTextInfoSearch"):
        url = BASE.rsplit("/", 1)[0] + "/" + op + "?" + urllib.parse.urlencode({"applicationNumber": num, "ServiceKey": service_key()})
        with urllib.request.urlopen(url, timeout=30) as r:
            root = ET.fromstring(r.read())
        path = text(root, ".//item/path")
        if path:
            break
    else:
        return None
    u = urllib.parse.urlparse(path)
    if u.scheme not in ("http", "https") or not (u.hostname or "").endswith(PDF_HOSTS):
        raise RuntimeError("unexpected full-text location: " + (u.hostname or u.scheme or "?"))
    if u.scheme == "http":
        path = urllib.parse.urlunparse(u._replace(scheme="https"))
    pdf = os.path.join(ROOT, "data", "raw", num + ".pdf")
    with urllib.request.urlopen(path, timeout=60) as r, open(pdf, "wb") as f:
        f.write(r.read())
    return parse_pdf(pdf, outdir)


def parse_pdf(pdf, outdir):
    """Extract the text and the JPEG figures of a gazette PDF into outdir."""
    import pypdf
    reader = pypdf.PdfReader(pdf)
    with open(os.path.join(outdir, "fulltext.txt"), "w", encoding="utf-8") as f:
        f.write("\n=====PAGE=====\n".join(p.extract_text() or "" for p in reader.pages))
    figs = []
    for i, page in enumerate(reader.pages):
        xo = page["/Resources"].get("/XObject")
        if not xo:
            continue
        for k, v in xo.get_object().items():
            v = v.get_object()
            if v.get("/Filter") == "/DCTDecode" and int(v.get("/Width", 0)) > 200:
                fn = f"fig-p{i + 1}-{re.sub(r'[^A-Za-z0-9_-]', '_', k[1:])}.jpg"
                with open(os.path.join(outdir, fn), "wb") as f:
                    f.write(v._data)
                figs.append(fn)
    return {"pdf": os.path.relpath(pdf, ROOT), "pages": len(reader.pages), "figures": figs}


if __name__ == "__main__":
    import time
    os.makedirs(os.path.join(ROOT, "data", "patents"), exist_ok=True)
    args = sys.argv[1:]
    if args[:1] == ["--pdf"]:
        for a in args[1:]:
            num = re.sub(r"\D", "", a)
            pdf = os.path.join(ROOT, "data", "raw", num + ".pdf")
            if not os.path.exists(pdf):
                print(num, "missing", os.path.relpath(pdf, ROOT))
                continue
            outdir = os.path.join(ROOT, "data", "patents", num)
            os.makedirs(outdir, exist_ok=True)
            ft = parse_pdf(pdf, outdir)
            with open(os.path.join(outdir, "biblio.json"), "w", encoding="utf-8") as f:
                json.dump({"applicationNumber": num, "claims": [], "source": "pdf", "fulltext": ft}, f, ensure_ascii=False, indent=2)
            print(num, "ok from PDF:", ft["pages"], "pages,", len(ft["figures"]), "figures (claims: read them in fulltext.txt)")
        sys.exit(0)
    if args == ["--all"]:
        master = json.load(open(os.path.join(ROOT, "data", "master.json"), encoding="utf-8"))
        args = [m["appno"] for m in master
                if not os.path.exists(os.path.join(ROOT, "data", "patents", m["appno"], "biblio.json"))]
        print(len(args), "to fetch", flush=True)
    for a in args:
        time.sleep(0.3)
        try:
            num, root = fetch(a)
        except Exception as e:  # network hiccup: report and move on, rerun resumes
            print(a, "FETCH ERROR", e, flush=True)
            continue
        try:
            info = parse(root)
        except RuntimeError as e:
            print(num, "ERROR", e)
            continue
        outdir = os.path.join(ROOT, "data", "patents", num)
        os.makedirs(outdir, exist_ok=True)
        try:
            info["fulltext"] = fulltext(num, outdir)
        except Exception as e:
            print(num, "FULLTEXT ERROR", e, flush=True)
            info["fulltext"] = None
        with open(os.path.join(outdir, "biblio.json"), "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        ft = info["fulltext"] or {}
        print(num, "ok", len(info["claims"]), "claims,", ft.get("pages"), "pages,", len(ft.get("figures", [])), "figures")
