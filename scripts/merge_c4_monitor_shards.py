#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input-dir", required=True)
    p.add_argument("--base-state", default="data/c4_monitor_state.json")
    p.add_argument("--candidates", required=True)
    p.add_argument("--report", required=True)
    p.add_argument("--state", required=True)
    p.add_argument("--public-status", required=True)
    args = p.parse_args()

    root = Path(args.input_dir)
    base_state = read(Path(args.base_state)) if Path(args.base_state).exists() else {"schemaVersion": 1, "endpoints": {}}
    candidates: dict[str, dict[str, Any]] = {}
    reports: list[dict[str, Any]] = []
    endpoints = dict(base_state.get("endpoints") or {})
    generated = datetime.now(timezone.utc).isoformat()

    for file in sorted(root.rglob("candidates.json")):
        payload = read(file)
        generated = max(generated, str(payload.get("generatedAt") or ""))
        for item in payload.get("candidates") or []:
            if isinstance(item, dict) and item.get("candidateId"):
                candidates[str(item["candidateId"])] = item
    for file in sorted(root.rglob("report.json")):
        payload = read(file)
        reports.extend(item for item in payload.get("sources") or [] if isinstance(item, dict))
    for file in sorted(root.rglob("state.json")):
        payload = read(file)
        endpoints.update(payload.get("endpoints") or {})

    candidate_rows = sorted(candidates.values(), key=lambda item: (str(item.get("startDate") or "9999"), str(item.get("title") or "")))
    report = {
        "schemaVersion": 1,
        "generatedAt": generated,
        "sourceCount": len(reports),
        "successfulSourceCount": sum(1 for item in reports if item.get("status") in {"success", "partial"}),
        "failedSourceCount": sum(1 for item in reports if item.get("status") == "failed"),
        "candidateCount": len(candidate_rows),
        "autoPublishEligibleCount": sum(1 for item in candidate_rows if item.get("autoPublishEligible")),
        "sources": sorted(reports, key=lambda item: str(item.get("endpointId") or "")),
        "published": False,
    }
    public_status = {
        "schemaVersion": 1,
        "updatedAt": generated,
        "monitoredPublicSourceCount": len(reports),
        "healthySourceCount": report["successfulSourceCount"],
        "failedSourceCount": report["failedSourceCount"],
        "candidateCount": report["candidateCount"],
        "autoPublishEligibleCount": report["autoPublishEligibleCount"],
        "schedule": "每天 04:00（台灣時間）",
        "socialApiStatus": "Instagram／Facebook 需 Meta 正式 API 與授權；尚未啟用的社群端點不會模擬登入或爬取。",
    }
    write(Path(args.candidates), {"schemaVersion": 1, "generatedAt": generated, "candidates": candidate_rows})
    write(Path(args.report), report)
    write(Path(args.state), {"schemaVersion": 1, "updatedAt": generated, "endpoints": endpoints})
    write(Path(args.public_status), public_status)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
