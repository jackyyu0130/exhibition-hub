import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class R14LocalUpdateAndFaviconTests(unittest.TestCase):
    def test_all_standard_favicon_files_exist(self):
        for relative in (
            "favicon.ico",
            "favicon.svg",
            "favicon-48.png",
            "favicon-96.png",
            "favicon-192.png",
            "favicon-512.png",
            "apple-touch-icon.png",
            "site.webmanifest",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_homepage_uses_stable_root_favicon_urls(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="/favicon.ico"', html)
        self.assertIn('href="/favicon.svg"', html)
        self.assertIn('href="/favicon-48.png"', html)
        self.assertIn('href="/site.webmanifest"', html)
        self.assertNotRegex(html, re.compile(r"favicon[^\"']*\?v="))

    def test_manifest_icons_are_absolute_and_available(self):
        payload = json.loads((ROOT / "site.webmanifest").read_text(encoding="utf-8"))
        for icon in payload["icons"]:
            self.assertTrue(icon["src"].startswith("/"))
            self.assertTrue((ROOT / icon["src"].lstrip("/")).is_file())

    def test_publish_workflow_is_manual_only(self):
        workflow = (ROOT / ".github/workflows/publish-prepared-site.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("schedule:", workflow)
        self.assertNotRegex(workflow, re.compile(r"\bcron:"))
        self.assertNotIn("scraper.py", workflow)

    def test_local_update_entrypoints_exist(self):
        self.assertTrue((ROOT / "run_weekly_update.command").is_file())
        self.assertTrue((ROOT / "scripts/run_local_weekly_update.py").is_file())

    def test_local_update_handoff_uses_develop_pr_and_reports_venue_count(self):
        runner = (ROOT / "scripts/run_local_weekly_update.py").read_text(
            encoding="utf-8"
        )
        guide = (ROOT / "R14_MAC_WEEKLY_UPDATE_GUIDE_ZH-TW.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("afterVenueCount", runner)
        self.assertIn("develop → main", runner)
        self.assertIn("Current branch 是 `develop`", guide)
        self.assertIn("develop → main", guide)
        self.assertNotIn("Commit to main", guide)


if __name__ == "__main__":
    unittest.main()
