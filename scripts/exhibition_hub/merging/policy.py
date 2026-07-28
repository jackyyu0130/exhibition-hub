from __future__ import annotations

from copy import deepcopy
from typing import Any

from .normalization import unique_strings


_SOURCE_PREFERRED_FIELDS = (
    "officialUrl",
    "sourceUrl",
    "description",
    "startDate",
    "endDate",
    "startTime",
    "endTime",
    "timeText",
    "price",
    "admission",
    "organizer",
    "organizers",
    "unit",
    "sourceCategory",
)


def merge_events(
    existing: dict[str, Any],
    source_event: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    result = deepcopy(existing)
    changed_fields: list[str] = []
    source_priority = int(
        source_event.get("sourcePriority") or 0
    )
    existing_priority = max(
        [
            int(item.get("priority") or 0)
            for item in result.get("sourceRecords") or []
            if isinstance(item, dict)
        ]
        or [0]
    )

    for field_name in _SOURCE_PREFERRED_FIELDS:
        source_value = source_event.get(field_name)
        existing_value = result.get(field_name)
        should_use = bool(source_value) and (
            not existing_value
            or source_priority >= existing_priority
        )
        if should_use and existing_value != source_value:
            result[field_name] = deepcopy(source_value)
            changed_fields.append(field_name)

    source_images = source_event.get("images") or []
    existing_images = result.get("images") or []
    images = unique_strings(
        [*source_images, *existing_images]
    )[:10]
    if images != existing_images:
        result["images"] = images
        result["image"] = (
            images[0]
            if images
            else result.get("image", "")
        )
        changed_fields.append("images")

    main_venue = str(
        source_event.get("venueName")
        or source_event.get("venueGroup")
        or ""
    )
    if main_venue:
        for field_name in (
            "locationName",
            "location",
            "venueGroup",
            "venueName",
        ):
            if result.get(field_name) != main_venue:
                result[field_name] = main_venue
                changed_fields.append(field_name)

    for field_name in (
        "venueIds",
        "venueNames",
        "subVenueNames",
        "sourceUrls",
        "organizers",
    ):
        combined = unique_strings(
            [
                *(source_event.get(field_name) or []),
                *(result.get(field_name) or []),
            ]
        )
        if combined != (result.get(field_name) or []):
            result[field_name] = combined
            changed_fields.append(field_name)

    source_detail = str(
        source_event.get("venueDetail") or ""
    )
    if source_detail and result.get("venueDetail") != source_detail:
        result["venueDetail"] = source_detail
        changed_fields.append("venueDetail")

    records = [
        item
        for item in result.get("sourceRecords") or []
        if isinstance(item, dict)
    ]
    known = {
        (
            str(item.get("sourceId") or ""),
            str(item.get("sourceEventId") or ""),
        )
        for item in records
    }
    for item in source_event.get("sourceRecords") or []:
        key = (
            str(item.get("sourceId") or ""),
            str(item.get("sourceEventId") or ""),
        )
        if key not in known:
            records.append(deepcopy(item))
            known.add(key)
            changed_fields.append("sourceRecords")
    result["sourceRecords"] = records
    result["sourcePriority"] = max(
        source_priority,
        int(result.get("sourcePriority") or 0),
    )
    result["collectorSourceId"] = str(
        source_event.get("collectorSourceId") or ""
    )
    result["sourceEventId"] = str(
        source_event.get("sourceEventId") or ""
    )
    result["lastSeenAt"] = source_event.get(
        "lastSeenAt",
        result.get("lastSeenAt"),
    )

    if source_event.get("admission") in {"free", "paid"}:
        result["admission"] = source_event["admission"]

    return result, sorted(set(changed_fields))
