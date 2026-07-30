#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from exhibition_hub.merging.quality import (
    evaluate_source_merge_candidate,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a non-published official-source "
            "merge candidate"
        )
    )
    parser.add_argument("--base", required=True)
    parser.add_argument("--source-run", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--merge-report", required=True)
    parser.add_argument("--review", required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument(
        "--require-full-details",
        action="store_true",
    )
    parser.add_argument(
        "--max-review",
        type=int,
        default=0,
    )
    parser.add_argument(
        "--output",
        default="source-merge-quality-report.json",
    )
    return parser.parse_args()


def load_json(path: str) -> object:
    return json.loads(
        Path(path).read_text(encoding="utf-8")
    )


def main() -> int:
    args = parse_args()
    review = load_json(args.review)
    if not isinstance(review, list):
        raise ValueError(
            "Review queue JSON must be a list"
        )

    report = evaluate_source_merge_candidate(
        base_payload=load_json(args.base),
        source_run=load_json(args.source_run),
        candidate=load_json(args.candidate),
        merge_report=load_json(args.merge_report),
        review_queue=review,
        source_id=args.source_id,
        require_full_details=args.require_full_details,
        max_review=max(0, args.max_review),
    )
    output = json.dumps(
        report,
        ensure_ascii=False,
        indent=2,
    )
    Path(args.output).write_text(
        output + "\n",
        encoding="utf-8",
    )
    print(output)
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
