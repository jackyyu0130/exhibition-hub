from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class R160CatalogConsistencyTests(unittest.TestCase):
    def test_category_filters_match_every_visible_detail_taxonomy(self) -> None:
        self.assertIn("function eventCategories(event)", APP)
        self.assertIn(
            "eventCategories(event).some(category => state.categories.has(category))",
            APP,
        )
        self.assertNotIn(
            "state.categories.has(eventPrimaryCategory(event))",
            APP,
        )
        self.assertIn("const detailCategories = eventCategories(event)", APP)
        self.assertIn("detailCategories.map(category =>", APP)

    def test_category_counts_use_the_same_multi_category_membership(self) -> None:
        self.assertGreaterEqual(
            APP.count("countBy(state.events, event => eventCategories(event))"),
            3,
        )
        self.assertNotIn(
            "countBy(state.events, event => [eventPrimaryCategory(event)])",
            APP,
        )

    def test_exhibition_cards_never_use_a_venue_photo_as_the_poster(self) -> None:
        image_markup = re.search(
            r"  function imageMarkup\(event, className = ''\) \{[\s\S]*?\n  \}",
            APP,
        )
        self.assertIsNotNone(image_markup)
        source = image_markup.group(0)
        self.assertNotIn("eventVenueImage(event)", source)
        self.assertNotIn("mediaKind === 'venue'", source)

    def test_branded_fallback_asset_is_packaged_and_referenced(self) -> None:
        asset = ROOT / "assets" / "exhibition-placeholder-v16.webp"
        self.assertTrue(asset.exists())
        self.assertGreater(asset.stat().st_size, 10_000)
        self.assertIn('url("exhibition-placeholder-v16.webp")', CSS)
        self.assertIn('data-media-kind="official-fallback"', APP)
        self.assertIn("fallback-art-brand", APP)

    def test_browser_cache_keys_are_bumped_for_the_new_runtime(self) -> None:
        self.assertIn('href="assets/styles.css?v=6.5.0-r18"', HTML)
        self.assertIn('src="assets/app.js?v=6.5.0-r18"', HTML)

    def test_card_prices_are_free_or_link_to_the_activity_page(self) -> None:
        compact_price = re.search(
            r"  function compactPriceLabel\(value = ''\) \{[\s\S]*?\n  \}",
            APP,
        )
        self.assertIsNotNone(compact_price)
        source = compact_price.group(0)
        self.assertIn("return '免費入場'", source)
        self.assertIn("return '票價請見活動頁面'", source)
        self.assertNotIn("NT$", source)
        self.assertNotIn('title="${escapeHtml(event.price)}"', APP)

    def test_detail_prices_use_the_same_public_label_as_cards(self) -> None:
        self.assertIn("detailMeta('票價', compactPriceLabel(event.price))", APP)
        self.assertNotIn("detailMeta('票價', event.price)", APP)


if __name__ == "__main__":
    unittest.main()
