#!/usr/bin/env python3
from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
from typing import Any, Mapping

from exhibition_hub.collectors import CollectorRunner, collector_registry
from exhibition_hub.collectors.base import CollectorSource
from exhibition_hub.collectors.sources import load_collector_sources
from exhibition_hub.merging import build_source_merge_candidate
from exhibition_hub.merging.candidate import load_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run active official venue collectors with source-level failure isolation"
    )
    parser.add_argument("--base", required=True)
    parser.add_argument("--source-registry", default="data/source_registry.json")
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--diff-output")
    parser.add_argument("--audit-dir", default="production-update-audit/official-sources")
    parser.add_argument("--exclude-source", action="append", default=["huashan-1914"])
    return parser.parse_args()


def write_json(path: str | Path, payload: object) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def publishable_records(report: Mapping[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for record in report.get("records") or []:
        if not isinstance(record, dict):
            continue
        raw = dict(record.get("raw") or {})
        if raw.get("editorialStatus") == "exclude_review":
            continue
        if not raw.get("detailFetched"):
            continue
        if not str(raw.get("title") or record.get("title") or "").strip():
            continue
        if not str(raw.get("officialUrl") or raw.get("detailUrl") or "").startswith(("http://", "https://")):
            continue
        if not str(raw.get("startDate") or "").strip() or not str(raw.get("endDate") or "").strip():
            continue
        if not (raw.get("imageUrl") or raw.get("imageUrls")):
            continue
        records.append(record)
    return records


def event_map(payload: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for event in payload.get("events") or []:
        if not isinstance(event, dict):
            continue
        event_id = str(event.get("id") or "").strip()
        if event_id:
            result[event_id] = event
    return result


def build_official_source_batch_diff(
    base: Mapping[str, Any],
    preview: Mapping[str, Any],
    report: Mapping[str, Any],
) -> dict[str, Any]:
    base_events = [
        event for event in base.get("events") or []
        if isinstance(event, dict)
    ]
    preview_events = [
        event for event in preview.get("events") or []
        if isinstance(event, dict)
    ]
    base_ids = [
        str(event.get("id") or "").strip()
        for event in base_events
    ]
    preview_ids = [
        str(event.get("id") or "").strip()
        for event in preview_events
    ]
    base_id_set = set(base_ids)
    preview_id_set = set(preview_ids)
    removed_ids = sorted(base_id_set - preview_id_set)
    added_ids = sorted(preview_id_set - base_id_set)

    base_by_id = event_map(base)
    preview_by_id = event_map(preview)
    modified_ids = sorted(
        event_id
        for event_id in base_id_set & preview_id_set
        if base_by_id[event_id] != preview_by_id[event_id]
    )

    source_items = [
        item for item in report.get("sources") or []
        if isinstance(item, dict)
    ]
    allowed_statuses = {
        "merged",
        "preserved_previous_base",
    }
    source_statuses_valid = all(
        str(item.get("status") or "") in allowed_statuses
        for item in source_items
    )
    preview_build = preview.get("officialSourceBuild") or {}
    preview_unique = (
        "" not in preview_ids
        and len(preview_ids) == len(set(preview_ids))
    )
    report_count_matches = (
        int(report.get("finalEventCount") or -1)
        == len(preview_events)
    )

    quality_gates = {
        "batchCompleted": True,
        "failureIsolationEnabled": (
            report.get("failureIsolation") is True
        ),
        "batchReportCountMatches": report_count_matches,
        "baseEventsPreserved": not removed_ids,
        "previewIdsUnique": preview_unique,
        "previewBuildUnpublished": (
            preview_build.get("published") is False
        ),
        "sourceStatusesValid": source_statuses_valid,
        "published": False,
    }

    failed_gates = [
        key
        for key, value in quality_gates.items()
        if key != "published" and not value
    ]
    if failed_gates:
        raise ValueError(
            "Official-source batch diff failed gates: "
            + ", ".join(failed_gates)
        )

    return {
        "mode": "official-source-batch-publish-diff",
        "published": False,
        "sourceId": "official-source-batch",
        "baseEventCount": len(base_events),
        "candidateEventCount": len(preview_events),
        "previewEventCount": len(preview_events),
        "addedEventCount": len(added_ids),
        "modifiedEventCount": len(modified_ids),
        "unchangedBaseEventCount": (
            len(base_id_set) - len(modified_ids)
        ),
        "removedBaseEventCount": len(removed_ids),
        "qualityGates": quality_gates,
        "addedIds": added_ids,
        "modifiedIds": modified_ids,
        "removedIds": removed_ids,
        "batchSummary": {
            "sourceCount": int(report.get("sourceCount") or 0),
            "successfulSourceCount": int(
                report.get("successfulSourceCount") or 0
            ),
            "failedSourceCount": int(
                report.get("failedSourceCount") or 0
            ),
            "skippedSourceCount": int(
                report.get("skippedSourceCount") or 0
            ),
        },
    }

def active_official_sources(
    registry_payload: Mapping[str, Any],
    *,
    excluded: set[str],
) -> list[CollectorSource]:
    result: list[CollectorSource] = []
    for item in registry_payload.get("sources") or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("id") or "") in excluded:
            continue
        if item.get("layer") != "venue_official":
            continue
        if item.get("status") != "active" or not item.get("enabled"):
            continue
        result.append(CollectorSource.from_mapping(item))
    return sorted(result, key=lambda source: (-int(source.raw.get("priority") or 0), source.id))


def main() -> int:
    args = parse_args()
    base_payload = load_json(args.base)
    current = deepcopy(base_payload)
    registry_payload = load_json(args.source_registry)
    audit_dir = Path(args.audit_dir)
    audit_dir.mkdir(parents=True, exist_ok=True)

    os.environ["EXHIBITION_HUB_FETCH_DETAILS"] = "1"
    os.environ.setdefault("EXHIBITION_HUB_DETAIL_LIMIT", "0")

    runner = CollectorRunner(collector_registry)
    source_reports: list[dict[str, Any]] = []
    successful_sources = 0
    failed_sources = 0
    skipped_sources = 0

    for source in active_official_sources(
        registry_payload,
        excluded=set(args.exclude_source or []),
    ):
        source_item: dict[str, Any] = {
            "sourceId": source.id,
            "sourceName": source.name,
            "status": "pending",
            "baseEventCount": len(current.get("events") or []),
        }
        try:
            run_report = runner.run_source(source)
            run_payload = run_report.to_dict()
            write_json(audit_dir / f"{source.id}-run.json", run_payload)
            valid = publishable_records(run_payload)
            minimum = max(1, int(source.raw.get("minimumRecords") or 1))
            source_item.update({
                "collectorStatus": run_payload.get("status"),
                "collectorSuccess": bool(run_payload.get("success")),
                "collectedRecordCount": len(run_payload.get("records") or []),
                "publishableRecordCount": len(valid),
                "minimumRecords": minimum,
                "warnings": list(run_payload.get("warnings") or []),
                "errors": list(run_payload.get("errors") or []),
            })
            if not run_payload.get("success") or len(valid) < minimum:
                source_item["status"] = "preserved_previous_base"
                source_item["reason"] = (
                    "collector_failed"
                    if not run_payload.get("success")
                    else "below_minimum_publishable_records"
                )
                failed_sources += 1
                source_reports.append(source_item)
                continue

            merge_input = deepcopy(run_payload)
            merge_input["status"] = "success"
            merge_input["success"] = True
            merge_input["records"] = valid
            candidate, merge_report, review = build_source_merge_candidate(
                current,
                merge_input,
                registry_payload,
                source_id=source.id,
            )
            write_json(audit_dir / f"{source.id}-merge-report.json", merge_report)
            write_json(audit_dir / f"{source.id}-review.json", review)
            current = candidate
            source_item.update({
                "status": "merged",
                "candidateEventCount": len(current.get("events") or []),
                "decisionCounts": merge_report.get("decisionCounts") or {},
                "reviewQueueCount": len(review),
            })
            successful_sources += 1
        except Exception as exc:
            source_item.update({
                "status": "preserved_previous_base",
                "reason": "isolated_exception",
                "errors": [f"{type(exc).__name__}: {exc}"],
            })
            failed_sources += 1
        source_reports.append(source_item)

    if not source_reports:
        skipped_sources = 1

    report = {
        "mode": "official-source-batch",
        "published": False,
        "failureIsolation": True,
        "base": args.base,
        "output": args.output,
        "sourceCount": len(source_reports),
        "successfulSourceCount": successful_sources,
        "failedSourceCount": failed_sources,
        "skippedSourceCount": skipped_sources,
        "finalEventCount": len(current.get("events") or []),
        "sources": source_reports,
    }
    batch_diff = build_official_source_batch_diff(
        base_payload,
        current,
        report,
    )
    write_json(args.output, current)
    write_json(args.report, report)
    if args.diff_output:
        write_json(args.diff_output, batch_diff)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
