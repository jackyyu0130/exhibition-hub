from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
import hashlib
import json
import re
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urljoin, urlparse, urlunparse


EVENT_KEYWORDS_RE = re.compile(
    r"演唱會|音樂會|音樂祭|音樂節|專場|巡迴|見面會|粉絲見面會|"
    r"展演|節目|活動|售票|開賣|festival|concert|live\s*(?:house|tour|in)|"
    r"world\s* tour|asia\s* tour|fan\s*(?:meeting|concert)|showcase|gig",
    re.I,
)
EXCLUDE_RE = re.compile(
    r"徵才|招募|課程|講座|工作坊|研習|營隊|場地租借|包場|設備介紹|"
    r"交通資訊|會員|關於我們|聯絡我們|隱私權|常見問題|回顧|花絮|"
    r"完售感謝|售罄感謝|取消公告|延期公告",
    re.I,
)
NAV_TEXT_RE = re.compile(
    r"^(?:首頁|關於|節目|活動|展演|購票|售票|更多|查看全部|read more|more|events?|programs?)$",
    re.I,
)
DATE_RANGE_RE = re.compile(
    r"(?P<y1>20\d{2})\s*(?:年|[./-])\s*(?P<m1>\d{1,2})\s*(?:月|[./-])\s*(?P<d1>\d{1,2})\s*日?"
    r"(?:\s*[（(][^）)]{0,8}[）)])?\s*(?:-|－|–|—|~|～|至|到)\s*"
    r"(?:(?P<y2>20\d{2})\s*(?:年|[./-])\s*)?(?P<m2>\d{1,2})\s*(?:月|[./-])\s*(?P<d2>\d{1,2})\s*日?",
    re.I,
)
DATE_SINGLE_RE = re.compile(
    r"(?P<y>20\d{2})\s*(?:年|[./-])\s*(?P<m>\d{1,2})\s*(?:月|[./-])\s*(?P<d>\d{1,2})\s*日?",
    re.I,
)
ISO_DATETIME_RE = re.compile(r"^(20\d{2})-(\d{2})-(\d{2})")
IMAGE_REJECT_RE = re.compile(
    r"logo|favicon|icon|avatar|loading|spinner|placeholder|header|footer|share|facebook|instagram|youtube",
    re.I,
)
TITLE_CLEAN_RE = re.compile(r"\s*[|｜]\s*(?:KKTIX|拓元售票|TixCraft|OPENTIX|ibon售票|年代售票|Ticket Plus).*$", re.I)


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_key(value: Any) -> str:
    text = clean(value).replace("臺", "台").lower()
    return re.sub(r"[\s　()（）\[\]【】<>《》\-_/／・·,，.。:：;；|｜'\"]+", "", text)


def normalize_url(value: str) -> str:
    parsed = urlparse(clean(value))
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    query = "&".join(
        part for part in parsed.query.split("&")
        if part and not part.lower().startswith(("utm_", "fbclid=", "gclid=", "xmt="))
    )
    return urlunparse((parsed.scheme, parsed.netloc.lower(), parsed.path or "/", "", query, ""))


def valid_public_url(value: Any) -> bool:
    return bool(normalize_url(str(value or "")))


def iso_date(value: Any) -> str:
    text = clean(value)
    match = ISO_DATETIME_RE.search(text)
    if match:
        return f"{int(match.group(1)):04d}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
    match = DATE_SINGLE_RE.search(text)
    if not match:
        return ""
    try:
        return date(int(match.group("y")), int(match.group("m")), int(match.group("d"))).isoformat()
    except ValueError:
        return ""


def extract_dates(text: str) -> tuple[str, str]:
    text = clean(text)
    match = DATE_RANGE_RE.search(text)
    if match:
        y1, m1, d1 = int(match.group("y1")), int(match.group("m1")), int(match.group("d1"))
        y2 = int(match.group("y2") or y1)
        m2, d2 = int(match.group("m2")), int(match.group("d2"))
        try:
            start = date(y1, m1, d1)
            end = date(y2, m2, d2)
            if end < start and not match.group("y2"):
                end = date(y1 + 1, m2, d2)
            return start.isoformat(), end.isoformat()
        except ValueError:
            pass
    single = iso_date(text)
    return (single, single) if single else ("", "")


def event_category(title: str, text: str = "") -> str:
    haystack = f"{title} {text}"
    if re.search(r"演唱會|world\s* tour|asia\s* tour|fan\s*concert|live\s*in", haystack, re.I):
        return "演唱會"
    if re.search(r"音樂祭|音樂節|festival", haystack, re.I):
        return "音樂"
    if re.search(r"音樂會|專場|樂團|爵士|live\s*house|gig|showcase", haystack, re.I):
        return "音樂"
    if re.search(r"舞台劇|音樂劇|劇場|舞蹈|馬戲|表演", haystack, re.I):
        return "表演"
    if re.search(r"展覽|個展|聯展|藝術|攝影|設計", haystack, re.I):
        return "美術"
    return "其他"


def content_type(category: str) -> str:
    return {
        "演唱會": "concert",
        "音樂": "music",
        "表演": "performance",
        "美術": "art_exhibition",
    }.get(category, "event")


class PageParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.links: list[dict[str, str]] = []
        self.images: list[str] = []
        self.meta: dict[str, str] = {}
        self.text_parts: list[str] = []
        self.h1_parts: list[str] = []
        self.jsonld_parts: list[str] = []
        self._anchor: dict[str, Any] | None = None
        self._ignored = 0
        self._h1 = 0
        self._jsonld = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr = {str(k).lower(): str(v or "") for k, v in attrs}
        if tag in {"style", "noscript", "svg", "template"}:
            self._ignored += 1
            return
        if tag == "script":
            if attr.get("type", "").lower() == "application/ld+json":
                self._jsonld += 1
            else:
                self._ignored += 1
            return
        if self._ignored:
            return
        if tag == "h1":
            self._h1 += 1
        if tag == "meta":
            key = clean(attr.get("property") or attr.get("name")).lower()
            value = clean(attr.get("content"))
            if key and value and key not in self.meta:
                self.meta[key] = value
        if tag == "img":
            src = attr.get("data-src") or attr.get("data-original") or attr.get("src")
            if src:
                self.images.append(urljoin(self.base_url, src))
            if self._anchor is not None and attr.get("alt"):
                self._anchor["parts"].append(attr["alt"])
        if tag == "a" and attr.get("href"):
            self._anchor = {
                "url": urljoin(self.base_url, attr["href"]),
                "parts": [attr.get("title", ""), attr.get("aria-label", "")],
            }

    def handle_data(self, data: str) -> None:
        if self._jsonld:
            self.jsonld_parts.append(data)
            return
        if self._ignored:
            return
        text = clean(data)
        if not text:
            return
        self.text_parts.append(text)
        if self._h1:
            self.h1_parts.append(text)
        if self._anchor is not None:
            self._anchor["parts"].append(text)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "script" and self._jsonld:
            self._jsonld -= 1
            return
        if tag in {"style", "noscript", "svg", "template", "script"} and self._ignored:
            self._ignored -= 1
            return
        if self._ignored:
            return
        if tag == "h1" and self._h1:
            self._h1 -= 1
        if tag == "a" and self._anchor is not None:
            text = clean(" ".join(self._anchor["parts"]))
            self.links.append({"url": normalize_url(self._anchor["url"]), "text": text})
            self._anchor = None

    def full_text(self) -> str:
        return clean(" ".join(self.text_parts))

    def h1(self) -> str:
        return clean(" ".join(self.h1_parts))


@dataclass
class VenueMatch:
    status: str
    canonical_name: str = ""
    region: str = ""
    matched_alias: str = ""
    candidates: tuple[str, ...] = ()


@dataclass
class Candidate:
    candidateId: str
    sourceId: str
    sourceName: str
    endpointId: str
    endpointPlatform: str
    sourceUrl: str
    title: str
    startDate: str
    endDate: str
    venueName: str
    region: str
    imageUrl: str
    category: str
    contentType: str
    description: str
    evidence: list[str]
    confidence: float
    venueMatchStatus: str
    venueMatchAlias: str
    duplicateOf: str
    autoPublishEligible: bool
    blockingIssues: list[str]
    discoveredAt: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def flatten_venue_rules(registry: Mapping[str, Any]) -> list[dict[str, str]]:
    rules: list[dict[str, str]] = []
    for org in registry.get("organizations") or []:
        if not isinstance(org, Mapping):
            continue
        for venue in org.get("venueMatches") or []:
            if not isinstance(venue, Mapping):
                continue
            canonical = clean(venue.get("canonicalName"))
            region = clean(venue.get("region"))
            for alias in [canonical, *(venue.get("aliases") or [])]:
                alias_text = clean(alias)
                if len(normalize_key(alias_text)) < 3:
                    continue
                rules.append({"canonicalName": canonical, "region": region, "alias": alias_text})
    rules.sort(key=lambda item: len(normalize_key(item["alias"])), reverse=True)
    return rules


def match_venue(text: str, organization: Mapping[str, Any], registry: Mapping[str, Any]) -> VenueMatch:
    normalized = normalize_key(text)
    hits: dict[tuple[str, str], str] = {}
    for rule in flatten_venue_rules(registry):
        if normalize_key(rule["alias"]) in normalized:
            hits[(rule["canonicalName"], rule["region"])] = rule["alias"]
    if len(hits) == 1:
        (canonical, region), alias = next(iter(hits.items()))
        return VenueMatch("matched", canonical, region, alias)
    if len(hits) > 1:
        names = tuple(sorted({name for name, _ in hits}))
        return VenueMatch("ambiguous", candidates=names)

    org_venues = [v for v in organization.get("venueMatches") or [] if isinstance(v, Mapping)]
    if "venue" in (organization.get("roles") or []) and len(org_venues) == 1:
        venue = org_venues[0]
        return VenueMatch(
            "matched_by_source",
            clean(venue.get("canonicalName")),
            clean(venue.get("region")),
            "source_default",
        )
    return VenueMatch("unmatched")


def jsonld_events(parser: PageParser, page_url: str) -> list[dict[str, Any]]:
    raw = clean(" ".join(parser.jsonld_parts))
    if not raw:
        return []
    payloads: list[Any] = []
    try:
        payloads.append(json.loads(raw))
    except json.JSONDecodeError:
        for match in re.finditer(r"\{[\s\S]*?\}", raw):
            try:
                payloads.append(json.loads(match.group(0)))
            except json.JSONDecodeError:
                continue

    result: list[dict[str, Any]] = []

    def walk(value: Any) -> Iterable[Mapping[str, Any]]:
        if isinstance(value, Mapping):
            yield value
            for child in value.values():
                yield from walk(child)
        elif isinstance(value, list):
            for child in value:
                yield from walk(child)

    for payload in payloads:
        for item in walk(payload):
            kind = item.get("@type")
            kinds = {str(x).lower() for x in (kind if isinstance(kind, list) else [kind])}
            if not kinds.intersection({"event", "musicevent", "theaterevent", "festival"}):
                continue
            location = item.get("location") or {}
            if isinstance(location, list):
                location = location[0] if location else {}
            image = item.get("image")
            if isinstance(image, list):
                image = image[0] if image else ""
            elif isinstance(image, Mapping):
                image = image.get("url") or ""
            result.append({
                "title": clean(item.get("name")),
                "startDate": iso_date(item.get("startDate")),
                "endDate": iso_date(item.get("endDate") or item.get("startDate")),
                "venueText": clean(location.get("name") if isinstance(location, Mapping) else location),
                "imageUrl": normalize_url(str(image or "")),
                "sourceUrl": normalize_url(str(item.get("url") or page_url)),
                "description": clean(item.get("description")),
                "evidence": ["json_ld_event", "official_detail"],
            })
    return result


def clean_image(values: Sequence[str]) -> str:
    for value in values:
        url = normalize_url(value)
        if not url:
            continue
        path = urlparse(url).path
        if IMAGE_REJECT_RE.search(path) or path.lower().endswith((".svg", ".gif")):
            continue
        return url
    return ""


def listing_links(parser: PageParser, endpoint: Mapping[str, Any]) -> list[dict[str, str]]:
    base_host = (urlparse(endpoint.get("url") or "").hostname or "").lower().removeprefix("www.")
    platform = clean(endpoint.get("accessMode"))
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in parser.links:
        url, text = normalize_url(row.get("url", "")), clean(row.get("text"))
        if not url or url in seen:
            continue
        host = (urlparse(url).hostname or "").lower().removeprefix("www.")
        if host != base_host:
            continue
        path = urlparse(url).path.lower()
        is_kktix = platform == "kktix_organizer" and "/events/" in path
        has_signal = bool(EVENT_KEYWORDS_RE.search(text) or DATE_SINGLE_RE.search(text))
        if not is_kktix and (not has_signal or NAV_TEXT_RE.fullmatch(text) or EXCLUDE_RE.search(text)):
            continue
        if len(text) < 3 and not is_kktix:
            continue
        seen.add(url)
        rows.append({"url": url, "text": text})
    return rows[:20]


def existing_index(events_payload: Mapping[str, Any] | Sequence[Any]) -> list[dict[str, str]]:
    raw_events: Sequence[Any]
    if isinstance(events_payload, Mapping):
        raw_events = events_payload.get("events") or []
    else:
        raw_events = events_payload
    result: list[dict[str, str]] = []
    for event in raw_events:
        if not isinstance(event, Mapping):
            continue
        result.append({
            "id": clean(event.get("id")),
            "title": normalize_key(event.get("title")),
            "date": clean(event.get("startDate")),
            "venue": normalize_key(event.get("venueName") or event.get("locationName") or event.get("venueGroup")),
            "url": normalize_url(str(event.get("sourceUrl") or "")),
        })
    return result


def find_duplicate(title: str, start_date: str, venue: str, source_url: str, index: Sequence[Mapping[str, str]]) -> str:
    title_key = normalize_key(title)
    venue_key = normalize_key(venue)
    source_url = normalize_url(source_url)
    for item in index:
        if source_url and item.get("url") == source_url:
            return clean(item.get("id"))
        if not title_key or title_key != item.get("title"):
            continue
        if start_date and item.get("date") and start_date != item.get("date"):
            continue
        if venue_key and item.get("venue") and venue_key != item.get("venue"):
            continue
        return clean(item.get("id"))
    return ""


def make_candidate(
    raw: Mapping[str, Any],
    organization: Mapping[str, Any],
    endpoint: Mapping[str, Any],
    registry: Mapping[str, Any],
    existing: Sequence[Mapping[str, str]],
    *,
    now: datetime,
) -> Candidate:
    title = TITLE_CLEAN_RE.sub("", clean(raw.get("title")))[:240]
    description = clean(raw.get("description"))[:1200]
    start_date = iso_date(raw.get("startDate"))
    end_date = iso_date(raw.get("endDate")) or start_date
    source_url = normalize_url(str(raw.get("sourceUrl") or endpoint.get("url") or ""))
    image_url = clean_image([str(raw.get("imageUrl") or "")])
    combined = " ".join([title, description, clean(raw.get("venueText"))])
    venue = match_venue(combined, organization, registry)
    category = event_category(title, description)
    evidence = sorted({clean(x) for x in raw.get("evidence") or [] if clean(x)})
    platform = clean(endpoint.get("platform"))

    confidence = 0.35
    if platform in {"official_website", "kktix_organizer"}:
        confidence += 0.15
    if "official_detail" in evidence:
        confidence += 0.10
    if "json_ld_event" in evidence:
        confidence += 0.10
    if start_date and end_date:
        confidence += 0.10
    if image_url:
        confidence += 0.08
    if venue.status in {"matched", "matched_by_source"}:
        confidence += 0.10
    if EVENT_KEYWORDS_RE.search(f"{title} {description}"):
        confidence += 0.02
    confidence = round(min(confidence, 0.99), 3)

    duplicate = find_duplicate(title, start_date, venue.canonical_name, source_url, existing)
    blocking: list[str] = []
    if len(title) < 4 or NAV_TEXT_RE.fullmatch(title):
        blocking.append("invalid_title")
    if EXCLUDE_RE.search(f"{title} {description}"):
        blocking.append("excluded_content")
    if not start_date or not end_date:
        blocking.append("missing_full_date")
    if venue.status not in {"matched", "matched_by_source"}:
        blocking.append("venue_not_unique")
    if not image_url:
        blocking.append("missing_image")
    if not source_url:
        blocking.append("missing_source_url")
    if duplicate:
        blocking.append("duplicate_existing_event")
    if start_date:
        try:
            if date.fromisoformat(end_date) < (now.date() - timedelta(days=2)):
                blocking.append("event_already_ended")
        except ValueError:
            blocking.append("invalid_date")
    if confidence < float(registry.get("safety", {}).get("autoPublishMinimumConfidence", 0.94)):
        blocking.append("confidence_below_auto_publish")
    if not endpoint.get("autoPublishAllowed"):
        blocking.append("source_candidate_only")
    if endpoint.get("accessMode") not in {"public_html", "kktix_organizer"}:
        blocking.append("non_official_read_mode")

    candidate_id = hashlib.sha256(
        f"{organization.get('id')}|{endpoint.get('id')}|{source_url}|{title}|{start_date}".encode("utf-8")
    ).hexdigest()[:24]
    return Candidate(
        candidateId=candidate_id,
        sourceId=clean(organization.get("id")),
        sourceName=clean(organization.get("name")),
        endpointId=clean(endpoint.get("id")),
        endpointPlatform=platform,
        sourceUrl=source_url,
        title=title,
        startDate=start_date,
        endDate=end_date,
        venueName=venue.canonical_name,
        region=venue.region,
        imageUrl=image_url,
        category=category,
        contentType=content_type(category),
        description=description,
        evidence=evidence,
        confidence=confidence,
        venueMatchStatus=venue.status,
        venueMatchAlias=venue.matched_alias,
        duplicateOf=duplicate,
        autoPublishEligible=not blocking,
        blockingIssues=blocking,
        discoveredAt=now.isoformat(),
    )


def detail_records(parser: PageParser, page_url: str, fallback_title: str = "") -> list[dict[str, Any]]:
    records = jsonld_events(parser, page_url)
    if records:
        return records
    full_text = parser.full_text()
    title = clean(parser.meta.get("og:title") or parser.h1() or fallback_title)
    title = TITLE_CLEAN_RE.sub("", title)
    start, end = extract_dates(full_text)
    image = clean_image([
        parser.meta.get("og:image", ""),
        parser.meta.get("twitter:image", ""),
        *parser.images,
    ])
    description = clean(parser.meta.get("og:description") or parser.meta.get("description") or full_text[:1200])
    if not title:
        return []
    return [{
        "title": title,
        "startDate": start,
        "endDate": end,
        "venueText": full_text,
        "imageUrl": image,
        "sourceUrl": page_url,
        "description": description,
        "evidence": ["official_detail"],
    }]
