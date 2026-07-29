import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from finalize_source_publish import finalize_publish  # noqa: E402


class SourcePublishFinalizerTests(unittest.TestCase):
    def setUp(self):
        self.current = {
            "events": [
                {"id": "a", "title": "A", "editorialStatus": "candidate"},
                {"id": "b", "title": "B", "editorialStatus": "candidate"},
            ]
        }
        self.preview = {
            "events": [
                {"id": "a", "title": "A", "editorialStatus": "candidate"},
                {"id": "b", "title": "B", "editorialStatus": "candidate"},
                {"id": "c", "title": "C", "editorialStatus": "candidate"},
            ],
            "officialSourceBuild": {"published": False},
        }
        self.diff = {
            "published": False,
            "previewEventCount": 3,
            "removedBaseEventCount": 0,
            "qualityGates": {
                "sourceRunSuccess": True,
                "fullDetailCoverage": True,
                "candidateQualityPassed": True,
                "reviewQueueEmpty": True,
                "baseEventsPreserved": True,
                "candidateIdsUnique": True,
                "previewIdsUnique": True,
                "sourceReferencesComplete": True,
                "sourceReferencesUnique": True,
                "published": False,
            },
        }
        self.source_run = {
            "sourceId": "huashan-1914",
            "success": True,
            "records": [{"source_event_id": "one"}],
            "metrics": {
                "detailRequestedCount": 1,
                "detailSuccessCount": 1,
                "detailFailureCount": 0,
            },
        }
        self.quality = {"passed": True, "failedGateIds": []}

    def finalize(self, **changes):
        values = {
            "current": self.current,
            "preview": self.preview,
            "diff": self.diff,
            "source_run": self.source_run,
            "quality_report": self.quality,
            "source_id": "huashan-1914",
            "minimum_events": 1,
            "max_drop_ratio": 0.15,
            "max_drop_count": 250,
        }
        values.update(changes)
        return finalize_publish(**values)

    def test_valid_preview_becomes_published(self):
        final, report = self.finalize()
        self.assertTrue(final["officialSourceBuild"]["published"])
        self.assertTrue(report["published"])
        self.assertEqual(report["addedEventCount"], 1)
        self.assertEqual(report["removedEventCount"], 0)

    def test_failed_quality_is_rejected(self):
        with self.assertRaises(ValueError):
            self.finalize(quality_report={"passed": False, "failedGateIds": ["x"]})

    def test_duplicate_ids_are_rejected(self):
        preview = dict(self.preview)
        preview["events"] = [*self.preview["events"], dict(self.preview["events"][0])]
        diff = dict(self.diff)
        diff["previewEventCount"] = 4
        with self.assertRaises(ValueError):
            self.finalize(preview=preview, diff=diff)

    def test_large_count_drop_is_rejected(self):
        current = {
            "events": [
                {"id": f"event-{index}", "editorialStatus": "candidate"}
                for index in range(20)
            ]
        }
        preview = {
            "events": [
                {"id": f"event-{index}", "editorialStatus": "candidate"}
                for index in range(5)
            ],
            "officialSourceBuild": {"published": False},
        }
        diff = dict(self.diff)
        diff["previewEventCount"] = 5
        with self.assertRaises(ValueError):
            self.finalize(
                current=current,
                preview=preview,
                diff=diff,
                max_drop_count=5,
            )

    def test_excluded_review_event_is_rejected(self):
        preview = dict(self.preview)
        preview["events"] = [
            *self.preview["events"],
            {"id": "x", "editorialStatus": "exclude_review"},
        ]
        diff = dict(self.diff)
        diff["previewEventCount"] = 4
        with self.assertRaises(ValueError):
            self.finalize(preview=preview, diff=diff)


if __name__ == "__main__":
    unittest.main()
