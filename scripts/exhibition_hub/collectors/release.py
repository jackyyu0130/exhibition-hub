from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


PUBLIC_DATA_FILES = (
    "data/exhibitions.json",
    "data/exhibitions.enriched.json",
    "data/exhibitions.curated.json",
)


def _read_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def public_data_snapshot(root: str | Path = ".") -> dict[str, str]:
    base = Path(root)
    return {
        relative: file_sha256(base / relative)
        for relative in PUBLIC_DATA_FILES
        if (base / relative).is_file()
    }


@dataclass(frozen=True)
class CollectorReleaseStage:
    id: str
    name: str
    mode: str
    enabled: bool
    publish_enabled: bool
    batch_id: str
    required_gates: tuple[str, ...]

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "CollectorReleaseStage":
        stage_id = str(value.get("id") or "").strip()
        name = str(value.get("name") or "").strip()
        mode = str(value.get("mode") or "").strip()
        batch_id = str(value.get("batchId") or "").strip()
        if not stage_id or not name or mode not in {"dry_run", "gated_publish"}:
            raise ValueError("Collector release stage requires id, name, and supported mode")
        if not batch_id:
            raise ValueError(f"Collector release stage requires batchId: {stage_id}")
        return cls(
            id=stage_id,
            name=name,
            mode=mode,
            enabled=bool(value.get("enabled", False)),
            publish_enabled=bool(value.get("publishEnabled", False)),
            batch_id=batch_id,
            required_gates=tuple(str(item) for item in value.get("requiredGates") or []),
        )


def load_release_stage(path: str | Path, stage_id: str) -> tuple[CollectorReleaseStage, dict[str, Any]]:
    payload = _read_json(path)
    stages = [CollectorReleaseStage.from_mapping(item) for item in payload.get("stages") or []]
    stage = next((item for item in stages if item.id == stage_id), None)
    if stage is None:
        raise ValueError(f"Unknown collector release stage: {stage_id}")
    return stage, payload


def _source_ids_for_batch(batch_payload: Mapping[str, Any], batch_id: str) -> list[str]:
    batch = next(
        (item for item in batch_payload.get("batches") or [] if item.get("id") == batch_id),
        None,
    )
    if not batch:
        raise ValueError(f"Release stage references unknown source batch: {batch_id}")
    return [str(item) for item in batch.get("sourceIds") or []]


def _assess_reports(paths: Iterable[str | Path]) -> dict[str, Any]:
    source_count = 0
    failed_source_count = 0
    record_count = 0
    reports: list[dict[str, Any]] = []
    for path in paths:
        payload = _read_json(path)
        sources = payload.get("sources") or []
        source_count += int(payload.get("sourceCount") or len(sources) or 0)
        failed_source_count += int(
            payload.get("failedSourceCount")
            or sum(1 for item in sources if item.get("status") == "failed")
            or 0
        )
        record_count += int(
            payload.get("recordCount")
            or payload.get("eventCount")
            or sum(int(item.get("recordCount") or 0) for item in sources)
            or 0
        )
        reports.append({
            "path": str(path),
            "status": str(payload.get("status") or "unknown"),
        })
    return {
        "reportCount": len(reports),
        "sourceCount": source_count,
        "failedSourceCount": failed_source_count,
        "recordCount": record_count,
        "reports": reports,
    }


def build_dry_run_report(
    *,
    stage_path: str | Path,
    stage_id: str,
    source_registry_path: str | Path,
    source_batches_path: str | Path,
    input_reports: Iterable[str | Path] = (),
    root: str | Path = ".",
) -> dict[str, Any]:
    stage, release_payload = load_release_stage(stage_path, stage_id)
    source_registry = _read_json(source_registry_path)
    source_batches = _read_json(source_batches_path)
    source_ids = _source_ids_for_batch(source_batches, stage.batch_id)
    registered = {str(item.get("id")): item for item in source_registry.get("sources") or []}
    missing = [source_id for source_id in source_ids if source_id not in registered]
    if missing:
        raise ValueError("Release batch references unregistered source(s): " + ", ".join(missing))

    assessment = _assess_reports(input_reports)
    gates = dict(release_payload.get("qualityGates") or {})
    max_failed = int(gates.get("maxFailedSources") or 0)
    min_records = int(gates.get("minimumCandidateRecords") or 0)
    gate_results = {
        "allSourcesRegistered": not missing,
        "failureThreshold": assessment["reportCount"] == 0 or assessment["failedSourceCount"] <= max_failed,
        "minimumCandidateRecords": assessment["reportCount"] == 0 or assessment["recordCount"] >= min_records,
        "publicDataUntouched": True,
    }

    # This component intentionally has no publication code. Stage 8 remains a
    # contract and gate foundation until publishEnabled is explicitly reviewed.
    return {
        "schemaVersion": 1,
        "release": "v6.5.0-r12-stable2",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "mode": "collector-dry-run",
        "stage": {
            "id": stage.id,
            "name": stage.name,
            "mode": stage.mode,
            "batchId": stage.batch_id,
            "enabled": stage.enabled,
        },
        "sourceIds": source_ids,
        "sourceCount": len(source_ids),
        "assessment": assessment,
        "qualityGates": gate_results,
        "publicDataBefore": public_data_snapshot(root),
        "publicDataAfter": public_data_snapshot(root),
        "publishRequested": False,
        "publishAllowed": False,
        "safety": {
            "writesPublicData": False,
            "commitsChanges": False,
            "pushesChanges": False,
            "stagePublishEnabled": stage.publish_enabled,
        },
    }
