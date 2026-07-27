"""Validate nationwide source and venue registries."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from exhibition_hub.registry import (  # noqa: E402
    load_source_registry,
    load_venue_registry,
    source_registry_summary,
    validate_all_registries,
)


def main() -> int:
    source_registry = load_source_registry()
    venue_registry = load_venue_registry()
    errors = validate_all_registries(
        source_registry,
        venue_registry,
    )

    report = {
        "succeeded": not errors,
        "errors": errors,
        "sourceRegistry": source_registry_summary(
            source_registry
        ),
        "venueCount": len(
            venue_registry.get("venues", [])
        ),
    }

    print(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        )
    )

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
