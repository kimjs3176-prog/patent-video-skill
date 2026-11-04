"""Narration: a spoken script per section, synthesised with edge-tts and laid onto a built project's scene timeline.

Script source: content["narration"] = {"hook", "overview", "process", "proof", "figures", "features", "apps", "outro"}
(1–2 spoken sentences each; see CONTENT_SPEC "narration"). Sections it leaves out get a plain line assembled from the content fields.

Each scene of the built project is matched to a section by its composition file name. Sections a template has no scene for
are merged into the previous scene (figures is dropped instead). The ending (outro) is never voiced: music only.
The voice is 선희 (ko-KR-SunHiNeural) unless --voice says otherwise. A line that does not fit its scene is re-voiced faster
(natural pace first, then +6 %, +12 %, up to +18 %) and then shortened by whole sentences, so narration never runs into the next scene.

Usage: python -I tools/narration.py <project dir> <content.json> [--voice ko-KR-SunHiNeural]
       python -I tools/narration.py --check data/content/<file>.json [...]   (template S: dry run, flags lines sped past +6 % or cut)
"""
import hashlib
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import CONTACT, ROOT  # noqa: E402
from visuals import pick_figures  # noqa: E402

VOICE = "ko-KR-SunHiNeural"  # house voice: 선희 (SunHi) for every video
SILENT = {"outro"}  # the ending is never voiced (music only)
ORDER = ["hook", "overview", "process", "proof", "figures", "features", "apps", "outro"]
KEYS = {
    "hook": ("teaser", "cover", "hook", "hero", "open", "front"),
    "overview": ("reveal", "summary", "headline", "split", "brief", "name", "title"),
    "process": ("process", "timeline", "flow", "steps", "wave", "how"),
    "proof": ("proof", "results", "chart"),
    "figures": ("figures",),
    "features": ("features", "tiles", "effects", "points", "grid", "cards", "facts"),
    "apps": ("apps", "uses", "outlook", "network", "index"),
    "outro": ("outro", "end", "colophon"),
}
CACHE = os.path.join(ROOT, "data", "voice_cache")
UVX = "uvx.exe" if os.name == "nt" else "uvx"
EDGE_TTS = "edge-tts==7.3.1"  # pinned: the package is fetched from PyPI at run time


# template S: the signature scenes are voiced one by one (scene key → line), the frame scenes keep the section lines
SIG_SCENES = ("route", "journey", "parts", "run", "path", "problem", "primers", "probe", "result", "tubes", "gel", "mix", "effect", "tree", "traits",
              "anatomy")
SIG_FRAME = {"teaser": "hook", "proof": "proof", "features": "features", "apps": "apps", "outro": "outro"}


def scene_key(fname):
    return re.sub(r"^[a-z]+\d*-", "", os.path.basename(fname)[:-5])


def section_of(fname):
    key = scene_key(fname)
    return next((s for s, ks in KEYS.items() if key in ks), None)


def scenes(index_html):
    return [(m.group(1), m.group(2), float(m.group(3)), float(m.group(4))) for m in re.finditer(
        r'<div id="([^"]+)" data-composition-id="[^"]+" data-composition-src="(compositions/[^"]+)" data-start="([\d.]+)" data-duration="([\d.]+)"', index_html)
        if m.group(1) != "tx"]


def auto_script(c):
    """Plain fallback when the content has no authored narration."""
    def clean(s):
        return re.sub(r"<[^>]+>", " ", s.replace("|", "")).strip()
    steps = c["process"]["steps"]
    pr = c["proof"]
    if pr.get("kind") == "anatomy":
        proof = f'{clean(pr.get("title", "핵심 구성"))}은 {", ".join(p["n"] for p in pr["parts"][:3])} 등으로 이루어집니다.'
    else:
        it = pr["items"][0]
        proof = f'{it["l"]}, {it["big"]}{it.get("u", "")}. {clean(it.get("s", "")).split("  ")[0]}.'
    return {
        "hook": f'{clean(c["headline"])}.',
        "overview": f'{c["institute"]}의 {c["sub"]}입니다.',
        "process": f'{clean(c["process"]["title"])}은 {steps[0]["n"]}부터 {steps[-1]["n"]}까지 이어집니다.',
        "proof": proof,
        "figures": "명세서 도면으로 기술을 살펴봅니다.",
        "features": f'{clean(c["features"].get("title", "핵심 특장점"))}을 정리했습니다.',
        "apps": f'{", ".join(a["n"] for a in c["apps"][:3])} 등에 활용할 수 있습니다.',
        "outro": f"기술이전 문의는 {CONTACT}입니다.",
    }


def auto_sig_script(c):
    """Per-scene lines for template S when the signature block has no authored narration."""
    def clean(s):
        return re.sub(r"<[^>]+>", " ", s.replace("|", "")).strip()
    sg = c["signature"]
    out = {}
    if sg.get("removed"):
        out["route"] = f'기존 공정에서 {sg["removed"]} 단계가 빠집니다.'
    if sg.get("stages"):
        out["journey"] = " ".join(f'{s["n"]}, {s["cond"]}.' for s in sg["stages"])
    if sg.get("callouts"):
        out["parts"] = f'{", ".join(p["n"] for p in sg["callouts"][:4])}로 이루어집니다.'
    run = sg.get("run") or {}
    if run:
        out["run"] = clean(run.get("title", "")) + ". " + " ".join(f'{q["n"]}, {q.get("d", "")}.' for q in run.get("steps", [])[:3])
    if sg.get("path"):
        out["path"] = clean(sg["path"].get("title", "")) + "."
    if sg.get("problem"):
        out["problem"] = clean(sg["problem"].get("title", "")) + "."
    if sg.get("primers"):
        out["primers"] = f'{len(sg["primers"])}개 프라이머가 {sg.get("target", "표적")}의 {len(sg.get("layout", []))}개 부위를 인식합니다.'
    if sg.get("probe"):
        out["probe"] = "프로브를 더하면 비특이 신호가 사라지고 표적만 남습니다."
    if sg.get("components"):
        out["mix"] = f'{", ".join(p["n"] for p in sg["components"][:3])}을 배합합니다.'
    if sg.get("effects"):
        out["effect"] = " ".join(f'{e["l"]}, 대조군 {e["control"]}에서 {e["treated"]}{e.get("unit", "")}로 바뀌었습니다.' for e in sg["effects"][:2])
    if sg.get("steps") and sg.get("type") == "lineage":
        out["tree"] = f'{sg.get("variety", "신품종")}은 {sg["steps"][0]["l"]}부터 {sg["steps"][-1]["l"]}까지 선발했습니다.'
    if sg.get("type") == "claim":
        cl = sg["claim"]
        feat = ", ".join(cl["elements"][i]["n"] for i in cl["feature"]["idx"])
        last = cl["preamble"].strip()[-1:] or "항"
        topic = cl["preamble"] + ("은" if "가" <= last <= "힣" and (ord(last) - 0xAC00) % 28 else "는")
        out["anatomy"] = (f'청구항 {cl["no"]}의 {topic} {", ".join(e["n"] for e in cl["elements"][:4])}로 이루어집니다. '
                          f'핵심은 {feat}입니다.')
        out["tree"] = f'여기서 {", ".join(d["l"] for d in sg["deps"][:3])} 등으로 권리가 이어집니다.'
        ev = sg.get("evidence")
        if ev:
            out["tree"] += f' {ev["l"]}, {ev["control"]}에서 {ev["treated"]}{ev.get("u", "")}입니다.'
    if sg.get("traits"):
        out["traits"] = " ".join(f'{t["l"]}은 {t["new"]}{t.get("unit", "")}입니다.' for t in sg["traits"][:2])
    rs = sg.get("result") or {}
    if rs:
        out[{"ct": "result", "tubes": "tubes", "gel": "gel"}[rs["kind"]]] = clean(rs.get("title", "")) + ". " + clean(rs.get("note", ""))
    return out


def sig_script(c):
    """Scene key → line for template S: signature.narration first, then the content's section lines, then generated."""
    base = auto_script(c)
    sec = dict(c.get("narration") or {})
    out = {k: sec.get(v) or base[v] for k, v in SIG_FRAME.items()}
    out.update(auto_sig_script(c))
    out.update(c["signature"].get("narration") or {})
    return {k: v for k, v in out.items() if v and k not in SILENT}


def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:  # a 0 s clip would "fit" every scene and overlap the next line
        raise RuntimeError(f"ffprobe could not read {os.path.basename(path)}: {r.stderr.strip()[-200:]}") from None


def synth(text, voice, rate):
    os.makedirs(CACHE, exist_ok=True)
    h = hashlib.sha1(f"{voice}|{rate}|{text}".encode("utf-8")).hexdigest()[:16]
    mp3 = os.path.join(CACHE, h + ".mp3")
    if not os.path.exists(mp3):
        tmp = f"{mp3}.{os.getpid()}.part.mp3"  # per process: two renderers may synthesize the same line at once
        subprocess.run([UVX, "--from", EDGE_TTS, "edge-tts", "--voice", voice, f"--rate={rate}", "--text", text, "--write-media", tmp],
                       check=True, capture_output=True, timeout=300)
        os.replace(tmp, mp3)
    return mp3, duration(mp3)


def sentences(text):
    return [s for s in re.split(r"(?<=[.!?。])\s+", text.strip()) if s]


def fit(text, avail, voice):
    """Voice text so it lasts at most avail seconds: faster first, then drop trailing sentences."""
    parts = sentences(text)
    while parts:
        t = " ".join(parts)
        for rate in ("+0%", "+6%", "+12%", "+18%"):  # natural pace first; speed up only as much as the scene needs
            mp3, dur = synth(t, voice, rate)
            if dur <= avail:
                return t, mp3, dur, rate
        parts = parts[:-1]
    return None


def assign(slots, script):
    have = {section_of(f) for _, f, _, _ in slots}
    texts = {}
    for sec in ORDER:
        line = (script.get(sec) or "").strip()
        if not line:
            continue
        if sec in have:
            texts[sec] = (texts.get(sec, "") + " " + line).strip()
            continue
        if sec == "figures":
            continue
        prev = next((p for p in reversed(ORDER[:ORDER.index(sec)]) if p in have), None)
        nxt = next((p for p in ORDER[ORDER.index(sec) + 1:] if p in have), None)
        tgt = prev or nxt
        if tgt:
            texts[tgt] = (texts.get(tgt, "") + " " + line).strip()
    return texts


def narrate(out, c, voice=VOICE, lead=0.45, tail=0.55, bgm_volume=0.22):
    ip = os.path.join(out, "index.html")
    html = open(ip, encoding="utf-8").read()
    html = re.sub(r'\s*<audio id="nar-[^>]*></audio>', "", html)
    slots = scenes(html)
    if c.get("signature") and any(scene_key(f) in SIG_SCENES for _, f, _, _ in slots):
        texts, keyof = sig_script(c), scene_key
    else:
        authored = {k: v for k, v in (c.get("narration") or {}).items() if v}
        script = {k: v for k, v in {**auto_script(c), **authored}.items() if k not in SILENT}  # unwritten sections fall back
        if not pick_figures(c):  # the figures scene falls back to step pictograms: no line about drawings
            script.pop("figures", None)
        texts, keyof = assign(slots, script), section_of
    vdir = os.path.join(out, "assets", "voice")
    os.makedirs(vdir, exist_ok=True)
    clips, report = [], []
    for i, (sid, f, st, du) in enumerate(slots):
        sec = keyof(f)
        if sec not in texts:
            continue
        nxt = slots[i + 1][2] if i + 1 < len(slots) else st + du
        start = st + (0.6 if st == 0 else lead)
        avail = max(1.0, nxt + 0.25 - start - tail)  # may run into the cross-fade, never past it
        got = fit(texts[sec], avail, voice)
        if not got:
            report.append(f"{sid}: no fit ({avail:.1f}s)")
            continue
        t, mp3, dur, rate = got
        name = f"{sid}.mp3"
        with open(mp3, "rb") as a, open(os.path.join(vdir, name), "wb") as b:
            b.write(a.read())
        clips.append(f'      <audio id="nar-{sid}" class="clip" src="assets/voice/{name}" data-start="{start:.2f}" data-duration="{dur:.2f}" '
                     f'data-track-index="{20 + len(clips) % 2}" data-volume="1"></audio>')
        report.append(f"{sid} [{sec}] {start:.1f}s +{dur:.1f}s/{avail:.1f}s rate {rate}{'' if t == texts[sec] else ' (shortened)'}: {t}")
    html = re.sub(r'(<audio id="bgm"[^>]*data-volume=")[\d.]+(")', rf"\g<1>{bgm_volume}\2", html)
    block = "\n".join(clips)
    if '      <audio id="bgm"' in html:
        html = html.replace('      <audio id="bgm"', block + '\n      <audio id="bgm"', 1)
    elif clips:  # no music (postprocess dropped the bgm tag): close the voice clips into the main composition instead
        html, k = re.subn(r'(\n\s*</div>\s*\n\s*<script>)', lambda m: "\n" + block + m.group(1), html, count=1)
        if not k:
            raise RuntimeError("index.html: no place to mount the narration clips")
    open(ip, "w", encoding="utf-8").write(html)
    open(os.path.join(out, "narration.txt"), "w", encoding="utf-8").write("\n".join([f"voice: {voice}"] + report) + "\n")
    return report


def check(paths, voice=VOICE, lead=0.45, tail=0.55):
    """Dry run for template S contents (no build needed): voice each scene line and report the ones that would be sped up
    past +6 % or cut. Fills the voice cache, so the later render reuses the clips. Returns the number of cut lines."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import build_sig
    cut = 0
    for p in paths:
        c = json.load(open(p, encoding="utf-8"))
        if not c.get("signature"):
            print(os.path.basename(p), "- no signature (S only)")
            continue
        slots, _ = build_sig.slots_for(c)
        texts = sig_script(c)
        for i, (sid, f, st, du) in enumerate(slots):
            key = scene_key(f + ".html")  # slots name the composition without its extension
            if key not in texts:
                continue
            nxt = slots[i + 1][2] if i + 1 < len(slots) else st + du
            start = st + (0.6 if st == 0 else lead)
            avail = max(1.0, nxt + 0.25 - start - tail)
            got = fit(texts[key], avail, voice)
            if not got:
                print(f"{os.path.basename(p)[:3]} {key:9s} NO FIT in {avail:.1f}s")
                cut += 1
                continue
            t, _, dur, rate = got
            shortened = t != texts[key]
            cut += shortened
            flag = "  <-- cut: shorten the line" if shortened else ("  <-- sped up " + rate if rate not in ("+0%", "+6%") else "")
            print(f"{os.path.basename(p)[:3]} {key:9s} {dur:4.1f}/{avail:4.1f}s {rate}{flag}")
    return cut


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    v = a[a.index("--voice") + 1] if "--voice" in a else VOICE
    if a and a[0] == "--check":  # python -I tools/narration.py --check data/content/<file>.json [...]
        sys.exit(1 if check([x for x in a[1:] if x.endswith(".json")], v) else 0)
    for line in narrate(a[0], json.load(open(a[1], encoding="utf-8")), v):
        print(line)
