from __future__ import annotations

from dataclasses import dataclass
import inspect
from typing import Iterable

from .base import BaseCollector, SourceKind


@dataclass(frozen=True)
class CollectorRegistration:
    collector_type: type[BaseCollector]
    source_id: str
    source_name: str
    source_kind: SourceKind
    priority: int = 100
    enabled: bool = True

    def create(self) -> BaseCollector:
        return self.collector_type()

    def to_dict(self) -> dict:
        return {
            "sourceId": self.source_id,
            "sourceName": self.source_name,
            "sourceKind": self.source_kind.value,
            "priority": self.priority,
            "enabled": self.enabled,
            "collectorClass": self.collector_type.__name__,
        }


class CollectorRegistry:
    def __init__(self) -> None:
        self._registrations: dict[str, CollectorRegistration] = {}

    def register(
        self,
        collector_type: type[BaseCollector],
        *,
        priority: int = 100,
        enabled: bool = True,
    ) -> CollectorRegistration:
        if not isinstance(collector_type, type) or not issubclass(
            collector_type,
            BaseCollector,
        ):
            raise TypeError("collector_type must be a BaseCollector subclass")
        if not isinstance(priority, int) or isinstance(priority, bool):
            raise TypeError("priority must be an integer")

        source_id = str(getattr(collector_type, "source_id", "")).strip()
        if not source_id:
            raise ValueError("Collector class must define source_id")
        if source_id in self._registrations:
            raise ValueError(f"Collector already registered: {source_id}")

        signature = inspect.signature(collector_type)
        required = [
            parameter
            for parameter in signature.parameters.values()
            if parameter.default is inspect.Parameter.empty
            and parameter.kind in {
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY,
            }
        ]
        if required:
            raise TypeError("Collector must be constructible without arguments")

        source_name = str(
            getattr(collector_type, "source_name", "") or source_id
        ).strip()
        source_kind = getattr(
            collector_type,
            "source_kind",
            SourceKind.HTML,
        )
        if not isinstance(source_kind, SourceKind):
            raise ValueError("Collector class must define a valid source_kind")

        registration = CollectorRegistration(
            collector_type=collector_type,
            source_id=source_id,
            source_name=source_name,
            source_kind=source_kind,
            priority=priority,
            enabled=bool(enabled),
        )
        self._registrations[source_id] = registration
        return registration

    def get(self, source_id: str) -> CollectorRegistration | None:
        return self._registrations.get(source_id)

    def create(self, source_id: str) -> BaseCollector | None:
        registration = self.get(source_id)
        return registration.create() if registration else None

    def ids(self) -> list[str]:
        return sorted(self._registrations)

    def registrations(self) -> list[CollectorRegistration]:
        return sorted(
            self._registrations.values(),
            key=lambda item: (item.priority, item.source_id),
        )

    def create_collectors(
        self,
        *,
        include: Iterable[str] | None = None,
        exclude: Iterable[str] | None = None,
    ) -> list[BaseCollector]:
        include_ids = set(include or [])
        exclude_ids = set(exclude or [])
        known_ids = set(self._registrations)

        unknown = (include_ids | exclude_ids) - known_ids
        if unknown:
            raise KeyError(f"Unknown collector source: {sorted(unknown)[0]}")

        collectors: list[BaseCollector] = []
        for registration in self.registrations():
            if not registration.enabled:
                continue
            if include_ids and registration.source_id not in include_ids:
                continue
            if registration.source_id in exclude_ids:
                continue
            collectors.append(registration.create())
        return collectors

    def as_summary(self) -> list[dict]:
        return [registration.to_dict() for registration in self.registrations()]


collector_registry = CollectorRegistry()
