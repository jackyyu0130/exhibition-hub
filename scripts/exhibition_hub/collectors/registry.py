from __future__ import annotations

from typing import Iterable, Type

from .base import BaseCollector


class CollectorRegistry:
    def __init__(self) -> None:
        self._collectors: dict[str, type[BaseCollector]] = {}

    def register(self, collector_type: type[BaseCollector]) -> type[BaseCollector]:
        source_id = str(getattr(collector_type, "source_id", "")).strip()
        if not source_id:
            raise ValueError("Collector class must define source_id")
        if source_id in self._collectors:
            raise ValueError(f"Collector already registered: {source_id}")
        self._collectors[source_id] = collector_type
        return collector_type

    def get(self, source_id: str) -> type[BaseCollector] | None:
        return self._collectors.get(source_id)

    def create(self, source_id: str) -> BaseCollector | None:
        collector_type = self.get(source_id)
        return collector_type() if collector_type else None

    def ids(self) -> list[str]:
        return sorted(self._collectors)


collector_registry = CollectorRegistry()
