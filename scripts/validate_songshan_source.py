#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
from urllib.parse import urlparse


DETAIL_RE = re.compile(r"^/exhibition/activity/[0-9a-f-]{20,}/?$", re.IGNORECASE)
EXCLUDE_RE = re.compile(
    r"(?:松山文創園區\s*[-–—]?\s*\d{1,2}\s*月展演攻略|課程|講座|論壇|工作坊|營隊|夏令營|培力|研習|講習|徵件|招募)",
    re.IGNORECASE,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding='utf-8'))
    records = [item for item in payload.get('records') or [] if isinstance(item, dict)]
    ids = [str(item.get('source_event_id') or item.get('sourceEventId') or '') for item in records]
    raws = [dict(item.get('raw') or {}) for item in records]
    metrics = payload.get('metrics') or {}

    invalid_urls = []
    missing_dates = []
    invalid_venues = []
    image_overflow = []
    exclusion_leaks = []
    detail_fetch_missing = []
    rejected_external_urls = []
    blank_titles = []
    for record, raw in zip(records, raws):
        event_id = str(record.get('source_event_id') or record.get('sourceEventId') or '')
        title = str(record.get('title') or raw.get('title') or '').strip()
        detail_url = str(record.get('detail_url') or record.get('detailUrl') or raw.get('detailUrl') or '')
        if not title or title == 'Image':
            blank_titles.append(event_id)
        parsed = urlparse(detail_url)
        if parsed.netloc.lower().removeprefix('www.') != 'songshanculturalpark.org' or not DETAIL_RE.match(parsed.path):
            invalid_urls.append(event_id)
        if not raw.get('startDate') or not raw.get('endDate'):
            missing_dates.append(event_id)
        if raw.get('venueName') != '松山文創園區':
            invalid_venues.append(event_id)
        if len(raw.get('imageUrls') or []) > 4:
            image_overflow.append(event_id)
        if EXCLUDE_RE.search(title) and raw.get('editorialStatus') != 'exclude_review':
            exclusion_leaks.append(event_id)
        if raw.get('detailFetched') is not True:
            detail_fetch_missing.append(event_id)
        if any('google.com' in str(url).lower() or 'facebook.com' in str(url).lower() for url in raw.get('externalUrls') or []):
            rejected_external_urls.append(event_id)

    duplicate_ids = sorted(item for item, count in Counter(ids).items() if item and count > 1)
    gates = {
        'sourceIdMatches': payload.get('sourceId') == 'songshan-cultural-park',
        'sourceRunSuccess': payload.get('success') is True,
        'recordsPresent': len(records) > 0,
        'sourceIdsUnique': bool(ids) and '' not in ids and not duplicate_ids,
        'fullDetailsRequested': int(metrics.get('detailRequestedCount') or 0) == len(records),
        'fullDetailsSucceeded': int(metrics.get('detailSuccessCount') or 0) == len(records),
        'noDetailFailures': int(metrics.get('detailFailureCount') or 0) == 0,
        'titlesValid': not blank_titles,
        'detailUrlsValid': not invalid_urls,
        'datesPresent': not missing_dates,
        'venueCanonical': not invalid_venues,
        'imageLimitRespected': not image_overflow,
        'excludedContentFlagged': not exclusion_leaks,
        'allRecordsDetailFetched': not detail_fetch_missing,
        'externalUrlsClean': not rejected_external_urls,
    }
    failed = [key for key, value in gates.items() if not value]
    report = {
        'mode': 'songshan-source-quality',
        'passed': not failed,
        'sourceId': payload.get('sourceId'),
        'recordCount': len(records),
        'gates': gates,
        'failedGateIds': failed,
        'details': {
            'duplicateIds': duplicate_ids,
            'blankTitleIds': blank_titles,
            'invalidUrlIds': invalid_urls,
            'missingDateIds': missing_dates,
            'invalidVenueIds': invalid_venues,
            'imageOverflowIds': image_overflow,
            'exclusionLeakIds': exclusion_leaks,
            'detailFetchMissingIds': detail_fetch_missing,
            'rejectedExternalUrlIds': rejected_external_urls,
        },
    }
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['passed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
