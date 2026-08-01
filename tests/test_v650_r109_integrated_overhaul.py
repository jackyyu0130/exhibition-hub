from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
CURATION = (ROOT / "scripts" / "exhibition_hub" / "curation.py").read_text(encoding="utf-8")
MATRIX = json.loads((ROOT / "data" / "taiwan_venue_matrix.json").read_text(encoding="utf-8"))

class R109IntegratedOverhaulTests(unittest.TestCase):
    def test_version(self):
        self.assertIn("6.5.0-r10.9", HTML)
    def test_search(self):
        self.assertIn("canonicalVenueQueryTarget", APP)
        self.assertIn("'松煙':'松山文創園區'", APP)
    def test_venue(self):
        self.assertIn("normalizedVenueLookupKey", APP)
        self.assertIn("尚無展演", APP)
    def test_anime(self):
        for token in ("ACG", "VTuber", "航海王", "鬼滅之刃", "鋼彈"):
            self.assertIn(token, APP)
            self.assertIn(token, CURATION)
    def test_mobile(self):
        self.assertIn("mobileDrawerTargetOffset", APP)
        self.assertIn("getBoundingClientRect", APP)
    def test_hero(self):
        self.assertIn("--hero-x: 49% !important", CSS)
    def test_matrix(self):
        record = next(v for v in MATRIX["venues"] if v.get("name") == "松山文創園區")
        self.assertTrue({"松菸","松煙","松山菸廠"}.issubset(set(record.get("aliases") or [])))

if __name__ == "__main__":
    unittest.main()
