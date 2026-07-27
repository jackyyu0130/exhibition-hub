import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from exhibition_hub.collectors.base import (  # noqa: E402
    BaseCollector,
    CollectorContext,
    CollectorError,
    SourceKind,
)
from exhibition_hub.collectors.runner import (  # noqa: E402
    run_collectors,
)


class WorkingCollector(BaseCollector):
    source_id = "working"
    source_name = "Working source"
    source_kind = SourceKind.API

    def _collect(self, context, result):
        result.add_event(
            {
                "title": "Working exhibition",
                "source": self.source_id,
            }
        )


class SecondWorkingCollector(BaseCollector):
    source_id = "second-working"
    source_name = "Second working source"
    source_kind = SourceKind.HTML

    def _collect(self, context, result):
        result.add_event(
            {
                "title": "Second exhibition",
                "source": self.source_id,
            }
        )


class PartiallyFailedCollector(BaseCollector):
    source_id = "partial-failure"
    source_name = "Partially failed source"
    source_kind = SourceKind.HTML

    def _collect(self, context, result):
        result.add_event(
            {
                "title": "Untrusted partial record",
                "source": self.source_id,
            }
        )
        raise CollectorError("Source stopped before completion")


class InvalidCollector(BaseCollector):
    source_id = ""
    source_name = ""
    source_kind = SourceKind.HTML

    def _collect(self, context, result):
        return None


class CollectorRunnerTests(unittest.TestCase):
    def test_all_working_collectors_are_combined(self):
        batch = run_collectors(
            [
                WorkingCollector(),
                SecondWorkingCollector(),
            ]
        )

        self.assertEqual(batch.source_count, 2)
        self.assertEqual(batch.successful_source_count, 2)
        self.assertEqual(batch.failed_source_count, 0)
        self.assertEqual(batch.event_count, 2)
        self.assertEqual(batch.published_event_count, 2)
        self.assertEqual(
            [event["title"] for event in batch.events],
            [
                "Working exhibition",
                "Second exhibition",
            ],
        )
        self.assertIsNotNone(batch.finished_at)

    def test_failed_source_does_not_block_other_sources(self):
        batch = run_collectors(
            [
                WorkingCollector(),
                PartiallyFailedCollector(),
                SecondWorkingCollector(),
            ]
        )

        self.assertEqual(batch.source_count, 3)
        self.assertEqual(batch.successful_source_count, 2)
        self.assertEqual(batch.failed_source_count, 1)

        # The failed source did return one partial record,
        # so it is counted for diagnostics.
        self.assertEqual(batch.event_count, 3)

        # Partial records from failed sources must not be published.
        self.assertEqual(batch.published_event_count, 2)
        self.assertEqual(
            {
                event["source"]
                for event in batch.events
            },
            {
                "working",
                "second-working",
            },
        )

        failed_result = batch.results[1]

        self.assertFalse(failed_result.succeeded)
        self.assertEqual(
            failed_result.errors,
            ["Source stopped before completion"],
        )

    def test_invalid_collector_setup_becomes_failed_result(self):
        batch = run_collectors(
            [
                WorkingCollector(),
                InvalidCollector(),
            ]
        )

        self.assertEqual(batch.source_count, 2)
        self.assertEqual(batch.successful_source_count, 1)
        self.assertEqual(batch.failed_source_count, 1)
        self.assertEqual(batch.published_event_count, 1)

        failed_result = batch.results[1]

        self.assertEqual(
            failed_result.source_id,
            "InvalidCollector",
        )
        self.assertIn(
            "Collector setup failed: ValueError",
            failed_result.errors[0],
        )

    def test_supplied_context_is_reused_by_batch(self):
        context = CollectorContext.create(
            settings={"environment": "test"}
        )

        batch = run_collectors(
            [WorkingCollector()],
            context=context,
        )

        self.assertEqual(batch.run_id, context.run_id)
        self.assertEqual(
            batch.started_at,
            context.started_at,
        )

    def test_summary_contains_source_diagnostics(self):
        batch = run_collectors(
            [
                WorkingCollector(),
                PartiallyFailedCollector(),
            ]
        )

        summary = batch.as_summary()

        self.assertEqual(summary["sourceCount"], 2)
        self.assertEqual(summary["successfulSourceCount"], 1)
        self.assertEqual(summary["failedSourceCount"], 1)
        self.assertEqual(summary["eventCount"], 2)
        self.assertEqual(summary["publishedEventCount"], 1)
        self.assertEqual(len(summary["sources"]), 2)
        self.assertIsNotNone(summary["finishedAt"])
        self.assertGreaterEqual(
            summary["durationSeconds"],
            0,
        )


if __name__ == "__main__":
    unittest.main()
