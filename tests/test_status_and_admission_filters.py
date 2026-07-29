import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")


class StatusAndAdmissionFilterTests(unittest.TestCase):
    def test_admission_has_independent_section(self):
        self.assertIn('id="listingAdmissionTitle">票價類型</h2>', HTML)
        self.assertIn('id="listingAdmissionOptions"', HTML)
        self.assertIn('ADMISSION', HTML)

    def test_status_and_admission_are_separate(self):
        self.assertIn("admission: 'all'", APP)
        self.assertIn("['free','免費展覽']", APP)
        self.assertIn("['paid','付費展覽']", APP)
        self.assertNotIn("['free','免費展覽']];\n    $('#listingStatusOptions')", APP)

    def test_status_click_toggles_off_on_second_click(self):
        self.assertIn(
            "updateUrl({[key]:currentValue === value ? null : value})",
            APP,
        )

    def test_admission_filters_free_and_paid(self):
        self.assertIn("state.admission === 'free' && !isFree(event)", APP)
        self.assertIn("state.admission === 'paid' && !isPaid(event)", APP)
        self.assertIn("function isPaid(event)", APP)

    def test_legacy_status_free_url_is_migrated(self):
        self.assertIn("const legacyFreeStatus = requestedStatus === 'free'", APP)
        self.assertIn("params.set('admission', 'free')", APP)
        self.assertIn("history.replaceState", APP)

    def test_all_status_buttons_share_exact_active_style(self):
        self.assertIn(
            '.listing-view-hero .status-filter-button.active,',
            CSS,
        )
        self.assertIn('background: var(--ink);', CSS)
        self.assertIn('color: #fff;', CSS)

    def test_status_typography_is_larger(self):
        self.assertIn('font-size: 17px;', CSS)
        self.assertIn('font-size: 12.5px;', CSS)
        self.assertIn('min-height: 39px;', CSS)

    def test_cache_version_is_642(self):
        self.assertIn('assets/styles.css?v=6.5.0', HTML)
        self.assertIn('assets/app.js?v=6.5.0', HTML)


if __name__ == '__main__':
    unittest.main()
