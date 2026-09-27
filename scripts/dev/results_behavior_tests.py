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
        """Hold API responses (and image loads) so tests can resolve them in
        adversarial order. `window.Image` is stubbed the same way as
        `fetch`: assigning `.src` only records the instance in
        `pendingImages`, so a test decides exactly when a photo "loads" via
        `.onload()`/`.onerror()`, instead of racing a real image fetch."""
        self.page.emulate_media(reduced_motion="reduce" if reduced else "no-preference")
        self.page.evaluate("""() => {
            window.pending = [];
            window.pendingImages = [];
            window.fetch = (url, options) => new Promise((resolve, reject) => {
                pending.push({url, resolve, reject});
                if (options && options.signal) {
                    options.signal.addEventListener('abort', () => {
                        reject(new DOMException('Aborted', 'AbortError'));
                    });
                }
            });
            window.Image = class {
                set src(value) {
                    this._src = value;
                    window.pendingImages.push(this);
                }
                get src() { return this._src; }
            };
        }""")
        self.start(
            "results-spotlight.js",
            '<div id="artist-spotlight-card" style="display:none"><div id="spotlight-card-content">'
            '<img id="spotlight-artist-img" class="hidden">'
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

    def resolve_pending(self, script):
        """Run `script` (which resolves one or more `pending` fetches) and flush
        the microtask queue far enough for the resulting `Promise.all(...)`
        chain in `startArtistSpotlightRotation` to settle."""
        self.page.evaluate(
            "async () => { (" + script + ")(); "
            "for (let i = 0; i < 20; i++) await Promise.resolve(); }"
        )

    def resolve_images(self, *indices):
        """Fire `onload` for the given `pendingImages` indices (a confirmed
        candidate's preload settling), then flush microtasks the same way
        `resolve_pending` does."""
        script = (
            "() => { "
            + " ".join(f"pendingImages[{index}].onload();" for index in indices)
            + " }"
        )
        self.resolve_pending(script)

    def test_spotlight_rotation_wraps_and_preserves_input(self):
        """Rotation uses the server order, wraps, and hides absent duration."""
        self.spotlight()
        self.assertEqual(
            self.page.locator("#artist-spotlight-card").evaluate(
                "el => getComputedStyle(el).display"
            ),
            "none",
        )
        self.resolve_pending("""() => {
            pending[0].resolve({ok: true, json: async () => ({image_url: 'https://img/a.jpg'})});
            pending[1].resolve({ok: true, json: async () => ({image_url: 'https://img/b.jpg'})});
        }""")
        self.resolve_images(0, 1)
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

    def test_card_hidden_until_settle_then_drops_unconfirmed_candidates(self):
        """The card stays hidden until every hydration settles, then rotation
        never shows a candidate without a confirmed photo (F-B21-60)."""
        self.spotlight()
        self.assertEqual(
            self.page.evaluate("pending[0].url"),
            "/api/artist_spotlight?artist=A%20%26%20B",
        )
        self.resolve_pending("""() => {
            pending[0].resolve({ok: true, json: async () => ({image_url: 'https://img/a.jpg', spotify_url: 'https://open.spotify.com/artist/a'})});
        }""")
        self.resolve_images(0)
        self.assertEqual(
            self.page.locator("#artist-spotlight-card").evaluate(
                "el => getComputedStyle(el).display"
            ),
            "none",
        )
        self.resolve_pending("""() => {
            pending[1].resolve({ok: true, json: async () => ({image_url: ''})});
        }""")
        self.assertEqual(
            self.page.locator("#spotlight-artist-name").inner_text(), "A & B"
        )
        self.assertEqual(
            self.page.locator("#spotlight-artist-rank").inner_text(), "01 / 01"
        )
        self.assertEqual(
            self.page.locator("#spotlight-spotify-link").get_attribute("href"),
            "https://open.spotify.com/artist/a",
        )
        # A filtered, single-candidate list never has a second tick to rotate
        # to: each single 7s tick must still show "A & B", never "Second"
        # (the dropped, unconfirmed candidate), unlike a real two-candidate
        # rotation that would wrap between them.
        self.page.clock.run_for(7000)
        self.assertEqual(
            self.page.locator("#spotlight-artist-name").inner_text(), "A & B"
        )
        self.page.clock.run_for(7000)
        self.assertEqual(
            self.page.locator("#spotlight-artist-name").inner_text(), "A & B"
        )

    def test_reduced_motion_keeps_first_confirmed_artist_after_failed_hydration(self):
        """A failed hydration drops its candidate; reduced motion keeps the
        surviving confirmed artist still."""
        self.spotlight(reduced=True)
        self.resolve_pending("""() => {
            pending[0].resolve({ok: false});
            pending[1].resolve({ok: true, json: async () => ({image_url: 'https://img/b.jpg'})});
        }""")
        self.resolve_images(0)
        self.assertEqual(
            self.page.locator("#spotlight-artist-name").inner_text(), "Second"
        )
        self.assertEqual(
            self.page.locator("#spotlight-artist-rank").inner_text(), "01 / 01"
        )
        self.page.clock.run_for(30000)
        self.assertEqual(
            self.page.locator("#spotlight-artist-name").inner_text(), "Second"
        )
        self.assertEqual(
            self.page.locator("#spotlight-scrobble-text").inner_text(),
            "10 scrobbles across 2 albums in 2025",
        )

    def test_photo_swaps_synchronously_with_name_on_rotation(self):
        """The visible photo always belongs to the candidate whose name is
        shown -- no stale photo under a new name during a swap (F-B21-60 /
        B2). Both photos are preloaded and cached before either candidate is
        ever shown, so a swap needs no further Image() at all."""
        self.spotlight()
        self.resolve_pending("""() => {
            pending[0].resolve({ok: true, json: async () => ({image_url: 'https://img/a.jpg'})});
            pending[1].resolve({ok: true, json: async () => ({image_url: 'https://img/b.jpg'})});
        }""")
        self.assertEqual(self.page.evaluate("pendingImages.length"), 2)
        self.resolve_images(0, 1)
        self.assertEqual(
            self.page.locator("#spotlight-artist-img").get_attribute("src"),
            "https://img/a.jpg",
        )
        self.assertEqual(
            self.page.locator("#spotlight-artist-name").inner_text(), "A & B"
        )
        self.page.clock.run_for(7150)
        self.assertEqual(
            self.page.locator("#spotlight-artist-name").inner_text(), "Second"
        )
        self.assertEqual(
            self.page.locator("#spotlight-artist-img").get_attribute("src"),
            "https://img/b.jpg",
        )
        # No third Image() at swap time: both photos were already preloaded.
        self.assertEqual(self.page.evaluate("pendingImages.length"), 2)

    def test_stalled_hydrate_request_is_dropped_after_timeout(self):
        """One candidate's hydrate request that never answers does not keep
        the card hidden forever: it is bounded by a timeout and dropped like
        an unconfirmed candidate, so the others still reveal the card
        (F-B21-60 / B3)."""
        self.spotlight()
        self.resolve_pending("""() => {
            pending[1].resolve({ok: true, json: async () => ({image_url: 'https://img/b.jpg'})});
        }""")
        self.resolve_images(0)
        # Still hidden: candidate 0's request has neither answered nor timed
        # out yet.
        self.assertEqual(
            self.page.locator("#artist-spotlight-card").evaluate(
                "el => getComputedStyle(el).display"
            ),
            "none",
        )
        self.page.clock.run_for(8000)
        self.assertEqual(
            self.page.locator("#spotlight-artist-name").inner_text(), "Second"
        )
        self.assertEqual(
            self.page.locator("#spotlight-artist-rank").inner_text(), "01 / 01"
        )

    def test_stalled_image_preload_is_dropped_after_timeout(self):
        """A confirmed candidate whose *photo* never answers does not keep the
        card hidden forever either: the fetch, its json body and the image
        preload all share one timeout budget, so a hung image is dropped like
        an unconfirmed candidate, not left pending indefinitely (F-B21-60 /
        B3 follow-up)."""
        self.spotlight()
        self.resolve_pending("""() => {
            pending[0].resolve({ok: true, json: async () => ({image_url: 'https://img/a.jpg'})});
            pending[1].resolve({ok: true, json: async () => ({image_url: 'https://img/b.jpg'})});
        }""")
        # Candidate 0's image (pendingImages[0]) never fires onload/onerror;
        # only candidate 1's does.
        self.resolve_images(1)
        # Still hidden: candidate 0's image has neither loaded nor timed out.
        self.assertEqual(
            self.page.locator("#artist-spotlight-card").evaluate(
                "el => getComputedStyle(el).display"
            ),
            "none",
        )
        self.page.clock.run_for(8000)
        self.assertEqual(
            self.page.locator("#spotlight-artist-name").inner_text(), "Second"
        )
        self.assertEqual(
            self.page.locator("#spotlight-artist-rank").inner_text(), "01 / 01"
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
