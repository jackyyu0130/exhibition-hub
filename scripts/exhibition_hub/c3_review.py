from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse

SPACE_RE = re.compile(r"\s+")
DATE_RE = re.compile(r"^20\d{2}-\d{2}-\d{2}$")
SOCIAL_HOSTS = {
    "instagram.com", "www.instagram.com", "facebook.com", "www.facebook.com",
    "threads.net", "www.threads.net", "dcard.tw", "www.dcard.tw", "ptt.cc", "www.ptt.cc",
}


def clean(value: Any) -> str:
    return SPACE_RE.sub(" ", str(value or "")).strip()


def normalize_title(value: Any) -> str:
    text = clean(value).lower().replace("臺", "台")
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", text)


def valid_url(value: Any) -> bool:
    parsed = urlparse(clean(value))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def valid_iso_date(value: Any) -> bool:
    text = clean(value)
    if not DATE_RE.match(text):
        return False
    try:
        date.fromisoformat(text)
        return True
    except ValueError:
        return False


def source_host(value: Any) -> str:
    return (urlparse(clean(value)).hostname or "").lower()


def is_social_url(value: Any) -> bool:
    host = source_host(value)
    return host in SOCIAL_HOSTS or any(host.endswith("." + item) for item in SOCIAL_HOSTS)


def load_json(path: str | Path, default: Any = None) -> Any:
    target = Path(path)
    if not target.is_file():
        return deepcopy(default)
    return json.loads(target.read_text(encoding="utf-8"))


def event_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        return [item for item in payload.get("events", []) if isinstance(item, dict)]
    return []


def catalog_index(payload: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        clean(item.get("id")): item
        for item in payload.get("sources", [])
        if isinstance(item, dict) and clean(item.get("id"))
    }


def existing_event_match(candidate: Mapping[str, Any], events: Iterable[Mapping[str, Any]]) -> dict[str, Any] | None:
    title_key = normalize_title(candidate.get("title"))
    source_url = clean(candidate.get("sourceUrl") or candidate.get("detailUrl"))
    best: tuple[float, dict[str, Any]] | None = None
    for event in events:
        event_id = clean(event.get("id") or event.get("uid"))
        if not event_id:
            continue
        urls = {
            clean(event.get("sourceUrl")), clean(event.get("officialUrl")), clean(event.get("ticketUrl")),
            *[clean(value) for value in event.get("sourceUrls", []) if clean(value)],
        }
        if source_url and source_url in urls:
            return {"eventId": event_id, "score": 1.0, "reason": "source_url_exact"}
        existing_title = normalize_title(event.get("title"))
        if not title_key or not existing_title:
            continue
        title_score = SequenceMatcher(None, title_key, existing_title).ratio()
        date_score = 0.0
        if clean(candidate.get("startDate")) and clean(candidate.get("startDate")) == clean(event.get("startDate")):
            date_score += 0.14
        if clean(candidate.get("endDate")) and clean(candidate.get("endDate")) == clean(event.get("endDate")):
            date_score += 0.06
        venue_text = normalize_title(candidate.get("venueName"))
        existing_venue = normalize_title(event.get("venueGroup") or event.get("locationName") or event.get("venueDetail"))
        venue_score = 0.10 if venue_text and existing_venue and (venue_text in existing_venue or existing_venue in venue_text) else 0.0
        score = min(0.99, title_score * 0.8 + date_score + venue_score)
        if best is None or score > best[0]:
            best = (score, {"eventId": event_id, "score": round(score, 4), "reason": "title_date_venue"})
    return best[1] if best and best[0] >= 0.72 else None


def source_kind(source: Mapping[str, Any], candidate: Mapping[str, Any]) -> str:
    category = clean(source.get("category"))
    if category == "ticketing":
        return "ticketing"
    if category == "organizer":
        return "organizer_official"
    if category == "livehouse":
        return "venue_official"
    if category == "festival":
        return "organizer_official"
    if candidate.get("candidateOrigin") == "c2":
        return "venue_official"
    return "manual"


def quality(candidate: Mapping[str, Any], source: Mapping[str, Any], policy: Mapping[str, Any]) -> tuple[float, list[str], list[str]]:
    score = 0.0
    flags: list[str] = []
    blockers: list[str] = []
    title = clean(candidate.get("title"))
    start = clean(candidate.get("startDate"))
    end = clean(candidate.get("endDate") or start)
    venue = clean(candidate.get("venueName"))
    region = clean(candidate.get("region"))
    url = clean(candidate.get("sourceUrl") or candidate.get("detailUrl"))
    kind = source_kind(source, candidate)

    if len(title) >= int(policy.get("thresholds", {}).get("minimumTitleLength", 3)):
        score += 0.18
    else:
        blockers.append("missing_or_short_title")
    if valid_iso_date(start) and valid_iso_date(end) and start <= end:
        score += 0.22
    else:
        blockers.append("invalid_or_missing_dates")
    if venue:
        score += 0.12
    else:
        flags.append("missing_venue")
    if region:
        score += 0.08
    else:
        flags.append("missing_region")
    if valid_url(url):
        score += 0.12
    else:
        blockers.append("invalid_source_url")
    if clean(candidate.get("imageUrl") or candidate.get("image")):
        score += 0.05
    else:
        flags.append("missing_image")
    if clean(candidate.get("organizer") or candidate.get("unit")):
        score += 0.05
    if clean(candidate.get("price")):
        score += 0.04
    if kind in {"ticketing", "venue_official", "government"}:
        score += 0.14
    elif kind == "organizer_official":
        score += 0.10
    else:
        score += 0.04

    if is_social_url(url):
        flags.append("social_only_evidence")
        score = min(score, 0.79)
    if source.get("verificationStatus") not in {"verified", "runtime_verified"}:
        flags.append("source_runtime_verification_required")
        score = min(score, 0.84)
    if source.get("discoveryMode") in {"name_match_only", "official_social_manual", "festival_official_page_or_manual"}:
        flags.append("manual_review_required")
        score = min(score, 0.79)
    return round(min(1.0, score), 3), flags, blockers


def normalize_candidate(raw: Mapping[str, Any], source: Mapping[str, Any], events: list[dict[str, Any]], policy: Mapping[str, Any]) -> dict[str, Any]:
    source_id = clean(raw.get("sourceId") or raw.get("sourceCatalogId") or source.get("id") or "manual")
    url = clean(raw.get("sourceUrl") or raw.get("detailUrl") or raw.get("postUrl") or raw.get("listingUrl"))
    title = clean(raw.get("title") or raw.get("shortExcerpt"))[:220]
    start = clean(raw.get("startDate"))
    end = clean(raw.get("endDate") or start)
    candidate_id = clean(raw.get("candidateId")) or hashlib.sha256(
        f"{source_id}|{url}|{title}|{start}|{end}".encode("utf-8")
    ).hexdigest()[:24]
    row = {
        "candidateId": candidate_id,
        "sourceId": source_id,
        "sourceName": clean(source.get("name") or source_id),
        "sourceKind": source_kind(source, raw),
        "candidateOrigin": clean(raw.get("candidateOrigin") or "manual"),
        "title": title,
        "startDate": start,
        "endDate": end,
        "venueName": clean(raw.get("venueName") or raw.get("locationName")),
        "region": clean(raw.get("region")),
        "address": clean(raw.get("address")),
        "price": clean(raw.get("price")),
        "organizer": clean(raw.get("organizer") or raw.get("unit")),
        "category": clean(raw.get("category") or "其他"),
        "sourceUrl": url,
        "imageUrl": clean(raw.get("imageUrl") or raw.get("image")),
        "shortDescription": clean(raw.get("shortDescription") or raw.get("description") or raw.get("shortExcerpt"))[:500],
        "reviewStatus": "pending",
        "publishEligible": False,
        "recommendedAction": "hold",
        "qualityScore": 0.0,
        "qualityFlags": [],
        "blockingIssues": [],
        "existingMatch": None,
    }
    row["existingMatch"] = existing_event_match(row, events)
    score, flags, blockers = quality(row, source, policy)
    row["qualityScore"] = score
    row["qualityFlags"] = flags
    row["blockingIssues"] = blockers
    auto_threshold = float(policy.get("thresholds", {}).get("automaticEligibility", 0.86))
    manual_threshold = float(policy.get("thresholds", {}).get("manualEligibility", 0.72))
    social_only = "social_only_evidence" in flags
    if not blockers and score >= auto_threshold and not social_only:
        row["publishEligible"] = True
        row["recommendedAction"] = "update_existing" if row["existingMatch"] else "new_event"
    elif not blockers and score >= manual_threshold:
        row["recommendedAction"] = "manual_review"
    elif blockers:
        row["recommendedAction"] = "reject_or_complete"
    return row


def build_queue(raw_candidates: Iterable[Mapping[str, Any]], catalog: Mapping[str, Any], events: list[dict[str, Any]], policy: Mapping[str, Any]) -> list[dict[str, Any]]:
    index = catalog_index(catalog)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in raw_candidates:
        source_id = clean(raw.get("sourceId") or raw.get("sourceCatalogId"))
        source = index.get(source_id, {
            "id": source_id or "manual", "name": source_id or "人工候選", "category": "manual",
            "discoveryMode": "manual", "verificationStatus": "pending_runtime_probe",
        })
        row = normalize_candidate(raw, source, events, policy)
        if row["candidateId"] in seen:
            continue
        seen.add(row["candidateId"])
        rows.append(row)
    return sorted(rows, key=lambda item: (-float(item.get("qualityScore") or 0), item.get("title") or ""))


def apply_decisions(queue: Iterable[Mapping[str, Any]], decisions_payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    decision_index = {
        clean(item.get("candidateId")): item
        for item in decisions_payload.get("decisions", [])
        if isinstance(item, dict) and clean(item.get("candidateId"))
    }
    rows: list[dict[str, Any]] = []
    for candidate in queue:
        row = deepcopy(dict(candidate))
        decision = decision_index.get(clean(row.get("candidateId")))
        if decision:
            row["reviewStatus"] = clean(decision.get("decision") or "pending")
            row["reviewNotes"] = clean(decision.get("notes"))[:500]
            row["evidenceUrl"] = clean(decision.get("evidenceUrl"))
            if row["reviewStatus"] == "approved" and not row.get("blockingIssues"):
                row["publishEligible"] = bool(row.get("publishEligible") or float(row.get("qualityScore") or 0) >= 0.72)
        rows.append(row)
    return rows
