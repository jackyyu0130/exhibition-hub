#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from typing import Iterable


REQUIRED_FILES = (
    "index.html",
    ".nojekyll",
    "favicon.ico",
    "favicon.svg",
    "favicon-48.png",
    "favicon-96.png",
    "favicon-192.png",
    "favicon-512.png",
    "apple-touch-icon.png",
    "logo-512.png",
    "site.webmanifest",
    "data/exhibitions.curated.json",
    "data/exhibitions.enriched.json",
    "data/exhibitions.json",
    "data/social_discussions.json",
    "data/venues.json",
    "data/northern_venue_matrix.json",
    "data/taiwan_venue_matrix.json",
    "data/venue_matrix_manifest.json",
    "data/venue_matrix_north.json",
    "data/venue_matrix_west.json",
    "data/venue_matrix_south.json",
    "data/venue_matrix_east.json",
)
OPTIONAL_FILES = ("CNAME",)
REQUIRED_DIRECTORIES = ("assets",)
BUILD_MANIFEST = "pages-build-manifest.json"
PUBLIC_RELEASE = "v6.5.0-r18.2"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build an atomic, validated GitHub Pages upload directory."
    )
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default="site")
    return parser.parse_args()


def _assert_safe_output(root: Path, output: Path) -> None:
    if output == root:
        raise ValueError("Output directory must not replace the repository root.")
    if output in root.parents:
        raise ValueError("Output directory must not be an ancestor of the repository root.")
    protected = [root / "assets", root / "data", root / "scripts", root / "tests", root / ".github"]
    if any(output == item or item in output.parents for item in protected):
        raise ValueError("Output directory must not replace or be nested inside a source directory.")


def _validate_required_sources(root: Path) -> None:
    missing = [relative for relative in REQUIRED_FILES if not (root / relative).is_file()]
    missing += [relative + "/" for relative in REQUIRED_DIRECTORIES if not (root / relative).is_dir()]
    if missing:
        raise FileNotFoundError("Missing required site file(s): " + ", ".join(missing))

    for relative in REQUIRED_FILES:
        if not relative.endswith(".json"):
            continue
        try:
            json.loads((root / relative).read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"Invalid required JSON file: {relative}: {exc}") from exc



def _iter_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_file():
            yield path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_manifest(staging: Path, copied: list[str]) -> None:
    files = []
    for path in _iter_files(staging):
        if path.name == BUILD_MANIFEST:
            continue
        files.append({
            "path": path.relative_to(staging).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        })
    payload = {
        "schemaVersion": 1,
        "release": PUBLIC_RELEASE,
        "builtAt": datetime.now(timezone.utc).isoformat(),
        "copiedEntries": copied,
        "fileCount": len(files),
        "files": files,
    }
    (staging / BUILD_MANIFEST).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _copy_public_site(root: Path, staging: Path) -> list[str]:
    copied: list[str] = []
    for relative in REQUIRED_FILES:
        source = root / relative
        target = staging / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.append(relative)

    for relative in OPTIONAL_FILES:
        source = root / relative
        if source.is_file():
            target = staging / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied.append(relative)

    for relative in REQUIRED_DIRECTORIES:
        shutil.copytree(
            root / relative,
            staging / relative,
            ignore=shutil.ignore_patterns(".DS_Store", "__pycache__", "*.pyc"),
        )
        copied.append(relative + "/")
    return copied


def build_pages_site(root: Path, output: Path) -> list[str]:
    """Build Pages output atomically so a failed build never erases the last site."""

    root = root.resolve()
    output = output.resolve()
    _assert_safe_output(root, output)
    _validate_required_sources(root)
    output.parent.mkdir(parents=True, exist_ok=True)

    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}.r12-staging-", dir=output.parent))
    backup = output.with_name(f".{output.name}.r12-backup")
    copied: list[str] = []
    try:
        copied = _copy_public_site(root, staging)
        _write_manifest(staging, copied)

        if backup.exists():
            shutil.rmtree(backup)
        if output.exists():
            output.replace(backup)
        staging.replace(output)
        if backup.exists():
            shutil.rmtree(backup)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        if backup.exists() and not output.exists():
            backup.replace(output)
        raise
    return [*copied, BUILD_MANIFEST]


def main() -> int:
    args = parse_args()
    copied = build_pages_site(Path(args.root), Path(args.output))
    print("Validated Pages site built atomically:")
    for item in copied:
        print(f"- {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
