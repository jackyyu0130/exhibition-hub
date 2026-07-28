from __future__ import annotations

import json
from pathlib import Path

from .base import CollectorSource


def load_collector_sources(path: str | Path) -> list[CollectorSource]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    values = payload.get("sources")
    if not isinstance(values, list):
        raise ValueError("source_registry.json must contain a sources list")
    return [CollectorSource.from_mapping(value) for value in values]
