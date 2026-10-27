"""Prepare background music when assets/music is empty, through the HyperFrames media-use audio engine.

Usage:
  python -I tools/music.py --check                                   # which routes work on this PC (changes nothing)
  python -I tools/music.py --mode retrieve|generate [--count 4] [--force] [--allow-install]

  retrieve   HeyGen music library, searched by mood (HeyGen sign-in or HEYGEN_API_KEY; uses credits)
  generate   Google Lyria when GEMINI_API_KEY / GOOGLE_API_KEY is set, else local MusicGen
             (first run pip-installs transformers + torch and downloads ~300 MB; slow on CPU;
              MusicGen weights are CC-BY-NC 4.0, non-commercial)

Writes assets/music/m<N>-<mood>.mp3 (60.5 s, faded in and out, crossfade-looped when the source is shorter) and
assets/music/SOURCES.json (provider, mode, query/prompt, licence note). The builders rotate whatever mp3s are in
assets/music in production order, so a few tracks cover any number of videos. Refuses to run when assets/music already
holds mp3 files unless --force. Pick the route with the user first (media-use preflight): never generate silently.
"""
import json
import os
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUSIC = os.path.join(ROOT, "assets", "music")
LENGTH = 60.5  # every template is ≤ 60 s
NPX = "npx.cmd" if os.name == "nt" else "npx"
HF = "hyperframes@0.8.207"
MEDIA_USE = [os.environ.get("HYPERFRAMES_MEDIA_USE", ""), os.path.join(os.path.expanduser("~"), ".claude", "skills", "media-use")]

# instrumental beds for technology-transfer films: (slug, retrieval query, generation prompt)
MOODS = [
    ("bright-tech", "uplifting corporate technology",
     "uplifting corporate technology underscore, bright modern piano with soft synth pads, steady light percussion, instrumental, no vocals, 105 BPM"),
    ("green-field", "calm hopeful acoustic",
     "calm hopeful agricultural innovation, warm acoustic guitar and light strings, gentle pulse, instrumental, no vocals, 95 BPM"),
    ("clean-lab", "clean science ambient",
     "clean scientific discovery, airy pads and soft electronic pulses, subtle bell motifs, instrumental, no vocals, 100 BPM"),
    ("warm-craft", "warm optimistic light",
     "warm optimistic craftsmanship, marimba and piano with light percussion, cheerful but restrained, instrumental, no vocals, 110 BPM"),
]
LICENCE = {
    "heygen": "HeyGen music library — check HeyGen's terms for your use",
    "lyria": "Google Lyria via the Gemini API — check Google's generative AI terms",
    "musicgen": "facebook/musicgen-small (CC-BY-NC 4.0) — non-commercial use only",
}


def media_use_dir():
    for d in MEDIA_USE:
        if d and os.path.exists(os.path.join(d, "audio", "scripts", "audio.mjs")):
            return d
    raise SystemExit("media-use skill not found (install the HyperFrames plugin, or set HYPERFRAMES_MEDIA_USE)")


def check():
    """Report the routes; read-only."""
    import importlib.util
    print("media-use:", media_use_dir())
    r = subprocess.run([NPX, HF, "auth", "status"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    for line in (r.stdout + r.stderr).splitlines():
        if "music" in line.lower() or "heygen" in line.lower() or "signed" in line.lower():
            print("  ", line.strip())
    gem = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
    mg = all(importlib.util.find_spec(m) is not None for m in ("torch", "transformers", "soundfile"))
    print("retrieve (HeyGen):", "ready" if os.environ.get("HEYGEN_API_KEY") or os.path.isdir(os.path.expanduser("~/.heygen")) else "needs `heygen auth login --oauth` or HEYGEN_API_KEY")
    print("generate (Lyria):", "ready" if gem else "needs GEMINI_API_KEY or GOOGLE_API_KEY")
    print("generate (MusicGen):", "ready" if mg else "installs transformers+torch on first run (~2 GB with model), CC-BY-NC")
    have = [f for f in os.listdir(MUSIC) if f.lower().endswith(".mp3")] if os.path.isdir(MUSIC) else []
    print("assets/music:", f"{len(have)} mp3 present" if have else "empty")


def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def to_bed(src, dst, length=LENGTH, xfade=3.0):
    """Crossfade-loop src until it covers length, then trim with a fade in/out; write mp3."""
    d = duration(src)
    if d <= xfade + 1:
        raise RuntimeError(f"track too short ({d:.1f}s)")
    k = 1 if d >= length else int((length - d) // (d - xfade)) + 2
    ins = []
    for _ in range(k):
        ins += ["-i", src]
    chain, last = [], "[0:a]"
    for i in range(1, k):
        out = f"[x{i}]"
        chain.append(f"{last}[{i}:a]acrossfade=d={xfade}:c1=tri:c2=tri{out}")
        last = out
    chain.append(f"{last}atrim=0:{length},afade=t=in:d=1.2,afade=t=out:st={length - 3:.2f}:d=3,loudnorm=I=-16:TP=-1.5[o]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", ";".join(chain), "-map", "[o]", "-ac", "2", "-ar", "44100", "-b:a", "192k", dst], check=True)


def one(mu, mode, slug, query, prompt):
    """Run the engine for one bed in its own scratch folder; return (source path, provider)."""
    work = tempfile.mkdtemp(prefix="bgm-")
    req = {"provider": "auto", "lines": [], "bgm": {"mode": mode, "query": query, "prompt": prompt}}
    json.dump(req, open(os.path.join(work, "audio_request.json"), "w", encoding="utf-8"), ensure_ascii=False)
    scripts = os.path.join(mu, "audio", "scripts")
    meta = os.path.join(work, "audio_meta.json")
    r = subprocess.run(["node", os.path.join(scripts, "audio.mjs"), "--request", os.path.join(work, "audio_request.json"),
                        "--hyperframes", work, "--out", meta, "--only", "bgm"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
    if not os.path.exists(meta):
        raise RuntimeError("engine failed: " + (r.stderr or r.stdout)[-400:])
    m = json.load(open(meta, encoding="utf-8"))
    if m.get("bgm_pending"):
        subprocess.run(["node", os.path.join(scripts, "wait-bgm.mjs"), "--audio-meta", meta, "--hyperframes", work, "--timeout-ms", "1800000"],
                       capture_output=True, text=True, timeout=1900)
        st = os.path.join(work, "bgm_status.json")
        status = json.load(open(st, encoding="utf-8")).get("status") if os.path.exists(st) else "unknown"
        if status != "ready":
            raise RuntimeError(f"generation {status}; log: {m.get('bgm_log')}")
    if not m.get("bgm"):
        why = [ln.strip() for ln in ((r.stderr or "") + "\n" + (r.stdout or "")).splitlines() if "bgm" in ln.lower()]
        raise RuntimeError("no track: " + ("; ".join(why)[-300:] or "see the engine output"))
    return os.path.join(work, m["bgm"]["path"]), (m.get("bgm_provider") or ("heygen" if mode == "retrieve" else "musicgen"))


def main(args):
    sys.stdout.reconfigure(errors="replace")  # engine/CLI text can hold characters a legacy console code page lacks
    if "--check" in args:
        return check()
    if "--mode" not in args:
        raise SystemExit(__doc__)
    mode = args[args.index("--mode") + 1]
    if mode not in ("retrieve", "generate"):
        raise SystemExit("--mode retrieve|generate")
    count = int(args[args.index("--count") + 1]) if "--count" in args else 4
    os.makedirs(MUSIC, exist_ok=True)
    if any(f.lower().endswith(".mp3") for f in os.listdir(MUSIC)) and "--force" not in args:
        raise SystemExit("assets/music already has mp3 files - nothing to do (use --force to add more)")
    mu = media_use_dir()
    import importlib.util
    heygen = bool(os.environ.get("HEYGEN_API_KEY")) or os.path.isdir(os.path.expanduser("~/.heygen"))
    lyria = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
    musicgen = all(importlib.util.find_spec(m) is not None for m in ("torch", "transformers", "soundfile"))
    if mode == "retrieve" and not heygen:
        raise SystemExit("retrieve needs HeyGen: run `heygen auth login --oauth` (or set HEYGEN_API_KEY), or use --mode generate")
    if mode == "generate" and not lyria and not musicgen and "--allow-install" not in args:
        raise SystemExit("generate has no ready backend: set GEMINI_API_KEY for Lyria, or pass --allow-install to let the engine "
                         "pip-install transformers+torch (~2 GB with the MusicGen model, CC-BY-NC non-commercial)")
    src_path = os.path.join(MUSIC, "SOURCES.json")
    sources = json.load(open(src_path, encoding="utf-8")) if os.path.exists(src_path) else []
    start = len([f for f in os.listdir(MUSIC) if f.lower().endswith(".mp3")])
    made = 0
    for i, (slug, query, prompt) in enumerate(MOODS[:count]):
        name = f"m{start + i + 1}-{slug}.mp3"
        t = time.time()
        try:
            src, provider = one(mu, mode, slug, query, prompt)
            to_bed(src, os.path.join(MUSIC, name))
        except Exception as e:  # keep going: a missing bed only means fewer tracks in the rotation
            print(name, "FAILED:", e, flush=True)
            continue
        made += 1
        sources.append({"file": name, "provider": provider, "mode": mode, "query": query, "prompt": prompt if mode == "generate" else None,
                        "seconds": LENGTH, "licence": LICENCE.get(provider, "check the provider's terms"), "made": time.strftime("%Y-%m-%d")})
        json.dump(sources, open(src_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(name, f"ok ({provider}, {time.time() - t:.0f}s)", flush=True)
    print(f"{made}/{count} tracks in assets/music" + ("" if made else " - videos will build without music"))


if __name__ == "__main__":
    main(sys.argv[1:])
