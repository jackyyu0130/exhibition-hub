#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping


INCLUDED_EDITORIAL_STATUSES = {
    "candidate",
    "needs_review",
}
EXCLUDED_EDITORIAL_STATUSES = {
    "exclude_review",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a non-published production preview from "
            "a validated official-source merge candidate."
        )
    )
    parser.add_argument("--base", required=True)
    parser.add_argument("--source-run", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--merge-report", required=True)
    parser.add_argument("--review", required=True)
    parser.add_argument("--quality-report", required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--preview-output", required=True)
    parser.add_argument("--diff-output", required=True)
    parser.add_argument("--excluded-output", required=True)
    return parser.parse_args()


def load_json(path: str) -> Any:
    return json.loads(
        Path(path).read_text(encoding="utf-8")
    )


def write_json(path: str, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def event_categories(
    event: Mapping[str, Any],
) -> list[str]:
    values = event.get("categories")
    if isinstance(values, list):
        result = [
            str(value).strip()
            for value in values
            if str(value).strip()
        ]
    else:
        result = []

    fallback = str(
        event.get("category") or ""
    ).strip()
    if not result and fallback:
        result = [fallback]
    return list(dict.fromkeys(result))


def recompute_stats(
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    total = len(events)
    image_count = sum(
        bool(str(event.get("image") or "").strip())
        for event in events
    )
    multi_image_count = sum(
        isinstance(event.get("images"), list)
        and len(event.get("images") or []) > 1
        for event in events
    )
    coordinate_count = sum(
        event.get("latitude") is not None
        and event.get("longitude") is not None
        for event in events
    )
    category_counts = Counter(
        category
        for event in events
        for category in event_categories(event)
    )
    return {
        "eventCount": total,
        "imageCount": image_count,
        "multiImageCount": multi_image_count,
        "coordinateCount": coordinate_count,
        "imageCoverage": (
            round(image_count / total, 4)
            if total
            else 0.0
        ),
        "coordinateCoverage": (
            round(coordinate_count / total, 4)
            if total
            else 0.0
        ),
        "categoryCounts": dict(category_counts),
    }


def source_record_ids(
    event: Mapping[str, Any],
    source_id: str,
) -> list[str]:
    values: list[str] = []
    for record in event.get("sourceRecords") or []:
        if not isinstance(record, dict):
            continue
        if str(record.get("sourceId") or "") != source_id:
            continue
        source_event_id = str(
            record.get("sourceEventId") or ""
        )
        if source_event_id:
            values.append(source_event_id)
    return values


def compact_event(
    event: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "id": event.get("id"),
        "title": event.get("title"),
        "startDate": event.get("startDate"),
        "endDate": event.get("endDate"),
        "regionCanonical": event.get(
            "regionCanonical"
        ),
        "venueName": event.get("venueName"),
        "admission": event.get("admission"),
        "editorialStatus": event.get(
            "editorialStatus"
        ),
        "officialUrl": event.get("officialUrl"),
    }


def changed_fields(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
) -> list[str]:
    ignored = {
        "lastSeenAt",
        "updatedAt",
    }
    keys = set(before) | set(after)
    return sorted(
        key
        for key in keys
        if key not in ignored
        and before.get(key) != after.get(key)
    )


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise ValueError(message)


def build_preview(
    *,
    base: Mapping[str, Any],
    source_run: Mapping[str, Any],
    candidate: Mapping[str, Any],
    merge_report: Mapping[str, Any],
    review: list[dict[str, Any]],
    quality_report: Mapping[str, Any],
    source_id: str,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    base_events = [
        deepcopy(item)
        for item in base.get("events") or []
        if isinstance(item, dict)
    ]
    candidate_events = [
        deepcopy(item)
        for item in candidate.get("events") or []
        if isinstance(item, dict)
    ]

    require(
        bool(source_run.get("success")),
        "Source run did not succeed.",
    )
    require(
        str(source_run.get("sourceId") or "")
        == source_id,
        "Source run ID does not match.",
    )
    require(
        quality_report.get("passed") is True,
        "Candidate quality report did not pass.",
    )
    require(
        not quality_report.get("failedGateIds"),
        "Candidate quality report has failed gates.",
    )
    require(
        merge_report.get("published") is False,
        "Merge report must remain non-published.",
    )
    require(
        (
            candidate.get("sourceMergeBuild") or {}
        ).get("published")
        is False,
        "Candidate must remain non-published.",
    )
    require(
        len(review) == 0,
        "Review queue must be empty.",
    )

    metrics = source_run.get("metrics") or {}
    record_count = len(
        [
            item
            for item in source_run.get("records") or []
            if isinstance(item, dict)
        ]
    )
    require(
        int(
            metrics.get("detailRequestedCount")
            or 0
        )
        == record_count,
        "Not every source record requested details.",
    )
    require(
        int(
            metrics.get("detailSuccessCount")
            or 0
        )
        == record_count,
        "Not every source detail page succeeded.",
    )
    require(
        int(
            metrics.get("detailFailureCount")
            or 0
        )
        == 0,
        "Source detail failures are not allowed.",
    )

    statuses = {
        str(
            event.get("editorialStatus")
            or ""
        )
        for event in candidate_events
    }
    unknown_statuses = sorted(
        statuses
        - INCLUDED_EDITORIAL_STATUSES
        - EXCLUDED_EDITORIAL_STATUSES
    )
    require(
        not unknown_statuses,
        "Unknown editorial statuses: "
        + ", ".join(unknown_statuses),
    )

    publish_events = [
        event
        for event in candidate_events
        if event.get("editorialStatus")
        in INCLUDED_EDITORIAL_STATUSES
    ]
    excluded_events = [
        event
        for event in candidate_events
        if event.get("editorialStatus")
        in EXCLUDED_EDITORIAL_STATUSES
        and source_record_ids(
            event,
            source_id,
        )
    ]

    base_ids = [
        str(event.get("id") or "")
        for event in base_events
    ]
    candidate_ids = [
        str(event.get("id") or "")
        for event in candidate_events
    ]
    publish_ids = [
        str(event.get("id") or "")
        for event in publish_events
    ]

    require(
        "" not in base_ids
        and len(base_ids) == len(set(base_ids)),
        "Base event IDs must be unique and non-empty.",
    )
    require(
        "" not in candidate_ids
        and len(candidate_ids)
        == len(set(candidate_ids)),
        "Candidate event IDs must be unique and non-empty.",
    )
    require(
        "" not in publish_ids
        and len(publish_ids) == len(set(publish_ids)),
        "Preview event IDs must be unique and non-empty.",
    )

    base_id_set = set(base_ids)
    candidate_id_set = set(candidate_ids)
    publish_id_set = set(publish_ids)

    removed_from_candidate = sorted(
        base_id_set - candidate_id_set
    )
    removed_from_preview = sorted(
        base_id_set - publish_id_set
    )
    require(
        not removed_from_candidate,
        "Candidate removed existing base events.",
    )
    require(
        not removed_from_preview,
        "Preview removed existing base events.",
    )

    reference_counts: Counter[str] = Counter()
    for event in candidate_events:
        for source_event_id in source_record_ids(
            event,
            source_id,
        ):
            reference_counts[source_event_id] += 1

    source_event_ids = [
        str(
            item.get("source_event_id")
            or item.get("sourceEventId")
            or (
                item.get("raw")
                or {}
            ).get("sourceEventId")
            or ""
        )
        for item in source_run.get("records") or []
        if isinstance(item, dict)
    ]
    missing_references = sorted(
        source_event_id
        for source_event_id in source_event_ids
        if reference_counts[source_event_id] == 0
    )
    duplicate_references = sorted(
        source_event_id
        for source_event_id in source_event_ids
        if reference_counts[source_event_id] > 1
    )
    require(
        not missing_references,
        "Some source records are absent from candidate.",
    )
    require(
        not duplicate_references,
        "Some source records appear in multiple events.",
    )

    base_by_id = {
        str(event["id"]): event
        for event in base_events
    }
    preview_by_id = {
        str(event["id"]): event
        for event in publish_events
    }
    added_ids = sorted(
        publish_id_set - base_id_set
    )
    modified_ids = sorted(
        event_id
        for event_id in base_id_set
        if base_by_id[event_id]
        != preview_by_id[event_id]
    )

    modified_events = []
    for event_id in modified_ids:
        after = preview_by_id[event_id]
        modified_events.append({
            "id": event_id,
            "title": after.get("title"),
            "changedFields": changed_fields(
                base_by_id[event_id],
                after,
            ),
        })

    preview = deepcopy(dict(base))
    preview["events"] = publish_events
    preview["updatedAt"] = (
        source_run.get("startedAt")
        or datetime.now(
            timezone.utc
        ).isoformat()
    )
    preview["stats"] = recompute_stats(
        publish_events
    )
    preview["officialSourceBuild"] = {
        "mode": "production-publish-preview",
        "published": False,
        "sourceId": source_id,
        "baseUpdatedAt": base.get("updatedAt"),
        "sourceRunStartedAt": source_run.get(
            "startedAt"
        ),
        "baseEventCount": len(base_events),
        "candidateEventCount": len(
            candidate_events
        ),
        "previewEventCount": len(
            publish_events
        ),
        "addedEventCount": len(added_ids),
        "modifiedEventCount": len(
            modified_ids
        ),
        "excludedSourceEventCount": len(
            excluded_events
        ),
        "sourceRecordCount": len(
            source_event_ids
        ),
    }

    expected_preview_count = (
        len(base_events)
        + len(added_ids)
    )
    require(
        len(publish_events)
        == expected_preview_count,
        "Preview event count formula failed.",
    )

    diff = {
        "mode": "production-publish-preview-diff",
        "published": False,
        "sourceId": source_id,
        "baseUpdatedAt": base.get("updatedAt"),
        "sourceRunStartedAt": source_run.get(
            "startedAt"
        ),
        "baseEventCount": len(base_events),
        "candidateEventCount": len(
            candidate_events
        ),
        "previewEventCount": len(
            publish_events
        ),
        "addedEventCount": len(added_ids),
        "modifiedEventCount": len(
            modified_ids
        ),
        "unchangedBaseEventCount": (
            len(base_events)
            - len(modified_ids)
        ),
        "removedBaseEventCount": 0,
        "excludedSourceEventCount": len(
            excluded_events
        ),
        "sourceRecordCount": len(
            source_event_ids
        ),
        "qualityGates": {
            "sourceRunSuccess": True,
            "fullDetailCoverage": True,
            "candidateQualityPassed": True,
            "reviewQueueEmpty": True,
            "baseEventsPreserved": True,
            "candidateIdsUnique": True,
            "previewIdsUnique": True,
            "sourceReferencesComplete": True,
            "sourceReferencesUnique": True,
            "published": False,
        },
        "addedEvents": [
            compact_event(
                preview_by_id[event_id]
            )
            for event_id in added_ids
        ],
        "modifiedEvents": modified_events,
        "excludedSourceEvents": [
            compact_event(event)
            for event in excluded_events
        ],
    }

    excluded = {
        "mode": "production-publish-preview-excluded",
        "published": False,
        "sourceId": source_id,
        "eventCount": len(excluded_events),
        "events": excluded_events,
    }

    return preview, diff, excluded


def main() -> int:
    args = parse_args()

    review = load_json(args.review)
    if not isinstance(review, list):
        raise ValueError(
            "Review queue JSON must be a list."
        )

    preview, diff, excluded = build_preview(
        base=load_json(args.base),
        source_run=load_json(args.source_run),
        candidate=load_json(args.candidate),
        merge_report=load_json(
            args.merge_report
        ),
        review=review,
        quality_report=load_json(
            args.quality_report
        ),
        source_id=args.source_id,
    )

    write_json(
        args.preview_output,
        preview,
    )
    write_json(
        args.diff_output,
        diff,
    )
    write_json(
        args.excluded_output,
        excluded,
    )

    print(
        json.dumps(
            {
                key: diff[key]
                for key in (
                    "mode",
                    "published",
                    "sourceId",
                    "baseEventCount",
                    "candidateEventCount",
                    "previewEventCount",
                    "addedEventCount",
                    "modifiedEventCount",
                    "removedBaseEventCount",
                    "excludedSourceEventCount",
                    "sourceRecordCount",
                )
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
