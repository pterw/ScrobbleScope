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

    SPOTLIGHT_MARKUP = (
        '<div id="artist-spotlight-card" style="display:none"><div id="spotlight-card-content">'
        '<img id="spotlight-artist-img" class="hidden">'
        '<span id="spotlight-artist-name"></span>'
        '<span id="spotlight-artist-rank"></span>'
        '<span id="spotlight-playtime-badge"></span>'
        '<span id="spotlight-playtime-sep"></span>'
        '<span id="spotlight-scrobble-text"></span>'
        '<a id="spotlight-spotify-link"></a></div></div>'
    )

    def spotlight(self, reduced=False, markup=None, artists=None):
        """Hold API responses (and image loads) so tests can resolve them in
        adversarial order. `window.Image` is stubbed the same way as
        `fetch`: assigning `.src` only records the instance in
        `pendingImages`, so a test decides exactly when a photo "loads" via
        `.onload()`/`.onerror()`, instead of racing a real image fetch.
        `markup` and `artists` replace the default card and candidates."""
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
            markup or self.SPOTLIGHT_MARKUP,
            {
                "year": 2025,
                "spotlight_artists": artists
                or [
                    {
                        "name": "A & B",
                        "scrobbles": 20,
                        "album_count": 1,
                        "play_time_seconds": 90,
                        "play_time": "1m 30s",
                    },
                    {
                        "name": "Second",
                        "scrobbles": 10,
                        "album_count": 2,
                        "play_time_seconds": 0,
                        "play_time": "",
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
        # Hydration builds its own candidates; it never writes a photo or a
        # Spotify link back into the server's `spotlight_artists` entries.
        self.assertEqual(
            self.page.evaluate(
                "APP_DATA.spotlight_artists.map(a => "
                "['image_url', 'spotify_url'].filter(key => key in a))"
            ),
            [[], []],
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
        # Nothing rotates, so no height is reserved for a taller candidate.
        self.assertEqual(
            self.page.locator("#artist-spotlight-card").evaluate(
                "el => el.style.minHeight"
            ),
            "",
        )

    def settle_two_candidates(self):
        """Confirm both candidates' photos; only the first has a Spotify link."""
        self.resolve_pending("""() => {
            pending[0].resolve({ok: true, json: async () => ({image_url: 'https://img/a.jpg', spotify_url: 'https://open.spotify.com/artist/a'})});
            pending[1].resolve({ok: true, json: async () => ({image_url: 'https://img/b.jpg'})});
        }""")
        self.resolve_images(0, 1)

    def test_a_rotating_card_reserves_its_tallest_height(self):
        """The counterpart of the reduced-motion case: a card that rotates
        holds the tallest candidate's height, so the rail below never moves."""
        self.spotlight()
        self.settle_two_candidates()
        self.assertNotEqual(
            self.page.locator("#artist-spotlight-card").evaluate(
                "el => el.style.minHeight"
            ),
            "",
        )

    def test_a_pointer_resting_on_a_card_shown_under_it_pauses_the_rotation(self):
        """A card that first appears under a still pointer is held: the
        browser hit-tests the pointer after the layout change and fires
        `pointerenter` itself, which the card listens for. Chromium only: this
        runner drives no other engine."""
        # A doctype, as every production page has one: without it the page is
        # in quirks mode, where a bare `:hover` matches nothing but links.
        self.spotlight(markup="<!doctype html>" + self.SPOTLIGHT_MARKUP)
        self.page.mouse.move(60, 15)
        self.settle_two_candidates()
        # The browser hit-tests the pointer against the new layout on its own
        # (real) schedule, outside the page's frozen clock.
        self.page.wait_for_function(
            "document.getElementById('artist-spotlight-card').matches(':hover')"
        )
        self.page.clock.run_for(7150)
        self.assertEqual(
            self.page.locator("#spotlight-artist-name").inner_text(), "A & B"
        )
        self.page.mouse.move(0, 700)
        self.page.wait_for_function(
            "!document.getElementById('artist-spotlight-card').matches(':hover')"
        )
        self.page.clock.run_for(7000)
        self.assertEqual(
            self.page.locator("#spotlight-artist-name").inner_text(), "Second"
        )

    #: A card whose height depends on the link: a 36px row when the link
    #: shows, 20px when it does not; the second candidate adds a 60px badge.
    #: The photo is out of the layout: the page blocks every request, so an
    #: `<img>` fails at a moment no test controls, and a failed image with alt
    #: text is an 18px line. The production card holds its photo in a sized box.
    LINK_LAYOUT_MARKUP = (
        "<style>.hidden{display:none}"
        "#spotlight-artist-name{display:block;height:20px}"
        "#spotlight-artist-img{display:none}"
        "#spotlight-playtime-badge{display:block;height:60px}"
        "#spotlight-playtime-badge.hidden{display:none}"
        ".link-icon{display:block;width:24px;height:24px}</style>"
        '<div id="artist-spotlight-card" style="display:none;width:400px">'
        '<div id="spotlight-card-content"><img id="spotlight-artist-img">'
        '<div style="display:flex"><span id="spotlight-artist-name"></span>'
        '<a id="spotlight-spotify-link" class="spotlight-spotify-link hidden">'
        '<span class="link-icon"></span></a></div>'
        '<span id="spotlight-artist-rank"></span>'
        '<span id="spotlight-playtime-badge"></span>'
        '<span id="spotlight-playtime-sep"></span>'
        '<span id="spotlight-scrobble-text"></span></div></div>'
    )

    def test_a_remeasure_under_focus_ignores_a_link_the_candidate_lacks(self):
        """While the link holds focus it stays in place through the measuring
        pass, but a candidate with no Spotify link must not be measured with
        it: the reserved height is the same whether or not focus is on the
        card."""
        self.spotlight(
            markup=self.LINK_LAYOUT_MARKUP,
            artists=[
                {
                    "name": "One",
                    "scrobbles": 5,
                    "album_count": 1,
                    "play_time_seconds": 0,
                    "play_time": "",
                },
                {
                    "name": "Two",
                    "scrobbles": 5,
                    "album_count": 1,
                    "play_time_seconds": 60,
                    "play_time": "1m",
                },
            ],
        )
        self.page.add_style_tag(path=str(ROOT / "static/css/results.css"))
        self.settle_two_candidates()
        card = self.page.locator("#artist-spotlight-card")
        remeasure = "document.fonts.dispatchEvent(new Event('loadingdone'))"
        self.page.evaluate(remeasure)
        unfocused = card.evaluate("el => el.style.minHeight")
        self.page.locator("#spotlight-spotify-link").focus()
        self.page.evaluate(remeasure)
        self.assertEqual(
            self.page.evaluate("document.activeElement.id"), "spotlight-spotify-link"
        )
        self.assertEqual(card.evaluate("el => el.style.minHeight"), unfocused)
        self.assertNotEqual(unfocused, "")
        self.assertNotIn("is-measuring-without-link", card.get_attribute("class") or "")

    def test_photo_swaps_synchronously_with_name_on_rotation(self):
        """The visible photo always belongs to the candidate whose name is
        shown -- no stale photo under a new name during a swap (F-B21-60).
        Both photos are preloaded and cached before either candidate is ever
        shown, so a swap needs no further Image() at all."""
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
        (F-B21-60)."""
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
        an unconfirmed candidate, not left pending indefinitely (F-B21-60)."""
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
        """Expose the Spotify hint through two actual focusable album links."""
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

    def test_tooltip_names_the_provider_each_link_opens(self):
        """A Deezer row's hint says Deezer, a Spotify row's says Spotify, and
        a row with no provider is a Spotify row; each link describes itself by
        the hint that names its own provider."""
        self.start(
            "results.js",
            '<table><tr data-provider="spotify"><td><a class="album-link" href="#a">A</a></td></tr>'
            '<tr data-provider="deezer"><td><a class="album-link" href="#b">B</a></td></tr>'
            '<tr><td><a class="album-link" href="#c">C</a></td></tr></table>',
            {},
        )
        described = self.page.locator(".album-link").evaluate_all(
            "links => links.map(link => document.getElementById("
            "link.getAttribute('aria-describedby')).textContent)"
        )
        self.assertEqual(
            described,
            [
                "Open this album on Spotify (new tab)",
                "Open this album on Deezer (new tab)",
                "Open this album on Spotify (new tab)",
            ],
        )
        self.page.keyboard.press("Tab")
        self.page.keyboard.press("Tab")
        visible = self.page.locator(".album-link-tooltip.is-visible")
        self.assertEqual(visible.count(), 1)
        self.assertEqual(visible.text_content(), "Open this album on Deezer (new tab)")

    def test_tooltip_keyboard_escape_and_scroll(self):
        """Keyboard access is immediate and dismissible without a mouse."""
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

    # An include run, shaped like the rendered Results page: five rows by play
    # count, two of them unmatched (one per reason) and without a duration.
    INCLUDE_ROWS = (
        ("Alpha", "50", "3000", "50 mins", ""),
        ("Lost One", "45", "0", "", "no_spotify_match"),
        ("Beta", "40", "2000", "33 mins", ""),
        ("Lost Two", "35", "0", "", "provider_unavailable"),
        ("Gamma", "30", "1000", "16 mins", ""),
    )
    INCLUDE_MARKERS = {
        "no_spotify_match": "Not Found",
        "provider_unavailable": "Unavailable",
    }

    def include_run(self, has_durations=True):
        """Load results.js into the rows an include run renders, with the
        Unmatched albums control, both stats and the locked Listening Time button."""
        self.page.emulate_media(reduced_motion="reduce")
        rows = ""
        for number, (name, plays, seconds, duration, unmatched) in enumerate(
            self.INCLUDE_ROWS, 1
        ):
            marker = (
                f'<span class="provider-badge provider-badge--unmatched">'
                f"{self.INCLUDE_MARKERS[unmatched]}</span>"
                if unmatched
                else ""
            )
            release = (
                '<td class="release-date-cell" data-export="">unknown</td>'
                if unmatched
                else '<td class="release-date-cell" data-export="2025-01-02">2025-01</td>'
            )
            rows += (
                f'<tr data-rank="{number}" data-album="{name}" data-artist="{name} Band" '
                f'data-play-count="{plays}" data-play-time-seconds="{seconds}" '
                f'data-play-time="{duration}" data-provider="" data-unmatched="{unmatched}">'
                f'<td><span class="rank-num">{number:02d}</span></td>'
                f"<td><span>{name}</span>{marker}</td>"
                f'<td class="metric-value-cell"><span class="metric-value">{plays}</span></td>'
                f"{release}</tr>"
            )
        self.start(
            "results.js",
            '<div id="toastContainer"></div><button id="export-csv"></button>'
            '<span id="stat-total-albums">5</span><span id="stat-scrobbles">200</span>'
            '<span id="stat-top-artist" title="Lost One Band">Lost One Band</span>'
            '<button id="toggle-sort-plays"></button>'
            '<button id="toggle-sort-playtime" disabled '
            'title="Unmatched albums have no listening time" '
            f'data-has-durations="{"true" if has_durations else "false"}" '
            'class="opacity-50 cursor-not-allowed"></button>'
            '<span id="metric-header-label"></span>'
            '<input type="radio" id="results_albums_matched" name="results_albums">'
            '<label for="results_albums_matched">Hide</label>'
            '<input type="radio" id="results_albums_all" name="results_albums" checked>'
            '<label for="results_albums_all">Include</label>'
            '<table id="results-table"><tbody>' + rows + "</tbody></table>",
            {"year": 2025, "username": "u"},
        )

    def visible_albums(self):
        return self.page.locator("tbody tr:not([hidden])").evaluate_all(
            "rows => rows.map(r => r.dataset.album)"
        )

    def stats(self):
        return [
            self.page.locator("#stat-total-albums").inner_text(),
            self.page.locator("#stat-scrobbles").inner_text(),
            self.page.locator("#stat-top-artist").inner_text(),
        ]

    def test_matched_only_hides_rows_renumbers_and_offers_listening_time(self):
        """Choosing Hide takes both unmatched rows out, ranks the rest 01..03,
        recomputes the stats and enables Listening Time; showing them again
        restores the play-count ranking, the stats and the locked button."""
        self.include_run()
        button = self.page.locator("#toggle-sort-playtime")
        self.assertTrue(button.is_disabled())
        self.assertEqual(
            self.visible_albums(), ["Alpha", "Lost One", "Beta", "Lost Two", "Gamma"]
        )

        self.page.locator("label[for=results_albums_matched]").click()
        self.assertEqual(self.visible_albums(), ["Alpha", "Beta", "Gamma"])
        self.assertEqual(
            self.page.locator("tbody tr:not([hidden]) .rank-num").all_text_contents(),
            ["01", "02", "03"],
        )
        self.assertEqual(
            self.page.locator("tbody tr:not([hidden])").evaluate_all(
                "rows => rows.map(r => r.dataset.rank)"
            ),
            ["1", "2", "3"],
        )
        self.assertEqual(self.stats(), ["3", "120", "Alpha Band"])
        self.assertTrue(button.is_enabled())
        self.assertIsNone(button.get_attribute("title"))
        self.assertIn(
            "Unmatched albums hidden; listening time is available.",
            self.page.locator("#toastContainer").inner_text(),
        )

        # Listening time orders the visible rows by time.
        self.page.evaluate(
            "document.querySelector('tbody tr[data-album=\"Gamma\"]').dataset.playTimeSeconds = '9000'"
        )
        button.click()
        self.assertEqual(self.visible_albums(), ["Gamma", "Alpha", "Beta"])
        self.assertEqual(
            self.page.locator("tbody tr:not([hidden]) .rank-num").all_text_contents(),
            ["01", "02", "03"],
        )

        # Choosing All again (the arrow key moves the selection back) returns
        # to play count first: the unmatched rows have no time.
        self.page.locator("#results_albums_matched").focus()
        self.page.keyboard.press("ArrowLeft")
        self.assertEqual(
            self.visible_albums(),
            ["Alpha", "Lost One", "Beta", "Lost Two", "Gamma"],
        )
        self.assertEqual(
            self.page.locator("#results-table").get_attribute("data-metric"), "plays"
        )
        self.assertEqual(
            self.page.locator(".rank-num").all_text_contents(),
            ["01", "02", "03", "04", "05"],
        )
        self.assertEqual(self.stats(), ["5", "200", "Alpha Band"])
        self.assertTrue(button.is_disabled())
        self.assertEqual(
            button.get_attribute("title"), "Unmatched albums have no listening time"
        )
        self.assertIn(
            "Unmatched albums shown; ranked by play count.",
            self.page.locator("#toastContainer").inner_text(),
        )

    def test_matched_only_without_durations_leaves_listening_time_off(self):
        """A run with no durations at all never offers Listening Time: hiding
        the unmatched rows keeps the button disabled, with the durations
        reason."""
        self.include_run(has_durations=False)
        self.page.locator("label[for=results_albums_matched]").click()
        button = self.page.locator("#toggle-sort-playtime")
        self.assertTrue(button.is_disabled())
        self.assertEqual(
            button.get_attribute("title"), "Spotify track durations not available"
        )
        self.assertEqual(self.stats()[:2], ["3", "120"])

    def test_csv_skips_hidden_rows_and_names_the_unmatched_marker(self):
        """The CSV lists the rows on the page: an unmatched row's Provider
        column holds its marker word, and a hidden row is absent."""
        self.include_run()
        with self.page.expect_download() as shown:
            self.page.locator("#export-csv").click()
        lines = Path(shown.value.path()).read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 6)
        self.assertEqual(lines[2], '"2","Lost One","Lost One Band","45","","Not Found"')
        self.assertEqual(
            lines[4], '"4","Lost Two","Lost Two Band","35","","Unavailable"'
        )
        self.assertEqual(lines[1], '"1","Alpha","Alpha Band","50","2025-01-02",""')

        self.page.locator("label[for=results_albums_matched]").click()
        with self.page.expect_download() as hidden:
            self.page.locator("#export-csv").click()
        lines = Path(hidden.value.path()).read_text(encoding="utf-8").splitlines()
        self.assertEqual(
            [line.split(",")[1] for line in lines[1:]],
            ['"Alpha"', '"Beta"', '"Gamma"'],
        )
        self.assertEqual(
            [line.split(",")[0] for line in lines[1:]], ['"1"', '"2"', '"3"']
        )
        self.assertNotIn("Lost", "\n".join(lines))

    def release_check_run(self, albums):
        """Load results-release-checks.js into an include run's rows and answer
        its one poll with `albums`: a matched row, then three unmatched rows
        whose release cell reads "unknown"."""

        def row(name, unmatched, export, cell):
            return (
                f'<tr data-album-key="{name.lower()}|x" data-album="{name}" '
                f'data-unmatched="{unmatched}"><td class="release-date-cell" '
                f'data-export="{export}">{cell}</td></tr>'
            )

        unknown = (
            '<span class="release-date-value release-date-value--unknown">'
            "unknown</span>"
        )
        rows = row(
            "Matched",
            "",
            "2025-01-02",
            '<span class="release-date-value">2025-01</span>',
        )
        for name in ("Confirmed", "Moved", "Nothing"):
            rows += row(name, "no_spotify_match", "", unknown)
        self.page.evaluate(
            """albums => {
                window.fetch = () => Promise.resolve({
                    ok: true,
                    json: () => Promise.resolve({
                        status: 'done', checked: 3, total: 3, moved_in: 0, albums,
                    }),
                });
            }""",
            albums,
        )
        self.start(
            "results-release-checks.js",
            '<div id="release-check-bar" data-job-id="j"><span id="release-check-status">'
            '</span></div><table id="results-table"><tbody>'
            + rows
            + "</tbody></table>",
            {},
        )
        self.page.evaluate(
            "async () => { for (let i = 0; i < 20; i++) await Promise.resolve(); }"
        )

    def cell(self, name):
        """The release cell of one row: its text, export value and unknown flag."""
        return self.page.locator(
            f'tr[data-album="{name}"] .release-date-cell'
        ).evaluate(
            """cell => ({
                text: cell.querySelector('.release-date-value').textContent,
                export: cell.dataset.export,
                unknown: cell.querySelector('.release-date-value--unknown') !== null,
                note: cell.querySelector('.release-check-note') !== null,
            })"""
        )

    def test_a_finding_fills_an_unmatched_rows_unknown_release_in_place(self):
        """A confirmed or moved-out finding gives an unmatched row the date it had
        none of: YYYY-MM in the cell, the full date in data-export, and the
        unknown class gone; a moved-out one also gets the note. Nothing found
        leaves "unknown", and a confirmed matched row is untouched."""
        self.release_check_run(
            [
                {
                    "key": "matched|x",
                    "state": "confirmed",
                    "original_release_date": "2024-05-06",
                },
                {
                    "key": "confirmed|x",
                    "state": "confirmed",
                    "original_release_date": "2025-03-14",
                },
                {
                    "key": "moved|x",
                    "state": "moved_out",
                    "original_release_date": "1999-05-01",
                },
                {
                    "key": "nothing|x",
                    "state": "unavailable",
                    "original_release_date": None,
                },
            ]
        )
        self.assertEqual(
            self.cell("Confirmed"),
            {
                "text": "2025-03",
                "export": "2025-03-14",
                "unknown": False,
                "note": False,
            },
        )
        self.assertEqual(
            self.cell("Moved"),
            {"text": "1999-05", "export": "1999-05-01", "unknown": False, "note": True},
        )
        self.assertEqual(
            self.cell("Nothing"),
            {"text": "unknown", "export": "", "unknown": True, "note": False},
        )
        self.assertEqual(
            self.cell("Matched"),
            {
                "text": "2025-01",
                "export": "2025-01-02",
                "unknown": False,
                "note": False,
            },
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
