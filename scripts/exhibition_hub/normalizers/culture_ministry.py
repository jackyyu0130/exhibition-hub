"""Normalize Culture Ministry records into site-ready event dictionaries."""

from __future__ import annotations

from datetime import datetime
from html import unescape
from html.parser import HTMLParser
import re
from typing import Any, Iterable, Mapping
from urllib.parse import urlsplit

from ..collectors.base import RawEvent


CULTURE_SOURCE_ID = "culture-ministry"
CULTURE_SOURCE_NAME = "文化部文化資料開放服務網"


class CultureNormalizationError(ValueError):
    """Raised when a Culture Ministry record cannot be normalized."""


class _PlainTextExtractor(HTMLParser):
    """Convert simple HTML descriptions into readable plain text."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        cleaned = data.strip()

        if cleaned:
            self.parts.append(cleaned)

    def get_text(self) -> str:
        return " ".join(self.parts)


def clean_text(value: Any) -> str:
    """Return a trimmed single-line string."""

    if value is None:
        return ""

    text = unescape(str(value))
    return " ".join(text.split())


def clean_html(value: Any) -> str:
    """Remove HTML tags while retaining readable description text."""

    text = clean_text(value)

    if not text:
        return ""

    parser = _PlainTextExtractor()

    try:
        parser.feed(text)
        parser.close()

    except Exception:
        return clean_text(
            re.sub(r"<[^>]+>", " ", text)
        )

    extracted = parser.get_text()

    if extracted:
        return clean_text(extracted)

    return clean_text(
        re.sub(r"<[^>]+>", " ", text)
    )


def first_text(*values: Any) -> str:
    """Return the first non-empty text value."""

    for value in values:
        cleaned = clean_text(value)

        if cleaned:
            return cleaned

    return ""


def normalize_date(value: Any) -> str:
    """Normalize a Culture date into YYYY-MM-DD when possible."""

    cleaned = clean_text(value)

    if not cleaned:
        return ""

    formats = (
        "%Y/%m/%d",
        "%Y-%m-%d",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    )

    for date_format in formats:
        try:
            parsed = datetime.strptime(
                cleaned,
                date_format,
            )
            return parsed.strftime("%Y-%m-%d")

        except ValueError:
            continue

    matched = re.match(
        r"^(\d{4})[/-](\d{1,2})[/-](\d{1,2})",
        cleaned,
    )

    if matched:
        year, month, day = matched.groups()

        return (
            f"{int(year):04d}-"
            f"{int(month):02d}-"
            f"{int(day):02d}"
        )

    return cleaned


def normalize_datetime(value: Any) -> str:
    """Normalize date-time text while preserving the time component."""

    cleaned = clean_text(value)

    if not cleaned:
        return ""

    formats = (
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d",
        "%Y-%m-%d",
    )

    for date_format in formats:
        try:
            parsed = datetime.strptime(
                cleaned,
                date_format,
            )

            if parsed.hour or parsed.minute or parsed.second:
                return parsed.strftime(
                    "%Y-%m-%dT%H:%M:%S"
                )

            return parsed.strftime("%Y-%m-%d")

        except ValueError:
            continue

    return cleaned


def normalize_float(value: Any) -> float | None:
    """Convert Culture coordinate values into floats."""

    if value is None:
        return None

    cleaned = clean_text(value)

    if not cleaned:
        return None

    try:
        return float(cleaned)

    except (TypeError, ValueError):
        return None


def normalize_boolean(value: Any) -> bool | None:
    """Normalize Culture Y/N sale flags."""

    cleaned = clean_text(value).lower()

    if cleaned in {
        "y",
        "yes",
        "true",
        "1",
        "是",
    }:
        return True

    if cleaned in {
        "n",
        "no",
        "false",
        "0",
        "否",
    }:
        return False

    return None


def normalize_url(value: Any) -> str:
    """Return only valid HTTP or HTTPS URLs."""

    if isinstance(value, list):
        for item in value:
            normalized = normalize_url(item)

            if normalized:
                return normalized

        return ""

    cleaned = clean_text(value)

    if not cleaned:
        return ""

    parsed = urlsplit(cleaned)

    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
    ):
        return ""

    return cleaned


def normalize_string_list(value: Any) -> list[str]:
    """Convert API unit fields into a unique string list."""

    if value is None:
        return []

    raw_items: Iterable[Any]

    if isinstance(value, (list, tuple, set)):
        raw_items = value

    else:
        raw_items = [value]

    output: list[str] = []
    seen: set[str] = set()

    for item in raw_items:
        cleaned = clean_text(item)

        if not cleaned or cleaned in seen:
            continue

        output.append(cleaned)
        seen.add(cleaned)

    return output


def normalize_sessions(value: Any) -> list[dict[str, Any]]:
    """Normalize Culture showInfo records."""

    if not isinstance(value, list):
        return []

    sessions: list[dict[str, Any]] = []

    for item in value:
        if not isinstance(item, Mapping):
            continue

        session = {
            "startTime": normalize_datetime(
                item.get("time")
            ),
            "endTime": normalize_datetime(
                item.get("endTime")
            ),
            "location": clean_text(
                item.get("location")
            ),
            "locationName": clean_text(
                item.get("locationName")
            ),
            "onSales": normalize_boolean(
                item.get("onSales")
            ),
            "price": clean_text(
                item.get("price")
            ),
            "latitude": normalize_float(
                item.get("latitude")
            ),
            "longitude": normalize_float(
                item.get("longitude")
            ),
        }

        if any(
            value not in {
                "",
                None,
            }
            for value in session.values()
        ):
            sessions.append(session)

    return sessions


def first_session_value(
    sessions: list[dict[str, Any]],
    key: str,
) -> Any:
    """Return the first useful value from normalized sessions."""

    for session in sessions:
        value = session.get(key)

        if value not in {
            "",
            None,
        }:
            return value

    return None


def detect_region(
    address: Any,
    location_name: Any = "",
) -> str:
    """Extract a Taiwan county or city from address and venue text.

    The Culture Ministry feed sometimes omits the county or city and only
    provides a district, township, road, or venue name. Direct county/city
    names remain the highest-confidence signal. Unique administrative areas
    and carefully scoped context keywords are used as fallbacks.
    """

    cleaned_address = clean_text(address)
    cleaned_location = clean_text(location_name)
    cleaned = f"{cleaned_address} {cleaned_location}".strip()

    regions = (
        "臺北市",
        "新北市",
        "桃園市",
        "臺中市",
        "臺南市",
        "高雄市",
        "基隆市",
        "新竹市",
        "嘉義市",
        "新竹縣",
        "苗栗縣",
        "彰化縣",
        "南投縣",
        "雲林縣",
        "嘉義縣",
        "屏東縣",
        "宜蘭縣",
        "花蓮縣",
        "臺東縣",
        "澎湖縣",
        "金門縣",
        "連江縣",
    )

    aliases = {
        "台北市": "臺北市",
        "台中市": "臺中市",
        "台南市": "臺南市",
        "台東縣": "臺東縣",
    }

    for region in regions:
        if region in cleaned:
            return region

    for alias, official_name in aliases.items():
        if alias in cleaned:
            return official_name

    unique_admin_areas = {
        "大同區": "臺北市",
        "內湖區": "臺北市",
        "香山區": "新竹市",
        "西屯區": "臺中市",
        "中西區": "臺南市",
        "鹽埕區": "高雄市",
        "鼓山區": "高雄市",
        "埔里鎮": "南投縣",
        "新港鄉": "嘉義縣",
    }

    for area_name, region in unique_admin_areas.items():
        if area_name in cleaned:
            return region

    context_keywords = {
        "臺北市": (
            "羅斯福路",
            "忠孝東路",
            "敦化南路",
            "南海路",
            "瑞光路",
            "承德路三段",
            "環河北路一段",
            "聯邦藝術中心",
            "金車文藝中心",
            "安卓藝術",
            "國立歷史博物館",
            "谷公館",
            "厭世會社",
        ),
        "臺中市": (
            "THE 201 ART",
            "順天建築",
        ),
        "高雄市": (
            "新浜碼頭藝術空間",
            "大仁路146號",
            "臨海一路",
            "光隆行",
        ),
        "南投縣": (
            "中台世界博物館",
            "中台路",
        ),
    }

    for region, keywords in context_keywords.items():
        if any(keyword in cleaned for keyword in keywords):
            return region

    return ""


def normalize_culture_event(
    record: Mapping[str, Any],
) -> dict[str, Any]:
    """Normalize one Culture Ministry activity record."""

    external_id = first_text(
        record.get("UID"),
        record.get("uid"),
        record.get("id"),
    )
    title = clean_text(
        record.get("title")
    )

    if not external_id:
        raise CultureNormalizationError(
            "Culture record is missing UID"
        )

    if not title:
        raise CultureNormalizationError(
            f"Culture record {external_id} is missing title"
        )

    sessions = normalize_sessions(
        record.get("showInfo")
    )

    address = clean_text(
        first_session_value(
            sessions,
            "location",
        )
    )
    location_name = clean_text(
        first_session_value(
            sessions,
            "locationName",
        )
    )

    image = normalize_url(
        record.get("imageUrl")
    )
    source_url = normalize_url(
        record.get("sourceWebPromote")
    )
    ticket_url = normalize_url(
        record.get("webSales")
    )

    organizers: list[str] = []
    organizer_seen: set[str] = set()

    for field_name in (
        "masterUnit",
        "showUnit",
        "subUnit",
        "supportUnit",
        "otherUnit",
    ):
        for organizer in normalize_string_list(
            record.get(field_name)
        ):
            if organizer in organizer_seen:
                continue

            organizers.append(organizer)
            organizer_seen.add(organizer)

    description = clean_html(
        first_text(
            record.get("descriptionFilterHtml"),
            record.get("comment"),
        )
    )

    raw_category = first_text(
        record.get("category"),
        record.get("_feedCategory"),
    )

    return {
        "id": (
            f"{CULTURE_SOURCE_ID}:"
            f"{external_id}"
        ),
        "externalId": external_id,
        "title": title,
        "description": description,
        "category": "展覽",
        "categories": ["展覽"],
        "rawCategory": raw_category,
        "startDate": normalize_date(
            record.get("startDate")
        ),
        "endDate": normalize_date(
            record.get("endDate")
        ),
        "locationName": location_name,
        "venueGroup": location_name,
        "address": address,
        "region": detect_region(
            address,
            location_name,
        ),
        "latitude": first_session_value(
            sessions,
            "latitude",
        ),
        "longitude": first_session_value(
            sessions,
            "longitude",
        ),
        "price": clean_text(
            first_session_value(
                sessions,
                "price",
            )
        ),
        "image": image,
        "images": (
            [image]
            if image
            else []
        ),
        "sourceUrl": source_url,
        "ticketUrl": ticket_url,
        "source": CULTURE_SOURCE_NAME,
        "sourceId": CULTURE_SOURCE_ID,
        "sourceName": first_text(
            record.get("sourceWebName"),
            CULTURE_SOURCE_NAME,
        ),
        "organizers": organizers,
        "sessions": sessions,
        "lastModified": normalize_datetime(
            record.get("editModifyDate")
        ),
    }


def normalize_culture_records(
    records: Iterable[RawEvent],
) -> tuple[
    list[dict[str, Any]],
    list[str],
]:
    """Normalize records while isolating individual bad entries."""

    normalized: list[dict[str, Any]] = []
    errors: list[str] = []

    for index, record in enumerate(records):
        try:
            normalized.append(
                normalize_culture_event(record)
            )

        except CultureNormalizationError as exc:
            errors.append(
                f"record[{index}]: {exc}"
            )

    return normalized, errors
