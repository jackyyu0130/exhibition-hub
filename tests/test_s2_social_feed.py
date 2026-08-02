import json,unittest
from pathlib import Path
from scripts.build_social_feed import build
ROOT=Path(__file__).resolve().parents[1]
class S2Tests(unittest.TestCase):
 def test_only_approved_high_confidence_valid_event_is_public(self):
  q=[{'candidateId':'a','source':'ptt','postUrl':'https://www.ptt.cc/bbs/Art/M.1.html','publishedAt':'2026-08-01T00:00:00+00:00','shortExcerpt':'測試','matchedEventId':'e1','matchConfidence':.8,'reviewStatus':'approved','engagementSnapshot':{}},{'candidateId':'b','source':'ptt','postUrl':'https://x.test/2','shortExcerpt':'no','matchedEventId':'e1','matchConfidence':.9,'reviewStatus':'pending'}]
  rows=build(q,[{'id':'e1'}]); self.assertEqual([x['candidateId'] for x in rows],['a'])
 def test_empty_feed_hides_section_and_pages_packages_json(self):
  h=(ROOT/'index.html').read_text(encoding='utf-8'); a=(ROOT/'assets/app.js').read_text(encoding='utf-8'); b=(ROOT/'scripts/build_pages_site.py').read_text(encoding='utf-8')
  self.assertIn('id="socialDiscussionsSection" hidden',h); self.assertIn("section.hidden=true",a); self.assertIn('data/social_discussions.json',b)
 def test_weights_are_exact(self):
  s=(ROOT/'scripts/build_social_feed.py').read_text(encoding='utf-8');
  for x in ('30*float','20*freshness','20*min','15*min','10*min','5*min'): self.assertIn(x,s)
if __name__=='__main__': unittest.main()
