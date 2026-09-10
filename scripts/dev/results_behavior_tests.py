"""Isolated Results script tests in Chromium; no Flask, network or new JS runner.

Run after installing the repository's pinned Playwright Chromium binary:
    python scripts/dev/results_behavior_tests.py
These complement the full-page frontend gate, without requiring its fixtures.
"""

import unittest
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]


class ResultsBehaviorTests(unittest.TestCase):
    """Exercise production scripts through DOM events with a controlled clock."""

    @classmethod
    def setUpClass(cls):
        """Share only the browser process, never document or timer state."""
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        """Release browser resources after all cases."""
        cls.browser.close()
        cls.runtime.stop()

    def setUp(self):
        """Create a fresh isolated page and freeze timers before script startup."""
        self.page = self.browser.new_page()
        self.addCleanup(self.page.close)
        self.page.route("**/*", lambda route: route.abort())
        self.page.clock.install()
        self.page.clock.pause_at(1000000000000)

    def start(self, script, markup, data):
        """Load the unmodified production script into a minimal real DOM."""
        self.page.set_content(markup)
        self.page.evaluate("data => window.APP_DATA = data", data)
        self.page.add_script_tag(path=str(ROOT / "static/js" / script))
        self.page.evaluate("document.dispatchEvent(new Event('DOMContentLoaded'))")

    def spotlight(self, reduced=False):
        """Hold API responses so tests can resolve them in adversarial order."""
        self.page.emulate_media(reduced_motion="reduce" if reduced else "no-preference")
        self.page.evaluate("""() => {
            window.pending = [];
            window.fetch = url => new Promise(resolve => pending.push({url, resolve}));
        }""")
        self.start(
            "results-spotlight.js",
            '<div id="artist-spotlight-card"><div id="spotlight-card-content">'
            '<span id="spotlight-artist-name"></span>'
            '<span id="spotlight-artist-rank"></span>'
            '<span id="spotlight-playtime-badge"></span>'
            '<span id="spotlight-playtime-sep"></span>'
            '<span id="spotlight-scrobble-text"></span>'
            '<a id="spotlight-spotify-link"></a></div></div>',
            {
                "year": 2025,
                "spotlight_artists": [
                    {
                        "name": "A & B",
                        "scrobbles": 20,
                        "album_count": 1,
                        "play_time_seconds": 90,
                    },
                    {
                        "name": "Second",
                        "scrobbles": 10,
                        "album_count": 2,
                        "play_time_seconds": 0,
                    },
                ],
            },
        )

    def test_spotlight_rotation_wraps_and_preserves_input(self):
        """Rotation uses the server order, wraps, and hides absent duration."""
        self.spotlight()
        self.assertEqual(
            self.page.locator("#spotlight-artist-name").inner_text(), "A & B"
        )
        self.assertEqual(
            self.page.locator("#spotlight-playtime-badge").inner_text(), "1m 30s"
        )
        self.page.clock.run_for(7150)
        self.assertEqual(
            self.page.locator("#spotlight-artist-name").inner_text(), "Second"
        )
        self.assertEqual(
            self.page.locator("#spotlight-artist-rank").inner_text(), "02 / 02"
        )
        self.assertIn(
            "hidden",
            self.page.locator("#spotlight-playtime-badge").get_attribute("class"),
        )
        self.page.clock.run_for(7000)
        self.assertEqual(
            self.page.locator("#spotlight-artist-name").inner_text(), "A & B"
        )
        self.assertEqual(
            self.page.evaluate("APP_DATA.spotlight_artists.map(a => a.name)"),
            ["A & B", "Second"],
        )

    def test_late_hydration_does_not_replace_visible_artist(self):
        """A previous artist's response is retained for its next turn only."""
        self.spotlight()
        self.assertEqual(
            self.page.evaluate("pending[0].url"),
            "/api/artist_spotlight?artist=A%20%26%20B",
        )
        self.page.clock.run_for(7150)
        self.page.evaluate("""async () => {
            pending[0].resolve({ok: true, json: async () => ({spotify_url: 'https://open.spotify.com/artist/a'})});
            await new Promise(resolve => queueMicrotask(resolve));
        }""")
        self.assertEqual(
            self.page.locator("#spotlight-artist-name").inner_text(), "Second"
        )
        self.assertIsNone(
            self.page.locator("#spotlight-spotify-link").get_attribute("href")
        )
        self.page.clock.run_for(7000)
        self.assertEqual(
            self.page.locator("#spotlight-spotify-link").get_attribute("href"),
            "https://open.spotify.com/artist/a",
        )
        self.assertNotIn(
            "spotify_url", self.page.evaluate("APP_DATA.spotlight_artists[0]")
        )

    def test_reduced_motion_keeps_first_artist_after_failed_hydration(self):
        """An API failure preserves text; reduced motion disables rotation."""
        self.spotlight(reduced=True)
        self.page.evaluate("pending.forEach(p => p.resolve({ok: false}))")
        self.page.clock.run_for(30000)
        self.assertEqual(
            self.page.locator("#spotlight-artist-name").inner_text(), "A & B"
        )
        self.assertEqual(
            self.page.locator("#spotlight-scrobble-text").inner_text(),
            "20 scrobbles across 1 album in 2025",
        )

    def leaderboard(self):
        """Use numeric-sort traps and an absent metric, with minimal controls."""
        self.page.emulate_media(reduced_motion="reduce")
        rows = "".join(
            f'<tr data-album="{name}" data-play-count="{plays}" '
            f'data-play-time-seconds="{seconds}" data-play-time="{name} duration">'
            '<td><span class="rank-num"></span></td><td class="metric-value-cell"></td></tr>'
            for name, plays, seconds in [
                ("A", "100", "9"),
                ("B", "20", "100"),
                ("C", "", ""),
            ]
        )
        self.start(
            "results.js",
            '<button id="toggle-sort-plays"></button>'
            '<button id="toggle-sort-playtime"></button><span id="metric-header-label"></span>'
            '<table id="results-table"><tbody>' + rows + "</tbody></table>",
            {"year": 2025},
        )

    def test_sort_updates_order_ranks_metrics_and_accessibility(self):
        """Both modes update canonical ranks and selected state, including zeros."""
        self.leaderboard()
        for mode, expected in [
            ("playtime", ["B", "A", "C"]),
            ("plays", ["A", "B", "C"]),
        ]:
            self.page.locator(f"#toggle-sort-{mode}").click()
            rows = self.page.locator("tbody tr")
            self.assertEqual(
                rows.evaluate_all("rows => rows.map(r => r.dataset.album)"), expected
            )
            self.assertEqual(
                rows.evaluate_all("rows => rows.map(r => r.dataset.rank)"),
                ["1", "2", "3"],
            )
            self.assertEqual(
                self.page.locator(".rank-num").all_text_contents(), ["01", "02", "03"]
            )
            self.assertEqual(
                self.page.locator(f"#toggle-sort-{mode}").get_attribute("aria-pressed"),
                "true",
            )
            other = "plays" if mode == "playtime" else "playtime"
            self.assertEqual(
                self.page.locator(f"#toggle-sort-{other}").get_attribute(
                    "aria-pressed"
                ),
                "false",
            )
            self.assertEqual(self.page.locator(".is-reordering").count(), 0)
        self.assertEqual(
            self.page.locator(".metric-value-cell").all_text_contents(),
            ["100", "20", "0"],
        )

    def tooltip(self):
        """Expose the shared tooltip through two actual focusable album links."""
        self.start(
            "results.js",
            '<a class="album-link" href="#a">A</a>'
            '<a class="album-link" href="#b">B</a>',
            {},
        )
        return self.page.locator("#album-link-tooltip")

    def test_tooltip_waits_and_cancels_short_hover(self):
        """A short hover never reveals the hint; a sustained hover does."""
        tip = self.tooltip()
        link = self.page.locator(".album-link").first
        link.dispatch_event("mouseenter")
        self.page.clock.run_for(449)
        self.assertNotIn("is-visible", tip.get_attribute("class"))
        link.dispatch_event("mouseleave")
        self.page.clock.run_for(500)
        self.assertNotIn("is-visible", tip.get_attribute("class"))
        link.dispatch_event("mouseenter")
        self.page.clock.run_for(450)
        self.assertIn("is-visible", tip.get_attribute("class"))

    def test_tooltip_keyboard_escape_and_scroll(self):
        """Keyboard access is immediate, shared and dismissible without a mouse."""
        tip = self.tooltip()
        self.page.keyboard.press("Tab")
        self.assertIn("is-visible", tip.get_attribute("class"))
        self.assertEqual(
            self.page.locator(":focus").get_attribute("aria-describedby"),
            tip.get_attribute("id"),
        )
        self.page.keyboard.press("Escape")
        self.assertNotIn("is-visible", tip.get_attribute("class"))
        self.page.keyboard.press("Tab")
        self.assertIn("is-visible", tip.get_attribute("class"))
        self.page.evaluate("window.dispatchEvent(new Event('scroll'))")
        self.assertNotIn("is-visible", tip.get_attribute("class"))
        self.assertEqual(self.page.locator('[role="tooltip"]').count(), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
