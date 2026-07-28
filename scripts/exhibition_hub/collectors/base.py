from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from time import perf_counter
from types import MappingProxyType
from typing import Any, Mapping, MutableMapping, Sequence, TypeAlias
from uuid import uuid4


RawEvent: TypeAlias = dict[str, Any]


class CollectorError(RuntimeError):
    """Expected failure while collecting from an external source."""


class CollectorContractError(ValueError):
    """Raised when a collector emits an invalid framework record."""


class SourceKind(str, Enum):
    API = "api"
    HTML = "html"
    RSS = "rss"
    SOCIAL = "social"
    MANUAL = "manual"


@dataclass(frozen=True)
class CollectorContext:
    run_id: str
    started_at: datetime
    timeout_seconds: float
    user_agent: str
    settings: Mapping[str, Any]

    @classmethod
    def create(
        cls,
        *,
        timeout_seconds: float = 25,
        user_agent: str = "TaiwanExhibitionJournal-Collector/1.0",
        settings: Mapping[str, Any] | None = None,
    ) -> "CollectorContext":
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")
        normalized_user_agent = str(user_agent).strip()
        if not normalized_user_agent:
            raise ValueError("user_agent must not be blank")
        copied_settings = dict(settings or {})
        return cls(
            run_id=uuid4().hex,
            started_at=datetime.now(timezone.utc),
            timeout_seconds=float(timeout_seconds),
            user_agent=normalized_user_agent,
            settings=MappingProxyType(copied_settings),
        )


@dataclass
class CollectionResult:
    source_id: str
    source_name: str
    source_kind: SourceKind
    events: list[RawEvent] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None

    @property
    def succeeded(self) -> bool:
        return not self.errors

    @property
    def event_count(self) -> int:
        return len(self.events)

    @property
    def duration_seconds(self) -> float:
        if self.finished_at is None:
            return 0.0
        return max(0.0, (self.finished_at - self.started_at).total_seconds())

    def add_event(self, event: Mapping[str, Any]) -> None:
        self.events.append(dict(event))

    def add_warning(self, warning: str) -> None:
        normalized = str(warning).strip()
        if normalized:
            self.warnings.append(normalized)

    def add_error(self, error: str) -> None:
        normalized = str(error).strip()
        if normalized:
            self.errors.append(normalized)

    def finish(self) -> None:
        if self.finished_at is None:
            self.finished_at = datetime.now(timezone.utc)

    def as_summary(self) -> dict[str, Any]:
        return {
            "sourceId": self.source_id,
            "sourceName": self.source_name,
            "sourceKind": self.source_kind.value,
            "succeeded": self.succeeded,
            "eventCount": self.event_count,
            "warningCount": len(self.warnings),
            "errorCount": len(self.errors),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "startedAt": self.started_at.isoformat(),
            "finishedAt": (
                self.finished_at.isoformat()
                if self.finished_at is not None
                else None
            ),
            "durationSeconds": self.duration_seconds,
        }


@dataclass(frozen=True)
class CollectorSource:
    id: str
    name: str
    status: str
    enabled: bool
    parser: str
    official_url: str
    listing_url: str
    trust_level: str
    refresh_hours: int
    raw: Mapping[str, Any] = field(repr=False)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "CollectorSource":
        source_id = str(value.get("id") or "").strip()
        name = str(value.get("name") or "").strip()
        if not source_id or not name:
            raise CollectorContractError("Collector source requires id and name")
        return cls(
            id=source_id,
            name=name,
            status=str(value.get("status") or "planned"),
            enabled=bool(value.get("enabled", False)),
            parser=str(value.get("parser") or ""),
            official_url=str(value.get("officialUrl") or ""),
            listing_url=str(value.get("listingUrl") or ""),
            trust_level=str(value.get("trustLevel") or "unknown"),
            refresh_hours=int(value.get("refreshHours") or 24),
            raw=value,
        )


@dataclass(frozen=True)
class CollectorRecord:
    source_id: str
    source_event_id: str
    title: str
    detail_url: str
    raw: Mapping[str, Any]

    def validate(self) -> None:
        missing = [
            field_name
            for field_name, field_value in (
                ("source_id", self.source_id),
                ("source_event_id", self.source_event_id),
                ("title", self.title),
                ("detail_url", self.detail_url),
            )
            if not str(field_value).strip()
        ]
        if missing:
            raise CollectorContractError(
                "Collector record missing: " + ", ".join(missing)
            )
        if not self.detail_url.startswith(("https://", "http://")):
            raise CollectorContractError("detail_url must be HTTP(S)")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass
class CollectorRunReport:
    source_id: str
    status: str
    records: list[CollectorRecord] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    fetched_pages: int = 0
    duration_ms: int = 0
    started_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def success(self) -> bool:
        return self.status in {"success", "partial", "skipped"} and not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "sourceId": self.source_id,
            "status": self.status,
            "success": self.success,
            "recordCount": len(self.records),
            "records": [record.to_dict() for record in self.records],
            "warnings": self.warnings,
            "errors": self.errors,
            "fetchedPages": self.fetched_pages,
            "durationMs": self.duration_ms,
            "startedAt": self.started_at,
        }


class BaseCollector:
    """Compatibility base for legacy collectors and venue collectors.

    Legacy collectors implement ``_collect(context, result)`` and use
    :meth:`collect`. New venue collectors implement ``collect_raw`` plus
    ``normalize_record`` and use :meth:`run`.
    """

    source_id: str = ""
    source_name: str = ""
    source_kind: SourceKind = SourceKind.MANUAL

    def _validate_identity(self) -> None:
        if not str(self.source_id).strip():
            raise ValueError("Collector must define source_id")
        if not str(self.source_name).strip():
            raise ValueError("Collector must define source_name")
        if not isinstance(self.source_kind, SourceKind):
            raise ValueError("Collector must define a valid source_kind")

    def collect(self, context: CollectorContext) -> CollectionResult:
        self._validate_identity()
        result = CollectionResult(
            source_id=self.source_id,
            source_name=self.source_name,
            source_kind=self.source_kind,
            started_at=context.started_at,
        )
        try:
            self._collect(context, result)
        except CollectorError as exc:
            result.add_error(str(exc))
        except Exception as exc:  # preserve collector boundary
            result.add_error(f"Unexpected {type(exc).__name__}: {exc}")
        finally:
            result.finish()
        return result

    def _collect(
        self,
        context: CollectorContext,
        result: CollectionResult,
    ) -> None:
        raise NotImplementedError(
            "Legacy collectors must implement _collect(context, result)"
        )

    def collect_raw(
        self,
        source: CollectorSource,
        client: Any,
    ) -> Sequence[Mapping[str, Any]]:
        raise NotImplementedError(
            "Venue collectors must implement collect_raw(source, client)"
        )

    def normalize_record(
        self,
        source: CollectorSource,
        raw: Mapping[str, Any],
    ) -> CollectorRecord:
        raise NotImplementedError(
            "Venue collectors must implement normalize_record(source, raw)"
        )

    def run(self, source: CollectorSource, client: Any) -> CollectorRunReport:
        started = perf_counter()
        report = CollectorRunReport(source_id=source.id, status="success")
        try:
            raw_records = list(self.collect_raw(source, client))
            for raw in raw_records:
                record = self.normalize_record(source, raw)
                record.validate()
                report.records.append(record)
        except Exception as exc:  # collector boundary: report, do not hide
            report.status = "failed"
            report.errors.append(f"{type(exc).__name__}: {exc}")
        report.duration_ms = round((perf_counter() - started) * 1000)
        return report
