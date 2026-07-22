#!/usr/bin/env python3
"""Build data/exhibitions.json for the Exhibition Hub GitHub Pages site.

This version fixes two common problems in the Ministry of Culture feed:
1. Event sessions are normally stored under ``showInfo`` (capital I), while some
   older data exports use ``showinfo``. Coordinates and venue data are read from
   both spellings and from every session, not only the first incomplete one.
2. Promotional images may use several field names, be nested, be relative URLs,
   or only appear as Open Graph metadata on the event source page.

Usage:
    python scripts/scraper.py
    python scripts/scraper.py --output data/exhibitions.json
    python scripts/scraper.py --input-file tests/fixture.json
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator
from urllib.parse import unquote, urljoin, urlparse

import requests

API_URLS = [
    "https://cloud.culture.tw/frontsite/trans/SearchShowAction.do?category=all&method=doFindTypeJ",
    "https://cloud.culture.tw/frontsite/trans/SearchShowAction.do?method=doFindTypeJOpenApi&category=all",
]
API_URL = API_URLS[0]
DEFAULT_OUTPUT = Path("data/exhibitions.json")
TAIPEI_TZ = timezone(timedelta(hours=8))
USER_AGENT = "TaiwanExhibitionJournal/3.2 (+https://github.com/jackyyu0130/exhibition-hub)"
CULTURE_BASE_URL = "https://cloud.culture.tw/"

CATEGORY_MAP = {
    "1": "音樂", "2": "表演", "3": "舞蹈", "4": "親子", "5": "音樂",
    "6": "美術", "7": "講座", "8": "電影", "11": "表演", "13": "商展",
    "14": "其他", "15": "其他", "17": "其他", "19": "其他",
}

REGION_ALIASES = {
    "臺北市": "台北市", "臺中市": "台中市", "臺南市": "台南市", "臺東縣": "台東縣",
}
REGIONS = [
    "台北市", "新北市", "基隆市", "桃園市", "新竹市", "新竹縣", "苗栗縣", "台中市",
    "彰化縣", "南投縣", "雲林縣", "嘉義市", "嘉義縣", "台南市", "高雄市", "屏東縣",
    "宜蘭縣", "花蓮縣", "台東縣", "澎湖縣", "金門縣", "連江縣",
]

KEYWORD_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("快閃", re.compile(r"快閃|期間限定|popup|pop-up", re.I)),
    ("攝影", re.compile(r"攝影|影像|photo", re.I)),
    ("動漫", re.compile(r"動漫|動畫|漫畫|卡通|anime|公仔|角色", re.I)),
    ("設計", re.compile(r"設計|建築|工藝|時尚|design", re.I)),
    ("市集", re.compile(r"市集|祭典|嘉年華|文創攤位", re.I)),
    ("商展", re.compile(r"展售|博覽會|商展|產業展", re.I)),
    ("親子", re.compile(r"親子|兒童|家庭", re.I)),
]

IMAGE_META_PATTERNS = [
    re.compile(r'<meta[^>]+(?:property|name)=["\']og:image(?::secure_url)?["\'][^>]+content=["\']([^"\']+)', re.I),
    re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']og:image(?::secure_url)?["\']', re.I),
    re.compile(r'<meta[^>]+(?:property|name)=["\']twitter:image(?::src)?["\'][^>]+content=["\']([^"\']+)', re.I),
    re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']twitter:image(?::src)?["\']', re.I),
    re.compile(r'<link[^>]+rel=["\']image_src["\'][^>]+href=["\']([^"\']+)', re.I),
]
IMG_SRC_PATTERN = re.compile(r'<img[^>]+(?:src|data-src|data-original)=["\']([^"\']+)', re.I)


@dataclass(frozen=True)
class SourceConfig:
    url: str = API_URL
    timeout: int = 45
    retries: int = 3


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        value = "、".join(clean_text(item) for item in value if clean_text(item))
    text = html.unescape(str(value))
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def first_value(*values: Any) -> Any:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, (list, dict)) and not value:
            continue
        return value
    return ""


def flatten_values(value: Any) -> Iterator[Any]:
    if value is None:
        return
    if isinstance(value, (list, tuple, set)):
        for item in value:
            yield from flatten_values(item)
        return
    if isinstance(value, dict):
        preferred = ("url", "src", "href", "image", "imageUrl", "imageURL", "original", "large")
        found = False
        for key in preferred:
            if key in value:
                found = True
                yield from flatten_values(value[key])
        if not found:
            for item in value.values():
                yield from flatten_values(item)
        return
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("[") or stripped.startswith("{"):
            try:
                yield from flatten_values(json.loads(stripped))
                return
            except json.JSONDecodeError:
                pass
    yield value


def normalize_url(value: Any, *, base_url: str = CULTURE_BASE_URL) -> str:
    text = html.unescape(str(value or "")).strip().strip('"\'')
    if not text:
        return ""
    text = text.replace("\\/", "/")
    # Some sources return percent-encoded full URLs.
    if re.match(r"^https?%3A", text, re.I):
        text = unquote(text)
    if text.startswith("//"):
        text = "https:" + text
    text = urljoin(base_url, text)
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return text


def valid_http_url(value: Any) -> str:
    return normalize_url(value)


def parse_date(value: Any) -> date | None:
    text = clean_text(value)
    if not text:
        return None
    text = text.replace("/", "-")
    match = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
    if not match:
        return None
    try:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError:
        return None


def date_string(value: Any) -> str:
    parsed = parse_date(value)
    return parsed.isoformat() if parsed else clean_text(value)


def number_or_none(value: Any, *, latitude: bool) -> float | None:
    try:
        text = str(value).strip().replace(",", ".")
        number = float(text)
    except (TypeError, ValueError):
        return None
    limit = 90 if latitude else 180
    if not -limit <= number <= limit or number == 0:
        return None
    return round(number, 7)


def coordinate_pair(*sources: dict[str, Any]) -> tuple[float | None, float | None]:
    lat_keys = ("latitude", "Latitude", "lat", "Lat", "mapLat", "y")
    lon_keys = ("longitude", "Longitude", "lng", "lon", "Lng", "mapLng", "x")
    for source in sources:
        if not isinstance(source, dict):
            continue
        raw_lat = first_value(*(source.get(key) for key in lat_keys))
        raw_lon = first_value(*(source.get(key) for key in lon_keys))
        lat = number_or_none(raw_lat, latitude=True)
        lon = number_or_none(raw_lon, latitude=False)
        if lat is not None and lon is not None:
            return lat, lon
        # Occasionally feeds swap x/y or latitude/longitude.
        swapped_lat = number_or_none(raw_lon, latitude=True)
        swapped_lon = number_or_none(raw_lat, latitude=False)
        if swapped_lat is not None and swapped_lon is not None:
            return swapped_lat, swapped_lon
    return None, None


def detect_region(*values: Any) -> str:
    text = " ".join(clean_text(value) for value in values)
    for old, new in REGION_ALIASES.items():
        text = text.replace(old, new)
    for region in REGIONS:
        if region in text:
            return region
    return "其他地區"


def normalize_categories(raw_category: Any, title: str, description: str) -> list[str]:
    categories: list[str] = []
    values = raw_category if isinstance(raw_category, list) else [raw_category]
    for value in values:
        text = clean_text(value)
        if not text:
            continue
        mapped = CATEGORY_MAP.get(text, text)
        if mapped not in categories:
            categories.append(mapped)
    combined = f"{title} {description}"
    for category, pattern in KEYWORD_RULES:
        if pattern.search(combined) and category not in categories:
            categories.insert(0, category)
    if not categories:
        categories = ["其他"]
    return categories[:3]


def show_entries(raw: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for key in ("showInfo", "showinfo", "show_info", "shows", "sessions"):
        value = raw.get(key)
        if isinstance(value, dict):
            entries.append(value)
        elif isinstance(value, list):
            entries.extend(item for item in value if isinstance(item, dict))
    return entries


def show_score(show: dict[str, Any]) -> int:
    lat, lon = coordinate_pair(show)
    score = 0
    if lat is not None and lon is not None:
        score += 100
    if clean_text(first_value(show.get("locationName"), show.get("venue"))):
        score += 25
    if clean_text(first_value(show.get("location"), show.get("address"))):
        score += 20
    if clean_text(first_value(show.get("time"), show.get("startTime"))):
        score += 5
    return score


def best_show(raw: dict[str, Any]) -> dict[str, Any]:
    entries = show_entries(raw)
    return max(entries, key=show_score) if entries else {}


def image_candidates(raw: dict[str, Any], show: dict[str, Any] | None = None) -> Iterator[Any]:
    keys = (
        "image", "images", "imageUrl", "imageURL", "imageURLList", "imageUrls",
        "poster", "posterUrl", "picture", "pictureUrl", "photo", "photoUrl", "cover", "coverUrl",
    )
    for source in (raw, show or {}):
        for key in keys:
            if key in source:
                yield from flatten_values(source.get(key))


def image_from_html(raw_html: Any, *, base_url: str = CULTURE_BASE_URL) -> str:
    text = html.unescape(str(raw_html or ""))
    for match in IMG_SRC_PATTERN.finditer(text):
        url = normalize_url(match.group(1), base_url=base_url)
        if url:
            return url
    return ""


def image_url(raw: dict[str, Any], show: dict[str, Any] | None = None) -> str:
    for candidate in image_candidates(raw, show):
        url = normalize_url(candidate)
        if url:
            return url
    return image_from_html(first_value(raw.get("descriptionFilterHtml"), raw.get("description")))


def source_url(raw: dict[str, Any]) -> str:
    for candidate in (
        raw.get("sourceUrl"), raw.get("sourceWebPromote"), raw.get("webSales"),
        raw.get("sourceWebSite"), raw.get("url"), raw.get("website"),
    ):
        url = normalize_url(candidate)
        if url:
            return url
    return ""


def discover_page_image(url: str, *, timeout: int = 12) -> str:
    if not url:
        return ""
    try:
        response = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
        )
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").lower()
        if "html" not in content_type and not response.text.lstrip().startswith("<"):
            return ""
        page = response.text[:800_000]
        for pattern in IMAGE_META_PATTERNS:
            match = pattern.search(page)
            if match:
                image = normalize_url(match.group(1), base_url=response.url)
                if image:
                    return image
        return image_from_html(page, base_url=response.url)
    except requests.RequestException:
        return ""


def stable_id(*values: Any) -> str:
    seed = "|".join(clean_text(value) for value in values if clean_text(value))
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:18]


def normalize_record(raw: dict[str, Any], index: int) -> dict[str, Any] | None:
    show = best_show(raw)
    title = clean_text(first_value(raw.get("title"), raw.get("titile"), raw.get("name")))
    if not title:
        return None

    raw_description = first_value(raw.get("description"), raw.get("descriptionFilterHtml"), raw.get("comment"))
    description = clean_text(raw_description)
    address = clean_text(first_value(
        raw.get("address"), raw.get("location"), show.get("location"), show.get("address")
    ))
    venue = clean_text(first_value(
        raw.get("locationName"), raw.get("venue"), show.get("locationName"), show.get("venue"), address, "地點待確認"
    ))
    start_date = date_string(first_value(raw.get("startDate"), raw.get("start"), show.get("time"), show.get("startTime")))
    end_date = date_string(first_value(
        raw.get("endDate"), raw.get("end"), raw.get("endTime"), show.get("endTime"), start_date
    ))
    event_source_url = source_url(raw)
    uid = clean_text(first_value(raw.get("id"), raw.get("UID"), raw.get("uid"))) or stable_id(
        title, start_date, venue, event_source_url, index
    )
    categories = normalize_categories(
        first_value(raw.get("categories"), raw.get("categoryName"), raw.get("category")), title, description
    )
    price = clean_text(first_value(raw.get("price"), raw.get("Price"), show.get("price"), raw.get("discountInfo")))
    if not price and str(first_value(show.get("onSales"), raw.get("onSales"))).upper() == "N":
        price = "免費"
    if not price:
        price = "票價請見活動頁面"

    latitude, longitude = coordinate_pair(show, raw)

    return {
        "id": uid,
        "title": title,
        "description": description,
        "sourceUrl": event_source_url,
        "image": image_url(raw, show),
        "categories": categories,
        "category": categories[0],
        "startDate": start_date,
        "endDate": end_date,
        "locationName": venue,
        "location": venue,
        "address": address,
        "region": detect_region(raw.get("region"), address, venue),
        "latitude": latitude,
        "longitude": longitude,
        "price": price,
        "unit": clean_text(first_value(raw.get("unit"), raw.get("organizer"), raw.get("showUnit"), raw.get("masterUnit"))),
        "transitInfo": clean_text(first_value(raw.get("transitInfo"), raw.get("transit"))),
        "hitRate": int(raw.get("hitRate") or 0) if str(raw.get("hitRate") or "0").isdigit() else 0,
        "source": clean_text(raw.get("source")) or "文化部開放資料",
    }



def is_demo_record(record: dict[str, Any]) -> bool:
    """Ignore the temporary mock records that shipped with the visual preview."""
    event_url = clean_text(record.get("sourceUrl")).lower()
    description = clean_text(record.get("description"))
    uid = clean_text(record.get("id"))
    title = clean_text(record.get("title"))
    if "example.com" in event_url:
        return True
    if "用於版面檢視" in description:
        return True
    if re.fullmatch(r"e\d+", uid, re.I) and title:
        return True
    return False

def is_still_relevant(record: dict[str, Any], *, past_grace_days: int = 7, future_days: int = 550) -> bool:
    today = datetime.now(TAIPEI_TZ).date()
    start = parse_date(record.get("startDate"))
    end = parse_date(record.get("endDate")) or start
    if end and end < today - timedelta(days=past_grace_days):
        return False
    if start and start > today + timedelta(days=future_days):
        return False
    return True


def dedupe_key(record: dict[str, Any]) -> str:
    uid = clean_text(record.get("id"))
    if uid:
        return f"id:{uid.lower()}"
    event_url = clean_text(record.get("sourceUrl"))
    if event_url:
        return f"url:{event_url.rstrip('/').lower()}"
    return "text:" + stable_id(record.get("title"), record.get("startDate"), record.get("locationName"))


def merge_records(primary: Iterable[dict[str, Any]], existing: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for record in existing:
        if not is_demo_record(record) and is_still_relevant(record):
            merged[dedupe_key(record)] = record
    for record in primary:
        if is_still_relevant(record):
            key = dedupe_key(record)
            old = merged.get(key, {})
            # Empty values from today's feed must not erase a previously discovered image or coordinate.
            merged[key] = {**old, **{k: v for k, v in record.items() if v not in (None, "", [])}}

    def sort_key(item: dict[str, Any]) -> tuple[date, str]:
        return parse_date(item.get("startDate")) or date.max, clean_text(item.get("title"))

    return sorted(merged.values(), key=sort_key)


def place_key(record: dict[str, Any], *, address_first: bool) -> str:
    value = record.get("address") if address_first else record.get("locationName")
    text = clean_text(value).replace("臺", "台")
    text = re.sub(r"[\s　,，、()（）\-]+", "", text).lower()
    region = clean_text(record.get("region")).replace("臺", "台")
    return f"{region}|{text}" if text else ""


def fill_coordinates_from_matching_places(events: list[dict[str, Any]]) -> int:
    address_map: dict[str, tuple[float, float]] = {}
    venue_map: dict[str, tuple[float, float]] = {}
    ambiguous: set[str] = set()

    for event in events:
        lat = event.get("latitude")
        lon = event.get("longitude")
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            continue
        for key, mapping in ((place_key(event, address_first=True), address_map), (place_key(event, address_first=False), venue_map)):
            if not key:
                continue
            pair = (round(float(lat), 6), round(float(lon), 6))
            if key in mapping and mapping[key] != pair:
                ambiguous.add(key)
            else:
                mapping[key] = pair

    for key in ambiguous:
        address_map.pop(key, None)
        venue_map.pop(key, None)

    filled = 0
    for event in events:
        if event.get("latitude") is not None and event.get("longitude") is not None:
            continue
        pair = address_map.get(place_key(event, address_first=True)) or venue_map.get(place_key(event, address_first=False))
        if pair:
            event["latitude"], event["longitude"] = pair
            filled += 1
    return filled


def enrich_missing_images(events: list[dict[str, Any]], *, max_fetches: int = 80, workers: int = 8) -> int:
    candidates = [event for event in events if not valid_http_url(event.get("image")) and valid_http_url(event.get("sourceUrl"))]
    candidates.sort(key=lambda event: int(event.get("hitRate") or 0), reverse=True)
    candidates = candidates[:max_fetches]
    if not candidates:
        return 0

    found = 0
    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = {executor.submit(discover_page_image, event["sourceUrl"]): event for event in candidates}
        for future in as_completed(futures):
            event = futures[future]
            try:
                image = future.result()
            except Exception:  # Defensive: one page must not stop the daily update.
                image = ""
            if image:
                event["image"] = image
                found += 1
    return found


def venue_images(events: Iterable[dict[str, Any]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for event in events:
        venue = clean_text(event.get("locationName"))
        image = valid_http_url(event.get("image"))
        if venue and image and venue not in result:
            result[venue] = image
    return result


def load_existing(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    items = payload if isinstance(payload, list) else payload.get("events", [])
    result = []
    for index, item in enumerate(items):
        if isinstance(item, dict):
            normalized = normalize_record(item, index)
            if normalized:
                normalized["source"] = clean_text(item.get("source")) or normalized["source"]
                result.append(normalized)
    return result


def fetch_json(config: SourceConfig) -> list[dict[str, Any]]:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json,text/plain,*/*"})
    urls = [config.url]
    if config.url == API_URL:
        urls.extend(url for url in API_URLS if url not in urls)

    errors: list[str] = []
    for url in urls:
        for attempt in range(1, config.retries + 1):
            try:
                response = session.get(url, timeout=config.timeout)
                response.raise_for_status()
                response.encoding = response.apparent_encoding or "utf-8"
                payload = response.json()
                if isinstance(payload, dict):
                    payload = payload.get("events") or payload.get("data") or payload.get("result") or []
                if not isinstance(payload, list):
                    raise ValueError("API response is not a JSON array")
                records = [item for item in payload if isinstance(item, dict)]
                if not records:
                    raise ValueError("API returned an empty record list")
                print(f"Fetched {len(records)} source records from {url}")
                return records
            except (requests.RequestException, ValueError, json.JSONDecodeError) as exc:
                message = f"{url} attempt {attempt}/{config.retries}: {exc}"
                errors.append(message)
                print(f"[warning] {message}", file=sys.stderr)
    raise RuntimeError("Unable to fetch source data. " + " | ".join(errors[-6:]))


def read_input_file(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("events") or payload.get("data") or payload.get("result") or []
    if not isinstance(payload, list):
        raise ValueError("Input JSON must be an array or an object containing events/data/result")
    return [item for item in payload if isinstance(item, dict)]


def write_output(path: Path, events: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image_count = sum(1 for event in events if valid_http_url(event.get("image")))
    coordinate_count = sum(
        1 for event in events
        if event.get("latitude") is not None and event.get("longitude") is not None
    )
    payload = {
        "updatedAt": datetime.now(TAIPEI_TZ).isoformat(timespec="seconds"),
        "source": "文化部文化資料開放服務網與既有自訂資料",
        "stats": {
            "eventCount": len(events),
            "imageCount": image_count,
            "coordinateCount": coordinate_count,
            "imageCoverage": round(image_count / len(events), 4) if events else 0,
            "coordinateCoverage": round(coordinate_count / len(events), 4) if events else 0,
        },
        "events": events,
        "venueImages": venue_images(events),
    }
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--input-file", type=Path, help="Read source records from a local JSON file instead of the API")
    parser.add_argument("--no-preserve-existing", action="store_true", help="Do not merge still-valid records already in the output file")
    parser.add_argument("--no-image-enrichment", action="store_true", help="Do not inspect source pages for missing Open Graph images")
    parser.add_argument("--max-image-fetches", type=int, default=int(os.environ.get("MAX_IMAGE_FETCHES", "80")))
    parser.add_argument("--api-url", default=os.environ.get("EXHIBITION_API_URL", API_URL))
    args = parser.parse_args()

    existing = [] if args.no_preserve_existing else load_existing(args.output)
    raw_records = read_input_file(args.input_file) if args.input_file else fetch_json(SourceConfig(url=args.api_url))
    normalized = []
    for index, raw in enumerate(raw_records):
        record = normalize_record(raw, index)
        if record:
            normalized.append(record)

    events = merge_records(normalized, existing)
    coordinate_fills = fill_coordinates_from_matching_places(events)
    image_fills = 0
    if not args.no_image_enrichment and not args.input_file:
        image_fills = enrich_missing_images(events, max_fetches=max(0, args.max_image_fetches))

    write_output(args.output, events)
    image_count = sum(1 for event in events if valid_http_url(event.get("image")))
    coordinate_count = sum(1 for event in events if event.get("latitude") is not None and event.get("longitude") is not None)
    print(
        f"Wrote {len(events)} events to {args.output}; "
        f"images={image_count} (enriched {image_fills}); "
        f"coordinates={coordinate_count} (inherited {coordinate_fills})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
