import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from build_enriched_candidate import (  # noqa: E402
    build_candidate_payload,
    recompute_stats,
)

from scripts.build_enriched_candidate import normalize_category_labels


class CategoryNormalizationTests(unittest.TestCase):
    def test_category_labels_are_normalized_for_production(self):
        event = normalize_category_labels({
            "categories": [
                "自然科學",
                "歷史文化",
                "快閃",
            ],
            "category": "自然科學",
            "contentType": "popup",
        })
        self.assertEqual(
            event["categories"],
            ["自然", "歷史", "快閃店"],
        )
        self.assertEqual(
            event["category"],
            "自然",
        )

    def test_concert_is_independent_from_music(self):
        event = normalize_category_labels({
            "categories": ["音樂", "表演"],
            "category": "音樂",
            "contentType": "concert",
        })
        self.assertEqual(
            event["categories"],
            ["演唱會", "表演"],
        )
        self.assertEqual(
            event["category"],
            "演唱會",
        )


class EnrichedCandidateBuilderTests(unittest.TestCase):
    def test_recompute_stats(self):
        events = [
            {
                "image": "a.jpg",
                "images": ["a.jpg", "b.jpg"],
                "latitude": 25.0,
                "longitude": 121.0,
                "categories": ["美術", "設計"],
            },
            {
                "image": "",
                "images": [],
                "latitude": None,
                "longitude": None,
                "category": "音樂",
            },
        ]

        stats = recompute_stats(events)

        self.assertEqual(stats["eventCount"], 2)
        self.assertEqual(stats["imageCount"], 1)
        self.assertEqual(stats["multiImageCount"], 1)
        self.assertEqual(stats["coordinateCount"], 1)
        self.assertEqual(stats["imageCoverage"], 0.5)
        self.assertEqual(stats["coordinateCoverage"], 0.5)
        self.assertEqual(
            stats["categoryCounts"],
            {
                "美術": 1,
                "設計": 1,
                "音樂": 1,
            },
        )

    def test_build_candidate_policy(self):
        source = {
            "updatedAt": "2026-07-27T19:01:56+08:00",
            "source": "test",
            "events": [
                {
                    "id": "candidate",
                    "title": "一般展覽",
                    "region": "台北市",
                    "locationName": "未知場館",
                    "categories": ["美術"],
                },
                {
                    "id": "needs-review",
                    "title": "線上攝影展",
                    "region": "新北市",
                    "locationName": "線上攝影展",
                    "categories": ["攝影"],
                },
                {
                    "id": "excluded",
                    "title": "2026春季社教成人班",
                    "region": "台南市",
                    "locationName": "場館資料整理中",
                    "categories": ["其他"],
                },
            ],
            "venueImages": {},
        }
        venue_registry = {
            "venues": [],
        }

        candidate, excluded, report = (
            build_candidate_payload(
                source,
                venue_registry,
                None,
            )
        )

        included_ids = {
            event["id"]
            for event in candidate["events"]
        }
        excluded_ids = {
            event["id"]
            for event in excluded["events"]
        }

        self.assertIn("candidate", included_ids)
        self.assertIn("needs-review", included_ids)
        self.assertIn("excluded", excluded_ids)
        self.assertNotIn("excluded", included_ids)
        self.assertFalse(
            candidate["registryBuild"]["published"]
        )
        self.assertEqual(
            candidate["stats"]["eventCount"],
            2,
        )
        self.assertEqual(
            report["excludedEventCount"],
            1,
        )


if __name__ == "__main__":
    unittest.main()
