import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from exhibition_hub.merging.quality import (  # noqa: E402
    evaluate_source_merge_candidate,
)


class SourceMergeQualityTests(unittest.TestCase):
    def setUp(self):
        self.base = {
            "events": [{
                "id": "base-1",
                "title": "既有活動",
            }]
        }
        self.source_run = {
            "sourceId": "huashan-1914",
            "success": True,
            "records": [
                {
                    "source_event_id": "source-a",
                    "raw": {
                        "detailFetched": True,
                        "imageUrl": "https://example.com/a.jpg",
                        "organizer": "主辦單位",
                        "venueName": "華山",
                        "sourceCategory": "園區活動",
                        "admission": "paid",
                        "description": "活動介紹",
                    },
                },
                {
                    "source_event_id": "source-b",
                    "raw": {
                        "detailFetched": True,
                        "imageUrl": "https://example.com/b.jpg",
                        "organizer": "主辦單位",
                        "venueName": "華山",
                        "sourceCategory": "園區活動",
                        "admission": "free",
                        "description": "活動介紹",
                    },
                },
            ],
            "metrics": {
                "detailRequestedCount": 2,
                "detailSuccessCount": 2,
                "detailFailureCount": 0,
            },
        }
        self.candidate = {
            "events": [
                {
                    "id": "base-1",
                    "sourceRecords": [{
                        "sourceId": "huashan-1914",
                        "sourceEventId": "source-a",
                    }],
                },
                {
                    "id": "new-1",
                    "sourceRecords": [{
                        "sourceId": "huashan-1914",
                        "sourceEventId": "source-b",
                    }],
                },
            ],
            "sourceMergeBuild": {
                "published": False,
            },
        }
        self.merge_report = {
            "published": False,
            "decisions": [
                {
                    "sourceEventId": "source-a",
                    "decision": "auto_merge",
                    "mergedIntoId": "base-1",
                },
                {
                    "sourceEventId": "source-b",
                    "decision": "new_event",
                    "newEventId": "new-1",
                },
            ],
        }

    def evaluate(self, **changes):
        values = {
            "base_payload": self.base,
            "source_run": self.source_run,
            "candidate": self.candidate,
            "merge_report": self.merge_report,
            "review_queue": [],
            "source_id": "huashan-1914",
            "require_full_details": True,
            "max_review": 0,
        }
        values.update(changes)
        return evaluate_source_merge_candidate(**values)

    def test_valid_full_candidate_passes(self):
        result = self.evaluate()
        self.assertTrue(result["passed"])
        self.assertEqual(result["failedGateIds"], [])

    def test_partial_detail_run_fails_full_gate(self):
        source_run = dict(self.source_run)
        source_run["metrics"] = {
            "detailRequestedCount": 1,
            "detailSuccessCount": 1,
            "detailFailureCount": 0,
        }
        result = self.evaluate(source_run=source_run)
        self.assertFalse(result["passed"])
        self.assertIn(
            "full_detail_coverage",
            result["failedGateIds"],
        )

    def test_duplicate_source_reference_fails(self):
        candidate = {
            **self.candidate,
            "events": [
                *self.candidate["events"],
                {
                    "id": "duplicate-ref",
                    "sourceRecords": [{
                        "sourceId": "huashan-1914",
                        "sourceEventId": "source-a",
                    }],
                },
            ],
        }
        result = self.evaluate(candidate=candidate)
        self.assertFalse(result["passed"])
        self.assertIn(
            "source_references_unique",
            result["failedGateIds"],
        )

    def test_review_queue_over_limit_fails(self):
        result = self.evaluate(
            review_queue=[{"title": "待確認"}],
        )
        self.assertFalse(result["passed"])
        self.assertIn(
            "review_queue_within_limit",
            result["failedGateIds"],
        )


if __name__ == "__main__":
    unittest.main()
