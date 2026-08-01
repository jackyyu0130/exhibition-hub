#!/usr/bin/env python3
"""Build the lightweight public exhibition feed from the enriched audit feed."""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import re
from typing import Any, Mapping

from exhibition_hub.curation import build_curated_payload


STRICT_ANIME_TITLE_RE = re.compile(
    r"動漫|動畫展|漫畫(?:原作|展)?|原畫展|電玩|遊戲展|電競|ACG|cosplay|"
    r"公仔|角色展|角色限定|模型展|玩具展|扭蛋|盒玩|卡牌|聲優|VTuber|"
    r"虛擬偶像|特攝|輕小說|IP(?:展|祭|授權)|寶可夢|吉伊卡哇|chiikawa|"
    r"櫻桃小丸子|蠟筆小新|哆啦A夢|三麗鷗|迪士尼|皮克斯|史努比|姆明|"
    r"航海王|ONE\s*PIECE|鬼滅之刃|咒術迴戰|進擊的巨人|排球少年|"
    r"名偵探柯南|七龍珠|鋼彈|GUNDAM|新世紀福音戰士|初音未來|"
    r"hololive|anime",
    re.I,
)
POPUP_TITLE_RE = re.compile(r"快閃|期間限定|限定店|pop-?up", re.I)
MARKET_TITLE_RE = re.compile(r"市集|餐車|美食|展售|蚤之市|嘉年華", re.I)
FILM_TITLE_RE = re.compile(r"電影|影展|放映|紀錄片|短片節|動畫影展", re.I)
MUSIC_TITLE_RE = re.compile(
    r"音樂會|演唱會|音樂祭|音樂節|交響|管弦|協奏|獨奏|重奏|樂團",
    re.I,
)
PERFORMANCE_TITLE_RE = re.compile(
    r"舞台劇|音樂劇|歌劇|劇場|戲劇|舞蹈|芭蕾|馬戲|偶戲",
    re.I,
)
ART_TITLE_RE = re.compile(
    r"美術|藝術|個展|聯展|畫展|攝影展|雕塑|裝置|典藏|書畫|陶藝",
    re.I,
)
DESIGN_TITLE_RE = re.compile(r"設計|建築|工藝|時尚|家居|文具", re.I)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/exhibitions.enriched.json")
    parser.add_argument("--matrix", default="data/taiwan_venue_matrix.json")
    parser.add_argument("--output", default="data/exhibitions.curated.json")
    parser.add_argument(
        "--report",
        default="data/update-reports/curated-feed-report.json",
    )
    return parser.parse_args()


def read_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def fallback_public_category(
    title: str,
    categories: list[str],
) -> str:
    """Choose a conservative replacement for a noisy anime source label."""
    rules = (
        ("電影", FILM_TITLE_RE),
        ("表演", PERFORMANCE_TITLE_RE),
        ("音樂", MUSIC_TITLE_RE),
        ("快閃店", POPUP_TITLE_RE),
        ("市集", MARKET_TITLE_RE),
        ("美術", ART_TITLE_RE),
        ("設計", DESIGN_TITLE_RE),
    )
    for label, pattern in rules:
        if pattern.search(title):
            return label
    for category in categories:
        if category not in {"動漫", "講座", "研習"}:
            return category
    return "其他"


def reconcile_public_categories(
    payload: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, int]]:
    """Enforce final public taxonomy contracts before serialization."""
    result = deepcopy(dict(payload))
    events = result.get("events") or []
    corrected_anime = 0

    for event in events:
        if not isinstance(event, dict):
            continue
        title = str(event.get("title") or "").strip()
        category = str(event.get("category") or "").strip()
        categories = [
            str(value).strip()
            for value in event.get("categories") or []
            if str(value).strip()
        ]
        is_public_anime = category == "動漫" or (
            categories and categories[0] == "動漫"
        )
        if not is_public_anime or STRICT_ANIME_TITLE_RE.search(title):
            continue

        replacement = fallback_public_category(title, categories)
        remaining = [
            value
            for value in categories
            if value not in {"動漫", replacement, "講座", "研習"}
        ]
        event["category"] = replacement
        event["categories"] = [replacement, *remaining][:3]
        corrected_anime += 1

    stats = dict(result.get("stats") or {})
    stats["taxonomyCorrectionCount"] = corrected_anime
    result["stats"] = stats
    return result, {"animeWithoutTitleSignal": corrected_anime}


def main() -> int:
    args = parse_args()
    payload, report = build_curated_payload(
        read_json(args.input),
        read_json(args.matrix),
    )
    payload, taxonomy_corrections = reconcile_public_categories(payload)
    report = dict(report)
    report["taxonomyCorrections"] = taxonomy_corrections
    write_json(args.output, payload)
    write_json(args.report, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
