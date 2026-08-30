import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_official_source_batch import build_official_source_batch_diff

WORKFLOW = (
    ROOT / ".github" / "workflows" / "update-exhibitions.yml"
).read_text(encoding="utf-8")


class R1101PublishDiffReconciliationTests(unittest.TestCase):
    def test_batch_diff_matches_post_collector_preview(self):
        base = {
            "events": [
                {"id": "a", "title": "A"},
                {"id": "b", "title": "B"},
            ],
            "officialSourceBuild": {"published": False},
        }
        preview = {
            "events": [
                {"id": "a", "title": "A"},
                {"id": "b", "title": "B updated"},
                {"id": "c", "title": "C"},
            ],
            "officialSourceBuild": {"published": False},
        }
        report = {
            "failureIsolation": True,
            "sourceCount": 2,
            "successfulSourceCount": 1,
            "failedSourceCount": 1,
            "skippedSourceCount": 0,
            "finalEventCount": 3,
            "sources": [
                {"sourceId": "one", "status": "merged"},
                {
                    "sourceId": "two",
                    "status": "preserved_previous_base",
                },
            ],
        }
        diff = build_official_source_batch_diff(
            base,
            preview,
            report,
        )
        self.assertEqual(diff["previewEventCount"], 3)
        self.assertEqual(diff["addedEventCount"], 1)
        self.assertEqual(diff["modifiedEventCount"], 1)
        self.assertEqual(diff["removedBaseEventCount"], 0)
        self.assertTrue(
            all(
                value
                for key, value in diff["qualityGates"].items()
                if key != "published"
            )
        )
        self.assertFalse(diff["qualityGates"]["published"])

    def test_batch_diff_rejects_removed_base_event(self):
        base = {
            "events": [{"id": "a"}, {"id": "b"}],
            "officialSourceBuild": {"published": False},
        }
        preview = {
            "events": [{"id": "a"}],
            "officialSourceBuild": {"published": False},
        }
        report = {
            "failureIsolation": True,
            "finalEventCount": 1,
            "sources": [],
        }
        with self.assertRaisesRegex(
            ValueError,
            "baseEventsPreserved",
        ):
            build_official_source_batch_diff(
                base,
                preview,
                report,
            )

    def test_workflow_finalizes_against_post_batch_diff(self):
        runner = (
            ROOT / "scripts/run_local_weekly_update.py"
        ).read_text(encoding="utf-8")
        self.assertIn("run_local_weekly_update.py", WORKFLOW)
        self.assertIn(
            'official-sources-diff.json',
            runner,
        )
        finalize_block = runner.split(
            '"8/11 套用安全發布門檻"',
            1,
        )[1].split(
            '"9/11 清理不合格圖片與社群連結"',
            1,
        )[0]
        self.assertIn(
            'str(AUDIT / "official-sources-diff.json")',
            finalize_block,
        )
        self.assertNotIn(
            'str(AUDIT / "publish-diff.json")',
            finalize_block,
        )


if __name__ == "__main__":
    unittest.main()
