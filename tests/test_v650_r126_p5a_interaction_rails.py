import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
VERSION = (ROOT / "VERSION.txt").read_text(encoding="utf-8")


class R126P5AInteractionRailCompatibilityTests(unittest.TestCase):
    """Compatibility checks retained for branches that previously received P5-A."""

    def test_detail_related_rail_has_visible_controls(self):
        self.assertIn('id="detailRelatedRail"', APP)
        self.assertIn('data-scroll-target="detailRelatedRail"', APP)
        self.assertIn('detail-related-heading', CSS)
        self.assertIn('target.scrollTo', APP)

    def test_home_venue_rail_has_three_screens(self):
        self.assertIn('.slice(0, 36)', APP)
        self.assertIn('#venueGrid.venue-grid', CSS)
        self.assertIn('grid-template-rows: repeat(3', CSS)
        self.assertIn('overflow-x: auto !important', CSS)
        self.assertIn('data-scroll-target="venueGrid"', HTML)

    def test_venue_type_tabs_have_left_and_right_controls(self):
        self.assertIn('venue-type-tabs-shell', HTML)
        self.assertEqual(HTML.count('data-scroll-target="venueTypeTabs"'), 2)
        self.assertIn('venue-type-scroll-button', CSS)

    def test_hero_intro_enters_from_right_without_layout_animation(self):
        p5b = CSS[CSS.index('STABLE2 P5-B'):]
        self.assertIn('clamp(310px, 42vw, 690px)', p5b)
        self.assertIn('clamp(270px, 37vw, 610px)', p5b)
        self.assertIn('clamp(230px, 32vw, 530px)', p5b)
        self.assertIn('transition-duration: 1.65s, 2.05s', p5b)
        self.assertNotIn('transition-property: width', p5b)
        self.assertNotIn('transition-property: left', p5b)

    def test_scroll_buttons_use_clamped_scroll_targets(self):
        self.assertIn('const nextLeft = Math.max(0, Math.min(maxLeft', APP)
        self.assertIn('target.scrollTo({left:nextLeft', APP)

    def test_cache_and_version_mark_p5b(self):
        self.assertIn('assets/styles.css?v=6.5.0-r12-stable2-p5b', HTML)
        self.assertIn('assets/app.js?v=6.5.0-r12-stable2-p5b', HTML)
        self.assertIn('Integrated repair: P5-B', VERSION)
        self.assertIn('P5-B', APP.splitlines()[0])


if __name__ == "__main__":
    unittest.main()
