import json
import sys
import tempfile
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
    *,
    enabled: bool = True,
) -> CollectorSource:
    return CollectorSource.from_mapping({
        "id": source_id,
        "name": source_id,
        "status": (
            "active"
            if enabled
            else "planned"
        ),
        "enabled": enabled,
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


class FakeRunner:
    def __init__(
        self,
        failing=(),
    ):
        self.failing = set(failing)
        self.called = []

    def run_source(
        self,
        active_source,
        *,
        allow_planned=False,
    ):
        self.called.append(
            active_source.id
        )
        if (
            active_source.id
            in self.failing
        ):
            return CollectorRunReport(
                source_id=(
                    active_source.id
                ),
                status="failed",
                errors=[
                    "simulated failure"
                ],
            )
        return CollectorRunReport(
            source_id=active_source.id,
            status="success",
        )


class CollectorBatchExecutorTests(
    unittest.TestCase
):
    def test_current_registry_has_enabled_active_batch(self):
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
        batch = registry.get(
            "active-official-venues"
        )
        self.assertIsNotNone(batch)
        self.assertTrue(batch.enabled)
        self.assertEqual(
            batch.source_ids,
            ("huashan-1914",),
        )

    def test_disabled_batch_is_skipped_by_default(self):
        batch = SourceBatch(
            id="disabled",
            name="Disabled",
            enabled=False,
            region_group_ids=(),
            source_ids=("a",),
            organizer_ids=(),
            failure_policy=(
                "isolate_source"
            ),
        )
        runner = FakeRunner()
        report = (
            CollectorBatchExecutor(
                runner
            ).run(
                batch,
                [source("a")],
            )
        )
        self.assertEqual(
            report.status,
            "skipped",
        )
        self.assertEqual(
            runner.called,
            [],
        )

    def test_disabled_source_is_reported_as_skipped(self):
        batch = SourceBatch(
            id="batch",
            name="Batch",
            enabled=True,
            region_group_ids=(),
            source_ids=("a", "b"),
            organizer_ids=(),
            failure_policy=(
                "isolate_source"
            ),
        )
        report = (
            CollectorBatchExecutor(
                FakeRunner()
            ).run(
                batch,
                [
                    source("a"),
                    source(
                        "b",
                        enabled=False,
                    ),
                ],
            )
        )
        self.assertEqual(
            report.status,
            "success",
        )
        self.assertEqual(
            report.runnable_source_ids,
            ["a"],
        )
        self.assertEqual(
            report.skipped_sources,
            [{
                "sourceId": "b",
                "reason": (
                    "disabled_or_planned"
                ),
            }],
        )

    def test_isolate_source_continues_after_failure(self):
        batch = SourceBatch(
            id="batch",
            name="Batch",
            enabled=True,
            region_group_ids=(),
            source_ids=(
                "a",
                "b",
                "c",
            ),
            organizer_ids=(),
            failure_policy=(
                "isolate_source"
            ),
        )
        runner = FakeRunner(
            failing={"b"}
        )
        report = (
            CollectorBatchExecutor(
                runner
            ).run(
                batch,
                [
                    source("a"),
                    source("b"),
                    source("c"),
                ],
                policy=BatchExecutionPolicy(
                    max_attempts_per_source=1,
                    retry_backoff_seconds=0,
                    source_timeout_seconds=30,
                    slow_source_threshold_ms=1000,
                ),
            )
        )
        self.assertEqual(
            runner.called,
            ["a", "b", "c"],
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

    def test_max_sources_per_run_is_enforced(self):
        payload = {
            "schemaVersion": 1,
            "regionGroups": [],
            "batches": [{
                "id": "too-many",
                "name": "Too many",
                "enabled": True,
                "sourceIds": [
                    "a",
                    "b",
                ],
                "regionGroupIds": [],
                "organizerIds": [],
                "failurePolicy": (
                    "isolate_source"
                ),
            }],
            "defaults": {
                "maxSourcesPerRun": 1,
                "failurePolicy": (
                    "isolate_source"
                ),
                "allowFutureSourceIds": True,
                "allowOrganizerExpansion": True,
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            path = (
                Path(directory)
                / "batches.json"
            )
            path.write_text(
                json.dumps(payload),
                encoding="utf-8",
            )
            with self.assertRaises(
                ValueError
            ):
                load_source_batch_registry(
                    path,
                    known_source_ids=[
                        "a",
                        "b",
                    ],
                )


if __name__ == "__main__":
    unittest.main()
