import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from exhibition_hub.collectors import (  # noqa: E402
    CollectorSource,
    SubprocessCollectorRunner,
)


def source() -> CollectorSource:
    return CollectorSource.from_mapping({
        "id": "test-source",
        "name": "Test source",
        "status": "active",
        "enabled": True,
        "parser": "test",
        "officialUrl": (
            "https://example.com"
        ),
        "listingUrl": (
            "https://example.com/list"
        ),
        "trustLevel": "official",
        "refreshHours": 12,
    })


class BatchSubprocessRuntimeTests(
    unittest.TestCase
):
    def test_subprocess_report_is_deserialized(self):
        with tempfile.TemporaryDirectory() as directory:
            script = (
                Path(directory)
                / "fake_collector.py"
            )
            script.write_text(
                textwrap.dedent(
                    """
                    import argparse
                    import json
                    from pathlib import Path

                    parser = argparse.ArgumentParser()
                    parser.add_argument("--report-output")
                    parser.add_argument("--source")
                    parser.add_argument("--source-registry")
                    args, _ = parser.parse_known_args()
                    payload = {
                        "sourceId": args.source,
                        "status": "success",
                        "success": True,
                        "recordCount": 0,
                        "records": [],
                        "warnings": [],
                        "errors": [],
                        "fetchedPages": 2,
                        "durationMs": 15,
                        "metrics": {"ok": True},
                    }
                    Path(args.report_output).write_text(
                        json.dumps(payload),
                        encoding="utf-8",
                    )
                    """
                ),
                encoding="utf-8",
            )
            result = (
                SubprocessCollectorRunner(
                    source_registry=(
                        "data/source_registry.json"
                    ),
                    script_path=script,
                ).run_source(
                    source(),
                    timeout_seconds=15,
                )
            )
            self.assertTrue(
                result.success
            )
            self.assertEqual(
                result.fetched_pages,
                2,
            )
            self.assertEqual(
                result.metrics["ok"],
                True,
            )

    def test_subprocess_timeout_is_raised(self):
        with tempfile.TemporaryDirectory() as directory:
            script = (
                Path(directory)
                / "slow_collector.py"
            )
            script.write_text(
                "import time\ntime.sleep(2)\n",
                encoding="utf-8",
            )
            runner = (
                SubprocessCollectorRunner(
                    source_registry=(
                        "data/source_registry.json"
                    ),
                    script_path=script,
                )
            )
            with self.assertRaises(
                TimeoutError
            ):
                runner.run_source(
                    source(),
                    timeout_seconds=0.05,
                )


if __name__ == "__main__":
    unittest.main()
