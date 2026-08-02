import json, unittest
from pathlib import Path
from scripts.exhibition_hub.collectors.venue_dry_run import extract_candidates
ROOT=Path(__file__).resolve().parents[1]
P=json.loads((ROOT/'data/collector_profiles.json').read_text(encoding='utf-8'))
class C2DryRunTests(unittest.TestCase):
 def test_groups_and_nonpublishing_contract(self):
  self.assertEqual(set(P['groups']),{'convention', 'live_house'})
  for rows in P['groups'].values():
   for p in rows:
    self.assertTrue(p['allowedDomains']); self.assertTrue(p['listingUrls'] or p.get('mode')=='verify_only')
 def test_fixture_extraction(self):
  profile={'sourceId':'fixture','allowedDomains':['example.org'],'listingUrls':['https://example.org/events'],'venueName':'Test','region':'臺北市','category':'展覽','detailUrlPatterns':['/event/'],'allowUndatedCandidates':False}
  html='<article><a href="/event/1"><img src="/a.jpg">2026/08/01 - 2026/08/03 測試展覽</a></article>'
  rows=extract_candidates(html,profile,'https://example.org/events')
  self.assertEqual(len(rows),1); self.assertEqual(rows[0]['startDate'],'2026-08-01'); self.assertFalse(rows[0]['candidateOnly'] is False)
 def test_workflow_never_writes_public_data(self):
  w=(ROOT/'.github/workflows/c2-venue-dry-run.yml').read_text(encoding='utf-8')
  self.assertIn('contents: read',w); self.assertIn('git diff --exit-code',w); self.assertNotIn('git push',w)
if __name__=='__main__': unittest.main()
