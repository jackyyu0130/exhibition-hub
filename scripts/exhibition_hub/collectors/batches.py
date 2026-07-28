from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

from .base import CollectorRunReport, CollectorSource


ALLOWED_FAILURE_POLICIES = {
    "isolate_source",
}


@dataclass(frozen=True)
class RegionGroup:
    id: str
    name: str
    coverage_regions: tuple[str, ...]

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, Any],
    ) -> "RegionGroup":
        group_id = str(
            value.get("id") or ""
        ).strip()
        name = str(
            value.get("name") or ""
        ).strip()
        if not group_id or not name:
            raise ValueError(
                "Region group requires id and name"
            )
        regions = tuple(
            str(item).strip()
            for item in (
                value.get("coverageRegions")
                or []
            )
            if str(item).strip()
        )
        return cls(
            id=group_id,
            name=name,
            coverage_regions=regions,
        )


@dataclass(frozen=True)
class SourceBatch:
    id: str
    name: str
    enabled: bool
    region_group_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    organizer_ids: tuple[str, ...]
    failure_policy: str

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, Any],
        *,
        default_failure_policy: str,
    ) -> "SourceBatch":
        batch_id = str(
            value.get("id") or ""
        ).strip()
        name = str(
            value.get("name") or ""
        ).strip()
        if not batch_id or not name:
            raise ValueError(
                "Source batch requires id and name"
            )

        source_ids = tuple(
            str(item).strip()
            for item in (
                value.get("sourceIds")
                or []
            )
            if str(item).strip()
        )
        if len(source_ids) != len(
            set(source_ids)
        ):
            raise ValueError(
                f"Duplicate source ID in batch: "
                f"{batch_id}"
            )

        failure_policy = str(
            value.get("failurePolicy")
            or default_failure_policy
        ).strip()
        if (
            failure_policy
            not in ALLOWED_FAILURE_POLICIES
        ):
            raise ValueError(
                "Unsupported failure policy: "
                + failure_policy
            )

        return cls(
            id=batch_id,
            name=name,
            enabled=bool(
                value.get("enabled", False)
            ),
            region_group_ids=tuple(
                str(item).strip()
                for item in (
                    value.get(
                        "regionGroupIds"
                    )
                    or []
                )
                if str(item).strip()
            ),
            source_ids=source_ids,
            organizer_ids=tuple(
                str(item).strip()
                for item in (
                    value.get("organizerIds")
                    or []
                )
                if str(item).strip()
            ),
            failure_policy=failure_policy,
        )


@dataclass(frozen=True)
class SourceBatchRegistry:
    schema_version: int
    updated_at: str
    region_groups: tuple[RegionGroup, ...]
    batches: tuple[SourceBatch, ...]
    max_sources_per_run: int
    default_failure_policy: str
    allow_future_source_ids: bool
    allow_organizer_expansion: bool

    def get(
        self,
        batch_id: str,
    ) -> SourceBatch | None:
        return next(
            (
                batch
                for batch in self.batches
                if batch.id == batch_id
            ),
            None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": (
                self.schema_version
            ),
            "updatedAt": self.updated_at,
            "regionGroups": [
                {
                    "id": group.id,
                    "name": group.name,
                    "coverageRegions": list(
                        group.coverage_regions
                    ),
                }
                for group in self.region_groups
            ],
            "batches": [
                {
                    "id": batch.id,
                    "name": batch.name,
                    "enabled": batch.enabled,
                    "regionGroupIds": list(
                        batch.region_group_ids
                    ),
                    "sourceIds": list(
                        batch.source_ids
                    ),
                    "organizerIds": list(
                        batch.organizer_ids
                    ),
                    "failurePolicy": (
                        batch.failure_policy
                    ),
                }
                for batch in self.batches
            ],
            "defaults": {
                "maxSourcesPerRun": (
                    self.max_sources_per_run
                ),
                "failurePolicy": (
                    self.default_failure_policy
                ),
                "allowFutureSourceIds": (
                    self.allow_future_source_ids
                ),
                "allowOrganizerExpansion": (
                    self.allow_organizer_expansion
                ),
            },
        }


def load_source_batch_registry(
    path: str | Path,
    *,
    known_source_ids: Sequence[str] = (),
) -> SourceBatchRegistry:
    payload = json.loads(
        Path(path).read_text(
            encoding="utf-8"
        )
    )
    if not isinstance(payload, dict):
        raise ValueError(
            "source_batches.json root "
            "must be an object"
        )

    defaults = payload.get("defaults") or {}
    default_failure_policy = str(
        defaults.get("failurePolicy")
        or "isolate_source"
    ).strip()
    if (
        default_failure_policy
        not in ALLOWED_FAILURE_POLICIES
    ):
        raise ValueError(
            "Unsupported default failure policy: "
            + default_failure_policy
        )

    max_sources = int(
        defaults.get(
            "maxSourcesPerRun"
        )
        or 10
    )
    if max_sources <= 0:
        raise ValueError(
            "maxSourcesPerRun must be positive"
        )

    region_groups = tuple(
        RegionGroup.from_mapping(item)
        for item in (
            payload.get("regionGroups")
            or []
        )
        if isinstance(item, dict)
    )
    region_ids = [
        group.id
        for group in region_groups
    ]
    if len(region_ids) != len(
        set(region_ids)
    ):
        raise ValueError(
            "Duplicate region group ID"
        )

    batches = tuple(
        SourceBatch.from_mapping(
            item,
            default_failure_policy=(
                default_failure_policy
            ),
        )
        for item in (
            payload.get("batches")
            or []
        )
        if isinstance(item, dict)
    )
    batch_ids = [
        batch.id
        for batch in batches
    ]
    if len(batch_ids) != len(
        set(batch_ids)
    ):
        raise ValueError(
            "Duplicate source batch ID"
        )

    known_regions = set(region_ids)
    known_sources = set(
        known_source_ids
    )
    allow_future = bool(
        defaults.get(
            "allowFutureSourceIds",
            False,
        )
    )
    for batch in batches:
        unknown_regions = (
            set(batch.region_group_ids)
            - known_regions
        )
        if unknown_regions:
            raise ValueError(
                f"Unknown region group in "
                f"{batch.id}: "
                + ", ".join(
                    sorted(
                        unknown_regions
                    )
                )
            )
        if (
            len(batch.source_ids)
            > max_sources
        ):
            raise ValueError(
                f"Batch {batch.id} exceeds "
                "maxSourcesPerRun"
            )
        unknown_sources = (
            set(batch.source_ids)
            - known_sources
        )
        if (
            known_sources
            and unknown_sources
            and not allow_future
        ):
            raise ValueError(
                f"Unknown source in "
                f"{batch.id}: "
                + ", ".join(
                    sorted(
                        unknown_sources
                    )
                )
            )

    return SourceBatchRegistry(
        schema_version=int(
            payload.get(
                "schemaVersion"
            )
            or 1
        ),
        updated_at=str(
            payload.get("updatedAt")
            or ""
        ),
        region_groups=region_groups,
        batches=batches,
        max_sources_per_run=(
            max_sources
        ),
        default_failure_policy=(
            default_failure_policy
        ),
        allow_future_source_ids=(
            allow_future
        ),
        allow_organizer_expansion=bool(
            defaults.get(
                "allowOrganizerExpansion",
                False,
            )
        ),
    )


class SourceRunner(Protocol):
    def run_source(
        self,
        source: CollectorSource,
        *,
        allow_planned: bool = False,
    ) -> CollectorRunReport:
        ...


@dataclass
class SourceBatchRunReport:
    batch_id: str
    batch_name: str
    status: str
    failure_policy: str
    started_at: str
    finished_at: str = ""
    duration_ms: int = 0
    requested_source_ids: list[str] = (
        field(default_factory=list)
    )
    runnable_source_ids: list[str] = (
        field(default_factory=list)
    )
    skipped_sources: list[
        dict[str, str]
    ] = field(default_factory=list)
    source_reports: list[
        dict[str, Any]
    ] = field(default_factory=list)

    @property
    def successful_source_count(
        self,
    ) -> int:
        return sum(
            bool(
                report.get("success")
            )
            for report in self.source_reports
        )

    @property
    def failed_source_count(
        self,
    ) -> int:
        return sum(
            not bool(
                report.get("success")
            )
            for report in self.source_reports
        )

    @property
    def record_count(self) -> int:
        return sum(
            int(
                report.get(
                    "recordCount"
                )
                or 0
            )
            for report in self.source_reports
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": "collector-batch-run",
            "batchId": self.batch_id,
            "batchName": self.batch_name,
            "status": self.status,
            "success": self.status in {
                "success",
                "partial",
            },
            "failurePolicy": (
                self.failure_policy
            ),
            "startedAt": self.started_at,
            "finishedAt": (
                self.finished_at
            ),
            "durationMs": (
                self.duration_ms
            ),
            "requestedSourceIds": list(
                self.requested_source_ids
            ),
            "runnableSourceIds": list(
                self.runnable_source_ids
            ),
            "skippedSources": list(
                self.skipped_sources
            ),
            "sourceCount": len(
                self.source_reports
            ),
            "successfulSourceCount": (
                self.successful_source_count
            ),
            "failedSourceCount": (
                self.failed_source_count
            ),
            "recordCount": (
                self.record_count
            ),
            "sources": list(
                self.source_reports
            ),
        }


class CollectorBatchExecutor:
    def __init__(
        self,
        runner: SourceRunner,
    ) -> None:
        self.runner = runner

    def run(
        self,
        batch: SourceBatch,
        sources: Sequence[
            CollectorSource
        ],
        *,
        allow_disabled_batch: bool = False,
        allow_planned: bool = False,
    ) -> SourceBatchRunReport:
        started = datetime.now(
            timezone.utc
        )
        report = SourceBatchRunReport(
            batch_id=batch.id,
            batch_name=batch.name,
            status="running",
            failure_policy=(
                batch.failure_policy
            ),
            started_at=(
                started.isoformat()
            ),
            requested_source_ids=list(
                batch.source_ids
            ),
        )

        if (
            not batch.enabled
            and not allow_disabled_batch
        ):
            report.status = "skipped"
            report.finished_at = (
                datetime.now(
                    timezone.utc
                ).isoformat()
            )
            return report

        source_map = {
            source.id: source
            for source in sources
        }
        for source_id in batch.source_ids:
            source = source_map.get(
                source_id
            )
            if source is None:
                report.skipped_sources.append({
                    "sourceId": source_id,
                    "reason": (
                        "not_registered"
                    ),
                })
                continue
            if (
                not source.enabled
                and not allow_planned
            ):
                report.skipped_sources.append({
                    "sourceId": source_id,
                    "reason": (
                        "disabled_or_planned"
                    ),
                })
                continue

            report.runnable_source_ids.append(
                source.id
            )
            try:
                source_report = (
                    self.runner.run_source(
                        source,
                        allow_planned=(
                            allow_planned
                        ),
                    )
                )
                report.source_reports.append(
                    source_report.to_dict()
                )
            except Exception as exc:
                report.source_reports.append({
                    "sourceId": source.id,
                    "status": "failed",
                    "success": False,
                    "recordCount": 0,
                    "records": [],
                    "warnings": [],
                    "errors": [
                        f"{type(exc).__name__}: "
                        f"{exc}"
                    ],
                    "fetchedPages": 0,
                    "durationMs": 0,
                    "metrics": {},
                })

        if not report.source_reports:
            report.status = "skipped"
        elif report.failed_source_count == 0:
            report.status = "success"
        elif (
            report.successful_source_count
            > 0
            and batch.failure_policy
            == "isolate_source"
        ):
            report.status = "partial"
        else:
            report.status = "failed"

        finished = datetime.now(
            timezone.utc
        )
        report.finished_at = (
            finished.isoformat()
        )
        report.duration_ms = round(
            (
                finished
                - started
            ).total_seconds()
            * 1000
        )
        return report
