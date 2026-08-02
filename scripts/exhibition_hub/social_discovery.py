from __future__ import annotations

import hashlib
import re
from typing import Any
from urllib.parse import urlparse

SPACE = re.compile(r"\s+")
CJK_RUN = re.compile(r"[\u4e00-\u9fff]{2,}")
WORD = re.compile(r"[A-Za-z0-9]{2,}")


def clean(value: Any) -> str:
    return SPACE.sub(" ", str(value or "")).strip()


def valid_public_url(url: Any) -> bool:
    parsed = urlparse(str(url or ""))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def normalized_text(value: Any) -> str:
    return re.sub(
        r"[\s　()（）\[\]【】<>《》\-_/／・·,，.。:：;；|｜'\"!?！？]+",
        "",
        clean(value).replace("臺", "台").lower(),
    )


def tokens(text: Any) -> set[str]:
    source = clean(text).lower()
    result = set(WORD.findall(source))
    for run in CJK_RUN.findall(source):
        result.add(run)
        # Chinese text does not contain spaces. Character n-grams make partial
        # exhibit/venue names match without storing or publishing full text.
        for size in (2, 3, 4):
            if len(run) < size:
                continue
            result.update(run[index:index + size] for index in range(len(run) - size + 1))
    return {item for item in result if len(item) > 1}


def event_index(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for event in events:
        event_id = str(event.get("id") or event.get("uid") or "")
        title = clean(event.get("title"))
        venue = clean(
            event.get("venueName")
            or event.get("locationName")
            or event.get("venueGroup")
        )
        text = " ".join(
            clean(event.get(key))
            for key in (
                "title", "locationName", "venueName", "venueGroup",
                "unit", "description",
            )
        )
        rows.append(
            {
                "id": event_id,
                "title": title,
                "titleKey": normalized_text(title),
                "venue": venue,
                "venueKey": normalized_text(venue),
                "tokens": tokens(text),
            }
        )
    return rows


def match_candidate(
    candidate: dict[str, Any],
    events: list[dict[str, Any]],
) -> tuple[str, float, list[str], str]:
    excerpt = clean(candidate.get("shortExcerpt"))
    keyword_text = " ".join(str(item) for item in candidate.get("keywords") or [])
    candidate_text = f"{excerpt} {keyword_text}"
    candidate_key = normalized_text(candidate_text)
    candidate_tokens = tokens(candidate_text)
    best = ("", 0.0, [], "")

    for event in event_index(events):
        if not event["id"]:
            continue

        title_key = event["titleKey"]
        venue_key = event["venueKey"]
        overlap = candidate_tokens & event["tokens"]
        denominator = max(4, min(len(candidate_tokens or {"_"}), len(event["tokens"] or {"_"})))
        score = len(overlap) / denominator

        if title_key and len(title_key) >= 4 and title_key in candidate_key:
            score = max(score, 0.95)
        elif title_key and len(title_key) >= 6:
            title_parts = tokens(event["title"])
            title_overlap = len(candidate_tokens & title_parts) / max(3, len(title_parts))
            score = max(score, min(0.89, title_overlap))

        if venue_key and len(venue_key) >= 3 and venue_key in candidate_key:
            score += 0.08

        score = min(0.99, score)
        if score > best[1]:
            best = (
                event["id"],
                score,
                sorted(overlap, key=len, reverse=True)[:12],
                event["title"],
            )
    return best


def normalize_candidate(raw: dict[str, Any], source: str) -> dict[str, Any]:
    excerpt = clean(raw.get("shortExcerpt") or raw.get("title"))[:240]
    url = clean(raw.get("postUrl"))
    if not excerpt or not valid_public_url(url):
        raise ValueError("candidate requires public URL and excerpt")

    payload: dict[str, Any] = {
        "source": source,
        "postUrl": url,
        "authorDisplay": "公開來源（已匿名）",
        "publishedAt": clean(raw.get("publishedAt")),
        "shortExcerpt": excerpt,
        "engagementSnapshot": raw.get("engagementSnapshot") or {},
        "matchedEventId": "",
        "matchedEventTitle": "",
        "matchConfidence": 0.0,
        "matchSignals": [],
        "keywords": raw.get("keywords") or [],
        "reviewStatus": "pending",
        "candidatePurpose": clean(raw.get("candidatePurpose")) or "social_discussion",
        "discoveryQuery": clean(raw.get("discoveryQuery")),
        "sourceAccountHash": clean(raw.get("sourceAccountHash")),
        "verifiedAccount": bool(raw.get("verifiedAccount")),
        "topicTag": clean(raw.get("topicTag")),
        "crossPlatformCount": 0,
        "siteViews": 0,
        "siteFavorites": 0,
        "editorWeight": float(raw.get("editorWeight") or 0),
        "popularityScore": 0.0,
    }
    payload["candidateId"] = hashlib.sha256(
        f"{source}|{url}".encode("utf-8")
    ).hexdigest()[:24]
    return payload


def score(candidate: dict[str, Any]) -> float:
    confidence = float(candidate.get("matchConfidence") or 0)
    engagement = candidate.get("engagementSnapshot") or {}
    interaction = sum(
        float(engagement.get(key) or 0)
        for key in ("likes", "replies", "shares", "upvotes")
    )
    return round(
        30 * confidence
        + 20 * min(1, interaction / 1000)
        + 15 * min(1, float(candidate.get("crossPlatformCount") or 0) / 3)
        + 10 * min(
            1,
            (
                float(candidate.get("siteViews") or 0)
                + 3 * float(candidate.get("siteFavorites") or 0)
            )
            / 1000,
        )
        + 5 * min(1, float(candidate.get("editorWeight") or 0)),
        3,
    )


def build_queue(
    candidates: list[dict[str, Any]],
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()

    for raw in candidates:
        source = clean(raw.get("source")).lower()
        if source not in {"threads", "ptt", "dcard", "manual", "instagram", "facebook"}:
            continue
        try:
            candidate = normalize_candidate(raw, source)
        except ValueError:
            continue
        if candidate["candidateId"] in seen:
            continue
        seen.add(candidate["candidateId"])

        event_id, confidence, signals, event_title = match_candidate(candidate, events)
        candidate.update(
            matchedEventId=event_id,
            matchedEventTitle=event_title,
            matchConfidence=round(confidence, 3),
            matchSignals=signals,
        )
        if source == "threads" and confidence < 0.68:
            candidate["candidatePurpose"] = "new_event_discovery"
        elif event_id and confidence >= 0.68:
            candidate["candidatePurpose"] = "social_discussion"
        candidate["popularityScore"] = score(candidate)
        rows.append(candidate)

    return sorted(
        rows,
        key=lambda item: (
            item.get("candidatePurpose") != "social_discussion",
            -float(item.get("matchConfidence") or 0),
            str(item.get("publishedAt") or ""),
        ),
    )
