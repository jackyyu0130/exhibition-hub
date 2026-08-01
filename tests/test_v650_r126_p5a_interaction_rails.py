import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
VERSION = (ROOT / "VERSION.txt").read_text(encoding="utf-8")


class R126P5AInteractionRailTests(unittest.TestCase):
    def test_detail_related_rail_has_visible_controls(self):
        self.assertIn('id="detailRelatedRail"', APP)
        self.assertIn('data-scroll-target="detailRelatedRail"', APP)
        self.assertIn('detail-related-controls', APP)
        self.assertIn(')), 10);', APP)

    def test_home_venue_rail_has_three_screens_and_deferred_media(self):
        self.assertIn('.slice(0, 36)', APP)
        self.assertIn('data-venue-src', APP)
        self.assertIn('function hydrateVenueRailPage', APP)
        self.assertIn('grid.dataset.pageCount', APP)
        self.assertIn('data-scroll-step="0.94"', HTML)

    def test_venue_type_tabs_have_left_and_right_controls(self):
        self.assertIn('venue-type-tabs-shell', HTML)
        self.assertEqual(HTML.count('data-scroll-target="venueTypeTabs"'), 2)
        self.assertIn('venue-type-scroll-button', CSS)

    def test_hero_intro_visibly_enters_from_right_without_layout_animation(self):
        p5a = CSS[CSS.index('STABLE2 P5-A'):]
        self.assertIn('clamp(360px, 49vw, 760px)', p5a)
        self.assertIn('clamp(300px, 42vw, 650px)', p5a)
        self.assertIn('clamp(250px, 36vw, 560px)', p5a)
        self.assertIn('transition-duration: 1.3s, 1.58s', p5a)
        self.assertNotIn('transition-property: width', p5a)
        self.assertNotIn('transition-property: left', p5a)

    def test_scroll_buttons_support_per_rail_step_and_venue_prefetch(self):
        self.assertIn("scrollButton.dataset.scrollStep || .85", APP)
        self.assertIn("hydrateVenueRailForDirection(target, direction)", APP)

    def test_cache_and_version_mark_p5a(self):
        self.assertIn('assets/styles.css?v=6.5.0-r12-stable2-p5a', HTML)
        self.assertIn('assets/app.js?v=6.5.0-r12-stable2-p5a', HTML)
        self.assertIn('Interaction patch: P5-A', VERSION)
        self.assertIn('STABLE2 P5-A', APP.splitlines()[0])


if __name__ == "__main__":
    unittest.main()
