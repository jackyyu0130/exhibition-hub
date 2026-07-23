import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("exhibition_scraper", ROOT / "scripts" / "scraper.py")
scraper = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = scraper
SPEC.loader.exec_module(scraper)


class FakeResponse:
    def __init__(self, text: str, url: str = "https://www.opentix.life/event/example"):
        self.text = text
        self.url = url
        self.headers = {"content-type": "text/html; charset=utf-8"}

    def raise_for_status(self):
        return None


class ScraperPolicyTests(unittest.TestCase):
    def test_title_match_accepts_matching_official_page(self):
        score = scraper.title_match_score(
            "藍寶石大歌廳《秀場傳奇》故事展",
            "藍寶石大歌廳－秀場傳奇故事展｜OPENTIX",
        )
        self.assertGreaterEqual(score, 0.8)

    def test_title_match_rejects_unrelated_ticket_page(self):
        score = scraper.title_match_score("台灣設計展", "KKTIX 活動報名平台")
        self.assertLess(score, 0.42)

    def test_facebook_groups_and_generic_ticket_home_are_rejected(self):
        self.assertTrue(scraper.is_facebook_group_url("https://www.facebook.com/groups/12345"))
        self.assertTrue(scraper.is_generic_ticketing_url("https://kktix.com/"))
        self.assertFalse(scraper.is_generic_ticketing_url("https://demo.kktix.cc/events/real-event"))

    def test_editorial_exclusions(self):
        excluded = [
            {"title": "夏日藝術工作坊", "category": "美術"},
            {"title": "城市美學", "category": "講座"},
            {"title": "社區小聚成果活動", "unit": "幸福里辦公處"},
            {"title": "地方展覽", "sourceUrl": "https://facebook.com/groups/987"},
            {"title": "親子館外展服務：繪本說故事"},
            {"title": "員林市立圖書館昆蟲觀察課"},
            {"title": "南投縣藝池藝術協會－自然與人文對話"},
        ]
        self.assertTrue(all(scraper.is_excluded_record(item) for item in excluded))
        self.assertFalse(scraper.is_excluded_record({"title": "國際藝術博覽會", "unit": "文化局"}))

    @patch.object(scraper, "image_url_responds", return_value=True)
    @patch.object(scraper.requests, "get")
    def test_opentix_metadata_extracts_matching_image_and_description(self, mock_get, _mock_image):
        page = """
        <html><head>
          <meta property="og:title" content="山海之間－當代藝術特展｜OPENTIX">
          <meta property="og:image" content="https://cdn.example.com/banner-original.jpg">
          <meta property="og:description" content="山海之間以當代藝術回望島嶼地景，集結多位藝術家共同展出。">
        </head><body>山海之間－當代藝術特展</body></html>
        """
        mock_get.return_value = FakeResponse(page)
        result = scraper.discover_page_metadata(
            "https://www.opentix.life/event/example",
            title="山海之間－當代藝術特展",
        )
        self.assertTrue(result["titleMatched"])
        self.assertEqual(result["images"][0], "https://cdn.example.com/banner-original.jpg")
        self.assertIn("當代藝術", result["description"])

    @patch.object(scraper, "discover_page_metadata")
    def test_mismatched_ticket_url_is_replaced_by_matching_official_url(self, discover):
        wrong = {
            "checkedUrl": "https://kktix.com/",
            "titleMatched": False,
            "titleMatchScore": 0.05,
            "relatedUrls": ["https://cloud.culture.tw/frontsite/event/123"],
        }
        correct = {
            "checkedUrl": "https://cloud.culture.tw/frontsite/event/123",
            "titleMatched": True,
            "titleMatchScore": 0.92,
            "images": ["https://cloud.culture.tw/poster.jpg"],
            "description": "正確的官方活動介紹。" * 8,
        }
        discover.side_effect = [wrong, correct]
        result = scraper.discover_event_metadata("https://kktix.com/", "正確活動")
        self.assertEqual(result["sourceUrlRejected"], "https://kktix.com/")
        self.assertEqual(result["bestSourceUrl"], correct["checkedUrl"])
        self.assertTrue(result["images"])


class PublishedDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads((ROOT / "data" / "exhibitions.json").read_text(encoding="utf-8"))

    def test_published_data_respects_exclusions(self):
        offenders = [event.get("title") for event in self.payload["events"] if scraper.is_excluded_record(event)]
        self.assertEqual(offenders, [])

    def test_published_data_has_no_generic_ticket_home(self):
        offenders = [event.get("sourceUrl") for event in self.payload["events"] if scraper.is_generic_ticketing_url(event.get("sourceUrl"))]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
