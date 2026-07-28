import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from exhibition_hub.collectors import (  # noqa: E402
    BatchExecutionPolicy,
    CollectorBatchExecutor,
    CollectorRunReport,
    CollectorSource,
    SourceBatch,
    load_source_batch_registry,
)


def source(
    source_id: str,
) -> CollectorSource:
    return CollectorSource.from_mapping({
        "id": source_id,
        "name": source_id,
        "status": "active",
        "enabled": True,
        "parser": "test",
        "officialUrl": (
            "https://example.com"
        ),
        "listingUrl": (
            "https://example.com/list"
        ),
        "trustLevel": "official",
        "refreshHours": 12,
    })


class ScenarioRunner:
    def __init__(self) -> None:
        self.calls = {}

    def run_source(
        self,
        active_source,
        *,
        allow_planned=False,
        timeout_seconds=None,
    ):
        count = (
            self.calls.get(
                active_source.id,
                0,
            )
            + 1
        )
        self.calls[
            active_source.id
        ] = count

        if active_source.id == "recover":
            if count == 1:
                return CollectorRunReport(
                    source_id=(
                        active_source.id
                    ),
                    status="failed",
                    errors=["temporary"],
                )
        if active_source.id == "timeout":
            raise TimeoutError("slow")
        return CollectorRunReport(
            source_id=active_source.id,
            status="success",
        )


class CollectorBatchResilienceTests(
    unittest.TestCase
):
    def setUp(self):
        self.batch = SourceBatch(
            id="batch",
            name="Batch",
            enabled=True,
            region_group_ids=(),
            source_ids=(
                "healthy",
                "recover",
                "timeout",
            ),
            organizer_ids=(),
            failure_policy=(
                "isolate_source"
            ),
        )
        self.policy = (
            BatchExecutionPolicy(
                max_attempts_per_source=2,
                retry_backoff_seconds=0,
                source_timeout_seconds=1,
                slow_source_threshold_ms=1000,
            )
        )

    def test_retry_recovery_and_timeout_are_reported(self):
        report = (
            CollectorBatchExecutor(
                ScenarioRunner(),
                sleeper=lambda _: None,
            ).run(
                self.batch,
                [
                    source("healthy"),
                    source("recover"),
                    source("timeout"),
                ],
                policy=self.policy,
            )
        )

        self.assertEqual(
            report.status,
            "partial",
        )
        self.assertEqual(
            report.successful_source_count,
            2,
        )
        self.assertEqual(
            report.failed_source_count,
            1,
        )
        self.assertEqual(
            report.recovered_source_count,
            1,
        )
        self.assertEqual(
            report.timed_out_source_count,
            1,
        )
        self.assertEqual(
            report.health_status,
            "degraded",
        )
        self.assertEqual(
            report.retries_used,
            2,
        )

    def test_policy_is_loaded_from_registry_defaults(self):
        registry = (
            load_source_batch_registry(
                ROOT
                / "data"
                / "source_batches.json",
                known_source_ids=[
                    "culture-ministry",
                    "huashan-1914",
                    "songshan-cultural-park",
                    "pier-2",
                    "opentix",
                    "taipei-music-center",
                    "kaohsiung-music-center",
                ],
            )
        )
        self.assertEqual(
            registry.execution_policy
            .max_attempts_per_source,
            3,
        )
        self.assertEqual(
            registry.execution_policy
            .source_timeout_seconds,
            180,
        )

    def test_batch_override_replaces_default_policy(self):
        batch = SourceBatch(
            id="override",
            name="Override",
            enabled=True,
            region_group_ids=(),
            source_ids=(),
            organizer_ids=(),
            failure_policy=(
                "isolate_source"
            ),
            max_attempts_per_source=4,
            source_timeout_seconds=30,
        )
        resolved = batch.resolve_policy(
            BatchExecutionPolicy()
        )
        self.assertEqual(
            resolved.max_attempts_per_source,
            4,
        )
        self.assertEqual(
            resolved.source_timeout_seconds,
            30,
        )


if __name__ == "__main__":
    unittest.main()
