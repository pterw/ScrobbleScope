// Artist spotlight presentation, hydration and rotation are independent of exports.
document.addEventListener('DOMContentLoaded', () => {
    /** Find the optional card elements once for each results document. */
    function spotlightView() {
        const ids = {
            card: 'artist-spotlight-card',
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

    /** Show listening duration only when the candidate has measured playtime.
     *  The server formats it (`play_time`) whenever it measured any. */
    function renderDuration(view, candidate) {
        if (!view.duration || !view.separator) return;
        const visible = candidate.play_time_seconds > 0;
        if (visible) view.duration.textContent = candidate.play_time;
        view.duration.classList.toggle('hidden', !visible);
        view.separator.classList.toggle('hidden', !visible);
    }

    /** Resolve once `url` has loaded (or failed) in a throwaway Image, so a
     *  confirmed candidate's photo is already in the browser cache before it
     *  is ever shown -- a swap can then set the visible <img>'s src and the
     *  text together, synchronously, with no stale photo under a new name
     *  (F-B21-60). A load failure resolves to `''`, the same as an
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
        view.image.src = candidate.image_url;
        view.image.alt = `Photograph of ${candidate.name}`;
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
    function renderCandidate(view, state, { keepLink = false } = {}) {
        const index = state.index;
        const candidate = state.candidates[index];
        if (!candidate) return;
        renderText(view, candidate, index, state.candidates.length);
        renderDuration(view, candidate);
        renderPortrait(view, candidate);
        if (!keepLink) renderLink(view, candidate);
    }

    /** True while the reader is using the card: the pointer is over it, or
     *  focus is inside it. Read from the document rather than from focus
     *  events alone, so a window that loses focus (which leaves the element
     *  focused) still counts. */
    function cardInUse(view, state) {
        return state.pointerInside || view.card.contains(document.activeElement);
    }

    /** Track the pointer over the card, for `cardInUse`. A card first
     *  shown under a still pointer needs no seeding: Chromium (the only engine the
     *  behaviour tests drive) hit-tests the pointer after the layout change and
     *  fires `pointerenter` itself. */
    function watchCardUse(view, state) {
        view.card.addEventListener('pointerenter', () => { state.pointerInside = true; });
        view.card.addEventListener('pointerleave', () => { state.pointerInside = false; });
        // Focus needs no listener: `cardInUse` reads `document.activeElement`,
        // so focus moving between elements inside the card never counts as
        // leaving it, and nothing can go stale.
    }

    /** Hold the card at the height of its tallest candidate, so the sticky
     *  rail below it never moves when the rotation swaps candidates.
     *  Each candidate is rendered once and the card's own rendered height is
     *  read back -- no line-count arithmetic -- and all of it happens in one
     *  synchronous pass, so nothing but the current candidate is ever
     *  painted. Called once the candidates are settled, again whenever the
     *  card's width (and so its layout) changes, and once fonts have loaded. */
    function reserveCardHeight(view, state) {
        const card = view.card;
        // A focused link must never be hidden or retargeted, even for the
        // instant of a measurement: leave the link alone while focus is in
        // the card.
        const keepLink = card.contains(document.activeElement);
        card.style.minHeight = '';
        let tallest = 0;
        state.candidates.forEach((candidate, index) => {
            // A link kept for focus is not this candidate's own: with no
            // Spotify URL it would show nothing, so take the kept link out of
            // the layout for this measurement (a class, so the link itself is
            // never written to) instead of reading a height it would not add.
            card.classList.toggle('is-measuring-without-link', keepLink && !candidate.spotify_url);
            renderCandidate(view, { ...state, index }, { keepLink });
            tallest = Math.max(tallest, card.getBoundingClientRect().height);
        });
        card.classList.remove('is-measuring-without-link');
        card.style.minHeight = `${tallest}px`;
        renderCandidate(view, state, { keepLink });
    }

    /** Keep the reserved height right as the card's layout changes. */
    function watchCardLayout(view, state) {
        let width = view.card.getBoundingClientRect().width;
        const remeasure = () => reserveCardHeight(view, state);
        if (typeof ResizeObserver === 'function') {
            new ResizeObserver(() => {
                const next = view.card.getBoundingClientRect().width;
                if (next === width) return;
                width = next;
                remeasure();
            }).observe(view.card);
        }
        // Web fonts load lazily, once the card first draws text: a font that
        // arrives after the first pass changes every line's height.
        if (document.fonts) {
            document.fonts.addEventListener('loadingdone', remeasure);
            document.fonts.ready.then(remeasure);
        }
    }

    //: One hung `/api/artist_spotlight` request must never keep the whole
    //  card hidden (F-B21-60): each hydrate attempt is bounded, and a
    //  timed-out candidate is dropped like an unconfirmed one.
    const HYDRATE_TIMEOUT_MS = 8000;

    /** Confirm one candidate's photo. Never renders itself -- every call settles
     *  before the rotation reveals anything, so `startArtistSpotlightRotation`'s
     *  own `Promise.all(...)` is the only place that decides what is shown.
     *  Each call writes only its own `state.candidates[index]`, and nothing
     *  else touches the array until every call has settled. */
    async function hydrateCandidate(state, candidate, index) {
        const expectedName = candidate.name;
        const controller = new AbortController();
        // One budget covers the fetch, its json body and the image preload
        // together: an image URL that never answers must still drop the
        // candidate, not just the request that fetched its URL (F-B21-60).
        // `deadline` resolves `''` -- the same as a failed preload -- when
        // the whole hydrate has run past its budget.
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
            if (!response.ok) return;
            const data = await response.json();
            // Only a confirmed Spotify photo counts (F-B21-60): falling back
            // to the seed here would let an unconfirmed album cover (or a
            // stale one from a previous candidate) pass the rotation's
            // `c => c.image_url` filter as if it were a photo of this
            // artist. A photo that fails to actually load is dropped the
            // same way: a confirmed URL is worthless if the browser never
            // manages to fetch the image itself, and a photo that never even
            // answers is dropped the same way as one that fails: both race
            // against the same `deadline`.
            const imageUrl = data.image_url ? await Promise.race([preloadImage(data.image_url), deadline]) : '';
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
            pointerInside: false,
        };
        const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        // Every hydrateCandidate call settles (resolves or rejects into its own
        // catch) before this .then() runs, and hydrateCandidate itself never
        // calls renderCandidate -- so nothing can draw the card before this
        // filter decides whether it is shown at all.
        Promise.all(
            state.candidates.map((candidate, index) => hydrateCandidate(state, candidate, index))
        ).then(() => {
            const withPhotos = state.candidates.filter(candidate => candidate.image_url);
            if (!withPhotos.length) return;
            state.candidates = withPhotos;
            state.index = 0;
            renderCandidate(view, state);
            // Nothing rotates, so nothing needs a height reserved for it.
            if (reducedMotion || state.candidates.length < 2) return;
            reserveCardHeight(view, state);
            watchCardLayout(view, state);
            watchCardUse(view, state);
            setInterval(() => {
                if (document.hidden || cardInUse(view, state)) return;
                state.index = (state.index + 1) % state.candidates.length;
                renderCandidate(view, state);
            }, 7000);
        });
    }
    startArtistSpotlightRotation();
});
