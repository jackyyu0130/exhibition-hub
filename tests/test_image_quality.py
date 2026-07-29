import unittest

from scripts.exhibition_hub.image_quality import (
    audit_payload,
    suspicious_image_reason,
)


class ImageQualityTests(unittest.TestCase):
    def test_interface_and_default_images_are_rejected(self):
        urls = {
            "https://www.opentix.life/_nuxt/img/flags.9c96e0ed.png",
            "https://activity.ncku.edu.tw/images/coordinate.png",
            "https://cloud.culture.tw/assets/images/BANNER_1200X630.jpg",
            "https://s3.resource.opentix.life/default/opentixPageDefault.png",
            "https://ntcart.museum/{{:defaultImg}}",
        }
        self.assertTrue(all(suspicious_image_reason(url) for url in urls))
        self.assertEqual(
            suspicious_image_reason("https://example.com/events/real-poster.jpg"),
            "",
        )

    def test_audit_fix_keeps_real_image_and_removes_facebook(self):
        payload = {
            "events": [{
                "id": "event-1",
                "title": "測試展覽",
                "image": "https://www.opentix.life/_nuxt/img/flags.9c96e0ed.png",
                "images": [
                    "https://www.opentix.life/_nuxt/img/flags.9c96e0ed.png",
                    "https://example.com/poster.jpg",
                ],
                "sourceUrls": [
                    "https://example.com/event",
                    "https://www.facebook.com/groups/example",
                ],
            }]
        }
        cleaned, report = audit_payload(payload, fix=True)
        event = cleaned["events"][0]
        self.assertEqual(event["image"], "https://example.com/poster.jpg")
        self.assertEqual(event["images"], ["https://example.com/poster.jpg"])
        self.assertEqual(event["sourceUrls"], ["https://example.com/event"])
        self.assertEqual(report["rejectedImageCount"], 1)
        self.assertEqual(report["facebookReferenceEventCount"], 1)


if __name__ == "__main__":
    unittest.main()
