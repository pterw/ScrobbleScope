"""Form checks: validation feedback, validator failures and races, visibility.

A slice of the frontend gate (F-B21-51). These checks drive the index form
through real clicks and intercepted validator requests, because the failure
they guard against is a stale or lost verdict that only a real request order
can produce.
"""

from __future__ import annotations

from scripts.dev._frontend_gate_shared import _reach_state

#: What must be invisible when a migrated page first loads. The scripts reveal
#: each one later.
#:
#: A class name is not evidence. `.index-grid` set display:grid and outranked
#: Tailwind's `.hidden`, so the heatmap rendered under a hero that never left,
#: and a probe asserting className passed anyway. Assert the computed value.
HIDDEN_ON_LOAD = {
    "/": (
        "#heatmap-form-section",
        "#heatmap-loading",
        "#heatmap-result",
        "#heatmap-result-headline",
        "#heatmap-result-frame",
        "#heatmap-error",
        "#decade_dropdown",
        "#release_year_group",
    ),
}


def check_validation_feedback(page, base_url: str) -> list[str]:
    """Typing clears a validation message that is already on screen.

    Bootstrap's .invalid-feedback was hidden unless a sibling carried
    .is-invalid, so dropping that class hid stale text for free. The
    replacement .field__error hides only while it is empty, so every script
    that writes into one has to empty it again. Both did not, and a rejected
    username stayed on screen while the reader typed a new one and after a
    valid one resolved -- a green field and a red error at once.

    No network call. The check writes a message into the node itself, which is
    exactly the state a rejection leaves behind, then types one real character
    and asks whether the handler cleared it. /validate_user needs a live
    Last.fm key, and a gate that needs a secret does not run in CI.
    """
    # The heatmap field lives in a panel that starts hidden, so its tab has to
    # be clicked before anything can be typed into it.
    fields = (
        ("/", "#username", ()),
        ("/", "#heatmap-username", (("click", "#mode-tab-heatmap"),)),
    )
    failures = []
    for path, selector, actions in fields:
        page.goto(f"{base_url}{path}", wait_until="load")
        _reach_state(page, actions)
        node = page.evaluate(
            """(selector) => {
                const input = document.querySelector(selector);
                if (!input) return 'no such input';
                const error = input.parentNode.querySelector('.field__error');
                if (!error) return 'no .field__error beside it';
                error.textContent = 'Username not found on Last.fm.';
                return null;
            }""",
            selector,
        )
        if node:
            failures.append(f"{path} {selector}: {node}")
            continue

        # A real keystroke. A dispatched event can reach a listener that a
        # person never could, which is the opposite of what this proves.
        page.locator(selector).type("a")
        left = page.evaluate(
            """(selector) => document.querySelector(selector)
                .parentNode.querySelector('.field__error').textContent""",
            selector,
        )
        if left:
            failures.append(
                f"{path} {selector}: typing left the message {left!r} on screen"
            )
    return failures


def check_private_profile_is_blocked(page, base_url: str) -> list[str]:
    """A private-profile verdict blocks both forms on the index before submit.

    The backend owns the Last.fm error-17 classification. This browser check
    supplies that result at the network boundary and proves the shared index
    validation UI turns it into an actionable message and native form block.
    """
    fields = (
        ("/", "#username", ()),
        ("/", "#heatmap-username", (("click", "#mode-tab-heatmap"),)),
    )
    message = (
        "This Last.fm profile is private. Make recent listening public and try again."
    )
    failures = []
    page.route(
        "**/validate_user*",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=f'{{"valid": false, "message": "{message}"}}',
        ),
    )
    try:
        for path, selector, actions in fields:
            page.goto(f"{base_url}{path}", wait_until="load")
            _reach_state(page, actions)
            page.locator(selector).type("private_profile")
            page.locator(selector).blur()
            page.wait_for_function(
                """(selector) => {
                    const input = document.querySelector(selector);
                    return input && !input.checkValidity();
                }""",
                arg=selector,
            )
            state = page.evaluate(
                """(selector) => {
                    const input = document.querySelector(selector);
                    const error = input.parentNode.querySelector('.field__error');
                    return {
                        blocked: !input.checkValidity(),
                        message: error ? error.textContent.trim() : '',
                    };
                }""",
                selector,
            )
            if not state["blocked"]:
                failures.append(f"{path} {selector}: private profile can submit")
            if state["message"] != message:
                failures.append(
                    f"{path} {selector}: private-profile message is {state['message']!r}"
                )
    finally:
        page.unroute("**/validate_user*")
    return failures


def check_validator_outage_is_recoverable(page, base_url: str) -> list[str]:
    """A failing validator does not lock the form it was meant to help.

    /validate_user answers a Last.fm outage with 503 and {"valid": false,
    "Validation service unavailable. Try again."}. Read as a verdict about the
    username, that sets a custom validity error, and then trying again is the
    one thing the message asks for that cannot work -- the heatmap form
    refuses at its own submit guard and the index form refuses at native
    validation, since only the heatmap form carries novalidate.

    The route is stubbed rather than called. A real 503 needs Last.fm to be
    down, and a gate that needs a secret does not run in CI.
    """
    fields = (
        ("/", "#username", ()),
        ("/", "#heatmap-username", (("click", "#mode-tab-heatmap"),)),
    )
    failures = []
    page.route(
        "**/validate_user*",
        lambda route: route.fulfill(
            status=503,
            content_type="application/json",
            body='{"valid": false, "message": "Validation service unavailable."}',
        ),
    )
    try:
        for path, selector, actions in fields:
            page.goto(f"{base_url}{path}", wait_until="load")
            _reach_state(page, actions)
            page.locator(selector).type("someone")
            page.locator(selector).blur()
            page.wait_for_timeout(600)
            state = page.evaluate(
                """(selector) => {
                    const input = document.querySelector(selector);
                    const error = input.parentNode.querySelector('.field__error');
                    return {
                        blocked: !input.checkValidity(),
                        told: error ? error.textContent.trim() : '',
                    };
                }""",
                selector,
            )
            if state["blocked"]:
                failures.append(
                    f"{path} {selector}: a 503 left the field refusing to submit, "
                    f"so the reader cannot do what it tells them"
                )
            if not state["told"]:
                failures.append(f"{path} {selector}: a 503 said nothing to the reader")
    finally:
        page.unroute("**/validate_user*")
    return failures


def _collecting_handler(sink: list) -> callable:
    """Return a one-parameter route handler that appends into ``sink``.

    Playwright inspects the handler's parameter count: one parameter means
    it is called with the route alone, two means (route, request). A
    ``lambda route, pending=pending: ...`` therefore has its ``pending``
    default overridden by the request object at call time -- the CI failure
    ``'Request' object has no attribute 'append'``. A factory closure binds
    the list without a second parameter, which also satisfies bugbear B023
    (no loop-variable capture) without that breakage.
    """

    def handler(route):
        sink.append(route)

    return handler


def check_stale_validator_failure_is_discarded(page, base_url: str) -> list[str]:
    """An older failed request cannot clear a newer same-name verdict.

    Two blur validations can overlap because an earlier fetch stays in flight;
    the album form's debounce cancels only work that has not started. A value
    comparison handles A then B, but not A then B then A: both requests name
    A. If the newer A is rejected first and the older A then fails, only
    request identity can keep the older catch from clearing current validity.
    """
    fields = (
        ("/", "#username", ()),
        ("/", "#heatmap-username", (("click", "#mode-tab-heatmap"),)),
    )
    failures = []
    for path, selector, actions in fields:
        pending = []
        handled = []
        page.route("**/validate_user*", _collecting_handler(pending))
        try:
            page.goto(f"{base_url}{path}", wait_until="load")
            _reach_state(page, actions)
            field = page.locator(selector)

            field.fill("repeated-request")
            field.blur()
            page.wait_for_timeout(400)
            field.fill("temporary-request")
            field.fill("repeated-request")
            field.blur()
            page.wait_for_timeout(400)
            if len(pending) != 2:
                failures.append(
                    f"{path} {selector}: expected two overlapping validations, "
                    f"held {len(pending)}"
                )
                continue

            pending[1].fulfill(
                status=404,
                content_type="application/json",
                body='{"valid": false, "message": "Newer username is invalid."}',
            )
            handled.append(pending[1])
            page.wait_for_function(
                "(selector) => !document.querySelector(selector).checkValidity()",
                arg=selector,
            )

            pending[0].abort("failed")
            handled.append(pending[0])
            page.wait_for_timeout(100)
            if page.locator(selector).evaluate("input => input.checkValidity()"):
                failures.append(
                    f"{path} {selector}: the older same-name failure cleared "
                    f"the newer invalid verdict"
                )
        finally:
            for route in pending:
                if route not in handled:
                    route.abort("failed")
            page.unroute("**/validate_user*")
    return failures


def check_current_validator_failure_replaces_old_verdict(
    page, base_url: str
) -> list[str]:
    """A current network failure cannot leave an older invalid verdict visible."""
    fields = (
        ("/", "#username", ()),
        ("/", "#heatmap-username", (("click", "#mode-tab-heatmap"),)),
    )
    failures = []
    for path, selector, actions in fields:
        pending = []
        handled = []
        page.route("**/validate_user*", _collecting_handler(pending))
        try:
            page.goto(f"{base_url}{path}", wait_until="load")
            _reach_state(page, actions)
            field = page.locator(selector)

            field.fill("same-request")
            field.blur()
            page.wait_for_timeout(400)
            if len(pending) != 1:
                failures.append(
                    f"{path} {selector}: expected the first validation, held "
                    f"{len(pending)}"
                )
                continue
            pending[0].fulfill(
                status=404,
                content_type="application/json",
                body='{"valid": false, "message": "Initial username is invalid."}',
            )
            handled.append(pending[0])
            page.wait_for_function(
                "(selector) => !document.querySelector(selector).checkValidity()",
                arg=selector,
            )

            field.focus()
            field.blur()
            page.wait_for_timeout(400)
            if len(pending) != 2:
                failures.append(
                    f"{path} {selector}: expected a same-name retry, held "
                    f"{len(pending)} validations"
                )
                continue
            pending[1].abort("failed")
            handled.append(pending[1])
            page.wait_for_timeout(100)
            state = field.evaluate(
                """input => ({
                    blocked: !input.checkValidity(),
                    invalidClass: input.classList.contains('is-invalid'),
                    told: input.parentNode.querySelector('.field__error')
                        .textContent.trim(),
                })"""
            )
            if state["blocked"]:
                failures.append(
                    f"{path} {selector}: a network failure blocked submission"
                )
            if state["invalidClass"]:
                failures.append(
                    f"{path} {selector}: a network failure left the old invalid style"
                )
            if "unavailable" not in state["told"].lower():
                failures.append(
                    f"{path} {selector}: a network failure left stale feedback "
                    f"{state['told']!r}"
                )
        finally:
            for route in pending:
                if route not in handled:
                    route.abort("failed")
            page.unroute("**/validate_user*")
    return failures


def check_true_warning_survives(page, base_url: str) -> list[str]:
    """Editing the username does not wipe a year warning that is still true.

    The complement of the check above, and the harder half to keep right.
    Clearing the last account's state has to take its error message with it:
    "This user joined Last.fm in 2015" is a claim about an account nobody is
    asking about any more. The obvious fix is to clear the year message
    outright, and that is wrong -- "Year cannot be in the future" is about
    the year, not the account, and has to survive.

    So the handler re-derives instead of clearing, and this proves the half a
    reader would not notice was broken: the message stays. No network call.
    A future year is refused by the year field alone.
    """
    page.goto(f"{base_url}/", wait_until="load")
    page.locator("#year").fill("")
    page.locator("#year").type("2099")
    before = _year_warning(page)
    if "future" not in before.lower():
        return [f"/ #year: 2099 did not raise a future-year warning, got {before!r}"]

    page.locator("#username").type("a")
    after = _year_warning(page)
    if after != before:
        return [
            f"/ #username: typing changed a year warning it does not own, "
            f"{before!r} -> {after!r}"
        ]
    return []


def _year_warning(page) -> str:
    """The text of the warning the year field writes beside itself."""
    return page.evaluate(
        """() => {
            const year = document.querySelector('#year');
            const error = year && year.parentNode.querySelector('.field__error');
            return error && error.style.display !== 'none'
                ? error.textContent
                : '';
        }"""
    )


def check_initial_visibility(page, base_url: str) -> list[str]:
    """Everything a script reveals later is really invisible on load.

    Computed display, not a class name. `.index-grid { display: grid }` beat
    Tailwind's `.hidden` because a page stylesheet loads after tailwind.css and
    wins at equal specificity, so the heatmap rendered below a hero that was
    supposed to be gone. A probe that asserted the class name passed.
    """
    failures = []
    for path, selectors in HIDDEN_ON_LOAD.items():
        page.goto(f"{base_url}{path}", wait_until="load")
        for selector in selectors:
            state = page.evaluate(
                """(selector) => {
                    const node = document.querySelector(selector);
                    if (!node) return null;
                    return getComputedStyle(node).display;
                }""",
                selector,
            )
            if state is None:
                failures.append(f"{path}: {selector} is not in the page at all")
            elif state != "none":
                failures.append(
                    f"{path}: {selector} should start hidden but computes "
                    f"display: {state}"
                )
    return failures
