#!/usr/bin/env python3
"""Build data/exhibitions.json for Taiwan Exhibition Journal.

The updater combines the Ministry of Culture all-category feed with each official
category feed, normalizes inconsistent field names, preserves previously found
media/coordinates, incrementally enriches missing images from official source
pages, and geocodes a small cached batch of missing addresses each run.
"""

from __future__ import annotations

import argparse
from difflib import SequenceMatcher
import hashlib
import html
import json
import math
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

try:
    import requests
except ModuleNotFoundError:  # Offline maintenance still works before dependencies are installed.
    class _RequestsFallback:
        class RequestException(RuntimeError):
            pass

        class Response:
            pass

        @staticmethod
        def get(*_args, **_kwargs):
            raise _RequestsFallback.RequestException("Install requirements.txt for network updates")

        class Session:
            def __init__(self):
                self.headers = {}

            def get(self, *_args, **_kwargs):
                raise _RequestsFallback.RequestException("Install requirements.txt for network updates")

    requests = _RequestsFallback()

CULTURE_BASE_URL = "https://cloud.culture.tw/"
API_TEMPLATE = CULTURE_BASE_URL + "frontsite/trans/SearchShowAction.do?method={method}&category={category}"
API_METHODS = ("doFindTypeJ", "doFindTypeJOpenApi")
DEFAULT_OUTPUT = Path("data/exhibitions.json")
DEFAULT_GEOCODE_CACHE = Path("data/geocode-cache.json")
DEFAULT_CURATED_OVERRIDES = Path("data/curated-overrides.json")
DETAIL_API_URL = CULTURE_BASE_URL + "frontsite/opendata/activityOpenDataJsonAction.do"
TAIPEI_TZ = timezone(timedelta(hours=8))
USER_AGENT = "TaiwanExhibitionJournal/4.4 (+https://github.com/jackyyu0130/exhibition-hub)"
DEFAULT_VENUE_ALIASES = Path("data/venue-aliases.json")

# Official Culture Ministry category codes. Public-facing categories deliberately
# omit 「徵選」 and 「商展」; those records are reclassified from their content.
CATEGORY_CODE_MAP = {
    "1": "音樂", "2": "表演", "3": "舞蹈", "4": "親子", "5": "音樂",
    "6": "美術", "7": "其他", "8": "電影", "11": "表演", "13": "競賽",
    "14": "其他", "15": "其他", "17": "音樂", "19": "其他",
}
CATEGORY_FEEDS = tuple(CATEGORY_CODE_MAP)
ALLOWED_CATEGORIES = (
    "快閃", "美術", "攝影", "設計", "動漫", "歷史文化", "自然科學", "親子",
    "音樂", "表演", "舞蹈", "電影", "市集", "競賽", "科技", "其他",
)
CATEGORY_ALIASES = {
    "展覽": "美術", "展覽資訊": "美術", "藝術": "美術", "視覺藝術": "美術",
    "戲劇": "表演", "戲劇表演": "表演", "綜藝": "表演", "綜藝活動": "表演",
    "音樂表演": "音樂", "獨立音樂": "音樂", "演唱會": "音樂",
    "講座資訊": "其他", "親子活動": "親子", "電影欣賞": "電影",
    "競賽活動": "競賽", "徵選活動": "其他", "徵選": "其他", "商展": "其他",
    "研習課程": "其他", "其他藝文資訊": "其他",
}

REGION_ALIASES = {"臺北市": "台北市", "臺中市": "台中市", "臺南市": "台南市", "臺東縣": "台東縣"}
REGIONS = [
    "台北市", "新北市", "基隆市", "桃園市", "新竹市", "新竹縣", "苗栗縣", "台中市",
    "彰化縣", "南投縣", "雲林縣", "嘉義市", "嘉義縣", "台南市", "高雄市", "屏東縣",
    "宜蘭縣", "花蓮縣", "台東縣", "澎湖縣", "金門縣", "連江縣",
]

# Region center/radius checks are used to reject obviously wrong official coordinates
# (for example a Miaoli event accidentally pointing to Taipei).
REGION_CENTERS: dict[str, tuple[float, float, float]] = {
    "台北市": (25.05, 121.54, 42), "新北市": (25.02, 121.47, 62), "基隆市": (25.13, 121.74, 28),
    "桃園市": (24.99, 121.30, 58), "新竹市": (24.81, 120.97, 26), "新竹縣": (24.84, 121.15, 58),
    "苗栗縣": (24.56, 120.82, 62), "台中市": (24.16, 120.68, 70), "彰化縣": (24.08, 120.54, 52),
    "南投縣": (23.91, 120.69, 86), "雲林縣": (23.71, 120.43, 58), "嘉義市": (23.48, 120.45, 24),
    "嘉義縣": (23.46, 120.57, 74), "台南市": (23.00, 120.22, 73), "高雄市": (22.63, 120.31, 94),
    "屏東縣": (22.55, 120.55, 102), "宜蘭縣": (24.68, 121.77, 76), "花蓮縣": (23.99, 121.61, 120),
    "台東縣": (22.76, 121.15, 126), "澎湖縣": (23.57, 119.58, 55), "金門縣": (24.44, 118.32, 36),
    "連江縣": (26.16, 119.95, 48),
}

KEYWORD_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("快閃", re.compile(r"快閃|期間限定|popup|pop-up", re.I)),
    ("攝影", re.compile(r"攝影|影像展|photo(?:graphy)?", re.I)),
    ("動漫", re.compile(r"動漫|動畫|漫畫|卡通|anime|公仔|角色展|模型展", re.I)),
    ("歷史文化", re.compile(r"歷史|文化資產|文物|考古|古蹟|史料|地方誌|民俗", re.I)),
    ("自然科學", re.compile(r"自然史|科學|生態|植物|動物|天文|地質|海洋|環境教育", re.I)),
    ("科技", re.compile(r"科技|人工智慧|\bAI\b|數位科技|半導體|資訊展|電腦展|機器人", re.I)),
    ("設計", re.compile(r"設計|建築|工藝|時尚|家居|文具|design", re.I)),
    ("舞蹈", re.compile(r"舞蹈|舞作|芭蕾", re.I)),
    ("音樂", re.compile(r"音樂|演唱會|樂團|管弦|獨立音樂|concert", re.I)),
    ("表演", re.compile(r"戲劇|劇場|表演|歌劇|馬戲|音樂劇|偶戲", re.I)),
    ("電影", re.compile(r"電影|(?<!攝)影展|放映", re.I)),
    ("市集", re.compile(r"市集|祭典|嘉年華|展售|商品展|食品展|旅展|文創攤位", re.I)),
    ("親子", re.compile(r"親子|兒童|家庭|幼兒", re.I)),
    ("競賽", re.compile(r"競賽|比賽|大賽|徵件比賽", re.I)),
    ("美術", re.compile(r"美術|藝術|繪畫|雕塑|裝置|當代|典藏|書畫|陶藝|視覺藝術|藝術博覽會|插畫博覽會", re.I)),
]

IMAGE_META_PATTERNS = [
    re.compile(r'<meta[^>]+(?:property|name)=["\']og:image(?::secure_url)?["\'][^>]+content=["\']([^"\']+)', re.I),
    re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']og:image(?::secure_url)?["\']', re.I),
    re.compile(r'<meta[^>]+(?:property|name)=["\']twitter:image(?::src)?["\'][^>]+content=["\']([^"\']+)', re.I),
    re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']twitter:image(?::src)?["\']', re.I),
    re.compile(r'<link[^>]+rel=["\']image_src["\'][^>]+href=["\']([^"\']+)', re.I),
]
IMG_SRC_PATTERN = re.compile(r'<img[^>]+(?:src|data-src|data-original|data-lazy-src|data-original-src|data-flickity-lazyload|data-echo)=["\']([^"\']+)', re.I)
IMG_SRCSET_PATTERN = re.compile(r'<(?:img|source)[^>]+(?:srcset|data-srcset)=["\']([^"\']+)', re.I)
JSON_IMAGE_PATTERN = re.compile(r'["\'](?:image|imageUrl|imageURL|images|thumbnailUrl|contentUrl|bannerUrl|bannerURL|coverImage|coverUrl|mainImage|posterUrl|originalImage)["\']\s*:\s*["\']([^"\']+)', re.I)
BACKGROUND_IMAGE_PATTERN = re.compile(r'background(?:-image)?\s*:\s*url\(["\']?([^"\')]+)', re.I)
BAD_IMAGE_HINTS = re.compile(
    r"(?:favicon|logo|icon|avatar|spacer|blank|loading|loader|spinner|progress|preload|placeholder|pixel|sprite|qr[_-]?code)",
    re.I,
)
LD_JSON_PATTERN = re.compile(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.I | re.S)
HTML_ADDRESS_PATTERN = re.compile(r'(?:\d{3,6}\s*)?(?:臺|台|新北|桃園|新竹|苗栗|彰化|南投|雲林|嘉義|高雄|屏東|宜蘭|花蓮|臺東|台東|澎湖|金門|連江)[^<\n]{0,55}?(?:路|街|大道|巷|弄)[^<\n]{0,28}?號(?:之\d+)?(?:\d+樓)?')
COORDINATE_PATTERNS = [
    re.compile(r'@(-?\d{2}\.\d+),(-?\d{2,3}\.\d+)'),
    re.compile(r'(?:query|q|destination)=(-?\d{2}\.\d+)%?2[Cc](-?\d{2,3}\.\d+)'),
    re.compile(r'["\']latitude["\']\s*:\s*["\']?(-?\d{2}\.\d+).*?["\']longitude["\']\s*:\s*["\']?(-?\d{2,3}\.\d+)', re.I | re.S),
]
VENUE_LABEL_PATTERN = re.compile(r'(?:活動地點|展演地點|展覽地點|場地|地點)\s*[：:]\s*([^<\n]{2,80})', re.I)
ABSOLUTE_IMAGE_PATTERN = re.compile(r'https?://[^\s"\'<>]+?\.(?:jpe?g|png|webp|avif)(?:\?[^\s"\'<>]*)?', re.I)
ABSOLUTE_URL_PATTERN = re.compile(r'https?://[^\s<>"\'）)\]}]+', re.I)
RELATED_LINK_PATTERN = re.compile(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.I | re.S)
CANONICAL_LINK_PATTERN = re.compile(r'<link[^>]+rel=["\'](?:canonical|alternate)["\'][^>]+href=["\']([^"\']+)', re.I)
PAGE_TITLE_PATTERN = re.compile(r'<title[^>]*>(.*?)</title>', re.I | re.S)
OG_TITLE_PATTERN = re.compile(r'<meta[^>]+(?:property|name)=["\'](?:og:title|twitter:title)["\'][^>]+content=["\']([^"\']+)', re.I)
FACEBOOK_HOST_PATTERN = re.compile(
    r'(?:^|\.)(?:facebook\.com|fb\.me|fbcdn\.net|facebookusercontent\.com)$',
    re.I,
)
FACEBOOK_REFERENCE_PATTERN = re.compile(r'(?:facebook|臉書|粉絲專頁)', re.I)
SOCIAL_HOST_PATTERN = re.compile(r'(?:^|\.)instagram\.com$', re.I)
TICKETING_HOST_PATTERN = re.compile(
    r'(?:^|\.)(?:opentix\.life|kktix\.com|tixcraft\.com|accupass\.com|udnfunlife\.com|ticketplus\.com\.tw|'
    r'ibon\.com\.tw|famiticket\.com\.tw|ticketscloud\.org|artsticket\.com\.tw)$',
    re.I,
)
OFFICIAL_DATA_HOST_PATTERN = re.compile(r'(?:^|\.)(?:culture\.tw|gov\.tw)$', re.I)
EXCLUDED_CONTENT_PATTERN = re.compile(
    r'講座|講習|研習|研討會|論壇|座談|分享會|演講|課程|工作坊|營隊|訓練班|培訓班|讀書會',
    re.I,
)
EXCLUDED_CATEGORY_PATTERN = re.compile(r'講座|講習|研習|課程|工作坊|營隊', re.I)
LOCAL_COMMUNITY_PATTERN = re.compile(
    r'社區發展協會|里辦公處|里民活動|地方社團|地方性社團|同好會|居民活動|社區小聚|社團例會',
    re.I,
)
SMALL_LOCAL_ACTIVITY_PATTERN = re.compile(
    r'外展服務|繪本說故事|客語說故事|(?:親子|圖書館|故事媽媽).{0,8}說故事|說故事(?:活動|時間|場次)|故事時間|故事媽媽|親子共讀|社區共讀|'
    r'假日電影院|(?:圖書館|分館|鄉|鎮|區|里).{0,12}電影欣賞|'
    r'文化走讀|深度走讀|城市走讀|導覽活動|借閱活動|閱讀推廣活動|'
    r'DIY|手作(?:活動|體驗|課)|(?:體驗|觀察|藝術|繪畫|書法|舞蹈|音樂|攝影)課|'
    r'(?:夏令|冬令|成長|親子|藝術|科學)營|交流會|同樂會',
    re.I,
)
LOCAL_ORGANIZATION_PATTERN = re.compile(r'(?:縣|市|鄉|鎮|區|里).{0,14}(?:協會|學會|社團|團委會)', re.I)
LOCAL_GOVERNMENT_PATTERN = re.compile(r'(?:市|區|鄉|鎮)公所', re.I)
LOCAL_SMALL_SHOW_PATTERN = re.compile(r'(?:社區|社團|學員|班級|志工|里民).{0,10}(?:成果展|聯展|展演|成果活動)', re.I)
COMPETITION_ACTIVITY_PATTERN = re.compile(r'競賽|比賽|大賽|初賽|複賽|決賽|徵件|徵選', re.I)
COMPETITION_SHOW_EXCEPTION_PATTERN = re.compile(r'得獎作品展|首獎典藏作品展|成果展|展覽|特展|音樂會|演唱會|公演|藝術節', re.I)
PUBLIC_SHOW_PATTERN = re.compile(r'展覽|特展|常設展|作品展|成果展|聯展|個展|書展|攝影展|美術展|展演|音樂會|演唱會|演出|藝術節|電影節|博覽會|劇場|戲劇|舞蹈', re.I)
LARGE_OR_OFFICIAL_EVENT_PATTERN = re.compile(r'國際|全國|博覽會|美術館|博物館|文化局|文化中心|文化處', re.I)
DESCRIPTION_META_PATTERNS = [
    re.compile(r'<meta[^>]+(?:property|name)=["\'](?:og:description|twitter:description|description)["\'][^>]+content=["\']([^"\']+)', re.I),
    re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\'](?:og:description|twitter:description|description)["\']', re.I),
]
JSON_DESCRIPTION_PATTERN = re.compile(r'["\'](?:description|eventDescription|introduction|summary)["\']\s*:\s*["\']((?:\\.|[^"\'])+)', re.I)
IMAGE_VALIDATION_CACHE: dict[str, bool] = {}


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


def clean_place_text(value: Any) -> str:
    text = clean_text(value)
    text = re.sub(r"^[=＝:：;；|｜]+|[=＝:：;；|｜]+$", "", text).strip()
    text = re.sub(r"\s{2,}", " ", text)
    return text


def load_venue_profiles(path: Path = DEFAULT_VENUE_ALIASES) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    items = payload.get("venues", []) if isinstance(payload, dict) else payload
    return [item for item in items if isinstance(item, dict) and clean_text(item.get("name"))]


VENUE_PROFILES = load_venue_profiles()


def normalize_venue_name(raw_venue: Any, address: Any = "") -> tuple[str, str]:
    original = clean_place_text(first_value(raw_venue, address, "地點待確認"))
    for profile in VENUE_PROFILES:
        canonical = clean_place_text(profile.get("name"))
        patterns = sorted((clean_place_text(item) for item in profile.get("patterns", []) if clean_place_text(item)), key=len, reverse=True)
        matched = next((pattern for pattern in patterns if pattern.lower() in original.lower()), "")
        if matched:
            detail = clean_place_text(original.replace(matched, "", 1))
            detail = re.sub(r"^[\s、,，/\-—－]+", "", detail)
            return canonical, detail

    district_only = bool(
        re.fullmatch(r"(?:臺|台|新北|桃園|新竹|苗栗|彰化|南投|雲林|嘉義|高雄|屏東|宜蘭|花蓮|臺東|台東|澎湖|金門|連江).{0,3}[市縣].{1,4}區(?:[（(].+[）)])?", original)
        or re.fullmatch(r".{1,6}區(?:[（(](?:臺|台).+[市縣][）)])?", original)
    )
    address_like = bool(re.search(r"(?:路|街|大道|巷|弄|號|樓)", original)) and not bool(re.search(r"館|園區|中心|藝廊|劇院|展場|空間|博物館|美術館|文化館|文創", original))
    if district_only or address_like:
        region = detect_region(address, original)
        return f"{region}｜場館資料整理中", ""
    return original or "地點待確認", ""


def poor_venue(value: Any) -> bool:
    text = clean_place_text(value)
    if not text or text == "地點待確認" or "場館資料整理中" in text:
        return True
    if re.search(r"[=＝]$", text):
        return True
    if re.fullmatch(r".{1,8}區(?:[（(].+[）)])?", text):
        return True
    return False


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
    # Some Culture Cloud records accidentally concatenate the host twice:
    # https://cloud.culture.twhttps://cloud.culture.tw/path/to/poster.jpg
    duplicated_scheme = re.match(r"^https?://[^/?#]+(?P<url>https?://.+)$", text, re.I)
    if duplicated_scheme:
        text = duplicated_scheme.group("url")
    # Malformed CMS fields sometimes contain a quoted metadata fragment and a
    # second, real image URL. Prefer that final absolute URL.
    nested_schemes = [match.start() for match in re.finditer(r"https?://", text, re.I)]
    if len(nested_schemes) > 1 and re.search(r"(?:\\?&q;|\\?&quot;|[\"'<>])", text[:nested_schemes[-1]], re.I):
        text = text[nested_schemes[-1]:]
        text = re.split(r"(?:\\?&q;|\\?&quot;|[\"'<>\s])", text, maxsplit=1, flags=re.I)[0]
    if re.match(r"^https?%3A", text, re.I):
        text = unquote(text)
    if text.startswith("//"):
        text = "https:" + text
    # A few upstream fields append prose directly after the hostname, for
    # example "https://lib.miaoli.gov.tw網站查詢，或洽...". Keep only the
    # valid ASCII authority so one malformed record cannot abort the full run.
    authority_match = re.match(r"^(https?://)([^/?#\s]+)(.*)$", text, re.I)
    if authority_match:
        authority = authority_match.group(2)
        if re.search(r"[^A-Za-z0-9.\-:\[\]]", authority):
            safe_authority = re.match(r"[A-Za-z0-9.-]+(?::\d+)?", authority)
            if not safe_authority:
                return ""
            text = f"{authority_match.group(1)}{safe_authority.group(0)}"
    try:
        text = urljoin(base_url, text)
        parsed = urlparse(text)
    except ValueError:
        return ""
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    host = parsed.netloc.lower().split(":")[0]
    # OPENTIX program routes currently resolve to a generic shell, while the
    # matching event route exposes full copy, JSON-LD and key art.
    if re.fullmatch(r"(?:www\.)?opentix\.life", host) and re.fullmatch(r"/program/\d+/?", parsed.path):
        event_path = re.sub(r"^/program/", "/event/", parsed.path)
        parsed = parsed._replace(path=event_path)
        text = parsed.geturl()
    return text


def unique_urls(values: Iterable[Any], *, base_url: str = CULTURE_BASE_URL) -> list[str]:
    result: list[str] = []
    for raw in values:
        url = normalize_url(raw, base_url=base_url)
        if url and not is_facebook_url(url) and url not in result:
            result.append(url)
    return result


def valid_http_url(value: Any) -> str:
    return normalize_url(value)


def url_host(value: Any) -> str:
    return urlparse(valid_http_url(value)).netloc.lower().split(":")[0]


def is_facebook_url(value: Any) -> bool:
    """Reject every Facebook-owned page and image host, not only groups."""
    url = valid_http_url(value)
    if not url:
        return False
    parsed = urlparse(url)
    host = parsed.netloc.lower().split(":")[0]
    path = unquote(parsed.path).lower()
    return bool(
        FACEBOOK_HOST_PATTERN.search(host)
        or re.search(r"(?:^|[/_.-])facebook(?:[/_.-]|$)", path)
    )


def is_facebook_group_url(value: Any) -> bool:
    url = valid_http_url(value)
    if not url:
        return False
    parsed = urlparse(url)
    return is_facebook_url(url) and "/groups/" in parsed.path.lower()


def is_ticketing_url(value: Any) -> bool:
    return bool(TICKETING_HOST_PATTERN.search(url_host(value)))


def is_generic_ticketing_url(value: Any) -> bool:
    url = valid_http_url(value)
    if not url or not is_ticketing_url(url):
        return False
    parsed = urlparse(url)
    return parsed.path.rstrip("/") == "" and not parsed.query and not parsed.fragment


def source_url_requires_title_validation(value: Any) -> bool:
    host = url_host(value)
    return bool(TICKETING_HOST_PATTERN.search(host) or SOCIAL_HOST_PATTERN.search(host))


def _compact_title(value: Any) -> str:
    text = clean_text(value).lower()
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"(?:opentix|kktix|tixcraft|accupass|udn售票|寬宏售票|年代售票|facebook)", "", text, flags=re.I)
    return re.sub(r"[^0-9a-z\u3400-\u9fff]+", "", text)


def title_match_score(event_title: Any, page_title: Any, page_text: Any = "") -> float:
    """Return a conservative 0..1 score that the page belongs to the event."""
    expected = _compact_title(event_title)
    candidate = _compact_title(page_title)
    if not expected:
        return 0.0
    scores: list[float] = []
    if candidate:
        scores.append(SequenceMatcher(None, expected, candidate).ratio())
        if expected in candidate:
            scores.append(0.98)
        elif len(candidate) >= 6 and candidate in expected:
            scores.append(0.88)
        expected_pairs = {expected[index:index + 2] for index in range(max(0, len(expected) - 1))}
        candidate_pairs = {candidate[index:index + 2] for index in range(max(0, len(candidate) - 1))}
        if expected_pairs:
            scores.append(len(expected_pairs & candidate_pairs) / len(expected_pairs))

    plain_page = _compact_title(str(page_text)[:240_000])
    if plain_page:
        if expected in plain_page:
            scores.append(0.92)
        meaningful = [
            _compact_title(token)
            for token in re.split(r"[\s：:、,，/|()（）【】《》\-—]+", clean_text(event_title))
            if len(_compact_title(token)) >= 2 and _compact_title(token) not in {"展覽", "活動", "特展", "台灣", "臺灣"}
        ]
        if meaningful:
            coverage = sum(token in plain_page for token in meaningful) / len(meaningful)
            scores.append(coverage * 0.82)
    return round(max(scores, default=0.0), 4)


def is_excluded_record(record: dict[str, Any]) -> bool:
    """Apply V4.3's exhibition-first editorial policy before publication."""
    source = first_value(record.get("sourceUrl"), record.get("url"), record.get("website"))
    if is_facebook_url(source):
        return True
    title = clean_text(first_value(record.get("title"), record.get("name"), record.get("actName")))
    categories = " ".join(clean_text(value) for value in flatten_values(first_value(record.get("categories"), record.get("category"), record.get("categoryName"))))
    feed_category = clean_text(record.get("_feedCategory"))
    if EXCLUDED_CONTENT_PATTERN.search(title) or SMALL_LOCAL_ACTIVITY_PATTERN.search(title) or EXCLUDED_CATEGORY_PATTERN.search(categories) or feed_category in {"7", "19"}:
        return True
    organizer = clean_text(first_value(record.get("unit"), record.get("organizer"), record.get("showUnit"), record.get("masterUnit"), record.get("org")))
    community_text = f"{title} {organizer}"
    if LOCAL_GOVERNMENT_PATTERN.search(community_text):
        return True
    if LOCAL_SMALL_SHOW_PATTERN.search(community_text):
        return True
    if COMPETITION_ACTIVITY_PATTERN.search(title) and not COMPETITION_SHOW_EXCEPTION_PATTERN.search(title):
        return True
    if LOCAL_COMMUNITY_PATTERN.search(community_text) and not LARGE_OR_OFFICIAL_EVENT_PATTERN.search(community_text):
        return True
    if LOCAL_ORGANIZATION_PATTERN.search(community_text) and not PUBLIC_SHOW_PATTERN.search(title) and not LARGE_OR_OFFICIAL_EVENT_PATTERN.search(community_text):
        return True
    return False


def editorialize_categories(record: dict[str, Any]) -> dict[str, Any]:
    """Keep award exhibitions/shows while removing the misleading competition label."""
    cleaned = dict(record)
    categories = [
        category
        for category in flatten_values(first_value(record.get("categories"), record.get("category")))
        if clean_text(category) in ALLOWED_CATEGORIES and clean_text(category) != "競賽"
    ]
    categories = [clean_text(category) for category in categories]
    if not categories:
        categories = [
            category
            for category in normalize_categories(
                "",
                clean_text(record.get("title")),
                clean_text(record.get("description")),
            )
            if category != "競賽"
        ]
    cleaned["categories"] = list(dict.fromkeys(categories))[:3] or ["其他"]
    cleaned["category"] = cleaned["categories"][0]
    return cleaned


def strip_facebook_references(value: Any) -> str:
    """Remove imported lines that direct visitors to Facebook."""
    text = clean_text(value)
    if not text:
        return ""
    kept = [line.strip() for line in text.splitlines() if not FACEBOOK_REFERENCE_PATTERN.search(line)]
    return "\n".join(line for line in kept if line).strip()


def sanitize_facebook_record(record: dict[str, Any]) -> dict[str, Any]:
    """Strip social, loading, logo, icon, and placeholder media before publishing."""
    cleaned = dict(record)
    images = [
        url
        for url in unique_urls([*(record.get("images") or []), record.get("image")])
        if probable_content_image(url)
    ]
    cleaned["images"] = images[:10]
    cleaned["image"] = images[0] if images else ""
    for key in ("description", "price", "unit", "transitInfo", "parkingInfo", "comment", "source"):
        cleaned[key] = strip_facebook_references(record.get(key))
    if is_facebook_url(record.get("sourceUrlRejected")):
        cleaned["sourceUrlRejected"] = ""
    sessions: list[dict[str, Any]] = []
    for session in record.get("sessions") or []:
        if not isinstance(session, dict):
            continue
        item = dict(session)
        item["price"] = strip_facebook_references(item.get("price"))
        sessions.append(item)
    cleaned["sessions"] = sessions
    return cleaned


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


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    value = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(value), math.sqrt(max(0.0, 1 - value)))


def coordinate_matches_region(region: str, lat: Any, lon: Any) -> bool:
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return False
    if not (20 <= lat <= 27 and 117.5 <= lon <= 124):
        return False
    profile = REGION_CENTERS.get(region)
    if not profile:
        return True
    return haversine_km(profile[0], profile[1], float(lat), float(lon)) <= profile[2]


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
    saw_other = False
    for value in [*split_category_values(raw_category), *split_category_values(feed_category)]:
        mapped = CATEGORY_CODE_MAP.get(value) or CATEGORY_ALIASES.get(value) or (value if value in ALLOWED_CATEGORIES else "")
        if mapped == "其他":
            saw_other = True
        elif mapped and mapped not in categories:
            categories.append(mapped)

    combined = f"{title} {description}"
    for category, pattern in KEYWORD_RULES:
        if pattern.search(combined) and category not in categories:
            categories.insert(0, category)

    cleaned = [category for category in categories if category in ALLOWED_CATEGORIES and category != "其他"]
    if not cleaned:
        cleaned = ["其他"] if saw_other or combined.strip() else ["其他"]
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
        if url and not is_generic_ticketing_url(url) and not is_facebook_url(url):
            return url
    # Official feeds often leave the source field empty but place the exhibition
    # page in the description. Recover only stable, non-image, non-Facebook URLs.
    source_text = " ".join(
        clean_text(first_value(raw.get(key)))
        for key in ("description", "descriptionFilterHtml", "comment", "transitInfo")
    )
    for match in ABSOLUTE_URL_PATTERN.finditer(source_text):
        url = normalize_url(match.group(0).rstrip("。，、；;:"))
        if (
            url
            and not is_facebook_url(url)
            and not is_generic_ticketing_url(url)
            and not re.search(r"\.(?:jpe?g|png|gif|webp|avif)(?:$|\?)", url, re.I)
        ):
            return url
    return ""


def collect_image_urls(raw: dict[str, Any], show: dict[str, Any] | None = None, *, page_base: str = CULTURE_BASE_URL) -> list[str]:
    urls = unique_urls(image_field_values(raw, show), base_url=page_base)
    urls.extend(url for url in image_from_html(first_value(raw.get("descriptionFilterHtml"), raw.get("description")), base_url=page_base) if url not in urls)
    return [url for url in urls if probable_content_image(url)][:8]


def probable_content_image(url: str) -> bool:
    parsed = urlparse(url)
    path = unquote(parsed.path).lower()
    if BAD_IMAGE_HINTS.search(path):
        return False
    filename = path.rsplit("/", 1)[-1]
    if re.search(r"(?:^|[-_])default(?:[-_.]|$)|programinfodefault", filename):
        return False
    if path.endswith((".svg", ".gif", ".ico")):
        return False
    # Tiny CMS thumbnails and tracking endpoints are rarely exhibition key art.
    if re.search(r"(?:^|[/_-])(16x16|32x32|50x50|64x64|80x80|100x100)(?:[/_.-]|$)", path):
        return False
    return True


def extract_opentix_description(page: str) -> str:
    """Extract OPENTIX's visible programme copy when metadata is abbreviated."""
    start_heading = r"節目介紹|活動介紹|展演介紹|作品介紹"
    end_heading = r"折扣方案|異動公告|展演須知|購取票須知|退換須知|注意事項"
    # Prefer the actual content heading, not the same words in a sticky tab bar.
    heading = re.search(
        rf"<h[1-6][^>]*>(?:\s|<[^>]+>)*(?:{start_heading})(?:\s|<[^>]+>)*</h[1-6]>",
        page,
        re.I | re.S,
    )
    search_from = heading.end() if heading else 0
    match = re.search(
        rf"(?P<body>.*?)(?=(?:<h[1-6][^>]*>(?:\s|<[^>]+>)*(?:{end_heading}))|$)",
        page[search_from:],
        re.I | re.S,
    )
    if not heading:
        match = re.search(
            rf"(?:{start_heading})(?P<body>.*?)(?=(?:{end_heading})|$)",
            page,
            re.I | re.S,
        )
    if not match:
        return ""
    description = clean_text(match.group("body"))
    description = re.sub(r"^(?:[：:\s]|&nbsp;)+", "", description)
    if len(description) < 40:
        return ""
    return description[:5000]


def image_url_responds(url: str, *, timeout: int = 12) -> bool:
    if is_facebook_url(url):
        return False
    if url in IMAGE_VALIDATION_CACHE:
        return IMAGE_VALIDATION_CACHE[url]
    result = False
    try:
        response = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            stream=True,
            headers={"User-Agent": USER_AGENT, "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.7", "Range": "bytes=0-65535"},
        )
        content_type = response.headers.get("content-type", "").lower()
        length = int(response.headers.get("content-length") or 0)
        chunk = next(response.iter_content(4096), b"")
        result = response.status_code in {200, 206} and bool(chunk) and (content_type.startswith("image/") or re.search(r"\.(?:jpe?g|png|webp|avif)(?:$|\?)", response.url, re.I)) and (not length or length >= 2500)
        response.close()
    except (requests.RequestException, ValueError, StopIteration):
        result = False
    IMAGE_VALIDATION_CACHE[url] = result
    return result


def related_page_urls(page: str, base_url: str) -> list[str]:
    """Find likely official, ticketing, Instagram, and event/detail pages.

    Search-engine image hotlinks are intentionally not used: they expire often,
    can point to unrelated copies, and are unsuitable for a daily automated feed.
    Facebook pages, groups, short links, and image hosts are never imported.
    """
    candidates: dict[str, int] = {}

    def add(candidate: Any, score: int) -> None:
        url = normalize_url(candidate, base_url=base_url)
        if not url or url == base_url or is_facebook_url(url):
            return
        parsed = urlparse(url)
        host = parsed.netloc.lower().split(":")[0]
        path = parsed.path.lower()
        if not host or any(token in path for token in ("/share", "/sharer", "/login", "/dialog/")):
            return
        if SOCIAL_HOST_PATTERN.search(host):
            score += 15
            if "/events/" in path:
                score += 45
        if TICKETING_HOST_PATTERN.search(host):
            score += 75
        if "opentix.life" in host:
            score += 35
        if OFFICIAL_DATA_HOST_PATTERN.search(host):
            score += 30
        candidates[url] = max(candidates.get(url, -999), score)

    for match in CANONICAL_LINK_PATTERN.finditer(page):
        add(match.group(1), 65)

    keywords = re.compile(r"官方|活動官網|詳細資訊|活動頁|售票|購票|主辦|instagram|event|detail|ticket", re.I)
    for match in RELATED_LINK_PATTERN.finditer(page):
        label = clean_text(match.group(2))
        href = match.group(1)
        normalized = normalize_url(href, base_url=base_url)
        host = urlparse(normalized).netloc.lower() if normalized else ""
        social = bool(SOCIAL_HOST_PATTERN.search(host))
        if keywords.search(label + " " + href) or social:
            add(href, 80 if keywords.search(label) else 45)

    return [url for url, _ in sorted(candidates.items(), key=lambda item: item[1], reverse=True)[:8]]


def _walk_jsonld(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_jsonld(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_jsonld(child)


def discover_page_metadata(url: str, *, title: str = "", timeout: int = 16) -> dict[str, Any]:
    if not url or is_facebook_url(url):
        return {}
    try:
        response = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
        )
        response.raise_for_status()
        if is_facebook_url(response.url):
            return {}
        content_type = response.headers.get("content-type", "").lower()
        if "html" not in content_type and not response.text.lstrip().startswith("<"):
            return {}
        page = response.text[:1_600_000]
        title_match = OG_TITLE_PATTERN.search(page) or PAGE_TITLE_PATTERN.search(page)
        page_title = clean_text(title_match.group(1)) if title_match else ""
        images: list[str] = []
        descriptions: list[str] = []
        venue = ""
        address = ""
        latitude: float | None = None
        longitude: float | None = None

        # Prefer social metadata and structured data over arbitrary inline images.
        for pattern in IMAGE_META_PATTERNS:
            images.extend(match.group(1) for match in pattern.finditer(page))
        for pattern in DESCRIPTION_META_PATTERNS:
            descriptions.extend(clean_text(match.group(1)) for match in pattern.finditer(page))

        for match in LD_JSON_PATTERN.finditer(page):
            raw = html.unescape(match.group(1)).strip()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                continue
            for node in _walk_jsonld(payload):
                node_type = clean_text(node.get("@type")).lower()
                if "image" in node:
                    images.extend(flatten_values(node.get("image")))
                if node_type == "event" and node.get("description"):
                    descriptions.append(clean_text(node.get("description")))
                if node_type in {"event", "place", "civicstructure", "performingartstheater", "museum"}:
                    location = node.get("location")
                    if isinstance(location, dict):
                        venue = venue or clean_place_text(first_value(location.get("name"), location.get("alternateName")))
                        address_value = location.get("address")
                        if isinstance(address_value, dict):
                            address = address or clean_place_text("".join(clean_text(address_value.get(key)) for key in ("postalCode", "addressRegion", "addressLocality", "streetAddress")))
                        else:
                            address = address or clean_place_text(address_value)
                        geo = location.get("geo") if isinstance(location.get("geo"), dict) else {}
                        lat, lon = coordinate_pair(geo, location)
                        latitude = latitude if latitude is not None else lat
                        longitude = longitude if longitude is not None else lon
                    if node_type in {"place", "civicstructure", "performingartstheater", "museum"}:
                        venue = venue or clean_place_text(first_value(node.get("name"), node.get("alternateName")))
                        address_value = node.get("address")
                        if isinstance(address_value, dict):
                            address = address or clean_place_text("".join(clean_text(address_value.get(key)) for key in ("postalCode", "addressRegion", "addressLocality", "streetAddress")))
                        else:
                            address = address or clean_place_text(address_value)
                        lat, lon = coordinate_pair(node.get("geo") if isinstance(node.get("geo"), dict) else {}, node)
                        latitude = latitude if latitude is not None else lat
                        longitude = longitude if longitude is not None else lon

        images.extend(match.group(1) for match in IMG_SRC_PATTERN.finditer(page))
        for match in IMG_SRCSET_PATTERN.finditer(page):
            for candidate in match.group(1).split(","):
                images.append(candidate.strip().split(" ")[0])
        images.extend(match.group(1) for match in JSON_IMAGE_PATTERN.finditer(page))
        images.extend(match.group(1) for match in BACKGROUND_IMAGE_PATTERN.finditer(page))
        images.extend(match.group(0) for match in ABSOLUTE_IMAGE_PATTERN.finditer(page))
        for match in JSON_DESCRIPTION_PATTERN.finditer(page):
            raw_description = match.group(1)
            try:
                raw_description = json.loads(f'"{raw_description}"')
            except json.JSONDecodeError:
                raw_description = raw_description.replace(r"\n", "\n").replace(r'\"', '"')
            descriptions.append(clean_text(raw_description))

        plain = clean_text(page)
        if not address:
            match = HTML_ADDRESS_PATTERN.search(plain)
            if match:
                address = clean_place_text(match.group(0))
        if not venue:
            match = VENUE_LABEL_PATTERN.search(plain)
            if match:
                venue = clean_place_text(match.group(1))
        if latitude is None or longitude is None:
            for pattern in COORDINATE_PATTERNS:
                match = pattern.search(page)
                if not match:
                    continue
                lat = number_or_none(match.group(1), latitude=True)
                lon = number_or_none(match.group(2), latitude=False)
                if lat is not None and lon is not None:
                    latitude, longitude = lat, lon
                    break

        normalized_images = [item for item in unique_urls(images, base_url=response.url) if probable_content_image(item)]
        title_tokens = [token.lower() for token in re.split(r"[\s：:、,，/|()（）【】]+", title) if len(token) >= 2]
        page_haystack = f"{page_title} {clean_text(page[:180000])}".lower()
        host = urlparse(response.url).netloc.lower()
        if "opentix.life" in host:
            opentix_description = extract_opentix_description(page)
            if opentix_description:
                descriptions.append(opentix_description)
        match_score = title_match_score(title, page_title, page_haystack) if title else 1.0
        title_matched = not title or match_score >= 0.42
        # Ticket and social platforms frequently redirect to a generic listing,
        # login, or unrelated event. Never reuse media or copy from such pages.
        if title and not title_matched:
            normalized_images = []
            descriptions = []

        def image_score(item: str, index: int) -> tuple[int, int]:
            decoded = unquote(item).lower()
            score = 0
            if any(token in decoded for token in title_tokens):
                score += 80
            if re.search(r"poster|banner|cover|event|activity|exhibition|主視覺|海報", decoded, re.I):
                score += 30
            if "cloudfront.net" in decoded:
                score += 12
            if re.search(r"thumb|thumbnail|small|avatar|profile", decoded, re.I):
                score -= 25
            return (-score, index)

        normalized_images = [item for _, item in sorted(enumerate(normalized_images), key=lambda pair: image_score(pair[1], pair[0]))]
        validated = [item for item in normalized_images[:24] if image_url_responds(item)]
        normalized_images = list(dict.fromkeys([*validated, *normalized_images]))[:18]
        normalized_descriptions = list(dict.fromkeys(item for item in descriptions if len(item) >= 24))
        description = max(normalized_descriptions, key=len, default="")[:5000]
        return {
            "images": normalized_images,
            "description": description,
            "pageTitle": page_title,
            "titleMatchScore": match_score,
            "titleMatched": title_matched,
            "venue": venue,
            "address": address,
            "latitude": latitude,
            "longitude": longitude,
            "checkedUrl": response.url,
            "relatedUrls": related_page_urls(page, response.url),
        }
    except requests.RequestException:
        return {}


def discover_page_images(url: str, *, timeout: int = 16) -> list[str]:
    return list(discover_page_metadata(url, timeout=timeout).get("images") or [])


def discover_event_metadata(url: str, title: str, *, timeout: int = 18) -> dict[str, Any]:
    """Read and cross-check the source plus likely official/ticket detail pages."""
    primary = discover_page_metadata(url, title=title, timeout=timeout)
    if not primary:
        return {}
    pages = [primary]
    for related in (primary.get("relatedUrls") or [])[:4]:
        child = discover_page_metadata(related, title=title, timeout=timeout)
        if child:
            pages.append(child)

    accepted = [page for page in pages if page.get("titleMatched")]
    if not accepted:
        return {
            "images": [],
            "sourceUrlVerified": False,
            "sourceUrlMatchScore": primary.get("titleMatchScore", 0),
            "sourceUrlRejected": valid_http_url(url),
        }

    def source_rank(page: dict[str, Any]) -> tuple[float, int]:
        checked_url = clean_text(page.get("checkedUrl"))
        host = url_host(checked_url)
        bonus = 0
        if "opentix.life" in host:
            bonus += 55
        elif TICKETING_HOST_PATTERN.search(host):
            bonus += 38
        if OFFICIAL_DATA_HOST_PATTERN.search(host):
            bonus += 30
        if checked_url.rstrip("/") == valid_http_url(url).rstrip("/"):
            bonus += 12
        return bonus, float(page.get("titleMatchScore") or 0)

    accepted.sort(key=source_rank, reverse=True)
    combined = dict(accepted[0])
    combined["images"] = []
    for page in accepted:
        combined["images"] = merge_list_values(combined.get("images"), page.get("images"))[:20]
    descriptions = [clean_text(page.get("description")) for page in accepted if clean_text(page.get("description"))]
    combined["description"] = max(descriptions, key=len, default="")
    for key in ("venue", "address", "latitude", "longitude"):
        combined[key] = next((page.get(key) for page in accepted if page.get(key) not in (None, "")), None)
    combined["bestSourceUrl"] = clean_text(accepted[0].get("checkedUrl"))
    combined["sourceUrlVerified"] = bool(primary.get("titleMatched"))
    combined["sourceUrlMatchScore"] = float(primary.get("titleMatchScore") or 0)
    if not primary.get("titleMatched"):
        combined["sourceUrlRejected"] = valid_http_url(url)
    return combined


def stable_id(*values: Any) -> str:
    seed = "|".join(clean_text(value) for value in values if clean_text(value))
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:18]


def normalize_record(raw: dict[str, Any], index: int) -> dict[str, Any] | None:
    show = best_show(raw)
    title = clean_text(first_value(raw.get("title"), raw.get("titile"), raw.get("name"), raw.get("actName")))
    if not title:
        return None
    if is_excluded_record(raw):
        return None

    raw_description = first_value(raw.get("description"), raw.get("descriptionFilterHtml"), raw.get("comment"))
    description = clean_text(raw_description)
    event_source_url = source_url(raw)
    address = clean_place_text(first_value(raw.get("address"), raw.get("location"), show.get("location"), show.get("address")))
    raw_venue = clean_place_text(first_value(raw.get("venueGroup"), raw.get("locationName"), raw.get("venue"), show.get("locationName"), show.get("venue"), address, "地點待確認"))
    venue_group, inferred_detail = normalize_venue_name(raw_venue, address)
    venue_detail = clean_place_text(first_value(raw.get("venueDetail"), inferred_detail))
    start_date = date_string(first_value(raw.get("startDate"), raw.get("start"), raw.get("startTime"), show.get("time"), show.get("startTime")))
    end_date = date_string(first_value(raw.get("endDate"), raw.get("end"), raw.get("endTime"), show.get("endTime"), start_date))
    uid = clean_text(first_value(raw.get("id"), raw.get("UID"), raw.get("uid"), raw.get("actId"))) or stable_id(title, start_date, venue_group, event_source_url, index)
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
        "locationName": venue_group,
        "location": venue_group,
        "venueGroup": venue_group,
        "venueDetail": venue_detail,
        "address": address,
        "region": detect_region(raw.get("region"), raw.get("cityName"), address, venue_group, raw_venue),
        "latitude": latitude,
        "longitude": longitude,
        "coordinateSource": clean_text(raw.get("coordinateSource")) or ("official_feed" if latitude is not None and longitude is not None else ""),
        "price": price,
        "unit": clean_text(first_value(raw.get("unit"), raw.get("organizer"), raw.get("showUnit"), raw.get("masterUnit"), raw.get("org"))),
        "transitInfo": clean_text(first_value(raw.get("transitInfo"), raw.get("transit"), raw.get("travellinginfo"))),
        "parkingInfo": clean_text(first_value(raw.get("parkingInfo"), raw.get("parkinginfo"))),
        "phone": clean_text(first_value(raw.get("phone"), raw.get("tel"))),
        "comment": clean_text(raw.get("comment")),
        "sessions": sessions,
        "hitRate": int(raw.get("hitRate") or 0) if str(raw.get("hitRate") or "0").isdigit() else 0,
        "source": clean_text(first_value(raw.get("source"), raw.get("sourceWebName"))) or "文化部開放資料",
        "firstSeenAt": clean_text(first_value(raw.get("firstSeenAt"), raw.get("first_seen_at"))),
        "lastSeenAt": clean_text(first_value(raw.get("lastSeenAt"), raw.get("last_seen_at"))),
        "pageMetadataCheckedAt": clean_text(raw.get("pageMetadataCheckedAt")),
        "sourceUrlVerified": bool(raw.get("sourceUrlVerified")),
        "sourceUrlMatchScore": float(raw.get("sourceUrlMatchScore") or 0) if re.fullmatch(r"\d+(?:\.\d+)?", str(raw.get("sourceUrlMatchScore") or "0")) else 0.0,
        "sourceUrlRejected": clean_text(raw.get("sourceUrlRejected")),
    }


def is_demo_record(record: dict[str, Any]) -> bool:
    event_url = clean_text(record.get("sourceUrl")).lower()
    description = clean_text(record.get("description"))
    uid = clean_text(record.get("id"))
    if "example.com" in event_url or "用於版面檢視" in description:
        return True
    return bool(re.fullmatch(r"e\d+", uid, re.I) and clean_text(record.get("title")))


def is_recruitment_only(record: dict[str, Any]) -> bool:
    text = f"{clean_text(record.get('title'))} {clean_text(record.get('description'))}"
    recruitment = bool(re.search(r"徵選|徵件|徵稿|招募|報名簡章|申請辦法", text))
    public_outcome = bool(re.search(r"成果展|入選展|得獎作品展|展覽|展出|發表會|頒獎典禮", text))
    return recruitment and not public_outcome


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


def semantic_dedupe_key(record: dict[str, Any]) -> str:
    """Merge the same exhibition imported with different provider IDs."""
    title = _compact_title(record.get("title"))
    start = date_string(record.get("startDate"))
    end = date_string(record.get("endDate"))
    if not title or not start:
        return ""
    return f"{title}|{start}|{end or start}"


def source_record_quality(record: dict[str, Any]) -> tuple[int, float, int]:
    url = valid_http_url(record.get("sourceUrl"))
    if not url or is_facebook_url(url) or is_generic_ticketing_url(url):
        return (-999, 0.0, 0)
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    score = 10
    if path:
        score += 14 + min(path.count("/"), 5)
    if record.get("sourceUrlVerified"):
        score += 75
    if OFFICIAL_DATA_HOST_PATTERN.search(parsed.netloc):
        score += 24
    if is_ticketing_url(url):
        score += 18
    if any(host in parsed.netloc.lower() for host in ("artemperor.tw", "artgalleryapollo.com")):
        score += 22
    return score, float(record.get("sourceUrlMatchScore") or 0), len(path)


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
        if key in {"locationName", "location", "venueGroup"} and poor_venue(value) and not poor_venue(old_value):
            continue
        merged[key] = value
    preferred_source = max((old, new), key=source_record_quality)
    if valid_http_url(preferred_source.get("sourceUrl")):
        for key in ("sourceUrl", "sourceUrlVerified", "sourceUrlMatchScore", "sourceUrlRejected", "pageMetadataCheckedAt"):
            if key in preferred_source:
                merged[key] = preferred_source.get(key)
    merged["images"] = [
        url
        for value in merge_list_values(old.get("images"), new.get("images"))
        if (url := valid_http_url(value)) and not is_facebook_url(url) and probable_content_image(url)
    ][:10]
    if merged["images"]:
        merged["image"] = merged["images"][0]
    merged["categories"] = [item for item in merge_list_values(new.get("categories"), old.get("categories")) if item in ALLOWED_CATEGORIES][:3] or ["其他"]
    merged["category"] = merged["categories"][0]
    merged["sessions"] = merge_list_values(old.get("sessions"), new.get("sessions"))
    return merged


def merge_records(primary: Iterable[dict[str, Any]], existing: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    now = datetime.now(TAIPEI_TZ).isoformat(timespec="seconds")
    for record in existing:
        if not is_demo_record(record) and not is_recruitment_only(record) and not is_excluded_record(record) and is_still_relevant(record):
            record = dict(record)
            record["firstSeenAt"] = clean_text(record.get("firstSeenAt")) or now
            record["lastSeenAt"] = clean_text(record.get("lastSeenAt")) or record["firstSeenAt"]
            merged[dedupe_key(record)] = record
    for record in primary:
        if is_recruitment_only(record) or is_excluded_record(record) or not is_still_relevant(record):
            continue
        key = dedupe_key(record)
        if key in merged:
            first_seen = clean_text(merged[key].get("firstSeenAt")) or now
            combined = merge_two_records(merged[key], record)
            combined["firstSeenAt"] = first_seen
            combined["lastSeenAt"] = now
            merged[key] = combined
        else:
            record = dict(record)
            record["firstSeenAt"] = clean_text(record.get("firstSeenAt")) or now
            record["lastSeenAt"] = now
            merged[key] = record

    def sort_key(item: dict[str, Any]) -> tuple[date, str]:
        return parse_date(item.get("startDate")) or date.max, clean_text(item.get("title"))

    # Provider IDs are not globally stable. A second title/date pass merges
    # duplicates such as one Culture Cloud record plus one gallery record.
    semantic: dict[str, dict[str, Any]] = {}
    unkeyed: list[dict[str, Any]] = []
    for record in merged.values():
        key = semantic_dedupe_key(record)
        if not key:
            unkeyed.append(record)
            continue
        if key in semantic:
            first_seen = min(
                (clean_text(value) for value in (semantic[key].get("firstSeenAt"), record.get("firstSeenAt")) if clean_text(value)),
                default=now,
            )
            semantic[key] = merge_two_records(semantic[key], record)
            semantic[key]["firstSeenAt"] = first_seen
            semantic[key]["lastSeenAt"] = now
        else:
            semantic[key] = record

    return sorted([*semantic.values(), *unkeyed], key=sort_key)


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
            event["coordinateSource"] = "matched_place"
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


def apply_curated_overrides(events: list[dict[str, Any]], path: Path = DEFAULT_CURATED_OVERRIDES) -> int:
    payload = load_json_object(path)
    overrides = payload.get("overrides") if isinstance(payload, dict) else []
    if not isinstance(overrides, list):
        return 0
    applied = 0
    for override in overrides:
        if not isinstance(override, dict):
            continue
        expected_title = _compact_title(override.get("title"))
        expected_start = date_string(override.get("startDate"))
        expected_end = date_string(override.get("endDate"))
        values = override.get("set")
        if not expected_title or not isinstance(values, dict):
            continue
        for event in events:
            if _compact_title(event.get("title")) != expected_title:
                continue
            if expected_start and date_string(event.get("startDate")) != expected_start:
                continue
            if expected_end and date_string(event.get("endDate")) != expected_end:
                continue
            clean_values = dict(values)
            if "sourceUrl" in clean_values:
                clean_values["sourceUrl"] = valid_http_url(clean_values["sourceUrl"])
                if not clean_values["sourceUrl"] or is_facebook_url(clean_values["sourceUrl"]):
                    clean_values.pop("sourceUrl", None)
            if isinstance(clean_values.get("images"), list):
                clean_values["images"] = unique_urls(clean_values["images"])[:18]
                clean_values["image"] = clean_values["images"][0] if clean_values["images"] else event.get("image", "")
            event.update({key: value for key, value in clean_values.items() if value not in (None, "")})
            applied += 1
    return applied


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
                if coordinate_matches_region(clean_text(event.get("region")), pair[0], pair[1]):
                    event["latitude"], event["longitude"] = pair
                    event["coordinateSource"] = "geocode_cache"
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
                if lat is not None and lon is not None and coordinate_matches_region(clean_text(event.get("region")), lat, lon):
                    cache[key] = [lat, lon]
                    event["latitude"], event["longitude"] = lat, lon
                    event["coordinateSource"] = "nominatim"
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
            or not clean_place_text(event.get("address"))
            or poor_venue(event.get("venueGroup") or event.get("locationName"))
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

def enrich_source_pages(events: list[dict[str, Any]], *, max_fetches: int = 450, workers: int = 10) -> int:
    now = datetime.now(TAIPEI_TZ)
    candidates: list[dict[str, Any]] = []
    for event in events:
        canonical_source = valid_http_url(event.get("sourceUrl"))
        if not canonical_source:
            continue
        event["sourceUrl"] = canonical_source
        checked = parse_date(event.get("pageMetadataCheckedAt"))
        missing_image = not event.get("images")
        opentix_missing_copy = "opentix.life" in url_host(canonical_source) and len(clean_text(event.get("description"))) < 120
        source_needs_verification = not bool(event.get("sourceUrlVerified")) or source_url_requires_title_validation(event.get("sourceUrl"))
        retry_days = 4 if missing_image or source_needs_verification else 21
        recently_checked = not opentix_missing_copy and checked is not None and checked >= (now.date() - timedelta(days=retry_days))
        needs_data = (
            missing_image
            or event.get("latitude") is None
            or event.get("longitude") is None
            or not clean_place_text(event.get("address"))
            or poor_venue(event.get("venueGroup") or event.get("locationName"))
            or len(clean_text(event.get("description"))) < 120
            or source_needs_verification
        )
        if needs_data and not recently_checked:
            candidates.append(event)
    candidates.sort(
        key=lambda event: (
            "opentix.life" in url_host(event.get("sourceUrl")) and len(clean_text(event.get("description"))) < 120,
            source_url_requires_title_validation(event.get("sourceUrl")),
            not bool(event.get("sourceUrlVerified")),
            not bool(event.get("images")),
            len(clean_text(event.get("description"))) < 120,
            poor_venue(event.get("venueGroup") or event.get("locationName")),
            int(event.get("hitRate") or 0),
        ),
        reverse=True,
    )
    candidates = candidates[:max_fetches]
    if not candidates:
        return 0

    enriched = 0
    checked_at = now.isoformat(timespec="seconds")
    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = {executor.submit(discover_event_metadata, event["sourceUrl"], clean_text(event.get("title"))): event for event in candidates}
        for future in as_completed(futures):
            event = futures[future]
            event["pageMetadataCheckedAt"] = checked_at
            try:
                metadata = future.result()
            except Exception:
                metadata = {}
            if not metadata:
                continue
            changed = False
            event["sourceUrlVerified"] = bool(metadata.get("sourceUrlVerified"))
            event["sourceUrlMatchScore"] = float(metadata.get("sourceUrlMatchScore") or 0)
            rejected_url = clean_text(metadata.get("sourceUrlRejected"))
            best_source_url = valid_http_url(metadata.get("bestSourceUrl"))
            if rejected_url:
                event["sourceUrlRejected"] = rejected_url
                if best_source_url:
                    event["sourceUrl"] = best_source_url
                    event["sourceUrlVerified"] = True
                else:
                    event["sourceUrl"] = ""
                changed = True
            elif best_source_url and best_source_url != valid_http_url(event.get("sourceUrl")):
                event["sourceUrl"] = best_source_url
                changed = True
            images = metadata.get("images") or []
            if images:
                event["images"] = merge_list_values(event.get("images"), images)[:18]
                event["image"] = event["images"][0]
                changed = True
            discovered_description = clean_text(metadata.get("description"))
            if len(discovered_description) > len(clean_text(event.get("description"))):
                event["description"] = discovered_description
                changed = True
            if metadata.get("address") and not clean_place_text(event.get("address")):
                event["address"] = clean_place_text(metadata["address"])
                changed = True
            if metadata.get("venue") and poor_venue(event.get("venueGroup") or event.get("locationName")):
                group, detail = normalize_venue_name(metadata["venue"], metadata.get("address") or event.get("address"))
                event["venueGroup"] = group
                event["venueDetail"] = detail
                event["locationName"] = group
                event["location"] = group
                event["region"] = detect_region(event.get("address"), group)
                changed = True
            if event.get("latitude") is None and metadata.get("latitude") is not None:
                if coordinate_matches_region(clean_text(event.get("region")), metadata["latitude"], metadata.get("longitude")):
                    event["latitude"] = metadata["latitude"]
                    event["coordinateSource"] = "source_page"
                    changed = True
            if event.get("longitude") is None and metadata.get("longitude") is not None:
                if coordinate_matches_region(clean_text(event.get("region")), metadata.get("latitude"), metadata["longitude"]):
                    event["longitude"] = metadata["longitude"]
                    event["coordinateSource"] = "source_page"
                    changed = True
            if changed:
                enriched += 1
    return enriched


def validate_all_coordinates(events: list[dict[str, Any]]) -> int:
    """Clear coordinates that are outside Taiwan or implausible for their stated county/city."""
    cleared = 0
    for event in events:
        lat, lon = event.get("latitude"), event.get("longitude")
        if lat is None or lon is None:
            continue
        if coordinate_matches_region(clean_text(event.get("region")), lat, lon):
            continue
        event["coordinateRejected"] = {"latitude": lat, "longitude": lon, "reason": "region_mismatch"}
        event["latitude"] = None
        event["longitude"] = None
        event["coordinateSource"] = ""
        cleared += 1
    return cleared


def venue_images(
    events: Iterable[dict[str, Any]],
    *,
    existing: dict[str, str] | None = None,
    allow_fetch: bool = True,
) -> dict[str, str]:
    # Prefer official venue imagery. When a venue has no usable official image,
    # use a current exhibition's key art as the explicitly labelled fallback.
    event_list = list(events)
    active_venues = {clean_place_text(event.get("venueGroup") or event.get("locationName")) for event in event_list}
    result: dict[str, str] = {
        clean_place_text(name): valid_http_url(url)
        for name, url in (existing or {}).items()
        if clean_place_text(name) in active_venues
        and valid_http_url(url)
        and not is_facebook_url(url)
        and probable_content_image(valid_http_url(url))
    }
    if allow_fetch:
        for profile in VENUE_PROFILES:
            name = clean_place_text(profile.get("name"))
            homepage = valid_http_url(profile.get("homepage"))
            if not name or name not in active_venues or not homepage or name in result:
                continue
            images = [item for item in discover_page_images(homepage, timeout=18) if image_url_responds(item)]
            if images:
                result[name] = images[0]

    def exhibition_image_rank(event: dict[str, Any]) -> tuple[int, date, int]:
        today = datetime.now(TAIPEI_TZ).date()
        start = parse_date(event.get("startDate")) or date.max
        end = parse_date(event.get("endDate")) or start
        active = int(start <= today <= end)
        upcoming = int(start > today)
        return active * 2 + upcoming, start, int(event.get("hitRate") or 0)

    for event in sorted(event_list, key=exhibition_image_rank, reverse=True):
        venue = clean_place_text(event.get("venueGroup") or event.get("locationName"))
        if not venue or venue in result or poor_venue(venue):
            continue
        image = next(
            (
                valid_http_url(candidate)
                for candidate in [*(event.get("images") or []), event.get("image")]
                if valid_http_url(candidate)
                and not is_facebook_url(candidate)
                and probable_content_image(valid_http_url(candidate))
            ),
            "",
        )
        if image:
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


def fetch_records_with_fallback(existing: list[dict[str, Any]], config: SourceConfig) -> tuple[list[dict[str, Any]], bool]:
    """Keep the last good catalogue when every Culture Ministry feed times out."""
    try:
        return fetch_all_json(config), False
    except RuntimeError:
        if not existing:
            raise
        print(
            "[warning] Culture Ministry feeds are temporarily unavailable; "
            "continuing with the last published catalogue and official-page enrichment.",
            file=sys.stderr,
        )
        return [], True


def read_input_file(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("events") or payload.get("data") or payload.get("result") or []
    if not isinstance(payload, list):
        raise ValueError("Input JSON must be an array or an object containing events/data/result")
    return [item for item in payload if isinstance(item, dict)]


def read_venue_image_map(path: Path | None) -> dict[str, str]:
    if not path or not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    venue_map = payload.get("venueImages", {}) if isinstance(payload, dict) else {}
    return {
        clean_place_text(name): valid_http_url(url)
        for name, url in venue_map.items()
        if clean_place_text(name)
        and valid_http_url(url)
        and not is_facebook_url(url)
        and probable_content_image(valid_http_url(url))
    } if isinstance(venue_map, dict) else {}


def write_output(
    path: Path,
    events: list[dict[str, Any]],
    *,
    venue_image_map: dict[str, str] | None = None,
    refresh_venue_images: bool = True,
) -> None:
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
        "venueImages": venue_images(events, existing=venue_image_map, allow_fetch=refresh_venue_images),
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
    parser.add_argument("--no-venue-image-enrichment", action="store_true")
    parser.add_argument("--no-geocoding", action="store_true")
    parser.add_argument("--max-detail-fetches", type=int, default=int(os.environ.get("MAX_DETAIL_FETCHES", "250")))
    parser.add_argument("--max-image-fetches", type=int, default=int(os.environ.get("MAX_IMAGE_FETCHES", "450")))
    parser.add_argument("--max-geocodes", type=int, default=int(os.environ.get("MAX_GEOCODES", "25")))
    parser.add_argument("--geocode-cache", type=Path, default=DEFAULT_GEOCODE_CACHE)
    parser.add_argument("--curated-overrides", type=Path, default=DEFAULT_CURATED_OVERRIDES)
    args = parser.parse_args()

    existing = [] if args.no_preserve_existing else load_existing(args.output)
    raw_records = read_input_file(args.input_file) if args.input_file else fetch_records_with_fallback(existing, SourceConfig())[0]
    venue_image_map = read_venue_image_map(args.input_file or (args.output if args.output.exists() else None))
    normalized = [record for index, raw in enumerate(raw_records) if (record := normalize_record(raw, index))]
    events = merge_records(normalized, existing)
    curated_overrides = apply_curated_overrides(events, args.curated_overrides)

    detail_enriched = 0
    if not args.input_file and args.max_detail_fetches > 0:
        detail_enriched = enrich_from_official_details(events, max_fetches=args.max_detail_fetches)

    enriched_images = 0
    if not args.no_image_enrichment and not args.input_file and args.max_image_fetches > 0:
        enriched_images = enrich_source_pages(events, max_fetches=args.max_image_fetches)
    # Curated corrections win if an upstream page later changes or redirects.
    apply_curated_overrides(events, args.curated_overrides)

    rejected_coordinates = validate_all_coordinates(events)
    inherited_coordinates = fill_coordinates_from_matching_places(events)
    geocoded = 0
    if not args.no_geocoding and not args.input_file and args.max_geocodes > 0:
        geocoded = geocode_missing_coordinates(events, cache_path=args.geocode_cache, max_fetches=args.max_geocodes)
    # Validate the inherited/geocoded results one more time before publishing.
    rejected_coordinates += validate_all_coordinates(events)

    events = [
        editorialize_categories(sanitize_facebook_record(event))
        for event in events
        if not is_excluded_record(event)
    ]
    write_output(
        args.output,
        events,
        venue_image_map=venue_image_map,
        refresh_venue_images=not args.no_venue_image_enrichment and not bool(args.input_file),
    )
    image_count = sum(1 for event in events if valid_http_url(event.get("image")))
    coordinate_count = sum(1 for event in events if event.get("latitude") is not None and event.get("longitude") is not None)
    print(
        f"Wrote {len(events)} events to {args.output}; official-details enriched={detail_enriched}; images={image_count} "
        f"(source-page metadata enriched {enriched_images}); coordinates={coordinate_count} "
        f"(matched {inherited_coordinates}, geocoded {geocoded}, rejected mismatches {rejected_coordinates}); "
        f"curated overrides={curated_overrides}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
