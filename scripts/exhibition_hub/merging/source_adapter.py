from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from typing import Any, Mapping

from exhibition_hub.classifiers.content_types import (
    classify_event,
)
from ..image_quality import clean_image_urls

from .normalization import unique_strings, unique_urls


_HINT_TO_CATEGORY = {
    "演唱會": "演唱會",
    "快閃店": "快閃店",
    "動漫": "動漫",
    "美術": "美術",
    "攝影": "攝影",
    "設計": "設計",
    "市集": "市集",
    "音樂": "音樂",
    "自然": "自然",
    "歷史": "歷史",
    "表演": "表演",
    "舞蹈": "舞蹈",
    "電影": "電影",
    "親子": "親子",
    "競賽": "競賽",
    "科技": "科技",
    "其他": "其他",
}

_CATEGORY_TO_CONTENT_TYPE = {
    "演唱會": "concert",
    "快閃店": "popup",
    "動漫": "exhibition",
    "美術": "art_exhibition",
    "攝影": "art_exhibition",
    "設計": "exhibition",
    "市集": "market",
    "音樂": "performance",
    "自然": "exhibition",
    "歷史": "exhibition",
    "表演": "performance",
    "舞蹈": "performance",
    "電影": "film_screening",
    "親子": "exhibition",
    "競賽": "exhibition",
    "科技": "exhibition",
    "其他": "exhibition",
}


def _stable_id(source_id: str, source_event_id: str) -> str:
    return hashlib.sha256(
        f"{source_id}:{source_event_id}".encode("utf-8")
    ).hexdigest()[:24]


def collector_record_to_event(
    record: Mapping[str, Any],
    *,
    source_priority: int,
    source_venue_ids: list[str] | None = None,
) -> dict[str, Any]:
    raw = dict(record.get("raw") or {})
    source_id = str(
        record.get("source_id")
        or record.get("sourceId")
        or ""
    )
    source_event_id = str(
        record.get("source_event_id")
        or record.get("sourceEventId")
        or raw.get("sourceEventId")
        or ""
    )
    title = str(
        record.get("title")
        or raw.get("title")
        or ""
    ).strip()
    official_url = str(
        raw.get("officialUrl")
        or record.get("detail_url")
        or record.get("detailUrl")
        or raw.get("detailUrl")
        or ""
    )
    images, _rejected_images = clean_image_urls(unique_urls(
        [
            raw.get("imageUrl"),
            *(raw.get("imageUrls") or []),
        ]
    ))
    category = _HINT_TO_CATEGORY.get(
        str(raw.get("contentTypeHint") or ""),
        "其他",
    )
    main_venue = str(
        raw.get("venueName")
        or raw.get("locationName")
        or ""
    ).strip()
    sub_venues = unique_strings(
        raw.get("venueNames") or []
    )
    organizers = unique_strings(
        [
            raw.get("organizer"),
            *(raw.get("organizers") or []),
        ]
    )
    now = datetime.now(timezone.utc).isoformat()
    source_entity_kind = "generic"
    if source_event_id.startswith("performance_"):
        source_entity_kind = (
            "performance_item"
            if "《" in title and "》" in title
            else "performance_series"
        )
    elif raw.get("contentTypeHint") == "表演":
        source_entity_kind = "performance_item"

    event = {
        "id": _stable_id(source_id, source_event_id),
        "title": title,
        "description": str(raw.get("description") or ""),
        "sourceUrl": official_url,
        "officialUrl": official_url,
        "sourceUrls": unique_urls(
            [
                official_url,
                *(raw.get("externalUrls") or []),
            ]
        ),
        "image": images[0] if images else "",
        "images": images,
        "categories": [category],
        "category": category,
        "startDate": str(raw.get("startDate") or ""),
        "endDate": str(raw.get("endDate") or ""),
        "startTime": str(raw.get("startTime") or ""),
        "endTime": str(raw.get("endTime") or ""),
        "timeText": str(raw.get("timeText") or ""),
        "locationName": main_venue,
        "location": main_venue,
        "venueGroup": main_venue,
        "venueDetail": "／".join(sub_venues),
        "subVenueNames": sub_venues,
        "address": str(raw.get("address") or ""),
        "region": str(raw.get("regionCanonical") or ""),
        "regionCanonical": str(
            raw.get("regionCanonical") or ""
        ),
        "latitude": None,
        "longitude": None,
        "coordinateSource": "",
        "price": str(raw.get("priceText") or ""),
        "admission": str(
            raw.get("admission") or "unknown"
        ),
        "organizer": (
            organizers[0] if organizers else ""
        ),
        "organizers": organizers,
        "unit": organizers[0] if organizers else "",
        "sessions": [],
        "hitRate": 0,
        "source": source_id,
        "collectorSourceId": source_id,
        "sourceEventId": source_event_id,
        "sourceEntityKind": source_entity_kind,
        "sourceCategory": str(
            raw.get("sourceCategory") or ""
        ),
        "sourcePriority": source_priority,
        "sourceRecords": [
            {
                "sourceId": source_id,
                "sourceEventId": source_event_id,
                "officialUrl": official_url,
                "priority": source_priority,
                "detailFetched": bool(
                    raw.get("detailFetched")
                ),
            }
        ],
        "firstSeenAt": now,
        "lastSeenAt": now,
        "sourceUrlVerified": bool(official_url),
        "sourceUrlMatchScore": (
            1.0 if official_url else 0.0
        ),
        "sourceUrlRejected": "",
        "venueIds": list(source_venue_ids or []),
        "venueNames": [main_venue] if main_venue else [],
        "venueId": (
            source_venue_ids[0]
            if source_venue_ids
            else ""
        ),
        "venueName": main_venue,
        "venueCoverageStatus": (
            "complete"
            if main_venue and source_venue_ids
            else "unmatched"
        ),
        "editorialStatus": str(
            raw.get("editorialStatus")
            or "candidate"
        ),
        "editorialFlags": [],
    }
    classified = classify_event(event)
    classified["category"] = category
    classified["categories"] = [category]
    classified["contentType"] = (
        _CATEGORY_TO_CONTENT_TYPE.get(
            category,
            classified.get("contentType", "exhibition"),
        )
    )
    classified["contentTypes"] = unique_strings(
        [
            classified["contentType"],
            *(
                classified.get("contentTypes")
                or []
            ),
        ]
    )
    if (
        str(raw.get("editorialStatus") or "")
        == "exclude_review"
    ):
        classified["editorialStatus"] = "exclude_review"
    return classified
