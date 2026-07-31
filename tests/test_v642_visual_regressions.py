import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")


class V642VisualRegressionTests(unittest.TestCase):
    def test_brand_asset_is_packaged_versioned_and_has_a_fallback(self):
        self.assertTrue(
            (ROOT / "assets" / "taiwan-exhibition-journal-logo-v10.png").is_file()
        )
        self.assertIn(
            "assets/taiwan-exhibition-journal-logo-v10.png?v=6.5.0-r7",
            HTML,
        )
        self.assertIn('class="brand-logo-fallback"', HTML)
        self.assertIn(".brand-logo-frame.logo-load-failed", CSS)

    def test_venue_type_tabs_cannot_be_compressed_into_arcs(self):
        regression_block = CSS[CSS.index(
            "/* Exhibition Hub V6.4.2 — post-deploy visual regression hotfixes */"
        ):]
        shared_rule = re.search(
            r"\.venue-selector-search,\s*"
            r"\.venue-selector-selected,\s*"
            r"\.venue-type-tabs\s*\{(.*?)\}",
            regression_block,
            re.S,
        )
        tabs_rule = re.search(
            r"\.venue-type-tabs\s*\{(.*?)\}",
            regression_block[shared_rule.end():],
            re.S,
        )
        self.assertIsNotNone(shared_rule)
        self.assertIsNotNone(tabs_rule)
        self.assertIn("flex-shrink: 0", shared_rule.group(1))
        self.assertIn("min-height: 38px", tabs_rule.group(1))

    def test_hero_shows_three_ticket_queue(self):
        self.assertIn("Exhibition Hub V6.5.0-R7", CSS)
        self.assertIn(".hero-ticket-slide", CSS)
        self.assertIn(".hero-ticket-slot-1", CSS)
        self.assertIn(".hero-ticket-slot-2", CSS)
        self.assertIn(".hero-ticket-slot-3", CSS)
        self.assertIn(".hero-carousel-next", CSS)
        self.assertIn(".hero-carousel-previous", CSS)
        self.assertNotIn("hero-postcard-image", (ROOT / "assets" / "app.js").read_text(encoding="utf-8"))

    def test_mobile_explore_cards_use_two_compact_columns(self):
        mobile_block = CSS
        grid_rule = re.search(
            r"\.listing-view \.exhibition-grid\s*\{(.*?)\}",
            mobile_block,
            re.S,
        )
        image_rule = re.search(
            r"\.listing-view \.card-image\s*\{(.*?)\}",
            mobile_block,
            re.S,
        )
        self.assertIsNotNone(grid_rule)
        self.assertIsNotNone(image_rule)
        self.assertIn(
            "grid-template-columns: repeat(2, minmax(0, 1fr))",
            grid_rule.group(1),
        )
        self.assertIn("aspect-ratio: 1 / 1", image_rule.group(1))

    def test_all_frontend_assets_share_the_same_cache_version(self):
        for marker in (
            "assets/styles.css?v=6.5.0-r10.4",
            "assets/app.js?v=6.5.0-r10.4",
            "assets/favicon-48.png?v=6.5.0-r7",
            "assets/apple-touch-icon.png?v=6.5.0-r7",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, HTML)


if __name__ == "__main__":
    unittest.main()
