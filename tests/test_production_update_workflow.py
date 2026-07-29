from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "update-exhibitions.yml"


class ProductionUpdateWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_full_tests_run_before_data_mutation(self):
        sanitize_index = self.text.index(
            "Sanitize checked-in images before tests"
        )
        tests_index = self.text.index(
            "Run project tests before production data update"
        )
        scraper_index = self.text.index(
            "Fetch and normalize Culture Ministry data"
        )
        self.assertLess(sanitize_index, tests_index)
        self.assertLess(tests_index, scraper_index)

    def test_checked_in_images_are_sanitized_before_tests(self):
        self.assertIn(
            "python scripts/audit_event_images.py",
            self.text,
        )
        self.assertIn(
            "/tmp/pretest-image-quality-audit.json",
            self.text,
        )

    def test_post_update_validation_is_count_independent(self):
        self.assertIn(
            "Validate dynamic published production data",
            self.text,
        )
        self.assertIn(
            "scripts/validate_published_data.py",
            self.text,
        )
        self.assertNotIn(
            "Validate frontend, scraper rules, and published data",
            self.text,
        )

    def test_recovery_workflow_change_triggers_data_update(self):
        self.assertIn(
            "production-pipeline-recovery",
            self.text,
        )
        self.assertIn(
            ".github/workflows/update-exhibitions",
            self.text,
        )

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
