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
        event,
        primary,
        included,
    ):
        result = classify_event(event)
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
            {
                "title": "2026 台北漫畫博覽會",
                "categories": ["動漫"],
            },
            "expo",
            ("expo", "pop_culture"),
        )

    def test_concert(self):
        self.assert_types(
            {"title": "某某世界巡迴演唱會"},
            "concert",
            ("concert",),
        )

    def test_music_festival(self):
        self.assert_types(
            {"title": "夏日海岸音樂祭"},
            "music_festival",
            ("music_festival",),
        )

    def test_independent_solo_exhibition(self):
        self.assert_types(
            {"title": "在城市之間－林某某個展"},
            "art_exhibition",
            ("art_exhibition",),
        )

    def test_character_popup(self):
        self.assert_types(
            {"title": "人氣角色期間限定快閃店"},
            "popup",
            ("popup", "pop_culture"),
        )

    def test_market(self):
        self.assert_types(
            {"title": "週末插畫文創市集"},
            "market",
            ("market", "pop_culture"),
        )

    def test_music_story_exhibition_is_not_concert(self):
        result = classify_event(
            {
                "title": "唱 我們的歌 流行音樂故事展",
                "description": (
                    "展區內含演唱會體驗區，"
                    "介紹臺灣流行音樂。"
                ),
                "categories": ["音樂", "美術"],
            }
        )
        self.assertEqual(
            result["contentType"],
            "art_exhibition",
        )

    def test_film_festival(self):
        self.assert_types(
            {
                "title": "城市紀錄片影展",
                "categories": ["電影"],
            },
            "film_screening",
            ("film_screening",),
        )

    def test_course_is_flagged(self):
        result = classify_event(
            {"title": "2026 春季社教成人班"}
        )
        self.assertEqual(
            result["editorialStatus"],
            "exclude_review",
        )
        self.assertIn(
            "possible_course_or_workshop",
            result["editorialFlags"],
        )

    def test_online_exhibition(self):
        result = classify_event(
            {
                "title": "定格微光線上攝影展",
                "locationName": "線上攝影展",
                "region": "其他地區",
            }
        )
        self.assertEqual(
            result["eventFormat"],
            "online",
        )
        self.assertEqual(
            result["editorialStatus"],
            "needs_review",
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
