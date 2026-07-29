#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from exhibition_hub.image_quality import audit_payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit and optionally remove generic/interface exhibition images."
    )
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--fix", action="store_true")
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("data/update-reports/image-quality-audit.json"),
    )
    return parser.parse_args()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    reports: list[dict[str, Any]] = []
    for path in args.files:
        cleaned, report = audit_payload(load(path), fix=args.fix)
        if args.fix:
            write(path, cleaned)
        reports.append({"path": path.as_posix(), **report})
    report_payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "mode": "fix" if args.fix else "audit",
        "reports": reports,
    }
    write(args.report, report_payload)
    for report in reports:
        print(
            f"{report['path']}: affected={report['affectedEventCount']}; "
            f"rejected={report['rejectedImageCount']}; "
            f"missing-after={report['missingImageCountAfter']}; "
            f"facebook-events={report['facebookReferenceEventCount']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
