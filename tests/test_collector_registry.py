import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from exhibition_hub.collectors.base import (  # noqa: E402
    BaseCollector,
    SourceKind,
)
from exhibition_hub.collectors.registry import (  # noqa: E402
    CollectorRegistry,
)


class FirstCollector(BaseCollector):
    source_id = "first"
    source_name = "First source"
    source_kind = SourceKind.API

    def _collect(self, context, result):
        result.add_event({"title": "First exhibition"})


class SecondCollector(BaseCollector):
    source_id = "second"
    source_name = "Second source"
    source_kind = SourceKind.HTML

    def _collect(self, context, result):
        result.add_event({"title": "Second exhibition"})


class DuplicateFirstCollector(BaseCollector):
    source_id = "first"
    source_name = "Duplicate first source"
    source_kind = SourceKind.RSS

    def _collect(self, context, result):
        return None


class DisabledCollector(BaseCollector):
    source_id = "disabled"
    source_name = "Disabled source"
    source_kind = SourceKind.SOCIAL

    def _collect(self, context, result):
        return None


class MissingIdentityCollector(BaseCollector):
    source_id = ""
    source_name = ""
    source_kind = SourceKind.HTML

    def _collect(self, context, result):
        return None


class RequiresArgumentCollector(BaseCollector):
    source_id = "requires-argument"
    source_name = "Requires argument"
    source_kind = SourceKind.API

    def __init__(self, required_value):
        self.required_value = required_value

    def _collect(self, context, result):
        return None


class CollectorRegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = CollectorRegistry()

    def test_register_and_get_collector(self):
        registration = self.registry.register(
            FirstCollector,
            priority=20,
        )

        stored = self.registry.get("first")

        self.assertIs(registration, stored)
        self.assertEqual(stored.source_id, "first")
        self.assertEqual(stored.source_name, "First source")
        self.assertEqual(stored.source_kind, SourceKind.API)
        self.assertEqual(stored.priority, 20)
        self.assertTrue(stored.enabled)

    def test_registrations_are_sorted_by_priority_then_id(self):
        self.registry.register(
            SecondCollector,
            priority=20,
        )
        self.registry.register(
            FirstCollector,
            priority=10,
        )
        self.registry.register(
            DisabledCollector,
            priority=20,
            enabled=False,
        )

        source_ids = [
            registration.source_id
            for registration in self.registry.registrations()
        ]

        self.assertEqual(
            source_ids,
            [
                "first",
                "disabled",
                "second",
            ],
        )

    def test_create_collectors_skips_disabled_sources(self):
        self.registry.register(FirstCollector)
        self.registry.register(
            DisabledCollector,
            enabled=False,
        )

        collectors = self.registry.create_collectors()

        self.assertEqual(len(collectors), 1)
        self.assertIsInstance(
            collectors[0],
            FirstCollector,
        )

    def test_include_and_exclude_filters(self):
        self.registry.register(FirstCollector)
        self.registry.register(SecondCollector)

        included = self.registry.create_collectors(
            include=["second"],
        )
        excluded = self.registry.create_collectors(
            exclude=["first"],
        )

        self.assertEqual(len(included), 1)
        self.assertIsInstance(
            included[0],
            SecondCollector,
        )

        self.assertEqual(len(excluded), 1)
        self.assertIsInstance(
            excluded[0],
            SecondCollector,
        )

    def test_unknown_filter_source_is_rejected(self):
        self.registry.register(FirstCollector)

        with self.assertRaises(KeyError):
            self.registry.create_collectors(
                include=["unknown"],
            )

        with self.assertRaises(KeyError):
            self.registry.create_collectors(
                exclude=["unknown"],
            )

    def test_duplicate_source_id_is_rejected(self):
        self.registry.register(FirstCollector)

        with self.assertRaises(ValueError):
            self.registry.register(
                DuplicateFirstCollector
            )

    def test_invalid_registration_is_rejected(self):
        with self.assertRaises(ValueError):
            self.registry.register(
                MissingIdentityCollector
            )

        with self.assertRaises(TypeError):
            self.registry.register(
                RequiresArgumentCollector
            )

        with self.assertRaises(TypeError):
            self.registry.register(
                FirstCollector,
                priority=1.5,
            )

    def test_registration_creates_fresh_instances(self):
        registration = self.registry.register(
            FirstCollector
        )

        first = registration.create()
        second = registration.create()

        self.assertIsInstance(first, FirstCollector)
        self.assertIsInstance(second, FirstCollector)
        self.assertIsNot(first, second)

    def test_summary_is_json_safe(self):
        self.registry.register(
            FirstCollector,
            priority=15,
        )

        summary = self.registry.as_summary()

        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]["sourceId"], "first")
        self.assertEqual(
            summary[0]["sourceKind"],
            "api",
        )
        self.assertEqual(summary[0]["priority"], 15)
        self.assertEqual(
            summary[0]["collectorClass"],
            "FirstCollector",
        )


if __name__ == "__main__":
    unittest.main()
