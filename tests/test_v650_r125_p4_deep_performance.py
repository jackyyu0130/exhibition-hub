import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
VERSION = (ROOT / "VERSION.txt").read_text(encoding="utf-8")


class R125P4DeepPerformanceTests(unittest.TestCase):
    def test_hero_intro_uses_stable_geometry_and_staged_transitions(self):
        self.assertIn("function scheduleHeroIntro(stack)", APP)
        self.assertIn("is-intro-pending", APP)
        self.assertIn("is-intro-playing", APP)
        self.assertIn("waitForHeroTypography", APP)
        p4 = CSS[CSS.index("STABLE2 P4"):]
        self.assertIn("calc(var(--hero-x, 0%) + 11%)", p4)
        self.assertIn("transition-duration: 1.08s, 1.34s", p4)
        self.assertIn("animation: none !important", p4)

    def test_noncritical_home_sections_hydrate_after_hero(self):
        self.assertIn("function scheduleCalmHomeTask", APP)
        self.assertIn("delayMs:1750", APP)
        self.assertIn("delayMs:2050", APP)
        self.assertIn("delayMs:2350", APP)
        self.assertIn("scheduleHomeVenueGrid({delayMs:2650", APP)
        self.assertIn("homeContentHydrated", APP)

    def test_home_media_is_decoded_serially_before_reveal(self):
        self.assertIn("function prepareSectionMedia", APP)
        self.assertIn("prepareSectionMedia(list, {limit:3, concurrency:1})", APP)
        self.assertIn("prepareSectionMedia(grid, {limit:12, concurrency:1})", APP)
        self.assertIn("waitForScrollIdle(700)", APP)
        self.assertIn("queueScrollRevealWhenReady", APP)

    def test_home_venue_cards_reuse_prebuilt_event_index(self):
        self.assertIn("homeVenueEventIndex: new Map()", APP)
        self.assertIn("state.homeVenueEventIndex = homeVenueEventIndex", APP)
        self.assertIn("const eventsByVenue = state.homeVenueEventIndex", APP)

    def test_home_cards_do_not_materialise_during_scroll(self):
        p4 = CSS[CSS.index("STABLE2 P4"):]
        self.assertIn(".home-view .nearby-mini-card", p4)
        self.assertIn(".home-view .venue-section .venue-tile", p4)
        self.assertIn("content-visibility: visible !important", p4)
        self.assertIn("contain: paint style !important", p4)

    def test_leaflet_is_removed_from_home_critical_path(self):
        self.assertNotIn('<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>', HTML)
        self.assertNotIn('<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">', HTML)
        self.assertIn("function ensureLeafletAssets()", APP)
        self.assertIn("script.async = true", APP)
        self.assertIn("map-runtime-placeholder", APP)

    def test_font_and_analytics_loading_avoid_intro_contention(self):
        self.assertIn("display=optional", HTML)
        self.assertIn("requestIdleCallback(load,{timeout:2600})", HTML)

    def test_scroll_control_classes_update_only_when_state_changes(self):
        self.assertIn("state.headerScrolledState !== headerScrolled", APP)
        self.assertIn("state.backToTopState !== backToTopVisible", APP)
        self.assertIn("state.scrollClassActive", APP)

    def test_release_and_cache_mark_p4(self):
        self.assertIn("assets/styles.css?v=6.5.0-r12-stable2-p5a", HTML)
        self.assertIn("assets/app.js?v=6.5.0-r12-stable2-p5a", HTML)
        self.assertIn("Interaction patch: P5-A", VERSION)
        self.assertIn("STABLE2 P5-A", APP.splitlines()[0])


if __name__ == "__main__":
    unittest.main()
