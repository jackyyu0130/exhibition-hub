"""Registry for discovering and creating exhibition collectors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .base import BaseCollector, SourceKind


@dataclass(slots=True, frozen=True)
class CollectorRegistration:
    """Metadata and factory information for one collector."""

    collector_type: type[BaseCollector]
    source_id: str
    source_name: str
    source_kind: SourceKind
    priority: int = 100
    enabled: bool = True

    def create(self) -> BaseCollector:
        """Create a fresh collector instance for one pipeline run."""

        collector = self.collector_type()

        current_source_id = str(
            getattr(collector, "source_id", "")
        ).strip()

        if current_source_id != self.source_id:
            raise ValueError(
                f"{self.collector_type.__name__}.source_id "
                f"changed from {self.source_id!r} "
                f"to {current_source_id!r}"
            )

        return collector

    def as_summary(self) -> dict[str, object]:
        return {
            "sourceId": self.source_id,
            "sourceName": self.source_name,
            "sourceKind": self.source_kind.value,
            "priority": self.priority,
            "enabled": self.enabled,
            "collectorClass": self.collector_type.__name__,
        }


class CollectorRegistry:
    """Ordered collection of available data-source collectors."""

    def __init__(self) -> None:
        self._registrations: dict[
            str,
            CollectorRegistration,
        ] = {}

    def register(
        self,
        collector_type: type[BaseCollector],
        *,
        priority: int = 100,
        enabled: bool = True,
    ) -> CollectorRegistration:
        """Register a collector class and validate its identity."""

        if not isinstance(priority, int):
            raise TypeError("priority must be an integer")

        try:
            collector = collector_type()

        except TypeError as exc:
            raise TypeError(
                f"{collector_type.__name__} must support "
                "construction without arguments"
            ) from exc

        source_id = str(
            getattr(collector, "source_id", "")
        ).strip()
        source_name = str(
            getattr(collector, "source_name", "")
        ).strip()
        source_kind = getattr(
            collector,
            "source_kind",
            None,
        )

        if not source_id:
            raise ValueError(
                f"{collector_type.__name__}.source_id "
                "must not be empty"
            )

        if not source_name:
            raise ValueError(
                f"{collector_type.__name__}.source_name "
                "must not be empty"
            )

        if not isinstance(source_kind, SourceKind):
            raise TypeError(
                f"{collector_type.__name__}.source_kind "
                "must be a SourceKind value"
            )

        if source_id in self._registrations:
            existing = self._registrations[source_id]

            raise ValueError(
                f"Duplicate collector source_id {source_id!r}: "
                f"{existing.collector_type.__name__} and "
                f"{collector_type.__name__}"
            )

        registration = CollectorRegistration(
            collector_type=collector_type,
            source_id=source_id,
            source_name=source_name,
            source_kind=source_kind,
            priority=priority,
            enabled=enabled,
        )

        self._registrations[source_id] = registration
        return registration

    def get(
        self,
        source_id: str,
    ) -> CollectorRegistration:
        """Return one registration or raise a clear error."""

        normalized_source_id = source_id.strip()

        try:
            return self._registrations[
                normalized_source_id
            ]

        except KeyError as exc:
            raise KeyError(
                f"Unknown collector source_id: "
                f"{normalized_source_id!r}"
            ) from exc

    def registrations(
        self,
    ) -> list[CollectorRegistration]:
        """Return all registrations in execution order."""

        return sorted(
            self._registrations.values(),
            key=lambda item: (
                item.priority,
                item.source_id,
            ),
        )

    def create_collectors(
        self,
        *,
        include: Iterable[str] | None = None,
        exclude: Iterable[str] | None = None,
    ) -> list[BaseCollector]:
        """Create enabled collectors selected by source ID."""

        included_ids = (
            {item.strip() for item in include if item.strip()}
            if include is not None
            else None
        )
        excluded_ids = {
            item.strip()
            for item in (exclude or [])
            if item.strip()
        }

        known_ids = set(self._registrations)

        requested_ids = (
            included_ids or set()
        ) | excluded_ids

        unknown_ids = requested_ids - known_ids

        if unknown_ids:
            unknown_list = ", ".join(
                sorted(unknown_ids)
            )

            raise KeyError(
                f"Unknown collector source IDs: "
                f"{unknown_list}"
            )

        collectors: list[BaseCollector] = []

        for registration in self.registrations():
            if not registration.enabled:
                continue

            if (
                included_ids is not None
                and registration.source_id
                not in included_ids
            ):
                continue

            if registration.source_id in excluded_ids:
                continue

            collectors.append(registration.create())

        return collectors

    def as_summary(self) -> list[dict[str, object]]:
        """Return JSON-safe metadata for monitoring pages."""

        return [
            registration.as_summary()
            for registration in self.registrations()
        ]
