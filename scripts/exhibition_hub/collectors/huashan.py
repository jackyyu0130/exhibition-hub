from __future__ import annotations

from html.parser import HTMLParser
import os
import re
from typing import Any, Mapping, Sequence
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

from .base import (
    BaseCollector,
    CollectorRecord,
    CollectorRunReport,
    CollectorSource,
    SourceKind,
)


DEFAULT_LISTING_URL = (
    "https://www.huashan1914.com/w/huashan1914/CustomEvent"
)
HUASHAN_VENUE_NAME = "華山1914文化創意產業園區"
HUASHAN_ADDRESS = "臺北市中正區八德路一段1號"
HUASHAN_REGION = "臺北市"

_DETAIL_PATH_RE = re.compile(
    r"^/w/(?:huashan1914|umaytheater)/(?:exhibition|event|performance)_[A-Za-z0-9_-]+/?$",
    re.IGNORECASE,
)
_DATE_PAIR_RE = re.compile(
    r"(?P<start>\d{4}[./-]\d{1,2}[./-]\d{1,2})"
    r"\s+"
    r"(?P<end>\d{4}[./-]\d{1,2}[./-]\d{1,2})"
)
_PAGE_COUNT_RE = re.compile(
    r"第\s*(?P<current>\d+)\s*頁\s*/\s*共\s*(?P<total>\d+)\s*頁"
)
_LISTING_CATEGORY_RE = re.compile(
    r"^(?P<category>園區店家活動|園區活動)\s*"
)
_TIME_RE = re.compile(
    r"(?P<start>\d{1,2}:\d{2})\s*(?P<start_ampm>AM|PM)?"
    r"\s*[-~～至]\s*"
    r"(?P<end>\d{1,2}:\d{2})\s*(?P<end_ampm>AM|PM)?",
    re.IGNORECASE,
)
_PRICE_SIGNAL_RE = re.compile(
    r"(?:NTD|NT\$|新臺幣|新台幣|票價|門票|售票|全票|優待票|愛心票|\d[\d,]*\s*元)",
    re.IGNORECASE,
)
_KNOWN_ACTIVITY_TYPES = (
    "展演活動",
    "市集活動",
    "論壇講座",
    "期間限定店",
    "品牌活動",
    "表演藝術",
)
_BLOCK_TAGS = {
    "article", "aside", "br", "dd", "div", "dl", "dt", "figcaption",
    "footer", "h1", "h2", "h3", "h4", "h5", "h6", "header", "li",
    "main", "p", "section", "td", "th", "tr", "ul", "ol",
}
_STOP_LABELS = {
    "主辦單位", "協辦單位", "活動地點", "展演活動", "市集活動",
    "論壇講座", "期間限定店", "品牌活動", "表演藝術", "Image",
    "相關活動", "如何來華山", "展覽資訊", "活動資訊",
}


def _normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _normalize_date(value: str) -> str:
    parts = re.split(r"[./-]", value)
    if len(parts) != 3:
        return ""
    year, month, day = (int(part) for part in parts)
    return f"{year:04d}-{month:02d}-{day:02d}"


def _with_page_index(url: str, page: int) -> str:
    if page <= 1:
        return url
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["index"] = str(page)
    return urlunparse(parsed._replace(query=urlencode(query)))


def _unique(values: Sequence[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = _normalize_space(value)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _truthy_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _clean_page_title(value: str) -> str:
    title = _normalize_space(value)
    for suffix in (
        "- 華山1914文化創意產業園區",
        "｜華山1914文化創意產業園區",
        "| 華山1914文化創意產業園區",
    ):
        if title.endswith(suffix):
            title = title[: -len(suffix)].strip()
    return title


def _normalize_time(value: str, ampm: str | None) -> str:
    hour_text, minute = value.split(":", 1)
    hour = int(hour_text)
    marker = (ampm or "").upper()
    if marker == "PM" and hour < 12:
        hour += 12
    elif marker == "AM" and hour == 12:
        hour = 0
    return f"{hour:02d}:{int(minute):02d}"


def _content_type_hint(source_category: str, title: str) -> str:
    if source_category == "期間限定店":
        return "快閃店"
    if source_category == "市集活動":
        return "市集"
    if source_category == "表演藝術":
        return "表演"
    if source_category == "論壇講座":
        return "其他"
    if source_category == "品牌活動":
        return "快閃店" if re.search(r"快閃|POP\s*UP", title, re.I) else "其他"
    if re.search(r"快閃|POP\s*UP", title, re.I):
        return "快閃店"
    if re.search(r"動漫|動畫|漫畫|CHIIKAWA|PEANUTS|咖波", title, re.I):
        return "動漫"
    if re.search(r"個展|攝影展", title):
        return "美術"
    return "其他"


class _HuashanListingParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.events: list[dict[str, Any]] = []
        self.page_text: list[str] = []
        self._anchor: dict[str, Any] | None = None

    @staticmethod
    def _is_detail_href(href: str) -> bool:
        absolute = urljoin(DEFAULT_LISTING_URL, href)
        parsed = urlparse(absolute)
        return (
            parsed.netloc.lower() == "www.huashan1914.com"
            and bool(_DETAIL_PATH_RE.match(parsed.path))
        )

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attrs_map = {str(name).lower(): value for name, value in attrs}

        if self._anchor is not None:
            if tag.lower() == "img":
                image = (
                    attrs_map.get("data-src")
                    or attrs_map.get("data-original")
                    or attrs_map.get("src")
                    or ""
                )
                if image and not self._anchor.get("imageUrl"):
                    self._anchor["imageUrl"] = urljoin(self.base_url, image)
            return

        if tag.lower() != "a":
            return

        href = str(attrs_map.get("href") or "").strip()
        if not href or not self._is_detail_href(href):
            return

        self._anchor = {
            "detailUrl": urljoin(self.base_url, href),
            "textParts": [],
            "imageUrl": "",
        }

    def handle_data(self, data: str) -> None:
        normalized = _normalize_space(data)
        if normalized:
            self.page_text.append(normalized)
            if self._anchor is not None:
                self._anchor["textParts"].append(normalized)

    def handle_endtag(self, tag: str) -> None:
        if self._anchor is None or tag.lower() != "a":
            return
        event = self._parse_anchor(self._anchor)
        if event is not None:
            self.events.append(event)
        self._anchor = None

    @staticmethod
    def _parse_anchor(anchor: Mapping[str, Any]) -> dict[str, Any] | None:
        text = _normalize_space(" ".join(anchor.get("textParts") or []))
        date_match = _DATE_PAIR_RE.search(text)
        if date_match is None:
            return None

        remainder = _normalize_space(text[date_match.end():])
        category_match = _LISTING_CATEGORY_RE.match(remainder)
        listing_category = ""
        if category_match is not None:
            listing_category = category_match.group("category")
            remainder = _normalize_space(remainder[category_match.end():])

        if not remainder:
            return None

        detail_url = str(anchor.get("detailUrl") or "")
        source_event_id = urlparse(detail_url).path.rstrip("/").split("/")[-1]

        return {
            "sourceEventId": source_event_id,
            "title": remainder,
            "startDate": _normalize_date(date_match.group("start")),
            "endDate": _normalize_date(date_match.group("end")),
            "listingCategory": listing_category,
            "detailUrl": detail_url,
            "imageUrl": str(anchor.get("imageUrl") or ""),
            "listingText": text,
        }

    def total_pages(self) -> int:
        text = " ".join(self.page_text)
        match = _PAGE_COUNT_RE.search(text)
        return max(1, int(match.group("total"))) if match else 1


class _HuashanDetailParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.text_parts: list[str] = []
        self.meta: dict[str, str] = {}
        self.image_urls: list[str] = []
        self.external_urls: list[str] = []
        self.canonical_url = ""

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        tag = tag.lower()
        attrs_map = {str(name).lower(): str(value or "") for name, value in attrs}
        if tag in _BLOCK_TAGS:
            self.text_parts.append("\n")

        if tag == "meta":
            key = (
                attrs_map.get("property")
                or attrs_map.get("name")
            ).strip().lower()
            content = attrs_map.get("content", "").strip()
            if key and content and key not in self.meta:
                self.meta[key] = content
        elif tag == "link" and "canonical" in attrs_map.get("rel", "").lower():
            self.canonical_url = urljoin(self.base_url, attrs_map.get("href", ""))
        elif tag == "img":
            image = (
                attrs_map.get("data-src")
                or attrs_map.get("data-original")
                or attrs_map.get("src")
            )
            if image:
                absolute = urljoin(self.base_url, image)
                if not re.search(r"(?:logo|icon|loading|blank|spacer)", absolute, re.I):
                    self.image_urls.append(absolute)
        elif tag == "a":
            href = attrs_map.get("href", "").strip()
            if href:
                absolute = urljoin(self.base_url, href)
                parsed = urlparse(absolute)
                if parsed.scheme in {"http", "https"} and parsed.netloc:
                    if parsed.netloc.lower() not in {
                        "www.huashan1914.com",
                        "huashan1914.com",
                        "media.huashan1914.com",
                    }:
                        self.external_urls.append(absolute)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in _BLOCK_TAGS:
            self.text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if data:
            self.text_parts.append(data)

    def lines(self) -> list[str]:
        text = "".join(self.text_parts).replace("\xa0", " ")
        return [
            _normalize_space(line)
            for line in re.split(r"[\r\n]+", text)
            if _normalize_space(line)
        ]


def _values_after_label(
    lines: Sequence[str],
    label: str,
    *,
    maximum: int = 8,
) -> list[str]:
    for index, line in enumerate(lines):
        if line != label and not line.startswith(label + "："):
            continue
        inline = line.split("：", 1)[1].strip() if "：" in line else ""
        values = [inline] if inline else []
        for candidate in lines[index + 1: index + 1 + maximum]:
            if candidate in _STOP_LABELS or candidate.startswith("######"):
                break
            if candidate.startswith("#"):
                continue
            values.append(candidate)
        return _unique(values)
    return []


def _extract_price_lines(lines: Sequence[str]) -> list[str]:
    values: list[str] = []
    for index, line in enumerate(lines):
        if _PRICE_SIGNAL_RE.search(line):
            values.append(line)
            if re.search(r"票價|門票", line) and index + 1 < len(lines):
                next_line = lines[index + 1]
                if len(next_line) <= 240 and next_line not in _STOP_LABELS:
                    values.append(next_line)
    return _unique(values)[:8]


def _classify_admission(price_text: str, full_text: str) -> str:
    combined = f"{price_text} {full_text}"
    if re.search(r"免費入場|免費參觀|自由入場|免票", combined):
        return "free"
    if re.search(r"售票制|NTD\s*\d|NT\$\s*\d|\d[\d,]*\s*元|全票|優待票|愛心票", combined, re.I):
        return "paid"
    return "unknown"


def _description_from_lines(lines: Sequence[str], title: str) -> str:
    start = -1
    for index, line in enumerate(lines):
        if line == "Image" or (title and line == title):
            start = index + 1
    if start < 0:
        return ""
    paragraphs: list[str] = []
    for line in lines[start:]:
        if line in {"相關活動", "如何來華山"}:
            break
        if line in _STOP_LABELS or line == title:
            continue
        if re.match(r"^\d{4}[./-]", line):
            continue
        paragraphs.append(line)
        if sum(len(value) for value in paragraphs) >= 900:
            break
    return _normalize_space(" ".join(paragraphs))[:1200]


class Huashan1914Collector(BaseCollector):
    source_id = "huashan-1914"
    source_name = HUASHAN_VENUE_NAME
    source_kind = SourceKind.HTML
    max_pages = 10

    def __init__(
        self,
        *,
        fetch_details: bool | None = None,
        detail_limit: int | None = None,
    ) -> None:
        self.fetch_details = (
            _truthy_env("EXHIBITION_HUB_HUASHAN_FETCH_DETAILS")
            if fetch_details is None
            else bool(fetch_details)
        )
        env_limit = os.getenv("EXHIBITION_HUB_HUASHAN_DETAIL_LIMIT", "0")
        self.detail_limit = (
            max(0, int(env_limit or 0))
            if detail_limit is None
            else max(0, int(detail_limit))
        )
        self.last_listing_pages = 0
        self.last_detail_requested = 0
        self.last_detail_success = 0
        self.last_detail_failures: list[str] = []

    @classmethod
    def parse_listing(
        cls,
        html: str,
        *,
        base_url: str = DEFAULT_LISTING_URL,
    ) -> tuple[list[dict[str, Any]], int]:
        parser = _HuashanListingParser(base_url)
        parser.feed(html)
        parser.close()
        return parser.events, parser.total_pages()

    @classmethod
    def parse_detail(
        cls,
        html: str,
        *,
        detail_url: str,
        listing: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        listing = dict(listing or {})
        parser = _HuashanDetailParser(detail_url)
        parser.feed(html)
        parser.close()
        lines = parser.lines()
        full_text = " ".join(lines)

        title = _clean_page_title(
            parser.meta.get("og:title")
            or parser.meta.get("twitter:title")
            or str(listing.get("title") or "")
        )
        description = _normalize_space(
            parser.meta.get("og:description")
            or parser.meta.get("description")
        )
        if not description or "華山1914" in description and len(description) < 80:
            description = _description_from_lines(lines, title)

        organizers = _values_after_label(lines, "主辦單位")
        venues = _values_after_label(lines, "活動地點")
        source_category = next(
            (value for value in _KNOWN_ACTIVITY_TYPES if value in lines or value in full_text[:1200]),
            "",
        )

        time_match = _TIME_RE.search(full_text)
        start_time = ""
        end_time = ""
        time_text = ""
        if time_match:
            start_time = _normalize_time(time_match.group("start"), time_match.group("start_ampm"))
            end_time = _normalize_time(time_match.group("end"), time_match.group("end_ampm"))
            time_text = _normalize_space(time_match.group(0))

        price_lines = _extract_price_lines(lines)
        price_text = _normalize_space(" / ".join(price_lines))
        admission = _classify_admission(price_text, full_text)

        meta_image = (
            parser.meta.get("og:image")
            or parser.meta.get("twitter:image")
            or ""
        )
        images = _unique([
            urljoin(detail_url, meta_image) if meta_image else "",
            *parser.image_urls,
            str(listing.get("imageUrl") or ""),
        ])

        external_urls = _unique(parser.external_urls)
        canonical = parser.canonical_url or detail_url
        editorial_status = "exclude_review" if source_category == "論壇講座" else "candidate"

        return {
            **listing,
            "title": title or str(listing.get("title") or ""),
            "detailUrl": canonical,
            "officialUrl": canonical,
            "startDate": str(listing.get("startDate") or ""),
            "endDate": str(listing.get("endDate") or ""),
            "startTime": start_time,
            "endTime": end_time,
            "timeText": time_text,
            "sourceCategory": source_category,
            "contentTypeHint": _content_type_hint(source_category, title),
            "organizer": organizers[0] if organizers else "",
            "organizers": organizers,
            "venueName": HUASHAN_VENUE_NAME,
            "venueNames": venues,
            "address": HUASHAN_ADDRESS,
            "regionCanonical": HUASHAN_REGION,
            "admission": admission,
            "priceText": price_text,
            "imageUrl": images[0] if images else "",
            "imageUrls": images,
            "description": description,
            "externalUrls": external_urls,
            "editorialStatus": editorial_status,
            "detailFetched": True,
        }

    def collect_raw(
        self,
        source: CollectorSource,
        client: Any,
    ) -> Sequence[Mapping[str, Any]]:
        listing_url = source.listing_url or DEFAULT_LISTING_URL
        records_by_url: dict[str, dict[str, Any]] = {}
        total_pages = 1
        self.last_listing_pages = 0
        self.last_detail_requested = 0
        self.last_detail_success = 0
        self.last_detail_failures = []

        for page in range(1, self.max_pages + 1):
            if page > total_pages:
                break
            page_url = _with_page_index(listing_url, page)
            response = client.get(page_url)
            self.last_listing_pages += 1
            events, detected_total = self.parse_listing(
                response.text,
                base_url=response.url or page_url,
            )
            total_pages = min(self.max_pages, max(total_pages, detected_total))

            new_count = 0
            for event in events:
                event["listingPage"] = page
                event["listingUrl"] = page_url
                detail_url = str(event["detailUrl"])
                if detail_url not in records_by_url:
                    records_by_url[detail_url] = event
                    new_count += 1
            if not events or (page > 1 and new_count == 0):
                break

        records = list(records_by_url.values())
        if not self.fetch_details:
            return records

        selected = records[: self.detail_limit or None]
        self.last_detail_requested = len(selected)
        enriched_by_url: dict[str, dict[str, Any]] = {
            str(record["detailUrl"]): record for record in records
        }
        for record in selected:
            detail_url = str(record["detailUrl"])
            try:
                response = client.get(detail_url)
                enriched_by_url[detail_url] = self.parse_detail(
                    response.text,
                    detail_url=response.url or detail_url,
                    listing=record,
                )
                self.last_detail_success += 1
            except Exception as exc:
                self.last_detail_failures.append(
                    f"{record.get('sourceEventId')}: {type(exc).__name__}: {exc}"
                )
                record["detailFetched"] = False
                record["detailError"] = f"{type(exc).__name__}: {exc}"
        return [enriched_by_url[str(record["detailUrl"])] for record in records]

    def normalize_record(
        self,
        source: CollectorSource,
        raw: Mapping[str, Any],
    ) -> CollectorRecord:
        return CollectorRecord(
            source_id=source.id,
            source_event_id=str(raw.get("sourceEventId") or ""),
            title=str(raw.get("title") or ""),
            detail_url=str(raw.get("detailUrl") or ""),
            raw=dict(raw),
        )

    def run(self, source: CollectorSource, client: Any) -> CollectorRunReport:
        report = super().run(source, client)
        report.fetched_pages = self.last_listing_pages + self.last_detail_requested
        detail_records = [record.raw for record in report.records if record.raw.get("detailFetched")]
        report.metrics = {
            "listingPagesFetched": self.last_listing_pages,
            "detailEnabled": self.fetch_details,
            "detailLimit": self.detail_limit,
            "detailRequestedCount": self.last_detail_requested,
            "detailSuccessCount": self.last_detail_success,
            "detailFailureCount": len(self.last_detail_failures),
            "detailCoverage": {
                "image": sum(bool(item.get("imageUrl")) for item in detail_records),
                "organizer": sum(bool(item.get("organizer")) for item in detail_records),
                "venue": sum(bool(item.get("venueNames")) for item in detail_records),
                "sourceCategory": sum(bool(item.get("sourceCategory")) for item in detail_records),
                "admissionKnown": sum(item.get("admission") in {"free", "paid"} for item in detail_records),
                "description": sum(bool(item.get("description")) for item in detail_records),
            },
        }
        if self.last_detail_failures:
            report.status = "partial" if report.records else "failed"
            report.warnings.extend(self.last_detail_failures)
        if report.success and not report.records:
            report.status = "partial"
            report.warnings.append("Huashan listing returned no event records")
        return report
