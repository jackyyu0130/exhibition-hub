from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Mapping

from .base import (
    CollectorRecord,
    CollectorRunReport,
    CollectorSource,
)


def collector_report_from_mapping(
    payload: Mapping[str, Any],
) -> CollectorRunReport:
    records: list[CollectorRecord] = []
    for item in payload.get("records") or []:
        if not isinstance(item, dict):
            continue
        records.append(
            CollectorRecord(
                source_id=str(
                    item.get("source_id")
                    or item.get("sourceId")
                    or payload.get("sourceId")
                    or ""
                ),
                source_event_id=str(
                    item.get("source_event_id")
                    or item.get("sourceEventId")
                    or ""
                ),
                title=str(
                    item.get("title")
                    or ""
                ),
                detail_url=str(
                    item.get("detail_url")
                    or item.get("detailUrl")
                    or ""
                ),
                raw=dict(
                    item.get("raw")
                    or {}
                ),
            )
        )

    return CollectorRunReport(
        source_id=str(
            payload.get("sourceId")
            or ""
        ),
        status=str(
            payload.get("status")
            or "failed"
        ),
        records=records,
        warnings=[
            str(item)
            for item in (
                payload.get("warnings")
                or []
            )
        ],
        errors=[
            str(item)
            for item in (
                payload.get("errors")
                or []
            )
        ],
        fetched_pages=int(
            payload.get("fetchedPages")
            or 0
        ),
        duration_ms=int(
            payload.get("durationMs")
            or 0
        ),
        metrics=dict(
            payload.get("metrics")
            or {}
        ),
        started_at=str(
            payload.get("startedAt")
            or ""
        ),
    )


class SubprocessCollectorRunner:
    def __init__(
        self,
        *,
        source_registry: str | Path,
        fetch_details: bool = False,
        detail_limit: int = 0,
        python_executable: str = (
            sys.executable
        ),
        script_path: str | Path = (
            "scripts/run_collectors.py"
        ),
    ) -> None:
        self.source_registry = str(
            source_registry
        )
        self.fetch_details = (
            fetch_details
        )
        self.detail_limit = max(
            0,
            int(detail_limit),
        )
        self.python_executable = str(
            python_executable
        )
        self.script_path = str(
            script_path
        )

    def run_source(
        self,
        source: CollectorSource,
        *,
        allow_planned: bool = False,
        timeout_seconds: float | None = None,
    ) -> CollectorRunReport:
        with tempfile.TemporaryDirectory(
            prefix=(
                "exhibition-hub-source-"
            )
        ) as directory:
            report_path = (
                Path(directory)
                / "source-report.json"
            )
            command = [
                self.python_executable,
                self.script_path,
                "--source",
                source.id,
                "--source-registry",
                self.source_registry,
                "--report-output",
                str(report_path),
            ]
            if allow_planned:
                command.append(
                    "--allow-planned"
                )
            if self.fetch_details:
                command.append(
                    "--fetch-details"
                )
                command.extend([
                    "--detail-limit",
                    str(
                        self.detail_limit
                    ),
                ])

            try:
                result = subprocess.run(
                    command,
                    text=True,
                    capture_output=True,
                    timeout=(
                        timeout_seconds
                        if timeout_seconds
                        else None
                    ),
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise TimeoutError(
                    f"Source {source.id} exceeded "
                    f"{timeout_seconds} seconds"
                ) from exc

            if report_path.exists():
                payload = json.loads(
                    report_path.read_text(
                        encoding="utf-8"
                    )
                )
                if (
                    result.returncode != 0
                    and not payload.get(
                        "errors"
                    )
                ):
                    payload.setdefault(
                        "errors",
                        [],
                    ).append(
                        result.stderr.strip()
                        or (
                            "Collector subprocess "
                            f"returned {result.returncode}"
                        )
                    )
                    payload["status"] = "failed"
                return (
                    collector_report_from_mapping(
                        payload
                    )
                )

            return CollectorRunReport(
                source_id=source.id,
                status="failed",
                errors=[
                    result.stderr.strip()
                    or result.stdout.strip()
                    or (
                        "Collector subprocess did "
                        "not create a report"
                    )
                ],
            )
