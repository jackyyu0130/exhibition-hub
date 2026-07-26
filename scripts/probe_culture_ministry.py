"""Safely inspect one live Culture Ministry feed.

This command downloads data for inspection only. It does not modify website
JSON files, commit changes, or deploy GitHub Pages.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from exhibition_hub.collectors.base import CollectorContext
from exhibition_hub.collectors.culture_ministry import (
    CultureMinistryCollector,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Download one Culture Ministry category "
            "without publishing any website data."
        )
    )
    parser.add_argument(
        "--category",
        default="6",
        help="Culture Ministry category ID. Default: 6 (展覽).",
    )
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=5,
        help="Maximum number of sample records to display.",
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


    def summarize_show_info(value: Any) -> dict[str, Any]:
    """Describe the session structure without printing every record."""

    if isinstance(value, list):
        first_item = next(
            (
                item
                for item in value
                if isinstance(item, dict)
            ),
            None,
        )

        return {
            "type": "list",
            "count": len(value),
            "firstItemKeys": (
                sorted(
                    str(key)
                    for key in first_item
                )
                if first_item
                else []
            ),
        }

    if isinstance(value, dict):
        return {
            "type": "dict",
            "count": 1,
            "firstItemKeys": sorted(
                str(key)
                for key in value
            ),
        }

    return {
        "type": type(value).__name__,
        "count": 0,
        "firstItemKeys": [],
    }


def build_sample(
    event: dict[str, Any],
) -> dict[str, Any]:
    """Return fields useful for designing the normalizer."""

    return {
        "topLevelKeys": sorted(
            str(key)
            for key in event
        ),
        "title": str(
            event.get("title") or ""
        ),
        "startDate": str(
            event.get("startDate") or ""
        ),
        "endDate": str(
            event.get("endDate") or ""
        ),
        "uid": str(
            event.get("UID")
            or event.get("uid")
            or event.get("id")
            or ""
        ),
        "category": str(
            event.get("category") or ""
        ),
        "showInfoSummary": summarize_show_info(
            event.get("showInfo")
        ),
        "imageUrl": str(
            event.get("imageUrl")
            or event.get("image")
            or ""
        )[:300],
        "sourceUrl": str(
            event.get("sourceWebPromote")
            or event.get("sourceUrl")
            or ""
        )[:300],
        "feedCategory": str(
            event.get("_feedCategory") or ""
        ),
        "collectorSource": str(
            event.get("_collectorSource") or ""
        ),
    }
    """Return only non-sensitive fields useful for API inspection."""

    return {
        "title": str(event.get("title") or ""),
        "startDate": str(event.get("startDate") or ""),
        "endDate": str(event.get("endDate") or ""),
        "location": str(
            event.get("showInfo")
            or event.get("location")
            or event.get("locationName")
            or ""
        )[:300],
        "feedCategory": str(
            event.get("_feedCategory") or ""
        ),
        "collectorSource": str(
            event.get("_collectorSource") or ""
        ),
    }


def main() -> int:
    arguments = parse_arguments()

    context = CollectorContext.create(
        timeout_seconds=arguments.timeout,
        settings={
            "environment": "live-probe",
            "publish": False,
        },
    )

    collector = CultureMinistryCollector(
        categories=[arguments.category]
    )
    result = collector.collect(context)

    report = {
        "mode": "live-probe",
        "published": False,
        "sourceId": result.source_id,
        "sourceName": result.source_name,
        "category": arguments.category,
        "succeeded": result.succeeded,
        "eventCount": result.event_count,
        "warningCount": len(result.warnings),
        "errorCount": len(result.errors),
        "warnings": result.warnings,
        "errors": result.errors,
        "samples": [
            build_sample(event)
            for event in result.events[
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

    return 0 if result.succeeded else 1


if __name__ == "__main__":
    sys.exit(main())
