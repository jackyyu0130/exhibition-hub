import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from exhibition_hub.registry import (  # noqa: E402
    enrich_event_with_registry,
    load_venue_registry,
    normalize_region,
    resolve_event_venue,
)


class EventRegistryEnrichmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.venue_registry = load_venue_registry()

    def test_region_normalization(self):
        self.assertEqual(
            normalize_region("台北市"),
            "臺北市",
        )
        self.assertEqual(
            normalize_region("台東縣"),
            "臺東縣",
        )

    def test_contains_match_for_venue_subspace(self):
        match = resolve_event_venue(
            {
                "locationName": (
                    "臺北流行音樂中心文化館"
                ),
                "region": "台北市",
            },
            self.venue_registry,
        )
        self.assertEqual(
            match["status"],
            "matched",
        )
        self.assertEqual(
            match["venue"]["id"],
            "taipei-music-center",
        )

    def test_alias_match_for_songshan(self):
        match = resolve_event_venue(
            {
                "locationName": "松菸",
                "region": "台北市",
            },
            self.venue_registry,
        )
        self.assertEqual(
            match["venue"]["id"],
            "songshan-cultural-park",
        )

    def test_palace_museum_region_disambiguation(self):
        match = resolve_event_venue(
            {
                "locationName": "國立故宮博物院",
                "region": "嘉義縣",
            },
            self.venue_registry,
        )
        self.assertEqual(
            match["venue"]["id"],
            "national-palace-museum-south",
        )

    def test_enrichment_preserves_original_location(self):
        event = {
            "id": "sample",
            "title": "流行音樂故事展",
            "locationName": (
                "臺北流行音樂中心文化館"
            ),
            "region": "台北市",
            "categories": ["音樂", "美術"],
        }
        enriched, diagnostic = (
            enrich_event_with_registry(
                event,
                self.venue_registry,
            )
        )
        self.assertEqual(
            enriched["locationName"],
            event["locationName"],
        )
        self.assertEqual(
            enriched["venueId"],
            "taipei-music-center",
        )
        self.assertEqual(
            enriched["venueIds"],
            ["taipei-music-center"],
        )
        self.assertEqual(
            enriched["regionCanonical"],
            "臺北市",
        )
        self.assertEqual(
            diagnostic["status"],
            "matched",
        )

    def test_multiple_venues_are_preserved(self):
        event = {
            "id": "multi",
            "title": "聯合放映",
            "locationName": "高雄市電影館3樓",
            "venueGroup": (
                "高雄市電影館3樓 | "
                "內惟藝術中心 Reel two 2廳"
            ),
            "region": "高雄市",
            "categories": ["電影"],
        }

        enriched, diagnostic = (
            enrich_event_with_registry(
                event,
                self.venue_registry,
            )
        )

        self.assertEqual(
            diagnostic["status"],
            "matched_multiple",
        )
        self.assertEqual(
            set(enriched["venueIds"]),
            {
                "kaohsiung-film-archive",
                "neiwei-arts-center",
            },
        )
        self.assertEqual(
            len(enriched["venueMatches"]),
            2,
        )
        self.assertEqual(
            enriched["venueId"],
            enriched["venueIds"][0],
        )

    def test_multiple_session_venues_are_preserved(self):
        event = {
            "id": "tour",
            "title": "巡迴節目",
            "locationName": "國家兩廳院",
            "region": "臺北市",
            "sessions": [
                {
                    "locationName": (
                        "臺北市中山堂中正廳"
                    )
                },
                {
                    "locationName": (
                        "苗北藝文中心演藝廳"
                    )
                },
            ],
        }

        enriched, diagnostic = (
            enrich_event_with_registry(
                event,
                self.venue_registry,
            )
        )

        self.assertEqual(
            diagnostic["status"],
            "matched_multiple",
        )
        self.assertEqual(
            set(enriched["venueIds"]),
            {
                "national-theater-and-concert-hall",
                "taipei-zhongshan-hall",
                "miaobei-art-center",
            },
        )


if __name__ == "__main__":
    unittest.main()
