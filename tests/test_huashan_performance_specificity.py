import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from exhibition_hub.collectors.huashan import (  # noqa: E402
    Huashan1914Collector,
)
from exhibition_hub.merging.policy import (  # noqa: E402
    merge_events,
)


class HuashanPerformanceSpecificityTests(unittest.TestCase):
    def test_specific_performance_keeps_primary_ticket_price(self):
        html = """
        <html>
          <head>
            <meta property="og:title"
                  content="【2026華山親子表藝節】賦格樂集《星空下的魔笛》">
          </head>
          <body>
            <h1>【2026華山親子表藝節】賦格樂集《星空下的魔笛》</h1>
            <div>票價資訊</div>
            <p>600元/張</p>
            <p>票價：500元/組</p>
            <div>活動地點</div>
            <p>烏梅劇院</p>
            <p>果酒練舞場</p>
          </body>
        </html>
        """
        result = Huashan1914Collector.parse_detail(
            html,
            detail_url=(
                "https://www.huashan1914.com/w/"
                "umaytheater/performance_example"
            ),
            listing={
                "title": (
                    "【2026華山親子表藝節】"
                    "賦格樂集《星空下的魔笛》"
                ),
                "startDate": "2026-07-19",
                "endDate": "2026-08-23",
            },
        )

        self.assertEqual(result["priceText"], "600元/張")
        self.assertEqual(result["admission"], "paid")

    def test_series_page_keeps_multiple_group_prices(self):
        html = """
        <html>
          <head>
            <meta property="og:title"
                  content="2026華山親子表藝節">
          </head>
          <body>
            <h1>2026華山親子表藝節</h1>
            <div>票價資訊</div>
            <p>早鳥價 8800元/組</p>
            <p>原價 9800元/組</p>
          </body>
        </html>
        """
        result = Huashan1914Collector.parse_detail(
            html,
            detail_url=(
                "https://www.huashan1914.com/w/"
                "umaytheater/performance_series"
            ),
            listing={
                "title": "2026華山親子表藝節",
            },
        )

        self.assertIn("8800元/組", result["priceText"])
        self.assertIn("9800元/組", result["priceText"])
        self.assertEqual(result["admission"], "paid")

    def test_specific_performance_preserves_precise_existing_venue(self):
        existing = {
            "id": "existing-event",
            "title": "2026華山親子表藝節《星空下的魔笛》",
            "startDate": "2026-08-22",
            "endDate": "2026-08-23",
            "venueDetail": "東3B館 烏梅劇院",
            "venueIds": ["huashan-1914"],
            "venueNames": [
                "華山1914文化創意產業園區"
            ],
            "sourceRecords": [],
        }
        source = {
            "sourceEntityKind": "performance_item",
            "startDate": "2026-07-19",
            "endDate": "2026-08-23",
            "venueDetail": "烏梅劇院／果酒練舞場",
            "venueIds": ["huashan-1914"],
            "venueNames": [
                "華山1914文化創意產業園區"
            ],
            "subVenueNames": [
                "烏梅劇院",
                "果酒練舞場",
            ],
            "sourcePriority": 90,
            "sourceRecords": [{
                "sourceId": "huashan-1914",
                "sourceEventId": "performance_example",
            }],
        }

        merged, changed = merge_events(existing, source)

        self.assertEqual(
            merged["venueDetail"],
            "東3B館 烏梅劇院",
        )
        self.assertNotIn("subVenueNames", merged)
        self.assertNotIn("venueDetail", changed)
        self.assertEqual(
            merged["startDate"],
            "2026-08-22",
        )


if __name__ == "__main__":
    unittest.main()
