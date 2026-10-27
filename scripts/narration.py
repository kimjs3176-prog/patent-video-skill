"""Narration: a spoken script per section, synthesised with edge-tts and laid onto a built project's scene timeline.

Script source: content["narration"] = {"hook", "overview", "process", "proof", "figures", "features", "apps", "outro"}
(1–2 spoken sentences each; see CONTENT_SPEC "narration"). Without it, a plain script is assembled from the content fields.

Each scene of the built project is matched to a section by its composition file name. Sections a template has no scene for
are merged into the previous scene (figures is dropped instead). A line that does not fit its scene is re-voiced faster
(+6 % by default, up to +22 %) and then shortened by whole sentences, so narration never runs into the next scene.

Usage: python -I tools/narration.py <project dir> <content.json> [--voice ko-KR-SunHiNeural]
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

VOICE = "ko-KR-SunHiNeural"
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


def section_of(fname):
    key = re.sub(r"^[a-z]+\d*-", "", os.path.basename(fname)[:-5])
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


def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def synth(text, voice, rate):
    os.makedirs(CACHE, exist_ok=True)
    h = hashlib.sha1(f"{voice}|{rate}|{text}".encode("utf-8")).hexdigest()[:16]
    mp3 = os.path.join(CACHE, h + ".mp3")
    if not os.path.exists(mp3):
        tmp = mp3 + ".part.mp3"
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
        for rate in ("+6%", "+14%", "+22%"):
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
    script = dict(c.get("narration") or auto_script(c))
    if not pick_figures(c):  # the figures scene falls back to step pictograms: no line about drawings
        script.pop("figures", None)
    texts = assign(slots, script)
    vdir = os.path.join(out, "assets", "voice")
    os.makedirs(vdir, exist_ok=True)
    clips, report = [], []
    for i, (sid, f, st, du) in enumerate(slots):
        sec = section_of(f)
        if sec not in texts:
            continue
        nxt = slots[i + 1][2] if i + 1 < len(slots) else st + du
        avail = max(1.0, nxt + 0.25 - st - lead - tail)  # may run into the cross-fade, never past it
        got = fit(texts[sec], avail, voice)
        if not got:
            report.append(f"{sid}: no fit ({avail:.1f}s)")
            continue
        t, mp3, dur, rate = got
        name = f"{sid}.mp3"
        with open(mp3, "rb") as a, open(os.path.join(vdir, name), "wb") as b:
            b.write(a.read())
        start = st + (0.6 if st == 0 else lead)
        clips.append(f'      <audio id="nar-{sid}" class="clip" src="assets/voice/{name}" data-start="{start:.2f}" data-duration="{dur:.2f}" '
                     f'data-track-index="{20 + len(clips) % 2}" data-volume="1"></audio>')
        report.append(f"{sid} [{sec}] {start:.1f}s +{dur:.1f}s/{avail:.1f}s rate {rate}{'' if t == texts[sec] else ' (shortened)'}: {t}")
    html = re.sub(r'(<audio id="bgm"[^>]*data-volume=")[\d.]+(")', rf"\g<1>{bgm_volume}\2", html)
    html = html.replace('      <audio id="bgm"', "\n".join(clips) + '\n      <audio id="bgm"', 1)
    open(ip, "w", encoding="utf-8").write(html)
    open(os.path.join(out, "narration.txt"), "w", encoding="utf-8").write("\n".join(report) + "\n")
    return report


if __name__ == "__main__":
    a = sys.argv[1:]
    v = a[a.index("--voice") + 1] if "--voice" in a else VOICE
    for line in narrate(a[0], json.load(open(a[1], encoding="utf-8")), v):
        print(line)
