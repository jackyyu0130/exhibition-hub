from __future__ import annotations

from datetime import date
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from exhibition_hub.curation import build_venue_indexes, evaluate_event


class R184CatalogVisibilityTests(unittest.TestCase):
    def event(self, *, hit_rate: int = 0) -> dict[str, object]:
        return {
            "id": "official-event",
            "title": "官方測試展覽",
            "endDate": "2099-12-31",
            "sourceUrl": "https://example.com/events/official-event",
            "images": ["https://example.com/images/poster.jpg"],
            "locationName": "測試展館",
            "venueGroup": "測試展館",
            "hitRate": hit_rate,
        }

    def venue_indexes(self, priority: str):
        return build_venue_indexes({
            "venues": [{
                "id": "test-venue",
                "name": "測試展館",
                "priority": priority,
                "confirmed": True,
            }],
        })

    def test_confirmed_venues_are_not_excluded_by_priority_or_zero_hit_rate(self):
        for priority in ("P1", "P2", "P3"):
            with self.subTest(priority=priority):
                by_id, by_name = self.venue_indexes(priority)
                keep, reason, venue = evaluate_event(
                    self.event(hit_rate=0),
                    by_id,
                    by_name,
                    today=date(2026, 9, 7),
                )
                self.assertTrue(keep)
                self.assertEqual(reason, "confirmed_venue_catalog")
                self.assertEqual(venue["priority"], priority)

    def test_unmatched_low_interest_event_is_still_excluded(self):
        keep, reason, venue = evaluate_event(
            self.event(hit_rate=0),
            {},
            {},
            today=date(2026, 9, 7),
        )
        self.assertFalse(keep)
        self.assertEqual(reason, "unmatched_or_low_interest")
        self.assertIsNone(venue)


if __name__ == "__main__":
    unittest.main()
