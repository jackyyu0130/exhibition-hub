"""Execution helpers for running multiple data collectors safely."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable

from .base import (
    BaseCollector,
    CollectionResult,
    CollectorContext,
    RawEvent,
    SourceKind,
)


@dataclass(slots=True)
class CollectionBatch:
    """Combined outcome of all collectors in one update run."""

    run_id: str
    started_at: datetime
    results: list[CollectionResult] = field(default_factory=list)
    finished_at: datetime | None = None

    @property
    def events(self) -> list[RawEvent]:
        """Return copies of all raw events from successful collectors."""

        combined: list[RawEvent] = []

        for result in self.results:
            if not result.succeeded:
                continue

            combined.extend(dict(event) for event in result.events)

        return combined

    @property
    def source_count(self) -> int:
        return len(self.results)

    @property
    def successful_source_count(self) -> int:
        return sum(result.succeeded for result in self.results)

    @property
    def failed_source_count(self) -> int:
        return self.source_count - self.successful_source_count

    @property
    def event_count(self) -> int:
        return sum(result.event_count for result in self.results)

    @property
    def published_event_count(self) -> int:
        return len(self.events)

    @property
    def duration_seconds(self) -> float | None:
        if self.finished_at is None:
            return None

        return max(
            0.0,
            (self.finished_at - self.started_at).total_seconds(),
        )

    def finish(self) -> None:
        if self.finished_at is None:
            self.finished_at = datetime.now(timezone.utc)

    def as_summary(self) -> dict[str, Any]:
        """Return a JSON-safe execution report."""

        return {
            "runId": self.run_id,
            "startedAt": self.started_at.isoformat(),
            "finishedAt": (
                self.finished_at.isoformat()
                if self.finished_at
                else None
            ),
            "durationSeconds": self.duration_seconds,
            "sourceCount": self.source_count,
            "successfulSourceCount": self.successful_source_count,
            "failedSourceCount": self.failed_source_count,
            "eventCount": self.event_count,
            "publishedEventCount": self.published_event_count,
            "sources": [
                result.as_summary()
                for result in self.results
            ],
        }


def run_collectors(
    collectors: Iterable[BaseCollector],
    *,
    context: CollectorContext | None = None,
) -> CollectionBatch:
    """Run collectors sequentially without one failure stopping the rest."""

    active_context = context or CollectorContext.create()

    batch = CollectionBatch(
        run_id=active_context.run_id,
        started_at=active_context.started_at,
    )

    for collector in collectors:
        try:
            result = collector.collect(active_context)

        except Exception as exc:
            result = _build_setup_failure_result(
                collector,
                exc,
            )

        batch.results.append(result)

    batch.finish()
    return batch


def _build_setup_failure_result(
    collector: BaseCollector,
    error: Exception,
) -> CollectionResult:
    """Convert an invalid collector setup into a normal failed result."""

    source_id = (
        str(getattr(collector, "source_id", "")).strip()
        or type(collector).__name__
    )
    source_name = (
        str(getattr(collector, "source_name", "")).strip()
        or type(collector).__name__
    )

    candidate_kind = getattr(
        collector,
        "source_kind",
        SourceKind.MANUAL,
    )
    source_kind = (
        candidate_kind
        if isinstance(candidate_kind, SourceKind)
        else SourceKind.MANUAL
    )

    result = CollectionResult(
        source_id=source_id,
        source_name=source_name,
        source_kind=source_kind,
    )
    result.add_error(
        f"Collector setup failed: "
        f"{type(error).__name__}: {error}"
    )
    result.finish()

    return result
