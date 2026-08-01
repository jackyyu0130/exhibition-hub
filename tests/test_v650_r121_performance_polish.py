import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
VERSION = (ROOT / "VERSION.txt").read_text(encoding="utf-8")


class R121PerformancePolishTests(unittest.TestCase):
    def test_latest_cache_bust_supersedes_p1(self):
        self.assertIn("assets/styles.css?v=6.5.0-r12-stable2-p5a", HTML)
        self.assertIn("assets/app.js?v=6.5.0-r12-stable2-p5a", HTML)
        self.assertIn("Interaction patch: P5-A", VERSION)

    def test_p1_filter_and_shadow_safeguards_remain(self):
        self.assertIn(".hero-ticket-stage .hero-postcard", CSS)
        self.assertIn(".exhibition-card .smart-image-foreground", CSS)
        self.assertIn("filter: none !important;", CSS)
        self.assertIn("contain: layout paint", CSS)

    def test_large_home_sections_no_longer_materialize_in_one_frame(self):
        for selector in (
            ".home-view > .featured-block",
            ".home-view > .split-feature",
            ".home-view > .nearby-home",
            ".home-view > .venue-section",
        ):
            self.assertIn(selector, CSS)
        self.assertIn("content-visibility: visible !important;", CSS)
        self.assertIn("contain-intrinsic-size: none !important;", CSS)

    def test_reveal_motion_remains_compositor_friendly(self):
        self.assertIn("transition-duration: 1.02s, 1.16s !important;", CSS)
        self.assertIn("transform: translate3d(0, 16px, 0) !important;", CSS)
        self.assertIn("cubic-bezier(.16,1,.3,1)", CSS)
        self.assertIn("filter: none !important;", CSS)
        self.assertIn("clip-path: none !important;", CSS)

    def test_scroll_state_disables_hover_repaint(self):
        self.assertIn("body.is-scrolling .exhibition-card", CSS)
        self.assertIn("body.is-scrolling .venue-tile:hover", CSS)
        self.assertIn("transition: none !important;", CSS)


if __name__ == "__main__":
    unittest.main()
