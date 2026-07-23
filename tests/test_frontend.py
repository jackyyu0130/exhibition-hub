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

    def test_v37_cache_busting(self):
        self.assertIn("assets/styles.css?v=3.7", self.html)
        self.assertIn("assets/app.js?v=3.7", self.html)


if __name__ == "__main__":
    unittest.main()
