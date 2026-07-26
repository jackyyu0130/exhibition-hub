import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from exhibition_hub.classifiers import (  # noqa: E402
    classify_event,
)


class ContentTypeClassifierTests(unittest.TestCase):
    def assert_types(
        self,
        title,
        primary,
        included,
    ):
        result = classify_event({"title": title})
        self.assertEqual(
            result["contentType"],
            primary,
        )

        for content_type in included:
            self.assertIn(
                content_type,
                result["contentTypes"],
            )

    def test_comic_expo(self):
        self.assert_types(
            "2026 台北漫畫博覽會",
            "expo",
            ("expo", "pop_culture"),
        )

    def test_concert(self):
        self.assert_types(
            "某某世界巡迴演唱會",
            "concert",
            ("concert",),
        )

    def test_music_festival(self):
        self.assert_types(
            "夏日海岸音樂祭",
            "music_festival",
            ("music_festival",),
        )

    def test_independent_solo_exhibition(self):
        self.assert_types(
            "在城市之間－林某某個展",
            "art_exhibition",
            ("art_exhibition",),
        )

    def test_character_popup(self):
        self.assert_types(
            "人氣角色期間限定快閃店",
            "popup",
            ("popup", "pop_culture"),
        )

    def test_market(self):
        self.assert_types(
            "週末插畫文創市集",
            "market",
            ("market", "pop_culture"),
        )

    def test_generic_exhibition_fallback(self):
        result = classify_event(
            {"title": "沒有明確分類的文化活動"}
        )
        self.assertEqual(
            result["contentTypes"],
            ["exhibition"],
        )


if __name__ == "__main__":
    unittest.main()
