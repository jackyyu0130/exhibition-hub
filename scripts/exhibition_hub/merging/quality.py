from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class QualityGate:
    id: str
    passed: bool
    actual: Any
    expected: Any
    severity: str = "error"
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _source_reference_counts(
    candidate: Mapping[str, Any],
    source_id: str,
) -> Counter[str]:
    counts: Counter[str] = Counter()
    for event in candidate.get("events") or []:
        if not isinstance(event, dict):
            continue
        for record in event.get("sourceRecords") or []:
            if not isinstance(record, dict):
                continue
            if str(record.get("sourceId") or "") != source_id:
                continue
            source_event_id = str(
                record.get("sourceEventId") or ""
            )
            if source_event_id:
                counts[source_event_id] += 1
    return counts


def _coverage_ratio(
    source_run: Mapping[str, Any],
    field_name: str,
) -> float:
    records = [
        item.get("raw") or {}
        for item in source_run.get("records") or []
        if isinstance(item, dict)
    ]
    if not records:
        return 0.0

    if field_name == "admissionKnown":
        count = sum(
            item.get("admission") in {"free", "paid"}
            for item in records
        )
    elif field_name == "venue":
        count = sum(
            bool(
                item.get("venueNames")
                or item.get("venueName")
            )
            for item in records
        )
    elif field_name == "image":
        count = sum(
            bool(
                item.get("imageUrl")
                or item.get("imageUrls")
            )
            for item in records
        )
    else:
        count = sum(
            bool(item.get(field_name))
            for item in records
        )
    return round(count / len(records), 4)


def evaluate_source_merge_candidate(
    *,
    base_payload: Mapping[str, Any],
    source_run: Mapping[str, Any],
    candidate: Mapping[str, Any],
    merge_report: Mapping[str, Any],
    review_queue: list[dict[str, Any]],
    source_id: str,
    require_full_details: bool = False,
    max_review: int = 0,
) -> dict[str, Any]:
    source_records = [
        item
        for item in source_run.get("records") or []
        if isinstance(item, dict)
    ]
    base_events = [
        item
        for item in base_payload.get("events") or []
        if isinstance(item, dict)
    ]
    candidate_events = [
        item
        for item in candidate.get("events") or []
        if isinstance(item, dict)
    ]
    decisions = [
        item
        for item in merge_report.get("decisions") or []
        if isinstance(item, dict)
    ]

    metrics = dict(source_run.get("metrics") or {})
    decision_counts = Counter(
        item.get("decision")
        for item in decisions
    )
    new_count = int(decision_counts.get("new_event", 0))
    expected_candidate_count = len(base_events) + new_count

    candidate_ids = [
        str(item.get("id") or "")
        for item in candidate_events
    ]
    source_event_ids = [
        str(
            item.get("source_event_id")
            or item.get("sourceEventId")
            or (item.get("raw") or {}).get("sourceEventId")
            or ""
        )
        for item in source_records
    ]
    source_reference_counts = _source_reference_counts(
        candidate,
        source_id,
    )

    missing_references = sorted(
        source_event_id
        for source_event_id in source_event_ids
        if source_reference_counts[source_event_id] == 0
    )
    duplicate_references = sorted(
        source_event_id
        for source_event_id in source_event_ids
        if source_reference_counts[source_event_id] > 1
    )

    full_detail_passed = (
        int(metrics.get("detailRequestedCount") or 0)
        == len(source_records)
        and int(metrics.get("detailSuccessCount") or 0)
        == len(source_records)
        and int(metrics.get("detailFailureCount") or 0)
        == 0
    )

    gates = [
        QualityGate(
            id="source_run_success",
            passed=bool(source_run.get("success")),
            actual=bool(source_run.get("success")),
            expected=True,
            message="Collector 必須成功完成。",
        ),
        QualityGate(
            id="source_id_matches",
            passed=str(source_run.get("sourceId") or "") == source_id,
            actual=str(source_run.get("sourceId") or ""),
            expected=source_id,
            message="來源 ID 必須與候選合併來源一致。",
        ),
        QualityGate(
            id="source_records_present",
            passed=len(source_records) > 0,
            actual=len(source_records),
            expected="> 0",
            message="來源至少必須取得一筆活動。",
        ),
        QualityGate(
            id="all_source_records_decided",
            passed=len(decisions) == len(source_records),
            actual=len(decisions),
            expected=len(source_records),
            message="每筆來源活動都必須有合併決策。",
        ),
        QualityGate(
            id="candidate_count_formula",
            passed=len(candidate_events) == expected_candidate_count,
            actual=len(candidate_events),
            expected=expected_candidate_count,
            message="候選總數必須等於既有活動加上 new_event。",
        ),
        QualityGate(
            id="candidate_ids_unique",
            passed=(
                bool(candidate_ids)
                and "" not in candidate_ids
                and len(candidate_ids) == len(set(candidate_ids))
            ),
            actual={
                "count": len(candidate_ids),
                "unique": len(set(candidate_ids)),
                "blank": candidate_ids.count(""),
            },
            expected={
                "countEqualsUnique": True,
                "blank": 0,
            },
            message="候選活動 ID 不可重複或空白。",
        ),
        QualityGate(
            id="source_references_complete",
            passed=not missing_references,
            actual=missing_references,
            expected=[],
            message="每筆來源活動必須出現在候選 sourceRecords。",
        ),
        QualityGate(
            id="source_references_unique",
            passed=not duplicate_references,
            actual=duplicate_references,
            expected=[],
            message="同一來源活動不可被加入兩個候選事件。",
        ),
        QualityGate(
            id="review_queue_within_limit",
            passed=len(review_queue) <= max_review,
            actual=len(review_queue),
            expected=f"<= {max_review}",
            message="人工審核佇列不可超過設定上限。",
        ),
        QualityGate(
            id="candidate_not_published",
            passed=(
                merge_report.get("published") is False
                and (
                    candidate.get("sourceMergeBuild") or {}
                ).get("published") is False
            ),
            actual={
                "report": merge_report.get("published"),
                "candidate": (
                    candidate.get("sourceMergeBuild") or {}
                ).get("published"),
            },
            expected={
                "report": False,
                "candidate": False,
            },
            message="5-E 仍只能建立候選，不可正式發布。",
        ),
    ]

    if require_full_details:
        gates.append(
            QualityGate(
                id="full_detail_coverage",
                passed=full_detail_passed,
                actual={
                    "recordCount": len(source_records),
                    "requested": metrics.get(
                        "detailRequestedCount"
                    ),
                    "success": metrics.get(
                        "detailSuccessCount"
                    ),
                    "failure": metrics.get(
                        "detailFailureCount"
                    ),
                },
                expected={
                    "requestedEqualsRecordCount": True,
                    "successEqualsRecordCount": True,
                    "failure": 0,
                },
                message="5-E 必須完成全部詳情頁，不可只抽樣。",
            )
        )

    coverage = {
        "image": _coverage_ratio(source_run, "image"),
        "organizer": _coverage_ratio(
            source_run,
            "organizer",
        ),
        "venue": _coverage_ratio(source_run, "venue"),
        "sourceCategory": _coverage_ratio(
            source_run,
            "sourceCategory",
        ),
        "admissionKnown": _coverage_ratio(
            source_run,
            "admissionKnown",
        ),
        "description": _coverage_ratio(
            source_run,
            "description",
        ),
    }
    coverage_thresholds = {
        "image": 0.75,
        "organizer": 0.65,
        "venue": 0.65,
        "sourceCategory": 0.9,
        "admissionKnown": 0.35,
        "description": 0.75,
    }
    coverage_warnings = [
        {
            "field": field_name,
            "actual": coverage[field_name],
            "threshold": threshold,
        }
        for field_name, threshold in coverage_thresholds.items()
        if coverage[field_name] < threshold
    ]

    error_gates = [
        gate
        for gate in gates
        if gate.severity == "error"
    ]
    passed = all(gate.passed for gate in error_gates)

    return {
        "mode": "source-merge-quality-validation",
        "sourceId": source_id,
        "passed": passed,
        "published": False,
        "counts": {
            "baseEventCount": len(base_events),
            "sourceRecordCount": len(source_records),
            "candidateEventCount": len(candidate_events),
            "decisionCount": len(decisions),
            "decisionCounts": dict(decision_counts),
            "reviewQueueCount": len(review_queue),
        },
        "detailMetrics": metrics,
        "coverage": coverage,
        "coverageThresholds": coverage_thresholds,
        "coverageWarnings": coverage_warnings,
        "gates": [
            gate.to_dict()
            for gate in gates
        ],
        "failedGateIds": [
            gate.id
            for gate in error_gates
            if not gate.passed
        ],
    }
