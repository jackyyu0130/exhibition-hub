from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class R186MobileDiscoveryTests(unittest.TestCase):
    def test_explore_header_has_a_search_form_that_reuses_search_navigation(self) -> None:
        self.assertIn('id="listingInlineSearchForm"', HTML)
        self.assertIn('id="listingInlineSearchInput"', HTML)
        self.assertIn("$('#listingInlineSearchForm')?.addEventListener('submit'", APP)
        self.assertIn("submitSearch($('#listingInlineSearchInput'))", APP)
        self.assertIn("listingInlineSearchInput.value = state.query", APP)

    def test_nearby_mobile_copy_has_inset_padding(self) -> None:
        self.assertIn(".nearby-view-hero {\n    padding-inline: clamp(24px, 8vw, 40px) !important;", CSS)
        self.assertIn(".nearby-view-hero > div:first-child", CSS)

    def test_mobile_menu_is_above_leaflet_map_layers(self) -> None:
        self.assertIn(".mobile-menu-backdrop { z-index: 3000 !important; }", CSS)
        self.assertIn(".mobile-menu { z-index: 3001 !important; }", CSS)
        self.assertIn("body.menu-open .nearby-map .leaflet-container", CSS)

    def test_venue_selector_is_single_select_and_legacy_urls_are_normalized(self) -> None:
        self.assertIn("const selectedVenue = venueValues[0] || null;", APP)
        self.assertIn("state.selectedVenues = selectedVenue ? new Set([selectedVenue]) : new Set();", APP)
        self.assertIn("state.venueDrawerDraft = new Set([name]);", APP)
        self.assertIn("const value = [...selected][0] || '';", APP)
        self.assertIn("搜尋或選擇展演場地", HTML)


if __name__ == "__main__":
    unittest.main()
