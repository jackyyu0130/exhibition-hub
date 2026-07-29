import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class NorthernVenueMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads((ROOT / "data" / "northern_venue_matrix.json").read_text(encoding="utf-8"))
        cls.venues = cls.payload["venues"]

    def test_covers_all_northern_regions(self):
        self.assertEqual(
            set(self.payload["coverageRegions"]),
            {"臺北市","新北市","基隆市","桃園市","新竹市","新竹縣","宜蘭縣"},
        )

    def test_venue_ids_are_unique(self):
        ids = [item["id"] for item in self.venues]
        self.assertEqual(len(ids), len(set(ids)))

    def test_world_trade_and_nangang_are_separate(self):
        ids = {item["id"] for item in self.venues}
        self.assertIn("taipei-world-trade-center-hall-1", ids)
        self.assertIn("taipei-nangang-exhibition-center-hall-1", ids)
        self.assertIn("taipei-nangang-exhibition-center-hall-2", ids)
        self.assertIn("taipei-international-convention-center", ids)

    def test_core_music_venues_exist(self):
        names = {item["name"] for item in self.venues}
        for name in [
            "臺北小巨蛋","臺北大巨蛋","臺北流行音樂中心表演廳",
            "Zepp New Taipei","NUZONE","藝富文創展演館／杰克音樂",
        ]:
            self.assertIn(name, names)

    def test_source_strategy_is_declared(self):
        allowed = set(self.payload["sourceStrategies"])
        self.assertTrue(all(item["sourceStrategy"] in allowed for item in self.venues))

if __name__ == "__main__":
    unittest.main()
