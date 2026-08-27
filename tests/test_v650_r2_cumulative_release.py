import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
VERSION = (ROOT / "VERSION.txt").read_text(encoding="utf-8")
MANIFEST = json.loads((ROOT / "MANIFEST_V6.5.0-R7.json").read_text(encoding="utf-8"))


class V650R2CumulativeReleaseTests(unittest.TestCase):
    def test_r7_assets_remain_and_favicon_uses_stable_root_urls(self):
        for marker in (
            "assets/styles.css?v=6.5.0-r11.0.2",
            "assets/app.js?v=6.5.0-r11.0.2",
            'href="/favicon-48.png"',
            'href="/apple-touch-icon.png"',
            "assets/taiwan-exhibition-journal-logo-v10.png?v=6.5.0-r7",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, HTML)

    def test_refined_hero_behaviors_remain_present(self):
        self.assertIn('id="heroNextButton"', HTML)
        self.assertIn('id="heroPreviousButton"', HTML)
        self.assertNotIn('id="heroShuffleButton"', HTML)
        self.assertNotIn("HERO_ROTATION_MS", APP)
        self.assertIn("function heroPoseIndex", APP)
        self.assertIn("function heroTicketSlideMarkup", APP)
        self.assertIn('data-pose="${poseIndex}"', APP)
        self.assertIn("const thirdIndex = heroIndex(2)", APP)
        self.assertIn("changeHeroPair(deltaX < 0 ? 1 : -1)", APP)
        self.assertIn(".hero-ticket-slide .hero-ticket-card", CSS)
        self.assertIn("min-height: 144px;", CSS)
        self.assertIn("mobile-home-quick-actions", HTML)
        self.assertIn(".listing-view .card-badge {", CSS)
        self.assertIn("justify-content: center;", CSS)
        self.assertIn(".hero-carousel-next { left: -78px; }", CSS)
        self.assertIn(".hero-ticket-slot-3", CSS)
        self.assertNotIn("hero-postcard-image", APP)

    def test_r1_huashan_recovery_files_are_present(self):
        paths = [
            "scripts/exhibition_hub/collectors/huashan.py",
            "scripts/run_collectors.py",
            "tests/test_huashan_detail_collector.py",
            "tests/fixtures/huashan_listing_page1.html",
            "tests/fixtures/huashan_listing_page2.html",
            "tests/fixtures/huashan_detail_chiikawa.html",
            "tests/fixtures/huashan_detail_osamu.html",
            "tests/fixtures/huashan_detail_popup.html",
        ]
        for relative in paths:
            with self.subTest(relative=relative):
                self.assertTrue((ROOT / relative).is_file())

    def test_release_metadata_identifies_refinement_r7(self):
        self.assertIn("V6.5.0-R7", VERSION)
        self.assertEqual(MANIFEST["version"], "6.5.0-R7")
        self.assertTrue(MANIFEST["frontendChanged"])
        self.assertFalse(MANIFEST["productionPipelineChanged"])
        self.assertFalse(MANIFEST["officialDataChanged"])
        self.assertIn("data/", MANIFEST["excludedFromSafePackage"])


if __name__ == "__main__":
    unittest.main()
