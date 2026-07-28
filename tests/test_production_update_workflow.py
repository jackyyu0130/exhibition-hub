from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "update-exhibitions.yml"


class ProductionUpdateWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_huashan_production_pipeline_is_present(self):
        for required in (
            "Build fresh enriched base",
            "Fetch current Huashan details",
            "Validate full Huashan candidate",
            "Finalize safe production data",
            "data/exhibitions.enriched.json",
        ):
            self.assertIn(required, self.text)

    def test_data_update_runs_on_schedule_manual_or_registry_activation(self):
        self.assertIn("Determine update mode", self.text)
        self.assertIn("data/source_registry.json", self.text)
        self.assertIn("steps.mode.outputs.run_update", self.text)

    def test_pages_upload_uses_minimal_site_directory(self):
        self.assertIn("python scripts/build_pages_site.py", self.text)
        self.assertIn("path: site", self.text)
        self.assertNotIn("path: .\n", self.text)

    def test_snapshot_and_failure_safe_artifact_are_present(self):
        self.assertIn("Snapshot current production data", self.text)
        self.assertIn("Upload production update audit", self.text)
        self.assertIn("if: always()", self.text)


if __name__ == "__main__":
    unittest.main()
