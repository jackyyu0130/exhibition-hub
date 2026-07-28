import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from exhibition_hub.collectors import SongshanCulturalParkCollector, collector_registry


class SongshanRegistryTests(unittest.TestCase):
    def test_collector_is_registered_for_explicit_dry_run(self):
        registration = collector_registry.get('songshan-cultural-park')
        self.assertIsNotNone(registration)
        self.assertEqual(registration.collector_type, SongshanCulturalParkCollector)
        self.assertFalse(registration.enabled)

    def test_source_remains_planned_and_disabled(self):
        payload = json.loads((ROOT / 'data' / 'source_registry.json').read_text(encoding='utf-8'))
        source = next(item for item in payload['sources'] if item['id'] == 'songshan-cultural-park')
        self.assertEqual(source['parser'], 'songshan_list_detail')
        self.assertEqual(source['listingUrl'], 'https://www.songshanculturalpark.org/exhibition')
        self.assertEqual(source['status'], 'planned')
        self.assertFalse(source['enabled'])

    def test_north_batch_remains_disabled(self):
        payload = json.loads((ROOT / 'data' / 'source_batches.json').read_text(encoding='utf-8'))
        batch = next(item for item in payload['batches'] if item['id'] == 'cultural-parks-north')
        self.assertFalse(batch['enabled'])
        self.assertEqual(batch['sourceIds'], ['huashan-1914', 'songshan-cultural-park'])


if __name__ == '__main__':
    unittest.main()
