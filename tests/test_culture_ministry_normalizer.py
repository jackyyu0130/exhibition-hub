import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from exhibition_hub.normalizers.culture_ministry import (  # noqa: E402
    CULTURE_SOURCE_ID,
    CULTURE_SOURCE_NAME,
    CultureNormalizationError,
    clean_html,
    detect_region,
    normalize_boolean,
    normalize_culture_event,
    normalize_culture_records,
    normalize_date,
    normalize_datetime,
    normalize_float,
    normalize_sessions,
    normalize_url,
)


class CultureNormalizationHelperTests(unittest.TestCase):
    def test_clean_html_removes_tags_and_keeps_text(self):
        result = clean_html(
            "<p>第一段</p><br><strong>第二段</strong>"
        )

        self.assertEqual(result, "第一段 第二段")

    def test_normalize_date_supports_common_formats(self):
        self.assertEqual(
            normalize_date("2026/07/28"),
            "2026-07-28",
        )
        self.assertEqual(
            normalize_date("2026-7-8"),
            "2026-07-08",
        )
        self.assertEqual(
            normalize_date("2026/07/28 09:00:00"),
            "2026-07-28",
        )
        self.assertEqual(normalize_date(""), "")

    def test_normalize_datetime_preserves_time(self):
        self.assertEqual(
            normalize_datetime("2026/07/28 09:30:00"),
            "2026-07-28T09:30:00",
        )
        self.assertEqual(
            normalize_datetime("2026/07/28"),
            "2026-07-28",
        )

    def test_normalize_float_handles_empty_and_invalid_values(self):
        self.assertEqual(
            normalize_float("24.157234"),
            24.157234,
        )
        self.assertIsNone(normalize_float(""))
        self.assertIsNone(normalize_float("unknown"))
        self.assertIsNone(normalize_float(None))

    def test_normalize_boolean_supports_culture_flags(self):
        self.assertTrue(normalize_boolean("Y"))
        self.assertTrue(normalize_boolean("是"))
        self.assertFalse(normalize_boolean("N"))
        self.assertFalse(normalize_boolean("否"))
        self.assertIsNone(normalize_boolean(""))
        self.assertIsNone(normalize_boolean("unknown"))

    def test_normalize_url_only_accepts_http_urls(self):
        self.assertEqual(
            normalize_url("https://example.com/event"),
            "https://example.com/event",
        )
        self.assertEqual(
            normalize_url(
                [
                    "",
                    "https://example.com/ticket",
                ]
            ),
            "https://example.com/ticket",
        )
        self.assertEqual(
            normalize_url("javascript:alert(1)"),
            "",
        )
        self.assertEqual(normalize_url(""), "")

    def test_detect_region_normalizes_taiwan_aliases(self):
        self.assertEqual(
            detect_region("臺北市中正區"),
            "臺北市",
        )
        self.assertEqual(
            detect_region("台中市北區館前路一號"),
            "臺中市",
        )
        self.assertEqual(
            detect_region("高雄市鼓山區"),
            "高雄市",
        )
        self.assertEqual(
            detect_region("地址未提供"),
            "",
        )


class CultureSessionNormalizationTests(unittest.TestCase):
    def test_normalize_sessions_converts_show_info(self):
        sessions = normalize_sessions(
            [
                {
                    "time": "2026/07/28 09:00:00",
                    "endTime": "2026/07/28 17:00:00",
                    "location": "臺中市北區館前路一號",
                    "locationName": "人類文化廳二樓",
                    "onSales": "Y",
                    "price": "全票100元",
                    "latitude": "24.157234",
                    "longitude": "120.66606",
                }
            ]
        )

        self.assertEqual(len(sessions), 1)

        session = sessions[0]

        self.assertEqual(
            session["startTime"],
            "2026-07-28T09:00:00",
        )
        self.assertEqual(
            session["endTime"],
            "2026-07-28T17:00:00",
        )
        self.assertEqual(
            session["locationName"],
            "人類文化廳二樓",
        )
        self.assertTrue(session["onSales"])
        self.assertEqual(
            session["latitude"],
            24.157234,
        )
        self.assertEqual(
            session["longitude"],
            120.66606,
        )

    def test_invalid_show_info_items_are_ignored(self):
        sessions = normalize_sessions(
            [
                "invalid",
                None,
                123,
            ]
        )

        self.assertEqual(sessions, [])

    def test_empty_show_info_returns_empty_list(self):
        self.assertEqual(normalize_sessions(None), [])
        self.assertEqual(normalize_sessions({}), [])
        self.assertEqual(normalize_sessions([]), [])


class CultureEventNormalizationTests(unittest.TestCase):
    def build_record(self):
        return {
            "UID": "culture-001",
            "title": "測試文化展覽",
            "category": "6",
            "descriptionFilterHtml": (
                "<p>這是一場測試展覽。</p>"
                "<p>歡迎前往參觀。</p>"
            ),
            "startDate": "2026/07/28",
            "endDate": "2026/12/31",
            "imageUrl": "https://example.com/image.jpg",
            "sourceWebPromote": (
                "https://example.com/exhibition"
            ),
            "sourceWebName": "官方活動網站",
            "webSales": "https://example.com/tickets",
            "editModifyDate": "2026/07/25 12:30:00",
            "masterUnit": [
                "主辦單位A",
            ],
            "showUnit": [
                "主辦單位A",
                "主辦單位B",
            ],
            "otherUnit": "協辦單位C",
            "showInfo": [
                {
                    "time": "2026/07/28 09:00:00",
                    "endTime": "2026/12/31 17:00:00",
                    "location": "台中市北區館前路一號",
                    "locationName": "測試展覽館",
                    "onSales": "Y",
                    "price": "全票100元，半票70元",
                    "latitude": "24.157234",
                    "longitude": "120.66606",
                }
            ],
            "_feedCategory": "6",
            "_collectorSource": "culture-ministry",
        }

    def test_complete_record_is_normalized(self):
        event = normalize_culture_event(
            self.build_record()
        )

        self.assertEqual(
            event["id"],
            "culture-ministry:culture-001",
        )
        self.assertEqual(
            event["externalId"],
            "culture-001",
        )
        self.assertEqual(
            event["title"],
            "測試文化展覽",
        )
        self.assertEqual(
            event["description"],
            "這是一場測試展覽。 歡迎前往參觀。",
        )
        self.assertEqual(
            event["startDate"],
            "2026-07-28",
        )
        self.assertEqual(
            event["endDate"],
            "2026-12-31",
        )
        self.assertEqual(
            event["locationName"],
            "測試展覽館",
        )
        self.assertEqual(
            event["venueGroup"],
            "測試展覽館",
        )
        self.assertEqual(
            event["address"],
            "台中市北區館前路一號",
        )
        self.assertEqual(
            event["region"],
            "臺中市",
        )
        self.assertEqual(
            event["latitude"],
            24.157234,
        )
        self.assertEqual(
            event["longitude"],
            120.66606,
        )
        self.assertEqual(
            event["price"],
            "全票100元，半票70元",
        )
        self.assertEqual(
            event["image"],
            "https://example.com/image.jpg",
        )
        self.assertEqual(
            event["images"],
            [
                "https://example.com/image.jpg",
            ],
        )
        self.assertEqual(
            event["sourceUrl"],
            "https://example.com/exhibition",
        )
        self.assertEqual(
            event["ticketUrl"],
            "https://example.com/tickets",
        )
        self.assertEqual(
            event["sourceId"],
            CULTURE_SOURCE_ID,
        )
        self.assertEqual(
            event["source"],
            CULTURE_SOURCE_NAME,
        )
        self.assertEqual(
            event["sourceName"],
            "官方活動網站",
        )
        self.assertEqual(
            event["organizers"],
            [
                "主辦單位A",
                "主辦單位B",
                "協辦單位C",
            ],
        )
        self.assertEqual(len(event["sessions"]), 1)
        self.assertEqual(
            event["lastModified"],
            "2026-07-25T12:30:00",
        )

    def test_missing_optional_fields_are_allowed(self):
        record = {
            "UID": "culture-002",
            "title": "缺少圖片與網址的展覽",
            "category": "6",
            "startDate": "2026/08/01",
            "endDate": "2026/08/31",
            "showInfo": [],
        }

        event = normalize_culture_event(record)

        self.assertEqual(event["image"], "")
        self.assertEqual(event["images"], [])
        self.assertEqual(event["sourceUrl"], "")
        self.assertEqual(event["ticketUrl"], "")
        self.assertEqual(event["sessions"], [])
        self.assertEqual(event["region"], "")
        self.assertEqual(event["organizers"], [])

    def test_invalid_optional_urls_are_removed(self):
        record = self.build_record()
        record["imageUrl"] = "file:///tmp/image.jpg"
        record["sourceWebPromote"] = "not-a-url"
        record["webSales"] = "javascript:alert(1)"

        event = normalize_culture_event(record)

        self.assertEqual(event["image"], "")
        self.assertEqual(event["images"], [])
        self.assertEqual(event["sourceUrl"], "")
        self.assertEqual(event["ticketUrl"], "")

    def test_missing_uid_is_rejected(self):
        record = self.build_record()
        record.pop("UID")

        with self.assertRaises(
            CultureNormalizationError
        ):
            normalize_culture_event(record)

    def test_missing_title_is_rejected(self):
        record = self.build_record()
        record["title"] = "   "

        with self.assertRaises(
            CultureNormalizationError
        ):
            normalize_culture_event(record)

    def test_batch_normalization_isolates_invalid_records(self):
        valid_record = self.build_record()
        invalid_record = {
            "UID": "missing-title",
            "title": "",
        }

        normalized, errors = normalize_culture_records(
            [
                valid_record,
                invalid_record,
            ]
        )

        self.assertEqual(len(normalized), 1)
        self.assertEqual(
            normalized[0]["externalId"],
            "culture-001",
        )
        self.assertEqual(len(errors), 1)
        self.assertIn(
            "missing title",
            errors[0],
        )


if __name__ == "__main__":
    unittest.main()
