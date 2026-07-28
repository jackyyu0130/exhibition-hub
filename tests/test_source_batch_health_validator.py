import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SourceBatchHealthValidatorTests(
    unittest.TestCase
):
    def run_validator(
        self,
        payload,
        *extra,
    ):
        with tempfile.TemporaryDirectory() as directory:
            source = (
                Path(directory)
                / "health.json"
            )
            output = (
                Path(directory)
                / "validation.json"
            )
            source.write_text(
                json.dumps(payload),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(
                        ROOT
                        / "scripts"
                        / "validate_source_batch_health.py"
                    ),
                    "--input",
                    str(source),
                    "--output",
                    str(output),
                    *extra,
                ],
                text=True,
                capture_output=True,
            )
            report = json.loads(
                output.read_text(
                    encoding="utf-8"
                )
            )
            return result.returncode, report

    def test_healthy_batch_passes(self):
        code, report = self.run_validator({
            "mode": (
                "collector-batch-health"
            ),
            "batchId": "batch",
            "status": "healthy",
            "sourceCount": 1,
            "failedSourceCount": 0,
            "timedOutSourceCount": 0,
            "recordCount": 10,
        }, "--require-records")
        self.assertEqual(code, 0)
        self.assertTrue(report["passed"])

    def test_failed_source_is_rejected(self):
        code, report = self.run_validator({
            "mode": (
                "collector-batch-health"
            ),
            "batchId": "batch",
            "status": "degraded",
            "sourceCount": 2,
            "failedSourceCount": 1,
            "timedOutSourceCount": 0,
            "recordCount": 10,
        })
        self.assertEqual(code, 2)
        self.assertIn(
            "failedSourcesWithinLimit",
            report["failedGateIds"],
        )


if __name__ == "__main__":
    unittest.main()
