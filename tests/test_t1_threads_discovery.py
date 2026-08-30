from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.exhibition_hub.threads_discovery import (
    build_query_plan,
    discover_threads,
    normalize_post,
)

ROOT = Path(__file__).resolve().parents[1]


class T1ThreadsDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(
            (ROOT / "data/threads_search_config.json").read_text(
                encoding="utf-8"
            )
        )
        self.now = datetime(2026, 8, 2, 12, tzinfo=timezone.utc)
        self.events = [
            {
                "id": "event-1",
                "title": "夢與緋光 特展",
                "startDate": "2026-08-10",
                "endDate": "2026-09-20",
            }
        ]

    def test_plan_combines_rotating_static_and_current_event_titles(self):
        plan = build_query_plan(
            self.config,
            self.events,
            now=self.now,
            include_top=True,
        )
        queries = {(item["q"], item["searchType"]) for item in plan}
        self.assertIn(("夢與緋光 特展", "RECENT"), queries)
        self.assertTrue(any(kind == "TOP" for _, kind in queries))
        self.assertLessEqual(
            sum(1 for item in plan if item["kind"] == "static"),
            self.config["limits"]["maxStaticQueriesPerRun"],
        )

    def test_post_is_anonymized_and_full_username_is_not_saved(self):
        candidate = normalize_post(
            {
                "id": "1",
                "permalink": "https://www.threads.com/@someone/post/ABC?xmt=tracking",
                "username": "someone",
                "text": "夢與緋光 特展看完很喜歡，展期到九月。",
                "timestamp": "2026-08-02T10:00:00+0000",
                "is_verified": False,
            },
            {
                "q": "夢與緋光 特展",
                "searchType": "RECENT",
                "kind": "event_title",
            },
            self.config,
        )
        self.assertIsNotNone(candidate)
        self.assertNotIn("username", candidate)
        self.assertNotIn("username", candidate)
        self.assertNotIn("authorDisplay", candidate)
        self.assertTrue(candidate["sourceAccountHash"])
        self.assertNotIn("xmt=", candidate["postUrl"])
        self.assertLessEqual(len(candidate["shortExcerpt"]), 240)

    def test_discovery_deduplicates_posts_returned_by_multiple_queries(self):
        post = {
            "id": "1",
            "permalink": "https://www.threads.com/@venue/post/ABC",
            "username": "taipei.selected",
            "text": "台北展覽推薦：夢與緋光 特展正在展出。",
            "timestamp": "2026-08-02T10:00:00+0000",
            "is_verified": True,
        }

        def fake_search(query):
            return [post]

        candidates, report = discover_threads(
            self.config,
            self.events,
            token="test-token",
            now=self.now,
            search_fn=fake_search,
        )
        self.assertEqual(len(candidates), 1)
        self.assertEqual(report["status"], "success")
        self.assertGreater(report["queryCount"], 1)
        self.assertTrue(candidates[0]["verifiedAccount"])
        self.assertGreater(candidates[0]["editorWeight"], 0)

    def test_missing_token_is_safe_skip_and_writes_report(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            output = folder / "threads.json"
            signals = folder / "signals.json"
            report = folder / "report.json"
            env = dict(os.environ)
            env.pop("THREADS_ACCESS_TOKEN", None)
            result = subprocess.run(
                [
                    "python",
                    str(ROOT / "scripts/run_threads_discovery.py"),
                    "--config",
                    str(ROOT / "data/threads_search_config.json"),
                    "--events",
                    str(ROOT / "data/exhibitions.curated.json"),
                    "--output",
                    str(output),
                    "--signals-output",
                    str(signals),
                    "--report",
                    str(report),
                ],
                cwd=ROOT,
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "not_configured")
            self.assertEqual(
                json.loads(output.read_text(encoding="utf-8"))["candidates"],
                [],
            )
            self.assertEqual(result.returncode, 0)

    def test_workflow_uses_secret_and_never_pushes(self):
        text = (
            ROOT / ".github/workflows/social-discovery-review.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("secrets.THREADS_ACCESS_TOKEN", text)
        self.assertIn("run_threads_discovery.py", text)
        self.assertIn("workflow_dispatch:", text)
        self.assertNotIn("schedule:", text)
        self.assertIn("contents: read", text)
        self.assertNotIn("git push", text)
        self.assertIn("Confirm no public feed mutation", text)


if __name__ == "__main__":
    unittest.main()
