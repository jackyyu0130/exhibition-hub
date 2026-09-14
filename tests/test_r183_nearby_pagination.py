import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "assets/app.js").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class R183NearbyPaginationTests(unittest.TestCase):
    def test_load_more_appends_without_restarting_grid_reveal(self):
        self.assertIn("listingGrid.insertAdjacentHTML('beforeend'", APP)
        self.assertIn("state.listingRenderedCount", APP)
        self.assertIn("listingGrid.classList.add('is-in-view')", APP)
        self.assertIn("loadMore.disabled", APP)

    def test_map_pin_becomes_nearby_search_origin(self):
        self.assertIn("draggable:true", APP)
        self.assertIn("state.nearbyOrigin = {lat:point.lat, lng:point.lng, label:'地圖選取位置', source:'pin'}", APP)
        self.assertIn("nearestVenues(200, origin ? NEARBY_RADIUS_KM : Infinity, origin)", APP)
        self.assertIn("function resetNearbyOrigin()", APP)
        self.assertIn('id="nearbyResetOriginButton"', HTML)

    def test_public_build_includes_geocode_cache(self):
        build = (ROOT / "scripts/build_pages_site.py").read_text(encoding="utf-8")
        self.assertIn('"data/geocode-cache.json"', build)


if __name__ == "__main__":
    unittest.main()
