#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from exhibition_hub.merging import (
    build_source_merge_candidate,
)
from exhibition_hub.merging.candidate import load_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a non-published candidate by merging "
            "an official collector run into enriched events"
        )
    )
    parser.add_argument(
        "--base",
        default="data/exhibitions.enriched.json",
    )
    parser.add_argument("--source-run", required=True)
    parser.add_argument(
        "--source-registry",
        default="data/source_registry.json",
    )
    parser.add_argument(
        "--source-id",
        required=True,
    )
    parser.add_argument(
        "--candidate-output",
        default="source-merge-candidate.json",
    )
    parser.add_argument(
        "--report-output",
        default="source-merge-report.json",
    )
    parser.add_argument(
        "--review-output",
        default="source-merge-review.json",
    )
    return parser.parse_args()


def write_json(path: str, payload: object) -> None:
    Path(path).write_text(
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
    candidate, report, review = (
        build_source_merge_candidate(
            load_json(args.base),
            load_json(args.source_run),
            load_json(args.source_registry),
            source_id=args.source_id,
        )
    )
    write_json(args.candidate_output, candidate)
    write_json(args.report_output, report)
    write_json(args.review_output, review)
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "mode",
                    "published",
                    "sourceId",
                    "baseEventCount",
                    "sourceRecordCount",
                    "detailFetchedCount",
                    "candidateEventCount",
                    "decisionCounts",
                    "reviewQueueCount",
                )
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
