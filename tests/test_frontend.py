import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FrontendContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.app = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
        cls.css = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")

    def test_shared_date_and_status_result_area(self):
        self.assertEqual(self.html.count('id="filterResultsSection"'), 1)
        self.assertNotIn('id="statusResultsSection"', self.html)
        self.assertNotIn('id="dateResultsSection"', self.html)

    def test_single_open_region_and_clear_all_controls(self):
        self.assertIn("data-region-accordion", self.app)
        self.assertIn("data-clear-all-filters", self.app)
        self.assertIn("details.open = false", self.app)

    def test_smart_images_use_blurred_backdrop_and_clear_foreground(self):
        self.assertIn("smart-image-blur", self.app)
        self.assertIn("smart-image-foreground", self.app)
        self.assertIn("filter: blur", self.css)

    def test_facebook_is_rejected_in_frontend(self):
        self.assertIn("function isFacebookUrl", self.app)
        self.assertIn("isFacebookUrl(sourceUrl)", self.app)

    def test_home_cards_are_square(self):
        self.assertIn(".home-view .exhibition-card .card-image { aspect-ratio: 1 / 1; }", self.css)

    def test_venue_cards_use_horizontal_motion_rail(self):
        self.assertIn('data-scroll-target="venueGrid"', self.html)
        self.assertIn('class="venue-grid" id="venueGrid"', self.html)
        self.assertIn("eventImage", self.app)
        self.assertIn("venue-tile motion-card motion-from-right", self.app)
        self.assertIn("grid-auto-flow: column", self.css)

    def test_city_map_replaces_simple_map_fragment(self):
        self.assertIn('class="paper-city-map"', self.html)
        self.assertIn("CITY ART WALK", self.html)
        self.assertNotIn('class="paper-map-fragment"', self.html)

    def test_v38_cache_busting(self):
        self.assertIn("assets/styles.css?v=3.8", self.html)
        self.assertIn("assets/app.js?v=3.8", self.html)


if __name__ == "__main__":
    unittest.main()
