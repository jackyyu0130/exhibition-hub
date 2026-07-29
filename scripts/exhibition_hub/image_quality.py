from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping
from urllib.parse import unquote, urlsplit
import re


_FACEBOOK_HOST_RE = re.compile(
    r"(?:^|\.)(?:facebook\.com|fb\.me|fbcdn\.net|facebookusercontent\.com)$",
    re.IGNORECASE,
)
_HARD_REJECT_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("opentix-interface-flags", re.compile(r"/_nuxt/img/flags\.", re.I)),
    ("site-interface-link-icon", re.compile(r"/_nuxt/img/linkto\.", re.I)),
    ("map-or-coordinate-image", re.compile(
        r"(?:/images?/coordinate\.|maps\.googleapis\.com/maps/api/staticmap)",
        re.I,
    )),
    ("generic-default-image", re.compile(
        r"(?:\{\{:defaultimg\}\}|defaultimg\.|programinfodefault|"
        r"/default/(?:orgcover|orgbanner)\.|opentixpagedefault|"
        r"(?:^|[/_.-])(?:no[-_]?pic|no[-_]?image)(?:[/_.-]|$))",
        re.I,
    )),
    ("culture-cloud-generic-banner", re.compile(
        r"cloud\.culture\.tw/assets/images/banner_1200x630\.",
        re.I,
    )),
    ("sharing-interface-icon", re.compile(
        r"(?:sharenav_(?:fb|twitter)|index_toplogo|top_icon_2|"
        r"(?:^|[/_.-])sharelogo(?:[/_.-]|$))",
        re.I,
    )),
    ("cms-navigation-icon", re.compile(
        r"(?:filedisplay=(?:logo|icon)[^&]*|/images/banner/p-but\.png|"
        r"/banner_live\.png)",
        re.I,
    )),
    ("loading-or-placeholder", re.compile(
        r"(?:^|[/_.-])(?:ajax[-_]?loader|loader|loading|spinner|progress|"
        r"preload|placeholder|blank|spacer|pixel|sprite|favicon|qr[-_]?code)"
        r"(?:[/_.-]|$)",
        re.I,
    )),
)


def is_facebook_url(value: Any) -> bool:
    try:
        parsed = urlsplit(str(value or ""))
    except ValueError:
        return False
    return bool(_FACEBOOK_HOST_RE.search(parsed.hostname or ""))


def suspicious_image_reason(value: Any) -> str:
    url = str(value or "").strip()
    if not url:
        return "empty"
    try:
        parsed = urlsplit(url)
    except ValueError:
        return "invalid-url"
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return "invalid-url"
    if is_facebook_url(url):
        return "facebook-media"
    decoded = unquote(url).lower()
    for reason, pattern in _HARD_REJECT_RULES:
        if pattern.search(decoded):
            return reason
    if parsed.path.lower().endswith((".svg", ".gif", ".ico")):
        return "non-poster-format"
    return ""


def clean_image_urls(values: Iterable[Any]) -> tuple[list[str], list[dict[str, str]]]:
    kept: list[str] = []
    rejected: list[dict[str, str]] = []
    seen: set[str] = set()
    for value in values:
        url = str(value or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        reason = suspicious_image_reason(url)
        if reason:
            rejected.append({"url": url, "reason": reason})
            continue
        kept.append(url)
    return kept, rejected


def sanitize_event(event: Mapping[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    cleaned = deepcopy(dict(event))
    values = [
        *(cleaned.get("images") or []),
        cleaned.get("image"),
    ]
    images, rejected = clean_image_urls(values)
    cleaned["images"] = images[:10]
    cleaned["image"] = cleaned["images"][0] if cleaned["images"] else ""

    for field in ("sourceUrls", "externalUrls"):
        if isinstance(cleaned.get(field), list):
            cleaned[field] = [
                str(value)
                for value in cleaned[field]
                if value and not is_facebook_url(value)
            ]
    for field in ("sourceUrl", "officialUrl", "ticketUrl", "sourceUrlRejected"):
        if is_facebook_url(cleaned.get(field)):
            cleaned[field] = ""
    if isinstance(cleaned.get("sourceRecords"), list):
        cleaned["sourceRecords"] = [
            item
            for item in cleaned["sourceRecords"]
            if not isinstance(item, dict)
            or not any(
                is_facebook_url(item.get(field))
                for field in ("officialUrl", "sourceUrl")
            )
        ]
    return cleaned, rejected


def audit_payload(payload: Mapping[str, Any], *, fix: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
    result = deepcopy(dict(payload))
    events: list[dict[str, Any]] = []
    removed_by_reason: Counter[str] = Counter()
    affected: list[dict[str, Any]] = []
    facebook_cleaned = 0
    without_images_before = 0
    without_images_after = 0
    rejected_venue_images: list[dict[str, str]] = []

    for raw in payload.get("events") or []:
        if not isinstance(raw, Mapping):
            continue
        if not raw.get("image") and not raw.get("images"):
            without_images_before += 1
        cleaned, rejected = sanitize_event(raw)
        if rejected:
            removed_by_reason.update(item["reason"] for item in rejected)
            affected.append({
                "id": str(raw.get("id") or ""),
                "title": str(raw.get("title") or ""),
                "removed": rejected,
                "usableImageCount": len(cleaned.get("images") or []),
            })
        original_social = (
            list(raw.get("sourceUrls") or []),
            list(raw.get("externalUrls") or []),
            raw.get("sourceUrl"),
            raw.get("officialUrl"),
        )
        cleaned_social = (
            list(cleaned.get("sourceUrls") or []),
            list(cleaned.get("externalUrls") or []),
            cleaned.get("sourceUrl"),
            cleaned.get("officialUrl"),
        )
        if original_social != cleaned_social:
            facebook_cleaned += 1
        if not cleaned.get("images"):
            without_images_after += 1
        events.append(cleaned if fix else dict(raw))

    result["events"] = events
    venue_images = dict(payload.get("venueImages") or {})
    if venue_images:
        for venue, url in list(venue_images.items()):
            reason = suspicious_image_reason(url)
            if not reason:
                continue
            rejected_venue_images.append({
                "venue": str(venue),
                "url": str(url),
                "reason": reason,
            })
            if fix:
                venue_images.pop(venue, None)
        result["venueImages"] = venue_images
    if fix:
        stats = dict(result.get("stats") or {})
        image_count = sum(bool(event.get("image")) for event in events)
        stats.update({
            "eventCount": len(events),
            "imageCount": image_count,
            "multiImageCount": sum(len(event.get("images") or []) > 1 for event in events),
            "imageCoverage": round(image_count / len(events), 4) if events else 0.0,
        })
        result["stats"] = stats
    report = {
        "eventCount": len(events),
        "fixApplied": fix,
        "affectedEventCount": len(affected),
        "rejectedImageCount": sum(removed_by_reason.values()),
        "rejectedByReason": dict(sorted(removed_by_reason.items())),
        "facebookReferenceEventCount": facebook_cleaned,
        "missingImageCountBefore": without_images_before,
        "missingImageCountAfter": without_images_after,
        "rejectedVenueImageCount": len(rejected_venue_images),
        "rejectedVenueImages": rejected_venue_images,
        "affectedEvents": affected,
    }
    return result, report
