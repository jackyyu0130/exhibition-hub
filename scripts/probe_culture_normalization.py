"""Run a read-only normalization dry run for Culture Ministry records.

This command downloads and normalizes live data for diagnostics only.
It does not modify website JSON files, create commits, or deploy the site.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import sys
from typing import Any

from exhibition_hub.collectors.base import CollectorContext
from exhibition_hub.collectors.culture_ministry import (
    CultureMinistryCollector,
)
from exhibition_hub.normalizers.culture_ministry import (
    normalize_culture_records,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Collect and normalize Culture Ministry data "
            "without publishing it."
        )
    )
    parser.add_argument(
        "--category",
        default="6",
        help="Culture Ministry category ID. Default: 6.",
    )
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=5,
        help="Maximum normalized samples to display.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="HTTP timeout in seconds.",
    )

    arguments = parser.parse_args()

    if not arguments.category.strip():
        parser.error("--category must not be empty")

    if arguments.sample_limit < 0:
        parser.error("--sample-limit must be zero or greater")

    if arguments.timeout <= 0:
        parser.error("--timeout must be greater than zero")

    return arguments


def calculate_percentage(
    count: int,
    total: int,
) -> float:
    """Return a percentage rounded to two decimal places."""

    if total <= 0:
        return 0.0

    return round(
        count / total * 100,
        2,
    )


def count_missing(
    events: list[dict[str, Any]],
    field_name: str,
) -> int:
    """Count normalized events missing a useful field value."""

    return sum(
        1
        for event in events
        if not event.get(field_name)
    )


def build_sample(
    event: dict[str, Any],
) -> dict[str, Any]:
    """Return a compact normalized event sample."""

    sessions = event.get("sessions")

    return {
        "id": event.get("id"),
        "title": event.get("title"),
        "startDate": event.get("startDate"),
        "endDate": event.get("endDate"),
        "locationName": event.get("locationName"),
        "address": event.get("address"),
        "region": event.get("region"),
        "latitude": event.get("latitude"),
        "longitude": event.get("longitude"),
        "price": event.get("price"),
        "image": event.get("image"),
        "sourceUrl": event.get("sourceUrl"),
        "ticketUrl": event.get("ticketUrl"),
        "organizers": event.get("organizers"),
        "sessionCount": (
            len(sessions)
            if isinstance(sessions, list)
            else 0
        ),
    }


def main() -> int:
    arguments = parse_arguments()

    context = CollectorContext.create(
        timeout_seconds=arguments.timeout,
        settings={
            "environment": "normalization-dry-run",
            "publish": False,
        },
    )

    collector = CultureMinistryCollector(
        categories=[arguments.category]
    )
    collection_result = collector.collect(context)

    if not collection_result.succeeded:
        report = {
            "mode": "normalization-dry-run",
            "published": False,
            "succeeded": False,
            "stage": "collection",
            "errors": collection_result.errors,
            "warnings": collection_result.warnings,
        }

        print(
            json.dumps(
                report,
                ensure_ascii=False,
                indent=2,
            )
        )

        return 1

    normalized, normalization_errors = (
        normalize_culture_records(
            collection_result.events
        )
    )

    total = len(normalized)

    missing_image = count_missing(
        normalized,
        "image",
    )
    missing_source_url = count_missing(
        normalized,
        "sourceUrl",
    )
    missing_ticket_url = count_missing(
        normalized,
        "ticketUrl",
    )
    missing_location_name = count_missing(
        normalized,
        "locationName",
    )
    missing_address = count_missing(
        normalized,
        "address",
    )
    missing_region = count_missing(
        normalized,
        "region",
    )
    missing_description = count_missing(
        normalized,
        "description",
    )

    missing_coordinates = sum(
        1
        for event in normalized
        if (
            event.get("latitude") is None
            or event.get("longitude") is None
        )
    )

    missing_sessions = sum(
        1
        for event in normalized
        if not event.get("sessions")
    )

    identifiers = [
        str(event.get("id") or "")
        for event in normalized
        if event.get("id")
    ]
    identifier_counts = Counter(identifiers)

    duplicate_ids = sorted(
        identifier
        for identifier, count
        in identifier_counts.items()
        if count > 1
    )

    region_counts = Counter(
        str(event.get("region") or "未辨識")
        for event in normalized
    )

    report = {
        "mode": "normalization-dry-run",
        "published": False,
        "succeeded": total > 0,
        "sourceId": collection_result.source_id,
        "category": arguments.category,
        "rawEventCount": collection_result.event_count,
        "normalizedEventCount": total,
        "normalizationErrorCount": len(
            normalization_errors
        ),
        "normalizationSuccessRate": (
            calculate_percentage(
                total,
                collection_result.event_count,
            )
        ),
        "duplicateIdCount": len(duplicate_ids),
        "duplicateIds": duplicate_ids[:20],
        "quality": {
            "missingImage": {
                "count": missing_image,
                "percentage": calculate_percentage(
                    missing_image,
                    total,
                ),
            },
            "missingSourceUrl": {
                "count": missing_source_url,
                "percentage": calculate_percentage(
                    missing_source_url,
                    total,
                ),
            },
            "missingTicketUrl": {
                "count": missing_ticket_url,
                "percentage": calculate_percentage(
                    missing_ticket_url,
                    total,
                ),
            },
            "missingLocationName": {
                "count": missing_location_name,
                "percentage": calculate_percentage(
                    missing_location_name,
                    total,
                ),
            },
            "missingAddress": {
                "count": missing_address,
                "percentage": calculate_percentage(
                    missing_address,
                    total,
                ),
            },
            "missingRegion": {
                "count": missing_region,
                "percentage": calculate_percentage(
                    missing_region,
                    total,
                ),
            },
            "missingCoordinates": {
                "count": missing_coordinates,
                "percentage": calculate_percentage(
                    missing_coordinates,
                    total,
                ),
            },
            "missingDescription": {
                "count": missing_description,
                "percentage": calculate_percentage(
                    missing_description,
                    total,
                ),
            },
            "missingSessions": {
                "count": missing_sessions,
                "percentage": calculate_percentage(
                    missing_sessions,
                    total,
                ),
            },
        },
        "regionCounts": dict(
            sorted(region_counts.items())
        ),
        "collectionWarnings": (
            collection_result.warnings
        ),
        "normalizationErrors": (
            normalization_errors[:20]
        ),
        "samples": [
            build_sample(event)
            for event in normalized[
                : arguments.sample_limit
            ]
        ],
    }

    print(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        )
    )

    return 0 if total > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
