import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_pages_site import build_pages_site  # noqa: E402


class PagesSiteBuilderTests(unittest.TestCase):
    def test_builder_deploys_only_public_site_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            output = Path(directory) / "site"
            (root / "assets").mkdir(parents=True)
            (root / "data").mkdir(parents=True)
            (root / "scripts").mkdir(parents=True)
            (root / "docs").mkdir(parents=True)
            (root / "index.html").write_text("ok", encoding="utf-8")
            (root / ".nojekyll").write_text("", encoding="utf-8")
            (root / "assets/app.js").write_text("ok", encoding="utf-8")
            (root / "data/exhibitions.enriched.json").write_text("{}", encoding="utf-8")
            (root / "data/exhibitions.json").write_text("{}", encoding="utf-8")
            (root / "scripts/private.py").write_text("no", encoding="utf-8")
            (root / "docs/private.md").write_text("no", encoding="utf-8")

            build_pages_site(root, output)

            self.assertTrue((output / "index.html").exists())
            self.assertTrue((output / "assets/app.js").exists())
            self.assertTrue((output / "data/exhibitions.enriched.json").exists())
            self.assertFalse((output / "scripts").exists())
            self.assertFalse((output / "docs").exists())
            self.assertFalse((output / "tests").exists())

    def test_missing_required_data_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            output = Path(directory) / "site"
            (root / "assets").mkdir(parents=True)
            (root / "index.html").write_text("ok", encoding="utf-8")
            (root / ".nojekyll").write_text("", encoding="utf-8")
            with self.assertRaises(FileNotFoundError):
                build_pages_site(root, output)


if __name__ == "__main__":
    unittest.main()
