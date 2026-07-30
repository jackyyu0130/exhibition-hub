import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")


class V650PostcardCarouselTests(unittest.TestCase):
    def test_frontend_assets_share_v650r4_cache_version(self):
        for marker in (
            "assets/styles.css?v=6.5.0-r6",
            "assets/app.js?v=6.5.0-r6",
            "assets/favicon-48.png?v=6.5.0-r6",
            "assets/apple-touch-icon.png?v=6.5.0-r6",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, HTML)

    def test_shuffle_control_and_timer_copy_are_removed(self):
        self.assertNotIn('id="heroShuffleButton"', HTML)
        self.assertNotIn("再抽一組觀展靈感", HTML)
        self.assertNotIn("HERO_ROTATION_MS", APP)

    def test_two_ticket_and_postcard_pairs_are_rendered_with_rotating_poses(self):
        self.assertIn("function heroPairMarkup", APP)
        self.assertIn("function heroPoseIndex", APP)
        self.assertIn('data-pose="${poseIndex}"', APP)
        self.assertIn("heroPairMarkup(pool[firstIndex], 1", APP)
        self.assertIn("heroPairMarkup(pool[secondIndex], 2", APP)
        self.assertIn("heroPoseIndex(incomingIndex)", APP)
        self.assertIn("hero-postcard-image", APP)

    def test_desktop_arrows_use_angle_brackets_outside_the_frame(self):
        self.assertIn('id="heroNextButton"', HTML)
        self.assertIn('id="heroPreviousButton"', HTML)
        self.assertIn('&lt;</span>', HTML)
        self.assertIn('&gt;</span>', HTML)
        self.assertIn("$('#heroNextButton')?.addEventListener", APP)
        self.assertIn("changeHeroPair(1);", APP)
        self.assertIn("changeHeroPair(-1);", APP)
        self.assertIn(".hero-visual > .hero-carousel-next { left: -72px; }", CSS)
        self.assertIn(".hero-visual > .hero-carousel-previous { right: -72px; }", CSS)

    def test_back_pair_and_incoming_pair_gain_depth_blur(self):
        self.assertIn('.hero-pair-slot-2 .hero-postcard,', CSS)
        self.assertIn('filter: blur(1.8px) saturate(.93);', CSS)
        self.assertIn('.hero-pair-slot-3 .hero-postcard,', CSS)
        self.assertIn('filter: blur(3px) saturate(.88);', CSS)
        self.assertIn('.hero-ticket-stack.is-moving-next .hero-pair-promote-next .hero-postcard,', CSS)
        self.assertIn('filter: blur(0px) saturate(1);', CSS)

    def test_mobile_swipe_left_is_next_and_right_is_previous(self):
        self.assertIn("changeHeroPair(deltaX < 0 ? 1 : -1)", APP)
        self.assertIn("state.heroSwipeBlockClickUntil", APP)
        self.assertIn(".hero-carousel-arrow { display: none; }", CSS)

    def test_mobile_home_has_four_direct_actions(self):
        for marker in (
            'data-open-mobile-filter="calendar"',
            'data-open-mobile-filter="category"',
            'data-open-mobile-filter="location"',
            "?view=all&amp;admission=free",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, HTML)
        self.assertIn("grid-template-columns: repeat(2,minmax(0,1fr));", CSS)

    def test_old_mobile_filter_workbench_is_hidden(self):
        self.assertIn(".home-view .filter-workbench,", CSS)
        self.assertIn("display: none !important;", CSS)

    def test_mobile_card_badges_are_centered(self):
        self.assertIn(".listing-view .card-badge {", CSS)
        self.assertIn("align-items: center;", CSS)
        self.assertIn("justify-content: center;", CSS)
        self.assertIn("text-align: center;", CSS)


if __name__ == "__main__":
    unittest.main()
