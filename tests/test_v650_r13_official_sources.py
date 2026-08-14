import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from exhibition_hub.collectors.base import CollectorSource
from exhibition_hub.collectors.official_sites import (
    TaipeiExpoParkExpoDomeCollector,
    TwtcHall1Collector,
    _clean_images,
)


REGISTRY = json.loads((ROOT / "data" / "source_registry.json").read_text(encoding="utf-8"))
VENUES = json.loads((ROOT / "data" / "venues.json").read_text(encoding="utf-8"))
MATRIX = json.loads((ROOT / "data" / "northern_venue_matrix.json").read_text(encoding="utf-8"))
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")


def source(source_id):
    item = next(value for value in REGISTRY["sources"] if value["id"] == source_id)
    return CollectorSource.from_mapping(item)


class V650R13OfficialSourceTests(unittest.TestCase):
    def test_blank_and_html_candidates_are_not_treated_as_images(self):
        detail_url = "https://example.test/News_Photo_Content.aspx?n=247&s=4499"
        image_url = "https://cdn.example.test/event/poster.jpg"
        self.assertEqual(
            _clean_images(["", detail_url, image_url], detail_url),
            [image_url],
        )

    def test_twtc_listing_only_accepts_hall_1_detail_links(self):
        html = """
        <table><tr><td>07/03 ~ 07/06</td><td>
          <a href="https://event.example/official">2026 台灣國際創意文具展</a>
          <a href="exhibition_more.aspx?p=menu1&id=28187">more</a>
        </td><td>展昭國際企業股份有限公司</td><td>02-12345678</td></tr>
        <tr><td>08/01</td><td><a href="exhibition_more.aspx?p=menu3&id=999">錯誤三館活動</a></td></tr>
        </table>
        """
        records, pages = TwtcHall1Collector.parse_listing(
            html,
            base_url="https://www.twtc.org.tw/exhibition?p=menu1",
            detail_patterns=[r"^/exhibition_more\.aspx$"],
        )
        self.assertEqual(pages, [])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["title"], "2026 台灣國際創意文具展")
        self.assertEqual(records[0]["eventUrl"], "https://event.example/official")
        self.assertIn("p=menu1", records[0]["detailUrl"])
        self.assertEqual(records[0]["organizer"], "展昭國際企業股份有限公司")

    def test_twtc_unlinked_title_does_not_fall_through_to_organizer(self):
        html = """
        <table><tr><td>07/04 ~ 07/04</td><td>
          104人力銀行 2026職涯博覽會
          <a href="exhibition_more.aspx?p=menu1&id=28459">more</a>
        </td><td><a href="http://invalid.test">一零四資訊科技股份有限公司</a></td>
        <td>02-29126104</td><td>世貿一館</td></tr></table>
        """
        records, _ = TwtcHall1Collector.parse_listing(
            html,
            base_url="https://www.twtc.org.tw/exhibition?p=menu1",
            detail_patterns=[r"^/exhibition_more\.aspx$"],
        )
        self.assertEqual(records[0]["title"], "104人力銀行 2026職涯博覽會")
        self.assertEqual(records[0]["eventUrl"], "")

    def test_twtc_detail_uses_official_gregorian_dates_and_hall(self):
        detail = """
        <html><head><link rel="canonical" href="https://www.twtc.org.tw/exhibition_more.aspx?p=menu1&id=28187"></head>
        <body><h2>2026 台灣國際創意文具展</h2>
        <p>展覽館別：一館1F</p><p>展出日期：2026/07/03 ~ 2026/07/06</p>
        <p>展出時間：10:00 ~ 18:00</p></body></html>
        """
        result = TwtcHall1Collector.parse_detail(
            detail,
            detail_url="https://www.twtc.org.tw/exhibition_more.aspx?p=menu1&id=28187",
            source=source("twtc-hall-1"),
            listing={"title": "2026 台灣國際創意文具展", "organizer": "展昭國際企業股份有限公司"},
        )
        self.assertEqual(result["startDate"], "2026-07-03")
        self.assertEqual(result["endDate"], "2026-07-06")
        self.assertEqual(result["venueName"], "臺北世貿一館")
        self.assertEqual(result["subVenueName"], "一館1F")

    def test_expo_dome_listing_converts_roc_dates_and_rejects_other_venues(self):
        html = """
        <a href="News_Photo_Content.aspx?n=247&s=4499" title="Nature Show 自然展">
          <img src="https://ws.expopark.taipei/poster@710x470.png">
          <span>Nature Show 自然展</span><i>115-11-14 ~ 115-11-15</i><i>爭艷館</i>
        </a>
        <a href="News_Photo_Content.aspx?n=247&s=4500" title="其他廣場活動">
          <span>其他廣場活動</span><i>115-12-01 ~ 115-12-02</i><i>圓山廣場</i>
        </a>
        """
        records, _ = TaipeiExpoParkExpoDomeCollector.parse_listing(
            html,
            base_url="https://www.expopark.taipei/news_exhibition.aspx?_CSN=43&n=247&sms=9029",
            detail_patterns=[r"^/News_Photo_Content\.aspx$"],
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["title"], "Nature Show 自然展")
        self.assertEqual(records[0]["startDate"], "2026-11-14")
        self.assertEqual(records[0]["endDate"], "2026-11-15")
        self.assertTrue(records[0]["imageUrl"].endswith("poster@710x470.png"))

    def test_registry_activates_two_sources_and_keeps_hall_3_retired(self):
        by_id = {item["id"]: item for item in REGISTRY["sources"]}
        for source_id in ("twtc-hall-1", "taipei-expo-park-expo-dome"):
            with self.subTest(source_id=source_id):
                self.assertEqual(by_id[source_id]["status"], "active")
                self.assertTrue(by_id[source_id]["enabled"])
                self.assertTrue(by_id[source_id]["publicationPolicy"]["publishEnabled"])
                self.assertEqual(by_id[source_id]["networkPolicy"]["failurePolicy"], "isolate_source")
        self.assertEqual(by_id["twtc-hall-3"]["status"], "retired")
        self.assertFalse(by_id["twtc-hall-3"]["enabled"])
        self.assertFalse(by_id["twtc-hall-3"]["publicationPolicy"]["publishEnabled"])

    def test_social_media_sources_remain_disabled(self):
        forbidden = ("facebook.com", "instagram.com")
        for item in REGISTRY["sources"]:
            urls = " ".join([
                str(item.get("officialUrl") or ""),
                str(item.get("listingUrl") or ""),
                *[str(value) for value in item.get("listingUrls") or []],
            ]).lower()
            if any(domain in urls for domain in forbidden):
                self.assertFalse(item.get("enabled"), item["id"])

    def test_venue_aliases_cover_both_traditional_variants(self):
        public = next(item for item in VENUES["venues"] if item["id"] == "taipei-expo-park-expo-dome")
        matrix = next(item for item in MATRIX["venues"] if item["id"] == "expo-park-expo-dome")
        expected = {"花博公園爭艷館", "花博公園爭豔館", "花博爭艷館", "花博爭豔館", "爭艷館", "爭豔館"}
        self.assertTrue(expected.issubset({public["name"], *public["aliases"]}))
        self.assertTrue(expected.issubset({matrix["name"], *matrix["aliases"]}))

    def test_home_metadata_uses_confirmed_title_and_stable_favicons(self):
        title = "台灣展覽誌｜全台展覽與演出資訊"
        self.assertIn(f"<title>{title}</title>", HTML)
        self.assertIn(f"const DEFAULT_PAGE_TITLE = '{title}'", APP)
        for marker in (
            'href="https://twexhibition.com/"',
            'href="/favicon.ico"',
            'href="/favicon-48.png"',
            'href="/apple-touch-icon.png"',
            'content="https://twexhibition.com/logo-512.png"',
        ):
            self.assertIn(marker, HTML)
        for filename in ("favicon.ico", "favicon-48.png", "apple-touch-icon.png", "logo-512.png"):
            self.assertTrue((ROOT / filename).is_file())


if __name__ == "__main__":
    unittest.main()
