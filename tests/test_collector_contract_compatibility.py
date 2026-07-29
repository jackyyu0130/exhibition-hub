import sys
import unittest
from pathlib import Path
from unittest.mock import Mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from exhibition_hub.collectors.base import (  # noqa: E402
    BaseCollector,
    CollectionResult,
    CollectorContext,
    CollectorRecord,
    CollectorSource,
    RawEvent,
    SourceKind,
)
from exhibition_hub.collectors.registry import (  # noqa: E402
    CollectorRegistry,
)
from exhibition_hub.collectors.runner import (  # noqa: E402
    CollectorRunner,
    run_collectors,
)


class LegacyCollector(BaseCollector):
    source_id = "legacy-example"
    source_name = "Legacy example"
    source_kind = SourceKind.API

    def _collect(self, context, result):
        result.add_event({"title": "Legacy event"})


class VenueCollector(BaseCollector):
    source_id = "venue-example"

    def collect_raw(self, source, client):
        return [{
            "id": "venue-event-1",
            "title": "Venue event",
            "url": "https://example.com/events/1",
        }]

    def normalize_record(self, source, raw):
        return CollectorRecord(
            source_id=source.id,
            source_event_id=raw["id"],
            title=raw["title"],
            detail_url=raw["url"],
            raw=raw,
        )


class CollectorCompatibilityTests(unittest.TestCase):
    def test_legacy_contract_remains_available(self):
        context = CollectorContext.create()
        result = LegacyCollector().collect(context)

        self.assertIsInstance(result, CollectionResult)
        self.assertTrue(result.succeeded)
        self.assertEqual(result.events[0]["title"], "Legacy event")

    def test_raw_event_alias_remains_available(self):
        event: RawEvent = {"title": "Typed event"}
        self.assertEqual(event["title"], "Typed event")

    def test_new_venue_contract_remains_available(self):
        registry = CollectorRegistry()
        registry.register(VenueCollector)

        source = CollectorSource.from_mapping({
            "id": "venue-example",
            "name": "Venue example",
            "enabled": True,
            "status": "active",
        })
        report = CollectorRunner(
            registry,
            client=Mock(),
        ).run_source(source)

        self.assertTrue(report.success)
        self.assertEqual(len(report.records), 1)

    def test_registry_supports_legacy_batch_creation(self):
        registry = CollectorRegistry()
        registration = registry.register(
            LegacyCollector,
            priority=10,
        )

        self.assertEqual(registration.source_name, "Legacy example")
        self.assertEqual(
            registry.create_collectors()[0].source_id,
            "legacy-example",
        )

    def test_legacy_and_new_runners_can_coexist(self):
        legacy_batch = run_collectors([LegacyCollector()])
        self.assertEqual(legacy_batch.published_event_count, 1)

        registry = CollectorRegistry()
        registry.register(VenueCollector)
        source = CollectorSource.from_mapping({
            "id": "venue-example",
            "name": "Venue example",
            "enabled": True,
            "status": "active",
        })
        venue_report = CollectorRunner(
            registry,
            client=Mock(),
        ).run_source(source)
        self.assertTrue(venue_report.success)
        self.assertIn("metrics", venue_report.to_dict())


if __name__ == "__main__":
    unittest.main()
