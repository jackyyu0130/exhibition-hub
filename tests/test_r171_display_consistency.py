from __future__ import annotations

from collections import Counter
import json
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from exhibition_hub.curation import public_categories


APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
CURATED = json.loads((ROOT / "data" / "exhibitions.curated.json").read_text(encoding="utf-8"))
AUDIT = json.loads(
    (ROOT / "data" / "update-reports" / "category-semantic-audit-r18.json")
    .read_text(encoding="utf-8")
)
CATEGORY_ORDER = [
    "演唱會", "快閃店", "動漫", "美術", "設計", "攝影", "市集", "音樂",
    "自然", "歷史", "表演", "舞蹈", "電影", "親子", "競賽", "科技", "其他",
]


class R171DisplayConsistencyTests(unittest.TestCase):
    def test_every_detail_category_is_selectable_and_finds_the_same_event(self) -> None:
        membership = Counter()
        for event in CURATED["events"]:
            categories = []
            for category in [event.get("category"), *(event.get("categories") or [])]:
                if category in CATEGORY_ORDER and category not in categories:
                    categories.append(category)
            self.assertTrue(categories, event["title"])
            self.assertEqual(categories, event["categories"], event["title"])
            self.assertEqual(event["category"], categories[0], event["title"])
            for category in categories:
                self.assertIn(category, CATEGORY_ORDER)
                membership[category] += 1

        self.assertEqual(dict(membership), {
            category: count
            for category, count in AUDIT["afterMembershipCounts"].items()
            if count
        })

    def test_every_event_still_matches_the_semantic_classifier(self) -> None:
        for event in CURATED["events"]:
            self.assertEqual(event["categories"], public_categories(event), event["title"])

    def test_anime_detail_labels_and_listing_have_the_same_events(self) -> None:
        anime = [event["title"] for event in CURATED["events"] if "動漫" in event["categories"]]
        self.assertEqual(len(anime), AUDIT["animeMembershipCount"])
        self.assertGreaterEqual(len(anime), 20)
        self.assertTrue(any("吉伊卡哇 人魚島的秘密" in title for title in anime))

    def test_all_public_price_surfaces_use_the_compact_label(self) -> None:
        self.assertIn("compactPriceLabel(event.price)", APP)
        self.assertIn("detailMeta('票價', compactPriceLabel(event.price))", APP)
        self.assertNotIn("detailMeta('票價', event.price)", APP)
        visual_price_uses = re.findall(
            r"(?:card-price|detailMeta\('票價')[^\n]*event\.price",
            APP,
        )
        self.assertEqual(len(visual_price_uses), 2)
        self.assertNotIn('title="${escapeHtml(event.price)}"', APP)

    def test_r18_cache_key_forces_the_fixed_runtime(self) -> None:
        self.assertIn('assets/styles.css?v=6.5.0-r18', HTML)
        self.assertIn('assets/app.js?v=6.5.0-r18', HTML)


if __name__ == "__main__":
    unittest.main()
