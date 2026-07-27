import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "assets" / "app.js").read_text(
    encoding="utf-8"
)
PAYLOAD = json.loads(
    (ROOT / "data" / "exhibitions.enriched.json").read_text(
        encoding="utf-8"
    )
)


class FullFeaturesNoDesignChangeTests(unittest.TestCase):
    def test_candidate_data_is_available(self):
        self.assertEqual(len(PAYLOAD["events"]), 2424)

    def test_enriched_then_legacy_fallback(self):
        enriched = APP.index(
            "data/exhibitions.enriched.json"
        )
        legacy = APP.index("data/exhibitions.json")
        self.assertLess(enriched, legacy)

    def test_standard_region_is_supported(self):
        self.assertIn("raw.regionCanonical", APP)

    def test_standard_and_multiple_venues_are_supported(self):
        for token in (
            "raw.venueName",
            "raw.venueNames",
            "raw.venueIds",
            "raw.unmatchedVenueValues",
            "function eventVenueNames",
            "function eventVenueCompactLabel",
            "eventVenueNames(event).includes(state.venue)",
        ):
            with self.subTest(token=token):
                self.assertIn(token, APP)

    def test_content_type_uses_existing_label_slot(self):
        self.assertIn(
            "eventContentTypeLabel(event)",
            APP,
        )
        self.assertIn(
            "data-content-type=",
            APP,
        )
        self.assertNotIn(
            'class="content-type-badge"',
            APP,
        )

    def test_editorial_status_is_supported(self):
        self.assertIn(
            "event.editorialStatus === 'exclude_review'",
            APP,
        )
        self.assertIn(
            "data-editorial-status=",
            APP,
        )

    def test_unmatched_venue_fallback_is_supported(self):
        self.assertIn(
            "event?.unmatchedVenueValues",
            APP,
        )
        self.assertIn(
            "event?.originalVenueGroup",
            APP,
        )

    def test_existing_layout_contract_is_preserved(self):
        self.assertNotIn("content-type-badge", APP)
        self.assertNotIn("巡迴場館", APP)
        self.assertIn("class=\"card-kicker\"", APP)
        self.assertIn("detailMeta('地點'", APP)

    def test_no_new_touring_row_label_is_added(self):
        self.assertNotIn("巡迴場館", APP)
        self.assertIn("detailMeta('地點'", APP)


if __name__ == "__main__":
    unittest.main()
