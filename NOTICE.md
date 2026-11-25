# Third-party notices

## Fonts (SIL Open Font License 1.1 — full texts in `assets/fonts/licenses/`)

| Font | Files | Source |
|---|---|---|
| Pretendard | `assets/fonts/pretendard/*.woff2` | https://github.com/orioncactus/pretendard |
| Noto Sans KR (variable) | `assets/fonts/NotoSansKR-VF.ttf` | https://github.com/google/fonts/tree/main/ofl/notosanskr |
| Noto Serif KR (variable) | `assets/fonts_serif/NotoSerifKR-VF.ttf` | https://github.com/google/fonts/tree/main/ofl/notoserifkr |
| Archivo, Manrope, IBM Plex Mono, Source Serif (Latin subsets) | `assets/fonts/ref/*.woff2` | via nexu-io/open-design (Apache-2.0) from Google Fonts |

At build time the pipeline subsets these fonts per video (`fontsub.py`); subsets remain under the OFL.

## Icons (in this repository)

`scripts/icons.py` holds 40 outline icons from **Tabler Icons** 3.35.0 (https://github.com/tabler/tabler-icons, npm
`@tabler/icons@3.35.0`, integrity sha512-yYXe+gJ56xlZFiXwV9zVoe3FWCGuZ/D7/G4ZIlDtGxSx5CGQK110wrnT29gUj52kEZoxqF7oURTk97GQxELOFQ==),
path data unchanged, each icon's paths joined into one and given a soft fill under its closed shapes.

MIT License — Copyright (c) 2020-2025 Paweł Kuna. Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: The
above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Design references

Templates G, H and I adapt the visual language of HyperFrames registry examples (swiss-grid, pentagram-stat, takram-organic,
nyt-graph, data-chart-nyt) as distributed in nexu-io/open-design (Apache-2.0). No source files from those templates are included.
The particle text effect in `visuals.py` follows the technique of the HyperFrames registry component `particle-text-dissolve`.

## Background music (in this repository)

The four tracks in `assets/music/` were supplied by the repository owner and made with Suno (titles, ids and dates in
`assets/music/SOURCES.md`). Their use follows the terms of the Suno account that made them: commercial use requires a paid
Suno plan at the time of creation. Replace the files if that does not hold.

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
