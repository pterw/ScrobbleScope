// Artist spotlight presentation, hydration and rotation are independent of exports.
document.addEventListener('DOMContentLoaded', () => {
    function formatDurationMobile(seconds) {
        seconds = Math.ceil(seconds);
        if (seconds < 60) return `${seconds}s`;
        const minutes = Math.floor(seconds / 60);
        const secRem = seconds % 60;
        if (minutes < 60) {
            return secRem > 0 ? `${minutes}m ${secRem}s` : `${minutes}m`;
        }
        const hours = Math.floor(minutes / 60);
        const minRem = minutes % 60;
        if (hours < 24) {
            return minRem > 0 ? `${hours}h ${minRem}m` : `${hours}h`;
        }
        const days = Math.floor(hours / 24);
        const hourRem = hours % 24;
        return hourRem > 0 ? `${days}d ${hourRem}h` : `${days}d`;
    }


    /** Find the optional card elements once for each results document. */
    function spotlightView() {
        const ids = {
            card: 'artist-spotlight-card', content: 'spotlight-card-content',
            name: 'spotlight-artist-name', image: 'spotlight-artist-img',
            link: 'spotlight-spotify-link', duration: 'spotlight-playtime-badge',
            separator: 'spotlight-playtime-sep', summary: 'spotlight-scrobble-text',
            position: 'spotlight-artist-rank',
        };
        return Object.fromEntries(Object.entries(ids).map(([key, id]) => [key, document.getElementById(id)]));
    }

    /** Refresh text without depending on optional portrait or link elements. */
    function renderText(view, candidate, index, count) {
        view.card.dataset.artist = candidate.name;
        view.card.dataset.spotlightIndex = String(index);
        view.card.style.display = '';
        if (view.name) {
            view.name.textContent = candidate.name;
            view.name.title = candidate.name;
        }
        if (view.position) view.position.textContent = `${String(index + 1).padStart(2, '0')} / ${String(count).padStart(2, '0')}`;
        if (view.summary) {
            const albums = candidate.album_count === 1 ? 'album' : 'albums';
            view.summary.textContent = `${Number(candidate.scrobbles).toLocaleString()} scrobbles across ${candidate.album_count} ${albums} in ${window.APP_DATA?.year || ''}`;
        }
    }

    /** Show listening duration only when the candidate has measured playtime. */
    function renderDuration(view, candidate) {
        if (!view.duration || !view.separator) return;
        const visible = candidate.play_time_seconds > 0;
        if (visible) view.duration.textContent = candidate.play_time || formatDurationMobile(candidate.play_time_seconds);
        view.duration.classList.toggle('hidden', !visible);
        view.separator.classList.toggle('hidden', !visible);
    }

    /** Remove a portrait whose preload failed after all. */
    function hidePortrait(view) {
        view.image.removeAttribute('src');
        view.image.classList.add('hidden');
    }

    /** Resolve once `url` has loaded (or failed) in a throwaway Image, so a
     *  confirmed candidate's photo is already in the browser cache before it
     *  is ever shown -- a swap can then set the visible <img>'s src and the
     *  text together, synchronously, with no stale photo under a new name
     *  (F-B21-60 / B2). A load failure resolves to `''`, the same as an
     *  unconfirmed candidate, rather than rejecting. */
    function preloadImage(url) {
        return new Promise(resolve => {
            const preloader = new Image();
            preloader.onload = () => resolve(url);
            preloader.onerror = () => resolve('');
            preloader.src = url;
        });
    }

    /** Show the current candidate's already-cached photo. Never itself
     *  preloads: every confirmed candidate's photo settled before the
     *  rotation reveals anything (see `hydrateCandidate`), so this only
     *  ever assigns an `<img>` src that is already in cache. */
    function renderPortrait(view, candidate) {
        if (!view.image) return;
        if (!candidate.image_url) {
            hidePortrait(view);
            return;
        }
        view.image.src = candidate.image_url;
        view.image.alt = `Photograph of ${candidate.name}`;
        view.image.classList.remove('hidden', 'opacity-0');
        view.image.style.opacity = '1';
    }

    /** Keep the link and its accessible name attached to the visible artist. */
    function renderLink(view, candidate) {
        if (!view.link) return;
        const visible = Boolean(candidate.spotify_url);
        view.link.classList.toggle('hidden', !visible);
        if (visible) {
            view.link.href = candidate.spotify_url;
            view.link.setAttribute('aria-label', `View ${candidate.name} on Spotify (opens in new tab)`);
        } else {
            view.link.removeAttribute('href');
        }
    }

    /** Apply the current candidate. Swaps are instant: no fade, no delay. */
    function renderCandidate(view, state) {
        const index = state.index;
        const candidate = state.candidates[index];
        if (!candidate) return;
        renderText(view, candidate, index, state.candidates.length);
        renderDuration(view, candidate);
        renderPortrait(view, candidate);
        renderLink(view, candidate);
    }

    //: One hung `/api/artist_spotlight` request must never keep the whole
    //  card hidden (F-B21-60 / B3): each hydrate attempt is bounded, and a
    //  timed-out candidate is dropped like an unconfirmed one.
    const HYDRATE_TIMEOUT_MS = 8000;

    /** Confirm one candidate's photo. Never renders itself -- every call settles
     *  before the rotation reveals anything, so `startArtistSpotlightRotation`'s
     *  own `Promise.all(...)` is the only place that decides what is shown. */
    async function hydrateCandidate(view, state, candidate, index) {
        const expectedName = candidate.name;
        const controller = new AbortController();
        // One budget covers the fetch, its json body and the image preload
        // together: an image URL that never answers must still drop the
        // candidate, not just the request that fetched its URL (F-B21-60 /
        // B3 follow-up). `deadline` resolves `''` -- the same as a failed
        // preload -- when the whole hydrate has run past its budget.
        let resolveDeadline;
        const deadline = new Promise(resolve => { resolveDeadline = resolve; });
        const timeout = setTimeout(() => {
            controller.abort();
            resolveDeadline('');
        }, HYDRATE_TIMEOUT_MS);
        try {
            const response = await fetch(
                `/api/artist_spotlight?artist=${encodeURIComponent(expectedName)}`,
                { signal: controller.signal }
            );
            if (!response.ok || state.candidates[index].name !== expectedName) return;
            const data = await response.json();
            if (state.candidates[index].name !== expectedName) return;
            // Only a confirmed Spotify photo counts (F-B21-60): falling back
            // to the seed here would let an unconfirmed album cover (or a
            // stale one from a previous candidate) pass the rotation's
            // `c => c.image_url` filter as if it were a photo of this
            // artist. A photo that fails to actually load is dropped the
            // same way (B2): a confirmed URL is worthless if the browser
            // never manages to fetch the image itself, and a photo that
            // never even answers is dropped the same way as one that fails
            // (B3 follow-up): both race against the same `deadline`.
            const imageUrl = data.image_url ? await Promise.race([preloadImage(data.image_url), deadline]) : '';
            if (state.candidates[index].name !== expectedName) return;
            state.candidates[index] = {
                ...candidate,
                image_url: imageUrl,
                spotify_url: data.spotify_url || '',
            };
        } catch (error) {
            console.warn('Could not hydrate artist spotlight for', expectedName, ':', error);
        } finally {
            clearTimeout(timeout);
        }
    }

    /** Wait for every candidate's confirmed photo, then rotate only those that
     *  have one; reduced motion keeps the first artist still. A candidate with
     *  no confirmed Spotify photo never enters the rotation, so the card
     *  never fakes a photo it does not have. */
    function startArtistSpotlightRotation() {
        const view = spotlightView();
        const artists = window.APP_DATA?.spotlight_artists;
        if (!view.card || !Array.isArray(artists) || !artists.length) return;
        const state = {
            candidates: artists.map(artist => ({ ...artist })), index: 0,
            reducedMotion: window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches,
        };
        // Every hydrateCandidate call settles (resolves or rejects into its own
        // catch) before this .then() runs, and hydrateCandidate itself never
        // calls renderCandidate -- so nothing can draw the card before this
        // filter decides whether it is shown at all.
        Promise.all(
            state.candidates.map((candidate, index) => hydrateCandidate(view, state, candidate, index))
        ).then(() => {
            const withPhotos = state.candidates.filter(candidate => candidate.image_url);
            if (!withPhotos.length) return;
            state.candidates = withPhotos;
            state.index = 0;
            renderCandidate(view, state);
            if (state.reducedMotion || state.candidates.length < 2) return;
            setInterval(() => {
                if (document.hidden) return;
                state.index = (state.index + 1) % state.candidates.length;
                renderCandidate(view, state);
            }, 7000);
        });
    }
    startArtistSpotlightRotation();
});
