import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from exhibition_hub.collectors.huashan import (  # noqa: E402
    Huashan1914Collector,
)


class HuashanAdmissionPrecedenceTests(unittest.TestCase):
    def test_explicit_ticket_price_overrides_generic_free_wording(self):
        html = """
        <html>
          <head>
            <meta property="og:title"
                  content="2026華山親子表藝節">
          </head>
          <body>
            <h1>2026華山親子表藝節</h1>
            <div>票價資訊</div>
            <p>
              5/8-5/18 早鳥價｜8800元/組，
              5/18-6/8 原價｜9800元/組。
            </p>
            <p>園區另有免費參加的公共活動。</p>
          </body>
        </html>
        """
        result = Huashan1914Collector.parse_detail(
            html,
            detail_url=(
                "https://www.huashan1914.com/w/"
                "umaytheater/performance_test"
            ),
            listing={
                "title": "2026華山親子表藝節",
                "startDate": "2026-06-06",
                "endDate": "2026-08-30",
            },
        )

        self.assertEqual(result["admission"], "paid")
        self.assertIn("8800元", result["priceText"])
        self.assertIn("9800元", result["priceText"])

    def test_explicit_free_admission_remains_free(self):
        html = """
        <html>
          <head>
            <meta property="og:title"
                  content="免費個展">
          </head>
          <body>
            <h1>免費個展</h1>
            <div>票價資訊</div>
            <p>免費入場</p>
          </body>
        </html>
        """
        result = Huashan1914Collector.parse_detail(
            html,
            detail_url=(
                "https://www.huashan1914.com/w/"
                "huashan1914/exhibition_free"
            ),
            listing={"title": "免費個展"},
        )

        self.assertEqual(result["admission"], "free")


if __name__ == "__main__":
    unittest.main()
