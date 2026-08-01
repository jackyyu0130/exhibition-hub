#!/usr/bin/env python3
"""Audit public ticket prices without trusting precise-looking source fragments."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from exhibition_hub.curation import sanitize_public_price  # noqa: E402


def audit_payload(payload: dict[str, Any], source: str) -> dict[str, Any]:
    corrections: list[dict[str, Any]] = []
    events = payload.get("events") or []
    for event in events:
        if not isinstance(event, dict):
            continue
        original = str(event.get("price") or "").strip()
        public, reason = sanitize_public_price(event)
        if reason and public != original:
            corrections.append({
                "id": event.get("id"),
                "title": event.get("title"),
                "originalPrice": original,
                "publicPrice": public,
                "reason": reason,
                "sourceUrl": event.get("sourceUrl"),
            })
    reasons: dict[str, int] = {}
    for item in corrections:
        reasons[item["reason"]] = reasons.get(item["reason"], 0) + 1
    return {
        "source": source,
        "eventCount": len(events),
        "correctionCount": len(corrections),
        "correctionReasons": dict(sorted(reasons.items())),
        "samples": corrections[:100],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    reports = []
    for path in args.inputs:
        payload = json.loads(path.read_text(encoding="utf-8"))
        reports.append(audit_payload(payload, str(path)))
    output = {
        "schemaVersion": 1,
        "audit": "public-ticket-price-sanity",
        "reports": reports,
        "totalCorrections": sum(item["correctionCount"] for item in reports),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
