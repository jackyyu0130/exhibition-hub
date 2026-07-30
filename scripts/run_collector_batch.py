#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from exhibition_hub.collectors import (
    BatchExecutionPolicy,
    CollectorBatchExecutor,
    SubprocessCollectorRunner,
    load_source_batch_registry,
)
from exhibition_hub.collectors.sources import (
    load_collector_sources,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a resilient official-source batch "
            "from data/source_batches.json"
        )
    )
    parser.add_argument(
        "--batch",
        required=True,
    )
    parser.add_argument(
        "--source-batches",
        default="data/source_batches.json",
    )
    parser.add_argument(
        "--source-registry",
        default="data/source_registry.json",
    )
    parser.add_argument(
        "--allow-disabled-batch",
        action="store_true",
    )
    parser.add_argument(
        "--allow-planned",
        action="store_true",
    )
    parser.add_argument(
        "--fetch-details",
        action="store_true",
    )
    parser.add_argument(
        "--detail-limit",
        type=int,
        default=0,
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Exit non-zero when any source "
            "remains failed after retries."
        ),
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
    )
    parser.add_argument(
        "--retry-backoff-seconds",
        type=float,
    )
    parser.add_argument(
        "--source-timeout-seconds",
        type=float,
    )
    parser.add_argument(
        "--slow-source-threshold-ms",
        type=int,
    )
    parser.add_argument(
        "--output-dir",
        default="collector-batch-output",
    )
    parser.add_argument(
        "--report-output",
        default="collector-batch-report.json",
    )
    parser.add_argument(
        "--health-output",
        default="collector-batch-health.json",
    )
    return parser.parse_args()


def write_json(
    path: Path,
    payload: object,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    sources = load_collector_sources(
        args.source_registry
    )
    registry = (
        load_source_batch_registry(
            args.source_batches,
            known_source_ids=[
                source.id
                for source in sources
            ],
        )
    )
    batch = registry.get(args.batch)
    if batch is None:
        output = {
            "mode": "collector-batch-run",
            "batchId": args.batch,
            "status": "failed",
            "success": False,
            "errors": [
                "Batch is not registered in "
                "source_batches.json"
            ],
        }
        write_json(
            Path(args.report_output),
            output,
        )
        return 2

    resolved = registry.resolve_policy(
        batch
    )
    policy = BatchExecutionPolicy(
        max_attempts_per_source=(
            args.max_attempts
            if args.max_attempts is not None
            else resolved.max_attempts_per_source
        ),
        retry_backoff_seconds=(
            args.retry_backoff_seconds
            if args.retry_backoff_seconds is not None
            else resolved.retry_backoff_seconds
        ),
        source_timeout_seconds=(
            args.source_timeout_seconds
            if args.source_timeout_seconds is not None
            else resolved.source_timeout_seconds
        ),
        slow_source_threshold_ms=(
            args.slow_source_threshold_ms
            if args.slow_source_threshold_ms is not None
            else resolved.slow_source_threshold_ms
        ),
    )

    runner = SubprocessCollectorRunner(
        source_registry=(
            args.source_registry
        ),
        fetch_details=(
            args.fetch_details
        ),
        detail_limit=(
            args.detail_limit
        ),
    )
    report = CollectorBatchExecutor(
        runner
    ).run(
        batch,
        sources,
        policy=policy,
        allow_disabled_batch=(
            args.allow_disabled_batch
        ),
        allow_planned=(
            args.allow_planned
        ),
    )
    payload = report.to_dict()
    health = report.health_report()

    output_dir = Path(
        args.output_dir
    )
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )
    write_json(
        output_dir
        / "batch-report.json",
        payload,
    )
    write_json(
        output_dir
        / "health-report.json",
        health,
    )

    all_records: list[dict] = []
    for source_report in (
        payload.get("sources")
        or []
    ):
        source_id = str(
            source_report.get("sourceId")
            or "unknown-source"
        )
        write_json(
            output_dir
            / "sources"
            / f"{source_id}.json",
            source_report,
        )
        all_records.extend(
            source_report.get("records")
            or []
        )

    write_json(
        output_dir
        / "records.json",
        {
            "batchId": payload.get(
                "batchId"
            ),
            "recordCount": len(
                all_records
            ),
            "records": all_records,
        },
    )
    write_json(
        Path(args.report_output),
        payload,
    )
    write_json(
        Path(args.health_output),
        health,
    )
    print(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
    )

    if (
        args.strict
        and report.failed_source_count
    ):
        return 2
    if report.status == "failed":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
