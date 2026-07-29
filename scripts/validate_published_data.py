#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
from typing import Any, Mapping

from exhibition_hub.image_quality import (
    is_facebook_url,
    suspicious_image_reason,
)

LEGACY_CATEGORIES = {
    "歷史文化",
    "自然科學",
    "快閃",
    "快閃活動",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate dynamic published exhibition data "
            "without relying on a fixed event count."
        )
    )
    parser.add_argument(
        "--input",
        required=True,
    )
    parser.add_argument(
        "--minimum-events",
        type=int,
        default=500,
    )
    parser.add_argument(
        "--require-published",
        action="store_true",
    )
    parser.add_argument(
        "--source-id",
        default="",
    )
    parser.add_argument(
        "--report-output",
        required=True,
    )
    return parser.parse_args()


def load_json(path: str) -> Any:
    return json.loads(
        Path(path).read_text(encoding="utf-8")
    )


def write_json(path: str, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def event_categories(
    event: Mapping[str, Any],
) -> list[str]:
    values = event.get("categories")
    if isinstance(values, list):
        result = [
            str(value).strip()
            for value in values
            if str(value).strip()
        ]
    else:
        result = []

    fallback = str(
        event.get("category") or ""
    ).strip()
    if not result and fallback:
        result = [fallback]
    return list(dict.fromkeys(result))


def is_valid_iso_date(value: Any) -> bool:
    text = str(value or "").strip()
    if not text:
        return True
    try:
        date.fromisoformat(text)
        return True
    except ValueError:
        return False


def evaluate(
    payload: Mapping[str, Any],
    *,
    minimum_events: int,
    require_published: bool,
    source_id: str,
) -> dict[str, Any]:
    events = [
        item
        for item in payload.get("events") or []
        if isinstance(item, dict)
    ]
    stats = payload.get("stats") or {}
    event_ids = [
        str(event.get("id") or "").strip()
        for event in events
    ]

    blank_titles = [
        str(event.get("id") or "")
        for event in events
        if not str(event.get("title") or "").strip()
    ]
    duplicate_ids = sorted(
        event_id
        for event_id, count in Counter(
            event_ids
        ).items()
        if event_id and count > 1
    )
    excluded_ids = [
        str(event.get("id") or "")
        for event in events
        if event.get("editorialStatus")
        == "exclude_review"
    ]

    invalid_date_ids: list[str] = []
    reversed_date_ids: list[str] = []
    for event in events:
        event_id = str(event.get("id") or "")
        start = str(
            event.get("startDate") or ""
        ).strip()
        end = str(
            event.get("endDate") or ""
        ).strip()
        if not is_valid_iso_date(start) or not is_valid_iso_date(end):
            invalid_date_ids.append(event_id)
        elif start and end and start > end:
            reversed_date_ids.append(event_id)

    category_counts = Counter(
        category
        for event in events
        for category in event_categories(
            event
        )
    )
    legacy_category_ids = [
        str(event.get("id") or "")
        for event in events
        if LEGACY_CATEGORIES.intersection(
            event_categories(event)
        )
    ]

    image_count = sum(
        bool(
            str(
                event.get("image")
                or ""
            ).strip()
        )
        for event in events
    )
    multi_image_count = sum(
        isinstance(
            event.get("images"),
            list,
        )
        and len(
            event.get("images")
            or []
        )
        > 1
        for event in events
    )
    coordinate_count = sum(
        event.get("latitude") is not None
        and event.get("longitude") is not None
        for event in events
    )
    suspicious_images = []
    facebook_references = []
    for event in events:
        event_id = str(event.get("id") or "")
        for url in [
            *(event.get("images") or []),
            event.get("image"),
        ]:
            if not str(url or "").strip():
                continue
            reason = suspicious_image_reason(url)
            if reason:
                suspicious_images.append({
                    "eventId": event_id,
                    "url": str(url),
                    "reason": reason,
                })
        for url in [
            event.get("sourceUrl"),
            event.get("officialUrl"),
            event.get("ticketUrl"),
            *(event.get("sourceUrls") or []),
            *(event.get("externalUrls") or []),
        ]:
            if is_facebook_url(url):
                facebook_references.append({
                    "eventId": event_id,
                    "url": str(url),
                })

    source_reference_counts: Counter[
        tuple[str, str]
    ] = Counter()
    source_record_event_count = 0
    for event in events:
        for record in event.get(
            "sourceRecords"
        ) or []:
            if not isinstance(record, dict):
                continue
            record_source_id = str(
                record.get("sourceId") or ""
            ).strip()
            source_event_id = str(
                record.get("sourceEventId")
                or ""
            ).strip()
            if not (
                record_source_id
                and source_event_id
            ):
                continue
            source_reference_counts[
                (
                    record_source_id,
                    source_event_id,
                )
            ] += 1
            if (
                source_id
                and record_source_id
                == source_id
            ):
                source_record_event_count += 1

    duplicate_source_references = [
        {
            "sourceId": key[0],
            "sourceEventId": key[1],
            "count": count,
        }
        for key, count in sorted(
            source_reference_counts.items()
        )
        if count > 1
    ]

    official_build = (
        payload.get(
            "officialSourceBuild"
        )
        or {}
    )

    stored_category_counts = dict(
        stats.get("categoryCounts") or {}
    )
    category_counts_match = (
        stored_category_counts
        == dict(category_counts)
    )
    if not require_published:
        category_counts_match = all(
            int(
                stored_category_counts.get(
                    category,
                    -1,
                )
            )
            == count
            for category, count
            in category_counts.items()
        ) and all(
            category in category_counts
            or int(count) == 0
            for category, count
            in stored_category_counts.items()
        )

    stored_image_count = int(
        stats.get("imageCount", -1)
    )
    stored_multi_image_count = int(
        stats.get("multiImageCount", -1)
    )
    image_count_matches = (
        stored_image_count
        == image_count
    )
    multi_image_count_matches = (
        stored_multi_image_count
        == multi_image_count
    )
    if not require_published:
        image_count_matches = (
            abs(
                stored_image_count
                - image_count
            )
            <= 1
        )
        multi_image_count_matches = (
            abs(
                stored_multi_image_count
                - multi_image_count
            )
            <= 1
        )

    gates = {
        "payloadIsObject": isinstance(
            payload,
            Mapping,
        ),
        "eventCountAboveMinimum": (
            len(events)
            >= max(
                1,
                minimum_events,
            )
        ),
        "eventIdsNonEmpty": (
            bool(event_ids)
            and "" not in event_ids
        ),
        "eventIdsUnique": (
            not duplicate_ids
        ),
        "titlesNonEmpty": (
            not blank_titles
        ),
        "datesValid": (
            not invalid_date_ids
        ),
        "dateRangesOrdered": (
            not reversed_date_ids
        ),
        "excludeReviewAbsent": (
            not excluded_ids
        ),
        "legacyCategoriesAbsent": (
            not legacy_category_ids
        ),
        "statsEventCountMatches": (
            int(
                stats.get(
                    "eventCount",
                    -1,
                )
            )
            == len(events)
        ),
        "statsImageCountMatches": (
            image_count_matches
        ),
        "statsMultiImageCountMatches": (
            multi_image_count_matches
        ),
        "statsCoordinateCountMatches": (
            int(
                stats.get(
                    "coordinateCount",
                    -1,
                )
            )
            == coordinate_count
        ),
        "statsCategoryCountsMatch": (
            category_counts_match
        ),
        "sourceReferencesUnique": (
            not duplicate_source_references
        ),
        "suspiciousImagesAbsent": (
            not suspicious_images
        ),
        "facebookReferencesAbsent": (
            not facebook_references
        ),
    }

    if require_published:
        gates[
            "officialSourceBuildPublished"
        ] = (
            official_build.get(
                "published"
            )
            is True
        )
        gates[
            "officialSourceBuildSourceMatches"
        ] = (
            not source_id
            or str(
                official_build.get(
                    "sourceId"
                )
                or ""
            )
            == source_id
        )
        gates[
            "publishedSourceRecordsPresent"
        ] = (
            not source_id
            or source_record_event_count
            > 0
        )

    failed_gates = [
        gate_id
        for gate_id, passed
        in gates.items()
        if not passed
    ]

    return {
        "mode": (
            "dynamic-published-data-validation"
        ),
        "passed": not failed_gates,
        "eventCount": len(events),
        "minimumEvents": max(
            1,
            minimum_events,
        ),
        "requirePublished": (
            require_published
        ),
        "sourceId": source_id,
        "officialSourceBuild": (
            official_build
        ),
        "metrics": {
            "imageCount": image_count,
            "multiImageCount": (
                multi_image_count
            ),
            "coordinateCount": (
                coordinate_count
            ),
            "categoryCounts": dict(
                category_counts
            ),
            "sourceRecordEventCount": (
                source_record_event_count
            ),
        },
        "gates": gates,
        "failedGateIds": failed_gates,
        "details": {
            "duplicateIds": duplicate_ids,
            "blankTitleIds": blank_titles,
            "invalidDateIds": (
                invalid_date_ids
            ),
            "reversedDateIds": (
                reversed_date_ids
            ),
            "excludeReviewIds": (
                excluded_ids
            ),
            "legacyCategoryIds": (
                legacy_category_ids
            ),
            "duplicateSourceReferences": (
                duplicate_source_references
            ),
            "suspiciousImages": suspicious_images,
            "facebookReferences": facebook_references,
        },
    }


def main() -> int:
    args = parse_args()
    payload = load_json(args.input)
    if not isinstance(payload, dict):
        raise ValueError(
            "Published data root must be an object."
        )

    report = evaluate(
        payload,
        minimum_events=max(
            1,
            args.minimum_events,
        ),
        require_published=(
            args.require_published
        ),
        source_id=args.source_id.strip(),
    )
    write_json(
        args.report_output,
        report,
    )
    print(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
