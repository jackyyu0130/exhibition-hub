from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from build_curated_feed import reconcile_public_categories
from exhibition_hub.curation import public_categories


APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
CURATED = json.loads((ROOT / "data" / "exhibitions.curated.json").read_text(encoding="utf-8"))
AUDIT = json.loads(
    (ROOT / "data" / "update-reports" / "category-semantic-audit-r17.json")
    .read_text(encoding="utf-8")
)


class R170SemanticTaxonomyTests(unittest.TestCase):
    def test_anime_popup_beats_the_film_title_inside_the_campaign_name(self) -> None:
        categories = public_categories({
            "title": "「劇場版 吉伊卡哇 人魚島的秘密」華山快閃店",
            "description": "舞台設計、藝術西街、科技公司",
            "contentType": "popup",
            "contentTypes": ["popup", "pop_culture"],
        })
        self.assertEqual(categories, ["快閃店", "動漫"])

    def test_anime_music_and_anime_film_keep_useful_hybrid_categories(self) -> None:
        music = public_categories({
            "title": "2026風動室內樂團《無限》ACG電玩動漫音樂會",
            "contentType": "performance",
            "contentTypes": ["performance", "pop_culture"],
        })
        film = public_categories({
            "title": "8月高雄市電影館｜劇場版 吉伊卡哇 人魚島的秘密",
            "contentType": "performance",
            "contentTypes": ["performance", "pop_culture"],
        })
        self.assertEqual(music, ["音樂", "動漫"])
        self.assertEqual(film, ["電影", "動漫"])

    def test_taiwan_does_not_trigger_the_ai_technology_rule(self) -> None:
        categories = public_categories({
            "title": "《管樂•Taiwan•金曲》",
            "description": "臺灣土地的音樂旅程",
            "contentType": "performance",
            "contentTypes": ["performance"],
        })
        self.assertEqual(categories, ["音樂"])

    def test_credits_and_sponsor_words_cannot_create_public_categories(self) -> None:
        categories = public_categories({
            "title": "別照鏡子",
            "description": "舞台設計、舞台美術、科技股份有限公司贊助",
            "category": "科技",
            "categories": ["科技", "設計", "美術"],
            "contentType": "performance",
            "contentTypes": ["performance"],
        })
        self.assertEqual(categories, ["表演"])

    def test_music_story_exhibition_is_not_overridden_by_description_credits(self) -> None:
        categories = public_categories({
            "title": "2026【唱 我們的歌 流行音樂故事展】",
            "description": "數位科技、展場設計、美術協力",
            "category": "科技",
            "categories": ["科技", "設計", "美術"],
            "contentType": "art_exhibition",
            "contentTypes": ["art_exhibition"],
        })
        self.assertEqual(categories, ["音樂"])

    def test_legitimate_technology_title_still_works(self) -> None:
        self.assertEqual(
            public_categories({
                "title": "AI機器人科技特展",
                "contentType": "exhibition",
                "contentTypes": ["exhibition"],
            }),
            ["科技"],
        )

    def test_official_popup_category_requires_popup_evidence_in_description(self) -> None:
        categories = public_categories({
            "title": "PEANUTS夏日海灘祭",
            "description": "史努比夏日限定快閃店，設有拍貼機與周邊商品。",
            "category": "快閃店",
            "categories": ["快閃店"],
            "contentType": "exhibition",
            "contentTypes": ["exhibition"],
        })
        self.assertEqual(categories, ["快閃店", "動漫"])

    def test_festival_stage_works_use_performance_or_dance(self) -> None:
        play = public_categories({
            "title": "2026臺北藝術節：創作社劇團《孃孃狂言》",
            "contentType": "festival",
            "contentTypes": ["festival"],
        })
        dance = public_categories({
            "title": "布拉瑞揚舞團《我・我們》第一部曲-2026苗北藝術節",
            "contentType": "festival",
            "contentTypes": ["festival"],
        })
        self.assertEqual(play, ["表演"])
        self.assertEqual(dance, ["舞蹈"])

    def test_final_reconciliation_rewrites_all_semantic_categories(self) -> None:
        payload, report = reconcile_public_categories({
            "events": [{
                "title": "別照鏡子",
                "description": "舞台設計、舞台美術、科技股份有限公司贊助",
                "category": "科技",
                "categories": ["科技", "設計", "美術"],
                "contentType": "performance",
                "contentTypes": ["performance"],
            }]
        })
        self.assertEqual(payload["events"][0]["category"], "表演")
        self.assertEqual(payload["events"][0]["categories"], ["表演"])
        self.assertEqual(report["semanticCategoryCorrections"], 1)

    def test_browser_uses_the_same_title_led_contract(self) -> None:
        self.assertIn("劇場(?!版)", APP)
        self.assertIn("AI(?![A-Za-z])", APP)
        self.assertIn("function titleSecondaryCategories(title = '')", APP)
        self.assertIn("types.has('popup') || POPUP_CATEGORY_PATTERN.test(titleText)", APP)
        self.assertIn("types.has('festival')", APP)
        self.assertNotIn("NATURAL_CATEGORY_PATTERN.test(supportingText)", APP)
        self.assertNotIn("TECHNOLOGY_CATEGORY_PATTERN.test(supportingText)", APP)
        self.assertIn('assets/app.js?v=6.5.0-r17.1', HTML)

    def test_current_public_feed_is_idempotently_reclassified(self) -> None:
        events = CURATED["events"]
        self.assertEqual(len(events), 693)
        for event in events:
            self.assertEqual(event["categories"], public_categories(event), event["title"])
            self.assertEqual(event["category"], event["categories"][0])
            self.assertLessEqual(len(event["categories"]), 3)

    def test_audit_and_public_stats_use_corrected_category_membership(self) -> None:
        self.assertEqual(AUDIT["eventCount"], 693)
        self.assertGreater(AUDIT["correctedCategoryArrays"], 500)
        membership = AUDIT["afterMembershipCounts"]
        self.assertGreaterEqual(membership["動漫"], 10)
        self.assertLess(membership["科技"], 10)
        self.assertEqual(CURATED["stats"]["categoryCounts"], membership)
        self.assertEqual(CURATED["stats"]["taxonomyVersion"], "6.5.0-r17")


if __name__ == "__main__":
    unittest.main()
