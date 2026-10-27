# 특허 기술소개영상 콘텐츠 작성 규칙 (content JSON)

각 특허마다 `data/content/<order 3자리>-<appno>.json` 1개를 작성한다. 생성기(`tools/build.py`)가 이 JSON으로
60초 언팩(신제품 발표회) 스타일 영상을 만든다. 예시: `data/content/007-1020190166418.json`(장치형, anatomy),
`137-1020190145266.json`(공정+수치형, stats), `146-1020210079188.json`(바이오 소재형, stats).
**작성 전에 예시 3개를 반드시 읽는다.**

## 입력
- `data/master.json`: order, appno, title, status
- `data/patents/<appno>/biblio.json`: 서지·요약·청구항(등록 청구항 = 권리범위, 가장 신뢰), rnd(과제정보)
- `data/patents/<appno>/fulltext.txt`: 공보 전문(발명의 효과·실시예·표). 공개공보일 수 있으니 청구항은 biblio.json 우선
- `data/patents/<appno>/fig-*.jpg / fig-*.png`: 도면 이미지(png = 흑백 기계도면, 부호 확인에 적합) (anatomy용, 필요할 때만 Read로 확인)

## 절대 규칙 (사실성)
1. 모든 수치·조건·효과는 명세서/청구항에 적힌 그대로. 계산해서 새 주장을 만들지 않는다(예: 23.6→14.6을 "38% 감소"로 쓰지 않음, "N배"는 명세서에 그 표현이 있을 때만).
2. 명세서에 없는 효과·시장·매출·인증은 쓰지 않는다. 활용분야(apps)는 청구항·발명의 효과·명세서에 언급된 용도 위주, 필요시 그 용도의 자연스러운 적용처까지만.
3. 청구항에 직접 포함된 용도는 apps 항목에 `"claim": true` (최대 3개).
4. 수치 데이터가 없는 특허(장치·시스템 등)는 proof.kind = "anatomy"로 하고, 구성요소 번호가 보이는 도면(사시도 등)을 figure로 지정. 부품 순서를 도면 부호 순서와 맞추고 source에 "(부호는 도면 번호와 동일)"을 적되, 실제로 일치할 때만.
5. 수치 데이터가 있으면 proof.kind = "stats", items 1~3개. 대조군 대비 막대(bars)는 표에 있는 값만. 그래프만 있고 수치가 본문에 없으면 그 막대는 넣지 않는다.
6. 명세서 내부 모순(단위 오기 등)이 있으면 더 타당한 쪽을 쓰고 `"notes"` 필드에 한 줄 기록.

## 문체
- 한국어 개조식. 문장형 종결("~합니다") 금지. 짧게.
- 글자 수 한도(넘으면 화면에서 잘림):
  - name: 영문 대문자 코드네임 2단어, 공백 포함 14자 이내, 뒤 단어 앞에 `|`(그라디언트 구분). 예 `"DEW |POT"`, `"POP RICE |BREW"`
  - sub: 한글 20자 이내 (기술 한 줄 설명)
  - headline, process.title, features.title, proof.title: 22자 이내, 강조할 끝부분 앞에 `|`
  - chips[].k 12자, chips[].v+u 10자(한글은 8자) 이내
  - process.steps[].n 9자, d 18자, big+u 8자(한글이면 4자) — big은 그 단계의 핵심 수치(조건) 또는 영문 동사 1단어(SENSE, COOL…)
  - process.note 40자 이내
  - proof.items[].big+u 8자, l 12자, s 2줄(`<br />`로 구분, 줄당 18자)
  - bars[].l 14자, bars[].t 8자
  - anatomy parts[].n 10자, d 22자 (최대 6개)
  - features.big.l 12자, big.s 14자; tiles[] 6개: v 7자(한글 5자), l 9자, s 13자
  - apps[] 5개: n 8자, s 2줄(`<br />`, 줄당 9자)
  - source 50자 이내: "자료: 등록특허 제10-XXXXXXX호 명세서 (표/도/실시예)"
- 등록특허면 `"patlabel": "등록특허"`, regno = 등록번호(10-XXXXXXX, 뒤 -0000 제거). 공개특허(미등록)면 `"patlabel": "공개특허"`, regno = 공개번호.
- institute: 전문의 "주관기관" 또는 "과제수행기관명"(또는 rnd)에 국립○○원이 있으면 "농촌진흥청 국립○○원", 없으면 "농촌진흥청".

## 디자인 필드
- palette: amber(식품·발효·곡물), green(작물·재배·친환경·토양), violet(바이오·기능성·화장품), aqua(장치·물·스마트팜·센서), rose(축산·반려동물·건강), blue(미생물·의약·분석·소프트웨어) 중 택1
- hero, apps[].icon, proof.items[].icon: 아래 이름 중에서만
  beer rice flask leaf sprout cell dna pot drop snow chip fan shield bowl globe capsule bottle factory cup chart thermo gear spark home hand coins pin fork animal tractor sun seed fish box water sensor mushroom bee

## 스키마
```json
{
  "order": 7, "appno": "1020190166418", "regno": "10-2387406", "patlabel": "등록특허",
  "title": "발명의 명칭 원문", "name": "DEW |POT", "sub": "...", "institute": "...",
  "palette": "aqua", "hero": "pot", "headline": "앞부분 |강조",
  "chips": [{"k": "", "v": "", "u": ""}, x4],
  "process": {"title": "", "steps": [{"n": "", "d": "", "big": "", "u": ""}, 3~6개], "note": ""},
  "proof": {"kind": "stats", "eyebrow": "PERFORMANCE",
            "items": [{"big": "", "u": "", "l": "", "s": "", "bars": [{"l": "", "v": 0, "t": "", "hi": true}], "max": 0, "icon": "shield"}]}
     또는 {"kind": "anatomy", "eyebrow": "ANATOMY", "title": "", "figure": "fig-p8-IM6.jpg", "figcap": "", "parts": [{"n": "", "d": "", "ref": "도면 부호(있을 때만, 예: 110)"}]},
  "source": "",
  "features": {"title": "", "big": {"l": "", "s": ""}, "tiles": [{"v": "", "l": "", "s": ""}, x6]},
  "apps": [{"icon": "", "n": "", "s": "줄1<br />줄2", "claim": true}, x5],
  "notes": "선택: 명세서 모순·판단 근거",
  "narration": {"hook": "", "overview": "", "process": "", "proof": "", "figures": "", "features": "", "apps": "", "outro": ""}
}
```
- bars: 하이라이트(이 기술) 항목에 `"hi": true`, max는 막대 최대값보다 약간 크게. bars가 없으면 item에 icon 지정.
- stats item은 각 4초 이상 보이므로 1~3개.

## 나레이션 대본 (narration, 선택 — `--narrate` 렌더링 때 사용)
화면 글자(개조식)를 그대로 읽지 말고, 같은 사실을 **말하는 문장**으로 쓴다. 장면마다 1~2문장.
- 음절 한도(공백 제외): hook 30 · overview 30 · process 45 · proof 50 · figures 25 · features 30 · apps 30 · outro 25.
  넘치면 템플릿별로 빨리 읽히거나 뒤 문장부터 잘리므로, **문장 하나만 남아도 말이 되게** 핵심을 앞 문장에 둔다.
- 수치는 명세서 그대로, 읽기 쉽게: `0.6–1.1 MPa` → "0.6에서 1.1 메가파스칼", `%` → "퍼센트", `℃` → "도". 계산한 배수 금지.
- figures: 실제 도면 종류를 확인했을 때만 구체적으로("공정도와 사진"), 아니면 "명세서 도면으로 구조를 살펴봅니다." 정도.
- outro: "기술이전 문의는 한국농업기술진흥원입니다."(고정 문구 유지, 기술이전 형태는 말하지 않는다). 면책 문구는 읽지 않는다(화면 표기).
- 기관명·코드네임은 화면에 있으므로 반복하지 않아도 된다. 과장·광고성 표현("획기적", "최고") 금지.
- 없으면 내용 필드로 단순 대본을 자동 생성한다(품질 낮음 → 대량 제작 때도 작성 권장).

## 시그니처 장면 (signature, 선택 — 템플릿 S)
기술 자체가 움직이는 장면. `type`에 따라 이야기 순서와 핵심 장면이 바뀐다. **모든 값은 명세서·청구항·도면에서 확인한 것만.**
도면 위 위치(x, y)는 그 도면 이미지의 가로·세로 비율(0~1)로, 도면을 직접 보고 부호가 가리키는 부품 위에 찍는다.

- `journey` (식품·공정): `conventional`(기존 공정 단계 이름들) · `removed`(빠지는 단계) · `removed_note` · `route_note` ·
  `stages[{key, n, cond, t:[최저,최고]℃ 또는 label}]` · `product` · `title`("쌀이 |쌀맥주가 되기까지" 형식).
  key(그림): puff(팽화) · mash(당화·혼합) · boil(가열) · ferment(발효) · cold(숙성·저온 → 마지막엔 완제품 잔).
- `loop` (장치): `figure` · `figcap` · `callouts[{ref, n, d, x, y}]` · `air_in`/`air_in2`/`heat_out`(도면 비율 좌표 경로) ·
  `drip`(응축·배출 지점) · `logic`(제어 루프 4단계) · `rules`(청구항의 제어 조건 2줄) ·
  `path_figure` · `path_figcap` · `path[{ref, n, d, x, y}]`(물·물질이 제품 안을 지나는 순서).
- `sequence` (프라이머·유전자): `problem[{v, l, s}]`(배경기술 수치 3개) · `target` · `primers[{id, seq, regions}]`(서열번호의 실제 염기) ·
  `layout`(표적 위 부위 순서) · `probe{seq, dye}` · `sybr_ntc`(프로브 없이 NTC의 Ct) · `sensitivity`/`specificity[{l, ct}]`
  (도면 Ct 표의 평균, 미검출은 null) · `cycles` · `cutoff` · `field`(현장 조건 3개).
- 모식도인 부분(부위 배치, 물방울 경로)은 화면에 "모식"이라고 표기된다. 곡선은 Ct 값에서 문턱선을 지나도록 그린다.

## 작성 후 자체 점검
- JSON 문법 유효(`python -I -c "import json;json.load(open(path,encoding='utf-8'))"`)
- 모든 수치를 명세서에서 다시 찾아 확인
- 글자 수 한도 확인
