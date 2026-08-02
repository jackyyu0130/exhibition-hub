import json,unittest
from pathlib import Path
from scripts.exhibition_hub.social_discovery import build_queue
ROOT=Path(__file__).resolve().parents[1]
class S1Tests(unittest.TestCase):
 def test_manual_candidate_is_anonymized_and_pending(self):
  rows=build_queue([{'source':'threads','postUrl':'https://www.threads.net/@venue/post/abc','shortExcerpt':'測試展覽 即將開幕','authorDisplay':'real person'}],[{'id':'e1','title':'測試展覽'}])
  self.assertEqual(rows[0]['authorDisplay'],'公開來源（已匿名）'); self.assertEqual(rows[0]['reviewStatus'],'pending'); self.assertLessEqual(len(rows[0]['shortExcerpt']),240)
 def test_sources_obey_platform_safety(self):
  d=json.loads((ROOT/'data/social_sources.json').read_text(encoding='utf-8')); by={x['id']:x for x in d['sources']}
  self.assertFalse(by['threads']['enabled']); self.assertTrue(by['threads']['requiresOfficialAccessToken']); self.assertTrue(by['dcard']['requiresWrittenAuthorization']); self.assertTrue(by['ptt']['enabled'])
 def test_local_review_ui_and_whitelist_exist(self):
  self.assertTrue((ROOT/'tools/social-review.html').is_file()); self.assertTrue((ROOT/'data/social_whitelist.json').is_file())
  ui=(ROOT/'tools/social-review.html').read_text(encoding='utf-8'); self.assertIn('核准',ui); self.assertIn('匯出審核後 JSON',ui)
 def test_workflow_is_artifact_only(self):
  w=(ROOT/'.github/workflows/social-discovery-review.yml').read_text(encoding='utf-8'); self.assertIn('contents: read',w); self.assertNotIn('git push',w); self.assertIn('upload-artifact',w)
if __name__=='__main__': unittest.main()
