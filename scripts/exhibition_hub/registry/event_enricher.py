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
) -> list[str]:
    values: list[str] = []

    for field_name in (
        "locationName",
        "venueGroup",
        "location",
    ):
        value = str(event.get(field_name) or "").strip()

        if value and value not in values:
            values.append(value)

    sessions = event.get("sessions")

    if isinstance(sessions, list):
        for session in sessions[:3]:
            if not isinstance(session, dict):
                continue

            value = str(
                session.get("locationName") or ""
            ).strip()

            if value and value not in values:
                values.append(value)

    return values


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


def _special_venue_match(
    event: Mapping[str, Any],
    venue_registry: Mapping[str, Any],
) -> dict[str, Any] | None:
    values = _event_venue_values(event)
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
                return {
                    "status": "matched",
                    "venue": venue,
                    "method": "special_pattern",
                    "confidence": 1.0,
                    "matchedValue": joined,
                    "matchedAlias": next(
                        pattern
                        for pattern in patterns
                        if pattern in joined
                    ),
                }

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
            return {
                "status": "matched",
                "venue": venue,
                "method": "special_region",
                "confidence": 0.95,
                "matchedValue": joined,
                "matchedAlias": "故宮",
            }

    return None


def resolve_event_venue(
    event: Mapping[str, Any],
    venue_registry: Mapping[str, Any],
    legacy_alias_registry: (
        Mapping[str, Any] | None
    ) = None,
) -> dict[str, Any]:
    """Resolve an event venue using exact and contained aliases."""

    special = _special_venue_match(
        event,
        venue_registry,
    )

    if special:
        return special

    alias_records = _build_alias_records(
        venue_registry,
        legacy_alias_registry,
    )
    event_region = normalize_region(
        event.get("region")
    )
    venue_values = _event_venue_values(event)

    exact_candidates: list[dict[str, Any]] = []

    for value in venue_values:
        normalized_value = normalize_venue_key(value)

        for record in alias_records:
            if record["alias"] != normalized_value:
                continue

            venue = record["venue"]

            if not _region_compatible(
                event_region,
                venue,
            ):
                continue

            exact_candidates.append(
                {
                    **record,
                    "matchedValue": value,
                }
            )

    exact_venues = _unique_venues(
        [
            candidate["venue"]
            for candidate in exact_candidates
        ]
    )

    if len(exact_venues) == 1:
        selected = next(
            candidate
            for candidate in exact_candidates
            if candidate["venue"]["id"]
            == exact_venues[0]["id"]
        )
        return {
            "status": "matched",
            "venue": selected["venue"],
            "method": (
                "legacy_exact"
                if selected["source"]
                == "legacy_alias"
                else "registry_exact"
            ),
            "confidence": 1.0,
            "matchedValue": selected[
                "matchedValue"
            ],
            "matchedAlias": selected["alias"],
        }

    if len(exact_venues) > 1:
        return {
            "status": "ambiguous",
            "venue": None,
            "method": "exact",
            "confidence": 0.0,
            "matchedValue": " | ".join(
                venue_values
            ),
            "matchedAlias": "",
            "candidateVenueIds": [
                venue["id"]
                for venue in exact_venues
            ],
        }

    contained_candidates: list[
        dict[str, Any]
    ] = []

    for value in venue_values:
        normalized_value = normalize_venue_key(value)

        for record in alias_records:
            alias = record["alias"]

            if len(alias) < 3:
                continue

            if alias not in normalized_value:
                continue

            venue = record["venue"]

            if not _region_compatible(
                event_region,
                venue,
            ):
                continue

            contained_candidates.append(
                {
                    **record,
                    "matchedValue": value,
                    "aliasLength": len(alias),
                }
            )

    if contained_candidates:
        longest = max(
            candidate["aliasLength"]
            for candidate in contained_candidates
        )
        best_candidates = [
            candidate
            for candidate in contained_candidates
            if candidate["aliasLength"] == longest
        ]
        best_venues = _unique_venues(
            [
                candidate["venue"]
                for candidate in best_candidates
            ]
        )

        if len(best_venues) == 1:
            selected = best_candidates[0]
            return {
                "status": "matched",
                "venue": selected["venue"],
                "method": (
                    "legacy_contains"
                    if selected["source"]
                    == "legacy_alias"
                    else "registry_contains"
                ),
                "confidence": 0.9,
                "matchedValue": selected[
                    "matchedValue"
                ],
                "matchedAlias": selected["alias"],
            }

        return {
            "status": "ambiguous",
            "venue": None,
            "method": "contains",
            "confidence": 0.0,
            "matchedValue": " | ".join(
                venue_values
            ),
            "matchedAlias": "",
            "candidateVenueIds": [
                venue["id"]
                for venue in best_venues
            ],
        }

    return {
        "status": "unmatched",
        "venue": None,
        "method": "none",
        "confidence": 0.0,
        "matchedValue": " | ".join(
            venue_values
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

    venue = match.get("venue")

    if isinstance(venue, dict):
        enriched["venueId"] = venue.get("id")
        enriched["venueName"] = venue.get("name")
        enriched["venueMatchConfidence"] = (
            match.get("confidence")
        )
    else:
        enriched["venueId"] = ""
        enriched["venueName"] = ""
        enriched["venueMatchConfidence"] = 0.0

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
        "candidateVenueIds": match.get(
            "candidateVenueIds",
            [],
        ),
    }

    return enriched, diagnostic
