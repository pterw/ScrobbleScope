"""Every page renders and loads exactly one framework stylesheet.

WP-2 moves Bootstrap and global.css out of base.html and into a per-page
block. A page that ends up with neither loses its theme completely, and a page
that ends up with both gets a Bootstrap/daisyUI class collision. Neither shows
up in any other test, and neither is visible until someone opens the page.

The browser gate checks the two pages it can reach over HTTP. This checks all
five, including the three that need a live job to reach.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from flask import render_template

from app import create_app

BOOTSTRAP = "bootstrap"
TAILWIND = "tailwind.css"

STATIC_CSS = Path(__file__).resolve().parents[1] / "static" / "css"
INLINE_SVG = Path(__file__).resolve().parents[1] / "templates" / "inline"

#: The bar baseline docs/design/README.md "Wordmark animation" names, and the
#: value shell.css uses as transform-origin for the pulse.
BAR_BASELINE = 63.5

#: The lockup's frame. The design project's own asset uses 0 0 453 69, which
#: cuts 3.2 units off the p descender in "Scope"; the owner took the extra 5
#: units on 2026-08-24. docs/design/RECONCILIATION.md records the deviation.
LOCKUP_VIEWBOX = "0 0 453 74"

#: Tokens WP-3 adds for the index page, with the values
#: docs/design/README.md "Design tokens" gives them. Single-value entries are
#: theme-independent and live in @theme static; pairs are (light, dark) and
#: live in the two daisyUI theme blocks.
INDEX_TOKENS = {
    "--radius-xs": ("4px",),
    "--radius-md": ("10px",),
    "--rocket-5": ("#f0903a",),
    "--ss-text-body": ("#4a4456", "#c5bfb1"),
    "--ss-text-muted": ("#6f6a7a", "#908a9a"),
    "--ss-border-default": ("#e5dfd1", "#2a2434"),
    "--ss-accent-soft": ("#efe9fa", "#2a1f44"),
    "--heatmap-empty": ("#e8e2d6", "#262230"),
}

#: Minimum context each template needs to render at all. The values are never
#: asserted on; they exist so Jinja can finish.
TEMPLATE_CONTEXT = {
    "index.html": {},
    "error.html": {},
    "loading.html": {
        "job_id": "job-1",
        "username": "someone",
        "year": "2024",
        "sort_by": "plays",
        "release_scope": "any",
        "decade": "",
        "release_year": "",
    },
    "results.html": {
        "job_id": "job-1",
        "username": "someone",
        "year": "2024",
    },
    "unmatched.html": {"reasons": {}},
}

#: Pages migrated to Tailwind. Every other page must still carry Bootstrap.
MIGRATED = {"error.html"}


@pytest.fixture
def app():
    """The application, for rendering templates outside a request."""
    application = create_app()
    application.config["TESTING"] = True
    return application


def _stylesheets(html: str) -> list[str]:
    """Return the href of every stylesheet link in the rendered page."""
    return re.findall(r'<link[^>]+rel="stylesheet"[^>]+href="([^"]+)"', html)


def _local_sheets(hrefs: list[str]) -> list[Path]:
    """Return the repository file behind every href that names a local sheet."""
    names = [href.rsplit("/", 1)[-1] for href in hrefs if "//" not in href]
    return [STATIC_CSS / name for name in names]


def _without_comments(text: str) -> str:
    """Return the stylesheet with every /* */ block removed.

    Both directions need this. A comment that names a token must not count as
    a definition, and prose that mentions var(--x) must not count as a read.
    """
    return re.sub(r"/\*.*?\*/", " ", text, flags=re.S)


def _declared(text: str) -> set[str]:
    """Return every custom property the stylesheet defines."""
    return set(re.findall(r"^\s*(--[\w-]+)\s*:", text, re.M))


def _read_without_fallback(text: str) -> set[str]:
    """Return every custom property the stylesheet reads with no fallback.

    A var() that carries a fallback still resolves when the token is absent,
    so only the bare form can break a declaration.
    """
    return {
        token
        for token, following in re.findall(r"var\(\s*(--[\w-]+)\s*(.?)", text)
        if following != ","
    }


@pytest.mark.parametrize("template", sorted(TEMPLATE_CONTEXT))
def test_every_page_loads_exactly_one_framework_stylesheet(app, template):
    """Two frameworks collide on .btn and .card; none strips the page's theme."""
    with app.test_request_context("/"):
        html = render_template(template, **TEMPLATE_CONTEXT[template])

    sheets = _stylesheets(html)
    bootstrap = [href for href in sheets if BOOTSTRAP in href.lower()]
    tailwind = [href for href in sheets if TAILWIND in href.lower()]

    assert len(bootstrap + tailwind) == 1, (
        f"{template} loads {len(bootstrap + tailwind)} framework stylesheets: "
        f"{bootstrap + tailwind}"
    )


@pytest.mark.parametrize("template", sorted(TEMPLATE_CONTEXT))
def test_each_page_loads_the_framework_its_markup_is_written_for(app, template):
    """A migrated page must not silently fall back to the legacy stack."""
    with app.test_request_context("/"):
        html = render_template(template, **TEMPLATE_CONTEXT[template])

    sheets = " ".join(_stylesheets(html)).lower()
    if template in MIGRATED:
        assert TAILWIND in sheets and BOOTSTRAP not in sheets
    else:
        assert BOOTSTRAP in sheets and TAILWIND not in sheets


@pytest.mark.parametrize("template", sorted(TEMPLATE_CONTEXT))
def test_every_page_carries_the_shared_shell(app, template):
    """The header bar and its stylesheet are on every page, migrated or not."""
    with app.test_request_context("/"):
        html = render_template(template, **TEMPLATE_CONTEXT[template])

    assert "css/shell.css" in html
    assert 'class="site-header"' in html
    # The frontend gate clicks .first, so a second match would silently decide
    # which control it drives.
    assert html.count("data-theme-toggle") == 1


@pytest.mark.parametrize("template", sorted(TEMPLATE_CONTEXT))
def test_every_custom_property_a_page_reads_is_defined_by_a_sheet_it_loads(
    app, template
):
    """An undefined var() with no fallback voids the whole declaration.

    It fails silently: no console error, no failing request, just a rule that
    stops applying. Tailwind emits a theme variable only when a generated
    utility uses it, so five tokens error.css reads were pruned out of the
    compiled sheet and the card lost its rounding. @theme static fixes that;
    this proves it, for every page rather than only the one that broke.

    The sheets are read back from the rendered page, so a template that starts
    or stops loading one is covered without editing this test. Bootstrap is a
    CDN file and is not checked; a var() it owns fails here, which is the
    right answer for a token the repository cannot see.

    Only handwritten sheets are checked as readers. tailwind.css is generated,
    and daisyUI leaves one dangling var() of its own in it -- .btn reads
    --fx-noise, which its suppressed :root block would have defined. That one
    is harmless, because the layer it paints is sized by --noise and every
    theme sets --noise to 0. Upstream quirks are not this test's business.
    """
    with app.test_request_context("/"):
        html = render_template(template, **TEMPLATE_CONTEXT[template])

    sheets = _local_sheets(_stylesheets(html))
    assert sheets, f"{template} loads no local stylesheet"

    texts = [_without_comments(sheet.read_text(encoding="utf-8")) for sheet in sheets]
    defined = set().union(*(_declared(text) for text in texts))

    for sheet, text in zip(sheets, texts):
        if sheet.name == TAILWIND:
            continue
        undefined = sorted(_read_without_fallback(text) - defined)
        assert not undefined, (
            f"{template} loads {sheet.name}, which reads {undefined} "
            f"with no fallback and no definition in "
            f"{sorted(other.name for other in sheets)}"
        )


@pytest.mark.parametrize("template", sorted(TEMPLATE_CONTEXT))
def test_no_page_carries_smil_animation(app, template):
    """CSS cannot stop SMIL, so prefers-reduced-motion never reaches it.

    An <animate> or <animateTransform> with repeatCount="indefinite" ignores
    the media query entirely. WP-2 stripped it from the header lockup and
    scoped this check to the header, because the full wordmark and the
    pinwheel still carried it. WP-3 strips both, so the check now covers the
    whole rendered page. All motion is shell.css keyframes.
    """
    with app.test_request_context("/"):
        html = render_template(template, **TEMPLATE_CONTEXT[template])

    assert (
        "<animate" not in html
    ), f"{template} ships SMIL, which no CSS media query can pause"


@pytest.mark.parametrize("template", sorted(TEMPLATE_CONTEXT))
def test_every_inline_mark_is_wrapped_for_the_css_animation(app, template):
    """Stripping SMIL without a wrapper leaves a mark that never moves.

    The animation rules key on .ss-mark, so a page that includes the
    wordmark and forgets the class loses the motion silently -- there is no
    error and the page still renders. Every page carries the header lockup,
    so every page must have at least one.
    """
    with app.test_request_context("/"):
        html = render_template(template, **TEMPLATE_CONTEXT[template])

    marks = html.count("ss-mark")
    bar_groups = html.count('id="horizontal_bars"')

    assert marks == bar_groups, (
        f"{template} renders {bar_groups} bar group(s) but {marks} ss-mark "
        f"wrapper(s); an unwrapped mark is frozen with no error"
    )


def test_shell_animates_the_pinwheel_and_reduced_motion_stops_it():
    """The pinwheel's SMIL is gone, so shell.css owns every part of it.

    Five animations were removed: one rotor spin and four blade extensions.
    All five need a CSS replacement, and all five need cancelling under
    reduced motion. A missing keyframe set is invisible -- the blade simply
    sits still while the others move.
    """
    shell = (STATIC_CSS / "shell.css").read_text(encoding="utf-8")
    reduced = shell.split("@media (prefers-reduced-motion: reduce)", 1)[1]

    for name in (
        "ss-pinwheel-spin",
        "ss-pinwheel-blade-right",
        "ss-pinwheel-blade-left",
        "ss-pinwheel-blade-up",
        "ss-pinwheel-blade-down",
    ):
        assert f"@keyframes {name}" in shell, f"shell.css has no {name} keyframes"

    # Matched as whole selectors, not substrings. ".ss-pinwheel svg > g" is a
    # prefix of ".ss-pinwheel svg > g > g", so a substring check would pass on
    # the blade rule alone and never fail for a missing rotor rule.
    cancelled = _selectors_that_cancel_animation(reduced)

    assert (
        ".ss-pinwheel svg > g" in cancelled
    ), f"reduced motion does not stop the pinwheel rotor; cancels {cancelled}"
    assert (
        ".ss-pinwheel svg > g > g" in cancelled
    ), f"reduced motion does not stop the pinwheel blades; cancels {cancelled}"


@pytest.mark.parametrize("token", sorted(INDEX_TOKENS))
def test_the_index_tokens_survive_the_tailwind_build(token):
    """These land a commit before the markup that reads them.

    Tailwind v4 emits a theme variable only when a generated utility uses it,
    and an undefined var() with no fallback voids the whole declaration, so a
    pruned token means a rule in commit 4 silently does not apply.

    The two sources behave differently, which was measured rather than
    assumed. Dropping the static keyword from @theme prunes exactly three of
    these -- --radius-xs, --radius-md and --rocket-5, the ones that live in
    that block and that nothing uses yet. The other five sit in the two
    daisyUI theme blocks, which daisyUI emits directly, so Tailwind's
    usage-based pruning never reaches them. Put a token nothing reads in
    @theme and it needs the static keyword; put it in a theme block and it
    does not.

    Asserted against the compiled stylesheet, not the source. The source only
    says what was asked for; the build says what shipped.
    """
    compiled = (STATIC_CSS / TAILWIND).read_text(encoding="utf-8")
    emitted = [
        value.strip()
        for value in re.findall(rf"{re.escape(token)}:\s*([^;]+);", compiled)
    ]

    assert emitted, f"{token} was pruned out of the compiled stylesheet"
    for expected in INDEX_TOKENS[token]:
        assert any(
            expected.lower() == value.lower() for value in emitted
        ), f"{token} should carry {expected}; the build emitted {emitted}"


def test_the_font_size_scale_is_not_shadowed_by_a_colour():
    """--text-* is Tailwind's font-size namespace, not a colour namespace.

    The design calls its body and muted colours --text-body and --text-muted.
    Adding them under those names would collide: --text-body: 1rem already
    exists in @theme static, .text-body is generated as
    font-size: var(--text-body), and a colour of the same name emitted under
    [data-theme] wins on specificity. The utility would then set a font size
    to a hex string and quietly do nothing. That is why the four colour
    tokens carry an ss- prefix.
    """
    compiled = (STATIC_CSS / TAILWIND).read_text(encoding="utf-8")

    for size_token in ("--text-body", "--text-label", "--text-display"):
        values = re.findall(rf"{re.escape(size_token)}:\s*([^;]+);", compiled)
        assert values, f"{size_token} is missing from the compiled sheet"
        for value in values:
            assert "#" not in value, (
                f"{size_token} resolves to {value.strip()}, a colour. A theme "
                f"block has shadowed the font-size scale."
            )


def test_the_pinwheel_keeps_the_shape_its_selectors_assume():
    """The CSS targets the blades structurally, so the shape is the contract.

    scrobblescope_pinwheel.svg has no class or id on its groups, and this WP
    deliberately added none. shell.css therefore selects one rotor group and
    four blade groups by nth-of-type, in the source order right, left, up,
    down. A re-cut asset with a different group count would animate the wrong
    things, or nothing, without any error.
    """
    svg = (INLINE_SVG / "scrobblescope_pinwheel.svg").read_text(encoding="utf-8")

    assert (
        svg.count("<g>") == 5
    ), f"expected one rotor and four blade groups, found {svg.count('<g>')}"
    # Counted as an attribute: the bare name also appears in the <style>
    # rule that colours them, so a plain substring count returns five.
    assert svg.count('class="pinwheel-blade"') == 4, "expected exactly four blades"


@pytest.mark.parametrize("template", sorted(TEMPLATE_CONTEXT))
def test_every_page_wraps_its_footer_extras(app, template):
    """The wrapper centres and spaces whatever a page adds after the content.

    Asserting the exact empty markup does double duty. It proves base.html
    still emits the wrapper, and it proves the tags stay on one line --
    `.page-footer-extras:empty` is what collapses the wrapper on the pages
    that add nothing, and a newline between the tags is a text node that
    stops :empty matching.
    """
    with app.test_request_context("/"):
        html = render_template(template, **TEMPLATE_CONTEXT[template])

    if template == "results.html":
        wrapper = html.split('<div class="page-footer-extras">', 1)[1]
        assert 'id="back-to-top"' in wrapper.split("</div>", 1)[0]
    else:
        assert '<div class="page-footer-extras"></div>' in html


def test_shell_stops_both_animations_under_reduced_motion():
    """Both rules are load-bearing and neither is obvious from its selector.

    The bar rule is the whole reason the SMIL was stripped. The footer rule
    restores opacity: cancelling a forwards animation that fades in from 0
    would otherwise hide the control permanently.
    """
    shell = (STATIC_CSS / "shell.css").read_text(encoding="utf-8")
    reduced = shell.split("@media (prefers-reduced-motion: reduce)", 1)[1]

    assert "#horizontal_bars path:nth-of-type(-n+5)" in reduced
    assert "opacity: 1;" in reduced


def _selectors_that_cancel_animation(css: str) -> set[str]:
    """Return every selector in a rule whose body sets animation: none.

    Comments are stripped first. Prose contains commas, so an unstripped
    comment splits into fragments that land in the result set and could
    satisfy a membership check without any rule existing.
    """
    return {
        selector.strip()
        for selectors, body in re.findall(
            r"([^{}]+)\{([^{}]*)\}", _without_comments(css)
        )
        if "animation: none" in body
        for selector in selectors.split(",")
        if selector.strip()
    }


def _lockup() -> str:
    """The header lockup markup."""
    return (INLINE_SVG / "scrobble_scope_lockup_inline.svg").read_text(encoding="utf-8")


def _bar_feet(svg: str) -> list[float]:
    """Return where each vertical bar path ends, in SVG user units."""
    return [
        round(float(top) + float(length), 2)
        for _x, top, length in re.findall(r'd="M([\d.]+),([\d.]+)v([\d.]+)"', svg)
    ]


def test_the_lockup_bars_share_the_baseline_shell_css_scales_from():
    """Each bar must end at 63.50 or it pulses from the wrong foot.

    shell.css pins transform-origin to 0 63.5px for all five at once. The
    bars used to end between 63.46 and 63.70, so each one drifted a little
    as it scaled. Nothing rendered wrongly enough to notice, which is why a
    test holds it now.
    """
    feet = _bar_feet(_lockup())

    assert len(feet) == 5, f"expected five bars, found {len(feet)}"
    assert set(feet) == {BAR_BASELINE}, f"bars end at {sorted(set(feet))}"


def test_the_lockup_seats_its_letterforms_on_the_bar_baseline():
    """Without the transform the word floats above the bars.

    The lockup drops the tagline that the bars used to descend alongside, so
    the letterforms need seating on the bar baseline. This is a static
    attribute -- geometry, not motion. The letterforms never animate, which
    docs/design/README.md "Wordmark animation" requires.
    """
    group = re.search(r'<g id="logo-text"[^>]*>', _lockup())

    assert group is not None, "the lockup has no #logo-text group"
    assert "transform=" in group.group(
        0
    ), "#logo-text lost its transform, so the word floats above the bars"
    assert "scale(1.1)" in group.group(0)


def test_the_lockup_frame_keeps_the_whole_descender():
    """A clipped descender is invisible to every other gate.

    The design project's own lockup uses 0 0 453 69 and cuts the p in
    "Scope". Nothing else here would catch that, so the frame is pinned.
    """
    assert f'viewBox="{LOCKUP_VIEWBOX}"' in _lockup()


@pytest.mark.parametrize("template", sorted(TEMPLATE_CONTEXT))
def test_every_page_sets_the_theme_before_first_paint(app, template):
    """The marker must be on <html>, and set in head, or the page flashes."""
    with app.test_request_context("/"):
        html = render_template(template, **TEMPLATE_CONTEXT[template])

    assert 'data-theme="light"' in html
    head = html.split("</head>")[0]
    assert "localStorage.getItem('darkMode')" in head
    assert "use.typekit.net/rwy8ghw.css" in head
