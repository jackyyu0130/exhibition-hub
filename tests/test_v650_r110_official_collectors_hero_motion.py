import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
WORKFLOW = (ROOT / ".github" / "workflows" / "update-exhibitions.yml").read_text(encoding="utf-8")
REGISTRY = json.loads((ROOT / "data" / "source_registry.json").read_text(encoding="utf-8"))
OFFICIAL = (ROOT / "scripts" / "exhibition_hub" / "collectors" / "official_sites.py").read_text(encoding="utf-8")


class R110OfficialCollectorsHeroMotionTests(unittest.TestCase):
    def test_cache_version_is_r110(self):
        self.assertIn("assets/styles.css?v=6.5.0-r11.0.2", HTML)
        self.assertIn("assets/app.js?v=6.5.0-r11.0.2", HTML)

    def test_first_batch_sources_are_active(self):
        active = {
            item["id"]
            for item in REGISTRY["sources"]
            if item.get("status") == "active" and item.get("enabled")
        }
        self.assertTrue({
            "songshan-cultural-park",
            "taipei-music-center",
            "kaohsiung-music-center",
            "tainan-art-museum",
            "taipei-performing-arts-center",
            "pier-2",
        }.issubset(active))

    def test_collector_batch_is_failure_isolated(self):
        self.assertTrue((ROOT / "scripts" / "run_official_source_batch.py").is_file())
        self.assertIn("failureIsolation", (ROOT / "scripts" / "run_official_source_batch.py").read_text(encoding="utf-8"))
        self.assertIn("Collect and merge active official venue sources", WORKFLOW)
        self.assertIn("official-sources-preview.json", WORKFLOW)
        self.assertIn("official-source-batch.json", WORKFLOW)

    def test_official_collector_classes_exist(self):
        for name in (
            "TaipeiMusicCenterCollector",
            "KaohsiungMusicCenterCollector",
            "TainanArtMuseumCollector",
            "TaipeiPerformingArtsCenterCollector",
            "Pier2ArtCenterCollector",
        ):
            self.assertIn(f"class {name}", OFFICIAL)

    def test_desktop_and_mobile_ticket_selection(self):
        self.assertIn("is-ticket-active", APP)
        self.assertIn("activateHeroTicketInteraction", APP)
        self.assertIn("is-touch-preview", APP)
        marker = "Exhibition Hub V6.5.0-R11.0"
        self.assertIn(marker, CSS)
        block = CSS.split(marker, 1)[1]
        self.assertIn("scale(1.035)", block)
        self.assertIn("z-index: 80 !important", block)
        self.assertIn("hero-ticket-choice-ring", block)

    def test_home_motion_uses_transform_and_opacity_not_clip_path(self):
        block = CSS.split("Exhibition Hub V6.5.0-R11.0", 1)[1]
        self.assertIn("clip-path: none !important", block)
        self.assertIn("transition-duration: .48s, .56s", block)
        self.assertIn("Math.min(index, 5)", APP)
        self.assertNotIn("void home.offsetWidth", APP)


if __name__ == "__main__":
    unittest.main()
