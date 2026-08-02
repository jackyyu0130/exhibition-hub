#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any

from exhibition_hub.threads_discovery import discover_threads


def read_json(path: str | Path, default: Any) -> Any:
    target = Path(path)
    if not target.exists():
        return default
    return json.loads(target.read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Discover public Threads exhibition candidates through Meta's official keyword_search API"
    )
    parser.add_argument("--config", default="data/threads_search_config.json")
    parser.add_argument("--events", default="data/exhibitions.curated.json")
    parser.add_argument("--output", default="social-review-artifact/threads_candidates.json")
    parser.add_argument("--signals-output", default="social-review-artifact/threads_new_event_signals.json")
    parser.add_argument("--report", default="social-review-artifact/threads_discovery_report.json")
    parser.add_argument("--token-env", default="THREADS_ACCESS_TOKEN")
    parser.add_argument("--include-top", action="store_true")
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    config = read_json(args.config, {})
    event_payload = read_json(args.events, {"events": []})
    events = (
        event_payload.get("events") or []
        if isinstance(event_payload, dict)
        else event_payload
    )
    token = os.environ.get(args.token_env, "").strip()

    if not token:
        candidate_payload = {
            "schemaVersion": 1,
            "generatedAt": now.isoformat(),
            "status": "not_configured",
            "reviewRequired": True,
            "publishAllowed": False,
            "candidates": [],
        }
        report = {
            "schemaVersion": 1,
            "generatedAt": now.isoformat(),
            "status": "not_configured",
            "requiredSecret": args.token_env,
            "requiredPermission": config.get("requiredPermission", "threads_keyword_search"),
            "candidateCount": 0,
            "message": "Threads Token 尚未設定；已安全跳過 Threads，PTT 與人工候選仍可繼續執行。",
        }
        write_json(args.output, candidate_payload)
        write_json(
            args.signals_output,
            {
                "schemaVersion": 1,
                "generatedAt": now.isoformat(),
                "signals": [],
            },
        )
        write_json(args.report, report)
        print(json.dumps(report, ensure_ascii=False))
        return 0

    candidates, report = discover_threads(
        config,
        events,
        token=token,
        now=now,
        include_top=args.include_top,
    )
    write_json(
        args.output,
        {
            "schemaVersion": 1,
            "generatedAt": now.isoformat(),
            "status": report.get("status"),
            "reviewRequired": True,
            "publishAllowed": False,
            "candidates": candidates,
        },
    )
    # The final match is calculated by run_social_discovery.py. At this stage,
    # every result is only a possible discussion or new-event discovery signal.
    write_json(
        args.signals_output,
        {
            "schemaVersion": 1,
            "generatedAt": now.isoformat(),
            "reviewRequired": True,
            "publishAllowed": False,
            "signals": candidates,
        },
    )
    write_json(args.report, report)
    print(
        json.dumps(
            {
                "status": report.get("status"),
                "candidateCount": len(candidates),
                "publishAllowed": False,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
