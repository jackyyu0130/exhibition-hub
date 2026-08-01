import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
VERSION = (ROOT / "VERSION.txt").read_text(encoding="utf-8")


class R123SectionSmoothnessTests(unittest.TestCase):
    def test_nearby_and_venue_sections_have_dedicated_motion_modes(self):
        self.assertIn('data-section-motion="nearby"', HTML)
        self.assertIn('data-section-motion="venue"', HTML)
        self.assertIn('nearby-mini-card motion-card', APP)

    def test_section_timings_are_slower_and_transform_only(self):
        self.assertIn('transition-duration: 1.38s, 1.56s', CSS)
        self.assertIn('transition-duration: 1.46s, 1.64s', CSS)
        self.assertIn('transition-property: opacity, transform', CSS)
        self.assertIn('clip-path: none', CSS)

    def test_scrolling_does_not_disable_card_reveal_transitions(self):
        marker = 'Exhibition Hub V6.5.0-R12 STABLE2 P3'
        section = CSS[CSS.index(marker):]
        self.assertIn('transition-property: opacity, transform', section)
        self.assertNotIn('body.is-scrolling .venue-tile {\n  transition: none', section)

    def test_venue_grid_prepares_before_it_reaches_viewport(self):
        self.assertIn("rootMargin:'1200px 0px'", APP)

    def test_cache_bust_and_version_mark_p3(self):
        self.assertIn('assets/styles.css?v=6.5.0-r12-stable2-p3', HTML)
        self.assertIn('assets/app.js?v=6.5.0-r12-stable2-p3', HTML)
        self.assertIn('Performance patch: P3', VERSION)


if __name__ == '__main__':
    unittest.main()
