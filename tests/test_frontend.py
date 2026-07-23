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

    def test_facebook_is_rejected_in_frontend(self):
        self.assertIn("function isFacebookUrl", self.app)
        self.assertIn("isFacebookUrl(sourceUrl)", self.app)

    def test_home_cards_are_square(self):
        self.assertIn(".home-view .exhibition-card .card-image { aspect-ratio: 1 / 1; }", self.css)

    def test_venue_cards_use_horizontal_motion_rail(self):
        self.assertIn('data-scroll-target="venueGrid"', self.html)
        self.assertIn('class="venue-grid" id="venueGrid"', self.html)
        self.assertIn("eventImage", self.app)
        self.assertIn("venue-tile motion-card motion-from-right", self.app)
        self.assertIn("grid-auto-flow: column", self.css)
        self.assertIn("grid-template-rows: repeat(3,142px)", self.css)
        self.assertIn(".slice(0, 36)", self.app)
        self.assertIn('class="venue-section-footer"', self.html)
        self.assertIn("window.__venueImageFallback", self.app)
        self.assertNotIn('venue-placeholder-mark" aria-hidden="true">館', self.app)
        self.assertIn("clip-path: inset(0 0 0 100% round 15px)", self.css)

    def test_city_map_replaces_simple_map_fragment(self):
        self.assertIn('class="paper-city-map"', self.html)
        self.assertIn("CITY ART WALK", self.html)
        self.assertNotIn('class="paper-map-fragment"', self.html)
        self.assertIn('class="city-landmarks"', self.html)
        self.assertIn('class="city-routes"', self.html)
        self.assertNotIn('class="city-blocks"', self.html)
        self.assertNotIn('class="city-compass"', self.html)
        self.assertNotIn('id="cityShadow"', self.html)

    def test_v46_cache_busting(self):
        self.assertIn("assets/styles.css?v=4.6", self.html)
        self.assertIn("assets/app.js?v=4.6", self.html)

    def test_filtered_cards_use_one_stable_animation(self):
        self.assertIn("cardMarkup(event,{revealIndex:index})", self.app)
        self.assertNotIn("cardMarkup(event,{motionIndex:index,revealIndex:index})", self.app)
        self.assertIn("filter-card-reveal-v39", self.css)

    def test_hero_pauses_on_hover_and_rotates_every_fifteen_seconds(self):
        self.assertIn("const HERO_ROTATION_MS = 15000", self.app)
        self.assertIn("pointerenter", self.app)
        self.assertIn("pauseHeroRotation", self.app)
        self.assertIn("resumeHeroRotation", self.app)
        self.assertIn("每 15 秒換一組推薦・懸浮即暫停", self.html)

    def test_nearby_auto_location_radius_distance_and_external_map(self):
        self.assertIn("const NEARBY_RADIUS_KM = 20", self.app)
        self.assertIn("requestLocation({automatic:true})", self.app)
        self.assertIn("distance-badge", self.app)
        self.assertIn("googleMapsDirectionsUrl", self.app)
        self.assertIn("你附近 20 公里", self.html)

    def test_favorites_are_four_square_cards_with_recommendations(self):
        self.assertIn('id="favoritesRecommendations"', self.html)
        self.assertIn('id="favoritesRecommendationRail"', self.html)
        self.assertIn(".favorites-grid {", self.css)
        self.assertIn("grid-template-columns: repeat(4", self.css)
        self.assertIn(".favorites-shell .favorites-grid .card-image { aspect-ratio: 1 / 1; }", self.css)
        self.assertIn("favorite-card-rise-v39", self.css)
        self.assertIn("affinity:", self.app)

    def test_supplied_brand_and_generated_fallback_art_are_used(self):
        self.assertIn("assets/taiwan-exhibition-journal-logo-v10.png", self.html)
        self.assertIn("exhibition-fallback-sprite-v40.png", self.css)
        self.assertIn("fallbackMarkup(event", self.app)

    def test_upcoming_time_dot_is_green(self):
        self.assertIn(".time-dot.upcoming { background: #3f8a62;", self.css)

    def test_v41_editorial_layout_and_copy(self):
        self.assertIn(".brand-logo-frame {\n  width: 210px;", self.css)
        self.assertIn("background-color: #eee8de;", self.css)
        self.assertIn("aspect-ratio: 16 / 10;", self.css)
        self.assertIn("height: 470px;", self.css)
        self.assertIn('class="discover-all-button"', self.html)
        self.assertIn("沿著收藏，遇見下一場", self.html)
        self.assertIn("循著展期，安排下一場相遇", self.html)
        self.assertIn("從一座場館，展開城市漫遊", self.html)
        self.assertIn("讓所在的位置成為起點", self.html)
        self.assertNotIn("關於資料", self.html)

    def test_v41_ticket_details_status_toggle_and_listing_title(self):
        self.assertIn("ticket-watermark", self.app)
        self.assertIn("border: 3px double", self.css)
        self.assertIn(".hero-ticket-card .barcode", self.css)
        self.assertIn("top: 108px;", self.css)
        self.assertIn("state.status === selectedStatus ? 'all' : selectedStatus", self.app)
        self.assertIn("listing-title-separator", self.app)
        self.assertNotIn("state.categories].join('＋')", self.app)
        self.assertIn("font-size: clamp(21px,2.15vw,29px)", self.css)

    def test_v45_copy_footer_hover_motion_and_whole_card_link(self):
        self.assertIn("展覽<br>是城市寫給你的信", self.html)
        self.assertIn("收錄全台展覽與演出。<br>拆封前，先聽聽城市想說些什麼。", self.html)
        self.assertIn("循著今日心緒，遇見一場展覽", self.html)
        self.assertIn("離你不遠，<br>還有這些選擇。", self.html)
        self.assertIn('id="footerRecordCount"', self.html)
        self.assertIn('id="footerVenueCount"', self.html)
        self.assertIn('id="footerUpdatedAt"', self.html)
        self.assertIn(".footer-metric {", self.css)
        self.assertIn("white-space: nowrap;", self.css)
        self.assertIn(".status-pills button:not(.active):hover", self.css)
        self.assertIn(".venue-section.is-in-view .venue-tile:hover", self.css)
        self.assertIn(".featured-block .motion-card", self.css)
        self.assertIn("clip-path: inset(0 0 12% 0 round 16px)", self.css)
        self.assertIn("cardMarkup(event,{wholeCardLink:true,listingIndex:index})", self.app)
        self.assertIn("is-whole-card-link", self.app)
        self.assertIn("data-card-href", self.app)
        self.assertIn("event.target !== wholeCard", self.app)

    def test_v44_hero_split_and_tighter_home_spacing(self):
        self.assertIn("border-left: 1px solid rgba(99,77,54,.2);", self.css)
        self.assertIn("border-top: 0;", self.css)
        self.assertIn(".discovery-panel { padding-top: 48px;", self.css)
        self.assertIn(".featured-block { padding-bottom: 46px;", self.css)
        self.assertIn(".split-feature { padding-bottom: 22px;", self.css)
        self.assertIn("padding-top: 42px;", self.css)
        self.assertIn("padding-bottom: 42px;", self.css)

    def test_v45_full_width_hero_filter_workbench_and_animation_reset(self):
        self.assertIn("height: 470px;", self.css)
        self.assertIn("padding-right: 0;", self.css)
        self.assertIn("width: min(760px,100%);", self.css)
        self.assertIn('class="filter-workbench"', self.html)
        self.assertLess(self.html.index('id="filterResultsSection"'), self.html.index('id="categoryStrip"'))
        self.assertIn(".filter-workbench .filter-results-section.is-visible", self.css)
        self.assertIn("function resetHomeAnimations()", self.app)
        self.assertIn("function replayHomeAnimations()", self.app)
        self.assertIn("if (previousView !== 'home') resetHomeAnimations();", self.app)
        self.assertIn("if (event.persisted) replayHomeAnimations();", self.app)
        self.assertIn("ticketStack.classList.remove('is-changing','is-entering')", self.app)

    def test_v46_warm_palette_full_hero_and_listing_motion(self):
        self.assertIn("--bg: #f3eee6;", self.css)
        self.assertIn("--surface: #fffaf3;", self.css)
        self.assertIn('class="hero-ticket-stage"', self.html)
        self.assertIn("min-height: 584px;", self.css)
        self.assertIn("width: min(700px,calc(100% - 42px));", self.css)
        self.assertIn("border: 0;", self.css)
        self.assertIn("listing-tone-block", self.html)
        self.assertIn(".listing-view.is-animated-in .listing-tone-block", self.css)
        self.assertIn("listing-card-reveal-v46", self.css)
        self.assertIn("listingIndex:index", self.app)
        self.assertIn("function replayListingBlockAnimations()", self.app)
        self.assertIn("if (previousView !== 'listing') replayListingBlockAnimations();", self.app)

    def test_v43_ticket_perforation_back_to_top_and_image_guard(self):
        self.assertIn("ticket-perforation", self.app)
        self.assertIn(".ticket-perforation {", self.css)
        self.assertIn('id="backToTopButton"', self.html)
        self.assertIn(".back-to-top-ticket {", self.css)
        self.assertIn("window.scrollTo({top:0,left:0,behavior:'smooth'})", self.app)
        self.assertIn("function isUsableImageUrl", self.app)
        self.assertIn("window.__validateExhibitionImage", self.app)


if __name__ == "__main__":
    unittest.main()
