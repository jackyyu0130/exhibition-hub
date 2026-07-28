from __future__ import annotations

from datetime import date
import re
import unicodedata
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit


_BRACKET_PREFIX_RE = re.compile(
    r"^(?:【[^】]{1,40}】|\[[^\]]{1,40}\])\s*"
)
_TITLE_NOISE_RE = re.compile(
    r"(?:台北|臺北|高雄|台中|臺中)?(?:場|站)?$"
)
_NON_WORD_RE = re.compile(
    r"[^0-9a-z\u4e00-\u9fff]+",
    re.IGNORECASE,
)
_TITLE_CORE_PATTERNS = (
    re.compile(r"《([^》]{2,120})》"),
    re.compile(r"「([^」]{2,120})」"),
    re.compile(r"『([^』]{2,120})』"),
)


def clean_text(value: Any) -> str:
    return re.sub(
        r"\s+",
        " ",
        unicodedata.normalize(
            "NFKC",
            str(value or ""),
        ),
    ).strip()


def normalize_title(value: Any) -> str:
    text = clean_text(value).lower()
    text = _BRACKET_PREFIX_RE.sub("", text)
    text = text.replace("臺", "台")
    text = _TITLE_NOISE_RE.sub("", text)
    return _NON_WORD_RE.sub("", text)


def title_variants(value: Any) -> list[str]:
    text = clean_text(value)
    result: list[str] = []

    full = normalize_title(text)
    if full:
        result.append(full)

    for pattern in _TITLE_CORE_PATTERNS:
        for match in pattern.finditer(text):
            core = normalize_title(match.group(1))
            if len(core) >= 4 and core not in result:
                result.append(core)

    return result


def normalize_name(value: Any) -> str:
    text = clean_text(value).lower().replace("臺", "台")
    return _NON_WORD_RE.sub("", text)


def normalize_url(value: Any) -> str:
    text = clean_text(value)
    if not text.startswith(("http://", "https://")):
        return ""
    parsed = urlsplit(text)
    host = parsed.netloc.lower()
    path = parsed.path.rstrip("/")
    return urlunsplit(
        (
            parsed.scheme.lower(),
            host,
            path,
            "",
            "",
        )
    )


def parse_date(value: Any) -> date | None:
    text = clean_text(value)[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def date_relation(
    left_start: Any,
    left_end: Any,
    right_start: Any,
    right_end: Any,
) -> dict[str, Any]:
    ls = parse_date(left_start)
    le = parse_date(left_end) or ls
    rs = parse_date(right_start)
    re_ = parse_date(right_end) or rs

    if not ls or not rs:
        return {
            "kind": "unknown",
            "score": 0.0,
            "compatible": True,
        }

    if le is None or re_ is None:
        return {
            "kind": "unknown",
            "score": 0.0,
            "compatible": True,
        }

    exact = ls == rs and le == re_
    if exact:
        return {
            "kind": "exact",
            "score": 1.0,
            "compatible": True,
        }

    overlap = max(ls, rs) <= min(le, re_)
    if overlap:
        start_gap = abs((ls - rs).days)
        end_gap = abs((le - re_).days)
        closeness = max(
            0.0,
            1.0 - min(60, start_gap + end_gap) / 60,
        )
        return {
            "kind": "overlap",
            "score": 0.72 + 0.22 * closeness,
            "compatible": True,
        }

    gap = min(
        abs((ls - re_).days),
        abs((rs - le).days),
        abs((ls - rs).days),
    )
    if gap <= 3:
        return {
            "kind": "near",
            "score": 0.55,
            "compatible": True,
        }

    return {
        "kind": "conflict",
        "score": 0.0,
        "compatible": False,
        "gapDays": gap,
    }


def unique_strings(values: Iterable[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = clean_text(value)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        result.append(cleaned)
    return result


def event_venue_values(event: dict[str, Any]) -> list[str]:
    values: list[Any] = [
        event.get("venueName"),
        event.get("venueGroup"),
        event.get("locationName"),
        event.get("location"),
    ]
    values.extend(event.get("venueNames") or [])
    values.extend(event.get("subVenueNames") or [])
    return unique_strings(values)


def event_organizers(event: dict[str, Any]) -> list[str]:
    values: list[Any] = [
        event.get("organizer"),
        event.get("unit"),
    ]
    values.extend(event.get("organizers") or [])
    return unique_strings(values)
