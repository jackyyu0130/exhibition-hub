from __future__ import annotations

from datetime import date
from pathlib import Path
import unittest

from scripts.finalize_source_publish import finalize_publish


AS_OF_DATE = date(2026, 8, 14)


def event(event_id: str, end_date: str | None) -> dict[str, str]:
    payload = {"id": event_id, "title": event_id}
    if end_date is not None:
        payload["endDate"] = end_date
    return payload


def preview_payload(events: list[dict[str, str]]) -> dict[str, object]:
    return {
        "events": events,
        "officialSourceBuild": {"published": False},
    }


def source_run() -> dict[str, object]:
    return {
        "success": True,
        "sourceId": "huashan-1914",
        "records": [{"id": "source-record"}],
        "metrics": {
            "detailRequestedCount": 1,
            "detailSuccessCount": 1,
            "detailFailureCount": 0,
        },
    }


def finalize(
    current_events: list[dict[str, str]],
    preview_events: list[dict[str, str]],
    *,
    max_active_removals: int,
    max_total_drop_ratio: float = 1.0,
):
    return finalize_publish(
        current={"events": current_events},
        preview=preview_payload(preview_events),
        diff={
            "published": False,
            "previewEventCount": len(preview_events),
            "removedBaseEventCount": 0,
            "qualityGates": {
                "published": False,
                "baseEventsPreserved": True,
            },
        },
        source_run=source_run(),
        quality_report={"passed": True, "failedGateIds": []},
        source_id="huashan-1914",
        minimum_events=1,
        max_drop_ratio=max_total_drop_ratio,
        max_drop_count=max_active_removals,
        as_of_date=AS_OF_DATE,
    )


class ProductionPublishGateTests(unittest.TestCase):
    def test_workflow_uses_strict_active_limit_and_triggers_data_refresh(self):
        workflow = Path(".github/workflows/update-exhibitions.yml").read_text(
            encoding="utf-8"
        )
        runner = Path("scripts/run_local_weekly_update.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("run_local_weekly_update.py", workflow)
        self.assertIn('"--max-drop-count", "25"', runner)
        self.assertNotIn('"--max-drop-count", "250"', runner)
        self.assertIn("scripts/finalize_source_publish.py", runner)

    def test_expired_cleanup_does_not_consume_active_removal_budget(self):
        current_events = [
            event("expired-a", "2026-08-01"),
            event("expired-b", "2026-08-13"),
            event("active-a", "2026-09-01"),
            event("kept-a", "2026-09-01"),
            event("kept-b", "2026-10-01"),
        ]
        final, report = finalize(
            current_events,
            [current_events[3], current_events[4]],
            max_active_removals=1,
        )

        self.assertTrue(final["officialSourceBuild"]["published"])
        self.assertEqual(report["expiredRemovedEventCount"], 2)
        self.assertEqual(report["activeRemovedEventCount"], 1)
        self.assertEqual(report["expiredRemovedIds"], ["expired-a", "expired-b"])
        self.assertEqual(report["activeRemovedIds"], ["active-a"])

    def test_active_removal_limit_still_blocks_publish(self):
        current_events = [
            event("active-a", "2026-09-01"),
            event("active-b", "2026-10-01"),
            event("kept", "2026-10-01"),
        ]
        with self.assertRaisesRegex(ValueError, "Active, future"):
            finalize(
                current_events,
                [current_events[2]],
                max_active_removals=1,
            )

    def test_missing_or_invalid_end_date_is_treated_as_active(self):
        current_events = [
            event("unknown-a", None),
            event("unknown-b", "not-a-date"),
            event("kept", "2026-10-01"),
        ]
        with self.assertRaisesRegex(ValueError, "date-unknown"):
            finalize(
                current_events,
                [current_events[2]],
                max_active_removals=1,
            )

    def test_total_drop_ratio_still_blocks_large_expired_cleanup(self):
        current_events = [
            event("expired-a", "2026-08-01"),
            event("expired-b", "2026-08-02"),
            event("expired-c", "2026-08-03"),
            event("kept", "2026-10-01"),
        ]
        with self.assertRaisesRegex(ValueError, "drop ratio"):
            finalize(
                current_events,
                [current_events[3]],
                max_active_removals=0,
                max_total_drop_ratio=0.20,
            )


if __name__ == "__main__":
    unittest.main()
