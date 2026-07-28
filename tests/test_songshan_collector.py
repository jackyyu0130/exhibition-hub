import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from exhibition_hub.collectors.songshan import SongshanCulturalParkCollector


LISTING_HTML = '''
<html><body>
<a href="/exhibition/activity/1f6f6688-f92b-4599-98e2-9f2db15c21c1">
<img src="/media/mayday.jpg" alt="擁抱五月天時光迴廊主題展">
<span>2026-07-01 - 2026-07-13</span>
<h3>擁抱五月天時光迴廊主題展</h3><p>看更多</p>
</a>
<a href="/exhibition/activity/1f6f6688-f92b-4599-98e2-9f2db15c21c1">
<span>2026-07-01 - 2026-07-13</span><h3>擁抱五月天時光迴廊主題展</h3>
</a>
<a href="/exhibition/activity/4a0b13cc-bd6b-4d63-ad90-c29cfd2a07e2">
<span>2026-06-19 - 2026-09-28</span><h3>伊藤潤二展「誘惑」</h3>
</a>
</body></html>
'''

DETAIL_HTML = '''
<html><head>
<meta property="og:title" content="擁抱五月天時光迴廊主題展 - 松山文創園區">
<meta property="og:image" content="https://www.songshanculturalpark.org/media/mayday-main.jpg">
<link rel="canonical" href="https://www.songshanculturalpark.org/exhibition/activity/1f6f6688-f92b-4599-98e2-9f2db15c21c1">
</head><body>
<div class="featured"><span>2025-01-01 - 2025-01-31</span><img src="/media/unrelated.jpg"><a href="https://tickets.example.com/unrelated">售票活動</a></div>
<h1>擁抱五月天時光迴廊主題展</h1>
<div>日期</div><div>2026-07-01 - 2026-07-13</div>
<div>地點</div><div>松山文創園區 台灣設計館 02 展間</div>
<p>人生無限時間線，交織你我故事象限。</p>
<p>活動時間｜10：00－21：20</p>
<p>活動地點｜松山文創園區 台灣設計館 02 展間</p>
<p>主辦單位｜相信音樂國際股份有限公司</p>
<p>免費入場</p>
<img src="/media/mayday-1.jpg"><img src="/assets/logo.svg">
<a href="https://calendar.google.com/calendar/render?action=TEMPLATE">加入行事曆</a>
<a href="https://tickets.example.com/mayday">購票資訊</a>
<div>園區資訊</div>
</body></html>
'''


class SongshanCollectorTests(unittest.TestCase):
    def test_listing_deduplicates_featured_and_grid_cards(self):
        events, pages = SongshanCulturalParkCollector.parse_listing(LISTING_HTML)
        self.assertEqual(len(events), 2)
        self.assertEqual(pages, [])
        self.assertEqual(events[0]['title'], '擁抱五月天時光迴廊主題展')
        self.assertEqual(events[0]['startDate'], '2026-07-01')
        self.assertEqual(events[0]['endDate'], '2026-07-13')

    def test_detail_extracts_official_fields(self):
        result = SongshanCulturalParkCollector.parse_detail(
            DETAIL_HTML,
            detail_url='https://www.songshanculturalpark.org/exhibition/activity/1f6f6688-f92b-4599-98e2-9f2db15c21c1',
            listing={'title': '擁抱五月天時光迴廊主題展'},
        )
        self.assertEqual(result['title'], '擁抱五月天時光迴廊主題展')
        self.assertEqual(result['startDate'], '2026-07-01')
        self.assertEqual(result['endDate'], '2026-07-13')
        self.assertEqual(result['startTime'], '10:00')
        self.assertEqual(result['endTime'], '21:20')
        self.assertEqual(result['venueName'], '松山文創園區')
        self.assertIn('台灣設計館 02 展間', result['venueNames'][0])
        self.assertEqual(result['organizer'], '相信音樂國際股份有限公司')
        self.assertEqual(result['admission'], 'free')
        self.assertEqual(len(result['imageUrls']), 2)
        self.assertNotIn('unrelated.jpg', ' '.join(result['imageUrls']))
        self.assertNotIn('logo.svg', ' '.join(result['imageUrls']))
        self.assertTrue(result['detailFetched'])
        self.assertFalse(any('google.com' in url for url in result['externalUrls']))

    def test_mixed_paid_and_free_ticket_text_is_paid(self):
        html = DETAIL_HTML.replace(
            '<p>免費入場</p>',
            '<p>展覽票價｜100元 / 80元 (團體票) / 免費 (優待票)</p>',
        )
        result = SongshanCulturalParkCollector.parse_detail(
            html,
            detail_url='https://www.songshanculturalpark.org/exhibition/activity/0235803d-3df7-4ca6-899c-4c2f275bff46',
            listing={'title': 'Spotlight 波蘭兒童插畫的狂歡舞台'},
        )
        self.assertEqual(result['admission'], 'paid')
        self.assertIn('100元', result['priceText'])

    def test_monthly_guide_and_courses_are_excluded(self):
        for title in ('松山文創園區- 7月展演攻略', '115 年品牌星躍實驗室〖培力課程〗', '兒童設計夏令營'):
            result = SongshanCulturalParkCollector.parse_detail(
                DETAIL_HTML.replace('擁抱五月天時光迴廊主題展', title),
                detail_url='https://www.songshanculturalpark.org/exhibition/activity/1f6f6688-f92b-4599-98e2-9f2db15c21c1',
                listing={'title': title},
            )
            self.assertEqual(result['editorialStatus'], 'exclude_review')

    def test_pop_up_title_gets_popup_hint(self):
        result = SongshanCulturalParkCollector.parse_detail(
            DETAIL_HTML.replace('擁抱五月天時光迴廊主題展', 'NishimuraYuji shop 台北松菸快閃店'),
            detail_url='https://www.songshanculturalpark.org/exhibition/activity/1f6f6688-f92b-4599-98e2-9f2db15c21c1',
        )
        self.assertEqual(result['contentTypeHint'], '快閃店')


if __name__ == '__main__':
    unittest.main()
