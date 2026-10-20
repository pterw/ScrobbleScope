/** Keep same-origin page navigation continuous without delaying modified links. */
(function () {
    'use strict';
    let leaving = false;

    /** Restore visibility on initial load and browser back/forward restoration. */
    function revealPage() {
        leaving = false;
        document.body.classList.remove('is-leaving');
        document.body.classList.add('is-ready');
    }

    /** Fade the current content before following a normal in-app link. */
    function followLink(event) {
        if (event.defaultPrevented || event.button !== 0 || event.metaKey ||
            event.ctrlKey || event.shiftKey || event.altKey) return;
        const link = event.target.closest('a[href]');
        if (!link || link.hasAttribute('download') ||
            (link.target && link.target !== '_self')) return;
        const target = new URL(link.href, location.href);
        if (target.origin !== location.origin ||
            !['http:', 'https:'].includes(target.protocol) ||
            (target.pathname === location.pathname && target.search === location.search)) return;
        if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
        event.preventDefault();
        if (leaving) return;
        leaving = true;
        document.body.classList.add('is-leaving');
        // A bounded timer also navigates if animation events are suppressed.
        window.setTimeout(() => location.assign(target.href), 140);
    }

    document.addEventListener('DOMContentLoaded', revealPage);
    window.addEventListener('pageshow', revealPage);
    document.addEventListener('click', followLink);
}());
