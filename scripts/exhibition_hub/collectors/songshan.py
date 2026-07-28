from __future__ import annotations

from html.parser import HTMLParser
import os
import re
from typing import Any, Mapping, Sequence
from urllib.parse import parse_qsl, urljoin, urlparse

from .base import (
    BaseCollector,
    CollectorRecord,
    CollectorRunReport,
    CollectorSource,
    SourceKind,
)


DEFAULT_LISTING_URL = "https://www.songshanculturalpark.org/exhibition"
SONGSHAN_VENUE_NAME = "松山文創園區"
SONGSHAN_ADDRESS = "臺北市信義區光復南路133號"
SONGSHAN_REGION = "臺北市"

_DETAIL_PATH_RE = re.compile(
    r"^/exhibition/activity/(?P<id>[0-9a-f-]{20,})/?$",
    re.IGNORECASE,
)
_DATE_RANGE_RE = re.compile(
    r"(?P<start>\d{4}[./-]\d{1,2}[./-]\d{1,2})"
    r"\s*(?:-|–|—|~|～|至)\s*"
    r"(?P<end>\d{4}[./-]\d{1,2}[./-]\d{1,2})"
)
_TIME_RE = re.compile(
    r"(?P<start>\d{1,2}[：:]\d{2})\s*(?:-|－|–|—|~|～|至)\s*"
    r"(?P<end>\d{1,2}[：:]\d{2})"
)
_PRICE_RE = re.compile(
    r"(?:NT\$?|新臺幣|新台幣|票價|門票|售票|全票|優惠票|優待票|"
    r"早鳥票|現場票|\d[\d,]*\s*元)",
    re.IGNORECASE,
)
_FREE_RE = re.compile(
    r"(?:免費入場|免費參觀|自由入場|免票|免費)",
    re.IGNORECASE,
)
_PAID_RE = re.compile(
    r"(?:售票|購票|票價|門票|全票|優惠票|優待票|早鳥票|"
    r"NT\$?|\d[\d,]*\s*元)",
    re.IGNORECASE,
)
_EXCLUDE_TITLE_RE = re.compile(
    r"(?:"
    r"松山文創園區\s*[-–—]?\s*\d{1,2}\s*月展演攻略|"
    r"課程|講座|論壇|工作坊|營隊|夏令營|培力|研習|講習|徵件|招募|"
    r"說明會|讀書會|導覽培訓|人才培訓"
    r")",
    re.IGNORECASE,
)
_IGNORED_TAGS = {"script", "style", "noscript", "svg", "template"}
_BLOCK_TAGS = {
    "article", "aside", "br", "dd", "div", "dl", "dt", "figcaption",
    "footer", "h1", "h2", "h3", "h4", "h5", "h6", "header", "li",
    "main", "p", "section", "td", "th", "tr", "ul", "ol",
}
_STOP_DESCRIPTION_LINES = {
    "首頁", "展演資訊", "精選活動", "展演活動", "加入行事曆", "Image",
    "看更多", "園區資訊", "戶外空間 24 小時開放", "日期", "地點",
    "活動資訊", "活動資訊｜", "票務資訊", "票務資訊｜",
    "展覽資訊", "Exhibition Info",
}
_IMAGE_REJECT_RE = re.compile(
    r"(?:logo|favicon|icon|loading|spinner|placeholder|avatar|arrow|"
    r"google|facebook|line|instagram|youtube|header|footer|map|share)",
    re.IGNORECASE,
)
_EXTERNAL_REJECT_HOST_RE = re.compile(
    r"(?:facebook\.com|instagram\.com|line\.me|youtube\.com|youtu\.be|"
    r"google\.com|calendar\.google\.com)",
    re.IGNORECASE,
)


def _normalize_space(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _normalize_date(value: Any) -> str:
    text = str(value or "").strip().replace(".", "-").replace("/", "-")
    match = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", text)
    if not match:
        return ""
    return f"{int(match.group(1)):04d}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"


def _normalize_time(value: Any) -> str:
    text = str(value or "").strip().replace("：", ":")
    match = re.match(r"^(\d{1,2}):(\d{2})$", text)
    if not match:
        return ""
    return f"{int(match.group(1)):02d}:{match.group(2)}"


def _unique(values: Sequence[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _normalize_space(value)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _is_detail_url(url: str) -> bool:
    parsed = urlparse(url)
    return (
        parsed.netloc.lower() in {
            "songshanculturalpark.org",
            "www.songshanculturalpark.org",
        }
        and bool(_DETAIL_PATH_RE.match(parsed.path))
    )


def _source_event_id(url: str) -> str:
    match = _DETAIL_PATH_RE.match(urlparse(url).path)
    return match.group("id") if match else ""


def _clean_page_title(value: str) -> str:
    title = _normalize_space(value)
    title = re.sub(
        r"\s*[-｜|]\s*(?:展演資訊\s*[-｜|]\s*)?松山文創園區\s*$",
        "",
        title,
        flags=re.IGNORECASE,
    )
    return title


def _clean_images(values: Sequence[str], base_url: str) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        raw_value = str(value or "").strip()
        if not raw_value:
            continue
        absolute = urljoin(base_url, raw_value)
        parsed = urlparse(absolute)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            continue
        if _IMAGE_REJECT_RE.search(parsed.path):
            continue
        lowered = absolute.lower()
        if lowered.endswith((".svg", ".gif")) or lowered.startswith("data:"):
            continue
        normalized = parsed._replace(fragment="").geturl()
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
        if len(result) >= 4:
            break
    return result


def _clean_external_urls(values: Sequence[str], base_url: str) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    base_host = urlparse(base_url).netloc.lower().removeprefix("www.")
    for value in values:
        absolute = urljoin(base_url, str(value or "").strip())
        parsed = urlparse(absolute)
        host = parsed.netloc.lower().removeprefix("www.")
        if parsed.scheme not in {"http", "https"} or not host:
            continue
        if host == base_host or _EXTERNAL_REJECT_HOST_RE.search(host):
            continue
        normalized = parsed._replace(fragment="").geturl()
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result[:8]


def _content_type_hint(title: str, text: str) -> str:
    haystack = f"{title} {text}"
    if re.search(r"快閃|POP[ -]?UP|限定店", haystack, re.IGNORECASE):
        return "快閃店"
    if re.search(r"市集|MARKET|祭典|文創節", haystack, re.IGNORECASE):
        return "市集"
    if re.search(r"演唱會|音樂祭|LIVE\b|CONCERT", haystack, re.IGNORECASE):
        return "演唱會"
    if re.search(r"舞蹈|劇場|戲劇|音樂會|演出|表演", haystack, re.IGNORECASE):
        return "表演"
    if re.search(r"動漫|漫畫|動畫|角色|公仔|遊戲|伊藤潤二|哆啦|小丸子|PEANUTS", haystack, re.IGNORECASE):
        return "動漫"
    if re.search(r"設計|DESIGN|iF\b", haystack, re.IGNORECASE):
        return "設計"
    if re.search(r"攝影|PHOTO", haystack, re.IGNORECASE):
        return "攝影"
    if re.search(r"藝術|美術|插畫|原畫|畫作|個展|聯展|作品展", haystack, re.IGNORECASE):
        return "美術"
    if re.search(r"親子|兒童|小朋友", haystack, re.IGNORECASE):
        return "親子"
    return "其他"


def _admission(price_text: str, full_text: str, external_urls: Sequence[str]) -> str:
    if _PAID_RE.search(price_text):
        return "paid"
    if _FREE_RE.search(price_text):
        return "free"
    if _PAID_RE.search(full_text) or any(
        re.search(r"ticket|tix|kktix|ibon|fami", url, re.IGNORECASE)
        for url in external_urls
    ):
        return "paid"
    if _FREE_RE.search(full_text):
        return "free"
    return "unknown"


class _SongshanListingParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.events: list[dict[str, Any]] = []
        self.pagination_urls: list[str] = []
        self._anchor: dict[str, Any] | None = None
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attrs_map = {str(name).lower(): str(value or "") for name, value in attrs}
        if tag in _IGNORED_TAGS:
            self._ignored_depth += 1
            return
        if self._ignored_depth:
            return

        if self._anchor is not None:
            if tag == "img":
                image = (
                    attrs_map.get("data-src")
                    or attrs_map.get("data-original")
                    or attrs_map.get("src")
                )
                alt = attrs_map.get("alt", "")
                if image and not self._anchor.get("imageUrl"):
                    self._anchor["imageUrl"] = urljoin(self.base_url, image)
                if alt:
                    self._anchor["attributeText"].append(alt)
            return

        if tag != "a":
            return
        href = attrs_map.get("href", "").strip()
        if not href:
            return
        absolute = urljoin(self.base_url, href)
        if _is_detail_url(absolute):
            self._anchor = {
                "detailUrl": absolute,
                "textParts": [],
                "attributeText": [
                    attrs_map.get("title", ""),
                    attrs_map.get("aria-label", ""),
                ],
                "imageUrl": "",
            }
            return

        parsed = urlparse(absolute)
        if (
            parsed.netloc.lower().removeprefix("www.")
            == urlparse(self.base_url).netloc.lower().removeprefix("www.")
            and parsed.path.rstrip("/") == "/exhibition"
            and any(key.lower() in {"page", "p"} for key, _ in parse_qsl(parsed.query))
        ):
            self.pagination_urls.append(absolute)

    def handle_data(self, data: str) -> None:
        if self._ignored_depth or self._anchor is None:
            return
        text = _normalize_space(data)
        if text:
            self._anchor["textParts"].append(text)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in _IGNORED_TAGS and self._ignored_depth:
            self._ignored_depth -= 1
            return
        if self._ignored_depth or self._anchor is None or tag != "a":
            return
        event = self._parse_anchor(self._anchor)
        if event:
            self.events.append(event)
        self._anchor = None

    @staticmethod
    def _parse_anchor(anchor: Mapping[str, Any]) -> dict[str, Any] | None:
        parts = _unique([
            *(anchor.get("textParts") or []),
            *(anchor.get("attributeText") or []),
        ])
        cleaned = [
            part for part in parts
            if part not in {"Image", "看更多", "加入行事曆"}
        ]
        joined = _normalize_space(" ".join(cleaned))
        date_match = _DATE_RANGE_RE.search(joined)
        start_date = _normalize_date(date_match.group("start")) if date_match else ""
        end_date = _normalize_date(date_match.group("end")) if date_match else ""

        title = ""
        for part in cleaned:
            if _DATE_RANGE_RE.fullmatch(part):
                continue
            if re.fullmatch(r"\d{4}[./-]\d{1,2}[./-]\d{1,2}", part):
                continue
            if len(part) >= 2:
                title = part
                break
        if date_match and (not title or title in date_match.group(0)):
            remainder = _normalize_space(joined[date_match.end():])
            title = remainder.split(" 看更多", 1)[0].strip()
        title = _clean_page_title(title)
        detail_url = str(anchor.get("detailUrl") or "")
        source_event_id = _source_event_id(detail_url)
        if not source_event_id or not title:
            return None
        return {
            "sourceEventId": source_event_id,
            "title": title,
            "startDate": start_date,
            "endDate": end_date,
            "detailUrl": detail_url,
            "imageUrl": str(anchor.get("imageUrl") or ""),
            "listingText": joined,
        }


class _SongshanDetailParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.text_parts: list[str] = []
        self.meta: dict[str, str] = {}
        self.images: list[str] = []
        self.links: list[str] = []
        self.canonical_url = ""
        self.h1_parts: list[str] = []
        self._ignored_depth = 0
        self._h1_depth = 0
        self._main_started = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attrs_map = {str(name).lower(): str(value or "") for name, value in attrs}
        if tag in _IGNORED_TAGS:
            self._ignored_depth += 1
            return
        if self._ignored_depth:
            return
        if tag in _BLOCK_TAGS:
            self.text_parts.append("\n")
        if tag == "h1":
            self._h1_depth += 1
            self._main_started = True
        elif tag == "meta":
            key = (attrs_map.get("property") or attrs_map.get("name") or "").strip().lower()
            content = attrs_map.get("content", "").strip()
            if key and content and key not in self.meta:
                self.meta[key] = content
        elif tag == "link" and "canonical" in attrs_map.get("rel", "").lower():
            self.canonical_url = urljoin(self.base_url, attrs_map.get("href", ""))
        elif tag == "img" and self._main_started:
            image = (
                attrs_map.get("data-src")
                or attrs_map.get("data-original")
                or attrs_map.get("src")
            )
            if image:
                self.images.append(urljoin(self.base_url, image))
        elif tag == "a" and self._main_started:
            href = attrs_map.get("href", "").strip()
            if href:
                self.links.append(urljoin(self.base_url, href))

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        text = _normalize_space(data)
        if not text:
            return
        self.text_parts.append(text)
        if self._h1_depth:
            self.h1_parts.append(text)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in _IGNORED_TAGS and self._ignored_depth:
            self._ignored_depth -= 1
            return
        if self._ignored_depth:
            return
        if tag == "h1" and self._h1_depth:
            self._h1_depth -= 1
        if tag in _BLOCK_TAGS:
            self.text_parts.append("\n")

    def lines(self) -> list[str]:
        text = " ".join(self.text_parts).replace(" \n ", "\n")
        return _unique(
            _normalize_space(line)
            for line in text.splitlines()
        )


def _main_lines(lines: Sequence[str], title: str) -> list[str]:
    if title not in lines:
        return list(lines)
    start = list(lines).index(title)
    result: list[str] = []
    for line in lines[start:]:
        if line == "園區資訊":
            break
        result.append(line)
    return result or list(lines)


def _date_after_label(lines: Sequence[str]) -> tuple[str, str]:
    for index, line in enumerate(lines):
        candidates = [line, *lines[index + 1:index + 3]] if line == "日期" else [line]
        for candidate in candidates:
            match = _DATE_RANGE_RE.search(candidate)
            if match:
                return _normalize_date(match.group("start")), _normalize_date(match.group("end"))
    return "", ""


def _value_after_label(lines: Sequence[str], label: str, *, maximum: int = 2) -> list[str]:
    result: list[str] = []
    for index, line in enumerate(lines):
        if line == label or line.startswith(label + "｜") or line.startswith(label + ":") or line.startswith(label + "："):
            inline = re.sub(rf"^{re.escape(label)}\s*[｜:：]?\s*", "", line).strip()
            if inline:
                result.append(inline)
            for value in lines[index + 1:index + 1 + maximum]:
                if value in _STOP_DESCRIPTION_LINES or value in {"日期", "地點"}:
                    break
                if value and not _DATE_RANGE_RE.fullmatch(value):
                    result.append(value)
            break
    return _unique(result)


def _description(lines: Sequence[str], title: str) -> str:
    result: list[str] = []
    started = False
    for line in lines:
        if line == title:
            started = True
            continue
        if not started:
            continue
        if line == "園區資訊":
            break
        if line in _STOP_DESCRIPTION_LINES:
            continue
        if _DATE_RANGE_RE.fullmatch(line) or line.startswith(("ADD|", "TEL|", "FAX|")):
            continue
        if line.startswith((
            "活動名稱：", "活動日期：", "活動時間：", "活動地點：",
            "活動日期｜", "活動時間｜", "活動地點｜", "主辦單位｜",
            "展覽名稱｜", "展覽地點｜", "展覽期間｜", "開放時間｜",
            "展覽票價｜", "共同主辦單位｜", "執行單位｜", "策展人｜",
            "Venue｜", "Dates｜", "Time｜", "Admission｜", "Organizers｜",
        )):
            continue
        if len(line) < 3:
            continue
        result.append(line)
        if sum(len(item) for item in result) >= 1000:
            break
    return _normalize_space(" ".join(result))[:1200]


def _price_text(lines: Sequence[str]) -> str:
    result: list[str] = []
    for line in lines:
        if _PRICE_RE.search(line) or _FREE_RE.search(line):
            if len(line) <= 180:
                result.append(line)
    return _normalize_space(" / ".join(_unique(result[:4])))


class SongshanCulturalParkCollector(BaseCollector):
    source_id = "songshan-cultural-park"
    source_name = SONGSHAN_VENUE_NAME
    source_kind = SourceKind.HTML
    max_pages = 8

    def __init__(
        self,
        *,
        fetch_details: bool | None = None,
        detail_limit: int | None = None,
    ) -> None:
        self.fetch_details = (
            str(os.getenv("EXHIBITION_HUB_FETCH_DETAILS", "")).lower()
            in {"1", "true", "yes", "on"}
            if fetch_details is None
            else bool(fetch_details)
        )
        env_limit = os.getenv("EXHIBITION_HUB_DETAIL_LIMIT", "0")
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
    ) -> tuple[list[dict[str, Any]], list[str]]:
        parser = _SongshanListingParser(base_url)
        parser.feed(html)
        parser.close()
        events_by_id: dict[str, dict[str, Any]] = {}
        for event in parser.events:
            event_id = str(event.get("sourceEventId") or "")
            if event_id and event_id not in events_by_id:
                events_by_id[event_id] = event
        return list(events_by_id.values()), _unique(parser.pagination_urls)

    @classmethod
    def parse_detail(
        cls,
        html: str,
        *,
        detail_url: str,
        listing: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        listing = dict(listing or {})
        parser = _SongshanDetailParser(detail_url)
        parser.feed(html)
        parser.close()
        lines = parser.lines()

        title = _clean_page_title(
            parser.meta.get("og:title")
            or parser.meta.get("twitter:title")
            or _normalize_space(" ".join(parser.h1_parts))
            or str(listing.get("title") or "")
        )
        main_lines = _main_lines(lines, title)
        full_text = _normalize_space(" ".join(main_lines))
        start_date = str(listing.get("startDate") or "")
        end_date = str(listing.get("endDate") or "")
        if not start_date or not end_date:
            parsed_start, parsed_end = _date_after_label(main_lines)
            start_date = start_date or parsed_start
            end_date = end_date or parsed_end

        venues = _value_after_label(main_lines, "地點", maximum=1)
        organizers = _value_after_label(main_lines, "主辦單位", maximum=1)
        time_match = _TIME_RE.search(full_text)
        start_time = _normalize_time(time_match.group("start")) if time_match else ""
        end_time = _normalize_time(time_match.group("end")) if time_match else ""
        time_text = (
            f"{start_time}–{end_time}"
            if start_time and end_time
            else ""
        )

        price_text = _price_text(main_lines)
        external_urls = _clean_external_urls(parser.links, detail_url)
        admission = _admission(price_text, full_text, external_urls)
        meta_image = parser.meta.get("og:image") or parser.meta.get("twitter:image") or ""
        images = _clean_images(
            [meta_image, str(listing.get("imageUrl") or ""), *parser.images],
            detail_url,
        )
        description = _normalize_space(
            parser.meta.get("og:description")
            or parser.meta.get("description")
        )
        if not description or len(description) < 40 or "松山文創園區" in description and len(description) < 90:
            description = _description(main_lines, title)

        canonical = parser.canonical_url or detail_url
        hint = _content_type_hint(title, full_text[:3000])
        editorial_status = (
            "exclude_review"
            if _EXCLUDE_TITLE_RE.search(title)
            else "candidate"
        )

        return {
            **listing,
            "title": title or str(listing.get("title") or ""),
            "detailUrl": canonical,
            "officialUrl": canonical,
            "startDate": start_date,
            "endDate": end_date,
            "startTime": start_time,
            "endTime": end_time,
            "timeText": time_text,
            "sourceCategory": "展演活動",
            "contentTypeHint": hint,
            "organizer": organizers[0] if organizers else "",
            "organizers": organizers,
            "venueName": SONGSHAN_VENUE_NAME,
            "venueNames": venues,
            "address": SONGSHAN_ADDRESS,
            "regionCanonical": SONGSHAN_REGION,
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
        queue = [listing_url]
        visited: set[str] = set()
        records_by_id: dict[str, dict[str, Any]] = {}
        self.last_listing_pages = 0
        self.last_detail_requested = 0
        self.last_detail_success = 0
        self.last_detail_failures = []

        while queue and len(visited) < self.max_pages:
            page_url = queue.pop(0)
            if page_url in visited:
                continue
            visited.add(page_url)
            response = client.get(page_url)
            self.last_listing_pages += 1
            events, pagination = self.parse_listing(
                response.text,
                base_url=response.url or page_url,
            )
            for event in events:
                event_id = str(event.get("sourceEventId") or "")
                event["listingUrl"] = page_url
                if event_id and event_id not in records_by_id:
                    records_by_id[event_id] = event
            for next_url in pagination:
                if next_url not in visited and next_url not in queue:
                    queue.append(next_url)

        records = list(records_by_id.values())
        if not self.fetch_details:
            return records

        selected = records[: self.detail_limit or None]
        self.last_detail_requested = len(selected)
        enriched = {str(item["sourceEventId"]): item for item in records}
        for record in selected:
            source_event_id = str(record.get("sourceEventId") or "")
            detail_url = str(record.get("detailUrl") or "")
            try:
                response = client.get(detail_url)
                enriched[source_event_id] = self.parse_detail(
                    response.text,
                    detail_url=response.url or detail_url,
                    listing=record,
                )
                self.last_detail_success += 1
            except Exception as exc:
                self.last_detail_failures.append(
                    f"{source_event_id}: {type(exc).__name__}: {exc}"
                )
                record["detailFetched"] = False
                record["detailError"] = f"{type(exc).__name__}: {exc}"
        return [enriched[str(item["sourceEventId"])] for item in records]

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
        detail_records = [record.raw for record in report.records if record.raw.get("detailFetched")]
        report.fetched_pages = self.last_listing_pages + self.last_detail_requested
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
                "admissionKnown": sum(item.get("admission") in {"free", "paid"} for item in detail_records),
                "description": sum(bool(item.get("description")) for item in detail_records),
            },
            "excludedReviewCount": sum(
                record.raw.get("editorialStatus") == "exclude_review"
                for record in report.records
            ),
        }
        if self.last_detail_failures:
            report.status = "partial" if report.records else "failed"
            report.warnings.extend(self.last_detail_failures)
        if report.success and not report.records:
            report.status = "partial"
            report.warnings.append("Songshan listing returned no event records")
        return report
