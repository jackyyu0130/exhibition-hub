from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping

from .dedupe import MatchDecision, find_best_match
from .policy import merge_events
from .source_adapter import collector_record_to_event


def load_source_priority(
    registry: Mapping[str, Any],
    source_id: str,
) -> tuple[int, list[str]]:
    for item in registry.get("sources") or []:
        if (
            isinstance(item, dict)
            and str(item.get("id") or "") == source_id
        ):
            return (
                int(item.get("priority") or 0),
                list(item.get("venueIds") or []),
            )
    raise ValueError(
        f"Source not found in registry: {source_id}"
    )


def _rebuild_stats(payload: dict[str, Any]) -> None:
    events = payload.get("events") or []
    image_count = sum(bool(item.get("image")) for item in events)
    multi_image_count = sum(
        len(item.get("images") or []) > 1
        for item in events
    )
    coordinate_count = sum(
        item.get("latitude") is not None
        and item.get("longitude") is not None
        for item in events
    )
    category_counts = Counter()
    for event in events:
        for category in event.get("categories") or []:
            category_counts[str(category)] += 1

    stats = dict(payload.get("stats") or {})
    stats.update(
        {
            "eventCount": len(events),
            "imageCount": image_count,
            "multiImageCount": multi_image_count,
            "coordinateCount": coordinate_count,
            "imageCoverage": round(
                image_count / len(events),
                4,
            ) if events else 0.0,
            "coordinateCoverage": round(
                coordinate_count / len(events),
                4,
            ) if events else 0.0,
            "categoryCounts": dict(category_counts),
        }
    )
    payload["stats"] = stats


def build_source_merge_candidate(
    base_payload: Mapping[str, Any],
    source_run: Mapping[str, Any],
    source_registry: Mapping[str, Any],
    *,
    source_id: str,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    list[dict[str, Any]],
]:
    if not source_run.get("success"):
        raise ValueError(
            "Source run must be successful before merge"
        )
    if str(source_run.get("sourceId") or "") != source_id:
        raise ValueError(
            "Source run sourceId does not match requested source"
        )

    source_priority, source_venue_ids = load_source_priority(
        source_registry,
        source_id,
    )
    candidate = deepcopy(dict(base_payload))
    events = [
        deepcopy(item)
        for item in candidate.get("events") or []
        if isinstance(item, dict)
    ]
    event_index = {
        str(item.get("id") or ""): index
        for index, item in enumerate(events)
    }

    decisions: list[dict[str, Any]] = []
    review_queue: list[dict[str, Any]] = []
    decision_counts: Counter[str] = Counter()
    fields_added: Counter[str] = Counter()

    for record in source_run.get("records") or []:
        if not isinstance(record, dict):
            continue
        source_event = collector_record_to_event(
            record,
            source_priority=source_priority,
            source_venue_ids=source_venue_ids,
        )
        best, alternatives = find_best_match(
            source_event,
            events,
        )

        decision = (
            best.decision
            if best is not None
            else MatchDecision.NEW
        )
        decision_counts[decision.value] += 1

        decision_item = {
            "sourceId": source_id,
            "sourceEventId": source_event["sourceEventId"],
            "title": source_event["title"],
            "startDate": source_event["startDate"],
            "endDate": source_event["endDate"],
            "officialUrl": source_event["officialUrl"],
            "detailFetched": bool(
                (record.get("raw") or {}).get(
                    "detailFetched"
                )
            ),
            "decision": decision.value,
            "bestMatch": (
                best.to_dict()
                if best is not None
                else None
            ),
            "alternatives": [
                item.to_dict()
                for item in alternatives
            ],
        }

        if decision == MatchDecision.AUTO_MERGE and best:
            index = event_index[best.existing_id]
            merged, changed = merge_events(
                events[index],
                source_event,
            )
            events[index] = merged
            for field_name in changed:
                fields_added[field_name] += 1
            decision_item["mergedIntoId"] = best.existing_id
            decision_item["changedFields"] = changed
        elif decision == MatchDecision.REVIEW:
            review_queue.append(
                {
                    **decision_item,
                    "sourceEvent": source_event,
                }
            )
        else:
            event_index[source_event["id"]] = len(events)
            events.append(source_event)
            decision_item["newEventId"] = source_event["id"]

        decisions.append(decision_item)

    candidate["events"] = events
    candidate["updatedAt"] = datetime.now(
        timezone.utc
    ).isoformat()
    candidate["sourceMergeBuild"] = {
        "mode": "source-merge-candidate",
        "published": False,
        "sourceId": source_id,
        "sourceRunStartedAt": source_run.get("startedAt"),
        "baseEventCount": len(
            base_payload.get("events") or []
        ),
        "candidateEventCount": len(events),
        "decisionCounts": dict(decision_counts),
    }
    _rebuild_stats(candidate)

    report = {
        "mode": "source-merge-dry-run",
        "published": False,
        "sourceId": source_id,
        "sourcePriority": source_priority,
        "baseEventCount": len(
            base_payload.get("events") or []
        ),
        "sourceRecordCount": len(
            source_run.get("records") or []
        ),
        "detailFetchedCount": sum(
            bool((item.get("raw") or {}).get("detailFetched"))
            for item in source_run.get("records") or []
            if isinstance(item, dict)
        ),
        "candidateEventCount": len(events),
        "decisionCounts": dict(decision_counts),
        "fieldChangeCounts": dict(fields_added),
        "reviewQueueCount": len(review_queue),
        "decisions": decisions,
        "qualityGates": {
            "sourceRunSuccess": bool(source_run.get("success")),
            "baseIdsUnique": (
                len(event_index) == len(events)
            ),
            "published": False,
        },
    }
    return candidate, report, review_queue


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(
        Path(path).read_text(encoding="utf-8")
    )
