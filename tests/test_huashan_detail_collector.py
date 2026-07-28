import json
from pathlib import Path
import unittest

from scripts.exhibition_hub.collectors.base import CollectorSource
from scripts.exhibition_hub.collectors.http import CollectorHttpResponse
from scripts.exhibition_hub.collectors.huashan import Huashan1914Collector


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


class DetailClient:
    def __init__(self):
        self.urls = []

    def get(self, url):
        self.urls.append(url)
        if "CustomEvent" in url:
            page = 2 if "index=2" in url else 1
            html = (FIXTURES / f"huashan_listing_page{page}.html").read_text(encoding="utf-8")
        elif "26061619433530946" in url:
            html = (FIXTURES / "huashan_detail_chiikawa.html").read_text(encoding="utf-8")
        elif "26070817500503214" in url:
            html = (FIXTURES / "huashan_detail_osamu.html").read_text(encoding="utf-8")
        else:
            html = (FIXTURES / "huashan_detail_popup.html").read_text(encoding="utf-8")
        return CollectorHttpResponse(url=url, status_code=200, text=html, headers={})


class HuashanDetailCollectorTests(unittest.TestCase):
    def test_parse_chiikawa_detail(self):
        html = (FIXTURES / "huashan_detail_chiikawa.html").read_text(encoding="utf-8")
        result = Huashan1914Collector.parse_detail(
            html,
            detail_url="https://www.huashan1914.com/w/huashan1914/exhibition_26061619433530946",
            listing={
                "title": "CHIIKAWA DAYS 台北特展",
                "startDate": "2026-07-04",
                "endDate": "2026-09-27",
            },
        )
        self.assertEqual(result["regionCanonical"], "臺北市")
        self.assertEqual(result["venueName"], "華山1914文化創意產業園區")
        self.assertEqual(result["venueNames"], ["東2A館", "東2B館", "東2C館", "東2D館"])
        self.assertEqual(result["organizer"], "OMOLABO")
        self.assertEqual(result["sourceCategory"], "展演活動")
        self.assertEqual(result["admission"], "paid")
        self.assertEqual(result["startTime"], "10:00")
        self.assertEqual(result["endTime"], "19:00")
        self.assertTrue(result["imageUrl"].endswith("chiikawa-main.jpg"))
        self.assertTrue(result["description"])
        self.assertIn("https://linktr.ee/0percent.taipei", result["externalUrls"])

    def test_parse_osamu_12_hour_time(self):
        html = (FIXTURES / "huashan_detail_osamu.html").read_text(encoding="utf-8")
        result = Huashan1914Collector.parse_detail(
            html,
            detail_url="https://www.huashan1914.com/w/huashan1914/exhibition_26070817500503214",
            listing={"title": "OSAMU GOODS 50週年展"},
        )
        self.assertEqual(result["startTime"], "10:00")
        self.assertEqual(result["endTime"], "18:00")
        self.assertEqual(result["admission"], "unknown")
        self.assertEqual(len(result["venueNames"]), 2)

    def test_popup_maps_to_popup_and_free(self):
        html = (FIXTURES / "huashan_detail_popup.html").read_text(encoding="utf-8")
        result = Huashan1914Collector.parse_detail(
            html,
            detail_url="https://www.huashan1914.com/w/huashan1914/exhibition_x",
            listing={"title": "星際大戰華山限定快閃店_Mission Cantina"},
        )
        self.assertEqual(result["sourceCategory"], "期間限定店")
        self.assertEqual(result["contentTypeHint"], "快閃店")
        self.assertEqual(result["admission"], "free")

    def test_detail_limit_and_metrics(self):
        source = CollectorSource.from_mapping({
            "id": "huashan-1914",
            "name": "華山1914文化創意產業園區",
            "status": "planned",
            "enabled": False,
            "listingUrl": "https://www.huashan1914.com/w/huashan1914/CustomEvent",
        })
        collector = Huashan1914Collector(fetch_details=True, detail_limit=2)
        report = collector.run(source, DetailClient())
        self.assertTrue(report.success)
        self.assertEqual(report.metrics["detailRequestedCount"], 2)
        self.assertEqual(report.metrics["detailSuccessCount"], 2)
        self.assertEqual(report.metrics["detailFailureCount"], 0)
        self.assertEqual(sum(bool(record.raw.get("detailFetched")) for record in report.records), 2)
        self.assertIn("metrics", report.to_dict())

    def test_listing_only_mode_is_unchanged(self):
        source = CollectorSource.from_mapping({
            "id": "huashan-1914",
            "name": "華山1914文化創意產業園區",
            "status": "planned",
            "enabled": False,
            "listingUrl": "https://www.huashan1914.com/w/huashan1914/CustomEvent",
        })
        collector = Huashan1914Collector(fetch_details=False)
        report = collector.run(source, DetailClient())
        self.assertTrue(report.success)
        self.assertFalse(report.metrics["detailEnabled"])
        self.assertEqual(report.metrics["detailRequestedCount"], 0)


if __name__ == "__main__":
    unittest.main()
