"""Classify events into editorial content types and review flags."""

from __future__ import annotations

from datetime import date
import re
from typing import Any, Mapping


EXHIBITION_TITLE_KEYWORDS = (
    "展覽",
    "特展",
    "常設展",
    "故事展",
    "主題展",
    "攝影展",
    "畫展",
    "個展",
    "聯展",
    "藝術展",
    "作品展",
    "成果展",
    "畢業展",
    "設計展",
    "文物展",
    "巡迴展",
    "沉浸式體驗展",
)

ART_EXHIBITION_TITLE_KEYWORDS = (
    "個展",
    "聯展",
    "畫展",
    "攝影展",
    "藝術展",
    "水墨展",
    "油畫展",
    "書法展",
    "雕塑展",
    "陶藝展",
    "版畫展",
    "裝置藝術",
    "藝術家",
)

EXPO_TITLE_KEYWORDS = (
    "博覽會",
    "展售會",
    "漫畫博覽會",
    "動漫節",
    "電玩展",
    "國際書展",
    "旅展",
    "寵物展",
    "加盟展",
    "國際展覽",
    "expo",
)

CONCERT_TITLE_KEYWORDS = (
    "演唱會",
    "巡迴演唱會",
    "世界巡演",
    "巡迴演出",
    "concert",
    "live in taipei",
    "live in kaohsiung",
    "fan concert",
    "粉絲演唱會",
)

MUSIC_FESTIVAL_TITLE_KEYWORDS = (
    "音樂祭",
    "music festival",
    "搖滾祭",
    "大港開唱",
    "浪人祭",
    "火球祭",
    "春浪",
)

PERFORMANCE_TITLE_KEYWORDS = (
    "舞台劇",
    "音樂劇",
    "戲劇",
    "舞蹈",
    "芭蕾",
    "歌劇",
    "表演藝術",
    "脫口秀",
    "相聲",
    "馬戲",
    "偶戲",
    "讀劇",
)

POPUP_TITLE_KEYWORDS = (
    "快閃",
    "期間限定",
    "限定店",
    "pop-up",
    "popup",
)

MARKET_TITLE_KEYWORDS = (
    "市集",
    "蚤之市",
    "手作市集",
    "文創市集",
    "創意市集",
)

FESTIVAL_TITLE_KEYWORDS = (
    "藝術節",
    "文化節",
    "設計節",
    "燈節",
    "城市節",
    "嘉年華",
)

FILM_TITLE_KEYWORDS = (
    "影展",
    "電影節",
    "電影放映",
    "特映會",
    "放映會",
    "紀錄片放映",
    "劇場版",
)

SUPPORTED_CONTENT_TYPES = {
    "exhibition",
    "art_exhibition",
    "expo",
    "concert",
    "music_festival",
    "performance",
    "popup",
    "market",
    "festival",
    "film_screening",
}

POP_CULTURE_KEYWORDS = (
    "動漫",
    "動畫",
    "漫畫",
    "電玩",
    "遊戲",
    "角色",
    "公仔",
    "模型",
    "插畫",
    "聲優",
    "寶可夢",
    "吉伊卡哇",
    "chiikawa",
    "三麗鷗",
    "迪士尼",
    "ip展",
    "ip 展",
)

COURSE_KEYWORDS = (
    "課程",
    "研習",
    "工作坊",
    "社教班",
    "成人班",
    "招生",
    "讀書會",
    "研習班",
    "訓練班",
    "體驗課",
    "夏令營",
    "冬令營",
    "營隊",
)

TALK_KEYWORDS = (
    "講座",
    "座談",
    "論壇",
    "分享會",
    "說明會",
    "研討會",
)

MERCHANDISE_KEYWORDS = (
    "周邊商品",
    "周邊館",
    "商品套組",
    "商品組",
    "postcard kit",
    "merchandise",
    "官方周邊",
)

PLACEHOLDER_VENUE_KEYWORDS = (
    "場館資料整理中",
    "地點資料整理中",
    "場地資料整理中",
)

ONLINE_KEYWORDS = (
    "線上展",
    "線上攝影展",
    "線上活動",
    "線上放映",
    "線上直播",
    "online exhibition",
    "virtual exhibition",
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _lower(value: Any) -> str:
    return _clean(value).lower()


def _contains_any(
    text: str,
    keywords: tuple[str, ...],
) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def _categories(event: Mapping[str, Any]) -> set[str]:
    values: set[str] = set()

    category = _clean(event.get("category"))

    if category:
        values.add(category)

    categories = event.get("categories")

    if isinstance(categories, list):
        values.update(
            _clean(item)
            for item in categories
            if _clean(item)
        )

    return values


def _combined_text(event: Mapping[str, Any]) -> str:
    values: list[str] = []

    for field_name in (
        "title",
        "description",
        "locationName",
        "venueGroup",
        "category",
        "unit",
    ):
        value = _clean(event.get(field_name))

        if value:
            values.append(value)

    categories = event.get("categories")

    if isinstance(categories, list):
        values.extend(
            _clean(item)
            for item in categories
            if _clean(item)
        )

    return " ".join(values).lower()


def classify_content_types(
    event: Mapping[str, Any],
) -> list[str]:
    """Return an ordered, multi-value editorial classification."""

    title = _lower(event.get("title"))
    categories = _categories(event)
    combined = _combined_text(event)
    declared_primary = _clean(event.get("contentType"))

    has_exhibition_title = _contains_any(
        title,
        EXHIBITION_TITLE_KEYWORDS,
    )
    has_art_title = _contains_any(
        title,
        ART_EXHIBITION_TITLE_KEYWORDS,
    )
    # Source category arrays are often noisy (for example a natural-history
    # exhibition may also arrive with the generic "動漫" code). Pop-culture
    # is therefore promoted only by a strong title signal, never by a stray
    # secondary source category.
    has_pop_culture = _contains_any(
        title,
        POP_CULTURE_KEYWORDS,
    )
    primary_category = _clean(
        event.get("category")
    )
    has_film = _contains_any(
        title,
        FILM_TITLE_KEYWORDS,
    ) or primary_category == "電影"

    if _contains_any(
        title,
        MUSIC_FESTIVAL_TITLE_KEYWORDS,
    ):
        primary = "music_festival"
    elif _contains_any(
        title,
        EXPO_TITLE_KEYWORDS,
    ):
        primary = "expo"
    elif _contains_any(
        title,
        POPUP_TITLE_KEYWORDS,
    ):
        primary = "popup"
    elif _contains_any(
        title,
        MARKET_TITLE_KEYWORDS,
    ) or "市集" in categories:
        primary = "market"
    elif has_art_title:
        primary = "art_exhibition"
    elif has_exhibition_title:
        if (
            "美術" in categories
            or "攝影" in categories
            or _contains_any(
                combined,
                ART_EXHIBITION_TITLE_KEYWORDS,
            )
        ):
            primary = "art_exhibition"
        else:
            primary = "exhibition"
    elif _contains_any(
        title,
        CONCERT_TITLE_KEYWORDS,
    ):
        primary = "concert"
    elif _contains_any(
        title,
        PERFORMANCE_TITLE_KEYWORDS,
    ):
        primary = "performance"
    elif _contains_any(
        title,
        FESTIVAL_TITLE_KEYWORDS,
    ):
        primary = "festival"
    elif has_film:
        primary = "film_screening"
    elif declared_primary in SUPPORTED_CONTENT_TYPES:
        # Preserve a structured type from an upstream official collector. It
        # is more reliable than category words found in credits/descriptions.
        primary = declared_primary
    elif primary_category in {"美術", "攝影"}:
        primary = "art_exhibition"
    elif primary_category == "設計":
        primary = "exhibition"
    elif primary_category == "市集":
        primary = "market"
    elif primary_category == "動漫":
        primary = "exhibition"
    elif primary_category in {"表演", "舞蹈", "音樂"}:
        primary = "performance"
    elif "美術" in categories or "攝影" in categories:
        primary = "art_exhibition"
    elif "表演" in categories or "舞蹈" in categories:
        primary = "performance"
    elif "音樂" in categories:
        primary = "performance"
    else:
        primary = "exhibition"

    content_types = [primary]

    if has_pop_culture and "pop_culture" not in content_types:
        content_types.append("pop_culture")

    if (
        primary in {"expo", "popup", "market"}
        and _contains_any(combined, POP_CULTURE_KEYWORDS)
        and "pop_culture" not in content_types
    ):
        content_types.append("pop_culture")

    return content_types


def detect_event_format(
    event: Mapping[str, Any],
) -> str:
    """Classify an event as physical, online, or hybrid."""

    title = _lower(event.get("title"))
    location = " ".join(
        _lower(event.get(field_name))
        for field_name in (
            "locationName",
            "location",
            "venueGroup",
        )
    )
    description = _lower(event.get("description"))

    strong_online = _contains_any(
        f"{title} {location}",
        ONLINE_KEYWORDS,
    ) or "線上" in title or "線上" in location

    mentions_online = (
        strong_online
        or "線上" in description
        or "直播" in description
        or "online" in description
    )

    has_named_physical_venue = bool(
        _clean(event.get("locationName"))
        and not _contains_any(
            location,
            PLACEHOLDER_VENUE_KEYWORDS,
        )
        and "線上" not in location
        and _clean(event.get("address"))
        and _clean(event.get("region")) != "其他地區"
    )

    if strong_online and not has_named_physical_venue:
        return "online"

    if mentions_online and has_named_physical_venue:
        return "hybrid"

    if strong_online:
        return "online"

    return "physical"


def detect_editorial_flags(
    event: Mapping[str, Any],
) -> list[str]:
    """Return non-destructive editorial review flags."""

    title = _lower(event.get("title"))
    location = " ".join(
        _lower(event.get(field_name))
        for field_name in (
            "locationName",
            "location",
            "venueGroup",
        )
    )
    flags: list[str] = []

    if _contains_any(title, COURSE_KEYWORDS):
        flags.append("possible_course_or_workshop")

    if _contains_any(title, TALK_KEYWORDS):
        flags.append("possible_talk_or_forum")

    if (
        _contains_any(title, MERCHANDISE_KEYWORDS)
        or location.strip() == "商品"
    ):
        flags.append("possible_merchandise")

    if _contains_any(
        location,
        PLACEHOLDER_VENUE_KEYWORDS,
    ):
        flags.append("placeholder_venue")

    event_format = detect_event_format(event)

    if event_format == "online":
        flags.append("online_only")

    start_value = _clean(event.get("startDate"))[:10]
    end_value = _clean(event.get("endDate"))[:10]

    try:
        start_date = date.fromisoformat(start_value)
        end_date = date.fromisoformat(end_value)

        if (end_date - start_date).days > 1826:
            flags.append("long_running_over_five_years")
    except ValueError:
        pass

    return flags


def editorial_status_from_flags(
    flags: list[str],
) -> str:
    """Return a conservative editorial queue status."""

    exclude_flags = {
        "possible_course_or_workshop",
        "possible_talk_or_forum",
        "possible_merchandise",
    }

    if exclude_flags.intersection(flags):
        return "exclude_review"

    review_flags = {
        "placeholder_venue",
        "online_only",
    }

    if review_flags.intersection(flags):
        return "needs_review"

    return "candidate"


def classify_event(
    event: Mapping[str, Any],
) -> dict[str, Any]:
    """Return an event copy with editorial classification fields."""

    result = dict(event)
    content_types = classify_content_types(event)
    flags = detect_editorial_flags(event)

    result["contentType"] = content_types[0]
    result["contentTypes"] = content_types
    result["eventFormat"] = detect_event_format(event)
    result["editorialStatus"] = (
        editorial_status_from_flags(flags)
    )
    result["editorialFlags"] = flags

    return result
