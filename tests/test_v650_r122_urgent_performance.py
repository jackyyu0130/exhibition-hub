import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
VERSION = (ROOT / "VERSION.txt").read_text(encoding="utf-8")


class R122UrgentPerformanceTests(unittest.TestCase):
    def test_compact_arrows_are_outside_ticket_area(self):
        self.assertIn("width: 42px !important;", CSS)
        self.assertIn("font-size: 25px !important;", CSS)
        self.assertIn("left: clamp(-28px, -1.7vw, -16px) !important;", CSS)
        self.assertIn("right: clamp(-28px, -1.7vw, -16px) !important;", CSS)

    def test_venue_matching_is_cached(self):
        self.assertIn("venueRegistryNormalizedIndex: new Map()", APP)
        self.assertIn("eventVenueRecordCache: new WeakMap()", APP)
        self.assertIn("state.eventVenueRecordCache.has(event)", APP)
        self.assertIn("state.venueNameMatchCache.has(normalized)", APP)

    def test_home_venue_grid_is_deferred_and_bounded(self):
        self.assertIn("function scheduleHomeVenueGrid()", APP)
        self.assertIn("requestIdleCallback(render, {timeout: 650})", APP)
        self.assertIn(".slice(0, 12)", APP)
        self.assertIn('grid.dataset.rendered = \'true\'', APP)

    def test_venue_route_paints_feedback_before_render(self):
        self.assertIn("function navigateWithFeedback", APP)
        self.assertGreaterEqual(APP.count("requestAnimationFrame(() =>"), 2)
        self.assertIn("internalLink.matches('.venue-tile')", APP)
        self.assertIn("body.is-route-pending::before", CSS)

    def test_initial_listing_render_is_small(self):
        self.assertIn("window.matchMedia('(max-width: 760px)').matches ? 12 : 24", APP)
        self.assertNotIn("state.listingRenderLimit = 72;", APP)

    def test_reveal_waits_for_a_real_painted_frame(self):
        self.assertIn("function queueScrollReveal(target)", APP)
        self.assertTrue("threshold:.14" in APP or "threshold:.08" in APP)
        self.assertTrue("rootMargin:'0px 0px -8% 0px'" in APP or "rootMargin:'0px 0px -3% 0px'" in APP)

    def test_release_marker(self):
        self.assertTrue("Performance patch: P2" in VERSION or "Performance patch: P3" in VERSION)
        self.assertTrue("STABLE2 P2" in APP.splitlines()[0] or "STABLE2 P3" in APP.splitlines()[0])


if __name__ == "__main__":
    unittest.main()
