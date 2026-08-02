#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urljoin

import requests

from exhibition_hub.social_discovery import build_queue


def read_json(path: str | Path, default: Any) -> Any:
    target = Path(path)
    if not target.exists():
        return default
    return json.loads(target.read_text(encoding="utf-8"))


def candidate_rows(path: str | Path) -> list[dict[str, Any]]:
    payload = read_json(path, {"candidates": []})
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return [
        item
        for item in payload.get("candidates") or []
        if isinstance(item, dict)
    ]


def ptt_candidates(config: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for board in config.get("boards", []):
        url = f"https://www.ptt.cc/bbs/{board}/index.html"
        try:
            response = requests.get(
                url,
                headers={
                    "User-Agent": "TaiwanExhibitionJournal-SocialDiscovery/1.0"
                },
                timeout=20,
            )
            response.raise_for_status()
            for href, title in re.findall(
                r'<a href="([^"]+)">([^<]+)</a>',
                response.text,
            ):
                if "/M." not in href:
                    continue
                rows.append(
                    {
                        "source": "ptt",
                        "postUrl": urljoin(url, href),
                        "shortExcerpt": title,
                        "publishedAt": "",
                        "keywords": [board],
                    }
                )
        except Exception:
            continue
    return rows[: int(config.get("maxCandidatesPerRun", 40))]


def dedupe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    seen = set()
    for item in rows:
        key = (
            str(item.get("source") or "").lower(),
            str(item.get("postUrl") or "").strip(),
        )
        if not key[1] or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", default="data/social_sources.json")
    parser.add_argument("--manual", default="data/social_manual_candidates.json")
    parser.add_argument("--events", default="data/exhibitions.curated.json")
    parser.add_argument(
        "--additional",
        action="append",
        default=[],
        help="Additional candidate JSON file; may be used more than once",
    )
    parser.add_argument(
        "--output",
        default="social-review-artifact/social_review_queue.json",
    )
    args = parser.parse_args()

    config = read_json(args.sources, {"sources": []})
    collected = candidate_rows(args.manual)
    for additional in args.additional:
        collected.extend(candidate_rows(additional))

    ptt = next(
        (
            item
            for item in config.get("sources") or []
            if item.get("id") == "ptt"
        ),
        {},
    )
    if ptt.get("enabled"):
        collected.extend(ptt_candidates(ptt))

    event_payload = read_json(args.events, {"events": []})
    events = (
        event_payload.get("events") or []
        if isinstance(event_payload, dict)
        else event_payload
    )
    queue = build_queue(dedupe(collected), events)
    payload = {
        "schemaVersion": 2,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "reviewRequired": True,
        "publishAllowed": False,
        "candidateCount": len(queue),
        "sourceCounts": {
            source: sum(1 for item in queue if item.get("source") == source)
            for source in sorted(
                {str(item.get("source") or "") for item in queue}
            )
            if source
        },
        "purposeCounts": {
            purpose: sum(
                1
                for item in queue
                if item.get("candidatePurpose") == purpose
            )
            for purpose in sorted(
                {
                    str(item.get("candidatePurpose") or "")
                    for item in queue
                }
            )
            if purpose
        },
        "candidates": queue,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "candidateCount": len(queue),
                "sourceCounts": payload["sourceCounts"],
                "publishAllowed": False,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
