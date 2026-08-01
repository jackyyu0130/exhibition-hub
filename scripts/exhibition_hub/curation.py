"""Public-feed curation policy for Taiwan Exhibition Journal.

The production enrichment file intentionally keeps broad source coverage for
review and auditing. The public site consumes a smaller curated feed focused on
major venues and high-interest events with a usable image and outbound link.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
import re
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse

from exhibition_hub.classifiers.content_types import classify_event
from exhibition_hub.image_quality import clean_image_urls


FACEBOOK_HOST_RE = re.compile(r"(^|\.)(facebook\.com|fb\.com|fb\.me)$", re.I)
SHORTENER_HOST_RE = re.compile(r"(^|\.)(reurl\.cc)$", re.I)
LIBRARY_RE = re.compile(r"圖書館|分館|圖書室|閱覽室|書庫|library", re.I)
DISTRICT_ONLY_RE = re.compile(
    r"^(?:(?:臺|台).{1,8}[市縣]|.{1,8}(?:區|鄉|鎮|市)[（(](?:臺|台).+[市縣][）)])$"
)
GENERIC_SPACE_RE = re.compile(
    r"^(?:第?\s*[一二三四五六七八九十0-9]+(?:\s*[、,，~～\-]\s*[一二三四五六七八九十0-9]+)*|"
    r"第?\s*[一二三四五六七八九十0-9]+(?:樓|展覽廳|展覽室|展廳)|"
    r"(?:一|二|三|四|五|六|七|八|九|十|[0-9]+)樓|"
    r"展覽廳|展覽室|展廳|多功能室|會議室|大廳|中庭)$"
)
SMALL_LOCAL_RE = re.compile(
    r"社區|里民|里辦公處|活動中心|地方社團|同好會|讀書會|故事時間|故事媽媽|"
    r"繪本說故事|親子共讀|假日電影院|外展服務|工作坊|研習|課程|講座|座談|"
    r"導覽活動|文化走讀|城市走讀|手作體驗|DIY|成果展|學生作品展|校內展|"
    r"高中|國中|國小|大學.{0,8}(?:系|所|社)|社團|成果發表|成果音樂會|畢業製作|"
    r"畢業展|校慶|班展|師生聯展|學生成果|社區大學|會員展|會員聯展|"
    r"書畫學會|攝影學會|美術學會|藝術學會|鄉公所|鎮公所|區公所|地方文化館",
    re.I,
)
PERMANENT_RE = re.compile(r"常設展|常設館|常態展|永久展", re.I)
MAJOR_TITLE_RE = re.compile(
    r"國際|全國|世界|巡迴|演唱會|音樂祭|音樂節|博覽會|藝術節|設計節|"
    r"影展|電影節|雙年展|三年展|特展|大展|聯展|個展|展演|劇場|歌劇|"
    r"舞台劇|音樂會|world\s+tour|asia\s+tour|concert",
    re.I,
)

SINGER_CONCERT_RE = re.compile(
    r"演唱會|巡迴演唱|fan\s*concert|live\s+in\s+(?:taipei|kaohsiung|taichung)|"
    r"live\s+tour|world\s+tour|asia\s+tour|tour\s*20\d{2}|concert\s*(?:20\d{2})?",
    re.I,
)
FILM_RE = re.compile(r"電影|影展|放映|映後|紀錄片|短片節|動畫影展", re.I)
PERFORMANCE_RE = re.compile(r"音樂劇|歌劇|舞台劇|劇場|戲劇|讀劇|偶戲|馬戲|歌舞劇|脫口秀|相聲", re.I)
DANCE_RE = re.compile(r"舞蹈|舞作|芭蕾|現代舞|街舞|國標舞", re.I)
MUSIC_RE = re.compile(r"音樂會|交響|管弦|協奏|獨奏|重奏|室內樂|古典音樂|爵士|國樂|樂團|音樂祭|音樂節|專場|不插電|live\s*house", re.I)
CLASSICAL_MUSIC_RE = re.compile(r"音樂會|交響|管弦|協奏|獨奏|重奏|室內樂|古典音樂|鋼琴|小提琴|大提琴|國樂|演奏會", re.I)
ANIME_RE = re.compile(r"動漫|動畫展|漫畫(?:原作|展)?|原畫展|電玩|遊戲展|電競|ACG|cosplay|公仔|角色展|角色限定|模型展|玩具展|扭蛋|盒玩|卡牌|聲優|VTuber|虛擬偶像|特攝|輕小說|IP(?:展|祭|授權)|寶可夢|吉伊卡哇|chiikawa|櫻桃小丸子|蠟筆小新|哆啦A夢|三麗鷗|迪士尼|皮克斯|史努比|姆明|航海王|ONE\s*PIECE|鬼滅之刃|咒術迴戰|進擊的巨人|排球少年|名偵探柯南|七龍珠|鋼彈|GUNDAM|新世紀福音戰士|初音未來|hololive|anime", re.I)
PHOTO_RE = re.compile(r"攝影|影像展|photography|photo\s+exhibition", re.I)
NATURE_RE = re.compile(r"自然史|自然|生態|植物|動物|天文|地質|海洋|環境教育|科學館", re.I)
HISTORY_RE = re.compile(r"歷史|文化資產|文物|考古|古蹟|史料|民俗|紀念", re.I)
TECH_RE = re.compile(r"科技|人工智慧|AI|數位科技|半導體|資訊展|電腦展|機器人", re.I)
DESIGN_RE = re.compile(r"設計|建築|工藝|時尚|家居|文具|design", re.I)
ART_RE = re.compile(r"美術|藝術|繪畫|雕塑|裝置|當代|典藏|書畫|陶藝|版畫|水墨", re.I)
POPUP_RE = re.compile(r"快閃|期間限定|pop-?up", re.I)
MARKET_RE = re.compile(r"市集|蚤之市|展售會", re.I)
CHILD_RE = re.compile(r"親子|兒童|家庭|幼兒", re.I)
COMPETITION_RE = re.compile(r"競賽|比賽|大賽|徵件比賽", re.I)

TAIPEI_TZ = timezone(timedelta(hours=8))
MUTUALLY_EXCLUSIVE = {"演唱會", "音樂", "表演", "舞蹈", "電影"}



PUBLIC_EVENT_FIELDS = (
    "id", "title", "description", "sourceUrl", "sourceUrlVerified", "sourceUrlRejected",
    "image", "images", "categories", "category", "contentType", "contentTypes",
    "eventFormat", "editorialStatus", "editorialFlags", "startDate", "endDate",
    "locationName", "location", "venueGroup", "venueDetail", "venueNames", "venueName",
    "venueIds", "venueId", "venueCoverageStatus", "unmatchedVenueValues", "address",
    "region", "regionCanonical", "latitude", "longitude", "coordinateSource", "price",
    "unit", "transitInfo", "hitRate", "source", "firstSeenAt", "lastSeenAt",
    "publicVenueId", "publicVenuePriority", "publicVenueType", "publicCurationReason",
)


def slim_public_event(event: Mapping[str, Any]) -> dict[str, Any]:
    """Return only fields used by the public frontend.

    Candidate/audit files keep the full source record. The public payload avoids
    repeated session, collector, parking, phone and merge diagnostics that are
    not rendered by the site and previously added several megabytes to startup.
    """
    return {
        field: deepcopy(event.get(field))
        for field in PUBLIC_EVENT_FIELDS
        if field in event and event.get(field) not in (None, "", [], {})
    }

def _clean(value: Any) -> str:
    return str(value or "").strip()


def _normalize_key(value: Any) -> str:
    text = _clean(value).replace("臺", "台").lower()
    return re.sub(r"[\s　()（）\-_/／・·,，.。:：;；|｜]+", "", text)


def _event_text(event: Mapping[str, Any]) -> str:
    fields = ("title", "locationName", "location", "venueGroup", "unit")
    return " ".join(_clean(event.get(field)) for field in fields)


def _event_place_values(event: Mapping[str, Any]) -> list[str]:
    values: list[str] = []
    for field in ("venueName", "locationName", "location", "venueGroup"):
        value = _clean(event.get(field))
        if value:
            values.append(value)
    for field in ("venueNames", "unmatchedVenueValues"):
        raw = event.get(field)
        if isinstance(raw, list):
            values.extend(_clean(item) for item in raw if _clean(item))
    return values


def valid_outbound_url(value: Any) -> bool:
    text = _clean(value)
    if not text:
        return False
    try:
        parsed = urlparse(text)
    except ValueError:
        return False
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    host = parsed.hostname or ""
    if FACEBOOK_HOST_RE.search(host) or SHORTENER_HOST_RE.search(host):
        return False
    return True


def event_has_outbound_link(event: Mapping[str, Any]) -> bool:
    return valid_outbound_url(event.get("sourceUrl")) and not bool(event.get("sourceUrlRejected"))


def _image_values(event: Mapping[str, Any]) -> Iterable[str]:
    raw_images = event.get("images")
    if isinstance(raw_images, list):
        for value in raw_images:
            if isinstance(value, str):
                yield value
    image = event.get("image")
    if isinstance(image, str):
        yield image


def usable_event_images(event: Mapping[str, Any]) -> list[str]:
    images, _ = clean_image_urls(_image_values(event))
    return [
        image for image in images
        if not re.search(r"/img/app/dl_(?:ios|google)[^/]*\.(?:png|jpe?g|webp)", image, re.I)
    ]


def event_has_image(event: Mapping[str, Any]) -> bool:
    return bool(usable_event_images(event))


def is_generic_place(value: Any) -> bool:
    text = _clean(value)
    if not text:
        return True
    if GENERIC_SPACE_RE.fullmatch(text):
        return True
    if DISTRICT_ONLY_RE.fullmatch(text):
        return True
    if "場館資料整理中" in text or "地點待確認" in text:
        return True
    return False


def build_venue_indexes(matrix_payload: Mapping[str, Any]) -> tuple[dict[str, Mapping[str, Any]], dict[str, Mapping[str, Any]]]:
    by_id: dict[str, Mapping[str, Any]] = {}
    by_name: dict[str, Mapping[str, Any]] = {}
    for venue in matrix_payload.get("venues") or []:
        if not isinstance(venue, Mapping) or not venue.get("confirmed"):
            continue
        venue_id = _clean(venue.get("id"))
        if venue_id:
            by_id[venue_id] = venue
        names = [venue.get("name"), *(venue.get("aliases") or [])]
        if venue.get("venueComplexName"):
            names.append(venue.get("venueComplexName"))
        for name in names:
            key = _normalize_key(name)
            if key and key not in by_name:
                by_name[key] = venue
    return by_id, by_name


def match_venue(
    event: Mapping[str, Any],
    by_id: Mapping[str, Mapping[str, Any]],
    by_name: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, Any] | None:
    for venue_id in event.get("venueIds") or []:
        if _clean(venue_id) in by_id:
            return by_id[_clean(venue_id)]
    best: tuple[int, Mapping[str, Any]] | None = None
    event_keys = [_normalize_key(value) for value in _event_place_values(event) if not is_generic_place(value)]
    for event_key in event_keys:
        if not event_key:
            continue
        exact = by_name.get(event_key)
        if exact:
            return exact
        for venue_key, venue in by_name.items():
            if len(venue_key) < 4:
                continue
            if venue_key in event_key or (len(event_key) >= 5 and event_key in venue_key):
                score = min(len(venue_key), len(event_key))
                if best is None or score > best[0]:
                    best = (score, venue)
    return best[1] if best else None


def is_singer_concert_title(title: str) -> bool:
    if FILM_RE.search(title) or PERFORMANCE_RE.search(title) or DANCE_RE.search(title):
        return False
    if CLASSICAL_MUSIC_RE.search(title) and not re.search(r"演唱會", title, re.I):
        return False
    return bool(SINGER_CONCERT_RE.search(title))


def public_categories(event: Mapping[str, Any]) -> list[str]:
    title = _clean(event.get("title"))
    description = _clean(event.get("description"))
    content_types = set(event.get("contentTypes") or [])
    existing = [
        _clean(value)
        for value in [event.get("category"), *(event.get("categories") or [])]
        if _clean(value)
    ]

    # Strong format categories inspect the title first. This prevents a stray
    # source category or a word in a long description from turning a museum
    # exhibition into anime, film, or a concert.
    if "film_screening" in content_types or FILM_RE.search(title):
        primary = "電影"
    elif DANCE_RE.search(title):
        primary = "舞蹈"
    elif PERFORMANCE_RE.search(title):
        primary = "表演"
    elif is_singer_concert_title(title):
        primary = "演唱會"
    elif "music_festival" in content_types or MUSIC_RE.search(title):
        primary = "音樂"
    elif ANIME_RE.search(title):
        primary = "動漫"
    elif POPUP_RE.search(title):
        primary = "快閃店"
    elif MARKET_RE.search(title):
        primary = "市集"
    elif PHOTO_RE.search(title):
        primary = "攝影"
    elif NATURE_RE.search(f"{title} {description}"):
        primary = "自然"
    elif HISTORY_RE.search(f"{title} {description}"):
        primary = "歷史"
    elif TECH_RE.search(f"{title} {description}"):
        primary = "科技"
    elif DESIGN_RE.search(f"{title} {description}"):
        primary = "設計"
    elif ART_RE.search(f"{title} {description}"):
        primary = "美術"
    elif CHILD_RE.search(title):
        primary = "親子"
    elif COMPETITION_RE.search(title):
        primary = "競賽"
    else:
        primary = next((value for value in existing if value not in {"講座", "研習"}), "其他")

    secondary: list[str] = []
    text = f"{title} {description}"
    optional_rules = (
        ("攝影", PHOTO_RE), ("自然", NATURE_RE), ("歷史", HISTORY_RE),
        ("科技", TECH_RE), ("設計", DESIGN_RE), ("美術", ART_RE),
        ("親子", CHILD_RE), ("競賽", COMPETITION_RE),
    )
    for label, pattern in optional_rules:
        if label != primary and pattern.search(text) and label not in secondary:
            secondary.append(label)
    for label in existing:
        if label == primary or label in secondary or label in {"講座", "研習"}:
            continue
        if primary in MUTUALLY_EXCLUSIVE and label in MUTUALLY_EXCLUSIVE:
            continue
        # Never inherit anime from a noisy source field unless the title itself
        # contains an anime/IP signal.
        if label == "動漫" and not ANIME_RE.search(title):
            continue
        secondary.append(label)
    return [primary, *secondary][:3]


def _event_is_current_or_future(event: Mapping[str, Any], today: date | None = None) -> bool:
    today = today or datetime.now(TAIPEI_TZ).date()
    try:
        end = date.fromisoformat(_clean(event.get("endDate"))[:10])
    except ValueError:
        return False
    return end >= today


def evaluate_event(
    event: Mapping[str, Any],
    by_id: Mapping[str, Mapping[str, Any]],
    by_name: Mapping[str, Mapping[str, Any]],
    *,
    today: date | None = None,
) -> tuple[bool, str, Mapping[str, Any] | None]:
    title = _clean(event.get("title"))
    text = _event_text(event)
    if not _event_is_current_or_future(event, today=today):
        return False, "expired", None
    if not event_has_outbound_link(event):
        return False, "missing_outbound_link", None
    if not event_has_image(event):
        return False, "missing_image", None
    if LIBRARY_RE.search(text):
        return False, "library_series", None
    if SMALL_LOCAL_RE.search(text):
        return False, "small_local_activity", None

    venue = match_venue(event, by_id, by_name)
    if not venue and all(is_generic_place(value) for value in _event_place_values(event)):
        return False, "generic_or_district_only_place", None

    hit_rate = int(event.get("hitRate") or 0)
    if PERMANENT_RE.search(title):
        if not venue or venue.get("priority") != "P0" or hit_rate < 120:
            return False, "low_interest_permanent_exhibition", venue

    if venue:
        priority = _clean(venue.get("priority"))
        if priority == "P0":
            return True, "confirmed_P0", venue
        if priority == "P1" and (hit_rate >= 5 or MAJOR_TITLE_RE.search(title)):
            return True, "confirmed_P1_visible_interest", venue
        if priority == "P2" and hit_rate >= 80:
            return True, "confirmed_P2_high_interest", venue
        return False, "low_priority_or_low_interest_venue", venue

    if hit_rate >= 300 and MAJOR_TITLE_RE.search(title):
        return True, "unmatched_high_interest", None
    return False, "unmatched_or_low_interest", None


def build_curated_payload(
    source_payload: Mapping[str, Any],
    matrix_payload: Mapping[str, Any],
    *,
    today: date | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    by_id, by_name = build_venue_indexes(matrix_payload)
    kept: list[dict[str, Any]] = []
    removed_counts: dict[str, int] = {}
    kept_counts: dict[str, int] = {}
    removed_samples: dict[str, list[dict[str, Any]]] = {}

    for raw_event in source_payload.get("events") or []:
        if not isinstance(raw_event, Mapping):
            continue
        event = classify_event(raw_event)
        categories = public_categories(event)
        event["categories"] = categories
        event["category"] = categories[0]
        keep, reason, venue = evaluate_event(event, by_id, by_name, today=today)
        target = kept_counts if keep else removed_counts
        target[reason] = target.get(reason, 0) + 1
        if not keep:
            samples = removed_samples.setdefault(reason, [])
            if len(samples) < 12:
                samples.append({
                    "id": event.get("id"),
                    "title": event.get("title"),
                    "locationName": event.get("locationName"),
                    "sourceUrl": event.get("sourceUrl"),
                })
            continue
        clean_images = usable_event_images(event)
        event["images"] = clean_images[:10]
        event["image"] = clean_images[0]
        if venue:
            canonical_venue_id = _clean(venue.get("id"))
            event["publicVenueId"] = canonical_venue_id
            if canonical_venue_id:
                event["venueId"] = canonical_venue_id
                existing_venue_ids = event.get("venueIds")
                if not isinstance(existing_venue_ids, list):
                    existing_venue_ids = []
                event["venueIds"] = list(dict.fromkeys([
                    canonical_venue_id,
                    *[
                        _clean(value)
                        for value in existing_venue_ids
                        if _clean(value)
                    ],
                ]))
            event["publicVenuePriority"] = venue.get("priority")
            event["publicVenueType"] = venue.get("venueType")
        event["publicCurationReason"] = reason
        kept.append(slim_public_event(event))

    # Popular and current items first in the serialized feed. Frontend sorting
    # can still apply other views without reprocessing thousands of low-value rows.
    kept.sort(
        key=lambda event: (
            -int(event.get("hitRate") or 0),
            _clean(event.get("endDate")),
            _clean(event.get("title")),
        )
    )

    now = datetime.now(timezone.utc).isoformat()
    payload = deepcopy(dict(source_payload))
    payload["events"] = kept
    payload["updatedAt"] = source_payload.get("updatedAt") or now
    payload["source"] = "curated-public-feed"
    payload["curation"] = {
        "schemaVersion": 1,
        "builtAt": now,
        "sourceEventCount": len(source_payload.get("events") or []),
        "publicEventCount": len(kept),
        "policy": "major-venues-valid-link-image-no-library-no-small-local",
        "matrixVenueCount": len(matrix_payload.get("venues") or []),
    }
    original_stats = dict(source_payload.get("stats") or {})
    original_stats.update({
        "sourceEventCount": len(source_payload.get("events") or []),
        "eventCount": len(kept),
        "curatedEventCount": len(kept),
        "imageCoverage": 100.0 if kept else 0.0,
        "outboundLinkCoverage": 100.0 if kept else 0.0,
    })
    payload["stats"] = original_stats

    used_venues = {
        _clean(event.get("venueGroup") or event.get("locationName"))
        for event in kept
    }
    venue_images = source_payload.get("venueImages") or {}
    if isinstance(venue_images, Mapping):
        payload["venueImages"] = {
            key: value for key, value in venue_images.items()
            if key in used_venues
        }

    report = {
        "schemaVersion": 1,
        "builtAt": now,
        "sourceEventCount": len(source_payload.get("events") or []),
        "publicEventCount": len(kept),
        "removedEventCount": len(source_payload.get("events") or []) - len(kept),
        "keptReasons": dict(sorted(kept_counts.items())),
        "removedReasons": dict(sorted(removed_counts.items())),
        "removedSamples": removed_samples,
    }
    return payload, report
