import unittest

from scripts.exhibition_hub.collectors.huashan import Huashan1914Collector


class HuashanDetailQualityTests(unittest.TestCase):
    def test_script_footer_and_related_event_noise_are_removed(self):
        html = """
        <!doctype html><html><head>
          <meta property="og:title" content="李亭香 - 華山1914文化創意產業園區">
          <meta property="og:image" content="/upload/event/li-main.jpg">
          <meta property="og:description" content="大稻埕百年餅店進駐華山芳釀所。">
        </head><body>
          <h1>李亭香</h1>
          <div>期間限定店</div>
          <h6>主辦單位</h6><div>灃誼食品企業有限公司</div>
          <h6>活動地點</h6>
          <div>中4B館1F-3.4(芳釀所)</div>
          <div>大稻埕百年餅店正式進駐華山芳釀所</div>
          <p>在台北大稻埕，有一陣飄散了百年的餅香。</p>
          <div>活動資訊</div>
          <p>免費入場</p>
          <img src="/upload/event/li-gallery.jpg">
          <div>相關活動</div>
          <p>票價：全票500元</p>
          <img src="/upload/event/unrelated.jpg">
          <a href="https://www.facebook.com/1914CP/">Huashan Facebook</a>
          <a href="https://example.com/li-event">活動連結</a>
          <script>
            event.preventDefault();
            $('[data-colorboxGroup]').each(function () {});
          </script>
        </body></html>
        """
        result = Huashan1914Collector.parse_detail(
            html,
            detail_url=(
                "https://www.huashan1914.com/w/huashan1914/"
                "exhibition_26072515232688455"
            ),
            listing={"title": "李亭香"},
        )

        self.assertEqual(
            result["venueNames"],
            ["中4B館1F-3.4(芳釀所)"],
        )
        self.assertEqual(result["admission"], "free")
        self.assertEqual(result["priceText"], "")
        self.assertNotIn("event.preventDefault", result["description"])
        self.assertNotIn(
            "https://www.facebook.com/1914CP/",
            result["externalUrls"],
        )
        self.assertIn(
            "https://example.com/li-event",
            result["externalUrls"],
        )
        self.assertLessEqual(len(result["imageUrls"]), 4)

    def test_performance_path_infers_performance_category(self):
        html = """
        <!doctype html><html><head>
          <meta property="og:title" content="【2026華山親子表藝節】星空下的魔笛">
          <meta property="og:image" content="/upload/event/performance.jpg">
        </head><body>
          <div>10:30 AM - 11:30 AM</div>
          <h1>【2026華山親子表藝節】星空下的魔笛</h1>
          <h6>主辦單位</h6><div>華山1914文創園區</div>
          <h6>活動地點</h6>
          <div>烏梅劇院</div>
          <div>果酒練舞場</div>
          <div>適合對象</div>
          <div>親子</div>
          <div>適合年齡</div>
          <div>3-12歲</div>
          <p>【票價】</p><p>600元/張</p>
          <div>相關活動</div>
          <p>票價：500元/組</p>
        </body></html>
        """
        result = Huashan1914Collector.parse_detail(
            html,
            detail_url=(
                "https://www.huashan1914.com/w/umaytheater/"
                "performance_26050416214384371"
            ),
            listing={"title": "【2026華山親子表藝節】星空下的魔笛"},
        )

        self.assertEqual(result["sourceCategory"], "表演藝術")
        self.assertEqual(result["contentTypeHint"], "表演")
        self.assertEqual(result["venueNames"], ["烏梅劇院", "果酒練舞場"])
        self.assertEqual(result["admission"], "paid")
        self.assertIn("600元/張", result["priceText"])
        self.assertNotIn("500元/組", result["priceText"])


if __name__ == "__main__":
    unittest.main()
