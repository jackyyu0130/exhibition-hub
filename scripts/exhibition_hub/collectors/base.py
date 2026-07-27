"""Shared contracts for all exhibition data collectors.

A collector is responsible only for retrieving raw records from one source.
Normalization, deduplication, publication, and monitoring are handled by other
pipeline layers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping, TypeAlias
from uuid import uuid4


RawEvent: TypeAlias = dict[str, Any]

DEFAULT_USER_AGENT = (
    "TaiwanExhibitionJournal/5.0 "
    "(+https://github.com/jackyyu0130/exhibition-hub)"
)


class SourceKind(StrEnum):
    """Supported source families used for reporting and routing."""

    API = "api"
    HTML = "html"
    RSS = "rss"
    SOCIAL = "social"
    MANUAL = "manual"


class CollectorError(RuntimeError):
    """Expected source failure that should not stop other collectors."""


@dataclass(slots=True, frozen=True)
class CollectorContext:
    """Settings shared with every collector during one pipeline run."""

    run_id: str
    started_at: datetime
    timeout_seconds: float = 30.0
    user_agent: str = DEFAULT_USER_AGENT
    settings: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.run_id.strip():
            raise ValueError("run_id must not be empty")

        if self.started_at.tzinfo is None:
            raise ValueError("started_at must be timezone-aware")

        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")

        if not self.user_agent.strip():
            raise ValueError("user_agent must not be empty")

        object.__setattr__(
            self,
            "settings",
            MappingProxyType(dict(self.settings)),
        )

    @classmethod
    def create(
        cls,
        *,
        timeout_seconds: float = 30.0,
        user_agent: str = DEFAULT_USER_AGENT,
        settings: Mapping[str, Any] | None = None,
    ) -> "CollectorContext":
        """Create a context for a new data update execution."""

        return cls(
            run_id=uuid4().hex,
            started_at=datetime.now(timezone.utc),
            timeout_seconds=timeout_seconds,
            user_agent=user_agent,
            settings=settings or {},
        )


@dataclass(slots=True)
class CollectionResult:
    """Raw records and diagnostics returned by one collector."""

    source_id: str
    source_name: str
    source_kind: SourceKind
    events: list[RawEvent] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    started_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    finished_at: datetime | None = None

    @property
    def succeeded(self) -> bool:
        return not self.errors

    @property
    def event_count(self) -> int:
        return len(self.events)

    @property
    def duration_seconds(self) -> float | None:
        if self.finished_at is None:
            return None

        return max(
            0.0,
            (self.finished_at - self.started_at).total_seconds(),
        )

    def add_event(self, event: Mapping[str, Any]) -> None:
        """Store a copy so the original record cannot be mutated later."""

        self.events.append(dict(event))

    def add_warning(self, message: str) -> None:
        cleaned = message.strip()

        if cleaned:
            self.warnings.append(cleaned)

    def add_error(self, message: str) -> None:
        cleaned = message.strip()

        if cleaned:
            self.errors.append(cleaned)

    def finish(self) -> None:
        if self.finished_at is None:
            self.finished_at = datetime.now(timezone.utc)

    def as_summary(self) -> dict[str, Any]:
        """Return JSON-safe metadata without duplicating event contents."""

        return {
            "sourceId": self.source_id,
            "sourceName": self.source_name,
            "sourceKind": self.source_kind.value,
            "succeeded": self.succeeded,
            "eventCount": self.event_count,
            "warningCount": len(self.warnings),
            "errorCount": len(self.errors),
            "startedAt": self.started_at.isoformat(),
            "finishedAt": (
                self.finished_at.isoformat()
                if self.finished_at
                else None
            ),
            "durationSeconds": self.duration_seconds,
        }


class BaseCollector(ABC):
    """Template for API, venue, RSS, and social collectors."""

    source_id: str = ""
    source_name: str = ""
    source_kind: SourceKind = SourceKind.HTML

    def collect(
        self,
        context: CollectorContext,
    ) -> CollectionResult:
        """Run one collector without stopping the complete pipeline."""

        self._validate_identity()

        result = CollectionResult(
            source_id=self.source_id,
            source_name=self.source_name,
            source_kind=self.source_kind,
        )

        try:
            self._collect(context, result)

        except CollectorError as exc:
            result.add_error(str(exc))

        except Exception as exc:
            result.add_error(
                f"Unexpected {type(exc).__name__}: {exc}"
            )

        finally:
            result.finish()

        return result

    def _validate_identity(self) -> None:
        if not self.source_id.strip():
            raise ValueError(
                f"{type(self).__name__}.source_id must not be empty"
            )

        if not self.source_name.strip():
            raise ValueError(
                f"{type(self).__name__}.source_name must not be empty"
            )

        if not isinstance(self.source_kind, SourceKind):
            raise TypeError(
                f"{type(self).__name__}.source_kind "
                "must be a SourceKind value"
            )

    @abstractmethod
    def _collect(
        self,
        context: CollectorContext,
        result: CollectionResult,
    ) -> None:
        """Retrieve raw records and append them to the result."""
