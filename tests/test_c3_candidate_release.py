from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


from scripts.exhibition_hub.c3_review import apply_decisions, build_queue

ROOT = Path(__file__).resolve().parents[1]


class C3CandidateReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / "data/c3_source_catalog.json").read_text(encoding="utf-8"))
        cls.policy = json.loads((ROOT / "data/c3_release_policy.json").read_text(encoding="utf-8"))
        cls.index_html = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.app_js = (ROOT / "assets/app.js").read_text(encoding="utf-8")

    def test_source_catalog_has_all_four_user_groups_and_safe_defaults(self):
        sources = self.catalog["sources"]
        self.assertEqual(self.catalog["sourceCount"], 96)
        self.assertEqual(len(sources), 96)
        self.assertEqual({item["category"] for item in sources}, {"ticketing", "organizer", "livehouse", "festival"})
        self.assertTrue(all(item.get("requiresManualReview") is True for item in sources))
        self.assertTrue(all(item.get("autoPublishAllowed") is False for item in sources))
        self.assertTrue(all(item.get("verificationStatus") for item in sources))

    def test_release_policy_requires_review_pr_and_environment_approval(self):
        publication = self.policy["publication"]
        self.assertFalse(publication["directPushToMain"])
        self.assertTrue(publication["createPullRequestOnly"])
        self.assertEqual(publication["requiresExactConfirmation"], "PREPARE_C3_RELEASE_PR")
        self.assertTrue(publication["requiresEnvironmentApproval"])
        self.assertFalse(self.policy["socialRules"]["communityPostsCanPublishEvents"])
        self.assertTrue(self.policy["socialRules"]["requiresSecondaryEvidenceForCoreFields"])

    def test_candidate_workflow_is_manual_read_only_and_artifact_only(self):
        path = ROOT / ".github/workflows/c3-candidate-review.yml"
        text = path.read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^permissions:\s*\n\s+contents:\s*read\s*$")
        self.assertIn("workflow_dispatch:", text)
        self.assertNotIn("schedule:", text)
        self.assertIn("Resolve rotating discovery window", text)
        self.assertIn("group=\"all\"", text)
        self.assertIn("offset=$(( ((day - 1) % windows) * chunk ))", text)
        self.assertIn("Confirm public data is untouched", text)
        self.assertIn("actions/upload-artifact@v4", text)
        self.assertNotIn("git push", text)

    def test_release_workflow_creates_pr_and_never_pushes_main(self):
        path = ROOT / ".github/workflows/c3-release-pr.yml"
        text = path.read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^\s{4}environment:\s*c3-production\s*$")
        self.assertIn("PREPARE_C3_RELEASE_PR", text)
        self.assertIn("gh pr create --base main", text)
        self.assertIn('git push origin "$branch"', text)
        self.assertNotIn("git push origin main", text)
        self.assertNotIn("git checkout main", text)

    def test_queue_blocks_incomplete_and_social_only_candidates(self):
        catalog = {
            "sources": [
                {
                    "id": "official-source",
                    "name": "Official",
                    "category": "ticketing",
                    "discoveryMode": "ticketing_public_candidate",
                    "verificationStatus": "runtime_verified",
                },
                {
                    "id": "social-source",
                    "name": "Social",
                    "category": "organizer",
                    "discoveryMode": "official_social_manual",
                    "verificationStatus": "runtime_verified",
                },
            ]
        }
        rows = build_queue(
            [
                {"sourceId": "official-source", "title": "缺日期活動", "sourceUrl": "https://example.com/event"},
                {
                    "sourceId": "social-source",
                    "title": "社群活動",
                    "startDate": "2026-10-01",
                    "endDate": "2026-10-01",
                    "venueName": "場館",
                    "region": "臺北市",
                    "sourceUrl": "https://www.instagram.com/p/example/",
                },
            ],
            catalog,
            [],
            self.policy,
        )
        incomplete = next(row for row in rows if row["title"] == "缺日期活動")
        social = next(row for row in rows if row["title"] == "社群活動")
        self.assertIn("invalid_or_missing_dates", incomplete["blockingIssues"])
        self.assertFalse(incomplete["publishEligible"])
        self.assertIn("social_only_evidence", social["qualityFlags"])
        self.assertFalse(social["publishEligible"])

    def test_manual_decision_does_not_remove_blocking_issues(self):
        queue = [{"candidateId": "x", "qualityScore": 0.95, "blockingIssues": ["invalid_or_missing_dates"], "publishEligible": False}]
        reviewed = apply_decisions(queue, {"decisions": [{"candidateId": "x", "decision": "approved"}]})
        self.assertEqual(reviewed[0]["reviewStatus"], "approved")
        self.assertFalse(reviewed[0]["publishEligible"])
        self.assertEqual(reviewed[0]["blockingIssues"], ["invalid_or_missing_dates"])

    def test_home_social_section_is_immediately_after_hero(self):
        hero_end = self.index_html.index('</section>', self.index_html.index('class="hero" id="top"'))
        social = self.index_html.index('id="socialDiscussionsSection"')
        discovery = self.index_html.index('id="discover"')
        self.assertLess(hero_end, social)
        self.assertLess(social, discovery)
        self.assertIn("最近大家在聊", self.index_html)
        self.assertIn("循著今日心緒，遇見一場展覽", self.index_html)

    def test_discussion_index_and_detail_module_are_gated(self):
        self.assertIn('id="socialView"', self.index_html)
        self.assertIn("大家怎麼說", self.app_js)
        self.assertIn("socialNavigationEligible", self.app_js)
        self.assertIn("rows.length >= 6", self.app_js)
        self.assertIn(".size >= 3", self.app_js)
        self.assertIn("r12-stable2-c3", self.index_html)

    def test_empty_release_preview_does_not_change_event_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            queue = tmp_path / "queue.json"
            decisions = tmp_path / "decisions.json"
            base = tmp_path / "base.json"
            output = tmp_path / "preview.json"
            audit = tmp_path / "audit.json"
            queue.write_text(json.dumps({"candidates": []}), encoding="utf-8")
            decisions.write_text(json.dumps({"decisions": []}), encoding="utf-8")
            base.write_text(json.dumps({"events": [{"id": "existing", "title": "Existing"}]}), encoding="utf-8")
            subprocess.run(
                [
                    "python",
                    str(ROOT / "scripts/build_c3_publish_preview.py"),
                    "--queue", str(queue),
                    "--decisions", str(decisions),
                    "--base", str(base),
                    "--output", str(output),
                    "--audit", str(audit),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            preview = json.loads(output.read_text(encoding="utf-8"))
            report = json.loads(audit.read_text(encoding="utf-8"))
            self.assertEqual(len(preview["events"]), 1)
            self.assertEqual(report["addedCount"], 0)
            self.assertFalse(report["published"])


if __name__ == "__main__":
    unittest.main()
