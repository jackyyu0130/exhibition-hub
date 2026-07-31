import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")


class V650PostcardCarouselTests(unittest.TestCase):
    def test_frontend_assets_share_v650r7_cache_version(self):
        for marker in (
            "assets/styles.css?v=6.5.0-r10.3",
            "assets/app.js?v=6.5.0-r10.3",
            "assets/favicon-48.png?v=6.5.0-r7",
            "assets/apple-touch-icon.png?v=6.5.0-r7",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, HTML)

    def test_shuffle_control_and_timer_copy_are_removed(self):
        self.assertNotIn('id="heroShuffleButton"', HTML)
        self.assertNotIn("再抽一組觀展靈感", HTML)
        self.assertNotIn("HERO_ROTATION_MS", APP)

    def test_three_ticket_queue_is_rendered_with_rotating_poses(self):
        self.assertIn("function heroTicketSlideMarkup", APP)
        self.assertIn("function heroPoseIndex", APP)
        self.assertIn('data-pose="${poseIndex}"', APP)
        self.assertIn("const thirdIndex = heroIndex(2)", APP)
        self.assertIn("heroTicketSlideMarkup(pool[firstIndex], 1", APP)
        self.assertIn("heroTicketSlideMarkup(pool[secondIndex], 2", APP)
        self.assertIn("heroTicketSlideMarkup(pool[thirdIndex], 3", APP)
        self.assertIn("heroTicketSlideMarkup(pool[incomingIndex], 4", APP)
        self.assertNotIn("hero-postcard-image", APP)
        self.assertNotIn("function heroPairMarkup", APP)

    def test_desktop_arrows_use_angle_brackets_outside_the_frame(self):
        self.assertIn('id="heroNextButton"', HTML)
        self.assertIn('id="heroPreviousButton"', HTML)
        self.assertIn('&lt;</span>', HTML)
        self.assertIn('&gt;</span>', HTML)
        self.assertIn("$('#heroNextButton')?.addEventListener", APP)
        self.assertIn("changeHeroPair(1);", APP)
        self.assertIn("changeHeroPair(-1);", APP)
        self.assertIn(".hero-carousel-next { left: -78px; }", CSS)
        self.assertIn(".hero-carousel-previous { right: -78px; }", CSS)

    def test_back_tickets_keep_queue_depth(self):
        self.assertIn(".hero-ticket-slot-1", CSS)
        self.assertIn(".hero-ticket-slot-2", CSS)
        self.assertIn(".hero-ticket-slot-3", CSS)
        self.assertIn(".hero-ticket-stack.is-moving-next .hero-ticket-exit-next", CSS)
        self.assertIn(".hero-ticket-stack.is-moving-next .hero-ticket-promote-next", CSS)
        self.assertIn(".hero-ticket-stack.is-moving-next .hero-ticket-incoming-next", CSS)
        self.assertIn(".hero-ticket-stack.is-moving-previous .hero-ticket-incoming-previous", CSS)

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
