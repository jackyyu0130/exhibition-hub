#!/usr/bin/env python3
"""Find high-confidence venue district mismatches from repeated event addresses."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
from typing import Any


def normalize(value: Any) -> str:
    return re.sub(r"[\s　()（）\-_/／・·,，.。:：;；|｜]+", "", str(value or "").replace("臺", "台").lower())


def address_district(value: Any) -> str:
    text = str(value or "").replace("臺", "台")
    city_match = re.search(r"(?:台北市|新北市|桃園市|台中市|台南市|高雄市|基隆市|新竹市|嘉義市)([^市縣]{1,5}區)", text)
    if city_match:
        return city_match.group(1)
    local_match = re.search(r"([^市縣]{1,5}(?:區|鄉|鎮|市))", text)
    return local_match.group(1) if local_match else ""


def event_names(event: dict[str, Any]) -> list[str]:
    values = [
        event.get("venueName"), event.get("parentVenueName"),
        event.get("venueGroup"), event.get("locationName"),
        *(event.get("venueNames") or []),
    ]
    return [str(value) for value in values if value]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    matrix = json.loads(args.matrix.read_text(encoding="utf-8"))
    payload = json.loads(args.events.read_text(encoding="utf-8"))
    events = payload.get("events") or []
    issues: list[dict[str, Any]] = []
    for venue in matrix.get("venues") or []:
        names = [venue.get("name"), *(venue.get("aliases") or [])]
        keys = [normalize(name) for name in names if name]
        districts: list[str] = []
        samples: list[dict[str, Any]] = []
        for event in events:
            candidate_keys = [normalize(name) for name in event_names(event)]
            matched = any(
                key and any(
                    key == candidate
                    or (len(key) >= 5 and key in candidate)
                    or (len(candidate) >= 5 and candidate in key)
                    for candidate in candidate_keys
                )
                for key in keys
            )
            if not matched:
                continue
            district = address_district(event.get("address"))
            if not district:
                continue
            districts.append(district)
            if len(samples) < 5:
                samples.append({"title": event.get("title"), "address": event.get("address")})
        counts = Counter(districts)
        if not counts:
            continue
        detected, count = counts.most_common(1)[0]
        current = str(venue.get("district") or "").replace("臺", "台")
        confidence = count / len(districts)
        if detected != current and count >= 2 and confidence >= 0.7:
            issues.append({
                "venueId": venue.get("id"),
                "venueName": venue.get("name"),
                "matrixDistrict": venue.get("district"),
                "detectedDistrict": detected,
                "matchedAddressCount": len(districts),
                "supportCount": count,
                "confidence": round(confidence, 4),
                "samples": samples,
            })
    report = {
        "schemaVersion": 1,
        "audit": "venue-name-address-district-consistency",
        "matrixVenueCount": len(matrix.get("venues") or []),
        "eventCount": len(events),
        "highConfidenceIssueCount": len(issues),
        "issues": issues,
        "note": "This is an internal consistency audit. It does not replace official manual verification for every venue.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
