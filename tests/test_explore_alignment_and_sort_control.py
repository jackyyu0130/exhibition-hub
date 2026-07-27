import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")


class ExploreAlignmentAndSortControlTests(unittest.TestCase):
    def test_explore_magnifier_icon_is_removed(self):
        heading_start = HTML.index(
            '<div class="listing-heading-column">'
        )
        category_start = HTML.index(
            '<section class="listing-category-panel"',
            heading_start,
        )
        heading = HTML[heading_start:category_start]
        self.assertNotIn("view-title-icon", heading)
        self.assertNotIn("<circle cx=\"10\"", heading)

    def test_title_and_status_share_left_alignment(self):
        self.assertIn(
            ".listing-view-hero .view-title-row {",
            CSS,
        )
        self.assertIn(
            "display: block;",
            CSS.split(
                "/* With the decorative magnifier removed",
                1,
            )[1],
        )

    def test_left_and_right_panels_are_equal_height(self):
        section = CSS.split(
            "/* Left and right cards share the same top",
            1,
        )[1]
        self.assertIn(
            ".listing-view-hero {\n  align-items: stretch;",
            section,
        )
        self.assertIn(
            "align-self: stretch;",
            section,
        )
        self.assertIn(
            "height: 100%;",
            section,
        )

    def test_status_and_sort_options_match_request(self):
        expected = [
            ("status:all", "全部展覽"),
            ("status:ongoing", "目前舉辦"),
            ("status:upcoming", "即將舉辦"),
            ("status:ending", "即將結束"),
            ("status:free", "免費展覽"),
            ("sort:title", "名稱排序"),
            ("sort:popular", "熱門排序"),
        ]
        for value, label in expected:
            with self.subTest(value=value):
                self.assertIn(
                    f'<option value="{value}">{label}</option>',
                    HTML,
                )

        self.assertNotIn(">推薦排序</option>", HTML)
        self.assertNotIn(">最新開展</option>", HTML)

    def test_popular_sort_uses_recommendation_score(self):
        self.assertIn(
            "recommendationScore(b) - recommendationScore(a)",
            APP,
        )
        self.assertIn(
            "if (state.sort === 'title')",
            APP,
        )

    def test_control_can_change_status_or_sort(self):
        self.assertIn(
            "const [mode, value] = "
            "String(event.target.value).split(':')",
            APP,
        )
        self.assertIn(
            "status:value === 'all' ? null : value",
            APP,
        )
        self.assertIn(
            "updateUrl({sort:value})",
            APP,
        )

    def test_cache_version_is_54(self):
        self.assertIn("assets/styles.css?v=5.4", HTML)
        self.assertIn("assets/app.js?v=5.4", HTML)


if __name__ == "__main__":
    unittest.main()
