from __future__ import annotations

from html.parser import HTMLParser
import hashlib
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


_IGNORED_TAGS = {"script", "style", "noscript", "svg", "template"}
_BLOCK_TAGS = {
    "article", "aside", "br", "dd", "div", "dl", "dt", "figcaption",
    "footer", "h1", "h2", "h3", "h4", "h5", "h6", "header", "li",
    "main", "p", "section", "td", "th", "tr", "ul", "ol",
}
_IMAGE_REJECT_RE = re.compile(
    r"(?:logo|favicon|icon|loading|spinner|placeholder|avatar|arrow|"
    r"google|facebook|line|instagram|youtube|header|footer|map|share)",
    re.I,
)
_DEFAULT_EXCLUDE_RE = re.compile(
    r"取消|課程|講座|論壇|工作坊|營隊|夏令營|培力|研習|講習|徵件|"
    r"招募|說明會|讀書會|導覽培訓|人才培訓",
    re.I,
)
_RANGE_RE = re.compile(
    r"(?P<start>\d{4}\s*(?:年|[./-])\s*\d{1,2}\s*(?:月|[./-])\s*\d{1,2}\s*日?)"
    r"(?:\s*[（(][^）)]{1,5}[）)])?\s*(?:-|－|–|—|~|～|至)\s*"
    r"(?P<end>\d{4}\s*(?:年|[./-])\s*\d{1,2}\s*(?:月|[./-])\s*\d{1,2}\s*日?)",
    re.I,
)
_SINGLE_DATE_RE = re.compile(
    r"(?P<date>\d{4}\s*(?:年|[./-])\s*\d{1,2}\s*(?:月|[./-])\s*\d{1,2}\s*日?)",
    re.I,
)
_ROC_RANGE_RE = re.compile(
    r"(?P<start>\d{2,3}\s*(?:年|[./-])\s*\d{1,2}\s*(?:月|[./-])\s*\d{1,2}\s*日?)"
    r"(?:\s*[（(][^）)]{1,5}[）)])?\s*(?:-|－|–|—|~|～|至)\s*"
    r"(?P<end>\d{2,3}\s*(?:年|[./-])\s*\d{1,2}\s*(?:月|[./-])\s*\d{1,2}\s*日?)",
    re.I,
)
_ROC_SINGLE_DATE_RE = re.compile(
    r"(?P<date>\d{2,3}\s*(?:年|[./-])\s*\d{1,2}\s*(?:月|[./-])\s*\d{1,2}\s*日?)",
    re.I,
)
_TIME_RE = re.compile(
    r"(?P<start>\d{1,2}[：:]\d{2})\s*(?:-|－|–|—|~|～|至)\s*"
    r"(?P<end>\d{1,2}[：:]\d{2})"
)
_FREE_RE = re.compile(r"免費入場|免費參觀|自由入場|免票|免費", re.I)
_PAID_RE = re.compile(
    r"售票|購票|票價|門票|全票|優惠票|優待票|早鳥票|"
    r"NT\$?|新臺幣|新台幣|\d[\d,]*\s*元",
    re.I,
)


def _space(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _unique(values: Sequence[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _space(value)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _date(value: Any) -> str:
    text = str(value or "").strip()
    match = re.search(r"(\d{4})\s*(?:年|[./-])\s*(\d{1,2})\s*(?:月|[./-])\s*(\d{1,2})", text)
    if not match:
        return ""
    return f"{int(match.group(1)):04d}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"


def _dates(text: str) -> tuple[str, str]:
    match = _RANGE_RE.search(text)
    if match:
        return _date(match.group("start")), _date(match.group("end"))
    match = _SINGLE_DATE_RE.search(text)
    if match:
        value = _date(match.group("date"))
        return value, value
    return "", ""


def _roc_date(value: Any) -> str:
    """Convert a Minguo/ROC date such as 115-08-14 to 2026-08-14."""
    text = str(value or "").strip()
    match = re.search(
        r"(?<!\d)(\d{2,3})\s*(?:年|[./-])\s*(\d{1,2})\s*(?:月|[./-])\s*(\d{1,2})",
        text,
    )
    if not match:
        return ""
    year = int(match.group(1)) + 1911
    return f"{year:04d}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"


def _roc_dates(text: str) -> tuple[str, str]:
    match = _ROC_RANGE_RE.search(text)
    if match:
        return _roc_date(match.group("start")), _roc_date(match.group("end"))
    match = _ROC_SINGLE_DATE_RE.search(text)
    if match:
        value = _roc_date(match.group("date"))
        return value, value
    return "", ""


def _clean_images(values: Sequence[str], base_url: str) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        candidate = str(value or "").strip()
        if not candidate:
            continue
        absolute = urljoin(base_url, candidate)
        parsed = urlparse(absolute)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            continue
        if parsed.path.lower().endswith((".aspx", ".html", ".htm", ".php")):
            continue
        if _IMAGE_REJECT_RE.search(parsed.path):
            continue
        if parsed.path.lower().endswith((".svg", ".gif")):
            continue
        normalized = parsed._replace(fragment="").geturl()
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
        if len(result) >= 6:
            break
    return result


def _external_urls(values: Sequence[str], base_url: str) -> list[str]:
    base_host = urlparse(base_url).netloc.lower().removeprefix("www.")
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        absolute = urljoin(base_url, str(value or "").strip())
        parsed = urlparse(absolute)
        host = parsed.netloc.lower().removeprefix("www.")
        if parsed.scheme not in {"http", "https"} or not host or host == base_host:
            continue
        if re.search(r"facebook|instagram|youtube|youtu\.be|line\.me|google", host, re.I):
            continue
        normalized = parsed._replace(fragment="").geturl()
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result[:8]


def _hint(title: str, text: str) -> str:
    haystack = f"{title} {text}"
    if re.search(r"電影|影展|放映|紀錄片|短片", title, re.I):
        return "電影"
    if re.search(r"音樂劇|歌劇|舞台劇|劇場|戲劇|讀劇|偶戲|馬戲|脫口秀|相聲", title, re.I):
        return "表演"
    if re.search(r"舞蹈|舞作|芭蕾|現代舞|街舞", title, re.I):
        return "舞蹈"
    if re.search(r"演唱會|WORLD\s*TOUR|ASIA\s*TOUR|FAN\s*CONCERT|LIVE\s*TOUR", title, re.I):
        return "演唱會"
    if re.search(r"音樂會|交響|管弦|協奏|獨奏|重奏|室內樂|爵士|國樂|音樂祭|音樂節|LIVE\s*HOUSE", haystack, re.I):
        return "音樂"
    if re.search(r"快閃|POP[ -]?UP|期間限定", title, re.I):
        return "快閃店"
    if re.search(r"動漫|動畫展|漫畫|原畫展|ACG|角色展|公仔|模型|遊戲展|"
                 r"寶可夢|吉伊卡哇|櫻桃小丸子|哆啦A夢|航海王|鬼滅之刃|鋼彈", title, re.I):
        return "動漫"
    if re.search(r"市集|MARKET|展售", title, re.I):
        return "市集"
    if re.search(r"攝影|PHOTO", title, re.I):
        return "攝影"
    if re.search(r"設計|DESIGN|建築|工藝|時尚", haystack, re.I):
        return "設計"
    if re.search(r"歷史|文物|考古|古蹟|文化資產", haystack, re.I):
        return "歷史"
    if re.search(r"自然|生態|植物|動物|天文|地質|海洋", haystack, re.I):
        return "自然"
    if re.search(r"科技|AI|人工智慧|數位|機器人", haystack, re.I):
        return "科技"
    if re.search(r"親子|兒童|家庭", title, re.I):
        return "親子"
    if re.search(r"藝術|美術|繪畫|雕塑|裝置|當代|典藏|書畫|個展|聯展", haystack, re.I):
        return "美術"
    return "其他"


class _ListingParser(HTMLParser):
    def __init__(self, base_url: str, detail_patterns: Sequence[re.Pattern[str]]) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.detail_patterns = list(detail_patterns)
        self.records: list[dict[str, str]] = []
        self.pagination: list[str] = []
        self._anchor: dict[str, Any] | None = None
        self._ignored = 0

    def _is_detail(self, absolute: str) -> bool:
        path = urlparse(absolute).path
        return any(pattern.search(path) for pattern in self.detail_patterns)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr = {str(k).lower(): str(v or "") for k, v in attrs}
        if tag in _IGNORED_TAGS:
            self._ignored += 1
            return
        if self._ignored:
            return
        if self._anchor is not None:
            if tag == "img":
                image = attr.get("data-src") or attr.get("data-original") or attr.get("src")
                if image and not self._anchor.get("image"):
                    self._anchor["image"] = urljoin(self.base_url, image)
                if attr.get("alt"):
                    self._anchor["parts"].append(attr["alt"])
            return
        if tag != "a" or not attr.get("href"):
            return
        absolute = urljoin(self.base_url, attr["href"])
        parsed = urlparse(absolute)
        base = urlparse(self.base_url)
        if parsed.netloc.lower().removeprefix("www.") != base.netloc.lower().removeprefix("www."):
            return
        if self._is_detail(absolute):
            self._anchor = {
                "url": absolute,
                "parts": [attr.get("title", ""), attr.get("aria-label", "")],
                "image": "",
            }
        elif parsed.query and parsed.path.rstrip("/") == base.path.rstrip("/"):
            query_keys = {key.lower() for key, _ in parse_qsl(parsed.query)}
            if query_keys.intersection({"page", "pages", "p"}):
                self.pagination.append(absolute)

    def handle_data(self, data: str) -> None:
        if self._ignored or self._anchor is None:
            return
        text = _space(data)
        if text:
            self._anchor["parts"].append(text)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in _IGNORED_TAGS and self._ignored:
            self._ignored -= 1
            return
        if self._ignored or tag != "a" or self._anchor is None:
            return
        parts = _unique(self._anchor["parts"])
        joined = _space(" ".join(parts))
        title = next((part for part in parts if len(part) >= 2 and not _SINGLE_DATE_RE.fullmatch(part)), "")
        start, end = _dates(joined)
        self.records.append({
            "sourceEventId": hashlib.sha256(self._anchor["url"].encode("utf-8")).hexdigest()[:24],
            "title": title,
            "detailUrl": self._anchor["url"],
            "imageUrl": str(self._anchor.get("image") or ""),
            "startDate": start,
            "endDate": end,
            "listingText": joined,
        })
        self._anchor = None


class _DetailParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.meta: dict[str, str] = {}
        self.images: list[str] = []
        self.links: list[str] = []
        self.text: list[str] = []
        self.h1: list[str] = []
        self.canonical = ""
        self._ignored = 0
        self._h1 = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr = {str(k).lower(): str(v or "") for k, v in attrs}
        if tag in _IGNORED_TAGS:
            self._ignored += 1
            return
        if self._ignored:
            return
        if tag in _BLOCK_TAGS:
            self.text.append("\n")
        if tag == "h1":
            self._h1 += 1
        elif tag == "meta":
            key = (attr.get("property") or attr.get("name") or "").lower()
            content = attr.get("content", "").strip()
            if key and content and key not in self.meta:
                self.meta[key] = content
        elif tag == "link" and "canonical" in attr.get("rel", "").lower():
            self.canonical = urljoin(self.base_url, attr.get("href", ""))
        elif tag == "img":
            image = attr.get("data-src") or attr.get("data-original") or attr.get("src")
            if image:
                self.images.append(urljoin(self.base_url, image))
        elif tag == "a" and attr.get("href"):
            self.links.append(urljoin(self.base_url, attr["href"]))

    def handle_data(self, data: str) -> None:
        if self._ignored:
            return
        text = _space(data)
        if not text:
            return
        self.text.append(text)
        if self._h1:
            self.h1.append(text)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in _IGNORED_TAGS and self._ignored:
            self._ignored -= 1
            return
        if self._ignored:
            return
        if tag == "h1" and self._h1:
            self._h1 -= 1
        if tag in _BLOCK_TAGS:
            self.text.append("\n")

    def full_text(self) -> str:
        return _space(" ".join(self.text))


class _TwtcListingParser(HTMLParser):
    """Parse the official TWTC Hall 1 schedule without mixing other halls."""

    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.records: list[dict[str, str]] = []
        self._row: list[dict[str, Any]] | None = None
        self._cell: dict[str, Any] | None = None
        self._anchor: dict[str, Any] | None = None
        self._ignored = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr = {str(k).lower(): str(v or "") for k, v in attrs}
        if tag in _IGNORED_TAGS:
            self._ignored += 1
            return
        if self._ignored:
            return
        if tag == "tr":
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = {"parts": [], "anchors": []}
        elif tag == "a" and self._cell is not None and attr.get("href"):
            self._anchor = {
                "url": urljoin(self.base_url, attr["href"]),
                "parts": [attr.get("title", ""), attr.get("aria-label", "")],
            }

    def handle_data(self, data: str) -> None:
        if self._ignored or self._cell is None:
            return
        text = _space(data)
        if not text:
            return
        self._cell["parts"].append(text)
        if self._anchor is not None:
            self._anchor["parts"].append(text)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in _IGNORED_TAGS and self._ignored:
            self._ignored -= 1
            return
        if self._ignored:
            return
        if tag == "a" and self._anchor is not None and self._cell is not None:
            self._anchor["text"] = _space(" ".join(_unique(self._anchor["parts"])))
            self._cell["anchors"].append(self._anchor)
            self._anchor = None
        elif tag in {"td", "th"} and self._cell is not None and self._row is not None:
            self._cell["text"] = _space(" ".join(_unique(self._cell["parts"])))
            self._row.append(self._cell)
            self._cell = None
        elif tag == "tr" and self._row is not None:
            self._finish_row(self._row)
            self._row = None

    def _finish_row(self, cells: Sequence[Mapping[str, Any]]) -> None:
        anchors = [dict(anchor) for cell in cells for anchor in cell.get("anchors") or []]
        detail = next((
            anchor for anchor in anchors
            if urlparse(str(anchor.get("url") or "")).path.lower().endswith("/exhibition_more.aspx")
            and dict(parse_qsl(urlparse(str(anchor.get("url") or "")).query)).get("p") == "menu1"
        ), None)
        if not detail:
            return
        detail_url = str(detail["url"])
        venue_text = _space(cells[-1].get("text")) if len(cells) >= 5 else ""
        if venue_text and not re.search(r"(?:臺北|台北)?世貿一館", venue_text):
            return
        detail_host = urlparse(detail_url).netloc.lower().removeprefix("www.")
        title_cell = next((
            cell for cell in cells
            if any(
                str(anchor.get("url") or "") == detail_url
                for anchor in cell.get("anchors") or []
            )
        ), {})
        title_anchor = next((
            dict(anchor) for anchor in title_cell.get("anchors") or []
            if str(anchor.get("url") or "") != detail_url
            and _space(anchor.get("text"))
            and _space(anchor.get("text")).lower() not in {"more", "詳細資料"}
        ), None)
        title = _space((title_anchor or {}).get("text"))
        if not title:
            title = re.sub(
                r"\b(?:more|詳細資料)\b",
                "",
                _space(title_cell.get("text")),
                flags=re.I,
            ).strip()
        event_url = ""
        if title_anchor:
            candidate = str(title_anchor.get("url") or "")
            candidate_host = urlparse(candidate).netloc.lower().removeprefix("www.")
            if candidate_host and candidate_host != detail_host:
                event_url = candidate
        organizer = _space(cells[2].get("text")) if len(cells) > 2 else ""
        self.records.append({
            "sourceEventId": hashlib.sha256(detail_url.encode("utf-8")).hexdigest()[:24],
            "title": title,
            "detailUrl": detail_url,
            "eventUrl": event_url,
            "organizer": organizer,
            "organizers": [organizer] if organizer else [],
            "listingText": _space(" ".join(str(cell.get("text") or "") for cell in cells)),
            "startDate": "",
            "endDate": "",
            "imageUrl": "",
        })


class ConfiguredOfficialSiteCollector(BaseCollector):
    source_kind = SourceKind.HTML
    max_pages = 5

    @classmethod
    def compile_patterns(cls, source: CollectorSource) -> list[re.Pattern[str]]:
        values = list(source.raw.get("detailPathPatterns") or [])
        if not values:
            raise ValueError(f"{source.id} requires detailPathPatterns")
        return [re.compile(str(value), re.I) for value in values]

    @classmethod
    def parse_listing(
        cls,
        html: str,
        *,
        base_url: str,
        detail_patterns: Sequence[str],
    ) -> tuple[list[dict[str, str]], list[str]]:
        parser = _ListingParser(
            base_url,
            [re.compile(pattern, re.I) for pattern in detail_patterns],
        )
        parser.feed(html)
        parser.close()
        by_url: dict[str, dict[str, str]] = {}
        for record in parser.records:
            if record["detailUrl"] not in by_url:
                by_url[record["detailUrl"]] = record
        return list(by_url.values()), _unique(parser.pagination)

    @classmethod
    def parse_detail(
        cls,
        html: str,
        *,
        detail_url: str,
        source: CollectorSource,
        listing: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        listing = dict(listing or {})
        parser = _DetailParser(detail_url)
        parser.feed(html)
        parser.close()
        text = parser.full_text()
        title = _space(
            parser.meta.get("og:title")
            or parser.meta.get("twitter:title")
            or " ".join(parser.h1)
            or listing.get("title")
        )
        title = re.sub(r"\s*[｜|—-]\s*(?:官方網站|節目資訊|展覽資訊).*$", "", title).strip()
        start, end = _dates(text)
        start = start or str(listing.get("startDate") or "")
        end = end or str(listing.get("endDate") or "") or start
        meta_image = parser.meta.get("og:image") or parser.meta.get("twitter:image") or ""
        images = _clean_images([meta_image, str(listing.get("imageUrl") or ""), *parser.images], detail_url)
        description = _space(
            parser.meta.get("og:description")
            or parser.meta.get("description")
        )
        if len(description) < 40:
            description = text[:1200]
        configured_venue = str(source.raw.get("venueName") or source.name)
        subvenues = [
            str(value)
            for value in source.raw.get("subVenueKeywords") or []
            if str(value) and str(value).lower() in text.lower()
        ]
        time_match = _TIME_RE.search(text)
        start_time = time_match.group("start").replace("：", ":") if time_match else ""
        end_time = time_match.group("end").replace("：", ":") if time_match else ""
        price_lines = [
            line for line in re.split(r"[\n。]", text)
            if (_PAID_RE.search(line) or _FREE_RE.search(line)) and len(line) <= 220
        ][:4]
        price = _space(" / ".join(_unique(price_lines)))
        admission = "paid" if _PAID_RE.search(price or text) else "free" if _FREE_RE.search(price or text) else "unknown"
        exclude_pattern = str(source.raw.get("excludeTitlePattern") or "")
        excluded = bool(_DEFAULT_EXCLUDE_RE.search(title))
        if exclude_pattern:
            excluded = excluded or bool(re.search(exclude_pattern, title, re.I))
        canonical = parser.canonical or detail_url
        return {
            **listing,
            "title": title,
            "detailUrl": canonical,
            "officialUrl": canonical,
            "startDate": start,
            "endDate": end,
            "startTime": start_time,
            "endTime": end_time,
            "timeText": f"{start_time}–{end_time}" if start_time and end_time else "",
            "sourceCategory": str(source.raw.get("sourceCategory") or "官方展演"),
            "contentTypeHint": _hint(title, text[:4000]),
            "organizer": "",
            "organizers": [],
            # R12 venue contract: venueNames contains canonical parent venues
            # only; halls/floors/galleries are represented as child spaces.
            "venueName": configured_venue,
            "venueNames": [configured_venue] if configured_venue else [],
            "venueGroup": configured_venue,
            "parentVenueName": configured_venue,
            "subVenueName": subvenues[0] if subvenues else "",
            "subVenueNames": _unique(subvenues),
            "venueDetail": "／".join(_unique(subvenues)),
            "address": str(source.raw.get("address") or ""),
            "regionCanonical": str(source.raw.get("regionCanonical") or ""),
            "admission": admission,
            "priceText": price,
            "imageUrl": images[0] if images else "",
            "imageUrls": images,
            "description": description,
            "externalUrls": _external_urls(parser.links, detail_url),
            "editorialStatus": "exclude_review" if excluded else "candidate",
            "detailFetched": True,
        }

    def collect_raw(self, source: CollectorSource, client: Any) -> Sequence[Mapping[str, Any]]:
        patterns = [pattern.pattern for pattern in self.compile_patterns(source)]
        listing_urls = list(source.raw.get("listingUrls") or [])
        if not listing_urls and source.listing_url:
            listing_urls = [source.listing_url]
        if not listing_urls:
            raise ValueError(f"{source.id} requires listingUrl or listingUrls")

        queue = [str(url) for url in listing_urls]
        visited: set[str] = set()
        by_url: dict[str, dict[str, Any]] = {}
        self.last_listing_pages = 0
        self.last_detail_requested = 0
        self.last_detail_success = 0
        self.last_detail_failures: list[str] = []

        maximum_pages = max(1, int(source.raw.get("maxListingPages") or self.max_pages))
        while queue and len(visited) < maximum_pages:
            page_url = queue.pop(0)
            if page_url in visited:
                continue
            visited.add(page_url)
            response = client.get(page_url)
            self.last_listing_pages += 1
            records, pagination = self.parse_listing(
                response.text,
                base_url=response.url or page_url,
                detail_patterns=patterns,
            )
            for record in records:
                by_url.setdefault(record["detailUrl"], record)
            for next_url in pagination:
                if next_url not in visited and next_url not in queue:
                    queue.append(next_url)

        records = list(by_url.values())
        fetch_details = str(os.getenv("EXHIBITION_HUB_FETCH_DETAILS", "1")).lower() not in {"0", "false", "no", "off"}
        if not fetch_details:
            return records
        detail_limit = max(0, int(os.getenv("EXHIBITION_HUB_DETAIL_LIMIT", "0") or 0))
        selected = records[: detail_limit or None]
        self.last_detail_requested = len(selected)
        enriched: list[dict[str, Any]] = []
        for record in selected:
            try:
                response = client.get(record["detailUrl"])
                enriched.append(self.parse_detail(
                    response.text,
                    detail_url=response.url or record["detailUrl"],
                    source=source,
                    listing=record,
                ))
                self.last_detail_success += 1
            except Exception as exc:
                self.last_detail_failures.append(
                    f"{record.get('detailUrl')}: {type(exc).__name__}: {exc}"
                )
        return enriched

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
        report.metrics = {
            "listingPagesFetched": self.last_listing_pages,
            "detailRequestedCount": self.last_detail_requested,
            "detailSuccessCount": self.last_detail_success,
            "detailFailureCount": len(self.last_detail_failures),
        }
        if self.last_detail_failures:
            report.status = "partial" if report.records else "failed"
            report.warnings.extend(self.last_detail_failures)
        if not report.records and report.status != "failed":
            report.status = "partial"
            report.warnings.append(f"{source.name} returned no publishable detail records")
        return report


class TaipeiMusicCenterCollector(ConfiguredOfficialSiteCollector):
    source_id = "taipei-music-center"
    source_name = "臺北流行音樂中心"


class KaohsiungMusicCenterCollector(ConfiguredOfficialSiteCollector):
    source_id = "kaohsiung-music-center"
    source_name = "高雄流行音樂中心"


class TainanArtMuseumCollector(ConfiguredOfficialSiteCollector):
    source_id = "tainan-art-museum"
    source_name = "臺南市美術館"


class TaipeiPerformingArtsCenterCollector(ConfiguredOfficialSiteCollector):
    source_id = "taipei-performing-arts-center"
    source_name = "臺北表演藝術中心"


class Pier2ArtCenterCollector(ConfiguredOfficialSiteCollector):
    source_id = "pier-2"
    source_name = "駁二藝術特區"


class TwtcHall1Collector(ConfiguredOfficialSiteCollector):
    source_id = "twtc-hall-1"
    source_name = "臺北世貿一館"

    @classmethod
    def parse_listing(
        cls,
        html: str,
        *,
        base_url: str,
        detail_patterns: Sequence[str],
    ) -> tuple[list[dict[str, str]], list[str]]:
        del detail_patterns
        parser = _TwtcListingParser(base_url)
        parser.feed(html)
        parser.close()
        by_url = {record["detailUrl"]: record for record in parser.records}
        return list(by_url.values()), []

    @classmethod
    def parse_detail(
        cls,
        html: str,
        *,
        detail_url: str,
        source: CollectorSource,
        listing: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        listing = dict(listing or {})
        record = super().parse_detail(
            html,
            detail_url=detail_url,
            source=source,
            listing=listing,
        )
        if _space(listing.get("title")):
            record["title"] = _space(listing["title"])
        organizer = _space(listing.get("organizer"))
        record["organizer"] = organizer
        record["organizers"] = [organizer] if organizer else []
        event_url = str(listing.get("eventUrl") or "")
        if event_url and not re.search(r"facebook|instagram|threads\.net", urlparse(event_url).netloc, re.I):
            record["externalUrls"] = [event_url]
        else:
            record["externalUrls"] = []
        start = str(record.get("startDate") or "")
        end = str(record.get("endDate") or "")
        date_text = f"{start} 至 {end}" if start and end and start != end else start
        summary_parts = [
            f"{record['title']}於臺北世貿一館舉辦。",
            f"展期：{date_text}。" if date_text else "",
            f"主辦單位：{organizer}。" if organizer else "",
            "入場方式與最新異動請以官方活動頁及主辦單位公告為準。",
        ]
        record["description"] = _space(" ".join(part for part in summary_parts if part))
        record["admission"] = "unknown"
        record["priceText"] = "入場方式請洽主辦單位"
        return record

    def collect_raw(self, source: CollectorSource, client: Any) -> Sequence[Mapping[str, Any]]:
        records = [dict(record) for record in super().collect_raw(source, client)]
        self.last_external_requested = 0
        self.last_external_success = 0
        for record in records:
            if record.get("imageUrl"):
                continue
            event_url = str(record.get("eventUrl") or "").strip()
            parsed = urlparse(event_url)
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.netloc
                or re.search(r"facebook|instagram|threads\.net|line\.me", parsed.netloc, re.I)
            ):
                continue
            self.last_external_requested += 1
            try:
                response = client.get(event_url)
                parser = _DetailParser(response.url or event_url)
                parser.feed(response.text)
                parser.close()
                images = _clean_images(
                    [
                        parser.meta.get("og:image", ""),
                        parser.meta.get("twitter:image", ""),
                        *parser.images,
                    ],
                    response.url or event_url,
                )
                if images:
                    record["imageUrl"] = images[0]
                    record["imageUrls"] = images
                    self.last_external_success += 1
                description = _space(
                    parser.meta.get("og:description")
                    or parser.meta.get("description")
                )
                if len(description) >= 40 and len(str(record.get("description") or "")) < 40:
                    record["description"] = description
            except Exception as exc:
                self.last_detail_failures.append(
                    f"{event_url}: {type(exc).__name__}: {exc}"
                )
        return records

    def run(self, source: CollectorSource, client: Any) -> CollectorRunReport:
        report = super().run(source, client)
        report.metrics.update({
            "externalEventPagesRequested": getattr(self, "last_external_requested", 0),
            "externalEventPagesWithUsableImage": getattr(self, "last_external_success", 0),
        })
        return report


class TaipeiExpoParkExpoDomeCollector(ConfiguredOfficialSiteCollector):
    source_id = "taipei-expo-park-expo-dome"
    source_name = "花博公園爭艷館"

    @classmethod
    def parse_listing(
        cls,
        html: str,
        *,
        base_url: str,
        detail_patterns: Sequence[str],
    ) -> tuple[list[dict[str, str]], list[str]]:
        records, pagination = super().parse_listing(
            html,
            base_url=base_url,
            detail_patterns=detail_patterns,
        )
        filtered: list[dict[str, str]] = []
        for record in records:
            listing_text = _space(record.get("listingText"))
            if not re.search(r"(?:花博公園)?爭[艷豔]館", listing_text):
                continue
            start, end = _roc_dates(listing_text)
            if start:
                record["startDate"] = start
                record["endDate"] = end or start
            filtered.append(record)
        return filtered, pagination

    @classmethod
    def parse_detail(
        cls,
        html: str,
        *,
        detail_url: str,
        source: CollectorSource,
        listing: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        listing = dict(listing or {})
        record = super().parse_detail(
            html,
            detail_url=detail_url,
            source=source,
            listing=listing,
        )
        if _space(listing.get("title")):
            record["title"] = _space(listing["title"])
        exclude_pattern = str(source.raw.get("excludeTitlePattern") or "")
        excluded = bool(_DEFAULT_EXCLUDE_RE.search(record["title"]))
        if exclude_pattern:
            excluded = excluded or bool(re.search(exclude_pattern, record["title"], re.I))
        record["editorialStatus"] = "exclude_review" if excluded else "candidate"
        start, end = _roc_dates(_space(
            f"{record.get('description', '')} {listing.get('listingText', '')}"
        ))
        record["startDate"] = start or str(listing.get("startDate") or record.get("startDate") or "")
        record["endDate"] = end or str(listing.get("endDate") or record.get("endDate") or record["startDate"])
        return record


OFFICIAL_SITE_COLLECTORS = (
    TaipeiMusicCenterCollector,
    KaohsiungMusicCenterCollector,
    TainanArtMuseumCollector,
    TaipeiPerformingArtsCenterCollector,
    Pier2ArtCenterCollector,
    TwtcHall1Collector,
    TaipeiExpoParkExpoDomeCollector,
)
