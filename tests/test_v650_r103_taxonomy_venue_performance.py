import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'assets' / 'app.js').read_text(encoding='utf-8')
CSS = (ROOT / 'assets' / 'styles.css').read_text(encoding='utf-8')
MATRIX = json.loads((ROOT / 'data' / 'taiwan_venue_matrix.json').read_text(encoding='utf-8'))


class R103TaxonomyVenuePerformanceTests(unittest.TestCase):
    def test_music_and_concert_are_strictly_separated(self):
        self.assertIn("concert:'音樂'", APP)
        self.assertIn('function primaryCategoryFor', APP)
        self.assertIn("return '演唱會';", APP)
        self.assertIn("return '音樂';", APP)
        self.assertIn("FILM_CATEGORY_PATTERN.test(titleText)", APP)
        self.assertIn("MUSIC_THEATRE_PATTERN.test(titleText)", APP)
        self.assertIn("function eventCategories(event)", APP)
        self.assertIn("eventCategories(event).some(category => state.categories.has(category))", APP)

    def test_region_filter_uses_canonical_venue_regions(self):
        self.assertIn('function eventRegions(event)', APP)
        self.assertIn('eventRegions(event).includes(state.region)', APP)
        self.assertIn('const catalog = venueCatalog();', APP)
        self.assertIn("catalog.filter(item => item.region === region)", APP)

    def test_live_house_entries_exist_in_confirmed_matrix(self):
        records = {item['name']: item for item in MATRIX['venues']}
        self.assertEqual(records['NUZONE']['venueType'], 'live_house')
        self.assertEqual(records["杰克音樂 Jack's studio"]['venueType'], 'live_house')
        self.assertTrue(records['NUZONE']['confirmed'])
        self.assertTrue(records["杰克音樂 Jack's studio"]['confirmed'])

    def test_hero_uses_transform_only_final_override(self):
        marker = 'Exhibition Hub V6.5.0-R10.5'
        self.assertIn(marker, CSS)
        block = CSS.split(marker, 1)[1]
        self.assertIn('transition: none !important', block)
        self.assertIn('will-change: auto !important', block)
        self.assertIn('is-r105-moving', APP)
        self.assertIn('moveSlot(first, 1, 0)', APP)
        function = APP.split("function changeHeroPair(direction)", 1)[1].split("const HOME_STATUS_COPY", 1)[0]
        self.assertNotIn('stack.animate', function)
        self.assertIn('IntersectionObserver', APP)
        self.assertIn('state.heroPaused', APP)

    def test_long_listing_is_batched(self):
        self.assertIn('listingRenderLimit: 48', APP)
        self.assertIn('const visibleItems = items.slice(0, state.listingRenderLimit)', APP)
        self.assertIn("button.id = 'listingLoadMore'", APP)
        self.assertIn('content-visibility: auto', CSS)


if __name__ == '__main__':
    unittest.main()
