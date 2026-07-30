#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate an official-source batch "
            "health report."
        )
    )
    parser.add_argument(
        "--input",
        required=True,
    )
    parser.add_argument(
        "--max-failed-sources",
        type=int,
        default=0,
    )
    parser.add_argument(
        "--max-timeouts",
        type=int,
        default=0,
    )
    parser.add_argument(
        "--require-records",
        action="store_true",
    )
    parser.add_argument(
        "--output",
        required=True,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = json.loads(
        Path(args.input).read_text(
            encoding="utf-8"
        )
    )
    gates = {
        "healthReportMode": (
            payload.get("mode")
            == "collector-batch-health"
        ),
        "sourceCountPositive": (
            int(
                payload.get("sourceCount")
                or 0
            )
            > 0
        ),
        "failedSourcesWithinLimit": (
            int(
                payload.get(
                    "failedSourceCount"
                )
                or 0
            )
            <= max(
                0,
                args.max_failed_sources,
            )
        ),
        "timeoutsWithinLimit": (
            int(
                payload.get(
                    "timedOutSourceCount"
                )
                or 0
            )
            <= max(
                0,
                args.max_timeouts,
            )
        ),
        "recordsPresent": (
            not args.require_records
            or int(
                payload.get("recordCount")
                or 0
            )
            > 0
        ),
        "notUnhealthy": (
            payload.get("status")
            != "unhealthy"
        ),
    }
    failed = [
        gate_id
        for gate_id, passed
        in gates.items()
        if not passed
    ]
    report = {
        "mode": (
            "collector-batch-health-validation"
        ),
        "passed": not failed,
        "batchId": payload.get(
            "batchId"
        ),
        "healthStatus": payload.get(
            "status"
        ),
        "gates": gates,
        "failedGateIds": failed,
    }
    Path(args.output).write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
