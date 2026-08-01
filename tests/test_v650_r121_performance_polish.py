import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
VERSION = (ROOT / "VERSION.txt").read_text(encoding="utf-8")


class R121PerformancePolishTests(unittest.TestCase):
    def test_stylesheet_cache_is_bumped_without_reloading_unchanged_javascript(self):
        self.assertIn("assets/styles.css?v=6.5.0-r12-stable2-p1", HTML)
        self.assertIn("assets/app.js?v=6.5.0-r12-stable2", HTML)
        self.assertIn("Performance patch: P1", VERSION)

    def test_desktop_hero_controls_are_inside_collage(self):
        self.assertIn("left: clamp(18px, 2vw, 30px) !important;", CSS)
        self.assertIn("right: clamp(18px, 2vw, 30px) !important;", CSS)
        self.assertIn("width: 52px !important;", CSS)

    def test_lower_home_sections_use_content_visibility(self):
        for selector in (
            ".home-view > .featured-block",
            ".home-view > .split-feature",
            ".home-view > .nearby-home",
            ".home-view > .venue-section",
        ):
            self.assertIn(selector, CSS)
        self.assertGreaterEqual(CSS.count("content-visibility: auto;"), 5)
        self.assertIn("contain-intrinsic-size: auto 860px;", CSS)

    def test_reveal_motion_is_slower_and_compositor_friendly(self):
        self.assertIn("transition-duration: .72s, .82s !important;", CSS)
        self.assertIn("transform: translate3d(0,10px,0) !important;", CSS)
        self.assertIn("cubic-bezier(.16,1,.3,1)", CSS)
        self.assertIn("animation: none !important;", CSS)

    def test_live_card_and_hero_filters_are_disabled(self):
        self.assertIn(".hero-ticket-stage .hero-postcard", CSS)
        self.assertIn(".exhibition-card .smart-image-foreground", CSS)
        self.assertIn("filter: none !important;", CSS)
        self.assertIn("contain: layout paint style;", CSS)


if __name__ == "__main__":
    unittest.main()
