import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_pages_site import BUILD_MANIFEST, REQUIRED_FILES, build_pages_site  # noqa: E402
from exhibition_hub.collectors.release import build_dry_run_report  # noqa: E402
from exhibition_hub.venues import (  # noqa: E402
    normalize_event_venue_contract,
    validate_event_venue_contract,
)


HTML = (ROOT / "index.html").read_text(encoding="utf-8")
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")


class R120IntegratedUxSourcesSocialTests(unittest.TestCase):
    def test_release_uses_stable2_marker_everywhere(self):
        self.assertIn("assets/styles.css?v=6.5.0-r12-stable2", HTML)
        self.assertIn("assets/app.js?v=6.5.0-r12-stable2", HTML)
        manifest = json.loads((ROOT / "MANIFEST_V6.5.0-R12.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["releaseMarker"], "v6.5.0-r12-stable2")
        stale = "r12-" + "stable1"
        for directory in (ROOT / "assets", ROOT / "data", ROOT / "scripts"):
            for path in directory.rglob("*"):
                if path.is_file() and path.suffix in {".js", ".css", ".json", ".py", ".yml", ".md"}:
                    self.assertNotIn(stale, path.read_text(encoding="utf-8", errors="ignore"), str(path))

    def test_hero_interaction_functions_are_real_definitions(self):
        self.assertIn("function clearHeroTicketInteraction", APP)
        self.assertIn("function activateHeroTicketInteraction", APP)
        self.assertLess(APP.index("function clearHeroTicketInteraction"), APP.index("function changeHeroPair"))
        self.assertIn("ticket.setAttribute('aria-expanded', 'true')", APP)

    def test_first_mobile_tap_navigates_without_preview_gate(self):
        self.assertIn("assets/app.js?v=6.5.0-r14-single-tap1", HTML)
        self.assertNotIn("state.mobilePreviewTicket !== ticketKey", APP)
        self.assertNotIn("activateHeroTicketInteraction(tappedSlide, {touch:true})", APP)
        self.assertIn("const internalLink = event.target.closest('a[href]')", APP)
        self.assertIn("navigateTo(url.href)", APP)

    def test_mobile_swipe_has_pointer_capture_and_touch_fallback(self):
        self.assertIn("setPointerCapture", APP)
        self.assertIn("releasePointerCapture", APP)
        self.assertIn("addEventListener('touchstart'", APP)
        self.assertIn("addEventListener('touchend'", APP)
        self.assertIn("changeHeroPair(deltaX < 0 ? 1 : -1)", APP)

    def test_card_price_display_uses_a_consistent_activity_page_label(self):
        self.assertIn("function compactPriceLabel", APP)
        self.assertIn("return '票價請見活動頁面'", APP)
        self.assertNotIn('title="${escapeHtml(event.price)}"', APP)
        self.assertIn("text-overflow: ellipsis", CSS)

    def test_integrated_motion_is_capped_and_reduced_motion_safe(self):
        self.assertIn("Exhibition Hub V6.5.0-R12 STABLE2", CSS)
        self.assertIn("min(calc(var(--motion-index, 0) * 24ms), 168ms)", CSS)
        self.assertIn("r12-view-enter", CSS)
        self.assertIn("prefers-reduced-motion: reduce", CSS)
        self.assertIn("venueDrawerTimer", APP)

    def test_stage_7_and_8_are_safe_by_default(self):
        stages = json.loads((ROOT / "data/collector_release_stages.json").read_text(encoding="utf-8"))
        stage7 = next(item for item in stages["stages"] if item["id"] == "stage-7-daily-dry-run")
        stage8 = next(item for item in stages["stages"] if item["id"] == "stage-8-gated-publish-foundation")
        self.assertTrue(stage7["enabled"])
        self.assertFalse(stage7["publishEnabled"])
        self.assertFalse(stage8["enabled"])
        self.assertFalse(stage8["publishEnabled"])

    def test_dry_run_never_allows_publication_or_changes_public_hashes(self):
        report = build_dry_run_report(
            stage_path=ROOT / "data/collector_release_stages.json",
            stage_id="stage-7-daily-dry-run",
            source_registry_path=ROOT / "data/source_registry.json",
            source_batches_path=ROOT / "data/source_batches.json",
            root=ROOT,
        )
        self.assertFalse(report["publishAllowed"])
        self.assertFalse(report["safety"]["writesPublicData"])
        self.assertEqual(report["publicDataBefore"], report["publicDataAfter"])

    def test_social_discovery_is_discovery_only_and_facebook_is_blocked(self):
        policy = json.loads((ROOT / "data/social_discovery_policy.json").read_text(encoding="utf-8"))
        self.assertEqual(policy["publicationPolicy"], "discovery_only")
        self.assertFalse(policy["facebookImportAllowed"])
        self.assertIn("official_venue_page", policy["requiredVerification"])
        self.assertIn("officialUrl", policy["canonicalFieldsForbidden"])

    def test_pages_builder_is_atomic_and_emits_hash_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            output = Path(directory) / "site"
            (root / "assets").mkdir(parents=True)
            (root / "data").mkdir(parents=True)
            for relative in REQUIRED_FILES:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                if relative.endswith(".json"):
                    path.write_text("{}\n", encoding="utf-8")
                else:
                    path.write_text("ok\n", encoding="utf-8")
            (root / "assets/app.js").write_text("ok\n", encoding="utf-8")
            build_pages_site(root, output)
            manifest = json.loads((output / BUILD_MANIFEST).read_text(encoding="utf-8"))
            self.assertEqual(manifest["release"], "v6.5.0-r14-local-weekly-favicon")
            self.assertGreater(manifest["fileCount"], 1)
            self.assertTrue(all(len(item["sha256"]) == 64 for item in manifest["files"]))

    def test_pages_builder_rejects_source_directory_output(self):
        with self.assertRaises(ValueError):
            build_pages_site(ROOT, ROOT / "data" / "site")

    def test_main_venue_and_subspace_contract_migrates_legacy_shape(self):
        normalized = normalize_event_venue_contract({
            "venueName": "臺北表演藝術中心",
            "venueNames": ["大劇院", "藍盒子"],
            "venueId": "tpac",
        })
        self.assertEqual(normalized["venueNames"], ["臺北表演藝術中心"])
        self.assertEqual(normalized["subVenueNames"], ["大劇院", "藍盒子"])
        self.assertEqual(normalized["parentVenueId"], "tpac")
        self.assertEqual(validate_event_venue_contract(normalized), [])

    def test_multi_parent_venue_contract_keeps_top_level_venues(self):
        normalized = normalize_event_venue_contract({
            "venueName": "主場館 A",
            "venueNames": ["主場館 A", "主場館 B"],
            "subVenueNames": ["二樓展間"],
        })
        self.assertEqual(normalized["venueNames"], ["主場館 A", "主場館 B"])
        self.assertEqual(normalized["subVenueNames"], ["二樓展間"])
        self.assertEqual(validate_event_venue_contract(normalized), [])

    def test_public_feed_preserves_subspace_contract_fields(self):
        curation = (ROOT / "scripts/exhibition_hub/curation.py").read_text(encoding="utf-8")
        for field in ("parentVenueName", "parentVenueId", "subVenueName", "subVenueNames"):
            self.assertIn(f'"{field}"', curation)


if __name__ == "__main__":
    unittest.main()
