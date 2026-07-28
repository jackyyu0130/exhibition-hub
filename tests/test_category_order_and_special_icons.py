import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
PAYLOAD = json.loads(
    (ROOT / "data" / "exhibitions.enriched.json").read_text(
        encoding="utf-8"
    )
)

EXPECTED_ORDER = [
    "演唱會",
    "快閃店",
    "動漫",
    "美術",
    "設計",
    "攝影",
    "市集",
    "音樂",
    "自然",
    "歷史",
    "表演",
    "舞蹈",
    "電影",
    "親子",
    "競賽",
    "科技",
    "其他",
]


class CategoryOrderAndSpecialIconTests(unittest.TestCase):
    def test_exact_shared_category_order(self):
        expected_js = ",".join(
            f"'{item}'" for item in EXPECTED_ORDER
        )
        self.assertIn(
            f"const CATEGORY_ORDER = [{expected_js}];",
            APP,
        )

    def test_home_and_listing_use_complete_shared_order(self):
        self.assertGreaterEqual(
            APP.count("const categories = CATEGORY_ORDER;"),
            2,
        )
        self.assertNotIn(
            "CATEGORY_ORDER.filter(category => counts[category])",
            APP,
        )
        self.assertNotIn(
            "CATEGORY_ORDER.filter("
            "category => categoryCounts[category])",
            APP,
        )

    def test_home_and_listing_use_six_column_desktop_layouts(self):
        self.assertIn(
            "grid-template-columns: repeat(6, minmax(0, 1fr))",
            CSS,
        )
        self.assertIn(
            "grid-template-columns: repeat(6, minmax(62px, 1fr))",
            CSS,
        )
        self.assertIn(
            "grid-column: auto !important",
            CSS,
        )

    def test_concert_has_independent_microphone_icon(self):
        self.assertIn("'演唱會': iconSvg", APP)
        self.assertIn(
            '<rect x="9" y="3" width="6" height="11" rx="3">',
            APP,
        )

    def test_popup_store_has_independent_outline_icon(self):
        self.assertIn("'快閃店': iconSvg", APP)
        self.assertIn("m18.2 2 .7 1.5", APP)
        self.assertIn("popup:'快閃店'", APP)

    def test_legacy_popup_names_are_aliased(self):
        self.assertIn("'快閃':'快閃店'", APP)
        self.assertIn("'快閃活動':'快閃店'", APP)

    def test_candidate_data_uses_popup_store_label(self):
        labels = {
            category
            for event in PAYLOAD["events"]
            for category in event.get("categories", [])
        }
        self.assertIn("快閃店", labels)
        self.assertNotIn("快閃", labels)

    def test_category_stats_match_dynamic_published_data(self):
        counts = PAYLOAD["stats"]["categoryCounts"]

        # The UI keeps a complete fixed category order, while dynamic
        # production data may legitimately contain zero events for one
        # or more categories. Stats only need to describe categories
        # that are actually present in the current catalogue.
        self.assertTrue(set(counts).issubset(set(EXPECTED_ORDER)))

        calculated = {
            category: sum(
                category in event.get("categories", [])
                for event in PAYLOAD["events"]
            )
            for category in counts
        }
        self.assertEqual(counts, calculated)


if __name__ == "__main__":
    unittest.main()
