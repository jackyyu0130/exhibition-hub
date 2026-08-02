#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from typing import Any, Mapping

import requests

from exhibition_hub.c4_monitor import (
    PageParser,
    detail_records,
    existing_index,
    listing_links,
    make_candidate,
    normalize_url,
)


def read_json(path: str | Path, default: Any) -> Any:
    target = Path(path)
    if not target.exists():
        return default
    return json.loads(target.read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Monitor C4 official sources and build venue-matched candidates")
    parser.add_argument("--registry", default="data/c4_monitored_sources.json")
    parser.add_argument("--state", default="data/c4_monitor_state.json")
    parser.add_argument("--events", default="data/exhibitions.enriched.json")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--max-detail-pages", type=int, default=12)
    parser.add_argument("--request-delay", type=float, default=0.7)
    return parser.parse_args()


def endpoint_rows(registry: Mapping[str, Any], shard_count: int, shard_index: int) -> list[tuple[Mapping[str, Any], Mapping[str, Any]]]:
    rows: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
    for org in registry.get("organizations") or []:
        if not isinstance(org, Mapping):
            continue
        for endpoint in org.get("endpoints") or []:
            if not isinstance(endpoint, Mapping) or not endpoint.get("enabled"):
                continue
            if endpoint.get("accessMode") not in {"public_html", "kktix_organizer"}:
                continue
            rows.append((org, endpoint))
    rows.sort(key=lambda item: (-int(item[1].get("priority") or 0), str(item[1].get("id") or "")))
    return [row for index, row in enumerate(rows) if index % shard_count == shard_index]


def main() -> int:
    args = parse_args()
    if args.shard_count < 1 or not 0 <= args.shard_index < args.shard_count:
        raise SystemExit("Invalid shard settings")

    registry = read_json(args.registry, {})
    state = read_json(args.state, {"schemaVersion": 1, "endpoints": {}})
    events = read_json(args.events, {"events": []})
    existing = existing_index(events)
    now = datetime.now(timezone.utc)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    headers = {
        "User-Agent": "TaiwanExhibitionJournal-C4Monitor/1.0 (+https://twexhibition.com/)",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.5",
    }
    session = requests.Session()
    candidates = []
    reports = []
    next_state: dict[str, Any] = {"schemaVersion": 1, "updatedAt": now.isoformat(), "endpoints": {}}

    for organization, endpoint in endpoint_rows(registry, args.shard_count, args.shard_index):
        endpoint_id = str(endpoint.get("id") or "")
        source_url = normalize_url(str(endpoint.get("url") or ""))
        report: dict[str, Any] = {
            "sourceId": organization.get("id"),
            "sourceName": organization.get("name"),
            "endpointId": endpoint_id,
            "platform": endpoint.get("platform"),
            "url": source_url,
            "status": "pending",
            "listingCandidateCount": 0,
            "candidateCount": 0,
            "autoPublishEligibleCount": 0,
            "errors": [],
        }
        previous = (state.get("endpoints") or {}).get(endpoint_id) or {}
        next_entry = dict(previous)
        next_entry.update({"lastAttemptAt": now.isoformat(), "lastUrl": source_url})
        try:
            response = session.get(source_url, headers=headers, timeout=25, allow_redirects=True)
            response.raise_for_status()
            final_url = normalize_url(response.url)
            parser = PageParser(final_url)
            parser.feed(response.text)
            links = listing_links(parser, endpoint)
            report["listingCandidateCount"] = len(links)

            raw_records: list[dict[str, Any]] = []
            raw_records.extend(detail_records(parser, final_url))
            for link in links[: args.max_detail_pages]:
                try:
                    detail = session.get(link["url"], headers=headers, timeout=25, allow_redirects=True)
                    detail.raise_for_status()
                    detail_parser = PageParser(normalize_url(detail.url))
                    detail_parser.feed(detail.text)
                    raw_records.extend(detail_records(detail_parser, normalize_url(detail.url), link.get("text", "")))
                except Exception as exc:  # source-level isolation
                    report["errors"].append(f"detail:{type(exc).__name__}:{exc}")
                time.sleep(max(0.0, args.request_delay))

            seen: set[str] = set()
            for raw in raw_records:
                candidate = make_candidate(raw, organization, endpoint, registry, existing, now=now)
                if candidate.candidateId in seen:
                    continue
                seen.add(candidate.candidateId)
                candidates.append(candidate.to_dict())
            report["candidateCount"] = len(seen)
            report["autoPublishEligibleCount"] = sum(1 for item in candidates if item["endpointId"] == endpoint_id and item["autoPublishEligible"])
            report["status"] = "success" if not report["errors"] else "partial"
            next_entry.update({
                "lastSuccessAt": now.isoformat(),
                "lastStatus": report["status"],
                "lastCandidateCount": report["candidateCount"],
                "lastAutoPublishEligibleCount": report["autoPublishEligibleCount"],
                "consecutiveFailures": 0,
            })
        except Exception as exc:
            report["status"] = "failed"
            report["errors"].append(f"listing:{type(exc).__name__}:{exc}")
            next_entry.update({
                "lastStatus": "failed",
                "lastError": report["errors"][-1],
                "consecutiveFailures": int(previous.get("consecutiveFailures") or 0) + 1,
            })
        reports.append(report)
        next_state["endpoints"][endpoint_id] = next_entry
        time.sleep(max(0.0, args.request_delay))

    payload = {
        "schemaVersion": 1,
        "generatedAt": now.isoformat(),
        "shardCount": args.shard_count,
        "shardIndex": args.shard_index,
        "sourceCount": len(reports),
        "candidateCount": len(candidates),
        "autoPublishEligibleCount": sum(1 for item in candidates if item.get("autoPublishEligible")),
        "candidates": candidates,
    }
    report_payload = {
        "schemaVersion": 1,
        "generatedAt": now.isoformat(),
        "shardCount": args.shard_count,
        "shardIndex": args.shard_index,
        "sourceCount": len(reports),
        "successfulSourceCount": sum(1 for item in reports if item["status"] in {"success", "partial"}),
        "failedSourceCount": sum(1 for item in reports if item["status"] == "failed"),
        "candidateCount": len(candidates),
        "autoPublishEligibleCount": payload["autoPublishEligibleCount"],
        "sources": reports,
        "publicDataWritten": False,
    }
    write_json(out / "candidates.json", payload)
    write_json(out / "report.json", report_payload)
    write_json(out / "state.json", next_state)
    print(json.dumps(report_payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
