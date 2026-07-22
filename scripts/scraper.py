#!/usr/bin/env python3
"""Build data/exhibitions.json for the Exhibition Hub GitHub Pages site.

Primary source: Ministry of Culture open data API (all categories).
The script also keeps still-valid custom records already present in the output file,
so replacing the frontend does not erase events collected by other sources.

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
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

import requests

API_URLS = [
    # 政府資料開放平臺目前實際的 JSON 資源網址
    "https://cloud.culture.tw/frontsite/trans/SearchShowAction.do?method=doFindTypeJ&category=all",
    # 文化部資料集備註所列的 OAS 介接網址，保留為備援
    "https://cloud.culture.tw/frontsite/trans/SearchShowAction.do?method=doFindTypeJOpenApi&category=all",
]
API_URL = API_URLS[0]
DEFAULT_OUTPUT = Path("data/exhibitions.json")
TAIPEI_TZ = timezone(timedelta(hours=8))
USER_AGENT = "TaiwanExhibitionJournal/3.0 (+https://github.com/jackyyu0130/exhibition-hub)"

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


def valid_http_url(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return ""
    parsed = urlparse(text)
    return text if parsed.scheme in {"http", "https"} and parsed.netloc else ""


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
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    limit = 90 if latitude else 180
    if not -limit <= number <= limit or number == 0:
        return None
    return round(number, 7)


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


def image_url(raw: dict[str, Any]) -> str:
    candidates: list[Any] = [raw.get("image"), raw.get("imageURL"), raw.get("imageUrl")]
    images = raw.get("images")
    if isinstance(images, list):
        candidates.extend(images)
    for candidate in candidates:
        if isinstance(candidate, dict):
            candidate = first_value(candidate.get("url"), candidate.get("src"), candidate.get("image"))
        url = valid_http_url(candidate)
        if url:
            return url
    return ""


def stable_id(*values: Any) -> str:
    seed = "|".join(clean_text(value) for value in values if clean_text(value))
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:18]


def normalize_record(raw: dict[str, Any], index: int) -> dict[str, Any] | None:
    show_info = raw.get("showinfo")
    show = show_info[0] if isinstance(show_info, list) and show_info else {}
    if not isinstance(show, dict):
        show = {}

    title = clean_text(first_value(raw.get("title"), raw.get("titile"), raw.get("name")))
    if not title:
        return None

    description = clean_text(first_value(raw.get("description"), raw.get("descriptionFilterHtml"), raw.get("comment")))
    address = clean_text(first_value(raw.get("address"), raw.get("location"), show.get("location")))
    venue = clean_text(first_value(raw.get("locationName"), raw.get("venue"), show.get("locationName"), address, "地點待確認"))
    start_date = date_string(first_value(raw.get("startDate"), raw.get("start"), show.get("time")))
    end_date = date_string(first_value(raw.get("endDate"), raw.get("end"), raw.get("endTime"), show.get("endTime"), start_date))
    source_url = valid_http_url(first_value(raw.get("sourceUrl"), raw.get("sourceWebPromote"), raw.get("webSales"), raw.get("sourceWebSite"), raw.get("url")))
    uid = clean_text(first_value(raw.get("id"), raw.get("UID"), raw.get("uid"))) or stable_id(title, start_date, venue, source_url, index)
    categories = normalize_categories(first_value(raw.get("categories"), raw.get("categoryName"), raw.get("category")), title, description)
    price = clean_text(first_value(raw.get("price"), raw.get("Price"), show.get("price"), raw.get("discountInfo")))
    if not price and str(raw.get("onSales", "")).upper() == "N":
        price = "免費"
    if not price:
        price = "票價請見活動頁面"

    latitude = number_or_none(first_value(raw.get("latitude"), raw.get("lat"), show.get("latitude")), latitude=True)
    longitude = number_or_none(first_value(raw.get("longitude"), raw.get("lng"), show.get("longitude")), latitude=False)

    return {
        "id": uid,
        "title": title,
        "description": description,
        "sourceUrl": source_url,
        "image": image_url(raw),
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
    source_url = clean_text(record.get("sourceUrl"))
    if source_url:
        return f"url:{source_url.rstrip('/').lower()}"
    return "text:" + stable_id(record.get("title"), record.get("startDate"), record.get("locationName"))


def merge_records(primary: Iterable[dict[str, Any]], existing: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for record in existing:
        if is_still_relevant(record):
            merged[dedupe_key(record)] = record
    for record in primary:
        if is_still_relevant(record):
            key = dedupe_key(record)
            old = merged.get(key, {})
            merged[key] = {**old, **{k: v for k, v in record.items() if v not in (None, "", [])}}

    def sort_key(item: dict[str, Any]) -> tuple[date, str]:
        return parse_date(item.get("startDate")) or date.max, clean_text(item.get("title"))

    return sorted(merged.values(), key=sort_key)


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
                # Keep source attribution from custom datasets when available.
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
    payload = {
        "updatedAt": datetime.now(TAIPEI_TZ).isoformat(timespec="seconds"),
        "source": "文化部文化資料開放服務網與既有自訂資料",
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
    write_output(args.output, events)
    print(f"Wrote {len(events)} events to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
