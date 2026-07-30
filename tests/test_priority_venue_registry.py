import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from exhibition_hub.registry import (  # noqa: E402
    load_venue_registry,
    resolve_venue,
)


class PriorityVenueRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_venue_registry()

    def test_priority_venue_aliases_resolve(self):
        expected = {
            "桃園展演中心展演廳": "taoyuan-arts-center",
            "高雄市文化中心至德堂": (
                "kaohsiung-cultural-center"
            ),
            "高雄市文化中心至善廳": (
                "kaohsiung-cultural-center"
            ),
            "臺中市葫蘆墩文化中心演奏廳": (
                "taichung-huludun-cultural-center"
            ),
            "宜蘭演藝廳": "yilan-performing-arts-hall",
            "嘉義縣表演藝術中心演藝廳": (
                "chiayi-county-performing-arts-center"
            ),
            "新竹縣政府文化局演藝廳": (
                "hsinchu-county-cultural-bureau-hall"
            ),
            "彰化藝術館": "changhua-art-museum",
            "高雄市音樂館": "kaohsiung-city-music-hall",
            "屏東演藝廳音樂廳": (
                "pingtung-performing-arts-hall"
            ),
            "基隆表演藝術中心演藝廳": (
                "keelung-performing-arts-center"
            ),
            "澎湖縣演藝廳": "penghu-performing-arts-hall",
            "嘉義市政府文化局音樂廳": (
                "chiayi-city-cultural-bureau-music-hall"
            ),
            "臺北市政大樓親子劇場": (
                "taipei-city-hall-family-theater"
            ),
            "台北偶戲館黑箱劇場": (
                "taipei-puppetry-museum"
            ),
            "北投中心新村-C1 藝棧": (
                "beitou-heart-village"
            ),
            "水源劇場": "water-source-theater",
            "蒙藏文化館": (
                "mongolian-tibetan-cultural-center"
            ),
            "金門縣文化局": (
                "kinmen-cultural-affairs-bureau"
            ),
            "原住民族文化發展中心": (
                "taiwan-indigenous-culture-development-center"
            ),
        }

        for alias, expected_id in expected.items():
            with self.subTest(alias=alias):
                venue = resolve_venue(alias, self.registry)
                self.assertIsNotNone(venue)
                self.assertEqual(venue["id"], expected_id)

    def test_placeholders_are_not_registered_as_venues(self):
        placeholders = {
            "台北市｜場館資料整理中",
            "台中市｜場館資料整理中",
            "高雄市｜場館資料整理中",
            "大溪區（桃園市）",
        }

        for value in placeholders:
            with self.subTest(value=value):
                self.assertIsNone(
                    resolve_venue(value, self.registry)
                )


if __name__ == "__main__":
    unittest.main()
