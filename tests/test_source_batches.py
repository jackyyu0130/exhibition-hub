import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SourceBatchRegistryTests(unittest.TestCase):
    def test_batches_are_extensible_by_region_and_organizer(self):
        payload = json.loads(
            (
                ROOT / "data" / "source_batches.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(payload["schemaVersion"], 2)
        self.assertEqual(
            len(payload["regionGroups"]),
            4,
        )
        source_ids = {
            item["id"]
            for item in json.loads(
                (
                    ROOT
                    / "data"
                    / "source_registry.json"
                ).read_text(encoding="utf-8")
            )["sources"]
        }
        for batch in payload["batches"]:
            self.assertIn("organizerIds", batch)
            self.assertIn(
                batch["failurePolicy"],
                {"isolate_source"},
            )
            self.assertTrue(
                set(batch["sourceIds"]).issubset(
                    source_ids
                )
            )

    def test_future_expansion_does_not_require_workflow_copy(self):
        payload = json.loads(
            (
                ROOT / "data" / "source_batches.json"
            ).read_text(encoding="utf-8")
        )
        self.assertTrue(
            payload["defaults"][
                "allowFutureSourceIds"
            ]
        )
        self.assertTrue(
            payload["defaults"][
                "allowOrganizerExpansion"
            ]
        )

    def test_active_official_venue_batch_is_enabled(self):
        payload = json.loads(
            (
                ROOT / "data" / "source_batches.json"
            ).read_text(encoding="utf-8")
        )
        batch = next(
            item
            for item in payload["batches"]
            if item["id"]
            == "active-official-venues"
        )
        self.assertTrue(batch["enabled"])
        self.assertEqual(
            batch["sourceIds"],
            ["huashan-1914"],
        )


if __name__ == "__main__":
    unittest.main()
