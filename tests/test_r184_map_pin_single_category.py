import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class R184MapPinAndSingleCategoryTests(unittest.TestCase):
    def test_map_uses_a_draggable_three_kilometre_search_pin(self) -> None:
        self.assertIn("draggable:true", APP)
        self.assertIn("nearbyPinIcon('origin')", APP)
        self.assertIn("source:'pin'", APP)
        self.assertIn("renderNearby({preserveViewport:true, viewport:nextViewport})", APP)
        self.assertNotIn("state.map.on('click', event =>", APP)
        self.assertIn("拖曳橘色圖釘重新搜尋", HTML)

    def test_venue_markers_open_a_popup_without_changing_the_search_origin(self) -> None:
        self.assertIn("marker.openPopup();", APP)
        self.assertIn("nearbyPinIcon('venue')", APP)
        self.assertNotIn("state.nearbyOrigin = {lat:coordinate.latitude, lng:coordinate.longitude, label:venue.name};", APP)

    def test_address_profiles_repair_outlier_navigation_coordinates(self) -> None:
        self.assertIn("function eventAddressLabel(event)", APP)
        self.assertIn("function eventNavigationCoordinates(event)", APP)
        self.assertIn("state.venueCanonicalProfiles = new Map();", APP)

    def test_category_url_and_state_keep_only_one_selection(self) -> None:
        self.assertIn("state.categories = new Set(categoryValues.slice(0, 1));", APP)
        self.assertIn("if (values[0]) params.set('category', values[0]);", APP)
        self.assertIn("updateUrl({category:state.categories.has(category) ? null : category});", APP)


if __name__ == "__main__":
    unittest.main()
