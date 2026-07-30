import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from prepare_source_publish_preview import (  # noqa: E402
    build_preview,
)


class SourcePublishPreviewTests(unittest.TestCase):
    def setUp(self):
        self.base = {
            "updatedAt": "2026-07-28T00:00:00+08:00",
            "events": [
                {
                    "id": "base-a",
                    "title": "既有活動",
                    "editorialStatus": "candidate",
                    "images": [],
                },
            ],
        }
        self.source_run = {
            "sourceId": "huashan-1914",
            "success": True,
            "startedAt": "2026-07-28T01:00:00+08:00",
            "records": [
                {
                    "source_event_id": "source-a",
                },
                {
                    "source_event_id": "source-b",
                },
                {
                    "source_event_id": "source-c",
                },
            ],
            "metrics": {
                "detailRequestedCount": 3,
                "detailSuccessCount": 3,
                "detailFailureCount": 0,
            },
        }
        self.candidate = {
            "events": [
                {
                    "id": "base-a",
                    "title": "既有活動",
                    "editorialStatus": "candidate",
                    "images": ["https://example.com/a.jpg"],
                    "sourceRecords": [{
                        "sourceId": "huashan-1914",
                        "sourceEventId": "source-a",
                    }],
                },
                {
                    "id": "new-b",
                    "title": "華山新活動",
                    "editorialStatus": "candidate",
                    "images": [],
                    "sourceRecords": [{
                        "sourceId": "huashan-1914",
                        "sourceEventId": "source-b",
                    }],
                },
                {
                    "id": "excluded-c",
                    "title": "課程活動",
                    "editorialStatus": "exclude_review",
                    "images": [],
                    "sourceRecords": [{
                        "sourceId": "huashan-1914",
                        "sourceEventId": "source-c",
                    }],
                },
            ],
            "sourceMergeBuild": {
                "published": False,
            },
        }
        self.merge_report = {
            "published": False,
        }
        self.quality_report = {
            "passed": True,
            "failedGateIds": [],
        }

    def build(self, **changes):
        values = {
            "base": self.base,
            "source_run": self.source_run,
            "candidate": self.candidate,
            "merge_report": self.merge_report,
            "review": [],
            "quality_report": self.quality_report,
            "source_id": "huashan-1914",
        }
        values.update(changes)
        return build_preview(**values)

    def test_valid_preview_preserves_base_and_excludes_review(self):
        preview, diff, excluded = self.build()

        self.assertEqual(
            len(preview["events"]),
            2,
        )
        self.assertEqual(
            diff["addedEventCount"],
            1,
        )
        self.assertEqual(
            diff["modifiedEventCount"],
            1,
        )
        self.assertEqual(
            diff["removedBaseEventCount"],
            0,
        )
        self.assertEqual(
            excluded["eventCount"],
            1,
        )
        self.assertFalse(
            preview["officialSourceBuild"][
                "published"
            ]
        )

    def test_failed_quality_report_is_rejected(self):
        quality = {
            "passed": False,
            "failedGateIds": ["full_detail_coverage"],
        }
        with self.assertRaises(ValueError):
            self.build(
                quality_report=quality,
            )

    def test_non_empty_review_queue_is_rejected(self):
        with self.assertRaises(ValueError):
            self.build(
                review=[{"title": "待確認"}],
            )

    def test_missing_base_event_is_rejected(self):
        candidate = {
            **self.candidate,
            "events": self.candidate["events"][1:],
        }
        with self.assertRaises(ValueError):
            self.build(
                candidate=candidate,
            )

    def test_duplicate_source_reference_is_rejected(self):
        duplicate = {
            "id": "duplicate",
            "title": "重複參照",
            "editorialStatus": "candidate",
            "sourceRecords": [{
                "sourceId": "huashan-1914",
                "sourceEventId": "source-a",
            }],
        }
        candidate = {
            **self.candidate,
            "events": [
                *self.candidate["events"],
                duplicate,
            ],
        }
        with self.assertRaises(ValueError):
            self.build(
                candidate=candidate,
            )


if __name__ == "__main__":
    unittest.main()
