#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import shutil


REQUIRED_FILES = (
    "index.html",
    ".nojekyll",
    "data/exhibitions.enriched.json",
    "data/exhibitions.json",
)
OPTIONAL_FILES = ("CNAME",)
REQUIRED_DIRECTORIES = ("assets",)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a minimal GitHub Pages upload directory."
    )
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default="site")
    return parser.parse_args()


def build_pages_site(root: Path, output: Path) -> list[str]:
    root = root.resolve()
    output = output.resolve()
    if output == root or root in output.parents and output == root:
        raise ValueError("Output directory must not replace the repository root.")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    copied: list[str] = []
    for relative in REQUIRED_FILES:
        source = root / relative
        if not source.exists():
            raise FileNotFoundError(f"Missing required site file: {relative}")
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.append(relative)

    for relative in OPTIONAL_FILES:
        source = root / relative
        if source.exists():
            target = output / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied.append(relative)

    for relative in REQUIRED_DIRECTORIES:
        source = root / relative
        if not source.is_dir():
            raise FileNotFoundError(f"Missing required site directory: {relative}")
        target = output / relative
        shutil.copytree(
            source,
            target,
            ignore=shutil.ignore_patterns(".DS_Store", "__pycache__"),
        )
        copied.append(relative + "/")

    return copied


def main() -> int:
    args = parse_args()
    copied = build_pages_site(Path(args.root), Path(args.output))
    print("Minimal Pages site built:")
    for item in copied:
        print(f"- {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
