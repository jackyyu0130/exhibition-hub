from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable

from .base import (
    BaseCollector,
    CollectionResult,
    CollectorContext,
    CollectorRunReport,
    CollectorSource,
    SourceKind,
)
from .http import CollectorHttpClient
from .registry import CollectorRegistry


@dataclass
class CollectorBatchResult:
    run_id: str
    started_at: datetime
    results: list[CollectionResult] = field(default_factory=list)
    finished_at: datetime | None = None

    @property
    def source_count(self) -> int:
        return len(self.results)

    @property
    def successful_source_count(self) -> int:
        return sum(1 for result in self.results if result.succeeded)

    @property
    def failed_source_count(self) -> int:
        return self.source_count - self.successful_source_count

    @property
    def event_count(self) -> int:
        return sum(result.event_count for result in self.results)

    @property
    def events(self) -> list[dict]:
        return [
            event
            for result in self.results
            if result.succeeded
            for event in result.events
        ]

    @property
    def published_event_count(self) -> int:
        return len(self.events)

    @property
    def duration_seconds(self) -> float:
        if self.finished_at is None:
            return 0.0
        return max(0.0, (self.finished_at - self.started_at).total_seconds())

    def as_summary(self) -> dict:
        return {
            "runId": self.run_id,
            "startedAt": self.started_at.isoformat(),
            "finishedAt": (
                self.finished_at.isoformat()
                if self.finished_at is not None
                else None
            ),
            "durationSeconds": self.duration_seconds,
            "sourceCount": self.source_count,
            "successfulSourceCount": self.successful_source_count,
            "failedSourceCount": self.failed_source_count,
            "eventCount": self.event_count,
            "publishedEventCount": self.published_event_count,
            "sources": [result.as_summary() for result in self.results],
        }


def run_collectors(
    collectors: Iterable[BaseCollector],
    *,
    context: CollectorContext | None = None,
) -> CollectorBatchResult:
    active_context = context or CollectorContext.create()
    batch = CollectorBatchResult(
        run_id=active_context.run_id,
        started_at=active_context.started_at,
    )

    for collector in collectors:
        try:
            result = collector.collect(active_context)
        except Exception as exc:
            source_id = str(getattr(collector, "source_id", "")).strip()
            source_name = str(getattr(collector, "source_name", "")).strip()
            source_kind = getattr(collector, "source_kind", SourceKind.MANUAL)
            if not isinstance(source_kind, SourceKind):
                source_kind = SourceKind.MANUAL
            result = CollectionResult(
                source_id=source_id or collector.__class__.__name__,
                source_name=source_name or collector.__class__.__name__,
                source_kind=source_kind,
                started_at=active_context.started_at,
            )
            result.add_error(
                f"Collector setup failed: {type(exc).__name__}: {exc}"
            )
            result.finish()
        batch.results.append(result)

    batch.finished_at = datetime.now(timezone.utc)
    return batch


class CollectorRunner:
    """Runner for the new official venue collector contract."""

    def __init__(
        self,
        registry: CollectorRegistry,
        client: CollectorHttpClient | None = None,
    ) -> None:
        self.registry = registry
        self.client = client or CollectorHttpClient()

    def run_source(
        self,
        source: CollectorSource,
        *,
        allow_planned: bool = False,
    ) -> CollectorRunReport:
        if not source.enabled and not allow_planned:
            return CollectorRunReport(
                source_id=source.id,
                status="skipped",
                warnings=["Source is disabled or planned"],
            )

        collector = self.registry.create(source.id)
        if collector is None:
            return CollectorRunReport(
                source_id=source.id,
                status="failed",
                errors=[f"Collector not implemented: {source.id}"],
            )

        return collector.run(source, self.client)
