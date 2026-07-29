import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from scraper import normalize_categories  # noqa: E402


HTML = (ROOT / "index.html").read_text(encoding="utf-8")
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
OVERRIDES = json.loads((ROOT / "data" / "curated-overrides.json").read_text(encoding="utf-8"))


class V64MobileMediaTaxonomyTests(unittest.TestCase):
    def test_mobile_drawer_contains_search_category_calendar_and_location(self):
        for identifier in (
            'id="mobileMenu"',
            'id="mobileSearchForm"',
            'id="mobileCategoryOptions"',
            'id="mobileCalendarGrid"',
            'id="mobileLocationSection"',
            'id="mobileRegionPanel"',
        ):
            with self.subTest(identifier=identifier):
                self.assertIn(identifier, HTML)
        self.assertIn('placeholder="搜尋展覽、場館、主辦方、歌手或演員"', HTML)
        self.assertIn("grid-template-columns: repeat(4, minmax(0, 1fr))", CSS)

    def test_mobile_launchers_match_home_and_explore_layout(self):
        self.assertIn('data-open-mobile-filter="category"', HTML)
        self.assertIn('data-open-mobile-filter="calendar"', HTML)
        self.assertIn('data-open-mobile-filter="location"', HTML)

    def test_logo_forces_a_fresh_home_load(self):
        self.assertIn('data-force-home-reload', HTML)
        self.assertIn("window.location.assign(new URL('./', window.location.href).href)", APP)

    def test_cards_show_semantic_category_and_hide_image_type_badges(self):
        self.assertIn("eventDisplayCategory(event)", APP)
        self.assertIn(".card-image .fallback-art-label", CSS)
        self.assertIn("display: none !important", CSS)

    def test_artist_concerts_are_not_grouped_as_general_music(self):
        for title in ("五月天 2026 巡迴演唱會", "米津玄師 2026 WORLD TOUR"):
            categories = normalize_categories("", title, "")
            with self.subTest(title=title):
                self.assertEqual(categories[0], "演唱會")
                self.assertNotIn("音樂", categories)

    def test_music_and_music_theatre_keep_separate_meanings(self):
        classical = normalize_categories("", "貝多芬第九號交響音樂會", "")
        musical = normalize_categories("", "悲慘世界音樂劇", "")
        self.assertEqual(classical[0], "音樂")
        self.assertNotIn("演唱會", classical)
        self.assertEqual(musical[0], "表演")
        self.assertNotIn("音樂", musical)

    def test_anime_max_uses_the_official_huashan_asset_identifier(self):
        record = next(
            item for item in OVERRIDES["overrides"]
            if item.get("title") == "動漫最高祭 Anime Max Festival"
        )
        changes = record["set"]
        self.assertEqual(changes["category"], "動漫")
        self.assertEqual(changes["categories"][0], "動漫")
        self.assertIn("KV_華山官網活動｜1920x1080.jpg", changes["images"][0])
        self.assertNotIn("KV_華山官網活動|1920x1080.jpg", changes["images"][0])


if __name__ == "__main__":
    unittest.main()
