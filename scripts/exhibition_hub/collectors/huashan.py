from __future__ import annotations

from html.parser import HTMLParser
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

_DETAIL_PATH_RE = re.compile(
    r"^/w/huashan1914/(?:exhibition|event)_[A-Za-z0-9_-]+/?$",
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
        attrs_map = {
            str(name).lower(): value
            for name, value in attrs
        }

        if self._anchor is not None:
            if tag.lower() == "img":
                image = (
                    attrs_map.get("data-src")
                    or attrs_map.get("data-original")
                    or attrs_map.get("src")
                    or ""
                )
                if image and not self._anchor.get("imageUrl"):
                    self._anchor["imageUrl"] = urljoin(
                        self.base_url,
                        image,
                    )
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
        if self._anchor is None:
            return

        if tag.lower() != "a":
            return

        event = self._parse_anchor(self._anchor)
        if event is not None:
            self.events.append(event)
        self._anchor = None

    @staticmethod
    def _parse_anchor(
        anchor: Mapping[str, Any],
    ) -> dict[str, Any] | None:
        text = _normalize_space(
            " ".join(anchor.get("textParts") or [])
        )
        date_match = _DATE_PAIR_RE.search(text)
        if date_match is None:
            return None

        remainder = _normalize_space(text[date_match.end():])
        category_match = _LISTING_CATEGORY_RE.match(remainder)
        listing_category = ""
        if category_match is not None:
            listing_category = category_match.group("category")
            remainder = _normalize_space(
                remainder[category_match.end():]
            )

        if not remainder:
            return None

        detail_url = str(anchor.get("detailUrl") or "")
        source_event_id = urlparse(detail_url).path.rstrip("/").split("/")[-1]

        return {
            "sourceEventId": source_event_id,
            "title": remainder,
            "startDate": _normalize_date(
                date_match.group("start")
            ),
            "endDate": _normalize_date(
                date_match.group("end")
            ),
            "listingCategory": listing_category,
            "detailUrl": detail_url,
            "imageUrl": str(anchor.get("imageUrl") or ""),
            "listingText": text,
        }

    def total_pages(self) -> int:
        text = " ".join(self.page_text)
        match = _PAGE_COUNT_RE.search(text)
        if match is None:
            return 1
        return max(1, int(match.group("total")))


class Huashan1914Collector(BaseCollector):
    source_id = "huashan-1914"
    source_name = "華山1914文化創意產業園區"
    source_kind = SourceKind.HTML
    max_pages = 10

    def __init__(self) -> None:
        self.last_fetched_pages = 0

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

    def collect_raw(
        self,
        source: CollectorSource,
        client: Any,
    ) -> Sequence[Mapping[str, Any]]:
        listing_url = (
            source.listing_url
            or DEFAULT_LISTING_URL
        )
        records_by_url: dict[str, dict[str, Any]] = {}
        total_pages = 1
        self.last_fetched_pages = 0

        for page in range(1, self.max_pages + 1):
            if page > total_pages:
                break

            page_url = _with_page_index(listing_url, page)
            response = client.get(page_url)
            self.last_fetched_pages += 1
            events, detected_total = self.parse_listing(
                response.text,
                base_url=response.url or page_url,
            )
            total_pages = min(
                self.max_pages,
                max(total_pages, detected_total),
            )

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

        return list(records_by_url.values())

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

    def run(
        self,
        source: CollectorSource,
        client: Any,
    ) -> CollectorRunReport:
        report = super().run(source, client)
        report.fetched_pages = self.last_fetched_pages
        if report.success and not report.records:
            report.status = "partial"
            report.warnings.append(
                "Huashan listing returned no event records"
            )
        return report
