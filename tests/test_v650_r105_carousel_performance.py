from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


class R105CarouselPerformanceTests(unittest.TestCase):
    def test_per_ticket_carousel_is_present(self):
        self.assertIn("is-r105-moving", APP)
        self.assertIn("moveSlot(first, 1, 0)", APP)
        self.assertIn("moveSlot(second, 2, 1)", APP)
        self.assertIn("moveSlot(third, 3, 2)", APP)
        self.assertIn("moveSlot(incoming, 4, 3)", APP)

    def test_reverse_carousel_is_present(self):
        self.assertIn("moveSlot(third, 3, 4)", APP)
        self.assertIn("moveSlot(second, 2, 3)", APP)
        self.assertIn("moveSlot(first, 1, 2)", APP)
        self.assertIn("moveSlot(incoming, 0, 1)", APP)

    def test_whole_stack_animation_removed(self):
        function = APP.split("function changeHeroPair(direction)", 1)[1].split("const HOME_STATUS_COPY", 1)[0]
        self.assertNotIn("stack.animate(", function)

    def test_static_data_can_revalidate_from_cache(self):
        self.assertNotIn("cache:'no-store'", APP)

    def test_expensive_persistent_blur_is_disabled(self):
        self.assertIn("Exhibition Hub V6.5.0-R10.5", CSS)
        self.assertRegex(CSS, r"\.site-header,[\s\S]*?backdrop-filter:\s*none\s*!important")

    def test_cache_version_bumped(self):
        self.assertIn("6.5.0-r10.5", INDEX)


if __name__ == "__main__":
    unittest.main()
