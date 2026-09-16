from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class R185OfficialSourceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = json.loads(
            (ROOT / "data/source_registry.json").read_text(encoding="utf-8")
        )
        cls.sources = {
            item["id"]: item
            for item in cls.registry["sources"]
        }

    def test_huashan_uses_current_exhibition_listing(self) -> None:
        source = self.sources["huashan-1914"]
        self.assertEqual(
            source["listingUrl"],
            "https://www.huashan1914.com/w/huashan1914/exhibition",
        )
        self.assertNotIn("CustomEvent", source["listingUrl"])

    def test_high_priority_sources_have_bounded_detail_limits(self) -> None:
        for source_id in (
            "huashan-1914",
            "songshan-cultural-park",
            "pier-2",
            "tainan-art-museum",
        ):
            source = self.sources[source_id]
            self.assertGreaterEqual(source.get("detailLimit", 0), 34)
            self.assertLessEqual(source["detailLimit"], 40)

    def test_source_level_limit_is_applied_in_runners(self) -> None:
        runner = (ROOT / "scripts/run_collectors.py").read_text(encoding="utf-8")
        batch = (ROOT / "scripts/run_official_source_batch.py").read_text(encoding="utf-8")
        self.assertIn('selected_source.raw.get("detailLimit")', runner)
        self.assertIn('source.raw.get("detailLimit")', batch)
        self.assertIn('EXHIBITION_HUB_DETAIL_LIMIT', batch)


if __name__ == "__main__":
    unittest.main()
