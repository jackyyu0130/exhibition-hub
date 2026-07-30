#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from exhibition_hub.collectors import (
    CollectorRunner,
    audit_collector_coverage,
    collector_registry,
)
from exhibition_hub.collectors.sources import load_collector_sources


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit or run official-source collectors")
    parser.add_argument("--source-registry", default="data/source_registry.json")
    parser.add_argument("--source")
    parser.add_argument("--allow-planned", action="store_true")
    parser.add_argument("--audit-only", action="store_true")
    parser.add_argument("--fetch-details", action="store_true")
    parser.add_argument("--detail-limit", type=int, default=0)
    parser.add_argument("--detail-retry-rounds", type=int, default=1)
    parser.add_argument("--report-output", default="collector-framework-report.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.fetch_details:
        detail_limit = str(max(0, args.detail_limit))
        detail_retry_rounds = str(max(0, args.detail_retry_rounds))
        os.environ["EXHIBITION_HUB_FETCH_DETAILS"] = "1"
        os.environ["EXHIBITION_HUB_DETAIL_LIMIT"] = detail_limit
        os.environ["EXHIBITION_HUB_DETAIL_RETRY_ROUNDS"] = detail_retry_rounds
        # Backward compatibility for the existing Huashan collector.
        os.environ["EXHIBITION_HUB_HUASHAN_FETCH_DETAILS"] = "1"
        os.environ["EXHIBITION_HUB_HUASHAN_DETAIL_LIMIT"] = detail_limit
        os.environ[
            "EXHIBITION_HUB_HUASHAN_DETAIL_RETRY_ROUNDS"
        ] = detail_retry_rounds
    sources = load_collector_sources(args.source_registry)

    if args.audit_only or not args.source:
        report = audit_collector_coverage(sources, collector_registry)
        exit_code = 0 if report["frameworkReady"] else 1
    else:
        source = next((item for item in sources if item.id == args.source), None)
        if source is None:
            report = {
                "mode": "collector-run",
                "sourceId": args.source,
                "status": "failed",
                "errors": ["Source is not registered in source_registry.json"],
            }
            exit_code = 2
        else:
            result = CollectorRunner(collector_registry).run_source(
                source,
                allow_planned=args.allow_planned,
            )
            report = {"mode": "collector-run", **result.to_dict()}
            exit_code = 0 if result.success else 2

    output = json.dumps(report, ensure_ascii=False, indent=2)
    Path(args.report_output).write_text(output + "\n", encoding="utf-8")
    print(output)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
