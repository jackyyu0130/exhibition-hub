from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "validate-develop.yml"


class ValidateDevelopWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_checked_in_images_are_sanitized_before_test_suite(self):
        sanitize_index = self.text.index(
            "Sanitize checked-in images before tests"
        )
        syntax_index = self.text.index("Check Python syntax")
        tests_index = self.text.index("Run automated tests")
        self.assertLess(sanitize_index, syntax_index)
        self.assertLess(sanitize_index, tests_index)
        self.assertIn(
            "python scripts/audit_event_images.py",
            self.text,
        )
        self.assertIn(
            "data/exhibitions.enriched.json",
            self.text,
        )


if __name__ == "__main__":
    unittest.main()
