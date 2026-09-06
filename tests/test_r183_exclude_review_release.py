from __future__ import annotations

import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.run_official_source_batch import sanitize_excluded_events


class ExcludeReviewReleaseTests(unittest.TestCase):
    def test_new_excluded_events_are_audit_only(self):
        base = {
            "events": [
                {"id": "published", "title": "既有展覽", "editorialStatus": "candidate"},
            ]
        }
        candidate = {
            "events": [
                {"id": "published", "title": "既有展覽", "editorialStatus": "candidate"},
                {
                    "id": "new-excluded",
                    "title": "商品活動",
                    "editorialStatus": "exclude_review",
                    "editorialFlags": ["possible_merchandise"],
                },
            ],
            "sourceMergeBuild": {"published": False},
        }

        sanitized, excluded, preserved = sanitize_excluded_events(candidate, base)

        self.assertEqual([item["id"] for item in sanitized["events"]], ["published"])
        self.assertEqual([item["id"] for item in excluded], ["new-excluded"])
        self.assertEqual(preserved, [])
        self.assertEqual(sanitized["sourceMergeBuild"]["candidateEventCount"], 1)
        self.assertEqual(sanitized["sourceMergeBuild"]["excludedReviewEventCount"], 1)
        self.assertNotIn(
            "exclude_review",
            {item.get("editorialStatus") for item in sanitized["events"]},
        )

    def test_existing_excluded_event_restores_previous_published_copy(self):
        base = {
            "events": [
                {
                    "id": "existing",
                    "title": "既有展覽",
                    "editorialStatus": "candidate",
                    "officialUrl": "https://example.test/existing",
                },
            ]
        }
        candidate = {
            "events": [
                {
                    "id": "existing",
                    "title": "既有展覽",
                    "editorialStatus": "exclude_review",
                    "editorialFlags": ["possible_course_or_workshop"],
                },
            ],
            "sourceMergeBuild": {"published": False},
        }

        sanitized, excluded, preserved = sanitize_excluded_events(candidate, base)

        self.assertEqual(excluded, [])
        self.assertEqual([item["id"] for item in preserved], ["existing"])
        self.assertEqual(sanitized["events"], base["events"])
        self.assertEqual(sanitized["sourceMergeBuild"]["excludedReviewEventCount"], 1)


if __name__ == "__main__":
    unittest.main()
