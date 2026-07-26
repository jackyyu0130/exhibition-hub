"""Classify events into the site's editorial content types."""

from __future__ import annotations

from typing import Any, Mapping


KEYWORDS: dict[str, tuple[str, ...]] = {
    "music_festival": (
        "音樂祭",
        "music festival",
        "搖滾祭",
        "大港開唱",
        "浪人祭",
        "火球祭",
        "春浪",
    ),
    "concert": (
        "演唱會",
        "巡迴演唱會",
        "concert",
        "live concert",
        "粉絲見面會",
        "fan meeting",
    ),
    "performance": (
        "舞台劇",
        "音樂劇",
        "戲劇",
        "舞蹈",
        "表演藝術",
        "脫口秀",
        "相聲",
        "馬戲",
        "演出",
    ),
    "expo": (
        "博覽會",
        "展售會",
        "國際展",
        "漫畫博覽會",
        "動漫節",
        "電玩展",
        "書展",
        "旅展",
        "寵物展",
        "設計展",
        "expo",
    ),
    "popup": (
        "快閃",
        "期間限定",
        "限定店",
        "pop-up",
        "popup",
    ),
    "market": (
        "市集",
        "蚤之市",
        "手作市集",
        "文創市集",
        "創意市集",
    ),
    "festival": (
        "藝術節",
        "文化節",
        "設計節",
        "燈節",
        "城市節",
        "嘉年華",
    ),
    "pop_culture": (
        "動漫",
        "動畫",
        "漫畫",
        "遊戲",
        "電玩",
        "角色",
        "模型",
        "公仔",
        "插畫",
        "ip展",
        "ip 展",
    ),
    "art_exhibition": (
        "個展",
        "聯展",
        "畫展",
        "藝術展",
        "攝影展",
        "當代藝術",
        "裝置藝術",
        "水墨",
        "油畫",
        "雕塑",
        "藝廊",
        "藝術家",
    ),
    "exhibition": (
        "展覽",
        "特展",
        "常設展",
        "文物展",
        "沉浸式",
        "策展",
        "展示",
    ),
}

PRIMARY_PRIORITY = (
    "music_festival",
    "concert",
    "performance",
    "expo",
    "popup",
    "market",
    "festival",
    "pop_culture",
    "art_exhibition",
    "exhibition",
)


def _event_text(event: Mapping[str, Any]) -> str:
    """Join useful event fields into one lower-case search string."""

    values: list[str] = []

    for field_name in (
        "title",
        "description",
        "category",
        "locationName",
        "venueGroup",
        "unit",
    ):
        value = event.get(field_name)

        if value:
            values.append(str(value))

    for field_name in ("categories", "tags"):
        value = event.get(field_name)

        if isinstance(value, list):
            values.extend(str(item) for item in value if item)

    return " ".join(values).lower()


def classify_content_types(
    event: Mapping[str, Any],
) -> list[str]:
    """Return ordered content types for an event."""

    text = _event_text(event)
    matched = {
        content_type
        for content_type, keywords in KEYWORDS.items()
        if any(keyword in text for keyword in keywords)
    }

    if "expo" in matched and any(
        keyword in text
        for keyword in (
            "漫畫",
            "動漫",
            "動畫",
            "電玩",
            "遊戲",
        )
    ):
        matched.add("pop_culture")

    if "popup" in matched and any(
        keyword in text
        for keyword in (
            "動漫",
            "動畫",
            "漫畫",
            "角色",
            "遊戲",
            "ip",
        )
    ):
        matched.add("pop_culture")

    if not matched:
        matched.add("exhibition")

    return [
        content_type
        for content_type in PRIMARY_PRIORITY
        if content_type in matched
    ]


def classify_event(
    event: Mapping[str, Any],
) -> dict[str, Any]:
    """Return an event copy with primary and multi-value types."""

    result = dict(event)
    content_types = classify_content_types(event)

    result["contentTypes"] = content_types
    result["contentType"] = content_types[0]

    return result
