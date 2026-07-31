"""Validation rules for source and venue registries."""

from __future__ import annotations

from typing import Any, Mapping
from urllib.parse import urlparse

from .constants import (
    CONTENT_TYPES,
    SOURCE_LAYERS,
    SOURCE_STATUSES,
    SOURCE_TYPES,
    TAIWAN_REGIONS,
    TRUST_LEVELS,
    VENUE_TYPES,
)
from .loader import normalize_venue_key


def _is_http_url(value: Any) -> bool:
    cleaned = str(value or "").strip()

    if not cleaned:
        return False

    parsed = urlparse(cleaned)
    return (
        parsed.scheme in {"http", "https"}
        and bool(parsed.netloc)
    )


def _duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicate_values: set[str] = set()

    for value in values:
        if value in seen:
            duplicate_values.add(value)
        seen.add(value)

    return sorted(duplicate_values)


def validate_source_registry(
    registry: Mapping[str, Any],
) -> list[str]:
    """Return validation errors for source_registry.json."""

    errors: list[str] = []

    if registry.get("schemaVersion") != 1:
        errors.append("source_registry.schemaVersion must be 1")

    coverage_regions = registry.get("coverageRegions")

    if not isinstance(coverage_regions, list):
        errors.append("source_registry.coverageRegions must be a list")
        coverage_regions = []

    missing_regions = sorted(
        set(TAIWAN_REGIONS) - set(coverage_regions)
    )
    extra_regions = sorted(
        set(coverage_regions) - set(TAIWAN_REGIONS)
    )

    if missing_regions:
        errors.append(
            "source_registry is missing Taiwan regions: "
            + ", ".join(missing_regions)
        )

    if extra_regions:
        errors.append(
            "source_registry has unknown regions: "
            + ", ".join(extra_regions)
        )

    sources = registry.get("sources")

    if not isinstance(sources, list):
        return errors + ["source_registry.sources must be a list"]

    source_ids = [
        str(source.get("id") or "").strip()
        for source in sources
        if isinstance(source, dict)
    ]

    for duplicate_id in _duplicates(
        [source_id for source_id in source_ids if source_id]
    ):
        errors.append(f"duplicate source id: {duplicate_id}")

    for index, source in enumerate(sources):
        prefix = f"sources[{index}]"

        if not isinstance(source, dict):
            errors.append(f"{prefix} must be an object")
            continue

        source_id = str(source.get("id") or "").strip()

        for field_name in (
            "id",
            "name",
            "layer",
            "sourceType",
            "parser",
            "status",
            "trustLevel",
        ):
            if not str(source.get(field_name) or "").strip():
                errors.append(
                    f"{prefix}.{field_name} must not be empty"
                )

        if source.get("layer") not in SOURCE_LAYERS:
            errors.append(f"{prefix}.layer is not supported")

        if source.get("sourceType") not in SOURCE_TYPES:
            errors.append(f"{prefix}.sourceType is not supported")

        if source.get("status") not in SOURCE_STATUSES:
            errors.append(f"{prefix}.status is not supported")

        if source.get("trustLevel") not in TRUST_LEVELS:
            errors.append(f"{prefix}.trustLevel is not supported")

        if not isinstance(source.get("enabled"), bool):
            errors.append(f"{prefix}.enabled must be boolean")

        priority = source.get("priority")

        if not isinstance(priority, int) or not 0 <= priority <= 100:
            errors.append(
                f"{prefix}.priority must be an integer from 0 to 100"
            )

        refresh_hours = source.get("refreshHours")

        if (
            not isinstance(refresh_hours, int)
            or refresh_hours <= 0
        ):
            errors.append(
                f"{prefix}.refreshHours must be a positive integer"
            )

        official_url = source.get("officialUrl")
        listing_url = source.get("listingUrl")

        for field_name, url_value in (
            ("officialUrl", official_url),
            ("listingUrl", listing_url),
        ):
            if url_value and not _is_http_url(url_value):
                errors.append(
                    f"{prefix}.{field_name} must be an HTTP(S) URL"
                )

        if (
            source.get("status") == "active"
            and source.get("enabled") is True
            and not (
                _is_http_url(official_url)
                or _is_http_url(listing_url)
            )
        ):
            errors.append(
                f"{prefix} active source needs officialUrl or listingUrl"
            )

        source_regions = source.get("coverageRegions")

        if not isinstance(source_regions, list) or not source_regions:
            errors.append(
                f"{prefix}.coverageRegions must be a non-empty list"
            )
        else:
            for region in source_regions:
                if region != "全台" and region not in TAIWAN_REGIONS:
                    errors.append(
                        f"{prefix}.coverageRegions has unknown region: "
                        f"{region}"
                    )

        content_types = source.get("contentTypes")

        if not isinstance(content_types, list):
            errors.append(
                f"{prefix}.contentTypes must be a list"
            )
        else:
            for content_type in content_types:
                if content_type not in CONTENT_TYPES:
                    errors.append(
                        f"{prefix}.contentTypes has unsupported value: "
                        f"{content_type}"
                    )

        venue_ids = source.get("venueIds")

        if not isinstance(venue_ids, list):
            errors.append(f"{prefix}.venueIds must be a list")

        if not source_id:
            continue

    return errors


def validate_venue_registry(
    registry: Mapping[str, Any],
    source_registry: Mapping[str, Any] | None = None,
) -> list[str]:
    """Return validation errors for venues.json."""

    errors: list[str] = []

    if registry.get("schemaVersion") != 1:
        errors.append("venues.schemaVersion must be 1")

    venues = registry.get("venues")

    if not isinstance(venues, list):
        return errors + ["venues.venues must be a list"]

    venue_ids = [
        str(venue.get("id") or "").strip()
        for venue in venues
        if isinstance(venue, dict)
    ]

    for duplicate_id in _duplicates(
        [venue_id for venue_id in venue_ids if venue_id]
    ):
        errors.append(f"duplicate venue id: {duplicate_id}")

    alias_owners: dict[str, str] = {}
    source_ids = {
        str(source.get("id") or "").strip()
        for source in (
            source_registry.get("sources", [])
            if source_registry is not None
            else []
        )
        if isinstance(source, dict)
    }

    for index, venue in enumerate(venues):
        prefix = f"venues[{index}]"

        if not isinstance(venue, dict):
            errors.append(f"{prefix} must be an object")
            continue

        venue_id = str(venue.get("id") or "").strip()
        name = str(venue.get("name") or "").strip()

        if not venue_id:
            errors.append(f"{prefix}.id must not be empty")

        if not name:
            errors.append(f"{prefix}.name must not be empty")

        region = venue.get("region")

        if region not in TAIWAN_REGIONS:
            errors.append(f"{prefix}.region is not supported")

        aliases = venue.get("aliases")

        if not isinstance(aliases, list):
            errors.append(f"{prefix}.aliases must be a list")
            aliases = []

        for alias in [name, *aliases]:
            normalized_alias = normalize_venue_key(alias)

            if not normalized_alias:
                errors.append(
                    f"{prefix} contains an empty venue alias"
                )
                continue

            existing_owner = alias_owners.get(normalized_alias)

            if (
                existing_owner is not None
                and existing_owner != venue_id
            ):
                errors.append(
                    "venue alias collision: "
                    f"{alias!r} belongs to both "
                    f"{existing_owner} and {venue_id}"
                )
            else:
                alias_owners[normalized_alias] = venue_id

        venue_types = venue.get("venueTypes")

        if not isinstance(venue_types, list) or not venue_types:
            errors.append(
                f"{prefix}.venueTypes must be a non-empty list"
            )
        else:
            for venue_type in venue_types:
                if venue_type not in VENUE_TYPES:
                    errors.append(
                        f"{prefix}.venueTypes has unsupported value: "
                        f"{venue_type}"
                    )

        official_url = venue.get("officialUrl")

        if official_url and not _is_http_url(official_url):
            errors.append(
                f"{prefix}.officialUrl must be an HTTP(S) URL"
            )

        linked_source_ids = venue.get("sourceIds")

        if not isinstance(linked_source_ids, list):
            errors.append(f"{prefix}.sourceIds must be a list")
        elif source_registry is not None:
            for linked_source_id in linked_source_ids:
                if linked_source_id not in source_ids:
                    errors.append(
                        f"{prefix}.sourceIds references unknown source: "
                        f"{linked_source_id}"
                    )

    return errors


def validate_cross_references(
    source_registry: Mapping[str, Any],
    venue_registry: Mapping[str, Any],
) -> list[str]:
    """Validate source-to-venue references."""

    errors: list[str] = []
    venue_ids = {
        str(venue.get("id") or "").strip()
        for venue in venue_registry.get("venues", [])
        if isinstance(venue, dict)
    }

    for index, source in enumerate(
        source_registry.get("sources", [])
    ):
        if not isinstance(source, dict):
            continue

        for venue_id in source.get("venueIds", []):
            if venue_id not in venue_ids:
                errors.append(
                    f"sources[{index}].venueIds references "
                    f"unknown venue: {venue_id}"
                )

    return errors


def validate_all_registries(
    source_registry: Mapping[str, Any],
    venue_registry: Mapping[str, Any],
) -> list[str]:
    """Validate both registries and their references."""

    return [
        *validate_source_registry(source_registry),
        *validate_venue_registry(
            venue_registry,
            source_registry,
        ),
        *validate_cross_references(
            source_registry,
            venue_registry,
        ),
    ]
