import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from exhibition_hub.registry import load_venue_registry, resolve_event_venue


class VenueAliasSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_venue_registry()

    def test_weiwuying_opera_house_does_not_match_taichung(self):
        match = resolve_event_venue(
            {
                "locationName": "衛武營國家藝術文化中心歌劇院",
                "region": "高雄市",
            },
            self.registry,
        )
        self.assertEqual(match["status"], "matched")
        self.assertEqual(
            match["candidateVenueIds"],
            ["weiwuying"],
        )

    def test_taichung_named_theater_still_matches(self):
        match = resolve_event_venue(
            {
                "locationName": "臺中國家歌劇院中劇院",
                "region": "臺中市",
            },
            self.registry,
        )
        self.assertEqual(match["status"], "matched")
        self.assertEqual(
            match["candidateVenueIds"],
            ["national-taichung-theater"],
        )


if __name__ == "__main__":
    unittest.main()
