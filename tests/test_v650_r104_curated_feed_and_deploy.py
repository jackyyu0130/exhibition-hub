import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'assets' / 'app.js').read_text(encoding='utf-8')
CSS = (ROOT / 'assets' / 'styles.css').read_text(encoding='utf-8')
INDEX = (ROOT / 'index.html').read_text(encoding='utf-8')
BUILD = (ROOT / 'scripts' / 'build_pages_site.py').read_text(encoding='utf-8')
WORKFLOW = (ROOT / '.github' / 'workflows' / 'update-exhibitions.yml').read_text(encoding='utf-8')
CURATED = json.loads((ROOT / 'data' / 'exhibitions.curated.json').read_text(encoding='utf-8'))
MATRIX = json.loads((ROOT / 'data' / 'taiwan_venue_matrix.json').read_text(encoding='utf-8'))
NORTH = json.loads((ROOT / 'data' / 'venue_matrix_north.json').read_text(encoding='utf-8'))


class R104CuratedFeedAndDeployTests(unittest.TestCase):
    def test_cache_version_and_curated_source_are_active(self):
        self.assertIn('assets/styles.css?v=6.5.0-r11.0.2', INDEX)
        self.assertIn('assets/app.js?v=6.5.0-r11.0.2', INDEX)
        curated_pos = APP.index("data/exhibitions.curated.json")
        enriched_pos = APP.index("data/exhibitions.enriched.json")
        self.assertLess(curated_pos, enriched_pos)
        self.assertIn("dataset.eventData = curated ? 'curated'", APP)

    def test_curated_feed_removes_low_quality_public_rows(self):
        events = CURATED['events']
        self.assertGreaterEqual(len(events), 100)
        self.assertLess(len(events), CURATED['curation']['sourceEventCount'])
        self.assertTrue(all(event.get('sourceUrl') for event in events))
        self.assertTrue(all(event.get('image') or event.get('images') for event in events))
        public_text = '\n'.join(
            ' '.join(str(event.get(key) or '') for key in ('title', 'locationName', 'venueGroup', 'unit'))
            for event in events
        )
        self.assertNotRegex(public_text, r'圖書館|分館|圖書室|閱覽室')
        titles = {event['title'] for event in events}
        self.assertFalse(any('斷層槽溝保存館常設展' in title for title in titles))
        self.assertNotIn('見城館常設展', titles)
        self.assertFalse(any('桃捷 × Dtto' in title for title in titles))

    def test_anime_category_requires_title_signal(self):
        for event in CURATED['events']:
            if event.get('category') != '動漫':
                continue
            self.assertRegex(
                event.get('title', ''),
                r'動漫|動畫展|漫畫|電玩|遊戲展|anime|公仔|角色展|模型展|寶可夢|吉伊卡哇|CHIIKAWA|櫻桃小丸子|蠟筆小新|哆啦A夢|三麗鷗|迪士尼|IP(?:展|祭)',
            )
        by_title = {event['title']: event for event in CURATED['events']}
        if 'w-inds. LIVE TOUR 2026 “GOLDEN SINGLES”' in by_title:
            self.assertEqual(by_title['w-inds. LIVE TOUR 2026 “GOLDEN SINGLES”']['category'], '演唱會')
        if '絢麗系列 — 角野隼斗世界巡演音樂會' in by_title:
            self.assertEqual(by_title['絢麗系列 — 角野隼斗世界巡演音樂會']['category'], '音樂')

    def test_venue_matrix_is_deployed_and_live_house_complete(self):
        required = (
            'data/exhibitions.curated.json',
            'data/taiwan_venue_matrix.json',
            'data/venue_matrix_manifest.json',
            'data/venue_matrix_north.json',
            'data/venue_matrix_west.json',
            'data/venue_matrix_south.json',
            'data/venue_matrix_east.json',
        )
        for path in required:
            self.assertIn(f'"{path}"', BUILD)
        records = {venue['name']: venue for venue in MATRIX['venues']}
        for name in ('NUZONE', '藝富文創展演館／杰克音樂', 'WESTAR', 'Legacy Taipei', 'THE WALL Live House'):
            self.assertIn(name, records)
            self.assertEqual(records[name]['venueType'], 'live_house')
            self.assertTrue(records[name]['confirmed'])
        self.assertIn('富邦美術館', records)
        self.assertIn('富邦美術館1樓', records['富邦美術館']['aliases'])
        self.assertEqual(MATRIX['stats']['totalVenues'], 236)
        self.assertEqual(NORTH['venueCount'], 123)

    def test_generic_hall_and_district_labels_cannot_become_venues(self):
        self.assertIn('Public venue filters are registry-led', APP)
        self.assertIn('if (!registry?.confirmed) return;', APP)
        self.assertIn('展覽廳|展覽室|展廳|多功能室|會議室|大廳|中庭', APP)
        self.assertIn('eventCanonicalVenueRecords(event)', APP)

    def test_performance_path_uses_lightweight_feed_and_animation(self):
        self.assertIn('listingRenderLimit: 48', APP)
        self.assertIn('Math.min(18, state.events.length)', APP)
        self.assertIn("requestAnimationFrame", APP)
        self.assertIn("is-r105-moving", APP)
        self.assertIn("moveSlot(first, 1, 0)", APP)
        self.assertNotIn("cache:'no-store'", APP)
        self.assertIn("cache:'no-cache'", APP)
        self.assertIn('transition: none !important', CSS)
        self.assertIn('content-visibility: auto', CSS)
        self.assertIn('Build curated public feed', WORKFLOW)
        self.assertIn('data/update-reports/curated-feed-report.json', WORKFLOW)


if __name__ == '__main__':
    unittest.main()
