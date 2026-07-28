import json
from pathlib import Path
import unittest

from scripts.exhibition_hub.collectors import (
    CollectorRunner,
    collector_registry,
)
from scripts.exhibition_hub.collectors.audit import (
    audit_collector_coverage,
)
from scripts.exhibition_hub.collectors.base import CollectorSource
from scripts.exhibition_hub.collectors.http import CollectorHttpResponse
from scripts.exhibition_hub.collectors.huashan import (
    DEFAULT_LISTING_URL,
    Huashan1914Collector,
)
from scripts.exhibition_hub.collectors.sources import (
    load_collector_sources,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


class FakeClient:
    def __init__(self):
        self.urls = []

    def get(self, url):
        self.urls.append(url)
        page = 2 if "index=2" in url else 1
        html = (
            FIXTURES / f"huashan_listing_page{page}.html"
        ).read_text(encoding="utf-8")
        return CollectorHttpResponse(
            url=url,
            status_code=200,
            text=html,
            headers={},
        )


class HuashanCollectorTests(unittest.TestCase):
    def setUp(self):
        self.sources = load_collector_sources(
            ROOT / "data" / "source_registry.json"
        )
        self.source = next(
            source
            for source in self.sources
            if source.id == "huashan-1914"
        )

    def test_source_stays_planned_but_has_listing_url(self):
        self.assertFalse(self.source.enabled)
        self.assertEqual(self.source.status, "planned")
        self.assertEqual(
            self.source.listing_url,
            DEFAULT_LISTING_URL,
        )

    def test_parse_listing_extracts_chiikawa(self):
        html = (
            FIXTURES / "huashan_listing_page1.html"
        ).read_text(encoding="utf-8")
        records, total_pages = (
            Huashan1914Collector.parse_listing(html)
        )

        self.assertEqual(total_pages, 2)
        chiikawa = next(
            record
            for record in records
            if "CHIIKAWA" in record["title"]
        )
        self.assertEqual(
            chiikawa["sourceEventId"],
            "exhibition_26061619433530946",
        )
        self.assertEqual(
            chiikawa["startDate"],
            "2026-07-04",
        )
        self.assertEqual(
            chiikawa["endDate"],
            "2026-09-27",
        )
        self.assertEqual(
            chiikawa["listingCategory"],
            "園區活動",
        )
        self.assertTrue(
            chiikawa["detailUrl"].startswith(
                "https://www.huashan1914.com/"
            )
        )
        self.assertTrue(
            chiikawa["imageUrl"].endswith(
                "/upload/chiikawa.jpg"
            )
        )

    def test_live_contract_paginates_and_deduplicates(self):
        client = FakeClient()
        report = CollectorRunner(
            collector_registry,
            client=client,
        ).run_source(
            self.source,
            allow_planned=True,
        )

        self.assertTrue(report.success)
        self.assertEqual(report.status, "success")
        self.assertEqual(report.fetched_pages, 2)
        self.assertEqual(len(report.records), 3)
        self.assertEqual(
            len({
                record.detail_url
                for record in report.records
            }),
            3,
        )
        self.assertIn("index=2", client.urls[1])

    def test_framework_audit_marks_huashan_implemented(self):
        audit = audit_collector_coverage(
            self.sources,
            collector_registry,
        )
        self.assertIn(
            "huashan-1914",
            audit["implementedCollectorIds"],
        )
        self.assertNotIn(
            "huashan-1914",
            audit["plannedSourcesMissingCollectors"],
        )
        self.assertTrue(audit["frameworkReady"])


if __name__ == "__main__":
    unittest.main()
