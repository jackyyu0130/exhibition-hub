#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from exhibition_hub.c3_review import build_queue, event_list, load_json


def collect_artifact_candidates(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not root.exists():
        return rows
    for path in sorted(root.rglob('*.json')):
        if path.name == 'summary.json':
            continue
        try:
            payload = json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            continue
        candidates = payload.get('candidates', []) if isinstance(payload, dict) else []
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            row = dict(candidate)
            row['candidateOrigin'] = row.get('candidateOrigin') or 'c2'
            rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', default='collector-artifacts')
    parser.add_argument('--manual', default='data/c3_manual_candidates.json')
    parser.add_argument('--catalog', default='data/c3_source_catalog.json')
    parser.add_argument('--policy', default='data/c3_release_policy.json')
    parser.add_argument('--events', default='data/exhibitions.enriched.json')
    parser.add_argument('--output', default='c3-review-artifact/c3_candidate_queue.json')
    parser.add_argument('--report', default='c3-review-artifact/c3_candidate_report.json')
    args = parser.parse_args()

    raw = collect_artifact_candidates(Path(args.input_dir))
    manual_payload = load_json(args.manual, {'candidates': []}) or {'candidates': []}
    for item in manual_payload.get('candidates', []):
        if isinstance(item, dict):
            row = dict(item); row['candidateOrigin'] = row.get('candidateOrigin') or 'manual'; raw.append(row)
    catalog = load_json(args.catalog, {'sources': []})
    policy = load_json(args.policy, {})
    events = event_list(load_json(args.events, {'events': []}))
    rows = build_queue(raw, catalog, events, policy)
    payload = {
        'schemaVersion': 1,
        'generatedAt': datetime.now(timezone.utc).isoformat(),
        'publishAllowed': False,
        'reviewRequired': True,
        'candidateCount': len(rows),
        'candidates': rows,
    }
    report = {
        'schemaVersion': 1,
        'generatedAt': payload['generatedAt'],
        'rawCandidateCount': len(raw),
        'candidateCount': len(rows),
        'publishEligibleCount': sum(bool(row.get('publishEligible')) for row in rows),
        'manualReviewCount': sum(row.get('recommendedAction') == 'manual_review' for row in rows),
        'blockedCount': sum(bool(row.get('blockingIssues')) for row in rows),
        'sourceCounts': {},
        'publishAllowed': False,
    }
    for row in rows:
        sid = str(row.get('sourceId') or 'unknown')
        report['sourceCounts'][sid] = report['sourceCounts'].get(sid, 0) + 1
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    rep = Path(args.report); rep.parent.mkdir(parents=True, exist_ok=True)
    rep.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
