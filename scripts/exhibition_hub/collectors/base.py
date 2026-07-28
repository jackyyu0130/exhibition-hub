from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Mapping, Sequence


class CollectorContractError(ValueError):
    """Raised when a collector emits an invalid record."""


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


class BaseCollector(ABC):
    """Base contract implemented by every official-source collector."""

    source_id: str

    @abstractmethod
    def collect_raw(self, source: CollectorSource, client: Any) -> Sequence[Mapping[str, Any]]:
        """Collect raw list/detail records from one official source."""

    @abstractmethod
    def normalize_record(
        self,
        source: CollectorSource,
        raw: Mapping[str, Any],
    ) -> CollectorRecord:
        """Convert one raw record into the shared collector contract."""

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
