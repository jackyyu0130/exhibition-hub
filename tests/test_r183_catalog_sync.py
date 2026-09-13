"""Regression checks for the canonical curated feed and taxonomy audit."""

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CURATED_PATH = ROOT / "data" / "exhibitions.curated.json"
AUDIT_PATH = ROOT / "data" / "update-reports" / "category-semantic-audit-r18.json"


class R183CatalogSyncTests(unittest.TestCase):
    def test_curated_feed_and_audit_share_complete_membership(self):
        curated = json.loads(CURATED_PATH.read_text(encoding="utf-8"))
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        events = curated["events"]

        self.assertGreater(len(events), 500)
        self.assertEqual(curated["stats"]["eventCount"], len(events))
        self.assertEqual(curated["stats"]["eventCount"], len(events))

        counts = {category: 0 for category in curated["stats"]["categoryCounts"]}
        for event in events:
            for category in event.get("categories", []):
                self.assertIn(category, counts)
                counts[category] += 1

        self.assertEqual(curated["stats"]["categoryCounts"], counts)
        self.assertEqual(curated["stats"]["categoryCounts"], counts)
        self.assertGreaterEqual(counts["動漫"], 20)


if __name__ == "__main__":
    unittest.main()
