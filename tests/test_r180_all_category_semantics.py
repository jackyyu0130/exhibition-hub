from __future__ import annotations

from collections import Counter
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from exhibition_hub.curation import public_categories


CATEGORY_ORDER = [
    "演唱會", "快閃店", "動漫", "美術", "設計", "攝影", "市集", "音樂",
    "自然", "歷史", "表演", "舞蹈", "電影", "親子", "競賽", "科技", "其他",
]
CURATED = json.loads((ROOT / "data" / "exhibitions.curated.json").read_text(encoding="utf-8"))
AUDIT = json.loads(
    (ROOT / "data" / "update-reports" / "category-semantic-audit-r18.json")
    .read_text(encoding="utf-8")
)
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")


class R180AllCategorySemanticTests(unittest.TestCase):
    def setUp(self) -> None:
        self.by_title = {event["title"]: event for event in CURATED["events"]}

    def assert_categories(self, title: str, expected: list[str]) -> None:
        self.assertIn(title, self.by_title)
        event = self.by_title[title]
        self.assertEqual(event["categories"], expected, title)
        self.assertEqual(event["category"], expected[0], title)

    def test_representative_corrections_cover_every_semantic_family(self) -> None:
        expected = {
            "Silver Screen Memories電影時代—非非藝術團隊演唱會": ["演唱會"],
            "IKEA收納行動車": ["快閃店"],
            "小梅的奇幻冒險：尋回心意之書": ["動漫"],
            "牧神的午後 | L'Après-midi d’un faune": ["美術"],
            "臨時公共空間的臨時展覽": ["設計"],
            "浮生—《人間》中的報導攝影，1985–1989": ["攝影"],
            "2026 國際住棚節文化市集": ["市集"],
            "音樂的交會點~傳統八音，說出當代語言": ["音樂"],
            "科博館《奇幻自然》常設展": ["自然"],
            "轉機：臺灣女子移動紀事特展": ["歷史"],
            "職男人生4-笑の祭典": ["表演"],
            "216": ["舞蹈"],
            "2027風動室內樂團《無限》電影配樂音樂會": ["音樂"],
            "《Spotlight ─ 波蘭兒童插畫的狂歡舞台》": ["美術", "親子"],
            "2026北流金舞台 歌唱大賽": ["音樂", "競賽"],
            "星球樂園PLANET PARK-全境式互動樂園": ["科技"],
        }
        for title, categories in expected.items():
            with self.subTest(title=title):
                self.assert_categories(title, categories)

    def test_anime_is_complete_across_exhibitions_music_films_and_popups(self) -> None:
        expected_anime_titles = [
            "CHIIKAWA DAYS 台北特展",
            "2026風動室內樂團《無限》宮崎駿動畫音樂精選",
            "8月高雄市電影館｜劇場版 吉伊卡哇 人魚島的秘密（中配版）",
            "2026貓貓蟲咖波 咖波小浪漫快閃店臺北站",
        ]
        for title in expected_anime_titles:
            self.assertIn("動漫", self.by_title[title]["categories"], title)
        self.assertEqual(
            sum("動漫" in event["categories"] for event in CURATED["events"]),
            AUDIT["animeMembershipCount"],
        )

    def test_all_17_categories_were_audited_and_the_feed_is_idempotent(self) -> None:
        self.assertEqual(AUDIT["categoriesReviewed"], CATEGORY_ORDER)
        self.assertEqual(AUDIT["categoryReviewCount"], 17)
        self.assertEqual(AUDIT["primaryCategoryMismatches"], 0)
        self.assertEqual(AUDIT["unsupportedCategoryLabels"], 0)
        self.assertEqual(AUDIT["semanticReclassificationMismatches"], 0)
        self.assertEqual(AUDIT["mutuallyExclusiveFormatConflicts"], 0)
        for event in CURATED["events"]:
            self.assertEqual(event["categories"], public_categories(event), event["title"])

    def test_non_catalog_talks_tours_and_classes_are_removed(self) -> None:
        titles = set(self.by_title)
        for fragment in ["苗北講堂", "藝術家對談", "節目導覽", "Live Podcast", "保證金繳交"]:
            self.assertFalse(any(fragment in title for title in titles), fragment)
        self.assertEqual(AUDIT["nonCatalogActivityRemovals"], 18)

    def test_membership_counts_match_every_category_page(self) -> None:
        membership = Counter(
            category
            for event in CURATED["events"]
            for category in event["categories"]
        )
        expected = {category: membership.get(category, 0) for category in CATEGORY_ORDER}
        self.assertEqual(expected, AUDIT["afterMembershipCounts"])
        self.assertEqual(expected, CURATED["stats"]["categoryCounts"])

    def test_frontend_trusts_the_audited_categories_for_curated_data(self) -> None:
        self.assertIn("trustCanonicalCategories", APP)
        self.assertIn("normalizeEvent(event, index, {trustCanonicalCategories:curated})", APP)
        self.assertIn("trustCanonicalCategories && canonicalCategories.length", APP)


if __name__ == "__main__":
    unittest.main()
