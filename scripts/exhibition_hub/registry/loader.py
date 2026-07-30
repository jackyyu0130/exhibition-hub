"""Registry loading and venue alias resolution helpers."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Mapping


def project_root() -> Path:
    """Return the repository root from this package location."""

    return Path(__file__).resolve().parents[3]


def _load_json(path: Path) -> dict[str, Any]:
    """Load a UTF-8 JSON object."""

    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, dict):
        raise ValueError(f"Registry root must be an object: {path}")

    return payload


def load_source_registry(
    path: str | Path | None = None,
) -> dict[str, Any]:
    """Load data/source_registry.json."""

    registry_path = (
        Path(path)
        if path is not None
        else project_root() / "data" / "source_registry.json"
    )
    return _load_json(registry_path)


def load_venue_registry(
    path: str | Path | None = None,
) -> dict[str, Any]:
    """Load data/venues.json."""

    registry_path = (
        Path(path)
        if path is not None
        else project_root() / "data" / "venues.json"
    )
    return _load_json(registry_path)


def normalize_venue_key(value: Any) -> str:
    """Normalize venue names for exact alias matching."""

    text = str(value or "").strip().lower()
    text = text.replace("台", "臺")
    text = re.sub(r"[\s\-－_・·（）()【】\[\]「」『』]+", "", text)
    return text


def build_venue_alias_index(
    venue_registry: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    """Build an alias-to-venue lookup table."""

    index: dict[str, dict[str, Any]] = {}

    for raw_venue in venue_registry.get("venues", []):
        if not isinstance(raw_venue, dict):
            continue

        names = [
            raw_venue.get("name"),
            *raw_venue.get("aliases", []),
        ]

        for name in names:
            normalized = normalize_venue_key(name)

            if normalized:
                index[normalized] = raw_venue

    return index


def resolve_venue(
    value: Any,
    venue_registry: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Resolve a canonical venue from its name or alias."""

    registry = (
        venue_registry
        if venue_registry is not None
        else load_venue_registry()
    )
    index = build_venue_alias_index(registry)
    return index.get(normalize_venue_key(value))


def source_registry_summary(
    source_registry: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a compact source coverage summary."""

    sources = [
        source
        for source in source_registry.get("sources", [])
        if isinstance(source, dict)
    ]

    active_sources = [
        source
        for source in sources
        if source.get("enabled") is True
        and source.get("status") == "active"
    ]

    region_counts: dict[str, int] = {}

    for source in sources:
        for region in source.get("coverageRegions", []):
            region_counts[region] = region_counts.get(region, 0) + 1

    return {
        "sourceCount": len(sources),
        "activeSourceCount": len(active_sources),
        "plannedSourceCount": sum(
            1
            for source in sources
            if source.get("status") == "planned"
        ),
        "coverageRegionCount": len(
            source_registry.get("coverageRegions", [])
        ),
        "sourceCountsByRegion": dict(
            sorted(region_counts.items())
        ),
    }
