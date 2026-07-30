from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import inspect
import json
from pathlib import Path
from time import perf_counter, sleep
from typing import Any, Callable, Mapping, Protocol, Sequence

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
        return cls(
            id=group_id,
            name=name,
            coverage_regions=tuple(
                str(item).strip()
                for item in (
                    value.get("coverageRegions")
                    or []
                )
                if str(item).strip()
            ),
        )


@dataclass(frozen=True)
class BatchExecutionPolicy:
    max_attempts_per_source: int = 3
    retry_backoff_seconds: float = 2.0
    source_timeout_seconds: float = 180.0
    slow_source_threshold_ms: int = 90000

    def __post_init__(self) -> None:
        if self.max_attempts_per_source <= 0:
            raise ValueError(
                "max_attempts_per_source must be positive"
            )
        if self.retry_backoff_seconds < 0:
            raise ValueError(
                "retry_backoff_seconds must not be negative"
            )
        if self.source_timeout_seconds <= 0:
            raise ValueError(
                "source_timeout_seconds must be positive"
            )
        if self.slow_source_threshold_ms <= 0:
            raise ValueError(
                "slow_source_threshold_ms must be positive"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "maxAttemptsPerSource": (
                self.max_attempts_per_source
            ),
            "retryBackoffSeconds": (
                self.retry_backoff_seconds
            ),
            "sourceTimeoutSeconds": (
                self.source_timeout_seconds
            ),
            "slowSourceThresholdMs": (
                self.slow_source_threshold_ms
            ),
        }


@dataclass(frozen=True)
class SourceBatch:
    id: str
    name: str
    enabled: bool
    region_group_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    organizer_ids: tuple[str, ...]
    failure_policy: str
    max_attempts_per_source: int | None = None
    retry_backoff_seconds: float | None = None
    source_timeout_seconds: float | None = None
    slow_source_threshold_ms: int | None = None

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
        if len(source_ids) != len(set(source_ids)):
            raise ValueError(
                f"Duplicate source ID in batch: {batch_id}"
            )

        failure_policy = str(
            value.get("failurePolicy")
            or default_failure_policy
        ).strip()
        if failure_policy not in ALLOWED_FAILURE_POLICIES:
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
                    value.get("regionGroupIds")
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
            max_attempts_per_source=(
                int(value["maxAttemptsPerSource"])
                if value.get("maxAttemptsPerSource") is not None
                else None
            ),
            retry_backoff_seconds=(
                float(value["retryBackoffSeconds"])
                if value.get("retryBackoffSeconds") is not None
                else None
            ),
            source_timeout_seconds=(
                float(value["sourceTimeoutSeconds"])
                if value.get("sourceTimeoutSeconds") is not None
                else None
            ),
            slow_source_threshold_ms=(
                int(value["slowSourceThresholdMs"])
                if value.get("slowSourceThresholdMs") is not None
                else None
            ),
        )

    def resolve_policy(
        self,
        defaults: BatchExecutionPolicy,
    ) -> BatchExecutionPolicy:
        return BatchExecutionPolicy(
            max_attempts_per_source=(
                self.max_attempts_per_source
                if self.max_attempts_per_source is not None
                else defaults.max_attempts_per_source
            ),
            retry_backoff_seconds=(
                self.retry_backoff_seconds
                if self.retry_backoff_seconds is not None
                else defaults.retry_backoff_seconds
            ),
            source_timeout_seconds=(
                self.source_timeout_seconds
                if self.source_timeout_seconds is not None
                else defaults.source_timeout_seconds
            ),
            slow_source_threshold_ms=(
                self.slow_source_threshold_ms
                if self.slow_source_threshold_ms is not None
                else defaults.slow_source_threshold_ms
            ),
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
    execution_policy: BatchExecutionPolicy

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

    def resolve_policy(
        self,
        batch: SourceBatch,
    ) -> BatchExecutionPolicy:
        return batch.resolve_policy(
            self.execution_policy
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": self.schema_version,
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
                    **(
                        {
                            "maxAttemptsPerSource":
                                batch.max_attempts_per_source
                        }
                        if batch.max_attempts_per_source is not None
                        else {}
                    ),
                    **(
                        {
                            "retryBackoffSeconds":
                                batch.retry_backoff_seconds
                        }
                        if batch.retry_backoff_seconds is not None
                        else {}
                    ),
                    **(
                        {
                            "sourceTimeoutSeconds":
                                batch.source_timeout_seconds
                        }
                        if batch.source_timeout_seconds is not None
                        else {}
                    ),
                    **(
                        {
                            "slowSourceThresholdMs":
                                batch.slow_source_threshold_ms
                        }
                        if batch.slow_source_threshold_ms is not None
                        else {}
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
                **self.execution_policy.to_dict(),
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
            "source_batches.json root must be an object"
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
        defaults.get("maxSourcesPerRun")
        or 10
    )
    if max_sources <= 0:
        raise ValueError(
            "maxSourcesPerRun must be positive"
        )

    execution_policy = BatchExecutionPolicy(
        max_attempts_per_source=int(
            defaults.get("maxAttemptsPerSource")
            or 3
        ),
        retry_backoff_seconds=float(
            defaults.get("retryBackoffSeconds")
            if defaults.get("retryBackoffSeconds")
            is not None
            else 2
        ),
        source_timeout_seconds=float(
            defaults.get("sourceTimeoutSeconds")
            or 180
        ),
        slow_source_threshold_ms=int(
            defaults.get("slowSourceThresholdMs")
            or 90000
        ),
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
    if len(region_ids) != len(set(region_ids)):
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
    if len(batch_ids) != len(set(batch_ids)):
        raise ValueError(
            "Duplicate source batch ID"
        )

    known_regions = set(region_ids)
    known_sources = set(known_source_ids)
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
                f"Unknown region group in {batch.id}: "
                + ", ".join(
                    sorted(unknown_regions)
                )
            )
        if len(batch.source_ids) > max_sources:
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
                f"Unknown source in {batch.id}: "
                + ", ".join(
                    sorted(unknown_sources)
                )
            )
        batch.resolve_policy(
            execution_policy
        )

    return SourceBatchRegistry(
        schema_version=int(
            payload.get("schemaVersion")
            or 1
        ),
        updated_at=str(
            payload.get("updatedAt")
            or ""
        ),
        region_groups=region_groups,
        batches=batches,
        max_sources_per_run=max_sources,
        default_failure_policy=(
            default_failure_policy
        ),
        allow_future_source_ids=allow_future,
        allow_organizer_expansion=bool(
            defaults.get(
                "allowOrganizerExpansion",
                False,
            )
        ),
        execution_policy=execution_policy,
    )


class SourceRunner(Protocol):
    def run_source(
        self,
        source: CollectorSource,
        *,
        allow_planned: bool = False,
        timeout_seconds: float | None = None,
    ) -> CollectorRunReport:
        ...


def _failed_source_payload(
    source_id: str,
    *,
    error: str,
    failure_type: str,
    duration_ms: int,
) -> dict[str, Any]:
    return {
        "sourceId": source_id,
        "status": "failed",
        "success": False,
        "recordCount": 0,
        "records": [],
        "warnings": [],
        "errors": [error],
        "fetchedPages": 0,
        "durationMs": duration_ms,
        "metrics": {},
        "failureType": failure_type,
    }


@dataclass
class SourceBatchRunReport:
    batch_id: str
    batch_name: str
    status: str
    failure_policy: str
    policy: BatchExecutionPolicy
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
    def recovered_source_count(
        self,
    ) -> int:
        return sum(
            bool(
                report.get(
                    "recoveredAfterRetry"
                )
            )
            for report in self.source_reports
        )

    @property
    def timed_out_source_count(
        self,
    ) -> int:
        return sum(
            bool(
                report.get("timedOut")
            )
            for report in self.source_reports
        )

    @property
    def retries_used(
        self,
    ) -> int:
        return sum(
            int(
                report.get("retryCount")
                or 0
            )
            for report in self.source_reports
        )

    @property
    def warning_count(
        self,
    ) -> int:
        return sum(
            len(
                report.get("warnings")
                or []
            )
            for report in self.source_reports
        )

    @property
    def record_count(self) -> int:
        return sum(
            int(
                report.get("recordCount")
                or 0
            )
            for report in self.source_reports
        )

    @property
    def slow_source_ids(
        self,
    ) -> list[str]:
        return [
            str(
                report.get("sourceId")
                or ""
            )
            for report in self.source_reports
            if int(
                report.get("totalDurationMs")
                or report.get("durationMs")
                or 0
            )
            >= self.policy.slow_source_threshold_ms
        ]

    @property
    def health_status(self) -> str:
        if not self.source_reports:
            return "skipped"
        if self.status == "failed":
            return "unhealthy"
        if (
            self.status == "partial"
            or self.recovered_source_count
            or self.timed_out_source_count
            or self.warning_count
            or self.slow_source_ids
        ):
            return "degraded"
        return "healthy"

    def health_report(
        self,
    ) -> dict[str, Any]:
        failed_ids = [
            str(
                item.get("sourceId")
                or ""
            )
            for item in self.source_reports
            if not item.get("success")
        ]
        timed_out_ids = [
            str(
                item.get("sourceId")
                or ""
            )
            for item in self.source_reports
            if item.get("timedOut")
        ]
        recovered_ids = [
            str(
                item.get("sourceId")
                or ""
            )
            for item in self.source_reports
            if item.get(
                "recoveredAfterRetry"
            )
        ]
        durations = [
            int(
                item.get("totalDurationMs")
                or item.get("durationMs")
                or 0
            )
            for item in self.source_reports
        ]
        return {
            "mode": (
                "collector-batch-health"
            ),
            "batchId": self.batch_id,
            "status": self.health_status,
            "operational": (
                self.failed_source_count == 0
            ),
            "failurePolicy": (
                self.failure_policy
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
            "recoveredSourceCount": (
                self.recovered_source_count
            ),
            "timedOutSourceCount": (
                self.timed_out_source_count
            ),
            "warningCount": (
                self.warning_count
            ),
            "retriesUsed": (
                self.retries_used
            ),
            "recordCount": (
                self.record_count
            ),
            "averageDurationMs": (
                round(
                    sum(durations)
                    / len(durations)
                )
                if durations
                else 0
            ),
            "maxDurationMs": (
                max(durations)
                if durations
                else 0
            ),
            "failedSourceIds": failed_ids,
            "timedOutSourceIds": (
                timed_out_ids
            ),
            "recoveredSourceIds": (
                recovered_ids
            ),
            "slowSourceIds": (
                self.slow_source_ids
            ),
            "policy": self.policy.to_dict(),
        }

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
            "policy": (
                self.policy.to_dict()
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
            "recoveredSourceCount": (
                self.recovered_source_count
            ),
            "timedOutSourceCount": (
                self.timed_out_source_count
            ),
            "retriesUsed": (
                self.retries_used
            ),
            "recordCount": (
                self.record_count
            ),
            "health": (
                self.health_report()
            ),
            "sources": list(
                self.source_reports
            ),
        }


class CollectorBatchExecutor:
    def __init__(
        self,
        runner: SourceRunner,
        *,
        sleeper: Callable[[float], None] = sleep,
    ) -> None:
        self.runner = runner
        self.sleeper = sleeper
        parameters = inspect.signature(
            runner.run_source
        ).parameters
        self.runner_accepts_timeout = (
            "timeout_seconds"
            in parameters
        )

    def _run_attempt(
        self,
        source: CollectorSource,
        *,
        allow_planned: bool,
        timeout_seconds: float,
    ) -> CollectorRunReport:
        if self.runner_accepts_timeout:
            return self.runner.run_source(
                source,
                allow_planned=(
                    allow_planned
                ),
                timeout_seconds=(
                    timeout_seconds
                ),
            )
        return self.runner.run_source(
            source,
            allow_planned=(
                allow_planned
            ),
        )

    def _run_source_with_retries(
        self,
        source: CollectorSource,
        *,
        allow_planned: bool,
        policy: BatchExecutionPolicy,
    ) -> dict[str, Any]:
        attempts: list[
            dict[str, Any]
        ] = []
        final_payload: dict[
            str, Any
        ] | None = None
        total_started = perf_counter()

        for attempt_number in range(
            1,
            policy.max_attempts_per_source
            + 1,
        ):
            attempt_started = perf_counter()
            failure_type = ""
            try:
                source_report = (
                    self._run_attempt(
                        source,
                        allow_planned=(
                            allow_planned
                        ),
                        timeout_seconds=(
                            policy.source_timeout_seconds
                        ),
                    )
                )
                payload = source_report.to_dict()
            except TimeoutError as exc:
                failure_type = "timeout"
                duration_ms = round(
                    (
                        perf_counter()
                        - attempt_started
                    )
                    * 1000
                )
                payload = (
                    _failed_source_payload(
                        source.id,
                        error=(
                            "TimeoutError: "
                            + str(exc)
                        ),
                        failure_type=(
                            failure_type
                        ),
                        duration_ms=(
                            duration_ms
                        ),
                    )
                )
            except Exception as exc:
                failure_type = "exception"
                duration_ms = round(
                    (
                        perf_counter()
                        - attempt_started
                    )
                    * 1000
                )
                payload = (
                    _failed_source_payload(
                        source.id,
                        error=(
                            f"{type(exc).__name__}: "
                            f"{exc}"
                        ),
                        failure_type=(
                            failure_type
                        ),
                        duration_ms=(
                            duration_ms
                        ),
                    )
                )

            attempt_duration_ms = round(
                (
                    perf_counter()
                    - attempt_started
                )
                * 1000
            )
            if not failure_type:
                failure_type = str(
                    payload.get(
                        "failureType"
                    )
                    or (
                        ""
                        if payload.get("success")
                        else "collector_failure"
                    )
                )

            attempts.append({
                "attempt": attempt_number,
                "success": bool(
                    payload.get("success")
                ),
                "status": str(
                    payload.get("status")
                    or ""
                ),
                "durationMs": (
                    attempt_duration_ms
                ),
                "failureType": (
                    failure_type
                ),
                "errorCount": len(
                    payload.get("errors")
                    or []
                ),
                "errors": list(
                    payload.get("errors")
                    or []
                ),
            })
            final_payload = payload
            if payload.get("success"):
                break
            if (
                attempt_number
                < policy.max_attempts_per_source
                and policy.retry_backoff_seconds
                > 0
            ):
                delay = (
                    policy.retry_backoff_seconds
                    * (
                        2
                        ** (
                            attempt_number
                            - 1
                        )
                    )
                )
                self.sleeper(delay)

        assert final_payload is not None
        total_duration_ms = round(
            (
                perf_counter()
                - total_started
            )
            * 1000
        )
        attempt_count = len(attempts)
        final_payload = dict(
            final_payload
        )
        final_payload.update({
            "attemptCount": attempt_count,
            "retryCount": max(
                0,
                attempt_count - 1,
            ),
            "recoveredAfterRetry": (
                bool(
                    final_payload.get(
                        "success"
                    )
                )
                and attempt_count > 1
            ),
            "timedOut": any(
                item.get("failureType")
                == "timeout"
                for item in attempts
            ),
            "timeoutSeconds": (
                policy.source_timeout_seconds
            ),
            "totalDurationMs": (
                total_duration_ms
            ),
            "attempts": attempts,
        })
        return final_payload

    def run(
        self,
        batch: SourceBatch,
        sources: Sequence[
            CollectorSource
        ],
        *,
        policy: BatchExecutionPolicy | None = None,
        allow_disabled_batch: bool = False,
        allow_planned: bool = False,
    ) -> SourceBatchRunReport:
        active_policy = (
            policy
            or BatchExecutionPolicy()
        )
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
            policy=active_policy,
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
                    "reason": "not_registered",
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
            report.source_reports.append(
                self._run_source_with_retries(
                    source,
                    allow_planned=(
                        allow_planned
                    ),
                    policy=active_policy,
                )
            )

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
