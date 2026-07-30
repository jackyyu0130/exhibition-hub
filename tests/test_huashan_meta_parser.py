import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from exhibition_hub.collectors.huashan import (  # noqa: E402
    Huashan1914Collector,
)


class HuashanMetaParserTests(unittest.TestCase):
    def test_meta_without_name_or_property_is_ignored(self):
        html = """
        <!doctype html>
        <html>
          <head>
            <meta charset="utf-8">
            <meta content="width=device-width">
            <meta property="og:title"
                  content="2026華山親子表藝節">
            <meta property="og:description"
                  content="親子表演藝術活動介紹。">
          </head>
          <body>
            <main>
              <h1>2026華山親子表藝節</h1>
              <p>主辦單位</p>
              <p>華山1914文化創意產業園區</p>
              <p>活動地點</p>
              <p>烏梅劇院</p>
              <p>表演藝術</p>
            </main>
          </body>
        </html>
        """
        result = Huashan1914Collector.parse_detail(
            html,
            detail_url=(
                "https://www.huashan1914.com/w/"
                "umaytheater/"
                "performance_26040110454037661"
            ),
            listing={
                "sourceEventId": (
                    "performance_26040110454037661"
                ),
                "title": "2026華山親子表藝節",
                "startDate": "2026-06-06",
                "endDate": "2026-08-30",
            },
        )

        self.assertTrue(result["detailFetched"])
        self.assertEqual(
            result["title"],
            "2026華山親子表藝節",
        )
        self.assertEqual(
            result["sourceCategory"],
            "表演藝術",
        )
        self.assertIn(
            "烏梅劇院",
            result["venueNames"],
        )

    def test_empty_meta_attributes_do_not_raise(self):
        html = """
        <html>
          <head>
            <meta>
            <meta name>
            <meta property>
            <meta name="" content="">
          </head>
          <body>
            <h1>測試活動</h1>
          </body>
        </html>
        """
        result = Huashan1914Collector.parse_detail(
            html,
            detail_url=(
                "https://www.huashan1914.com/w/"
                "huashan1914/exhibition_test"
            ),
            listing={
                "title": "測試活動",
                "startDate": "2026-07-01",
                "endDate": "2026-07-31",
            },
        )
        self.assertTrue(result["detailFetched"])
        self.assertEqual(result["title"], "測試活動")


if __name__ == "__main__":
    unittest.main()
