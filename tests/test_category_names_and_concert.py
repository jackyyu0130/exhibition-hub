import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
PAYLOAD = json.loads(
    (ROOT / "data" / "exhibitions.enriched.json").read_text(encoding="utf-8")
)


class CategoryNamingAndConcertTests(unittest.TestCase):
    def test_category_labels_are_shortened(self):
        self.assertIn("'音樂','自然','歷史','表演'", APP)
        self.assertIn("'電影','親子','競賽','科技'", APP)
        self.assertNotIn("'歷史文化': iconSvg", APP)
        self.assertNotIn("'自然科學': iconSvg", APP)

    def test_legacy_category_names_are_aliased(self):
        self.assertIn("'歷史文化':'歷史'", APP)
        self.assertIn("'自然科學':'自然'", APP)

    def test_concert_is_independent_category(self):
        self.assertIn("'演唱會','快閃店','動漫'", APP)
        self.assertIn("concert:'演唱會'", APP)
        self.assertIn("'演唱會': iconSvg", APP)

    def test_concert_records_do_not_count_as_music(self):
        concerts = [
            event for event in PAYLOAD["events"]
            if event.get("contentType") == "concert"
        ]
        self.assertGreater(len(concerts), 0)
        for event in concerts:
            with self.subTest(title=event.get("title")):
                self.assertEqual(event["categories"][0], "演唱會")
                self.assertNotIn("音樂", event["categories"])

    def test_shortened_labels_are_written_to_candidate_data(self):
        labels = {
            category
            for event in PAYLOAD["events"]
            for category in event.get("categories", [])
        }
        self.assertNotIn("歷史文化", labels)
        self.assertNotIn("自然科學", labels)


if __name__ == "__main__":
    unittest.main()
