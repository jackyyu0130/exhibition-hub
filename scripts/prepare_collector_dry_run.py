#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from exhibition_hub.collectors.release import build_dry_run_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a non-publishing Collector stage 7/8 dry-run report."
    )
    parser.add_argument("--stage", default="stage-7-daily-dry-run")
    parser.add_argument("--release-stages", default="data/collector_release_stages.json")
    parser.add_argument("--source-registry", default="data/source_registry.json")
    parser.add_argument("--source-batches", default="data/source_batches.json")
    parser.add_argument("--input-report", action="append", default=[])
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default="collector-dry-run-report.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_dry_run_report(
        stage_path=args.release_stages,
        stage_id=args.stage,
        source_registry_path=args.source_registry,
        source_batches_path=args.source_batches,
        input_reports=args.input_report,
        root=args.root,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
