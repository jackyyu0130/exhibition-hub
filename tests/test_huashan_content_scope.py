import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from exhibition_hub.collectors.huashan import (  # noqa: E402
    Huashan1914Collector,
)


class HuashanContentScopeTests(unittest.TestCase):
    def test_related_assets_and_generic_links_are_excluded(self):
        html = """
        <html>
          <head>
            <meta property="og:title"
                  content="流浪蓋婭號 WANDERING GAIA">
            <meta property="og:image"
                  content="/event/gaia-main.jpg">
          </head>
          <body>
            <h1>流浪蓋婭號 WANDERING GAIA</h1>
            <div>展演活動</div>
            <div>活動地點</div><div>東3A館</div>
            <div>票價資訊</div>
            <p>票價：全票350元、優惠票250元、家庭套票800元、愛心票175元</p>
            <img src="/event/gaia-gallery.jpg">
            <a href="https://tickets.example.com/gaia">購票</a>
            <a href="https://tea.huashan1914.org/beingproject">共用頁</a>
            <a href="https://reurl.cc/33kmg9">共用短網址</a>
            <h2>相關活動</h2>
            <p>票價：全票500元、家庭套票1,100元</p>
            <img src="/event/bologna.jpg">
            <a href="https://example.com/other-event">其他活動</a>
          </body>
        </html>
        """
        result = Huashan1914Collector.parse_detail(
            html,
            detail_url=(
                "https://www.huashan1914.com/w/"
                "huashan1914/exhibition_gaia"
            ),
            listing={
                "title": "流浪蓋婭號 WANDERING GAIA",
                "imageUrl": (
                    "https://media.huashan1914.com/"
                    "event/gaia-main.jpg"
                ),
            },
        )

        self.assertIn("全票350元", result["priceText"])
        self.assertNotIn("1,100元", result["priceText"])
        self.assertTrue(
            all("bologna.jpg" not in url for url in result["imageUrls"])
        )
        self.assertIn(
            "https://tickets.example.com/gaia",
            result["externalUrls"],
        )
        self.assertNotIn(
            "https://tea.huashan1914.org/beingproject",
            result["externalUrls"],
        )
        self.assertNotIn(
            "https://reurl.cc/33kmg9",
            result["externalUrls"],
        )


    def test_long_ticket_paragraph_keeps_price_fragments_only(self):
        html = """
        <html><head>
          <meta property="og:title"
                content="CHIIKAWA DAYS 台北特展">
        </head><body>
          <h1>CHIIKAWA DAYS 台北特展</h1>
          <div>展演活動</div>
          <div>活動及票價資訊</div>
          <p>
            本次特展採售票制與預約入場，帶來沉浸式體驗，
            票價：特典套票 NTD1580、全票 NTD490、
            優待票 NTD470、愛心票 NTD245。
          </p>
        </body></html>
        """
        result = Huashan1914Collector.parse_detail(
            html,
            detail_url=(
                "https://www.huashan1914.com/w/"
                "huashan1914/exhibition_chiikawa"
            ),
            listing={"title": "CHIIKAWA DAYS 台北特展"},
        )

        self.assertEqual(result["admission"], "paid")
        self.assertIn("NTD1580", result["priceText"])
        self.assertIn("NTD490", result["priceText"])
        self.assertNotIn("沉浸式體驗", result["priceText"])

    def test_reward_amount_does_not_become_paid_admission(self):
        html = """
        <html><head>
          <meta property="og:title"
                content="一粒米：好土台灣 徵件活動">
        </head><body>
          <h1>一粒米：好土台灣 徵件活動</h1>
          <div>展演活動</div>
          <p>入選獎勵：誠品書店禮券600元／15名</p>
        </body></html>
        """
        result = Huashan1914Collector.parse_detail(
            html,
            detail_url=(
                "https://www.huashan1914.com/w/"
                "huashan1914/exhibition_submission"
            ),
            listing={"title": "一粒米：好土台灣 徵件活動"},
        )

        self.assertEqual(result["admission"], "unknown")
        self.assertEqual(result["priceText"], "")
        self.assertEqual(
            result["editorialStatus"],
            "exclude_review",
        )

    def test_emoji_images_are_removed_and_gallery_is_capped(self):
        html = """
        <html><head>
          <meta property="og:title"
                content="測試活動">
          <meta property="og:image"
                content="/event/main.jpg">
        </head><body>
          <h1>測試活動</h1>
          <img src="/event/gallery-1.jpg">
          <img src="/event/gallery-2.jpg">
          <img src="/event/1f4cd.png">
          <img src="/event/gallery-3.jpg">
        </body></html>
        """
        result = Huashan1914Collector.parse_detail(
            html,
            detail_url=(
                "https://www.huashan1914.com/w/"
                "huashan1914/exhibition_test"
            ),
            listing={"title": "測試活動"},
        )

        self.assertLessEqual(len(result["imageUrls"]), 3)
        self.assertTrue(
            all("1f4cd.png" not in url for url in result["imageUrls"])
        )


if __name__ == "__main__":
    unittest.main()
