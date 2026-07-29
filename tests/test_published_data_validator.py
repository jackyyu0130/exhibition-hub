import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_published_data import evaluate  # noqa: E402


def build_payload(event_count=3, published=True):
    events = []
    for index in range(event_count):
        events.append({
            "id": f"event-{index}",
            "title": f"活動 {index}",
            "startDate": "2026-07-01",
            "endDate": "2026-07-31",
            "image": (
                "https://example.com/a.jpg"
                if index == 0
                else ""
            ),
            "images": (
                [
                    "https://example.com/a.jpg",
                    "https://example.com/b.jpg",
                ]
                if index == 0
                else []
            ),
            "categories": ["美術"],
            "editorialStatus": "candidate",
            "latitude": 25.0 if index == 0 else None,
            "longitude": 121.5 if index == 0 else None,
            "sourceRecords": (
                [{
                    "sourceId": "huashan-1914",
                    "sourceEventId": f"source-{index}",
                }]
                if index == 0
                else []
            ),
        })
    return {
        "updatedAt": "2026-07-28T00:00:00Z",
        "events": events,
        "stats": {
            "eventCount": event_count,
            "imageCount": 1,
            "multiImageCount": 1,
            "coordinateCount": 1,
            "imageCoverage": round(1 / event_count, 4),
            "coordinateCoverage": round(1 / event_count, 4),
            "categoryCounts": {
                "美術": event_count,
            },
        },
        "officialSourceBuild": {
            "published": published,
            "sourceId": "huashan-1914",
        },
    }


class PublishedDataValidatorTests(unittest.TestCase):
    def test_dynamic_event_count_passes(self):
        payload = build_payload(event_count=7)
        result = evaluate(
            payload,
            minimum_events=5,
            require_published=True,
            source_id="huashan-1914",
        )
        self.assertTrue(result["passed"])
        self.assertEqual(result["eventCount"], 7)

    def test_count_change_does_not_require_fixture_update(self):
        for count in (5, 19, 125):
            with self.subTest(count=count):
                payload = build_payload(
                    event_count=count,
                )
                result = evaluate(
                    payload,
                    minimum_events=5,
                    require_published=False,
                    source_id="",
                )
                self.assertTrue(result["passed"])

    def test_legacy_non_published_stats_allow_one_count_drift(self):
        payload = build_payload()
        payload["stats"]["imageCount"] += 1
        payload["stats"]["multiImageCount"] += 1
        payload["stats"]["categoryCounts"]["競賽"] = 0

        result = evaluate(
            payload,
            minimum_events=1,
            require_published=False,
            source_id="",
        )
        self.assertTrue(result["passed"])

        strict = evaluate(
            payload,
            minimum_events=1,
            require_published=True,
            source_id="huashan-1914",
        )
        self.assertFalse(strict["passed"])

    def test_duplicate_id_is_rejected(self):
        payload = build_payload()
        payload["events"][1]["id"] = "event-0"
        result = evaluate(
            payload,
            minimum_events=1,
            require_published=False,
            source_id="",
        )
        self.assertFalse(result["passed"])
        self.assertIn(
            "eventIdsUnique",
            result["failedGateIds"],
        )

    def test_stats_mismatch_is_rejected(self):
        payload = build_payload()
        payload["stats"]["eventCount"] = 99
        result = evaluate(
            payload,
            minimum_events=1,
            require_published=False,
            source_id="",
        )
        self.assertFalse(result["passed"])
        self.assertIn(
            "statsEventCountMatches",
            result["failedGateIds"],
        )

    def test_unpublished_data_is_rejected_when_required(self):
        payload = build_payload(published=False)
        result = evaluate(
            payload,
            minimum_events=1,
            require_published=True,
            source_id="huashan-1914",
        )
        self.assertFalse(result["passed"])
        self.assertIn(
            "officialSourceBuildPublished",
            result["failedGateIds"],
        )

    def test_generic_image_and_facebook_reference_are_rejected(self):
        payload = build_payload()
        payload["events"][0]["image"] = (
            "https://www.opentix.life/_nuxt/img/flags.9c96e0ed.png"
        )
        payload["events"][0]["images"] = [payload["events"][0]["image"]]
        payload["events"][0]["sourceUrls"] = [
            "https://www.facebook.com/groups/example"
        ]
        payload["stats"]["multiImageCount"] = 0
        result = evaluate(
            payload,
            minimum_events=1,
            require_published=False,
            source_id="",
        )
        self.assertFalse(result["passed"])
        self.assertIn("suspiciousImagesAbsent", result["failedGateIds"])
        self.assertIn("facebookReferencesAbsent", result["failedGateIds"])


if __name__ == "__main__":
    unittest.main()
