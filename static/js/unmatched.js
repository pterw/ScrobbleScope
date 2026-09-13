// static/js/unmatched.js
// Client-side artwork hydration, Results scaling, and disclosure for unmatched album groups.

document.addEventListener('DOMContentLoaded', () => {
    const unmatchedPage = document.querySelector('.unmatched-page');

    /** Scale the bounded Results composition from its authored rem baseline. */
    function syncResultsScale() {
        if (!unmatchedPage) return;
        const rootSize = parseFloat(getComputedStyle(document.documentElement).fontSize);
        const baseRem = parseFloat(getComputedStyle(unmatchedPage).getPropertyValue('--results-base-rem')) || 75;
        const baseWidth = rootSize * baseRem;
        if (!(baseWidth > 0)) return;
        const scale = Math.max(1, unmatchedPage.getBoundingClientRect().width / baseWidth);
        unmatchedPage.style.setProperty('--results-scale', String(scale));
    }

    if (unmatchedPage) {
        syncResultsScale();
        if ('ResizeObserver' in window) {
            new ResizeObserver(syncResultsScale).observe(unmatchedPage);
        }
        window.addEventListener('resize', syncResultsScale);
    }

    const artistImageRequests = new Map();

    /** Fetch one artist portrait per normalized name through the shared API. */
    function fetchArtistImage(artistName) {
        const key = artistName.trim().toLocaleLowerCase();
        if (!artistImageRequests.has(key)) {
            const request = fetch(`/api/artist_spotlight?artist=${encodeURIComponent(artistName)}`)
                .then(response => response.ok ? response.json() : null)
                .then(data => data?.image_url || null)
                .catch(() => null);
            artistImageRequests.set(key, request);
        }
        return artistImageRequests.get(key);
    }

    /** Replace an initials fallback only after its artist portrait has loaded. */
    async function hydrateArtistImage(artwork) {
        const artistName = artwork.dataset.artistName?.trim();
        const image = artwork.querySelector('.unmatched-artist-image');
        const fallback = artwork.querySelector('.unmatched-artwork-fallback');
        if (!artistName || !image || !fallback || artwork.dataset.hydrated) return;
        artwork.dataset.hydrated = 'true';

        const imageUrl = await fetchArtistImage(artistName);
        if (!imageUrl || artwork.dataset.artistName?.trim() !== artistName) return;
        image.addEventListener('load', () => {
            image.alt = `${artistName} artist portrait`;
            image.style.display = 'block';
            fallback.style.display = 'none';
        }, { once: true });
        image.src = imageUrl;
    }

    /** Defer remote portraits until their rows enter the viewport. */
    function observeArtistImages() {
        const artworks = document.querySelectorAll('[data-artist-image]');
        if (!('IntersectionObserver' in window)) {
            artworks.forEach(hydrateArtistImage);
            return;
        }
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) return;
                observer.unobserve(entry.target);
                hydrateArtistImage(entry.target);
            });
        }, { rootMargin: '100px' });
        artworks.forEach(artwork => observer.observe(artwork));
    }

    observeArtistImages();

    const groups = document.querySelectorAll('.unmatched-group');
    groups.forEach((group) => {
        const expanderBtn = group.querySelector('.unmatched-expander-btn');
        const backToTopBtn = group.querySelector('.unmatched-back-to-top-btn');
        if (!expanderBtn) return;

        const total = parseInt(expanderBtn.getAttribute('data-total-count'), 10) || 0;
        const step = parseInt(expanderBtn.getAttribute('data-step'), 10) || 25;
        const initial = parseInt(expanderBtn.getAttribute('data-initial'), 10) || 10;
        let visibleCount = initial;

        /**
         * Reveal exactly `count` rows and put the button into the state that the
         * count implies. One writer for the row visibility, the button label and
         * `aria-expanded`, so the expander and the back-to-top control cannot
         * drift apart the way two copies of this logic would.
         */
        function applyVisibleCount(count, isCollapsed) {
            visibleCount = count;
            const rows = group.querySelectorAll('.results-table tbody tr');
            rows.forEach((row, idx) => {
                row.classList.toggle('hidden', idx >= count);
            });

            const remaining = total - count;
            if (count >= total) {
                expanderBtn.textContent = 'Show fewer';
                expanderBtn.setAttribute('aria-expanded', 'true');
                return;
            }
            if (remaining <= step) {
                expanderBtn.textContent = isCollapsed
                    ? `Show all ${total} albums`
                    : `Show remaining ${remaining} albums`;
            } else {
                expanderBtn.textContent = `Show next ${step} (${remaining} remaining)`;
            }
            expanderBtn.setAttribute('aria-expanded', 'false');
        }

        expanderBtn.addEventListener('click', () => {
            if (visibleCount >= total) {
                applyVisibleCount(initial, true);
                group.scrollIntoView({ behavior: 'smooth', block: 'start' });
                return;
            }
            applyVisibleCount(Math.min(visibleCount + step, total), false);
        });

        if (backToTopBtn) {
            // Owner ruling, 2026-09-11: returning to the top also collapses the
            // report, so the reader is not left above a table padded with rows
            // they had just revealed.
            backToTopBtn.addEventListener('click', () => {
                applyVisibleCount(initial, true);
                group.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
        }
    });
});
