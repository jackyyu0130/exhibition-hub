import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from exhibition_hub.merging.dedupe import (  # noqa: E402
    MatchDecision,
    score_match,
)


class SourceMergeDedupeTests(unittest.TestCase):
    def setUp(self):
        self.existing = {
            "id": "existing-1",
            "title": "波隆那世界插畫大獎展",
            "startDate": "2026-07-04",
            "endDate": "2026-09-28",
            "regionCanonical": "臺北市",
            "venueIds": ["huashan-1914"],
            "venueName": "華山1914文化創意產業園區",
            "sourceUrl": "https://www.opentix.life/event/1",
        }
        self.source = {
            "title": "波隆那世界插畫大獎展",
            "startDate": "2026-07-04",
            "endDate": "2026-09-28",
            "regionCanonical": "臺北市",
            "venueIds": ["huashan-1914"],
            "venueName": "華山1914文化創意產業園區",
            "officialUrl": (
                "https://www.huashan1914.com/w/"
                "huashan1914/exhibition_1"
            ),
            "collectorSourceId": "huashan-1914",
            "sourceEventId": "exhibition_1",
        }

    def test_exact_title_date_and_venue_auto_merge(self):
        result = score_match(
            self.source,
            self.existing,
        )
        self.assertEqual(
            result.decision,
            MatchDecision.AUTO_MERGE,
        )
        self.assertGreaterEqual(result.score, 0.84)

    def test_date_conflict_does_not_auto_merge(self):
        source = dict(self.source)
        source["startDate"] = "2027-07-04"
        source["endDate"] = "2027-09-28"
        result = score_match(source, self.existing)
        self.assertNotEqual(
            result.decision,
            MatchDecision.AUTO_MERGE,
        )
        self.assertIn("dates_conflict", result.reasons)

    def test_source_reference_is_strong_match(self):
        existing = dict(self.existing)
        existing["title"] = "活動名稱曾經改版"
        existing["sourceRecords"] = [{
            "sourceId": "huashan-1914",
            "sourceEventId": "exhibition_1",
        }]
        result = score_match(self.source, existing)
        self.assertEqual(
            result.decision,
            MatchDecision.AUTO_MERGE,
        )
        self.assertTrue(result.source_reference_exact)


if __name__ == "__main__":
    unittest.main()
