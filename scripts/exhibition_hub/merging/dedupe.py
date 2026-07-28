from __future__ import annotations

from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from enum import Enum
from typing import Any, Iterable

from .normalization import (
    date_relation,
    event_organizers,
    event_venue_values,
    normalize_name,
    normalize_title,
    normalize_url,
)


class MatchDecision(str, Enum):
    AUTO_MERGE = "auto_merge"
    REVIEW = "needs_review"
    NEW = "new_event"


@dataclass(frozen=True)
class MatchResult:
    decision: MatchDecision
    score: float
    existing_id: str
    existing_title: str
    title_similarity: float
    date_kind: str
    date_score: float
    venue_score: float
    organizer_score: float
    url_exact: bool
    source_reference_exact: bool
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["decision"] = self.decision.value
        value["reasons"] = list(self.reasons)
        return value


def _title_similarity(left: dict[str, Any], right: dict[str, Any]) -> float:
    left_title = normalize_title(left.get("title"))
    right_title = normalize_title(right.get("title"))
    if not left_title or not right_title:
        return 0.0
    return SequenceMatcher(
        None,
        left_title,
        right_title,
    ).ratio()


def _venue_score(left: dict[str, Any], right: dict[str, Any]) -> float:
    left_ids = set(left.get("venueIds") or [])
    right_ids = set(right.get("venueIds") or [])
    if left_ids and right_ids and left_ids.intersection(right_ids):
        return 1.0

    left_values = {
        normalize_name(value)
        for value in event_venue_values(left)
        if normalize_name(value)
    }
    right_values = {
        normalize_name(value)
        for value in event_venue_values(right)
        if normalize_name(value)
    }
    if left_values.intersection(right_values):
        return 0.92

    for left_value in left_values:
        for right_value in right_values:
            if (
                len(left_value) >= 5
                and len(right_value) >= 5
                and (
                    left_value in right_value
                    or right_value in left_value
                )
            ):
                return 0.82

    if (
        left.get("regionCanonical")
        and left.get("regionCanonical")
        == right.get("regionCanonical")
    ):
        return 0.28
    return 0.0


def _organizer_score(
    left: dict[str, Any],
    right: dict[str, Any],
) -> float:
    left_values = {
        normalize_name(value)
        for value in event_organizers(left)
        if normalize_name(value)
    }
    right_values = {
        normalize_name(value)
        for value in event_organizers(right)
        if normalize_name(value)
    }
    return 1.0 if left_values.intersection(right_values) else 0.0


def _source_reference_exact(
    source_event: dict[str, Any],
    existing: dict[str, Any],
) -> bool:
    source_id = str(source_event.get("collectorSourceId") or "")
    event_id = str(source_event.get("sourceEventId") or "")
    for item in existing.get("sourceRecords") or []:
        if not isinstance(item, dict):
            continue
        if (
            str(item.get("sourceId") or "") == source_id
            and str(item.get("sourceEventId") or "") == event_id
        ):
            return True
    return False


def score_match(
    source_event: dict[str, Any],
    existing: dict[str, Any],
) -> MatchResult:
    title_similarity = _title_similarity(source_event, existing)
    dates = date_relation(
        source_event.get("startDate"),
        source_event.get("endDate"),
        existing.get("startDate"),
        existing.get("endDate"),
    )
    venue_score = _venue_score(source_event, existing)
    organizer_score = _organizer_score(source_event, existing)

    source_url = normalize_url(
        source_event.get("officialUrl")
        or source_event.get("sourceUrl")
    )
    existing_urls = {
        normalize_url(existing.get("officialUrl")),
        normalize_url(existing.get("sourceUrl")),
        *{
            normalize_url(value)
            for value in existing.get("sourceUrls") or []
        },
    }
    existing_urls.discard("")
    url_exact = bool(source_url and source_url in existing_urls)
    source_reference_exact = _source_reference_exact(
        source_event,
        existing,
    )

    score = (
        title_similarity * 0.56
        + float(dates["score"]) * 0.22
        + venue_score * 0.14
        + organizer_score * 0.05
    )
    if url_exact:
        score += 0.35
    if source_reference_exact:
        score += 0.5
    score = min(1.0, round(score, 4))

    reasons: list[str] = []
    if url_exact:
        reasons.append("official_url_exact")
    if source_reference_exact:
        reasons.append("source_reference_exact")
    if title_similarity >= 0.96:
        reasons.append("title_exact_or_near_exact")
    elif title_similarity >= 0.8:
        reasons.append("title_similar")
    if dates["kind"] == "exact":
        reasons.append("dates_exact")
    elif dates["kind"] in {"overlap", "near"}:
        reasons.append(f"dates_{dates['kind']}")
    elif dates["kind"] == "conflict":
        reasons.append("dates_conflict")
    if venue_score >= 0.8:
        reasons.append("venue_match")
    elif venue_score > 0:
        reasons.append("region_match")
    if organizer_score:
        reasons.append("organizer_match")

    auto_merge = (
        source_reference_exact
        or url_exact
        or (
            score >= 0.84
            and title_similarity >= 0.78
            and bool(dates["compatible"])
            and venue_score >= 0.28
        )
    )
    needs_review = (
        not auto_merge
        and score >= 0.64
        and title_similarity >= 0.58
    )

    decision = (
        MatchDecision.AUTO_MERGE
        if auto_merge
        else MatchDecision.REVIEW
        if needs_review
        else MatchDecision.NEW
    )
    return MatchResult(
        decision=decision,
        score=score,
        existing_id=str(existing.get("id") or ""),
        existing_title=str(existing.get("title") or ""),
        title_similarity=round(title_similarity, 4),
        date_kind=str(dates["kind"]),
        date_score=round(float(dates["score"]), 4),
        venue_score=round(venue_score, 4),
        organizer_score=round(organizer_score, 4),
        url_exact=url_exact,
        source_reference_exact=source_reference_exact,
        reasons=tuple(reasons),
    )


def find_best_match(
    source_event: dict[str, Any],
    existing_events: Iterable[dict[str, Any]],
) -> tuple[MatchResult | None, list[MatchResult]]:
    source_region = str(
        source_event.get("regionCanonical") or ""
    )
    scored: list[MatchResult] = []
    for existing in existing_events:
        existing_region = str(
            existing.get("regionCanonical")
            or existing.get("region")
            or ""
        )
        if (
            source_region
            and existing_region
            and source_region.replace("台", "臺")
            != existing_region.replace("台", "臺")
        ):
            continue
        result = score_match(source_event, existing)
        if result.score >= 0.42:
            scored.append(result)

    scored.sort(
        key=lambda item: (
            item.score,
            item.title_similarity,
            item.date_score,
        ),
        reverse=True,
    )
    return (
        scored[0] if scored else None,
        scored[:3],
    )
