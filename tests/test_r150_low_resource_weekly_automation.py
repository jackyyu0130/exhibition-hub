from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


class LowResourceWorkflowTests(unittest.TestCase):
    def test_only_weekly_update_keeps_a_schedule(self) -> None:
        scheduled = []
        for path in sorted((ROOT / ".github/workflows").glob("*.yml")):
            if "schedule:" in path.read_text(encoding="utf-8"):
                scheduled.append(path.name)
        self.assertEqual(["update-exhibitions.yml"], scheduled)

    def test_weekly_workflow_has_compute_and_safety_limits(self) -> None:
        workflow = (
            ROOT / ".github/workflows/update-exhibitions.yml"
        ).read_text(encoding="utf-8")
        self.assertEqual(1, workflow.count("cron:"))
        self.assertIn('cron: "17 19 * * 6"', workflow)
        self.assertIn("cancel-in-progress: true", workflow)
        self.assertIn("timeout-minutes: 55", workflow)
        self.assertIn("WEEKLY_UPDATE_ENABLED", workflow)
        self.assertIn("vars.WEEKLY_UPDATE_ENABLED != 'false'", workflow)
        self.assertIn('MAX_DETAIL_FETCHES: "80"', workflow)
        self.assertIn('MAX_IMAGE_FETCHES: "80"', workflow)
        self.assertIn('CULTURE_API_WORKERS: "2"', workflow)
        self.assertNotIn("matrix:", workflow)
        self.assertNotIn("unittest discover", workflow)
        self.assertNotIn("branches: [main]", workflow)


class CultureFeedRetryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import sys

        scripts = str(ROOT / "scripts")
        if scripts not in sys.path:
            sys.path.insert(0, scripts)

    def test_empty_payload_moves_to_alternate_method_without_retries(self) -> None:
        import scraper

        class EmptyResponse:
            apparent_encoding = "utf-8"
            encoding = "utf-8"

            @staticmethod
            def raise_for_status() -> None:
                return None

            @staticmethod
            def json() -> list[object]:
                return []

        class EmptySession:
            def __init__(self) -> None:
                self.headers: dict[str, str] = {}
                self.calls = 0

            def get(self, *_args, **_kwargs) -> EmptyResponse:
                self.calls += 1
                return EmptyResponse()

        session = EmptySession()
        with patch.object(scraper, "network_session", return_value=session):
            records = scraper.fetch_category(
                "all",
                scraper.SourceConfig(timeout=5, retries=3, workers=1),
            )

        self.assertEqual([], records)
        self.assertEqual(len(scraper.API_METHODS), session.calls)

    def test_environment_integer_is_bounded(self) -> None:
        import scraper

        with patch.dict("os.environ", {"TEST_LIMIT": "999"}):
            self.assertEqual(
                4,
                scraper.bounded_environment_integer(
                    "TEST_LIMIT", 2, minimum=1, maximum=4
                ),
            )


if __name__ == "__main__":
    unittest.main()
