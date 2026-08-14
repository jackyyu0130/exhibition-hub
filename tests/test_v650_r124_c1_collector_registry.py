import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCES=json.loads((ROOT/'data/source_registry.json').read_text(encoding='utf-8'))
BATCHES=json.loads((ROOT/'data/source_batches.json').read_text(encoding='utf-8'))
STAGES=json.loads((ROOT/'data/collector_release_stages.json').read_text(encoding='utf-8'))
VENUES=json.loads((ROOT/'data/collector_venues.json').read_text(encoding='utf-8'))
WORKFLOW=(ROOT/'.github/workflows/collector-dry-run.yml').read_text(encoding='utf-8')
PRODUCTION=(ROOT/'.github/workflows/update-exhibitions.yml').read_text(encoding='utf-8')

C1_IDS={
 'twtc-hall-1','twtc-hall-3','tainex-hall-1','tainex-hall-2',
 'legacy-taipei','legacy-max','the-wall-live-house','nuzone','clapper-studio','pipe-live-music','westar',
 'national-theater-concert-hall','national-taichung-theater',
 'taipei-fine-arts-museum','fubon-art-museum','moca-taipei','national-palace-museum',
 'national-museum-natural-science','national-taiwan-museum','chimei-museum','juming-museum',
}

class C1CollectorRegistryTests(unittest.TestCase):
    def test_exactly_21_c1_sources_are_registered_and_only_hall_1_is_activated(self):
        by_id={x['id']:x for x in SOURCES['sources']}
        self.assertTrue(C1_IDS.issubset(by_id))
        self.assertEqual(len(C1_IDS),21)
        for source_id in C1_IDS - {'twtc-hall-1'}:
            source=by_id[source_id]
            self.assertFalse(source['enabled'])
            self.assertFalse(source['publicationPolicy']['publishEnabled'])
            self.assertFalse(source['publicationPolicy']['writePublicData'])
            self.assertEqual(source['networkPolicy']['failurePolicy'],'isolate_source')
            self.assertTrue(source['allowedDomains'])
            self.assertLessEqual(source['networkPolicy']['maxAttempts'],2)
            self.assertGreaterEqual(source['networkPolicy']['minDelaySeconds'],2)
        hall_1=by_id['twtc-hall-1']
        self.assertTrue(hall_1['enabled'])
        self.assertEqual(hall_1['status'],'active')
        self.assertTrue(hall_1['publicationPolicy']['publishEnabled'])
        self.assertTrue(hall_1['publicationPolicy']['writePublicData'])
        self.assertEqual(hall_1['networkPolicy']['failurePolicy'],'isolate_source')

    def test_hall_3_is_verify_only_and_juming_is_present(self):
        by_id={x['id']:x for x in SOURCES['sources']}
        self.assertEqual(by_id['twtc-hall-3']['status'],'retired')
        self.assertEqual(by_id['twtc-hall-3']['auditMode'],'verify_only')
        self.assertEqual(by_id['juming-museum']['status'],'planned')
        self.assertIn('juming.org.tw',by_id['juming-museum']['allowedDomains'])

    def test_collector_venue_targets_do_not_replace_public_venue_registry(self):
        self.assertEqual(VENUES['venueCount'],21)
        self.assertEqual({x['id'] for x in VENUES['venues']},C1_IDS)
        self.assertIn('不由前台讀取',VENUES['description'])

    def test_four_groups_and_combined_audit_batch_are_disabled(self):
        by_id={x['id']:x for x in BATCHES['batches']}
        group_ids=['c1-convention-venues-audit','c1-live-houses-audit','c1-performing-arts-audit','c1-museums-audit']
        union=set()
        for batch_id in group_ids:
            self.assertFalse(by_id[batch_id]['enabled'])
            self.assertEqual(by_id[batch_id]['failurePolicy'],'isolate_source')
            union.update(by_id[batch_id]['sourceIds'])
        self.assertEqual(union,C1_IDS)
        self.assertEqual(set(by_id['c1-planned-venue-registry-audit']['sourceIds']),C1_IDS)

    def test_daily_workflow_builds_registry_only_report(self):
        self.assertIn('stage-7-c1-venue-registry-audit',WORKFLOW)
        stage=next(x for x in STAGES['stages'] if x['id']=='stage-7-c1-venue-registry-audit')
        self.assertFalse(stage['publishEnabled'])
        self.assertEqual(stage['batchId'],'c1-planned-venue-registry-audit')

    def test_planned_only_registry_change_is_deploy_only(self):
        self.assertIn('check_source_registry_activation.py',PRODUCTION)
        self.assertIn('source-registry-planned-only',PRODUCTION)

if __name__=='__main__': unittest.main()
