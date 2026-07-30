"""Dry-run venue registry and content classification on events.

The command never overwrites the input file. It can optionally write a
preview JSON and a diagnostic report to separate paths.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from exhibition_hub.registry import (  # noqa: E402
    enrich_event_with_registry,
    load_venue_registry,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Apply venue and content registries in dry-run mode."
        )
    )
    parser.add_argument(
        "--input",
        default="data/exhibitions.json",
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
        "--report-output",
        default="",
        help="Optional path for the dry-run report JSON.",
    )
    parser.add_argument(
        "--preview-output",
        default="",
        help=(
            "Optional path for a full enriched preview JSON. "
            "The input path cannot be used."
        ),
    )
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=50,
        help="Maximum samples per diagnostic queue.",
    )

    arguments = parser.parse_args()

    if arguments.sample_limit < 0:
        parser.error("--sample-limit must be zero or greater")

    input_path = Path(arguments.input).resolve()

    for output_name in (
        "report_output",
        "preview_output",
    ):
        value = getattr(arguments, output_name)

        if value and Path(value).resolve() == input_path:
            parser.error(
                f"--{output_name.replace('_', '-')} "
                "must not overwrite --input"
            )

    return arguments


def load_json_object(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, dict):
        raise ValueError(
            f"JSON root must be an object: {path}"
        )

    return payload


def write_json(
    path: Path,
    payload: dict[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def percentage(
    count: int,
    total: int,
) -> float:
    if total <= 0:
        return 0.0

    return round(count / total * 100, 2)


def compact_event_sample(
    event: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": event.get("id"),
        "title": event.get("title"),
        "locationName": event.get("locationName"),
        "region": event.get("region"),
        "regionCanonical": event.get(
            "regionCanonical"
        ),
        "venueId": event.get("venueId"),
        "venueName": event.get("venueName"),
        "venueIds": event.get("venueIds"),
        "venueNames": event.get("venueNames"),
        "venueCoverageStatus": event.get(
            "venueCoverageStatus"
        ),
        "venueValueCount": event.get(
            "venueValueCount"
        ),
        "matchedVenueValueCount": event.get(
            "matchedVenueValueCount"
        ),
        "unmatchedVenueValues": event.get(
            "unmatchedVenueValues"
        ),
        "contentType": event.get("contentType"),
        "contentTypes": event.get(
            "contentTypes"
        ),
        "eventFormat": event.get("eventFormat"),
        "editorialStatus": event.get(
            "editorialStatus"
        ),
        "editorialFlags": event.get(
            "editorialFlags"
        ),
    }


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

    events = source_payload.get("events")

    if not isinstance(events, list):
        raise ValueError(
            "Input JSON must contain an events list."
        )

    enriched_events: list[dict[str, Any]] = []
    venue_diagnostics: list[
        dict[str, Any]
    ] = []

    for event in events:
        if not isinstance(event, dict):
            continue

        enriched, diagnostic = (
            enrich_event_with_registry(
                event,
                venue_registry,
                legacy_registry,
            )
        )
        enriched_events.append(enriched)
        venue_diagnostics.append(diagnostic)

    total = len(enriched_events)
    venue_status_counts = Counter(
        diagnostic["status"]
        for diagnostic in venue_diagnostics
    )
    venue_method_counts = Counter(
        diagnostic["method"]
        for diagnostic in venue_diagnostics
    )
    venue_coverage_counts = Counter(
        diagnostic.get(
            "venueCoverageStatus",
            "none",
        )
        for diagnostic in venue_diagnostics
    )
    primary_type_counts = Counter(
        event.get("contentType") or "unknown"
        for event in enriched_events
    )
    all_type_counts = Counter(
        content_type
        for event in enriched_events
        for content_type in event.get(
            "contentTypes",
            [],
        )
    )
    event_format_counts = Counter(
        event.get("eventFormat") or "unknown"
        for event in enriched_events
    )
    editorial_status_counts = Counter(
        event.get("editorialStatus") or "unknown"
        for event in enriched_events
    )
    editorial_flag_counts = Counter(
        flag
        for event in enriched_events
        for flag in event.get(
            "editorialFlags",
            [],
        )
    )
    venue_counts = Counter(
        venue_name
        for event in enriched_events
        for venue_name in event.get(
            "venueNames",
            [],
        )
        if venue_name
    )

    resolved_event_count = sum(
        venue_status_counts.get(status, 0)
        for status in (
            "matched",
            "matched_multiple",
        )
    )
    multi_venue_event_count = venue_status_counts.get(
        "matched_multiple",
        0,
    )

    normalized_region_change_count = sum(
        1
        for event in enriched_events
        if event.get("regionCanonical")
        != event.get("region")
    )

    unmatched_location_counts = Counter(
        str(
            diagnostic.get("locationName")
            or "（空白場館）"
        )
        for diagnostic in venue_diagnostics
        if diagnostic["status"] == "unmatched"
    )
    unmatched_venue_value_counts = Counter(
        str(value or "（空白場館）")
        for diagnostic in venue_diagnostics
        for value in diagnostic.get(
            "unmatchedVenueValues",
            [],
        )
        if value
    )

    matched_events = [
        compact_event_sample(event)
        for event in enriched_events
        if event.get("venueIds")
    ]
    unmatched_events = [
        {
            **compact_event_sample(event),
            "venueDiagnostic": diagnostic,
        }
        for event, diagnostic in zip(
            enriched_events,
            venue_diagnostics,
        )
        if diagnostic["status"] == "unmatched"
    ]
    ambiguous_events = [
        diagnostic
        for diagnostic in venue_diagnostics
        if diagnostic["status"] == "ambiguous"
    ]
    multi_venue_events = [
        {
            **compact_event_sample(event),
            "venueDiagnostic": diagnostic,
        }
        for event, diagnostic in zip(
            enriched_events,
            venue_diagnostics,
        )
        if diagnostic["status"]
        == "matched_multiple"
    ]
    partial_venue_events = [
        {
            **compact_event_sample(event),
            "venueDiagnostic": diagnostic,
        }
        for event, diagnostic in zip(
            enriched_events,
            venue_diagnostics,
        )
        if diagnostic.get(
            "venueCoverageStatus"
        ) == "partial"
    ]
    review_events = [
        compact_event_sample(event)
        for event in enriched_events
        if event.get("editorialStatus")
        != "candidate"
    ]

    report = {
        "mode": "event-registry-dry-run",
        "published": False,
        "inputPath": str(input_path),
        "inputEventCount": len(events),
        "processedEventCount": total,
        "venueRegistryCount": len(
            venue_registry.get("venues", [])
        ),
        "legacyAliasesLoaded": (
            legacy_registry is not None
        ),
        "venueResolution": {
            "statusCounts": dict(
                sorted(
                    venue_status_counts.items()
                )
            ),
            "methodCounts": dict(
                sorted(
                    venue_method_counts.items()
                )
            ),
            "resolvedEventCount": (
                resolved_event_count
            ),
            "multiVenueEventCount": (
                multi_venue_event_count
            ),
            "matchedPercentage": percentage(
                resolved_event_count,
                total,
            ),
            "topMatchedVenues": dict(
                venue_counts.most_common(30)
            ),
            "topUnmatchedLocationNames": dict(
                unmatched_location_counts.most_common(
                    50
                )
            ),
            "venueCoverageStatusCounts": dict(
                sorted(
                    venue_coverage_counts.items()
                )
            ),
            "completeCoveragePercentage": percentage(
                venue_coverage_counts.get(
                    "complete",
                    0,
                ),
                total,
            ),
            "topUnmatchedVenueValues": dict(
                unmatched_venue_value_counts.most_common(
                    50
                )
            ),
        },
        "classification": {
            "primaryContentTypeCounts": dict(
                sorted(
                    primary_type_counts.items()
                )
            ),
            "allContentTypeCounts": dict(
                sorted(
                    all_type_counts.items()
                )
            ),
            "eventFormatCounts": dict(
                sorted(
                    event_format_counts.items()
                )
            ),
            "editorialStatusCounts": dict(
                sorted(
                    editorial_status_counts.items()
                )
            ),
            "editorialFlagCounts": dict(
                sorted(
                    editorial_flag_counts.items()
                )
            ),
        },
        "regionNormalization": {
            "changedCount": (
                normalized_region_change_count
            ),
            "changedPercentage": percentage(
                normalized_region_change_count,
                total,
            ),
        },
        "samples": {
            "matchedEvents": matched_events[
                : arguments.sample_limit
            ],
            "multiVenueEvents": multi_venue_events[
                : arguments.sample_limit
            ],
            "partialVenueEvents": partial_venue_events[
                : arguments.sample_limit
            ],
            "unmatchedEvents": unmatched_events[
                : arguments.sample_limit
            ],
            "ambiguousEvents": ambiguous_events[
                : arguments.sample_limit
            ],
            "editorialReviewEvents": review_events[
                : arguments.sample_limit
            ],
        },
    }

    if arguments.report_output:
        write_json(
            Path(arguments.report_output),
            report,
        )

    if arguments.preview_output:
        preview_payload = dict(source_payload)
        preview_payload["events"] = enriched_events
        preview_payload[
            "registryDryRun"
        ] = {
            "published": False,
            "venueRegistryCount": len(
                venue_registry.get("venues", [])
            ),
            "resolvedEventCount": (
                resolved_event_count
            ),
            "multiVenueEventCount": (
                multi_venue_event_count
            ),
        }
        write_json(
            Path(arguments.preview_output),
            preview_payload,
        )

    stdout_summary = {
        "mode": report["mode"],
        "published": False,
        "inputEventCount": len(events),
        "processedEventCount": total,
        "venueRegistryCount": report[
            "venueRegistryCount"
        ],
        "venueResolution": report[
            "venueResolution"
        ],
        "classification": report[
            "classification"
        ],
        "regionNormalization": report[
            "regionNormalization"
        ],
        "reportOutput": arguments.report_output,
        "previewOutput": arguments.preview_output,
    }

    print(
        json.dumps(
            stdout_summary,
            ensure_ascii=False,
            indent=2,
        )
    )

    return 0 if total == len(events) else 1


if __name__ == "__main__":
    sys.exit(main())
