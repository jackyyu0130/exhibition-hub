import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SongshanSourceValidatorTests(unittest.TestCase):
    def run_validator(self, payload):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.json'
            output = Path(directory) / 'quality.json'
            source.write_text(json.dumps(payload), encoding='utf-8')
            result = subprocess.run([
                sys.executable,
                str(ROOT / 'scripts' / 'validate_songshan_source.py'),
                '--input', str(source),
                '--output', str(output),
            ], text=True, capture_output=True)
            return result.returncode, json.loads(output.read_text(encoding='utf-8'))

    def payload(self):
        return {
            'sourceId': 'songshan-cultural-park',
            'success': True,
            'records': [{
                'source_id': 'songshan-cultural-park',
                'source_event_id': '1f6f6688-f92b-4599-98e2-9f2db15c21c1',
                'title': '擁抱五月天時光迴廊主題展',
                'detail_url': 'https://www.songshanculturalpark.org/exhibition/activity/1f6f6688-f92b-4599-98e2-9f2db15c21c1',
                'raw': {
                    'startDate': '2026-07-01',
                    'endDate': '2026-07-13',
                    'venueName': '松山文創園區',
                    'imageUrls': ['https://example.com/a.jpg'],
                    'editorialStatus': 'candidate',
                    'detailFetched': True,
                    'externalUrls': [],
                },
            }],
            'metrics': {
                'detailRequestedCount': 1,
                'detailSuccessCount': 1,
                'detailFailureCount': 0,
            },
        }

    def test_valid_source_passes(self):
        code, report = self.run_validator(self.payload())
        self.assertEqual(code, 0)
        self.assertTrue(report['passed'])

    def test_google_calendar_link_is_rejected(self):
        payload = self.payload()
        payload['records'][0]['raw']['externalUrls'] = [
            'https://calendar.google.com/calendar/render?action=TEMPLATE'
        ]
        code, report = self.run_validator(payload)
        self.assertEqual(code, 2)
        self.assertIn('externalUrlsClean', report['failedGateIds'])

    def test_course_must_be_excluded(self):
        payload = self.payload()
        payload['records'][0]['title'] = '兒童設計夏令營課程'
        code, report = self.run_validator(payload)
        self.assertEqual(code, 2)
        self.assertIn('excludedContentFlagged', report['failedGateIds'])


if __name__ == '__main__':
    unittest.main()
