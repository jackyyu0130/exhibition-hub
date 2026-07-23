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

    def test_all_facebook_hosts_and_generic_ticket_home_are_rejected(self):
        self.assertTrue(scraper.is_facebook_group_url("https://www.facebook.com/groups/12345"))
        self.assertTrue(scraper.is_facebook_url("https://www.facebook.com/events/12345"))
        self.assertTrue(scraper.is_facebook_url("https://scontent-tpe1-1.xx.fbcdn.net/poster.jpg"))
        self.assertTrue(scraper.is_facebook_url("https://fb.me/example"))
        self.assertFalse(scraper.is_facebook_url("https://www.opentix.life/event/example"))
        self.assertTrue(scraper.is_generic_ticketing_url("https://kktix.com/"))
        self.assertFalse(scraper.is_generic_ticketing_url("https://demo.kktix.cc/events/real-event"))

    def test_related_pages_never_return_facebook(self):
        page = """
        <a href="https://www.facebook.com/events/123">Facebook 活動</a>
        <a href="https://fb.me/example">臉書</a>
        <a href="https://www.opentix.life/event/real-show">購票</a>
        """
        result = scraper.related_page_urls(page, "https://cloud.culture.tw/event/1")
        self.assertIn("https://www.opentix.life/event/real-show", result)
        self.assertFalse(any(scraper.is_facebook_url(url) for url in result))

    def test_concatenated_culture_cloud_image_url_is_repaired(self):
        broken = "https://cloud.culture.twhttps://cloud.culture.tw/e_new_upload/poster.jpg"
        self.assertEqual(
            scraper.normalize_url(broken),
            "https://cloud.culture.tw/e_new_upload/poster.jpg",
        )

    def test_url_with_prose_appended_to_hostname_does_not_abort_update(self):
        malformed = "https://lib.miaoli.gov.tw網站查詢，或洽本案聯絡人教育處圖資科丁小姐，電話：037-338227"
        self.assertEqual(scraper.normalize_url(malformed), "https://lib.miaoli.gov.tw")
        self.assertEqual(scraper.normalize_url("https://example.com／錯誤說明：請洽承辦人"), "https://example.com")

    def test_invalid_netloc_returns_empty_instead_of_raising(self):
        self.assertEqual(scraper.normalize_url("https://：完全錯誤的網址"), "")

    def test_source_url_can_be_recovered_from_description(self):
        result = scraper.source_url({
            "description": "完整介紹：https://artemperor.tw/tidbits/19988",
        })
        self.assertEqual(result, "https://artemperor.tw/tidbits/19988")

    def test_semantic_dedupe_merges_different_provider_ids(self):
        first = {
            "id": "culture-a",
            "title": "《吟遊於母星之間》曾詩涵個展",
            "startDate": "2026-06-20",
            "endDate": "2026-08-01",
            "locationName": "活動名稱誤作場館",
            "venueGroup": "活動名稱誤作場館",
            "sourceUrl": "",
            "images": [],
            "categories": ["美術"],
            "category": "美術",
            "description": "較短介紹",
            "firstSeenAt": "2026-07-01T00:00:00+08:00",
        }
        second = {
            **first,
            "id": "gallery-b",
            "locationName": "阿波羅畫廊",
            "venueGroup": "阿波羅畫廊",
            "sourceUrl": "https://artemperor.tw/tidbits/19988",
            "sourceUrlVerified": True,
            "sourceUrlMatchScore": 1.0,
            "description": "完整展覽介紹" * 30,
        }
        merged = scraper.merge_records([first, second], [])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["sourceUrl"], second["sourceUrl"])
        self.assertEqual(merged[0]["venueGroup"], "阿波羅畫廊")

    def test_venue_image_falls_back_to_current_exhibition_art(self):
        event = {
            "title": "展覽",
            "venueGroup": "測試美術館",
            "startDate": "2026-01-01",
            "endDate": "2030-12-31",
            "images": ["https://example.com/current-exhibition.jpg"],
            "image": "https://example.com/current-exhibition.jpg",
        }
        result = scraper.venue_images([event], existing={}, allow_fetch=False)
        self.assertEqual(result["測試美術館"], event["image"])

    @patch.object(scraper.requests, "get")
    def test_facebook_page_is_not_requested(self, mock_get):
        self.assertEqual(scraper.discover_page_metadata("https://www.facebook.com/events/123"), {})
        mock_get.assert_not_called()

    def test_editorial_exclusions(self):
        excluded = [
            {"title": "夏日藝術工作坊", "category": "美術"},
            {"title": "城市美學", "category": "講座"},
            {"title": "社區小聚成果活動", "unit": "幸福里辦公處"},
            {"title": "地方展覽", "sourceUrl": "https://facebook.com/groups/987"},
            {"title": "親子館外展服務：繪本說故事"},
            {"title": "員林市立圖書館昆蟲觀察課"},
            {"title": "南投縣藝池藝術協會－自然與人文對話"},
            {"title": "115年度頭份市客語說故事活動（115年7月-2場次）", "unit": "頭份市公所"},
            {"title": "全國學生南北管音樂比賽－初賽與複賽", "category": "競賽"},
            {"title": "地方藝文成果活動", "unit": "梧棲區公所"},
            {"title": "幸福社區學員成果展", "unit": "幸福社區發展協會"},
        ]
        self.assertTrue(all(scraper.is_excluded_record(item) for item in excluded))
        self.assertFalse(scraper.is_excluded_record({"title": "國際藝術博覽會", "unit": "文化局"}))
        self.assertFalse(scraper.is_excluded_record({"title": "漫畫博覽會", "unit": "中華動漫出版同業協進會"}))
        self.assertFalse(scraper.is_excluded_record({"title": "台北國際寵物用品博覽會", "unit": "展昭國際企業"}))
        self.assertFalse(scraper.is_excluded_record({"title": "今夜漫才大舞台", "unit": "卡米地喜劇俱樂部"}))
        self.assertFalse(scraper.is_excluded_record({"title": "世界合唱比賽行前音樂會", "category": "音樂"}))
        self.assertFalse(scraper.is_excluded_record({"title": "科博館《古代人說故事》南屯遺址文物展", "unit": "國立自然科學博物館"}))
        self.assertFalse(scraper.is_excluded_record({"title": "琴韻飄鄉巡迴音樂會（社區活動中心）", "unit": "閩聲愛樂協會"}))
        relabeled = scraper.editorialize_categories({
            "title": "寫生比賽得獎作品展",
            "categories": ["競賽", "美術"],
        })
        self.assertEqual(relabeled["category"], "美術")
        self.assertNotIn("競賽", relabeled["categories"])

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
        competition_labels = [
            event.get("title")
            for event in self.payload["events"]
            if event.get("category") == "競賽" or "競賽" in (event.get("categories") or [])
        ]
        self.assertEqual(competition_labels, [])

    def test_published_data_has_no_generic_ticket_home(self):
        offenders = [event.get("sourceUrl") for event in self.payload["events"] if scraper.is_generic_ticketing_url(event.get("sourceUrl"))]
        self.assertEqual(offenders, [])

    def test_published_data_contains_no_facebook_urls(self):
        offenders = []
        for event in self.payload["events"]:
            urls = [event.get("sourceUrl"), event.get("image"), *(event.get("images") or [])]
            if any(scraper.is_facebook_url(url) for url in urls if url):
                offenders.append(event.get("title"))
        offenders.extend(
            name for name, url in self.payload.get("venueImages", {}).items()
            if scraper.is_facebook_url(url)
        )
        self.assertEqual(offenders, [])

    def test_curated_source_and_semantic_duplicate_cleanup(self):
        matches = [
            event for event in self.payload["events"]
            if "吟遊於母星之間" in event.get("title", "")
        ]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["sourceUrl"], "https://artemperor.tw/tidbits/19988")
        self.assertEqual(matches[0]["venueGroup"], "阿波羅畫廊")

    def test_published_images_have_no_concatenated_scheme(self):
        offenders = [
            url
            for event in self.payload["events"]
            for url in event.get("images", [])
            if "https://cloud.culture.twhttps://" in url
        ]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
