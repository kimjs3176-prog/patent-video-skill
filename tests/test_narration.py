"""Golden table for the narration text rules: what the screen writes → what the narrator says.

Run from the repository root:  python -I -X utf8 -m unittest discover -s tests
No network and no TTS: only speak(), josa() and sentences() are exercised. When a rule changes on purpose, update the
expected line here in the same commit; any other difference is a regression.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

from narration import josa, sentences, speak, spoken  # noqa: E402

SPEAK = [
    # units and figures
    ("25℃", "25도."),
    ("1,000 rpm", "1,000 알피엠."),
    ("0.5 ㎛", "0.5 마이크로미터."),
    ("3 mL을 첨가", "3 밀리리터를 첨가."),
    ("10 m²의 면적", "10 제곱미터의 면적."),
    ("R² 값", "R 제곱 값."),
    ("5 mM 용액", "5 밀리몰 용액."),
    ("10⁻³ M", "10의 마이너스 3제곱 몰."),
    ("10 kGy 조사", "10 킬로그레이 조사."),
    ("5,000 lux", "5,000 럭스."),
    ("50 ppm", "50 피피엠."),
    ("12 °Brix", "12 브릭스."),
    ("5 m를", "5 미터를."),
    ("5 s 동안", "5 초 동안."),
    ("3 mol", "3 몰."),
    ("2 GPa", "2 기가파스칼."),
    ("100 mPa·s", "100 밀리파스칼초."),
    ("10 N·m", "10 뉴턴미터."),
    ("1 ha", "1 헥타르."),
    ("Ø 30 mm", "지름 30 밀리미터."),
    ("6.5±0.2", "6.5 플러스마이너스 0.2."),
    ("1,500×g로 원심분리", "1,500 지로 원심분리."),
    ("1x10⁸ CFU/g", "그램당 1 곱하기 10의 8제곱 CFU."),
    ("10⁸CFU", "10의 8제곱 CFU."),
    ("5×10⁶ cells/mL", "밀리리터당 5 곱하기 10의 6제곱 cells."),
    ("1.5 mg·kg⁻¹", "킬로그램당 1.5 밀리그램."),
    ("10 mm × 20 mm", "10 밀리미터 곱하기 20 밀리미터."),
    ("0.2~0.5 kg/m²", "제곱미터당 0.2에서 0.5 킬로그램."),
    ("1.0×10⁷ cells/well", "웰당 1.0 곱하기 10의 7제곱 cells."),
    ("EC 1.5 dS/m", "EC 1.5 데시지멘스 퍼 미터."),
    ("300 nm~400 nm", "300 나노미터에서 400 나노미터."),
    ("0.05% (w/v)", "0.05퍼센트, 중량 대 부피."),
    ("Brix 12° 이상", "브릭스 12도 이상."),
    ("약 50배입니다", "약 오십 배입니다."),
    ("1,000배", "천 배."),
    ("2배 증가", "2배 증가."),
    ("10배양", "10배양."),
    ("16L:8D 조건에서 배양", "명기 16시간, 암기 8시간 조건에서 배양."),
    # percentages
    ("5%p 증가", "5퍼센트포인트 증가."),
    ("0.1 wt%의", "0.1중량퍼센트의."),
    ("10~20 wt%", "10에서 20중량퍼센트."),
    ("2.5배↑", "2.5배 증가."),
    ("수율 30%↓", "수율 30퍼센트 감소."),
    # ranges
    ("50~90분", "50에서 90분."),
    ("60-80℃", "60에서 80도."),
    ("-40℃에서 보관", "영하 40도에서 보관."),
    ("-20~-5℃", "영하 20에서 영하 5도."),
    ("pH 6.5-7.0", "pH 6.5에서 7.0."),
    ("10-2019-0145266", "10-2019-0145266."),
    # rates
    ("3,250 kg/10a", "10아르당 3,250 킬로그램."),
    ("2-3 g/주", "주당 2에서 3 그램."),
    ("10~20 mg/L", "리터당 10에서 20 밀리그램."),
    ("1~3 mL/min", "분당 1에서 3 밀리리터."),
    ("300~500 kg/10a", "10아르당 300에서 500 킬로그램."),
    ("2.5 g/L을 첨가", "리터당 2.5 그램을 첨가."),
    ("3 mg/L로", "리터당 3 밀리그램으로."),
    ("5 m/s", "초당 5 미터."),
    ("2 h/day", "하루 2 시간."),
    ("12시간/일 조명", "하루 12시간 조명."),
    ("30 mg/kg/day 투여", "하루 체중 킬로그램당 30 밀리그램 투여."),
    ("1회/일 투여", "하루 1회 투여."),
    # ratios, fractions, comparisons, arrows
    ("1/3로 감소", "3분의 1로 감소."),
    ("1:2:3 비율로 혼합", "1 대 2 대 3 비율로 혼합."),
    ("1:10의 중량비로", "1 대 10의 중량비로."),
    ("10:30에 시작", "10:30에 시작."),
    ("수분 <5%, 순도 >99%", "수분 5퍼센트 미만, 순도 99퍼센트 초과."),
    ("온도 ≤ 40℃, 습도 ≥ 80%", "온도 40도 이하, 습도 80퍼센트 이상."),
    ("<5 mg/L로 유지", "리터당 5 밀리그램 미만으로 유지."),
    ("23.6→14.6으로 감소", "23.6에서 14.6으로 감소."),
    ("23.6%→14.6%로 감소", "23.6퍼센트에서 14.6퍼센트로 감소."),
    ("가열 → 냉각", "가열, 그다음 냉각."),
    ("팽화미 + 맥아", "팽화미와 맥아."),
    ("가열·가압", "가열, 가압."),
    # formulas
    ("CO₂를 흡수", "이산화탄소를 흡수."),
    ("이산화탄소(CO₂)를", "이산화탄소를."),
    ("H₂O₂ 처리", "과산화수소 처리."),
    # asides, companies, acronyms, abbreviations
    ("설향(딸기)은 맛있다", "설향은 맛있다."),
    ("세포(45%)에 넣는다", "세포에, 45퍼센트, 넣는다."),
    ("(주)에이비씨에서 개발한 기술입니다", "주식회사 에이비씨에서 개발한 기술입니다."),
    ("한국(주)에서 개발한", "한국 주식회사에서 개발한."),
    ("(KIST)가 개발한 기술입니다", "KIST가 개발한 기술입니다."),
    ("PCR으로 증폭", "PCR로 증폭."),
    ("DNA이 포함", "DNA가 포함."),
    ("결과는 ca. 5배 높다", "결과는 약 5배 높다."),
    ("Fig. 3의 장치", "도 3의 장치."),
    # markup and end marks
    ("A &amp; B", "A & B."),
    ("줄바꿈<br />테스트", "줄바꿈 테스트."),
    ("흡입한다..", "흡입한다."),
    ("어렵다?.", "어렵다?"),
    ("잠시...", "잠시..."),
]

JOSA = [
    (("PCR", "으로로"), "PCR로"), (("DNA", "을를"), "DNA를"), (("HPLC", "으로로"), "HPLC로"), (("pH", "이가"), "pH가"),
    (("sensor", "이가"), "sensor가"), (("polymer", "을를"), "polymer를"), (("film", "을를"), "film을"),
    (("coating", "이가"), "coating이"), (("3", "은는"), "3은"), (("2", "을를"), "2를"), (("팽화미", "과와"), "팽화미와"),
    (("10 m²", "이가"), "10 m²가"), (("10⁸", "이가"), "10⁸이"),
]

SENTENCES = [
    ("도 3에 나타낸 바와 같이 Fig. 3의 장치는 수분을 응축한다. 그리고 물을 공급한다.",
     ["도 3에 나타낸 바와 같이 Fig. 3의 장치는 수분을 응축한다.", "그리고 물을 공급한다."]),
    ("시료 1. 혼합 단계 2. 가열 단계를 거친다. 끝.", ["시료 1. 혼합 단계 2. 가열 단계를 거친다.", "끝."]),
    ("결과는 ca. 5배 높다. 다음.", ["결과는 ca. 5배 높다.", "다음."]),
    ("농도는 2024. 다음 문장.", ["농도는 2024.", "다음 문장."]),
]


class Music(unittest.TestCase):
    def test_pick_is_fixed_per_patent_and_spread(self):
        from music import pick
        names = ["m1.mp3", "m2.mp3", "m3.mp3", "m4.mp3"]
        self.assertEqual(pick("1020190145266", names), pick("1020190145266", names))
        got = {pick(f"10202000{i:05d}", names) for i in range(40)}
        self.assertEqual(got, set(names))
        self.assertIsNone(pick("1020190145266", []))


class Pronounce(unittest.TestCase):
    def test_numbers_said_either_way(self):
        from pronounce import _numbers
        for said, digits in (("다섯 단계입니다", "5단계입니다"), ("약 오십 배입니다", "약 50배입니다"), ("만이천 개", "12000개")):
            self.assertEqual(_numbers(said), _numbers(digits))


class Narration(unittest.TestCase):
    def test_speak(self):
        for src, want in SPEAK:
            with self.subTest(src=src):
                self.assertEqual(speak(src), want)

    def test_speak_leaves_spoken_lines_alone(self):
        for line in ("팽화미로 만든 쌀맥주입니다.", "액화 공정 없이 완성하는 쌀맥주."):
            self.assertEqual(speak(line), line)

    def test_josa(self):
        for (word, pair), want in JOSA:
            with self.subTest(word=word):
                self.assertEqual(josa(word, pair), want)

    def test_sentences(self):
        for src, want in SENTENCES:
            with self.subTest(src=src):
                self.assertEqual(sentences(src), want)

    def test_full_line_is_not_marked_shortened(self):  # a stray '…' between sentences is not a cut
        self.assertEqual(spoken("좋다! … 정말 좋다."), "좋다! 정말 좋다.")


if __name__ == "__main__":
    unittest.main()
