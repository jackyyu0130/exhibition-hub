import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from exhibition_hub.merging.normalization import (  # noqa: E402
    URL_NORMALIZATION_VERSION,
    normalize_url,
    unique_urls,
)


class UrlIntegrityTests(unittest.TestCase):
    def test_url_normalization_hotfix_version(self):
        self.assertEqual(URL_NORMALIZATION_VERSION, "6.4.0")

    def test_full_width_path_punctuation_is_not_nfkc_normalized(self):
        url = (
            "https://media.huashan1914.com/WebUPD/huashan1914/exhibition/"
            "KV_華山官網活動｜1920x1080.jpg"
        )
        self.assertEqual(normalize_url(url), url)
        self.assertEqual(unique_urls([url, url]), [url])
        self.assertNotIn("|1920", normalize_url(url))

    def test_matching_normalization_still_drops_query_and_fragment(self):
        self.assertEqual(
            normalize_url("HTTPS://Example.COM/event/?utm_source=test#top"),
            "https://example.com/event",
        )


if __name__ == "__main__":
    unittest.main()
