#!/usr/bin/env python3
"""Build data/exhibitions.json for Taiwan Exhibition Journal.

The updater combines the Ministry of Culture all-category feed with each official
category feed, normalizes inconsistent field names, preserves previously found
media/coordinates, incrementally enriches missing images from official source
pages, and geocodes a small cached batch of missing addresses each run.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator
from urllib.parse import unquote, urljoin, urlparse

import requests

CULTURE_BASE_URL = "https://cloud.culture.tw/"
API_TEMPLATE = CULTURE_BASE_URL + "frontsite/trans/SearchShowAction.do?method={method}&category={category}"
API_METHODS = ("doFindTypeJ", "doFindTypeJOpenApi")
DEFAULT_OUTPUT = Path("data/exhibitions.json")
DEFAULT_GEOCODE_CACHE = Path("data/geocode-cache.json")
DETAIL_API_URL = CULTURE_BASE_URL + "frontsite/opendata/activityOpenDataJsonAction.do"
TAIPEI_TZ = timezone(timedelta(hours=8))
USER_AGENT = "TaiwanExhibitionJournal/3.3 (+https://github.com/jackyyu0130/exhibition-hub)"

# Official Culture Ministry category codes.
CATEGORY_CODE_MAP = {
    "1": "音樂",      # 音樂表演
    "2": "表演",      # 戲劇表演
    "3": "舞蹈",
    "4": "親子",
    "5": "音樂",      # 獨立音樂
    "6": "美術",      # 展覽資訊
    "7": "講座",
    "8": "電影",
    "11": "表演",     # 綜藝活動
    "13": "競賽",
    "14": "徵選",
    "15": "其他",
    "17": "音樂",     # 演唱會
    "19": "研習",
}
CATEGORY_FEEDS = tuple(CATEGORY_CODE_MAP)
ALLOWED_CATEGORIES = (
    "快閃", "美術", "攝影", "設計", "動漫", "音樂", "表演", "舞蹈", "講座",
    "市集", "商展", "電影", "親子", "競賽", "徵選", "研習", "其他",
)
CATEGORY_ALIASES = {
    "展覽": "美術", "展覽資訊": "美術", "藝術": "美術", "視覺藝術": "美術",
    "戲劇": "表演", "戲劇表演": "表演", "綜藝": "表演", "綜藝活動": "表演",
    "音樂表演": "音樂", "獨立音樂": "音樂", "演唱會": "音樂",
    "講座資訊": "講座", "親子活動": "親子", "電影欣賞": "電影",
    "競賽活動": "競賽", "徵選活動": "徵選", "研習課程": "研習",
    "其他藝文資訊": "其他",
}

REGION_ALIASES = {"臺北市": "台北市", "臺中市": "台中市", "臺南市": "台南市", "臺東縣": "台東縣"}
REGIONS = [
    "台北市", "新北市", "基隆市", "桃園市", "新竹市", "新竹縣", "苗栗縣", "台中市",
    "彰化縣", "南投縣", "雲林縣", "嘉義市", "嘉義縣", "台南市", "高雄市", "屏東縣",
    "宜蘭縣", "花蓮縣", "台東縣", "澎湖縣", "金門縣", "連江縣",
]

KEYWORD_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("快閃", re.compile(r"快閃|期間限定|popup|pop-up", re.I)),
    ("攝影", re.compile(r"攝影|影像展|photo(?:graphy)?", re.I)),
    ("動漫", re.compile(r"動漫|動畫|漫畫|卡通|anime|公仔|角色展|模型展", re.I)),
    ("設計", re.compile(r"設計|建築|工藝|時尚|design", re.I)),
    ("舞蹈", re.compile(r"舞蹈|舞作|芭蕾", re.I)),
    ("音樂", re.compile(r"音樂|演唱會|樂團|管弦|獨立音樂|concert", re.I)),
    ("表演", re.compile(r"戲劇|劇場|表演|歌劇|馬戲|音樂劇|偶戲", re.I)),
    ("講座", re.compile(r"講座|論壇|座談|分享會|演講", re.I)),
    ("研習", re.compile(r"研習|課程|工作坊|營隊", re.I)),
    ("市集", re.compile(r"市集|祭典|嘉年華|文創攤位", re.I)),
    ("商展", re.compile(r"展售|博覽會|商展|產業展|商品展", re.I)),
    ("電影", re.compile(r"電影|影展|放映", re.I)),
    ("親子", re.compile(r"親子|兒童|家庭|幼兒", re.I)),
    ("競賽", re.compile(r"競賽|比賽|大賽|徵件比賽", re.I)),
    ("徵選", re.compile(r"徵選|徵件|徵稿|招募", re.I)),
    ("美術", re.compile(r"美術|藝術|繪畫|雕塑|裝置|當代|典藏|書畫|陶藝|視覺藝術", re.I)),
]

IMAGE_META_PATTERNS = [
    re.compile(r'<meta[^>]+(?:property|name)=["\']og:image(?::secure_url)?["\'][^>]+content=["\']([^"\']+)', re.I),
    re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']og:image(?::secure_url)?["\']', re.I),
    re.compile(r'<meta[^>]+(?:property|name)=["\']twitter:image(?::src)?["\'][^>]+content=["\']([^"\']+)', re.I),
    re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']twitter:image(?::src)?["\']', re.I),
    re.compile(r'<link[^>]+rel=["\']image_src["\'][^>]+href=["\']([^"\']+)', re.I),
]
IMG_SRC_PATTERN = re.compile(r'<img[^>]+(?:src|data-src|data-original|data-lazy-src)=["\']([^"\']+)', re.I)
IMG_SRCSET_PATTERN = re.compile(r'<(?:img|source)[^>]+(?:srcset|data-srcset)=["\']([^"\']+)', re.I)
JSON_IMAGE_PATTERN = re.compile(r'["\'](?:image|imageUrl|imageURL|thumbnailUrl|contentUrl)["\']\s*:\s*["\']([^"\']+)', re.I)
BACKGROUND_IMAGE_PATTERN = re.compile(r'background(?:-image)?\s*:\s*url\(["\']?([^"\')]+)', re.I)
BAD_IMAGE_HINTS = re.compile(r"(?:favicon|logo|icon|avatar|spacer|blank|loading|pixel|sprite|qr[_-]?code)", re.I)


@dataclass(frozen=True)
class SourceConfig:
    timeout: int = 45
    retries: int = 3
    workers: int = 6


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        value = "、".join(item for item in (clean_text(v) for v in value) if item)
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
        keys = ("url", "src", "href", "image", "imageUrl", "imageURL", "original", "large", "poster", "cover")
        preferred = [value[key] for key in keys if key in value]
        for item in preferred or value.values():
            yield from flatten_values(item)
        return
    if isinstance(value, str):
        stripped = value.strip()
        if (stripped.startswith("[") and stripped.endswith("]")) or (stripped.startswith("{") and stripped.endswith("}")):
            try:
                yield from flatten_values(json.loads(stripped))
                return
            except json.JSONDecodeError:
                pass
    yield value


def normalize_url(value: Any, *, base_url: str = CULTURE_BASE_URL) -> str:
    text = html.unescape(str(value or "")).strip().strip('"\'')
    if not text or text.startswith("data:"):
        return ""
    text = text.replace("\\/", "/")
    if re.match(r"^https?%3A", text, re.I):
        text = unquote(text)
    if text.startswith("//"):
        text = "https:" + text
    text = urljoin(base_url, text)
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return text


def unique_urls(values: Iterable[Any], *, base_url: str = CULTURE_BASE_URL) -> list[str]:
    result: list[str] = []
    for raw in values:
        url = normalize_url(raw, base_url=base_url)
        if url and url not in result:
            result.append(url)
    return result


def valid_http_url(value: Any) -> str:
    return normalize_url(value)


def parse_date(value: Any) -> date | None:
    text = clean_text(value).replace("/", "-")
    if not text:
        return None
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
        number = float(str(value).strip().replace(",", "."))
    except (TypeError, ValueError):
        return None
    limit = 90 if latitude else 180
    if number == 0 or not -limit <= number <= limit:
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


def split_category_values(raw: Any) -> Iterator[str]:
    values = raw if isinstance(raw, list) else [raw]
    for value in values:
        for item in re.split(r"[、,，/|;；]+", clean_text(value)):
            item = item.strip()
            if item:
                yield item


def normalize_categories(raw_category: Any, title: str, description: str, feed_category: Any = "") -> list[str]:
    categories: list[str] = []
    for value in [*split_category_values(raw_category), *split_category_values(feed_category)]:
        mapped = CATEGORY_CODE_MAP.get(value) or CATEGORY_ALIASES.get(value) or (value if value in ALLOWED_CATEGORIES else "")
        if mapped and mapped not in categories:
            categories.append(mapped)

    combined = f"{title} {description}"
    for category, pattern in KEYWORD_RULES:
        if pattern.search(combined) and category not in categories:
            categories.insert(0, category)

    cleaned = [category for category in categories if category in ALLOWED_CATEGORIES]
    if not cleaned:
        cleaned = ["其他"]
    return list(dict.fromkeys(cleaned))[:3]


def show_entries(raw: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for key in ("showInfo", "showinfo", "show_info", "shows", "sessions"):
        value = raw.get(key)
        if isinstance(value, dict):
            entries.append(value)
        elif isinstance(value, list):
            entries.extend(item for item in value if isinstance(item, dict))
    return entries


def normalize_session(show: dict[str, Any]) -> dict[str, Any]:
    lat, lon = coordinate_pair(show)
    return {
        "time": date_string(first_value(show.get("time"), show.get("startTime"))),
        "endTime": date_string(first_value(show.get("endTime"), show.get("end"))),
        "locationName": clean_text(first_value(show.get("locationName"), show.get("venue"))),
        "address": clean_text(first_value(show.get("location"), show.get("address"))),
        "latitude": lat,
        "longitude": lon,
        "price": clean_text(first_value(show.get("price"), show.get("Price"))),
        "onSales": clean_text(show.get("onSales")),
    }


def show_score(show: dict[str, Any]) -> int:
    lat, lon = coordinate_pair(show)
    return (
        (100 if lat is not None and lon is not None else 0)
        + (25 if clean_text(first_value(show.get("locationName"), show.get("venue"))) else 0)
        + (20 if clean_text(first_value(show.get("location"), show.get("address"))) else 0)
        + (5 if clean_text(first_value(show.get("time"), show.get("startTime"))) else 0)
    )


def best_show(raw: dict[str, Any]) -> dict[str, Any]:
    entries = show_entries(raw)
    return max(entries, key=show_score) if entries else {}


def image_field_values(raw: dict[str, Any], show: dict[str, Any] | None = None) -> Iterator[Any]:
    keys = (
        "image", "images", "imageCandidates", "imageUrl", "imageURL", "imageURLList", "imageUrls",
        "poster", "posterUrl", "picture", "pictureUrl", "photo", "photoUrl", "cover", "coverUrl", "representImage",
    )
    for source in (raw, show or {}):
        for key in keys:
            if key in source:
                yield from flatten_values(source.get(key))


def image_from_html(raw_html: Any, *, base_url: str = CULTURE_BASE_URL) -> list[str]:
    text = html.unescape(str(raw_html or ""))
    return unique_urls((match.group(1) for match in IMG_SRC_PATTERN.finditer(text)), base_url=base_url)


def source_url(raw: dict[str, Any]) -> str:
    for candidate in (
        raw.get("sourceUrl"), raw.get("sourceWebPromote"), raw.get("sourceWebSite"), raw.get("website"),
        raw.get("url"), raw.get("webSales"),
    ):
        url = normalize_url(candidate)
        if url:
            return url
    return ""


def collect_image_urls(raw: dict[str, Any], show: dict[str, Any] | None = None, *, page_base: str = CULTURE_BASE_URL) -> list[str]:
    urls = unique_urls(image_field_values(raw, show), base_url=page_base)
    urls.extend(url for url in image_from_html(first_value(raw.get("descriptionFilterHtml"), raw.get("description")), base_url=page_base) if url not in urls)
    return urls[:8]


def probable_content_image(url: str) -> bool:
    parsed = urlparse(url)
    if BAD_IMAGE_HINTS.search(parsed.path):
        return False
    if parsed.path.lower().endswith(".svg"):
        return False
    return True


def discover_page_images(url: str, *, timeout: int = 14) -> list[str]:
    if not url:
        return []
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
            return []
        page = response.text[:1_200_000]
        candidates: list[str] = []
        for pattern in IMAGE_META_PATTERNS:
            candidates.extend(match.group(1) for match in pattern.finditer(page))
        candidates.extend(match.group(1) for match in IMG_SRC_PATTERN.finditer(page))
        for match in IMG_SRCSET_PATTERN.finditer(page):
            for candidate in match.group(1).split(","):
                candidates.append(candidate.strip().split(" ")[0])
        candidates.extend(match.group(1) for match in JSON_IMAGE_PATTERN.finditer(page))
        candidates.extend(match.group(1) for match in BACKGROUND_IMAGE_PATTERN.finditer(page))
        return [item for item in unique_urls(candidates, base_url=response.url) if probable_content_image(item)][:10]
    except requests.RequestException:
        return []


def stable_id(*values: Any) -> str:
    seed = "|".join(clean_text(value) for value in values if clean_text(value))
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:18]


def normalize_record(raw: dict[str, Any], index: int) -> dict[str, Any] | None:
    show = best_show(raw)
    title = clean_text(first_value(raw.get("title"), raw.get("titile"), raw.get("name"), raw.get("actName")))
    if not title:
        return None

    raw_description = first_value(raw.get("description"), raw.get("descriptionFilterHtml"), raw.get("comment"))
    description = clean_text(raw_description)
    event_source_url = source_url(raw)
    address = clean_text(first_value(raw.get("address"), raw.get("location"), show.get("location"), show.get("address")))
    venue = clean_text(first_value(raw.get("locationName"), raw.get("venue"), show.get("locationName"), show.get("venue"), address, "地點待確認"))
    start_date = date_string(first_value(raw.get("startDate"), raw.get("start"), raw.get("startTime"), show.get("time"), show.get("startTime")))
    end_date = date_string(first_value(raw.get("endDate"), raw.get("end"), raw.get("endTime"), show.get("endTime"), start_date))
    uid = clean_text(first_value(raw.get("id"), raw.get("UID"), raw.get("uid"), raw.get("actId"))) or stable_id(title, start_date, venue, event_source_url, index)
    categories = normalize_categories(
        first_value(raw.get("categories"), raw.get("categoryName"), raw.get("category")),
        title,
        description,
        raw.get("_feedCategory", ""),
    )
    price = clean_text(first_value(raw.get("price"), raw.get("Price"), show.get("price"), raw.get("discountInfo"), raw.get("charge")))
    if not price and str(first_value(show.get("onSales"), raw.get("onSales"))).upper() == "N":
        price = "免費"
    if not price:
        price = "票價請見活動頁面"

    latitude, longitude = coordinate_pair(show, raw)
    sessions = [normalize_session(item) for item in show_entries(raw)]
    sessions = [item for item in sessions if any(value not in (None, "") for value in item.values())]
    images = collect_image_urls(raw, show, page_base=event_source_url or CULTURE_BASE_URL)

    return {
        "id": uid,
        "title": title,
        "description": description,
        "sourceUrl": event_source_url,
        "image": images[0] if images else "",
        "images": images,
        "categories": categories,
        "category": categories[0],
        "startDate": start_date,
        "endDate": end_date,
        "locationName": venue,
        "location": venue,
        "address": address,
        "region": detect_region(raw.get("region"), raw.get("cityName"), address, venue),
        "latitude": latitude,
        "longitude": longitude,
        "price": price,
        "unit": clean_text(first_value(raw.get("unit"), raw.get("organizer"), raw.get("showUnit"), raw.get("masterUnit"), raw.get("org"))),
        "transitInfo": clean_text(first_value(raw.get("transitInfo"), raw.get("transit"), raw.get("travellinginfo"))),
        "parkingInfo": clean_text(first_value(raw.get("parkingInfo"), raw.get("parkinginfo"))),
        "phone": clean_text(first_value(raw.get("phone"), raw.get("tel"))),
        "comment": clean_text(raw.get("comment")),
        "sessions": sessions,
        "hitRate": int(raw.get("hitRate") or 0) if str(raw.get("hitRate") or "0").isdigit() else 0,
        "source": clean_text(first_value(raw.get("source"), raw.get("sourceWebName"))) or "文化部開放資料",
    }


def is_demo_record(record: dict[str, Any]) -> bool:
    event_url = clean_text(record.get("sourceUrl")).lower()
    description = clean_text(record.get("description"))
    uid = clean_text(record.get("id"))
    if "example.com" in event_url or "用於版面檢視" in description:
        return True
    return bool(re.fullmatch(r"e\d+", uid, re.I) and clean_text(record.get("title")))


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


def merge_list_values(old: Any, new: Any) -> list[Any]:
    result: list[Any] = []
    for value in [*(old if isinstance(old, list) else []), *(new if isinstance(new, list) else [])]:
        marker = json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else str(value)
        if marker not in {json.dumps(item, ensure_ascii=False, sort_keys=True) if isinstance(item, (dict, list)) else str(item) for item in result}:
            result.append(value)
    return result


def merge_two_records(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    merged = dict(old)
    placeholders = {"地點待確認", "票價請見活動頁面", "其他地區", "文化部開放資料"}
    for key, value in new.items():
        if value in (None, "", []):
            continue
        old_value = old.get(key)
        if isinstance(value, str) and value in placeholders and old_value not in (None, "", [], value):
            continue
        if key == "description" and len(clean_text(value)) < len(clean_text(old_value)):
            continue
        merged[key] = value
    merged["images"] = merge_list_values(old.get("images"), new.get("images"))[:10]
    if merged["images"]:
        merged["image"] = merged["images"][0]
    merged["categories"] = [item for item in merge_list_values(new.get("categories"), old.get("categories")) if item in ALLOWED_CATEGORIES][:3] or ["其他"]
    merged["category"] = merged["categories"][0]
    merged["sessions"] = merge_list_values(old.get("sessions"), new.get("sessions"))
    return merged


def merge_records(primary: Iterable[dict[str, Any]], existing: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for record in existing:
        if not is_demo_record(record) and is_still_relevant(record):
            merged[dedupe_key(record)] = record
    for record in primary:
        if is_still_relevant(record):
            key = dedupe_key(record)
            merged[key] = merge_two_records(merged[key], record) if key in merged else record

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
        lat, lon = event.get("latitude"), event.get("longitude")
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


def load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def normalize_geocode_key(event: dict[str, Any]) -> str:
    query = clean_text(first_value(event.get("address"), f"{event.get('locationName', '')} {event.get('region', '')}"))
    query = query.replace("臺", "台")
    return re.sub(r"\s+", " ", query).strip()


def geocode_missing_coordinates(events: list[dict[str, Any]], *, cache_path: Path, max_fetches: int = 25) -> int:
    cache = load_json_object(cache_path)
    candidates = [
        event for event in events
        if event.get("latitude") is None and event.get("longitude") is None
        and normalize_geocode_key(event) and event.get("locationName") != "地點待確認"
    ]
    candidates.sort(key=lambda event: int(event.get("hitRate") or 0), reverse=True)
    network_used = 0
    filled = 0
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})

    for event in candidates:
        key = normalize_geocode_key(event)
        if key in cache:
            pair = cache[key]
            if isinstance(pair, list) and len(pair) == 2:
                event["latitude"], event["longitude"] = pair
                filled += 1
            continue
        if network_used >= max_fetches:
            break
        try:
            response = session.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": f"{key}, Taiwan", "format": "jsonv2", "limit": 1, "countrycodes": "tw"},
                timeout=18,
            )
            response.raise_for_status()
            data = response.json()
            if data:
                lat = number_or_none(data[0].get("lat"), latitude=True)
                lon = number_or_none(data[0].get("lon"), latitude=False)
                if lat is not None and lon is not None and 20 <= lat <= 27 and 118 <= lon <= 123.8:
                    cache[key] = [lat, lon]
                    event["latitude"], event["longitude"] = lat, lon
                    filled += 1
                else:
                    cache[key] = None
            else:
                cache[key] = None
        except (requests.RequestException, ValueError, json.JSONDecodeError):
            # Do not cache temporary failures.
            pass
        network_used += 1
        time.sleep(1.05)

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    return filled



def fetch_activity_detail(uid: str, *, timeout: int = 20) -> dict[str, Any]:
    """Fetch the official single-activity record when the list feed is incomplete."""
    if not uid:
        return {}
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json,text/plain,*/*"})
    for method in ("doFindActivityByIdOpenApi", "doFindActivityById"):
        try:
            response = session.get(DETAIL_API_URL, params={"method": method, "id": uid}, timeout=timeout)
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, list):
                payload = next((item for item in payload if isinstance(item, dict)), {})
            if isinstance(payload, dict):
                nested = payload.get("data") or payload.get("result") or payload.get("event")
                if isinstance(nested, list):
                    nested = next((item for item in nested if isinstance(item, dict)), {})
                if isinstance(nested, dict):
                    payload = nested
                if clean_text(first_value(payload.get("title"), payload.get("titile"), payload.get("UID"), payload.get("id"))):
                    return payload
        except (requests.RequestException, ValueError, json.JSONDecodeError):
            continue
    return {}


def enrich_from_official_details(events: list[dict[str, Any]], *, max_fetches: int = 250, workers: int = 8) -> int:
    """Fill missing media/location/description from the official per-event endpoint."""
    candidates = [
        event for event in events
        if event.get("id") and (
            not event.get("images")
            or event.get("latitude") is None
            or event.get("longitude") is None
            or not clean_text(event.get("address"))
            or len(clean_text(event.get("description"))) < 60
        )
    ]
    candidates.sort(key=lambda event: int(event.get("hitRate") or 0), reverse=True)
    candidates = candidates[:max_fetches]
    if not candidates:
        return 0

    enriched = 0
    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = {executor.submit(fetch_activity_detail, clean_text(event.get("id"))): event for event in candidates}
        for future in as_completed(futures):
            event = futures[future]
            try:
                raw = future.result()
            except Exception:
                raw = {}
            if not raw:
                continue
            raw.setdefault("UID", event.get("id"))
            normalized = normalize_record(raw, 0)
            if normalized:
                merged = merge_two_records(event, normalized)
                event.clear()
                event.update(merged)
                enriched += 1
    return enriched

def enrich_missing_images(events: list[dict[str, Any]], *, max_fetches: int = 300, workers: int = 10) -> int:
    candidates = [event for event in events if not event.get("images") and valid_http_url(event.get("sourceUrl"))]
    candidates.sort(key=lambda event: int(event.get("hitRate") or 0), reverse=True)
    candidates = candidates[:max_fetches]
    if not candidates:
        return 0

    found = 0
    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = {executor.submit(discover_page_images, event["sourceUrl"]): event for event in candidates}
        for future in as_completed(futures):
            event = futures[future]
            try:
                images = future.result()
            except Exception:
                images = []
            if images:
                event["images"] = merge_list_values(event.get("images"), images)[:10]
                event["image"] = event["images"][0]
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
    payload = load_json_object(path)
    items = payload.get("events", [])
    result: list[dict[str, Any]] = []
    for index, item in enumerate(items if isinstance(items, list) else []):
        if isinstance(item, dict):
            normalized = normalize_record(item, index)
            if normalized:
                normalized = merge_two_records(normalized, item)
                result.append(normalized)
    return result


def extract_payload(response: requests.Response) -> list[dict[str, Any]]:
    response.encoding = response.apparent_encoding or "utf-8"
    payload = response.json()
    if isinstance(payload, dict):
        payload = payload.get("events") or payload.get("data") or payload.get("result") or []
    if not isinstance(payload, list):
        raise ValueError("API response is not a JSON array")
    records = [item for item in payload if isinstance(item, dict)]
    if not records:
        raise ValueError("API returned an empty record list")
    return records


def fetch_category(category: str, config: SourceConfig) -> list[dict[str, Any]]:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json,text/plain,*/*"})
    errors: list[str] = []
    for method in API_METHODS:
        url = API_TEMPLATE.format(method=method, category=category)
        for attempt in range(1, config.retries + 1):
            try:
                response = session.get(url, timeout=config.timeout)
                response.raise_for_status()
                records = extract_payload(response)
                for record in records:
                    record.setdefault("_feedCategory", category)
                print(f"Fetched {len(records)} records for category={category} via {method}")
                return records
            except (requests.RequestException, ValueError, json.JSONDecodeError) as exc:
                errors.append(f"{url} attempt {attempt}/{config.retries}: {exc}")
    print(f"[warning] category={category} failed: {' | '.join(errors[-3:])}", file=sys.stderr)
    return []


def fetch_all_json(config: SourceConfig) -> list[dict[str, Any]]:
    categories = ("all", *CATEGORY_FEEDS)
    records: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=config.workers) as executor:
        futures = {executor.submit(fetch_category, category, config): category for category in categories}
        for future in as_completed(futures):
            records.extend(future.result())
    if not records:
        raise RuntimeError("Unable to fetch any exhibition records from the Culture Ministry feeds")
    return records


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
    multi_image_count = sum(1 for event in events if len(event.get("images") or []) > 1)
    coordinate_count = sum(1 for event in events if event.get("latitude") is not None and event.get("longitude") is not None)
    category_counts: dict[str, int] = {}
    for event in events:
        for category in event.get("categories") or [event.get("category")]:
            if category:
                category_counts[category] = category_counts.get(category, 0) + 1
    payload = {
        "updatedAt": datetime.now(TAIPEI_TZ).isoformat(timespec="seconds"),
        "source": "文化部文化資料開放服務網；活動官方頁面；既有快取資料",
        "stats": {
            "eventCount": len(events),
            "imageCount": image_count,
            "multiImageCount": multi_image_count,
            "coordinateCount": coordinate_count,
            "imageCoverage": round(image_count / len(events), 4) if events else 0,
            "coordinateCoverage": round(coordinate_count / len(events), 4) if events else 0,
            "categoryCounts": category_counts,
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
    parser.add_argument("--input-file", type=Path, help="Read records from local JSON instead of official APIs")
    parser.add_argument("--no-preserve-existing", action="store_true")
    parser.add_argument("--no-image-enrichment", action="store_true")
    parser.add_argument("--no-geocoding", action="store_true")
    parser.add_argument("--max-detail-fetches", type=int, default=int(os.environ.get("MAX_DETAIL_FETCHES", "250")))
    parser.add_argument("--max-image-fetches", type=int, default=int(os.environ.get("MAX_IMAGE_FETCHES", "300")))
    parser.add_argument("--max-geocodes", type=int, default=int(os.environ.get("MAX_GEOCODES", "25")))
    parser.add_argument("--geocode-cache", type=Path, default=DEFAULT_GEOCODE_CACHE)
    args = parser.parse_args()

    existing = [] if args.no_preserve_existing else load_existing(args.output)
    raw_records = read_input_file(args.input_file) if args.input_file else fetch_all_json(SourceConfig())
    normalized = [record for index, raw in enumerate(raw_records) if (record := normalize_record(raw, index))]
    events = merge_records(normalized, existing)

    detail_enriched = 0
    if not args.input_file and args.max_detail_fetches > 0:
        detail_enriched = enrich_from_official_details(events, max_fetches=args.max_detail_fetches)

    inherited_coordinates = fill_coordinates_from_matching_places(events)
    geocoded = 0
    if not args.no_geocoding and not args.input_file and args.max_geocodes > 0:
        geocoded = geocode_missing_coordinates(events, cache_path=args.geocode_cache, max_fetches=args.max_geocodes)

    enriched_images = 0
    if not args.no_image_enrichment and not args.input_file and args.max_image_fetches > 0:
        enriched_images = enrich_missing_images(events, max_fetches=args.max_image_fetches)

    write_output(args.output, events)
    image_count = sum(1 for event in events if valid_http_url(event.get("image")))
    coordinate_count = sum(1 for event in events if event.get("latitude") is not None and event.get("longitude") is not None)
    print(
        f"Wrote {len(events)} events to {args.output}; official-details enriched={detail_enriched}; images={image_count} "
        f"(source-page enriched {enriched_images}); coordinates={coordinate_count} "
        f"(matched {inherited_coordinates}, geocoded {geocoded})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
