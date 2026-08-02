from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import sys

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/exhibition_hub/c4_monitor.py"
spec = importlib.util.spec_from_file_location("c4_monitor", MODULE_PATH)
c4 = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = c4
spec.loader.exec_module(c4)


class C4SourceMonitorTests(unittest.TestCase):
    def setUp(self):
        self.registry = {
            "safety": {"autoPublishMinimumConfidence": 0.94},
            "organizations": [
                {
                    "id": "venue-a",
                    "name": "Venue A",
                    "roles": ["venue"],
                    "venueMatches": [
                        {
                            "canonicalName": "Legacy Taipei",
                            "region": "臺北市",
                            "aliases": ["Legacy Taipei", "華山 Legacy"],
                        }
                    ],
                }
            ],
        }
        self.org = self.registry["organizations"][0]
        self.endpoint = {
            "id": "venue-a-1",
            "platform": "official_website",
            "url": "https://example.com/events",
            "accessMode": "public_html",
            "autoPublishAllowed": True,
        }

    def test_extracts_full_and_cross_year_date_ranges(self):
        self.assertEqual(c4.extract_dates("2026/09/12 - 2026/09/13"), ("2026-09-12", "2026-09-13"))
        self.assertEqual(c4.extract_dates("2026年12月31日至1月1日"), ("2026-12-31", "2027-01-01"))

    def test_matches_unique_venue_alias(self):
        match = c4.match_venue("演出地點：華山 Legacy", self.org, self.registry)
        self.assertIn(match.status, {"matched", "matched_by_source"})
        self.assertEqual(match.canonical_name, "Legacy Taipei")
        self.assertEqual(match.region, "臺北市")

    def test_official_complete_candidate_can_be_auto_publish_eligible(self):
        raw = {
            "title": "Example Band 2026 Live in Taipei 演唱會",
            "startDate": "2026-09-12",
            "endDate": "2026-09-12",
            "venueText": "Legacy Taipei",
            "imageUrl": "https://example.com/poster.jpg",
            "sourceUrl": "https://example.com/events/example-band",
            "description": "Example Band 世界巡迴台北站，演出地點 Legacy Taipei。",
            "evidence": ["official_detail", "json_ld_event"],
        }
        candidate = c4.make_candidate(
            raw,
            self.org,
            self.endpoint,
            self.registry,
            [],
            now=datetime(2026, 8, 2, tzinfo=timezone.utc),
        )
        self.assertTrue(candidate.autoPublishEligible)
        self.assertGreaterEqual(candidate.confidence, 0.94)
        self.assertEqual(candidate.venueName, "Legacy Taipei")
        self.assertEqual(candidate.blockingIssues, [])

    def test_missing_image_and_date_are_blocked(self):
        raw = {
            "title": "Example Band Live",
            "sourceUrl": "https://example.com/events/example-band",
            "description": "Legacy Taipei",
            "evidence": ["official_detail"],
        }
        candidate = c4.make_candidate(
            raw,
            self.org,
            self.endpoint,
            self.registry,
            [],
            now=datetime(2026, 8, 2, tzinfo=timezone.utc),
        )
        self.assertFalse(candidate.autoPublishEligible)
        self.assertIn("missing_full_date", candidate.blockingIssues)
        self.assertIn("missing_image", candidate.blockingIssues)

    def test_existing_event_is_not_published_again(self):
        raw = {
            "title": "Example Band 2026 Live in Taipei 演唱會",
            "startDate": "2026-09-12",
            "endDate": "2026-09-12",
            "venueText": "Legacy Taipei",
            "imageUrl": "https://example.com/poster.jpg",
            "sourceUrl": "https://example.com/events/example-band",
            "description": "Legacy Taipei",
            "evidence": ["official_detail", "json_ld_event"],
        }
        existing = [{"id": "existing", "title": c4.normalize_key(raw["title"]), "date": "2026-09-12", "venue": c4.normalize_key("Legacy Taipei"), "url": c4.normalize_url(raw["sourceUrl"])}]
        candidate = c4.make_candidate(
            raw,
            self.org,
            self.endpoint,
            self.registry,
            existing,
            now=datetime(2026, 8, 2, tzinfo=timezone.utc),
        )
        self.assertFalse(candidate.autoPublishEligible)
        self.assertEqual(candidate.duplicateOf, "existing")
        self.assertIn("duplicate_existing_event", candidate.blockingIssues)

    def test_apply_script_preserves_base_and_adds_only_eligible(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            base = folder / "base.json"
            candidates = folder / "candidates.json"
            output = folder / "output.json"
            report = folder / "report.json"
            base.write_text(json.dumps({"events": [{"id": "old", "title": "Old"}]}), encoding="utf-8")
            candidates.write_text(json.dumps({"candidates": [
                {
                    "candidateId": "good",
                    "sourceId": "venue-a",
                    "sourceName": "Venue A",
                    "endpointId": "venue-a-1",
                    "sourceUrl": "https://example.com/good",
                    "title": "Good Live 演唱會",
                    "startDate": "2026-09-12",
                    "endDate": "2026-09-12",
                    "venueName": "Legacy Taipei",
                    "region": "臺北市",
                    "imageUrl": "https://example.com/good.jpg",
                    "category": "演唱會",
                    "contentType": "concert",
                    "description": "desc",
                    "confidence": 0.98,
                    "evidence": ["official_detail"],
                    "autoPublishEligible": True,
                },
                {
                    "candidateId": "blocked",
                    "title": "Blocked",
                    "autoPublishEligible": False,
                },
            ]}), encoding="utf-8")
            subprocess.run([
                "python",
                str(ROOT / "scripts/apply_c4_candidates.py"),
                "--base", str(base),
                "--candidates", str(candidates),
                "--output", str(output),
                "--report", str(report),
            ], check=True, cwd=ROOT, capture_output=True, text=True)
            result = json.loads(output.read_text(encoding="utf-8"))
            audit = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(len(result["events"]), 2)
            self.assertEqual(audit["addedCount"], 1)
            self.assertIn("old", {event["id"] for event in result["events"]})

    def test_registry_has_user_supplied_sources_and_social_safety(self):
        registry = json.loads((ROOT / "data/c4_monitored_sources.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(registry["organizationCount"], 70)
        self.assertGreaterEqual(registry["endpointCount"], 95)
        self.assertEqual(registry["dailySchedule"], "04:00")
        self.assertFalse(registry["safety"]["directSocialScraping"])
        ids = {item["id"] for item in registry["organizations"]}
        for source_id in {"tixcraft", "kktix", "legacy", "livewarehouse", "livenationtw", "taiwan-music-festival"}:
            self.assertIn(source_id, ids)
        social = [endpoint for org in registry["organizations"] for endpoint in org["endpoints"] if endpoint["platform"] in {"instagram", "facebook"}]
        self.assertTrue(social)
        self.assertTrue(all(endpoint["accessMode"] == "meta_api_required" and endpoint["enabled"] is False for endpoint in social))

    def test_c4_workflow_runs_at_taiwan_0400_and_validates_before_push(self):
        text = (ROOT / ".github/workflows/c4-source-monitor.yml").read_text(encoding="utf-8")
        self.assertIn('cron: "0 20 * * *"', text)
        self.assertIn('matrix:\n        shard: [0, 1, 2, 3]', text)
        self.assertIn("Run complete regression tests", text)
        self.assertIn("Finalize public status and quality gates", text)
        self.assertIn("git push origin HEAD:main", text)
        self.assertLess(text.index("Run complete regression tests"), text.index("git push origin HEAD:main"))



if __name__ == "__main__":
    unittest.main()
