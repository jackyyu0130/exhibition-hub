from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


class R106HeroHoverStabilityTests(unittest.TestCase):
    def test_frontend_cache_version_is_r106(self):
        self.assertIn("assets/styles.css?v=6.5.0-r10.6", INDEX)
        self.assertIn("assets/app.js?v=6.5.0-r10.6", INDEX)

    def test_hover_preserves_variable_based_slot_position(self):
        marker = "Exhibition Hub V6.5.0-R10.6"
        self.assertIn(marker, CSS)
        block = CSS.split(marker, 1)[1]
        self.assertIn(".hero-ticket-stage .hero-ticket-slide:hover", block)
        self.assertIn(
            "transform: translate3d(var(--hero-x, 0%), var(--hero-y, 0px), 0) !important",
            block,
        )
        self.assertIn("z-index: var(--hero-z, 1) !important", block)
        self.assertIn("opacity: var(--hero-opacity, 1) !important", block)

    def test_ticket_card_hover_does_not_translate(self):
        block = CSS.split("Exhibition Hub V6.5.0-R10.6", 1)[1]
        self.assertIn(".hero-ticket-stage .hero-ticket-card:hover", block)
        self.assertIn(
            "transform: translateZ(0) rotate(var(--hero-ticket-rotate, -1.6deg)) !important",
            block,
        )
        self.assertNotIn("translateY(-7px)", block)
        self.assertNotIn("translate(-8px,-7px)", block)
        self.assertNotIn("translate(-12px,-7px)", block)

    def test_mobile_touch_preview_is_position_locked(self):
        block = CSS.split("Exhibition Hub V6.5.0-R10.6", 1)[1]
        self.assertIn("@media (hover: none), (pointer: coarse)", block)
        self.assertIn(".hero-ticket-stage .hero-ticket-card.is-touch-preview", block)


if __name__ == "__main__":
    unittest.main()
