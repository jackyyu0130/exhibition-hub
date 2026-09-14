from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class R187NearbyPinPlacementTests(unittest.TestCase):
    def test_current_location_stays_separate_from_the_search_pin(self) -> None:
        self.assertIn("const origin = state.nearbyOrigin || state.userLocation;", APP)
        self.assertIn("if (state.userLocation) {", APP)
        self.assertNotIn("if (state.userLocation && state.nearbyOrigin) {", APP)
        self.assertIn("L.circleMarker([state.userLocation.lat, state.userLocation.lng]", APP)
        self.assertIn("你目前的位置會保留在地圖上", APP)

    def test_default_pin_is_a_top_left_control_below_the_zoom_control(self) -> None:
        self.assertIn("const control = L.control({position:'topleft'});", APP)
        self.assertIn("control.addTo(state.map);", APP)
        self.assertIn("nearby-pin-control", APP)
        self.assertIn("container.hidden = Boolean(state.nearbyOrigin);", APP)
        self.assertIn(".nearby-pin-control.leaflet-bar", CSS)
        self.assertRegex(
            CSS,
            r"\.nearby-pin-control\.leaflet-bar\s*\{[\s\S]*?clear:\s*both;",
        )
        self.assertIn("touch-action: none", CSS)

    def test_search_pin_uses_the_supplied_flat_yellow_and_lavender_artwork(self) -> None:
        self.assertIn('rect x="13.5" y="26" width="5" height="12" rx="2.5" fill="#9695ad"', APP)
        self.assertIn('circle cx="16" cy="14" r="14" fill="#ffdf43"', APP)
        self.assertIn("The movable/search pin follows the supplied flat yellow-and-lavender artwork", CSS)
        self.assertIn(".nearby-map-pin-origin .nearby-map-pin-shell", CSS)

    def test_pin_can_be_picked_placed_and_dragged_again(self) -> None:
        self.assertIn("nearbyPinPlacementArmed: false", APP)
        self.assertIn("setNearbyPinPlacementArmed(true);", APP)
        self.assertIn("if (!state.nearbyPinPlacementArmed) return;", APP)
        self.assertIn("state.map.on('click', handleNearbyMapClick);", APP)
        self.assertIn("pointerdown", APP)
        self.assertIn("mouseEventToLatLng(upEvent)", APP)
        self.assertIn("draggable:true", APP)
        self.assertIn("searchPin.on('dragend'", APP)

    def test_desktop_double_click_places_without_also_zooming(self) -> None:
        self.assertIn("window.matchMedia('(hover: hover) and (pointer: fine)').matches", APP)
        self.assertIn("doubleClickZoom:!desktopPinPlacement", APP)
        self.assertIn("state.map.on('dblclick', handleNearbyMapDoubleClick);", APP)
        self.assertRegex(
            APP,
            r"function handleNearbyMapDoubleClick\(event\)[\s\S]*?placeNearbySearchPin\(event\?\.latlng\);",
        )

    def test_every_placement_uses_one_validated_viewport_preserving_path(self) -> None:
        placement = re.search(
            r"function placeNearbySearchPin\(latlng,[\s\S]*?\n  \}",
            APP,
        )
        self.assertIsNotNone(placement)
        source = placement.group(0)
        self.assertIn("Number.isFinite(Number(point.lat))", source)
        self.assertIn("Number.isFinite(Number(point.lng))", source)
        self.assertIn("source:'pin'", source)
        self.assertIn("renderNearby({preserveViewport:true, viewport:nextViewport})", source)
        self.assertGreaterEqual(APP.count("placeNearbySearchPin("), 5)

    def test_late_geolocation_does_not_discard_a_newer_pin_placement(self) -> None:
        self.assertIn("const pinRevisionAtRequest = state.nearbyPinRevision;", APP)
        self.assertIn("const pinMovedWhileLocating = state.nearbyPinRevision !== pinRevisionAtRequest;", APP)
        self.assertIn("if (!pinMovedWhileLocating) {", APP)

    def test_subtitle_and_accessible_map_label_explain_all_controls(self) -> None:
        self.assertIn('id="nearbyPinInstructions"', HTML)
        self.assertIn("拖曳黃色圖釘重新搜尋", HTML)
        self.assertIn("左上角黃色圖釘拿取", HTML)
        self.assertIn("電腦版可直接雙擊地圖放置", HTML)
        self.assertIn('aria-describedby="nearbyPinInstructions"', HTML)
        self.assertIn("電腦版可雙擊地圖放置圖釘", HTML)


if __name__ == "__main__":
    unittest.main()
