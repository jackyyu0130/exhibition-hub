import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from exhibition_hub.merging.dedupe import (  # noqa: E402
    MatchDecision,
    score_match,
)
from exhibition_hub.merging.policy import (  # noqa: E402
    merge_events,
)
from exhibition_hub.merging.source_adapter import (  # noqa: E402
    collector_record_to_event,
)


class PerformanceTitleMergeTests(unittest.TestCase):
    def make_existing(
        self,
        title,
        start_date,
        end_date,
    ):
        return {
            "id": "existing-event",
            "title": title,
            "startDate": start_date,
            "endDate": end_date,
            "regionCanonical": "臺北市",
            "venueIds": ["huashan-1914"],
            "venueName": (
                "華山1914文化創意產業園區"
            ),
            "sourceRecords": [],
        }

    def make_source(
        self,
        source_event_id,
        title,
        start_date,
        end_date,
    ):
        return collector_record_to_event(
            {
                "source_id": "huashan-1914",
                "source_event_id": source_event_id,
                "title": title,
                "detail_url": "https://example.com/event",
                "raw": {
                    "title": title,
                    "sourceEventId": source_event_id,
                    "startDate": start_date,
                    "endDate": end_date,
                    "venueName": (
                        "華山1914文化創意產業園區"
                    ),
                    "regionCanonical": "臺北市",
                    "officialUrl": (
                        "https://example.com/event"
                    ),
                },
            },
            source_priority=90,
            source_venue_ids=["huashan-1914"],
        )

    def test_exact_quoted_work_title_auto_merges(self):
        source = self.make_source(
            "performance_1",
            (
                "【2026華山親子表藝節】賦格樂集"
                "《星空下的魔笛》"
            ),
            "2026-07-19",
            "2026-08-23",
        )
        existing = self.make_existing(
            "2026華山親子表藝節《星空下的魔笛》",
            "2026-08-22",
            "2026-08-23",
        )

        result = score_match(source, existing)

        self.assertEqual(
            result.decision,
            MatchDecision.AUTO_MERGE,
        )
        self.assertIn(
            "core_title_exact",
            result.reasons,
        )

    def test_different_quoted_work_titles_do_not_merge(self):
        source = self.make_source(
            "performance_2",
            (
                "【2026華山親子表藝節】賦格樂集"
                "《星空下的魔笛》"
            ),
            "2026-07-19",
            "2026-08-23",
        )
        existing = self.make_existing(
            (
                "2026華山親子表藝節"
                "《擁抱海洋永續親子音樂會》"
            ),
            "2026-08-08",
            "2026-08-09",
        )

        result = score_match(source, existing)

        self.assertNotEqual(
            result.decision,
            MatchDecision.AUTO_MERGE,
        )

    def test_specific_existing_performance_dates_are_kept(self):
        source = self.make_source(
            "performance_3",
            (
                "【2026華山親子表藝節】福德隆劇場"
                "《把書吃掉｜西遊太空篇》"
            ),
            "2026-06-06",
            "2026-08-02",
        )
        existing = self.make_existing(
            (
                "2026華山親子表藝節"
                "《把書吃掉｜西遊太空篇》"
            ),
            "2026-08-01",
            "2026-08-02",
        )

        merged, changed = merge_events(existing, source)

        self.assertEqual(
            merged["startDate"],
            "2026-08-01",
        )
        self.assertEqual(
            merged["endDate"],
            "2026-08-02",
        )
        self.assertNotIn("startDate", changed)
        self.assertNotIn("endDate", changed)

    def test_series_dates_can_still_expand(self):
        source = self.make_source(
            "performance_4",
            "2026華山親子表藝節",
            "2026-06-06",
            "2026-08-30",
        )
        existing = self.make_existing(
            "2026華山親子表藝節",
            "2026-08-01",
            "2026-08-30",
        )

        merged, changed = merge_events(existing, source)

        self.assertEqual(
            source["sourceEntityKind"],
            "performance_series",
        )
        self.assertEqual(
            merged["startDate"],
            "2026-06-06",
        )
        self.assertIn("startDate", changed)


if __name__ == "__main__":
    unittest.main()
