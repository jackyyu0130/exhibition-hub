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

    def test_sort_options_match_request(self):
        expected = [
            ("recommended", "推薦排序"),
            ("popular", "熱門排序"),
            ("title", "名稱排序"),
            ("time", "時間排序"),
        ]
        for value, label in expected:
            with self.subTest(value=value):
                self.assertIn(
                    f'<option value="{value}">{label}</option>',
                    HTML,
                )

        self.assertNotIn('option value="status:', HTML)
        self.assertNotIn(">最新開展</option>", HTML)
        self.assertNotIn(">即將結束</option>", HTML)

    def test_recommended_and_popular_are_different(self):
        self.assertIn(
            "recommendationScore(b) - recommendationScore(a)",
            APP,
        )
        self.assertIn(
            "(Number(b.hitRate) || 0) - (Number(a.hitRate) || 0)",
            APP,
        )
        self.assertIn(
            "if (state.sort === 'popular')",
            APP,
        )

    def test_time_sort_orders_nearest_period_first(self):
        self.assertIn("function eventTimeSortKey(event)", APP)
        self.assertIn("function compareTimeSort(a, b)", APP)
        self.assertIn("result.sort(compareTimeSort)", APP)
        self.assertIn(
            "if (startTime <= today && endTime >= today)",
            APP,
        )
        self.assertIn(
            "if (startTime > today)",
            APP,
        )

    def test_control_only_changes_sort(self):
        self.assertIn(
            "const value = String(event.target.value)",
            APP,
        )
        self.assertIn(
            "sort:value === 'recommended' ? null : value",
            APP,
        )
        self.assertNotIn(
            "String(event.target.value).split(':')",
            APP,
        )

    def test_cache_version_is_642(self):
        self.assertIn("assets/styles.css?v=6.5.0-r6", HTML)
        self.assertIn("assets/app.js?v=6.5.0-r6", HTML)


if __name__ == "__main__":
    unittest.main()
