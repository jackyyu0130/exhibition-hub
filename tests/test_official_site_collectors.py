import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from exhibition_hub.collectors.base import CollectorSource
from exhibition_hub.collectors.official_sites import (
    TaipeiPerformingArtsCenterCollector,
)


class OfficialSiteCollectorParserTests(unittest.TestCase):
    def setUp(self):
        self.source = CollectorSource.from_mapping({
            "id": "taipei-performing-arts-center",
            "name": "臺北表演藝術中心",
            "status": "active",
            "enabled": True,
            "parser": "official_site_configured",
            "officialUrl": "https://tpac.org.taipei/",
            "listingUrl": "https://tpac.org.taipei/program",
            "trustLevel": "official",
            "refreshHours": 12,
            "detailPathPatterns": [r"^/program/\d+/?$"],
            "venueName": "臺北表演藝術中心",
            "regionCanonical": "臺北市",
            "address": "臺北市士林區劍潭路1號",
            "subVenueKeywords": ["大劇院", "藍盒子"],
        })

    def test_listing_parser_collects_detail_link(self):
        html = """
        <a href="/program/123"><img src="/poster.jpg" alt="測試舞台劇">
        測試舞台劇 2026-08-10 - 2026-08-12</a>
        """
        records, _ = TaipeiPerformingArtsCenterCollector.parse_listing(
            html,
            base_url="https://tpac.org.taipei/program",
            detail_patterns=[r"^/program/\d+/?$"],
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["startDate"], "2026-08-10")
        self.assertEqual(records[0]["endDate"], "2026-08-12")

    def test_detail_parser_normalizes_required_fields(self):
        html = """
        <html><head>
        <meta property="og:title" content="測試舞台劇">
        <meta property="og:image" content="https://tpac.org.taipei/images/poster.jpg">
        <meta name="description" content="這是一場用於驗證官方場館解析器的完整節目介紹，內容具有足夠長度。">
        <link rel="canonical" href="https://tpac.org.taipei/program/123">
        </head><body><h1>測試舞台劇</h1>
        <p>2026年8月10日 至 2026年8月12日</p>
        <p>演出地點：大劇院</p><p>票價：NT$800</p></body></html>
        """
        record = TaipeiPerformingArtsCenterCollector.parse_detail(
            html,
            detail_url="https://tpac.org.taipei/program/123",
            source=self.source,
        )
        self.assertEqual(record["startDate"], "2026-08-10")
        self.assertEqual(record["endDate"], "2026-08-12")
        self.assertEqual(record["venueName"], "臺北表演藝術中心")
        self.assertIn("大劇院", record["venueNames"])
        self.assertEqual(record["admission"], "paid")
        self.assertTrue(record["imageUrl"])


if __name__ == "__main__":
    unittest.main()
