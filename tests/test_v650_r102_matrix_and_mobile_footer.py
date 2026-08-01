import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")


class V650R102MatrixAndMobileFooterTests(unittest.TestCase):
    def test_confirmed_four_region_matrices_have_expected_counts(self):
        expected = {
            "north": ("venue_matrix_north.json", 123),
            "west": ("venue_matrix_west.json", 44),
            "south": ("venue_matrix_south.json", 49),
            "east": ("venue_matrix_east.json", 20),
        }
        total = 0
        ids = set()
        for region_group, (filename, count) in expected.items():
            payload = json.loads((ROOT / "data" / filename).read_text(encoding="utf-8"))
            self.assertEqual(payload["regionGroup"], region_group)
            self.assertEqual(payload["venueCount"], count)
            self.assertEqual(len(payload["venues"]), count)
            total += count
            for venue in payload["venues"]:
                self.assertTrue(venue["confirmed"])
                self.assertNotIn(venue["id"], ids)
                ids.add(venue["id"])
        self.assertEqual(total, 236)

    def test_combined_matrix_matches_confirmed_workbook(self):
        payload = json.loads((ROOT / "data" / "taiwan_venue_matrix.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["stats"], {
            "totalVenues": 236,
            "north": 123,
            "west": 44,
            "south": 49,
            "east": 20,
        })
        self.assertEqual(len(payload["venues"]), 236)
        self.assertIn("全台場館矩陣與1-9階段總檢視_V1.1.xlsx", payload["confirmationSource"])

    def test_frontend_loads_confirmed_nationwide_matrix_after_existing_registries(self):
        self.assertIn("fetch('data/taiwan_venue_matrix.json'", APP)
        self.assertIn("const confirmedTaiwanVenues = normalizeMatrixVenues", APP)
        self.assertIn("state.venueRegistry = [...stableVenues, ...northernVenues, ...confirmedTaiwanVenues]", APP)
        self.assertIn("state.venueRegistry.filter(registry => registry?.confirmed)", APP)
        self.assertIn("unavailable = item.count === 0", APP)
        self.assertIn("尚無展演", APP)

    def test_mobile_all_three_tickets_show_journal_footer_and_barcode(self):
        for selector in (
            ".hero-ticket-slot-1 .ticket-footer",
            ".hero-ticket-slot-2 .ticket-footer",
            ".hero-ticket-slot-3 .ticket-footer",
        ):
            with self.subTest(selector=selector):
                self.assertIn(selector, CSS)
        self.assertIn("display: flex !important;", CSS)
        self.assertIn(".hero-ticket-slot-3 .ticket-footer .barcode", CSS)

    def test_social_icons_share_instagram_visual_box(self):
        self.assertIn('.footer-social-icon[aria-label="Facebook"] svg,', CSS)
        self.assertIn('.footer-social-icon[aria-label="Instagram"] svg,', CSS)
        self.assertIn('.footer-social-icon[aria-label="Threads"] img {', CSS)
        self.assertIn("width: 18px !important;", CSS)
        self.assertIn("height: 18px !important;", CSS)

    def test_region_batches_match_confirmed_matrix_coverage(self):
        payload = json.loads((ROOT / "data" / "source_batches.json").read_text(encoding="utf-8"))
        groups = {item["name"]: item["coverageRegions"] for item in payload["regionGroups"]}
        self.assertIn("宜蘭縣", groups["北部"])
        self.assertIn("連江縣", groups["北部"])
        self.assertIn("金門縣", groups["西部"])
        self.assertIn("澎湖縣", groups["南部"])
        self.assertEqual(groups["東部"], ["花蓮縣", "臺東縣"])


if __name__ == "__main__":
    unittest.main()
