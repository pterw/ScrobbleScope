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
        const step = parseInt(expanderBtn.getAttribute('data-step'), 10) || 50;
        const initial = parseInt(expanderBtn.getAttribute('data-initial'), 10) || 10;
        let visibleCount = initial;

        expanderBtn.addEventListener('click', () => {
            const rows = group.querySelectorAll('.results-table tbody tr');
            if (visibleCount >= total) {
                // Currently fully expanded, collapse back to initial 10
                visibleCount = initial;
                rows.forEach((row, idx) => {
                    row.classList.toggle('hidden', idx >= initial);
                });
                const remaining = total - initial;
                if (remaining <= step) {
                    expanderBtn.textContent = `Show all ${total} albums`;
                } else {
                    expanderBtn.textContent = `Show next ${step} (${remaining} remaining)`;
                }
                expanderBtn.setAttribute('aria-expanded', 'false');
                group.scrollIntoView({ behavior: 'smooth', block: 'start' });
                return;
            }

            visibleCount = Math.min(visibleCount + step, total);
            rows.forEach((row, idx) => {
                row.classList.toggle('hidden', idx >= visibleCount);
            });

            if (visibleCount >= total) {
                expanderBtn.textContent = 'Show fewer';
                expanderBtn.setAttribute('aria-expanded', 'true');
            } else {
                const remaining = total - visibleCount;
                if (remaining <= step) {
                    expanderBtn.textContent = `Show remaining ${remaining} albums`;
                } else {
                    expanderBtn.textContent = `Show next ${step} (${remaining} remaining)`;
                }
                expanderBtn.setAttribute('aria-expanded', 'false');
            }
        });

        if (backToTopBtn) {
            backToTopBtn.addEventListener('click', () => {
                group.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
        }
    });
});
