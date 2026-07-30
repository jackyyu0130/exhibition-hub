"""Run a read-only normalization dry run for Culture Ministry records.

This command downloads and normalizes live data for diagnostics only.
It does not modify website JSON files, create commits, or deploy the site.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
import sys
from typing import Any
from urllib.parse import urlparse

from exhibition_hub.collectors.base import CollectorContext
from exhibition_hub.collectors.culture_ministry import (
    CultureMinistryCollector,
)
from exhibition_hub.normalizers.culture_ministry import (
    normalize_culture_records,
)


QUALITY_TIERS = (
    "ready",
    "needs_enrichment",
    "needs_review",
    "rejected",
)

LOW_TRUST_SOURCE_DOMAINS = (
    "facebook.com",
    "fb.com",
    "instagram.com",
    "threads.net",
    "twitter.com",
    "x.com",
)

SHORTENER_DOMAINS = (
    "bit.ly",
    "goo.gl",
    "lihi.cc",
    "lihi1.com",
    "lihi1.me",
    "ppt.cc",
    "reurl.cc",
    "tinyurl.com",
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
        "--quality-sample-limit",
        type=int,
        default=150,
        help=(
            "Maximum events to display for each quality queue. "
            "Default: 150."
        ),
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

    if arguments.quality_sample_limit < 0:
        parser.error(
            "--quality-sample-limit must be zero or greater"
        )

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


def clean_string(value: Any) -> str:
    """Return a trimmed string for diagnostic comparisons."""

    if value is None:
        return ""

    return str(value).strip()


def parse_normalized_date(value: Any) -> date | None:
    """Parse a normalized YYYY-MM-DD value when possible."""

    cleaned = clean_string(value)

    if not cleaned:
        return None

    try:
        return date.fromisoformat(cleaned[:10])
    except ValueError:
        return None


def get_url_domain(value: Any) -> str:
    """Return a lower-case hostname without a leading www."""

    cleaned = clean_string(value)

    if not cleaned:
        return ""

    parsed = urlparse(cleaned)
    domain = (parsed.hostname or "").lower()

    if domain.startswith("www."):
        domain = domain[4:]

    return domain


def domain_matches(
    domain: str,
    candidates: tuple[str, ...],
) -> bool:
    """Return whether a hostname matches a listed root domain."""

    return any(
        domain == candidate
        or domain.endswith(f".{candidate}")
        for candidate in candidates
    )


def describe_source_url(value: Any) -> str:
    """Classify a source URL for publication-quality review."""

    cleaned = clean_string(value)

    if not cleaned:
        return "missing"

    parsed = urlparse(cleaned)

    if parsed.scheme not in {"http", "https"}:
        return "invalid"

    domain = get_url_domain(cleaned)

    if not domain:
        return "invalid"

    if domain_matches(
        domain,
        LOW_TRUST_SOURCE_DOMAINS,
    ):
        return "social"

    if domain_matches(
        domain,
        SHORTENER_DOMAINS,
    ):
        return "shortener"

    return "official_candidate"


def appears_to_require_ticket(
    price: Any,
) -> bool:
    """Estimate whether a listed price likely requires a ticket URL."""

    cleaned = clean_string(price).lower()

    if not cleaned:
        return False

    free_markers = (
        "免費",
        "自由入場",
        "free",
        "免票",
    )

    return not any(
        marker in cleaned
        for marker in free_markers
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


def build_unrecognized_region_sample(
    event: dict[str, Any],
) -> dict[str, Any]:
    """Return fields needed to inspect an unrecognized region."""

    return {
        "id": event.get("id"),
        "title": event.get("title"),
        "startDate": event.get("startDate"),
        "endDate": event.get("endDate"),
        "locationName": event.get("locationName"),
        "address": event.get("address"),
        "latitude": event.get("latitude"),
        "longitude": event.get("longitude"),
        "sourceUrl": event.get("sourceUrl"),
        "ticketUrl": event.get("ticketUrl"),
    }


def evaluate_event_quality(
    event: dict[str, Any],
    duplicate_ids: set[str],
) -> dict[str, Any]:
    """Assign a publication-quality tier and explain the reasons."""

    rejected_reasons: list[str] = []
    review_reasons: list[str] = []
    enrichment_reasons: list[str] = []

    event_id = clean_string(event.get("id"))
    title = clean_string(event.get("title"))
    start_date_value = clean_string(
        event.get("startDate")
    )
    end_date_value = clean_string(
        event.get("endDate")
    )
    location_name = clean_string(
        event.get("locationName")
    )
    address = clean_string(event.get("address"))
    region = clean_string(event.get("region"))
    sessions = event.get("sessions")

    core_fields = {
        "id": event_id,
        "title": title,
        "startDate": start_date_value,
        "endDate": end_date_value,
        "locationName": location_name,
        "address": address,
        "region": region,
    }

    for field_name, field_value in core_fields.items():
        if not field_value:
            rejected_reasons.append(
                f"missing_core_field:{field_name}"
            )

    if not isinstance(sessions, list) or not sessions:
        rejected_reasons.append(
            "missing_core_field:sessions"
        )

    start_date = parse_normalized_date(
        start_date_value
    )
    end_date = parse_normalized_date(
        end_date_value
    )

    if start_date_value and start_date is None:
        rejected_reasons.append(
            "invalid_date:startDate"
        )

    if end_date_value and end_date is None:
        rejected_reasons.append(
            "invalid_date:endDate"
        )

    if (
        start_date is not None
        and end_date is not None
        and end_date < start_date
    ):
        rejected_reasons.append(
            "invalid_date_range:end_before_start"
        )

    if event_id and event_id in duplicate_ids:
        review_reasons.append("duplicate_id")

    source_url = clean_string(
        event.get("sourceUrl")
    )
    source_url_kind = describe_source_url(
        source_url
    )

    if source_url_kind == "missing":
        enrichment_reasons.append(
            "missing_source_url"
        )
    elif source_url_kind == "invalid":
        review_reasons.append(
            "invalid_source_url"
        )
    elif source_url_kind == "social":
        review_reasons.append(
            "social_media_source_url"
        )
    elif source_url_kind == "shortener":
        review_reasons.append(
            "shortened_source_url"
        )

    if not clean_string(event.get("image")):
        enrichment_reasons.append("missing_image")

    if not clean_string(
        event.get("description")
    ):
        enrichment_reasons.append(
            "missing_description"
        )

    if (
        event.get("latitude") is None
        or event.get("longitude") is None
    ):
        enrichment_reasons.append(
            "missing_coordinates"
        )

    organizers = event.get("organizers")

    if not isinstance(organizers, list) or not organizers:
        enrichment_reasons.append(
            "missing_organizers"
        )

    ticket_url = clean_string(
        event.get("ticketUrl")
    )

    if (
        appears_to_require_ticket(
            event.get("price")
        )
        and not ticket_url
    ):
        enrichment_reasons.append(
            "missing_ticket_url_for_priced_event"
        )

    ticket_url_kind = describe_source_url(
        ticket_url
    )

    if ticket_url and ticket_url_kind == "invalid":
        review_reasons.append(
            "invalid_ticket_url"
        )
    elif ticket_url and ticket_url_kind == "social":
        review_reasons.append(
            "social_media_ticket_url"
        )
    elif ticket_url and ticket_url_kind == "shortener":
        review_reasons.append(
            "shortened_ticket_url"
        )

    if rejected_reasons:
        tier = "rejected"
        reasons = rejected_reasons
    elif review_reasons:
        tier = "needs_review"
        reasons = review_reasons
    elif enrichment_reasons:
        tier = "needs_enrichment"
        reasons = enrichment_reasons
    else:
        tier = "ready"
        reasons = []

    return {
        "tier": tier,
        "reasons": reasons,
        "rejectedReasons": rejected_reasons,
        "reviewReasons": review_reasons,
        "enrichmentReasons": enrichment_reasons,
        "sourceUrlKind": source_url_kind,
    }


def build_quality_event_sample(
    event: dict[str, Any],
    assessment: dict[str, Any],
) -> dict[str, Any]:
    """Return a compact quality-queue entry."""

    return {
        "id": event.get("id"),
        "title": event.get("title"),
        "tier": assessment.get("tier"),
        "reasons": assessment.get("reasons"),
        "sourceUrlKind": assessment.get(
            "sourceUrlKind"
        ),
        "startDate": event.get("startDate"),
        "endDate": event.get("endDate"),
        "locationName": event.get(
            "locationName"
        ),
        "address": event.get("address"),
        "region": event.get("region"),
        "image": event.get("image"),
        "sourceUrl": event.get("sourceUrl"),
        "ticketUrl": event.get("ticketUrl"),
    }



def build_source_domain_counts(
    events: list[dict[str, Any]],
) -> dict[str, int]:
    """Count source URL hostnames for enrichment planning."""

    counts: Counter[str] = Counter()

    for event in events:
        domain = get_url_domain(
            event.get("sourceUrl")
        )

        if domain:
            counts[domain] += 1

    return dict(
        sorted(
            counts.items(),
            key=lambda item: (
                -item[1],
                item[0],
            ),
        )
    )


def build_image_host_counts(
    events: list[dict[str, Any]],
) -> dict[str, int]:
    """Count image hostnames for diagnostics."""

    counts: Counter[str] = Counter()

    for event in events:
        domain = get_url_domain(
            event.get("image")
        )

        if domain:
            counts[domain] += 1

    return dict(
        sorted(
            counts.items(),
            key=lambda item: (
                -item[1],
                item[0],
            ),
        )
    )


def build_enrichment_queue_entry(
    event: dict[str, Any],
    actions: list[str],
    priority: str,
) -> dict[str, Any]:
    """Return one compact enrichment queue entry."""

    return {
        "id": event.get("id"),
        "title": event.get("title"),
        "priority": priority,
        "actions": actions,
        "startDate": event.get("startDate"),
        "endDate": event.get("endDate"),
        "locationName": event.get(
            "locationName"
        ),
        "address": event.get("address"),
        "region": event.get("region"),
        "price": event.get("price"),
        "image": event.get("image"),
        "sourceUrl": event.get("sourceUrl"),
        "sourceUrlKind": describe_source_url(
            event.get("sourceUrl")
        ),
        "ticketUrl": event.get("ticketUrl"),
    }


def plan_enrichment_actions(
    event: dict[str, Any],
) -> tuple[str, list[str]]:
    """Return the priority and actions needed for one event."""

    actions: list[str] = []

    source_url = clean_string(
        event.get("sourceUrl")
    )
    source_kind = describe_source_url(
        source_url
    )
    image = clean_string(event.get("image"))
    description = clean_string(
        event.get("description")
    )
    ticket_url = clean_string(
        event.get("ticketUrl")
    )

    if source_kind == "social":
        actions.append(
            "replace_social_source_with_official_page"
        )
    elif source_kind == "shortener":
        actions.append(
            "resolve_shortened_source_url"
        )
    elif source_kind == "invalid":
        actions.append(
            "replace_invalid_source_url"
        )
    elif source_kind == "missing":
        actions.append(
            "find_official_source_url"
        )

    if not image:
        if source_kind == "official_candidate":
            actions.append(
                "extract_image_from_official_page"
            )
        else:
            actions.append(
                "find_official_image_after_source_resolution"
            )

    if not description:
        actions.append(
            "add_description_from_official_page"
        )

    if (
        event.get("latitude") is None
        or event.get("longitude") is None
    ):
        actions.append(
            "add_coordinates_optional"
        )

    if (
        appears_to_require_ticket(
            event.get("price")
        )
        and not ticket_url
    ):
        actions.append(
            "verify_ticket_url_for_priced_event"
        )

    if any(
        action in actions
        for action in (
            "replace_social_source_with_official_page",
            "resolve_shortened_source_url",
            "replace_invalid_source_url",
        )
    ):
        priority = "P1_source_review"
    elif "find_official_source_url" in actions:
        priority = "P2_find_official_source"
    elif "extract_image_from_official_page" in actions:
        priority = "P3_extract_official_image"
    elif actions:
        priority = "P4_optional_enrichment"
    else:
        priority = "P0_ready"

    return priority, actions


def build_enrichment_plan(
    events: list[dict[str, Any]],
    sample_limit: int,
) -> dict[str, Any]:
    """Build prioritized queues for source and image enrichment."""

    queue_names = (
        "P0_ready",
        "P1_source_review",
        "P2_find_official_source",
        "P3_extract_official_image",
        "P4_optional_enrichment",
    )

    queues: dict[str, list[dict[str, Any]]] = {
        name: []
        for name in queue_names
    }
    action_counts: Counter[str] = Counter()
    source_kind_counts: Counter[str] = Counter()

    for event in events:
        source_kind = describe_source_url(
            event.get("sourceUrl")
        )
        source_kind_counts[source_kind] += 1

        priority, actions = plan_enrichment_actions(
            event
        )
        action_counts.update(actions)

        queues[priority].append(
            build_enrichment_queue_entry(
                event,
                actions,
                priority,
            )
        )

    return {
        "queueCounts": {
            queue_name: len(queues[queue_name])
            for queue_name in queue_names
        },
        "queuePercentages": {
            queue_name: calculate_percentage(
                len(queues[queue_name]),
                len(events),
            )
            for queue_name in queue_names
        },
        "actionCounts": dict(
            sorted(
                action_counts.items(),
                key=lambda item: (
                    -item[1],
                    item[0],
                ),
            )
        ),
        "sourceUrlKindCounts": {
            source_kind: source_kind_counts.get(
                source_kind,
                0,
            )
            for source_kind in (
                "official_candidate",
                "missing",
                "social",
                "shortener",
                "invalid",
            )
        },
        "sourceDomainCounts": (
            build_source_domain_counts(events)
        ),
        "imageHostCounts": (
            build_image_host_counts(events)
        ),
        "queues": {
            queue_name: queues[queue_name][
                :sample_limit
            ]
            for queue_name in queue_names
        },
        "notes": {
            "P0_ready": (
                "No source or enrichment action is "
                "currently required."
            ),
            "P1_source_review": (
                "Social, shortened, or invalid source "
                "URLs must be replaced or resolved first."
            ),
            "P2_find_official_source": (
                "No source URL is available. Locate the "
                "official venue or exhibition page."
            ),
            "P3_extract_official_image": (
                "An official-looking source exists, but "
                "the exhibition image is missing."
            ),
            "P4_optional_enrichment": (
                "Only optional fields such as coordinates "
                "or ticket verification remain."
            ),
        },
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
    duplicate_id_set = set(duplicate_ids)

    region_counts = Counter(
        str(event.get("region") or "未辨識")
        for event in normalized
    )

    unrecognized_region_events = [
        build_unrecognized_region_sample(event)
        for event in normalized
        if not event.get("region")
    ]

    quality_assessments = [
        (
            event,
            evaluate_event_quality(
                event,
                duplicate_id_set,
            ),
        )
        for event in normalized
    ]

    quality_tier_counts = Counter(
        assessment["tier"]
        for _, assessment in quality_assessments
    )

    quality_tier_percentages = {
        tier: calculate_percentage(
            quality_tier_counts.get(tier, 0),
            total,
        )
        for tier in QUALITY_TIERS
    }

    quality_queues = {
        tier: [
            build_quality_event_sample(
                event,
                assessment,
            )
            for event, assessment
            in quality_assessments
            if assessment["tier"] == tier
        ]
        for tier in QUALITY_TIERS
    }

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
        "qualityTierCounts": {
            tier: quality_tier_counts.get(tier, 0)
            for tier in QUALITY_TIERS
        },
        "qualityTierPercentages": (
            quality_tier_percentages
        ),
        "enrichmentPlan": build_enrichment_plan(
            normalized,
            arguments.quality_sample_limit,
        ),
        "publicationPolicy": {
            "automaticPublishTier": "ready",
            "blockedFromAutomaticPublish": [
                "needs_enrichment",
                "needs_review",
                "rejected",
            ],
            "notes": {
                "ready": (
                    "Core fields and publication assets "
                    "passed the current checks."
                ),
                "needs_enrichment": (
                    "Core fields passed, but optional "
                    "content or assets are incomplete."
                ),
                "needs_review": (
                    "A source URL, duplicate ID, or other "
                    "risk requires human verification."
                ),
                "rejected": (
                    "A core field or valid date range is "
                    "missing, so automatic publication "
                    "is blocked."
                ),
            },
        },
        "readyEvents": quality_queues["ready"][
            : arguments.quality_sample_limit
        ],
        "enrichmentEvents": (
            quality_queues["needs_enrichment"][
                : arguments.quality_sample_limit
            ]
        ),
        "reviewEvents": (
            quality_queues["needs_review"][
                : arguments.quality_sample_limit
            ]
        ),
        "rejectedEvents": (
            quality_queues["rejected"][
                : arguments.quality_sample_limit
            ]
        ),
        "regionCounts": dict(
            sorted(region_counts.items())
        ),
        "unrecognizedRegionCount": len(
            unrecognized_region_events
        ),
        "unrecognizedRegionEvents": (
            unrecognized_region_events[:30]
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
