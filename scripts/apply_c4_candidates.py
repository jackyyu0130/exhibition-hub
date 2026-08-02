#!/usr/bin/env python3
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping


def read(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path: str | Path, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def norm(value: Any) -> str:
    text = str(value or "").replace("臺", "台").lower()
    return re.sub(r"[\s　()（）\[\]【】<>《》\-_/／・·,，.。:：;；|｜'\"]+", "", text)


def existing_keys(events: list[Mapping[str, Any]]) -> set[tuple[str, str, str]]:
    return {
        (norm(item.get("title")), str(item.get("startDate") or ""), norm(item.get("venueName") or item.get("locationName")))
        for item in events
        if isinstance(item, Mapping)
    }


def candidate_to_event(item: Mapping[str, Any], now: str) -> dict[str, Any]:
    key = f"{item.get('sourceId')}|{item.get('sourceUrl')}|{item.get('title')}|{item.get('startDate')}"
    event_id = "c4-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:20]
    image = str(item.get("imageUrl") or "")
    venue = str(item.get("venueName") or "")
    region = str(item.get("region") or "")
    category = str(item.get("category") or "其他")
    content = str(item.get("contentType") or "event")
    return {
        "id": event_id,
        "title": str(item.get("title") or "").strip(),
        "description": str(item.get("description") or "").strip()[:1200],
        "sourceUrl": str(item.get("sourceUrl") or ""),
        "sourceUrlVerified": True,
        "image": image,
        "images": [image],
        "categories": [category],
        "category": category,
        "contentType": content,
        "contentTypes": [content],
        "eventFormat": "physical",
        "editorialStatus": "published",
        "editorialFlags": ["c4_official_source_auto_verified", "c4_unique_venue_match"],
        "startDate": str(item.get("startDate") or ""),
        "endDate": str(item.get("endDate") or item.get("startDate") or ""),
        "locationName": venue,
        "location": venue,
        "venueGroup": venue,
        "venueName": venue,
        "venueNames": [venue],
        "venueCoverageStatus": "matched",
        "region": region,
        "regionCanonical": region,
        "price": "依官方公告",
        "unit": str(item.get("sourceName") or ""),
        "source": "c4_official_monitor",
        "firstSeenAt": now,
        "lastSeenAt": now,
        "c4SourceId": str(item.get("sourceId") or ""),
        "c4EndpointId": str(item.get("endpointId") or ""),
        "c4Confidence": float(item.get("confidence") or 0),
        "c4Evidence": list(item.get("evidence") or []),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--base", required=True)
    p.add_argument("--candidates", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--report", required=True)
    p.add_argument("--maximum-additions", type=int, default=40)
    args = p.parse_args()

    base = read(args.base)
    result = deepcopy(base)
    events = [item for item in result.get("events") or [] if isinstance(item, dict)]
    keys = existing_keys(events)
    now = datetime.now(timezone.utc).isoformat()
    added: list[str] = []
    skipped: list[dict[str, str]] = []

    payload = read(args.candidates)
    for item in payload.get("candidates") or []:
        if not isinstance(item, Mapping) or not item.get("autoPublishEligible"):
            continue
        key = (norm(item.get("title")), str(item.get("startDate") or ""), norm(item.get("venueName")))
        if key in keys:
            skipped.append({"candidateId": str(item.get("candidateId") or ""), "reason": "duplicate_after_merge"})
            continue
        if len(added) >= args.maximum_additions:
            skipped.append({"candidateId": str(item.get("candidateId") or ""), "reason": "maximum_additions_reached"})
            continue
        event = candidate_to_event(item, now)
        events.append(event)
        keys.add(key)
        added.append(event["id"])

    result["events"] = events
    if added:
        metadata = dict(result.get("metadata") or {})
        metadata["c4MonitorAppliedAt"] = now
        metadata["c4AddedCount"] = len(added)
        result["metadata"] = metadata
    report = {
        "schemaVersion": 1,
        "generatedAt": now,
        "baseEventCount": len(base.get("events") or []),
        "finalEventCount": len(events),
        "addedCount": len(added),
        "addedIds": added,
        "skipped": skipped,
        "published": False,
        "qualityGates": {
            "baseEventsPreserved": len(events) >= len(base.get("events") or []),
            "maximumAdditionsRespected": len(added) <= args.maximum_additions,
            "onlyEligibleCandidatesApplied": True,
            "directSocialCandidatesApplied": False,
        },
    }
    write(args.output, result)
    write(args.report, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
