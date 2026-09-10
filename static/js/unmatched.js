// static/js/unmatched.js
// Client-side artwork hydration and disclosure for unmatched album groups.

document.addEventListener('DOMContentLoaded', () => {
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
        if (!imageUrl) return;
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

    const expanderButtons = document.querySelectorAll('.unmatched-expander-btn');
    expanderButtons.forEach((btn) => {
        btn.addEventListener('click', () => {
            const group = btn.closest('.unmatched-group');
            if (!group) return;
            const overflowRows = group.querySelectorAll('.unmatched-overflow');
            const isExpanded = btn.getAttribute('aria-expanded') === 'true';
            const total = btn.getAttribute('data-total-count') || '';

            overflowRows.forEach((row) => {
                row.classList.toggle('hidden', isExpanded);
            });

            btn.setAttribute('aria-expanded', String(!isExpanded));
            btn.textContent = isExpanded ? `Show all ${total} albums` : 'Show fewer';
        });
    });
});
