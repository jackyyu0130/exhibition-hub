"""Build a reviewable enriched exhibition candidate dataset.

The command reads an existing exhibitions JSON file, enriches every event
with venue registry and content classification fields, excludes only events
whose editorial status is ``exclude_review``, and writes new output files.
It never overwrites the input file.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from exhibition_hub.registry import (  # noqa: E402
    enrich_event_with_registry,
    load_venue_registry,
)


INCLUDED_EDITORIAL_STATUSES = {
    "candidate",
    "needs_review",
}
EXCLUDED_EDITORIAL_STATUSES = {
    "exclude_review",
}

CATEGORY_ALIASES = {
    "歷史文化": "歷史",
    "自然科學": "自然",
    "快閃": "快閃店",
    "快閃活動": "快閃店",
}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build enriched candidate data without publishing it."
        )
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input exhibitions JSON path.",
    )
    parser.add_argument(
        "--venues",
        default="data/venues.json",
        help="Venue registry JSON path.",
    )
    parser.add_argument(
        "--legacy-aliases",
        default="data/venue-aliases.json",
        help=(
            "Optional legacy venue alias JSON path. "
            "Use an empty value to disable."
        ),
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Candidate exhibitions JSON output path.",
    )
    parser.add_argument(
        "--report-output",
        required=True,
        help="Candidate build report JSON output path.",
    )
    parser.add_argument(
        "--excluded-output",
        required=True,
        help="Excluded review queue JSON output path.",
    )

    arguments = parser.parse_args()
    input_path = Path(arguments.input).resolve()

    for output_name in (
        "output",
        "report_output",
        "excluded_output",
    ):
        output_path = Path(
            getattr(arguments, output_name)
        ).resolve()

        if output_path == input_path:
            parser.error(
                f"--{output_name.replace('_', '-')} "
                "must not overwrite --input"
            )

    return arguments


def load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(
        path.read_text(encoding="utf-8")
    )

    if not isinstance(payload, dict):
        raise ValueError(
            f"JSON root must be an object: {path}"
        )

    return payload


def write_json(
    path: Path,
    payload: Mapping[str, Any],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def percentage(count: int, total: int) -> float:
    if total <= 0:
        return 0.0

    return round(count / total, 4)


def event_categories(
    event: Mapping[str, Any],
) -> list[str]:
    categories = event.get("categories")

    if isinstance(categories, list):
        values = [
            str(value).strip()
            for value in categories
            if str(value).strip()
        ]
    else:
        values = []

    fallback = str(
        event.get("category") or ""
    ).strip()

    if not values and fallback:
        values = [fallback]

    return list(dict.fromkeys(values))


def normalize_category_labels(
    event: Mapping[str, Any],
) -> dict[str, Any]:
    result = dict(event)
    normalized = [
        CATEGORY_ALIASES.get(
            category,
            category,
        )
        for category in event_categories(event)
    ]
    normalized = list(
        dict.fromkeys(
            category
            for category in normalized
            if category
        )
    )

    content_type = str(
        result.get("contentType")
        or ""
    ).strip()
    if content_type == "concert":
        normalized = [
            category
            for category in normalized
            if category != "音樂"
        ]
        normalized = [
            "演唱會",
            *[
                category
                for category in normalized
                if category != "演唱會"
            ],
        ]

    if content_type == "popup" and "快閃店" not in normalized:
        normalized.append("快閃店")

    result["categories"] = normalized
    result["category"] = (
        normalized[0]
        if normalized
        else ""
    )
    return result


def recompute_stats(
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    total = len(events)
    image_count = sum(
        1
        for event in events
        if str(event.get("image") or "").strip()
    )
    multi_image_count = sum(
        1
        for event in events
        if isinstance(event.get("images"), list)
        and len(event.get("images", [])) > 1
    )
    coordinate_count = sum(
        1
        for event in events
        if event.get("latitude") is not None
        and event.get("longitude") is not None
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
        "imageCoverage": percentage(
            image_count,
            total,
        ),
        "coordinateCoverage": percentage(
            coordinate_count,
            total,
        ),
        "categoryCounts": dict(
            category_counts.items()
        ),
    }


def compact_event(
    event: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "id": event.get("id"),
        "title": event.get("title"),
        "locationName": event.get("locationName"),
        "region": event.get("region"),
        "regionCanonical": event.get(
            "regionCanonical"
        ),
        "venueIds": event.get("venueIds", []),
        "venueCoverageStatus": event.get(
            "venueCoverageStatus"
        ),
        "contentType": event.get("contentType"),
        "contentTypes": event.get(
            "contentTypes",
            [],
        ),
        "eventFormat": event.get("eventFormat"),
        "editorialStatus": event.get(
            "editorialStatus"
        ),
        "editorialFlags": event.get(
            "editorialFlags",
            [],
        ),
    }


def build_candidate_payload(
    source_payload: Mapping[str, Any],
    venue_registry: Mapping[str, Any],
    legacy_registry: Mapping[str, Any] | None,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    source_events = source_payload.get("events")

    if not isinstance(source_events, list):
        raise ValueError(
            "Input JSON must contain an events list."
        )

    enriched_events: list[dict[str, Any]] = []

    for event in source_events:
        if not isinstance(event, dict):
            continue

        enriched, _ = enrich_event_with_registry(
            event,
            venue_registry,
            legacy_registry,
        )
        enriched_events.append(
            normalize_category_labels(
                enriched
            )
        )

    editorial_counts = Counter(
        str(
            event.get("editorialStatus")
            or "unknown"
        )
        for event in enriched_events
    )

    included_events = [
        event
        for event in enriched_events
        if event.get("editorialStatus")
        in INCLUDED_EDITORIAL_STATUSES
    ]
    excluded_events = [
        event
        for event in enriched_events
        if event.get("editorialStatus")
        in EXCLUDED_EDITORIAL_STATUSES
    ]
    unknown_policy_events = [
        event
        for event in enriched_events
        if event.get("editorialStatus")
        not in (
            INCLUDED_EDITORIAL_STATUSES
            | EXCLUDED_EDITORIAL_STATUSES
        )
    ]

    if unknown_policy_events:
        unknown_statuses = sorted(
            {
                str(
                    event.get("editorialStatus")
                    or "unknown"
                )
                for event in unknown_policy_events
            }
        )
        raise ValueError(
            "Unknown editorial statuses: "
            + ", ".join(unknown_statuses)
        )

    venue_coverage_counts = Counter(
        str(
            event.get("venueCoverageStatus")
            or "none"
        )
        for event in included_events
    )
    resolved_event_count = sum(
        1
        for event in included_events
        if event.get("venueIds")
    )
    multi_venue_event_count = sum(
        1
        for event in included_events
        if len(event.get("venueIds", [])) > 1
    )

    candidate_payload = dict(source_payload)
    candidate_payload["stats"] = recompute_stats(
        included_events
    )
    candidate_payload["events"] = included_events
    candidate_payload["registryBuild"] = {
        "mode": "enriched-candidate",
        "published": False,
        "sourceUpdatedAt": source_payload.get(
            "updatedAt"
        ),
        "inputEventCount": len(source_events),
        "processedEventCount": len(
            enriched_events
        ),
        "outputEventCount": len(
            included_events
        ),
        "excludedEventCount": len(
            excluded_events
        ),
        "venueRegistryCount": len(
            venue_registry.get("venues", [])
        ),
        "editorialStatusCounts": dict(
            sorted(editorial_counts.items())
        ),
        "resolvedEventCount": (
            resolved_event_count
        ),
        "multiVenueEventCount": (
            multi_venue_event_count
        ),
        "venueCoverageStatusCounts": dict(
            sorted(
                venue_coverage_counts.items()
            )
        ),
    }

    excluded_payload = {
        "mode": "excluded-events-review",
        "published": False,
        "sourceUpdatedAt": source_payload.get(
            "updatedAt"
        ),
        "eventCount": len(excluded_events),
        "events": excluded_events,
    }

    report = {
        "mode": "enriched-candidate-build",
        "published": False,
        "sourceUpdatedAt": source_payload.get(
            "updatedAt"
        ),
        "inputEventCount": len(source_events),
        "processedEventCount": len(
            enriched_events
        ),
        "outputEventCount": len(
            included_events
        ),
        "excludedEventCount": len(
            excluded_events
        ),
        "venueRegistryCount": len(
            venue_registry.get("venues", [])
        ),
        "editorialStatusCounts": dict(
            sorted(editorial_counts.items())
        ),
        "venueCoverageStatusCounts": dict(
            sorted(
                venue_coverage_counts.items()
            )
        ),
        "resolvedEventCount": resolved_event_count,
        "multiVenueEventCount": (
            multi_venue_event_count
        ),
        "candidateStats": candidate_payload[
            "stats"
        ],
        "excludedEvents": [
            compact_event(event)
            for event in excluded_events
        ],
        "reviewEventCount": editorial_counts.get(
            "needs_review",
            0,
        ),
    }

    return (
        candidate_payload,
        excluded_payload,
        report,
    )


def main() -> int:
    arguments = parse_arguments()

    input_path = Path(arguments.input)
    venue_path = Path(arguments.venues)
    legacy_path = (
        Path(arguments.legacy_aliases)
        if arguments.legacy_aliases
        else None
    )

    source_payload = load_json_object(input_path)
    venue_registry = load_venue_registry(
        venue_path
    )
    legacy_registry = (
        load_json_object(legacy_path)
        if legacy_path is not None
        and legacy_path.exists()
        else None
    )

    candidate, excluded, report = (
        build_candidate_payload(
            source_payload,
            venue_registry,
            legacy_registry,
        )
    )

    write_json(Path(arguments.output), candidate)
    write_json(
        Path(arguments.excluded_output),
        excluded,
    )
    write_json(
        Path(arguments.report_output),
        report,
    )

    print(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
