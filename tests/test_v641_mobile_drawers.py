import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")


class V641MobileDrawerTests(unittest.TestCase):
    def test_drawers_are_outside_the_backdrop_filtered_header(self):
        header_end = HTML.index("</header>")
        menu_start = HTML.index('id="mobileMenu"')
        backdrop_start = HTML.index('id="mobileMenuBackdrop"')
        self.assertLess(header_end, menu_start)
        self.assertLess(header_end, backdrop_start)

    def test_primary_mobile_navigation_sits_between_search_and_filters(self):
        search = HTML.index('id="mobileSearchForm"')
        navigation = HTML.index('class="mobile-menu-nav"')
        categories = HTML.index('id="mobileCategorySection"')
        self.assertLess(search, navigation)
        self.assertLess(navigation, categories)

    def test_mobile_categories_follow_the_explore_category_order(self):
        order = re.search(r"const CATEGORY_ORDER = \[(.*?)\];", APP, re.S)
        self.assertIsNotNone(order)
        self.assertIn(
            "state.mobileCategoriesExpanded ? CATEGORY_ORDER : CATEGORY_ORDER.slice(0, 4)",
            APP,
        )
        self.assertTrue(order.group(1).strip().startswith("'演唱會','快閃店','動漫','美術'"))

    def test_open_drawers_lock_and_restore_the_page_viewport(self):
        for marker in (
            "function lockViewport(owner)",
            "function unlockViewport(owner)",
            "lockViewport('mobile-menu')",
            "unlockViewport('mobile-menu')",
            "lockViewport('venue-selector')",
            "unlockViewport('venue-selector')",
            "document.body.style.position = 'fixed'",
            "window.scrollTo({top:restoreY, left:0, behavior:'auto'})",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, APP)

    def test_drawer_surfaces_block_horizontal_swipes_and_scroll_chaining(self):
        for marker in (
            "overflow-x: hidden;",
            "overscroll-behavior: contain;",
            "touch-action: pan-y;",
            "max-width: 100vw;",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, CSS)
        self.assertIn("html.overlay-open", CSS)
        self.assertIn("overflow-x: clip;", CSS)

    def test_venue_footer_belongs_to_the_drawer_layout_not_the_viewport(self):
        footer_rule = re.search(r"\.venue-selector-footer\s*\{(.*?)\}", CSS, re.S)
        self.assertIsNotNone(footer_rule)
        self.assertIn("position: static", footer_rule.group(1))
        self.assertIn("flex: 0 0 auto", footer_rule.group(1))
        self.assertNotIn("position: fixed", footer_rule.group(1))
        self.assertIn("flex: 1 1 auto", CSS)

    def test_mobile_filter_sections_use_distinct_warm_surfaces(self):
        for selector in (
            "#mobileCategorySection",
            "#mobileCalendarSection",
            "#mobileLocationSection",
        ):
            with self.subTest(selector=selector):
                self.assertIn(selector, CSS)

    def test_favicon_assets_use_stable_root_urls_and_include_touch_icon(self):
        for marker in (
            'href="/favicon-48.png"',
            'href="/apple-touch-icon.png"',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, HTML)
        for filename in ("favicon-48.png", "apple-touch-icon.png"):
            with self.subTest(filename=filename):
                self.assertTrue((ROOT / filename).is_file())


if __name__ == "__main__":
    unittest.main()
