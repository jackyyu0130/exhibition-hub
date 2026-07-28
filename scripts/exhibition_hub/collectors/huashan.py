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
    "適合對象", "適合年齡", "聯絡資訊", "展演資訊",
    "活動及票價資訊", "活動時間", "票價資訊", "售票資訊",
}
_IGNORED_TEXT_TAGS = {"script", "style", "noscript", "template", "svg"}
_JS_NOISE_RE = re.compile(
    r"(?:event\.preventDefault|e\.preventDefault|\$\s*\(|"
    r"function\s*\(|data-colorboxGroup|document\.|window\.)",
    re.IGNORECASE,
)
_VENUE_HINT_RE = re.compile(
    r"(?:館|劇院|練舞場|展演空間|空間|廳|廣場|所|樓|\b\d+F\b)",
    re.IGNORECASE,
)
_GENERIC_EXTERNAL_RE = re.compile(
    r"(?:facebook\.com/1914CP|instagram\.com/huashan1914_creative_park|"
    r"youtube\.com/channel/UCE4Xrh2u4FGB25h0I3aHE6A|"
    r"104\.com\.tw/jobbank/custjob|"
    r"tea\.huashan1914\.org/beingproject|"
    r"reurl\.cc/33kmg9)",
    re.IGNORECASE,
)
_ASSET_STOP_RE = re.compile(
    r"^(?:相關活動|更多活動|推薦活動|其他活動|你可能也喜歡|如何來華山)"
)
_PRICE_SECTION_RE = re.compile(
    r"^(?:【?票價】?|票價資訊|售票資訊|門票資訊|活動及票價資訊)"
)
_PRICE_AMOUNT_RE = re.compile(
    r"(?:"
    r"(?:NTD|NT\$|NT\.?|新臺幣|新台幣)\s*[\d,]+\s*(?:元)?"
    r"|[\d,]+\s*元"
    r"|[\d,]+\s*/\s*(?:張|人|組|位)"
    r")",
    re.IGNORECASE,
)
_PRICE_FRAGMENT_RE = re.compile(
    r"(?:(?:特典套票|全票|優待票|愛心票|早鳥價|原價|票價)"
    r"\s*[:：]?\s*)?"
    r"(?:"
    r"(?:NTD|NT\$|NT\.?)\s*[\d,]+\s*(?:元)?"
    r"|[\d,]+\s*元(?:\s*/\s*(?:張|人|組|位))?"
    r"|[\d,]+\s*/\s*(?:張|人|組|位)"
    r")",
    re.IGNORECASE,
)
_NON_ADMISSION_PRICE_RE = re.compile(
    r"(?:禮券|獎金|贈品|抽獎|購物金|徵件獎勵|入選獎勵)"
)
_EDITORIAL_EXCLUDE_TITLE_RE = re.compile(
    r"(?:徵件|招募|工作坊|講座|課程|營隊|研習)"
)
_EMOJI_IMAGE_RE = re.compile(
    r"(?:^|/)(?:1f[0-9a-f]{3,}|emoji)[^/]*\.(?:png|gif|webp)$",
    re.IGNORECASE,
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
        self._ignored_depth = 0
        self._asset_collection_stopped = False

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        tag = tag.lower()
        attrs_map = {str(name).lower(): str(value or "") for name, value in attrs}
        if tag in _IGNORED_TEXT_TAGS:
            self._ignored_depth += 1
            return
        if self._ignored_depth:
            return
        if tag in _BLOCK_TAGS:
            self.text_parts.append("\n")

        if tag == "meta":
            key = (
                attrs_map.get("property")
                or attrs_map.get("name")
                or ""
            ).strip().lower()
            content = attrs_map.get("content", "").strip()
            if key and content and key not in self.meta:
                self.meta[key] = content
        elif tag == "link" and "canonical" in attrs_map.get("rel", "").lower():
            self.canonical_url = urljoin(self.base_url, attrs_map.get("href", ""))
        elif tag == "img" and not self._asset_collection_stopped:
            image = (
                attrs_map.get("data-src")
                or attrs_map.get("data-original")
                or attrs_map.get("src")
            )
            if image:
                absolute = urljoin(self.base_url, image)
                if not re.search(
                    r"(?:logo|icon|loading|blank|spacer)",
                    absolute,
                    re.I,
                ):
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
        tag = tag.lower()
        if tag in _IGNORED_TEXT_TAGS:
            self._ignored_depth = max(0, self._ignored_depth - 1)
            return
        if self._ignored_depth:
            return
        if tag in _BLOCK_TAGS:
            self.text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        normalized = _normalize_space(data)
        if normalized and _ASSET_STOP_RE.match(normalized):
            self._asset_collection_stopped = True
        if data:
            self.text_parts.append(data)

    def lines(self) -> list[str]:
        text = "".join(self.text_parts).replace("\xa0", " ")
        return [
            _normalize_space(line)
            for line in re.split(r"[\r\n]+", text)
            if _normalize_space(line)
        ]


def _main_detail_lines(
    lines: Sequence[str],
    title: str,
) -> list[str]:
    start = 0
    if title:
        for index, line in enumerate(lines):
            if line == title:
                start = index
                break
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index] in {"相關活動", "如何來華山"}:
            end = index
            break
    return list(lines[start:end])


def _is_clean_text(value: str) -> bool:
    text = _normalize_space(value)
    return bool(text) and not _JS_NOISE_RE.search(text)


def _is_organizer_value(value: str) -> bool:
    text = _normalize_space(value)
    if not _is_clean_text(text) or len(text) > 100:
        return False
    if text in _STOP_LABELS or re.search(r"https?://", text, re.I):
        return False
    return True


def _is_venue_value(value: str) -> bool:
    text = _normalize_space(value)
    if not _is_clean_text(text) or len(text) > 80:
        return False
    if text in _STOP_LABELS or re.search(r"https?://", text, re.I):
        return False
    if re.search(
        r"[。！？]|適合|年齡|票價|上映時間|場次|官方粉絲團|連絡電話|"
        r"正式進駐|邀請|帶你|感受|歡迎|是否曾經|這是一場",
        text,
    ):
        return False
    return bool(_VENUE_HINT_RE.search(text))


def _values_after_label(
    lines: Sequence[str],
    label: str,
    *,
    maximum: int = 8,
    validator: Any | None = None,
) -> list[str]:
    validator = validator or _is_clean_text
    for index, line in enumerate(lines):
        if line != label and not line.startswith(label + "："):
            continue
        inline = line.split("：", 1)[1].strip() if "：" in line else ""
        values: list[str] = []
        if inline and validator(inline):
            values.append(inline)
        for candidate in lines[index + 1: index + 1 + maximum]:
            if candidate in _STOP_LABELS or candidate.startswith("######"):
                break
            if candidate.startswith("#"):
                continue
            if not validator(candidate):
                if values:
                    break
                continue
            values.append(candidate)
        return _unique(values)
    return []


def _price_value_from_line(line: str) -> str:
    text = _normalize_space(line)
    if not _is_clean_text(text):
        return ""
    if re.search(r"https?://|適合年齡|上映時間|場次", text, re.I):
        return ""
    if _NON_ADMISSION_PRICE_RE.search(text):
        return ""

    amount_matches = list(_PRICE_AMOUNT_RE.finditer(text))
    if not amount_matches:
        return ""

    if len(text) <= 180:
        return text

    fragments = _unique([
        match.group(0)
        for match in _PRICE_FRAGMENT_RE.finditer(text)
        if _normalize_space(match.group(0))
    ])
    return _normalize_space(" / ".join(fragments[:8]))


def _extract_price_lines(lines: Sequence[str]) -> list[str]:
    section_starts = [
        index
        for index, line in enumerate(lines)
        if _PRICE_SECTION_RE.match(_normalize_space(line))
    ]

    for start in section_starts:
        values: list[str] = []
        for candidate in lines[start: start + 14]:
            normalized = _normalize_space(candidate)
            if (
                values
                and normalized in _STOP_LABELS
                and not _PRICE_SECTION_RE.match(normalized)
            ):
                break
            value = _price_value_from_line(normalized)
            if not value:
                continue
            values.append(value)
            if len(_PRICE_AMOUNT_RE.findall(value)) >= 2:
                break
            if len(values) >= 3:
                break
        if values:
            return _unique(values)

    values: list[str] = []
    for line in lines:
        value = _price_value_from_line(line)
        if not value:
            continue
        values.append(value)
        if len(_PRICE_AMOUNT_RE.findall(value)) >= 2:
            break
        if len(values) >= 2:
            break
    return _unique(values)


def _classify_admission(price_text: str, full_text: str) -> str:
    # A scoped, explicit ticket price is stronger evidence than
    # generic "免費" wording elsewhere on the same page.
    if re.search(
        r"NTD\s*\d|NT\$\s*\d|\d[\d,]*\s*元|"
        r"全票|優待票|愛心票|早鳥價|原價",
        price_text,
        re.I,
    ):
        return "paid"
    if re.search(
        r"免費入場|免費參觀|自由入場|免票|免費參加",
        price_text,
    ):
        return "free"
    if re.search(r"售票制|購票入場|售票入場", full_text, re.I):
        return "paid"
    if re.search(
        r"免費入場|免費參觀|自由入場|免票|免費參加",
        full_text,
    ):
        return "free"
    return "unknown"


def _infer_source_category(
    source_category: str,
    title: str,
    detail_url: str,
) -> str:
    if source_category:
        return source_category
    path = urlparse(detail_url).path.lower()
    if "/performance_" in path or re.search(r"表藝節|劇場|音樂會|舞台劇", title):
        return "表演藝術"
    if re.search(r"快閃|期間限定|POP\s*UP", title, re.I):
        return "期間限定店"
    return ""


def _clean_image_urls(values: Sequence[str]) -> list[str]:
    return _unique([
        value
        for value in values
        if value and not _EMOJI_IMAGE_RE.search(value)
    ])[:3]


def _clean_external_urls(values: Sequence[str]) -> list[str]:
    return _unique([
        value
        for value in values
        if not _GENERIC_EXTERNAL_RE.search(value)
    ])[:6]


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
        scoped_lines = _main_detail_lines(lines, title)
        scoped_text = " ".join(scoped_lines)

        if not description or "華山1914" in description and len(description) < 80:
            description = _description_from_lines(scoped_lines, title)

        organizers = _values_after_label(
            scoped_lines,
            "主辦單位",
            maximum=4,
            validator=_is_organizer_value,
        )
        venues = _values_after_label(
            scoped_lines,
            "活動地點",
            maximum=6,
            validator=_is_venue_value,
        )
        source_category = next(
            (
                value
                for value in _KNOWN_ACTIVITY_TYPES
                if value in scoped_lines or value in scoped_text[:1200]
            ),
            "",
        )
        source_category = _infer_source_category(
            source_category,
            title,
            detail_url,
        )

        time_match = _TIME_RE.search(scoped_text) or _TIME_RE.search(full_text)
        start_time = ""
        end_time = ""
        time_text = ""
        if time_match:
            start_time = _normalize_time(time_match.group("start"), time_match.group("start_ampm"))
            end_time = _normalize_time(time_match.group("end"), time_match.group("end_ampm"))
            time_text = _normalize_space(time_match.group(0))

        price_lines = _extract_price_lines(scoped_lines)
        price_text = _normalize_space(" / ".join(price_lines))
        admission = _classify_admission(price_text, scoped_text)

        meta_image = (
            parser.meta.get("og:image")
            or parser.meta.get("twitter:image")
            or ""
        )
        images = _clean_image_urls([
            urljoin(detail_url, meta_image) if meta_image else "",
            str(listing.get("imageUrl") or ""),
            *parser.image_urls,
        ])

        external_urls = _clean_external_urls(parser.external_urls)
        canonical = parser.canonical_url or detail_url
        editorial_status = "candidate"
        if (
            source_category == "論壇講座"
            or _EDITORIAL_EXCLUDE_TITLE_RE.search(title)
            or (
                any("beclass.com" in value for value in external_urls)
                and re.search(r"探索計畫|報名|課程", title)
            )
        ):
            editorial_status = "exclude_review"

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
