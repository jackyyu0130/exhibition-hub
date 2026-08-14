#!/usr/bin/env python3
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo


TAIPEI_TIMEZONE = ZoneInfo("Asia/Taipei")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate and finalize an official-source production preview "
            "without overwriting the current published file in place."
        )
    )
    parser.add_argument("--current", required=True)
    parser.add_argument("--preview", required=True)
    parser.add_argument("--diff", required=True)
    parser.add_argument("--source-run", required=True)
    parser.add_argument("--quality-report", required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report-output", required=True)
    parser.add_argument("--minimum-events", type=int, default=500)
    parser.add_argument("--max-drop-ratio", type=float, default=0.15)
    parser.add_argument(
        "--max-drop-count",
        type=int,
        default=25,
        help=(
            "Maximum active, future, or date-unknown events that may be "
            "removed. Expired events do not consume this budget."
        ),
    )
    parser.add_argument(
        "--as-of-date",
        help=(
            "Date used to classify expired events (YYYY-MM-DD). "
            "Defaults to today's date in Asia/Taipei."
        ),
    )
    return parser.parse_args()


def load_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def json_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def event_ids(payload: Mapping[str, Any]) -> list[str]:
    return [
        str(event.get("id") or "")
        for event in payload.get("events") or []
        if isinstance(event, dict)
    ]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def parse_event_date(value: Any) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def removed_event_ids_by_lifecycle(
    current_events: list[dict[str, Any]],
    preview_ids: set[str],
    *,
    as_of_date: date,
) -> tuple[list[str], list[str]]:
    expired_ids: set[str] = set()
    active_or_unknown_ids: set[str] = set()

    for event in current_events:
        event_id = str(event.get("id") or "").strip()
        if not event_id or event_id in preview_ids:
            continue

        end_date = parse_event_date(event.get("endDate"))
        if end_date is not None and end_date < as_of_date:
            expired_ids.add(event_id)
        else:
            # Missing or invalid dates are deliberately treated as active so
            # an ambiguous record can never bypass the production gate.
            active_or_unknown_ids.add(event_id)

    return sorted(expired_ids), sorted(active_or_unknown_ids)


def finalize_publish(
    *,
    current: Mapping[str, Any],
    preview: Mapping[str, Any],
    diff: Mapping[str, Any],
    source_run: Mapping[str, Any],
    quality_report: Mapping[str, Any],
    source_id: str,
    minimum_events: int,
    max_drop_ratio: float,
    max_drop_count: int,
    as_of_date: date | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    current_events = [
        event for event in current.get("events") or []
        if isinstance(event, dict)
    ]
    preview_events = [
        event for event in preview.get("events") or []
        if isinstance(event, dict)
    ]
    current_ids = event_ids(current)
    preview_ids = event_ids(preview)

    require(bool(source_run.get("success")), "Source run failed.")
    require(
        str(source_run.get("sourceId") or "") == source_id,
        "Source ID does not match.",
    )
    require(
        quality_report.get("passed") is True
        and not quality_report.get("failedGateIds"),
        "Source quality report did not pass.",
    )
    require(
        diff.get("published") is False,
        "Input diff must still be a preview.",
    )
    require(
        (preview.get("officialSourceBuild") or {}).get("published") is False,
        "Input preview must still be non-published.",
    )
    require(
        len(preview_events) >= max(1, minimum_events),
        "Preview event count is below the production minimum.",
    )
    require(
        "" not in preview_ids and len(preview_ids) == len(set(preview_ids)),
        "Preview event IDs must be non-empty and unique.",
    )
    require(
        not any(
            event.get("editorialStatus") == "exclude_review"
            for event in preview_events
        ),
        "Preview still contains exclude_review events.",
    )
    require(
        int(diff.get("previewEventCount") or -1) == len(preview_events),
        "Preview count does not match its diff report.",
    )
    require(
        int(diff.get("removedBaseEventCount") or 0) == 0,
        "Source merge removed events from the fresh base.",
    )
    gates = diff.get("qualityGates") or {}
    require(
        gates.get("published") is False,
        "Preview quality gate must confirm unpublished state.",
    )
    require(
        all(
            bool(value)
            for key, value in gates.items()
            if key != "published"
        ),
        "One or more preview quality gates failed.",
    )

    current_count = len(current_events)
    preview_count = len(preview_events)
    preview_id_set = set(preview_ids)
    removed_ids = sorted(set(current_ids) - preview_id_set)
    added_ids = sorted(preview_id_set - set(current_ids))
    effective_as_of_date = as_of_date or datetime.now(TAIPEI_TIMEZONE).date()
    expired_removed_ids, active_removed_ids = removed_event_ids_by_lifecycle(
        current_events,
        preview_id_set,
        as_of_date=effective_as_of_date,
    )
    drop_count = max(0, current_count - preview_count)
    drop_ratio = (
        round(drop_count / current_count, 6)
        if current_count else 0.0
    )
    active_removed_ratio = (
        round(len(active_removed_ids) / current_count, 6)
        if current_count else 0.0
    )

    require(
        len(active_removed_ids) <= max(0, max_drop_count),
        (
            "Active, future, or date-unknown production removals "
            f"{len(active_removed_ids)} exceed {max_drop_count}."
        ),
    )
    require(
        drop_ratio <= max(0.0, max_drop_ratio),
        f"Production count drop ratio {drop_ratio} exceeds {max_drop_ratio}.",
    )

    metrics = source_run.get("metrics") or {}
    source_records = [
        item for item in source_run.get("records") or []
        if isinstance(item, dict)
    ]
    require(bool(source_records), "Source run returned zero records.")
    require(
        int(metrics.get("detailRequestedCount") or 0) == len(source_records),
        "Not every source record requested a detail page.",
    )
    require(
        int(metrics.get("detailSuccessCount") or 0) == len(source_records),
        "Not every source detail page succeeded.",
    )
    require(
        int(metrics.get("detailFailureCount") or 0) == 0,
        "Source detail failures are not allowed for production.",
    )

    published_at = datetime.now(timezone.utc).isoformat()
    final = deepcopy(dict(preview))
    build = deepcopy(final.get("officialSourceBuild") or {})
    build.update({
        "mode": "production-publish",
        "published": True,
        "publishedAt": published_at,
        "sourceId": source_id,
        "previousPublishedEventCount": current_count,
        "publishedEventCount": preview_count,
        "productionAddedEventCount": len(added_ids),
        "productionRemovedEventCount": len(removed_ids),
        "productionExpiredRemovedEventCount": len(expired_removed_ids),
        "productionActiveRemovedEventCount": len(active_removed_ids),
    })
    final["officialSourceBuild"] = build
    final["updatedAt"] = published_at

    report = {
        "mode": "production-publish-report",
        "published": True,
        "publishedAt": published_at,
        "sourceId": source_id,
        "currentEventCount": current_count,
        "publishedEventCount": preview_count,
        "addedEventCount": len(added_ids),
        "removedEventCount": len(removed_ids),
        "dropCount": drop_count,
        "dropRatio": drop_ratio,
        "asOfDate": effective_as_of_date.isoformat(),
        "expiredRemovedEventCount": len(expired_removed_ids),
        "activeRemovedEventCount": len(active_removed_ids),
        "activeRemovedRatio": active_removed_ratio,
        "safetyLimits": {
            "minimumEvents": minimum_events,
            "maxActiveRemovedCount": max_drop_count,
            "maxTotalDropRatio": max_drop_ratio,
            "maxDropCount": max_drop_count,
            "maxDropRatio": max_drop_ratio,
            "countGateScope": "active_future_or_date_unknown_removed_events",
            "ratioGateScope": "net_total_event_count",
        },
        "sourceRecordCount": len(source_records),
        "detailSuccessCount": int(metrics.get("detailSuccessCount") or 0),
        "qualityPassed": True,
        "previewQualityGates": gates,
        "hashes": {
            "current": json_hash(current),
            "preview": json_hash(preview),
            "published": json_hash(final),
        },
        "addedIds": added_ids,
        "removedIds": removed_ids,
        "expiredRemovedIds": expired_removed_ids,
        "activeRemovedIds": active_removed_ids,
    }
    return final, report


def main() -> int:
    args = parse_args()
    as_of_date = None
    if args.as_of_date:
        as_of_date = parse_event_date(args.as_of_date)
        if as_of_date is None:
            raise ValueError("--as-of-date must use YYYY-MM-DD format.")
    final, report = finalize_publish(
        current=load_json(args.current),
        preview=load_json(args.preview),
        diff=load_json(args.diff),
        source_run=load_json(args.source_run),
        quality_report=load_json(args.quality_report),
        source_id=args.source_id,
        minimum_events=max(1, args.minimum_events),
        max_drop_ratio=max(0.0, args.max_drop_ratio),
        max_drop_count=max(0, args.max_drop_count),
        as_of_date=as_of_date,
    )
    write_json(args.output, final)
    write_json(args.report_output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
