#!/usr/bin/env python3
"""Build the lightweight public exhibition feed from the enriched audit feed."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from exhibition_hub.curation import build_curated_payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/exhibitions.enriched.json")
    parser.add_argument("--matrix", default="data/taiwan_venue_matrix.json")
    parser.add_argument("--output", default="data/exhibitions.curated.json")
    parser.add_argument("--report", default="data/update-reports/curated-feed-report.json")
    return parser.parse_args()


def read_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    payload, report = build_curated_payload(read_json(args.input), read_json(args.matrix))
    write_json(args.output, payload)
    write_json(args.report, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
