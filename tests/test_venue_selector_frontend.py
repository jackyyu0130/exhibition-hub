import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class VenueSelectorFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.js = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
        cls.css = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")

    def test_drawer_markup_exists(self):
        for marker in [
            'id="venueSelectorLaunch"',
            'id="venueSelectorDrawer"',
            'id="venueSelectorSearch"',
            'id="venueSelectorApply"',
        ]:
            self.assertIn(marker, self.html)

    def test_multi_venue_query_is_supported(self):
        self.assertIn("state.selectedVenues = new Set(venueValues)", self.js)
        self.assertIn("const value = [...selected].join(',')", self.js)

    def test_registry_is_loaded(self):
        self.assertIn("fetch('data/venues.json'", self.js)
        self.assertIn("state.venueRegistry", self.js)
        self.assertIn("data/northern_venue_matrix.json", self.js)

    def test_site_palette_drawer_styles_exist(self):
        self.assertIn(".venue-selector-drawer", self.css)
        self.assertIn("#fbf5ec", self.css)
        self.assertIn("@media (max-width: 760px)", self.css)

if __name__ == "__main__":
    unittest.main()
