import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from exhibition_hub.merging.candidate import (  # noqa: E402
    build_source_merge_candidate,
)


class SourceMergeCandidateTests(unittest.TestCase):
    def test_merge_and_new_event_are_non_published(self):
        base = {
            "events": [{
                "id": "base-1",
                "title": "波隆那世界插畫大獎展",
                "startDate": "2026-07-04",
                "endDate": "2026-09-28",
                "regionCanonical": "臺北市",
                "venueIds": ["huashan-1914"],
                "venueName": "華山1914文化創意產業園區",
                "images": [],
            }],
            "stats": {},
        }
        run = {
            "sourceId": "huashan-1914",
            "success": True,
            "records": [
                {
                    "source_id": "huashan-1914",
                    "source_event_id": "a",
                    "title": "波隆那世界插畫大獎展",
                    "detail_url": "https://example.com/a",
                    "raw": {
                        "sourceEventId": "a",
                        "title": "波隆那世界插畫大獎展",
                        "startDate": "2026-07-04",
                        "endDate": "2026-09-28",
                        "venueName": "華山1914文化創意產業園區",
                        "regionCanonical": "臺北市",
                        "officialUrl": "https://example.com/a",
                        "imageUrls": ["https://example.com/a.jpg"],
                    },
                },
                {
                    "source_id": "huashan-1914",
                    "source_event_id": "b",
                    "title": "全新華山獨家活動",
                    "detail_url": "https://example.com/b",
                    "raw": {
                        "sourceEventId": "b",
                        "title": "全新華山獨家活動",
                        "startDate": "2026-08-10",
                        "endDate": "2026-08-20",
                        "venueName": "華山1914文化創意產業園區",
                        "regionCanonical": "臺北市",
                        "officialUrl": "https://example.com/b",
                    },
                },
            ],
        }
        registry = {
            "sources": [{
                "id": "huashan-1914",
                "priority": 90,
                "venueIds": ["huashan-1914"],
            }],
        }
        candidate, report, review = (
            build_source_merge_candidate(
                base,
                run,
                registry,
                source_id="huashan-1914",
            )
        )
        self.assertFalse(report["published"])
        self.assertEqual(
            report["decisionCounts"]["auto_merge"],
            1,
        )
        self.assertEqual(
            report["decisionCounts"]["new_event"],
            1,
        )
        self.assertEqual(len(candidate["events"]), 2)
        self.assertEqual(review, [])
        self.assertIn(
            "https://example.com/a.jpg",
            candidate["events"][0]["images"],
        )


if __name__ == "__main__":
    unittest.main()
