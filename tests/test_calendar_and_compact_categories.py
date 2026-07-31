import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class CalendarAndCompactCategoryTests(unittest.TestCase):
    def test_selected_calendar_date_keeps_dark_text(self):
        self.assertIn(".calendar-day.selected {", CSS)
        selected_block = CSS.split(
            "/* Selected dates use a warm light background",
            1,
        )[1].split(
            "/* Once another date is selected",
            1,
        )[0]
        self.assertIn("background: #f2d8c5", selected_block)
        self.assertIn("color: #352d28", selected_block)
        self.assertNotIn("color: #fff", selected_block)

    def test_today_is_muted_after_another_date_is_selected(self):
        self.assertIn(
            ".calendar-shell.has-selected-date "
            ".calendar-day.today:not(.selected)",
            CSS,
        )
        self.assertIn(
            "classList.toggle('has-selected-date', Boolean(state.date))",
            APP,
        )

    def test_clicking_selected_date_clears_it(self):
        self.assertIn(
            "updateUrl({date:nextDate === state.date ? null : nextDate})",
            APP,
        )

    def test_home_categories_are_six_per_desktop_row(self):
        self.assertIn(
            ".category-strip {",
            CSS,
        )
        self.assertIn(
            "grid-template-columns: repeat(6, minmax(0, 1fr)) !important",
            CSS,
        )

    def test_explore_categories_are_six_circles_per_row(self):
        self.assertIn(
            "grid-template-columns: repeat(6, minmax(62px, 1fr)) !important",
            CSS,
        )
        self.assertIn('class="listing-category-item"', APP)

    def test_only_circle_is_the_category_button(self):
        self.assertIn(
            '<button class="listing-category-option',
            APP,
        )
        item_start = APP.index('class="listing-category-item"')
        button_end = APP.index("</button>", item_start)
        label_start = APP.index(
            "<strong>${escapeHtml(category)}</strong>",
            item_start,
        )
        self.assertGreater(label_start, button_end)
        self.assertNotIn(
            "<strong>",
            APP[item_start:button_end],
        )
        self.assertIn(
            "width: 48px;",
            CSS,
        )
        self.assertIn(
            "height: 48px;",
            CSS,
        )

    def test_frontend_cache_version_is_642(self):
        self.assertIn("assets/styles.css?v=6.5.0-r10.3", HTML)
        self.assertIn("assets/app.js?v=6.5.0-r10.3", HTML)


if __name__ == "__main__":
    unittest.main()
