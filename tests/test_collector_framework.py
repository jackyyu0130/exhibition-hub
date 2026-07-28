import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from scripts.exhibition_hub.collectors.audit import audit_collector_coverage
from scripts.exhibition_hub.collectors.base import (
    BaseCollector,
    CollectorRecord,
    CollectorSource,
)
from scripts.exhibition_hub.collectors.http import (
    CollectorHttpClient,
    CollectorHttpError,
)
from scripts.exhibition_hub.collectors.registry import CollectorRegistry
from scripts.exhibition_hub.collectors.runner import CollectorRunner
from scripts.exhibition_hub.collectors.sources import load_collector_sources


ROOT = Path(__file__).resolve().parents[1]


class ExampleCollector(BaseCollector):
    source_id = 'example-source'

    def collect_raw(self, source, client):
        return [{
            'id': 'event-1',
            'title': '測試展覽',
            'url': 'https://example.com/events/1',
        }]

    def normalize_record(self, source, raw):
        return CollectorRecord(
            source_id=source.id,
            source_event_id=raw['id'],
            title=raw['title'],
            detail_url=raw['url'],
            raw=raw,
        )


class CollectorFrameworkTests(unittest.TestCase):
    def test_source_registry_loads(self):
        sources = load_collector_sources(ROOT / 'data' / 'source_registry.json')
        self.assertGreaterEqual(len(sources), 10)
        self.assertIn('huashan-1914', {source.id for source in sources})

    def test_registry_rejects_duplicate_collectors(self):
        registry = CollectorRegistry()
        registry.register(ExampleCollector)
        with self.assertRaises(ValueError):
            registry.register(ExampleCollector)

    def test_runner_skips_disabled_source_by_default(self):
        registry = CollectorRegistry()
        registry.register(ExampleCollector)
        source = CollectorSource.from_mapping({
            'id': 'example-source',
            'name': 'Example',
            'status': 'planned',
            'enabled': False,
            'officialUrl': 'https://example.com',
        })
        report = CollectorRunner(registry, client=Mock()).run_source(source)
        self.assertEqual(report.status, 'skipped')
        self.assertTrue(report.success)

    def test_runner_can_run_planned_source_explicitly(self):
        registry = CollectorRegistry()
        registry.register(ExampleCollector)
        source = CollectorSource.from_mapping({
            'id': 'example-source',
            'name': 'Example',
            'status': 'planned',
            'enabled': False,
            'officialUrl': 'https://example.com',
        })
        report = CollectorRunner(registry, client=Mock()).run_source(
            source,
            allow_planned=True,
        )
        self.assertEqual(report.status, 'success')
        self.assertEqual(len(report.records), 1)

    def test_missing_collector_is_reported(self):
        source = CollectorSource.from_mapping({
            'id': 'missing-source',
            'name': 'Missing',
            'status': 'active',
            'enabled': True,
        })
        report = CollectorRunner(CollectorRegistry(), client=Mock()).run_source(source)
        self.assertEqual(report.status, 'failed')
        self.assertIn('not implemented', report.errors[0])

    def test_audit_treats_culture_as_external_legacy_pipeline(self):
        sources = load_collector_sources(ROOT / 'data' / 'source_registry.json')
        audit = audit_collector_coverage(sources, CollectorRegistry())
        self.assertTrue(audit['frameworkReady'])
        self.assertIn('culture-ministry', audit['externalManagedSourceIds'])
        self.assertIn('huashan-1914', audit['plannedSourcesMissingCollectors'])
        self.assertEqual(audit['nextPilotSourceId'], 'huashan-1914')

    def test_http_client_rejects_relative_url(self):
        with self.assertRaises(CollectorHttpError):
            CollectorHttpClient.validate_url('/relative/path')

    def test_collector_record_requires_http_url(self):
        record = CollectorRecord(
            source_id='example',
            source_event_id='1',
            title='測試',
            detail_url='/relative',
            raw={},
        )
        with self.assertRaises(ValueError):
            record.validate()


if __name__ == '__main__':
    unittest.main()
