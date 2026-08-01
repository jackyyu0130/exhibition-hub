from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
CURATION = (
    ROOT / "scripts" / "exhibition_hub" / "curation.py"
).read_text(encoding="utf-8")


class R1102VenueCountReconciliationTests(unittest.TestCase):
    def test_cache_version_is_r1102(self):
        self.assertIn("assets/styles.css?v=6.5.0-r11.0.2", HTML)
        self.assertIn("assets/app.js?v=6.5.0-r11.0.2", HTML)

    def test_all_venue_fields_are_matching_candidates(self):
        self.assertIn("function eventVenueCandidateValues(event)", APP)
        for field in (
            "event?.venueNames",
            "event?.unmatchedVenueValues",
            "event?.venueName",
            "event?.originalVenueGroup",
            "event?.originalLocationName",
            "event?.venueGroup",
            "event?.locationName",
        ):
            self.assertIn(field, APP)

    def test_public_venue_id_survives_normalization(self):
        self.assertIn(
            "publicVenueId: String(raw.publicVenueId || '').trim()",
            APP,
        )

    def test_confirmed_registry_wins(self):
        block = APP.split(
            "function venueRegistryRecord(name)", 1
        )[1].split(
            "function eventCanonicalVenueRecords(event)", 1
        )[0]
        self.assertIn("if (direct?.confirmed) return direct", block)
        self.assertNotIn("if(direct) return direct", block)

    def test_canonical_ids_are_resolved_first(self):
        block = APP.split(
            "function eventCanonicalVenueRecords(event)", 1
        )[1].split(
            "function eventCanonicalVenueNames(event)", 1
        )[0]
        self.assertIn("event?.publicVenueId", block)
        self.assertIn("state.venueRegistryById", block)
        self.assertIn("eventVenueCandidateValues(event)", block)

    def test_catalog_counts_records_directly(self):
        block = APP.split(
            "function rebuildVenueCatalogCache()", 1
        )[1].split("function venueCatalog()", 1)[0]
        self.assertIn(
            "const canonicalRecords = eventCanonicalVenueRecords(event)",
            block,
        )
        self.assertNotIn(
            "const registry = venueRegistryRecord(eventName)",
            block,
        )
        self.assertIn("matchedEventCount", block)
        self.assertIn("unmatchedEventCount", block)

    def test_curation_persists_canonical_ids(self):
        self.assertIn(
            'event["venueId"] = canonical_venue_id',
            CURATION,
        )
        self.assertIn(
            'event["venueIds"] = list(dict.fromkeys',
            CURATION,
        )


if __name__ == "__main__":
    unittest.main()
