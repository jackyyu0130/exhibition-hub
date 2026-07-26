import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from exhibition_hub.collectors.base import (  # noqa: E402
    BaseCollector,
    CollectionResult,
    CollectorContext,
    CollectorError,
    SourceKind,
)


class SuccessfulCollector(BaseCollector):
    source_id = "successful"
    source_name = "Successful source"
    source_kind = SourceKind.API

    def _collect(self, context, result):
        result.add_event({"title": "Test exhibition"})
        result.add_warning("Partial metadata")


class ExpectedFailureCollector(BaseCollector):
    source_id = "expected-failure"
    source_name = "Expected failure"
    source_kind = SourceKind.HTML

    def _collect(self, context, result):
        raise CollectorError("Temporary source outage")


class UnexpectedFailureCollector(BaseCollector):
    source_id = "unexpected-failure"
    source_name = "Unexpected failure"
    source_kind = SourceKind.HTML

    def _collect(self, context, result):
        raise ValueError("Broken parser")


class MissingIdentityCollector(BaseCollector):
    def _collect(self, context, result):
        return None


class CollectorContextTests(unittest.TestCase):
    def test_create_returns_timezone_aware_unique_context(self):
        first = CollectorContext.create(
            settings={"region": "台北市"}
        )
        second = CollectorContext.create()

        self.assertNotEqual(first.run_id, second.run_id)
        self.assertIsNotNone(first.started_at.tzinfo)
        self.assertEqual(first.settings["region"], "台北市")

    def test_settings_are_copied_and_read_only(self):
        source_settings = {"limit": 20}
        context = CollectorContext.create(
            settings=source_settings
        )
        source_settings["limit"] = 99

        self.assertEqual(context.settings["limit"], 20)

        with self.assertRaises(TypeError):
            context.settings["limit"] = 30

    def test_invalid_context_values_are_rejected(self):
        with self.assertRaises(ValueError):
            CollectorContext.create(timeout_seconds=0)

        with self.assertRaises(ValueError):
            CollectorContext.create(user_agent="   ")


class CollectionResultTests(unittest.TestCase):
    def test_add_event_stores_a_copy(self):
        result = CollectionResult(
            source_id="test",
            source_name="Test",
            source_kind=SourceKind.MANUAL,
        )
        original = {"title": "Original title"}

        result.add_event(original)
        original["title"] = "Changed title"

        self.assertEqual(
            result.events[0]["title"],
            "Original title",
        )

    def test_summary_is_json_safe_and_does_not_include_events(self):
        result = CollectionResult(
            source_id="test",
            source_name="Test",
            source_kind=SourceKind.RSS,
        )
        result.add_event({"title": "Exhibition"})
        result.add_warning(" warning ")
        result.finish()

        summary = result.as_summary()

        self.assertTrue(summary["succeeded"])
        self.assertEqual(summary["eventCount"], 1)
        self.assertEqual(summary["warningCount"], 1)
        self.assertNotIn("events", summary)
        self.assertIsNotNone(summary["finishedAt"])
        self.assertGreaterEqual(
            summary["durationSeconds"],
            0,
        )


class BaseCollectorTests(unittest.TestCase):
    def setUp(self):
        self.context = CollectorContext.create()

    def test_successful_collector_returns_records_and_diagnostics(
        self,
    ):
        result = SuccessfulCollector().collect(self.context)

        self.assertTrue(result.succeeded)
        self.assertEqual(result.event_count, 1)
        self.assertEqual(
            result.warnings,
            ["Partial metadata"],
        )
        self.assertIsNotNone(result.finished_at)

    def test_expected_failure_is_captured_without_raising(self):
        result = ExpectedFailureCollector().collect(
            self.context
        )

        self.assertFalse(result.succeeded)
        self.assertEqual(
            result.errors,
            ["Temporary source outage"],
        )
        self.assertIsNotNone(result.finished_at)

    def test_unexpected_failure_is_captured_without_raising(
        self,
    ):
        result = UnexpectedFailureCollector().collect(
            self.context
        )

        self.assertFalse(result.succeeded)
        self.assertEqual(
            result.errors,
            ["Unexpected ValueError: Broken parser"],
        )

    def test_missing_collector_identity_is_rejected(self):
        with self.assertRaises(ValueError):
            MissingIdentityCollector().collect(
                self.context
            )


if __name__ == "__main__":
    unittest.main()
