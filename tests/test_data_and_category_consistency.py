import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
PAYLOAD = json.loads(
    (ROOT / "data" / "exhibitions.enriched.json").read_text(encoding="utf-8")
)


class DataAndCategoryConsistencyTests(unittest.TestCase):
    def test_home_does_not_limit_categories_to_twelve(self):
        self.assertNotIn(".slice(0, 12)", APP)
        self.assertGreaterEqual(
            APP.count("const categories = CATEGORY_ORDER;"),
            2,
        )

    def test_home_uses_outline_category_icons(self):
        self.assertIn(
            ".category-chip .category-icon svg",
            CSS,
        )
        self.assertIn("fill: none", CSS)
        self.assertIn("stroke: currentColor", CSS)

    def test_reurl_service_images_are_rejected(self):
        self.assertIn("reurl\\.cc", APP)

    def test_candidate_data_has_no_reurl_images(self):
        offenders = [
            {
                "id": event.get("id"),
                "url": url,
            }
            for event in PAYLOAD["events"]
            for url in [
                event.get("image"),
                *(event.get("images") or []),
            ]
            if url and "reurl.cc" in url.lower()
        ]
        self.assertEqual(offenders, [])

    def test_existing_layout_contract_is_preserved(self):
        self.assertNotIn("content-type-badge", APP)
        self.assertNotIn("巡迴場館", APP)
        self.assertIn("detailMeta('地點'", APP)


if __name__ == "__main__":
    unittest.main()
