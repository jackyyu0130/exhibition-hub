import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from exhibition_hub.curation import apply_verified_event_corrections, public_categories, sanitize_public_price

APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
VERSION = (ROOT / "VERSION.txt").read_text(encoding="utf-8")
MATRIX = json.loads((ROOT / "data" / "taiwan_venue_matrix.json").read_text(encoding="utf-8"))


class P5BIntegratedRepairTests(unittest.TestCase):
    def test_hero_intro_overrides_idle_transition_none(self):
        self.assertIn(".hero-ticket-stage .hero-ticket-stack.is-intro-playing .hero-ticket-slide", CSS)
        self.assertIn(".hero-ticket-stack.is-intro-playing.is-intro-pending", CSS)
        self.assertIn("transition-duration: 1.72s, 2.12s !important;", CSS)
        self.assertIn(".hero-ticket-slot-2 { transition-delay: .06s !important; }", CSS)
        self.assertIn(".hero-ticket-slot-3 { transition-delay: .38s !important; }", CSS)
        self.assertIn(".hero-ticket-slot-1 { transition-delay: .70s !important; }", CSS)

    def test_hero_transition_is_attached_before_pending_pose_is_removed(self):
        start = APP.index("function scheduleHeroIntro(stack)")
        end = APP.index("function renderHeroTickets", start)
        block = APP[start:end]
        non_reduced = block[block.index("stack.classList.add('is-intro-playing')"):]
        self.assertLess(non_reduced.index("classList.add('is-intro-playing')"), non_reduced.index("classList.remove('is-intro-pending')"))
        self.assertIn("await nextFrame()", block)
        p5b = CSS[CSS.index("STABLE2 P5-B"):]
        self.assertIn("transition-duration: 1.65s, 2.05s", p5b)
        self.assertIn("+ clamp(310px, 42vw, 690px)", p5b)

    def test_featured_and_date_cards_mount_before_deferred_nearby_work(self):
        render_home = APP[APP.index("function renderHome()") : APP.index("function renderCategoryStrip()")]
        self.assertLess(render_home.index("featuredRail.innerHTML = featured.length"), render_home.index("delayMs:800"))
        self.assertLess(render_home.index("upcomingList.innerHTML"), render_home.index("delayMs:800"))
        self.assertNotIn("home-section-placeholder", render_home.split("delayMs:800")[0])
        p5b = CSS[CSS.index("STABLE2 P5-B"):]
        self.assertIn(".featured-block .motion-card", p5b)
        self.assertIn("[data-split-reveal] > .time-column", p5b)

    def test_related_exhibitions_have_visible_working_controls(self):
        self.assertIn('id="detailRelatedRail"', APP)
        self.assertIn('data-scroll-target="detailRelatedRail"', APP)
        self.assertIn("detail-related-heading", CSS)
        self.assertIn("detail-related-rail", CSS)
        self.assertIn("target.scrollTo", APP)

    def test_home_venue_rail_has_three_pages_and_overflow(self):
        self.assertIn(".slice(0, 36)", APP)
        self.assertIn("#venueGrid.venue-grid", CSS)
        self.assertIn("grid-template-rows: repeat(3", CSS)
        self.assertIn("overflow-x: auto !important", CSS)
        self.assertIn('data-scroll-target="venueGrid"', HTML)

    def test_implausible_and_date_fragment_prices_are_suppressed(self):
        verified = apply_verified_event_corrections({"title": "natori ONE-MAN LIVE TOUR ‘Koshin (March)’ in Taipei", "price": "NT$10"})
        low, low_reason = sanitize_public_price({"title": "其他 ONE-MAN LIVE TOUR", "price": "NT$10"})
        malformed, malformed_reason = sanitize_public_price({"title": "兒童藝術節", "price": "NT$1–2,026"})
        valid, valid_reason = sanitize_public_price({
            "title": "巡迴演唱會",
            "price": "早鳥 NT$1,888、原價 NT$2,088；2026/8/1 起恢復原價",
        })
        self.assertIn("NT$4,200", verified["price"])
        self.assertEqual(verified["startDate"], "2026-08-08")
        self.assertEqual(verified["endDate"], "2026-08-09")
        self.assertEqual(low, "票價請見活動頁面")
        self.assertEqual(low_reason, "unsupported_low_amount")
        self.assertEqual(malformed, "票價請見活動頁面")
        self.assertEqual(malformed_reason, "date_fragment")
        self.assertIn("1,888", valid)
        self.assertIsNone(valid_reason)

    def test_declared_music_performance_beats_description_history_words(self):
        categories = public_categories({
            "title": "夢與緋光",
            "description": "跨時代交響樂團演出，曲目包含 Sibelius Violin Concerto 與 Dvořák Symphony No. 8",
            "category": "音樂",
            "categories": ["音樂", "美術", "演唱會"],
            "contentTypes": ["performance"],
        })
        self.assertEqual(categories[0], "音樂")

    def test_jacks_studio_and_other_high_confidence_districts_are_corrected(self):
        records = {item["id"]: item for item in MATRIX["venues"]}
        jack = records["yi-fu-wen-chuang-zhan-yan-guan-jie-ke-yin-le"]
        self.assertEqual(jack["name"], "杰克音樂 Jack's studio")
        self.assertEqual(jack["district"], "萬華區")
        self.assertIn("昆明街76號", jack["address"])
        self.assertEqual(records["cheng-shi-wu-tai"]["district"], "松山區")
        self.assertEqual(records["hui-xiang-yin-le-yi-wen-zhan-yan-kong-jian"]["district"], "中區")
        self.assertEqual(records["gao-xiong-liu-xing-yin-le-zhong-xin"]["district"], "鹽埕區")

    def test_nearby_search_reuses_venue_and_geocode_coordinates(self):
        self.assertIn("venueCoordinateIndex: new Map()", APP)
        self.assertIn("function eventCoordinates(event)", APP)
        self.assertIn("state.venueCoordinateIndex.get", APP)
        self.assertIn("state.geocodeCache", APP)
        self.assertIn("addressDistrictKey", APP)
        self.assertIn("state.venueRegistry.forEach(registry =>", APP)
        self.assertIn("_coordinatePrecision", APP)

    def test_cache_and_version_identify_p5b(self):
        self.assertIn("r12-stable2-p5b", HTML)
        self.assertIn("Integrated repair: P5-B", VERSION)


if __name__ == "__main__":
    unittest.main()
