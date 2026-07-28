#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from exhibition_hub.collectors import (
    BatchExecutionPolicy,
    CollectorBatchExecutor,
    CollectorRunReport,
    CollectorSource,
    SourceBatch,
)


class SimulationRunner:
    def __init__(self) -> None:
        self.attempts: dict[
            str, int
        ] = {}

    def run_source(
        self,
        source: CollectorSource,
        *,
        allow_planned: bool = False,
        timeout_seconds: float | None = None,
    ) -> CollectorRunReport:
        attempt = (
            self.attempts.get(
                source.id,
                0,
            )
            + 1
        )
        self.attempts[
            source.id
        ] = attempt

        if source.id == "recovering":
            if attempt == 1:
                return CollectorRunReport(
                    source_id=source.id,
                    status="failed",
                    errors=[
                        "simulated transient failure"
                    ],
                )
            return CollectorRunReport(
                source_id=source.id,
                status="success",
            )

        if source.id == "timeout":
            raise TimeoutError(
                "simulated timeout"
            )

        return CollectorRunReport(
            source_id=source.id,
            status="success",
        )


def source(
    source_id: str,
) -> CollectorSource:
    return CollectorSource.from_mapping({
        "id": source_id,
        "name": source_id,
        "status": "active",
        "enabled": True,
        "parser": "simulation",
        "officialUrl": (
            "https://example.com"
        ),
        "listingUrl": (
            "https://example.com/list"
        ),
        "trustLevel": "official",
        "refreshHours": 12,
    })


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        required=True,
    )
    args = parser.parse_args()

    batch = SourceBatch(
        id="resilience-simulation",
        name="Resilience simulation",
        enabled=True,
        region_group_ids=(),
        source_ids=(
            "healthy",
            "recovering",
            "timeout",
        ),
        organizer_ids=(),
        failure_policy=(
            "isolate_source"
        ),
    )
    policy = BatchExecutionPolicy(
        max_attempts_per_source=2,
        retry_backoff_seconds=0,
        source_timeout_seconds=0.1,
        slow_source_threshold_ms=1000,
    )
    report = CollectorBatchExecutor(
        SimulationRunner(),
        sleeper=lambda _: None,
    ).run(
        batch,
        [
            source("healthy"),
            source("recovering"),
            source("timeout"),
        ],
        policy=policy,
    )
    payload = report.to_dict()

    assertions = {
        "batchPartial": (
            payload["status"]
            == "partial"
        ),
        "healthySourceContinued": (
            payload[
                "successfulSourceCount"
            ]
            == 2
        ),
        "failedSourceIsolated": (
            payload[
                "failedSourceCount"
            ]
            == 1
        ),
        "retryRecovered": (
            payload[
                "recoveredSourceCount"
            ]
            == 1
        ),
        "timeoutRecorded": (
            payload[
                "timedOutSourceCount"
            ]
            == 1
        ),
        "healthDegraded": (
            payload["health"][
                "status"
            ]
            == "degraded"
        ),
    }
    output = {
        "mode": (
            "collector-batch-resilience-simulation"
        ),
        "passed": all(
            assertions.values()
        ),
        "assertions": assertions,
        "report": payload,
    }
    Path(args.output).write_text(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if output["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
