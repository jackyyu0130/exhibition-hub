"""Apply venue registry matches and editorial classifications."""

from __future__ import annotations

from collections import defaultdict
import re
from typing import Any, Mapping

from exhibition_hub.classifiers import classify_event
from .loader import normalize_venue_key


REGION_ALIASES = {
    "台北市": "臺北市",
    "台中市": "臺中市",
    "台南市": "臺南市",
    "台東縣": "臺東縣",
    "台灣": "臺灣",
}

LEGACY_CANONICAL_OVERRIDES = {
    (
        "客家委員會客家文化發展中心"
        "臺灣客家文化館"
    ): "taiwan-hakka-culture-museum",
}

LEGACY_PATTERNS_NOT_SAFE_TO_MERGE = {
    "故宮南院",
    "故宮北院",
    "國立故宮博物院",
    "故宮博物院",
    "桃園市兒童美術館",
}

SPECIAL_VENUE_PATTERNS = {
    "national-palace-museum-south": (
        "故宮南院",
        "故宮博物院南部院區",
        "國立故宮博物院南部院區",
    ),
    "national-palace-museum-north": (
        "故宮北院",
        "國立故宮博物院北部院區",
        "臺北故宮",
        "台北故宮",
    ),
}


def normalize_region(value: Any) -> str:
    """Normalize common 台/臺 region variants."""

    cleaned = str(value or "").strip()

    if cleaned in REGION_ALIASES:
        return REGION_ALIASES[cleaned]

    if cleaned.startswith("台"):
        return "臺" + cleaned[1:]

    return cleaned


def _unique_venues(
    venues: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []

    for venue in venues:
        venue_id = str(venue.get("id") or "")

        if not venue_id or venue_id in seen:
            continue

        seen.add(venue_id)
        result.append(venue)

    return result


def _build_alias_records(
    venue_registry: Mapping[str, Any],
    legacy_alias_registry: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    venues = [
        venue
        for venue in venue_registry.get("venues", [])
        if isinstance(venue, dict)
    ]
    venue_by_id = {
        str(venue.get("id") or ""): venue
        for venue in venues
        if venue.get("id")
    }
    aliases_to_venues: dict[
        str,
        list[dict[str, Any]],
    ] = defaultdict(list)

    for venue in venues:
        for alias in [
            venue.get("name"),
            *venue.get("aliases", []),
        ]:
            normalized = normalize_venue_key(alias)

            if normalized:
                aliases_to_venues[normalized].append(
                    venue
                )

    records: dict[
        tuple[str, str],
        dict[str, Any],
    ] = {}

    for normalized_alias, matched_venues in (
        aliases_to_venues.items()
    ):
        for venue in _unique_venues(matched_venues):
            records[
                (
                    normalized_alias,
                    str(venue.get("id")),
                )
            ] = {
                "alias": normalized_alias,
                "venue": venue,
                "source": "registry",
            }

    if not legacy_alias_registry:
        return sorted(
            records.values(),
            key=lambda item: len(item["alias"]),
            reverse=True,
        )

    for legacy_entry in legacy_alias_registry.get(
        "venues",
        [],
    ):
        if not isinstance(legacy_entry, dict):
            continue

        canonical_name = str(
            legacy_entry.get("name") or ""
        ).strip()
        canonical_key = normalize_venue_key(
            canonical_name
        )

        candidate_venues = _unique_venues(
            aliases_to_venues.get(
                canonical_key,
                [],
            )
        )

        override_id = LEGACY_CANONICAL_OVERRIDES.get(
            canonical_name
        )

        if override_id and override_id in venue_by_id:
            candidate_venues = [
                venue_by_id[override_id]
            ]

        if len(candidate_venues) != 1:
            continue

        venue = candidate_venues[0]

        for pattern in legacy_entry.get(
            "patterns",
            [],
        ):
            cleaned_pattern = str(pattern or "").strip()

            if (
                not cleaned_pattern
                or cleaned_pattern
                in LEGACY_PATTERNS_NOT_SAFE_TO_MERGE
            ):
                continue

            normalized_pattern = normalize_venue_key(
                cleaned_pattern
            )

            if not normalized_pattern:
                continue

            records[
                (
                    normalized_pattern,
                    str(venue.get("id")),
                )
            ] = {
                "alias": normalized_pattern,
                "venue": venue,
                "source": "legacy_alias",
            }

    return sorted(
        records.values(),
        key=lambda item: len(item["alias"]),
        reverse=True,
    )


def _event_venue_values(
    event: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Return unique venue strings with matching context."""

    values: dict[str, dict[str, Any]] = {}

    for field_name in (
        "locationName",
        "venueGroup",
        "location",
    ):
        value = str(event.get(field_name) or "").strip()

        if not value:
            continue

        allow_cross_region = any(
            delimiter in value
            for delimiter in (
                "|",
                "｜",
                "、",
            )
        )
        current = values.get(value)

        if current is None:
            values[value] = {
                "value": value,
                "allowCrossRegion": (
                    allow_cross_region
                ),
                "source": field_name,
            }
        elif allow_cross_region:
            current["allowCrossRegion"] = True

    sessions = event.get("sessions")

    if isinstance(sessions, list):
        for session in sessions:
            if not isinstance(session, dict):
                continue

            value = str(
                session.get("locationName") or ""
            ).strip()

            if not value:
                continue

            current = values.get(value)

            if current is None:
                values[value] = {
                    "value": value,
                    "allowCrossRegion": True,
                    "source": "session",
                }
            else:
                current["allowCrossRegion"] = True

    return list(values.values())

def _region_compatible(
    event_region: str,
    venue: Mapping[str, Any],
) -> bool:
    venue_region = normalize_region(
        venue.get("region")
    )

    if not event_region or event_region == "其他地區":
        return True

    return not venue_region or venue_region == event_region


def _candidate_match_record(
    candidate: Mapping[str, Any],
    method: str,
    confidence: float,
) -> dict[str, Any]:
    venue = candidate["venue"]

    return {
        "venue": venue,
        "venueId": venue.get("id"),
        "venueName": venue.get("name"),
        "method": method,
        "confidence": confidence,
        "matchedValue": candidate.get(
            "matchedValue",
            "",
        ),
        "matchedAlias": candidate.get(
            "alias",
            "",
        ),
    }


def _deduplicate_match_records(
    matches: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()

    for match in matches:
        venue_id = str(match.get("venueId") or "")

        if not venue_id or venue_id in seen:
            continue

        seen.add(venue_id)
        result.append(match)

    return result


def _single_match_payload(
    match: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "status": "matched",
        "venue": match["venue"],
        "venues": [match["venue"]],
        "matches": [dict(match)],
        "method": match["method"],
        "confidence": match["confidence"],
        "matchedValue": match["matchedValue"],
        "matchedAlias": match["matchedAlias"],
        "candidateVenueIds": [
            match["venueId"]
        ],
    }


def _multiple_match_payload(
    matches: list[dict[str, Any]],
    method: str,
    matched_values: list[str],
) -> dict[str, Any]:
    unique_matches = _deduplicate_match_records(
        matches
    )
    venues = [
        match["venue"]
        for match in unique_matches
    ]
    confidence = min(
        (
            float(match.get("confidence") or 0.0)
            for match in unique_matches
        ),
        default=0.0,
    )

    return {
        "status": "matched_multiple",
        "venue": venues[0] if venues else None,
        "venues": venues,
        "matches": unique_matches,
        "method": method,
        "confidence": confidence,
        "matchedValue": " | ".join(
            matched_values
        ),
        "matchedAlias": "",
        "candidateVenueIds": [
            venue.get("id")
            for venue in venues
        ],
    }


def _special_venue_match(
    event: Mapping[str, Any],
    venue_registry: Mapping[str, Any],
) -> dict[str, Any] | None:
    value_records = _event_venue_values(event)
    values = [
        record["value"]
        for record in value_records
    ]
    joined = " ".join(values)
    region = normalize_region(event.get("region"))
    venue_by_id = {
        str(venue.get("id") or ""): venue
        for venue in venue_registry.get("venues", [])
        if isinstance(venue, dict)
    }

    for venue_id, patterns in (
        SPECIAL_VENUE_PATTERNS.items()
    ):
        if any(pattern in joined for pattern in patterns):
            venue = venue_by_id.get(venue_id)

            if venue:
                matched_alias = next(
                    pattern
                    for pattern in patterns
                    if pattern in joined
                )
                return _single_match_payload(
                    {
                        "venue": venue,
                        "venueId": venue.get("id"),
                        "venueName": venue.get("name"),
                        "method": "special_pattern",
                        "confidence": 1.0,
                        "matchedValue": joined,
                        "matchedAlias": matched_alias,
                    }
                )

    if "故宮" in joined:
        if region == "嘉義縣":
            venue = venue_by_id.get(
                "national-palace-museum-south"
            )
        elif region == "臺北市":
            venue = venue_by_id.get(
                "national-palace-museum-north"
            )
        else:
            venue = None

        if venue:
            return _single_match_payload(
                {
                    "venue": venue,
                    "venueId": venue.get("id"),
                    "venueName": venue.get("name"),
                    "method": "special_region",
                    "confidence": 0.95,
                    "matchedValue": joined,
                    "matchedAlias": "故宮",
                }
            )

    return None


def resolve_event_venue(
    event: Mapping[str, Any],
    venue_registry: Mapping[str, Any],
    legacy_alias_registry: (
        Mapping[str, Any] | None
    ) = None,
) -> dict[str, Any]:
    """Resolve one or multiple venues from an event."""

    special = _special_venue_match(
        event,
        venue_registry,
    )
    value_records = _event_venue_values(event)

    if special and len(value_records) <= 1:
        return special

    alias_records = _build_alias_records(
        venue_registry,
        legacy_alias_registry,
    )
    event_region = normalize_region(
        event.get("region")
    )
    collected_matches: list[
        dict[str, Any]
    ] = []

    for value_record in value_records:
        value = value_record["value"]
        allow_cross_region = bool(
            value_record.get("allowCrossRegion")
        )
        normalized_value = normalize_venue_key(value)

        exact_candidates: list[
            dict[str, Any]
        ] = []

        for record in alias_records:
            if record["alias"] != normalized_value:
                continue

            venue = record["venue"]

            if (
                not allow_cross_region
                and not _region_compatible(
                    event_region,
                    venue,
                )
            ):
                continue

            exact_candidates.append(
                {
                    **record,
                    "matchedValue": value,
                }
            )

        if exact_candidates:
            collected_matches.extend(
                _candidate_match_record(
                    candidate,
                    (
                        "legacy_exact"
                        if candidate["source"]
                        == "legacy_alias"
                        else "registry_exact"
                    ),
                    1.0,
                )
                for candidate in exact_candidates
            )
            continue

        contained_candidates: list[
            dict[str, Any]
        ] = []

        for record in alias_records:
            alias = record["alias"]

            if len(alias) < 3:
                continue

            if alias not in normalized_value:
                continue

            venue = record["venue"]

            if (
                not allow_cross_region
                and not _region_compatible(
                    event_region,
                    venue,
                )
            ):
                continue

            contained_candidates.append(
                {
                    **record,
                    "matchedValue": value,
                    "aliasLength": len(alias),
                }
            )

        if not contained_candidates:
            continue

        longest_by_venue: dict[
            str,
            dict[str, Any],
        ] = {}

        for candidate in contained_candidates:
            venue_id = str(
                candidate["venue"].get("id") or ""
            )
            existing = longest_by_venue.get(
                venue_id
            )

            if (
                existing is None
                or candidate["aliasLength"]
                > existing["aliasLength"]
            ):
                longest_by_venue[
                    venue_id
                ] = candidate

        collected_matches.extend(
            _candidate_match_record(
                candidate,
                (
                    "legacy_contains"
                    if candidate["source"]
                    == "legacy_alias"
                    else "registry_contains"
                ),
                0.9,
            )
            for candidate in longest_by_venue.values()
        )

    unique_matches = _deduplicate_match_records(
        collected_matches
    )

    if len(unique_matches) == 1:
        return _single_match_payload(
            unique_matches[0]
        )

    if len(unique_matches) > 1:
        match_methods = {
            str(match.get("method") or "")
            for match in unique_matches
        }
        method = (
            "multi_exact"
            if all(
                value.endswith("_exact")
                for value in match_methods
            )
            else "multi_mixed"
        )

        return _multiple_match_payload(
            unique_matches,
            method,
            [
                record["value"]
                for record in value_records
            ],
        )

    if special:
        return special

    return {
        "status": "unmatched",
        "venue": None,
        "venues": [],
        "matches": [],
        "method": "none",
        "confidence": 0.0,
        "matchedValue": " | ".join(
            record["value"]
            for record in value_records
        ),
        "matchedAlias": "",
        "candidateVenueIds": [],
    }

def enrich_event_with_registry(
    event: Mapping[str, Any],
    venue_registry: Mapping[str, Any],
    legacy_alias_registry: (
        Mapping[str, Any] | None
    ) = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return an enriched event copy and its venue diagnostic."""

    enriched = classify_event(event)
    match = resolve_event_venue(
        event,
        venue_registry,
        legacy_alias_registry,
    )
    enriched["regionCanonical"] = normalize_region(
        event.get("region")
    )

    matches = [
        item
        for item in match.get("matches", [])
        if isinstance(item, dict)
    ]
    venues = [
        item.get("venue")
        for item in matches
        if isinstance(item.get("venue"), dict)
    ]

    venue_ids = [
        str(venue.get("id") or "")
        for venue in venues
        if venue.get("id")
    ]
    venue_names = [
        str(venue.get("name") or "")
        for venue in venues
        if venue.get("name")
    ]

    enriched["venueIds"] = venue_ids
    enriched["venueNames"] = venue_names
    enriched["venueMatches"] = [
        {
            "venueId": item.get("venueId"),
            "venueName": item.get("venueName"),
            "method": item.get("method"),
            "confidence": item.get("confidence"),
            "matchedValue": item.get(
                "matchedValue"
            ),
            "matchedAlias": item.get(
                "matchedAlias"
            ),
        }
        for item in matches
    ]

    enriched["venueId"] = (
        venue_ids[0]
        if venue_ids
        else ""
    )
    enriched["venueName"] = (
        venue_names[0]
        if venue_names
        else ""
    )
    enriched["venueMatchConfidence"] = (
        match.get("confidence")
        if venue_ids
        else 0.0
    )

    diagnostic = {
        "eventId": event.get("id"),
        "title": event.get("title"),
        "locationName": event.get("locationName"),
        "region": event.get("region"),
        "regionCanonical": enriched[
            "regionCanonical"
        ],
        "status": match.get("status"),
        "method": match.get("method"),
        "confidence": match.get("confidence"),
        "matchedValue": match.get("matchedValue"),
        "matchedAlias": match.get("matchedAlias"),
        "venueId": enriched["venueId"],
        "venueName": enriched["venueName"],
        "venueIds": venue_ids,
        "venueNames": venue_names,
        "venueMatches": enriched[
            "venueMatches"
        ],
        "candidateVenueIds": match.get(
            "candidateVenueIds",
            [],
        ),
    }

    return enriched, diagnostic
