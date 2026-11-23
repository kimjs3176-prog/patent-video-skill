# Third-party notices

## Fonts (SIL Open Font License 1.1 — full texts in `assets/fonts/licenses/`)

| Font | Files | Source |
|---|---|---|
| Pretendard | `assets/fonts/pretendard/*.woff2` | https://github.com/orioncactus/pretendard |
| Noto Sans KR (variable) | `assets/fonts/NotoSansKR-VF.ttf` | https://github.com/google/fonts/tree/main/ofl/notosanskr |
| Noto Serif KR (variable) | `assets/fonts_serif/NotoSerifKR-VF.ttf` | https://github.com/google/fonts/tree/main/ofl/notoserifkr |
| Archivo, Manrope, IBM Plex Mono, Source Serif (Latin subsets) | `assets/fonts/ref/*.woff2` | via nexu-io/open-design (Apache-2.0) from Google Fonts |

At build time the pipeline subsets these fonts per video (`fontsub.py`); subsets remain under the OFL.

## Design references

Templates G, H and I adapt the visual language of HyperFrames registry examples (swiss-grid, pentagram-stat, takram-organic,
nyt-graph, data-chart-nyt) as distributed in nexu-io/open-design (Apache-2.0). No source files from those templates are included.
The particle text effect in `visuals.py` follows the technique of the HyperFrames registry component `particle-text-dissolve`.

## Pronunciation check (installed by requirements.txt, not redistributed)

| Component | Version | License | Use |
|---|---|---|---|
| faster-whisper (SYSTRAN) | 1.2.1 | MIT | speech recognition for `scripts/pronounce.py` |
| Whisper "small" model (OpenAI, CTranslate2 conversion by SYSTRAN) | faster-whisper-small | MIT | downloaded once to the Hugging Face cache on first use |

## Libraries loaded at render time (not redistributed)

| Library | Version | License | Use |
|---|---|---|---|
| GSAP | 3.15.1 | GreenSock standard license (no-charge) | scene timelines |

It is fetched from jsDelivr by the rendering browser; no copy is included in this repository.

## Not included

The videos carry no background music. Sound effects are not redistributed (see README). Patent data fetched from KIPRIS is not part of this
repository; the three example content files in `references/examples/` describe public Korean patents.
