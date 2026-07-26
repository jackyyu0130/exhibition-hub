import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from exhibition_hub.registry import (  # noqa: E402
    load_source_registry,
    load_venue_registry,
    resolve_venue,
    source_registry_summary,
    validate_all_registries,
)


class RegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_registry = load_source_registry()
        cls.venue_registry = load_venue_registry()

    def test_registries_are_valid(self):
        self.assertEqual(
            validate_all_registries(
                self.source_registry,
                self.venue_registry,
            ),
            [],
        )

    def test_nationwide_coverage_has_22_regions(self):
        summary = source_registry_summary(
            self.source_registry
        )
        self.assertEqual(
            summary["coverageRegionCount"],
            22,
        )

    def test_common_venue_aliases_resolve(self):
        expected = {
            "松菸": "songshan-cultural-park",
            "北流": "taipei-music-center",
            "大巨蛋": "taipei-dome",
            "國美館": (
                "national-taiwan-museum-of-fine-arts"
            ),
            "駁二": "pier-2-art-center",
        }

        for alias, expected_id in expected.items():
            with self.subTest(alias=alias):
                venue = resolve_venue(
                    alias,
                    self.venue_registry,
                )
                self.assertIsNotNone(venue)
                self.assertEqual(
                    venue["id"],
                    expected_id,
                )

    def test_tai_and_taiwan_character_variants_resolve(self):
        venue = resolve_venue(
            "台北市立美術館",
            self.venue_registry,
        )
        self.assertIsNotNone(venue)
        self.assertEqual(
            venue["id"],
            "taipei-fine-arts-museum",
        )


if __name__ == "__main__":
    unittest.main()
