#!/usr/bin/env python3
"""Detect whether enabled active source configuration changed between Git refs.

Planned/audit-only source additions must not trigger a production data refresh.
This script reads repository blobs only and performs no network access.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from typing import Any, Mapping

FINGERPRINT_KEYS = (
    "id", "status", "enabled", "parser", "officialUrl", "listingUrl",
    "listingUrls", "detailPathPatterns", "refreshHours", "minimumRecords",
)


def active_fingerprint(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows=[]
    for source in payload.get("sources") or []:
        if not isinstance(source, dict):
            continue
        if source.get("status") != "active" or source.get("enabled") is not True:
            continue
        rows.append({key: source.get(key) for key in FINGERPRINT_KEYS})
    return sorted(rows, key=lambda item: str(item.get("id") or ""))


def read_ref(ref: str, path: str) -> dict[str, Any]:
    result=subprocess.run(
        ["git","show",f"{ref}:{path}"], check=True, capture_output=True, text=True,
    )
    value=json.loads(result.stdout)
    if not isinstance(value,dict):
        raise ValueError("source registry root must be an object")
    return value


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--before-ref", required=True)
    parser.add_argument("--after-ref", required=True)
    parser.add_argument("--path", default="data/source_registry.json")
    args=parser.parse_args()
    try:
        before=read_ref(args.before_ref,args.path)
        after=read_ref(args.after_ref,args.path)
        changed=active_fingerprint(before) != active_fingerprint(after)
        reason="active-enabled-source-change" if changed else "planned-or-disabled-only"
    except Exception as exc:
        changed=True
        reason=f"conservative-fallback:{type(exc).__name__}"
    print(f"activation_changed={'true' if changed else 'false'}")
    print(f"reason={reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
