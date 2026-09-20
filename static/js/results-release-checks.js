// Live original-release corrections, disclosed without moving the page.
//
// The correction worker (scrobblescope/release_checks.py) asks MusicBrainz for
// each album's original release date at one request per second, long after the
// table is on screen. This script polls GET /api/release_checks and discloses
// what it finds. The owner's ruling governs every choice here: results render
// at once, corrections land live, a corrected row stays where it is, and the
// list re-sorts only on reload.
document.addEventListener('DOMContentLoaded', () => {
    const bar = document.getElementById('release-check-bar');
    if (!bar) return;

    const statusLine = document.getElementById('release-check-status');
    const reloadLink = document.getElementById('release-check-reload');
    const jobId = bar.dataset.jobId;
    if (!jobId) return;

    const POLL_MS = 2000;
    // The two states that can still change. Everything else stops the loop,
    // including a status this script has never heard of: the endpoint answers
    // "error" for a missing or expired job precisely so that an unrecognised
    // word is the stopping condition rather than a list to fall off the end of.
    const LIVE_STATES = ['pending', 'running'];

    let stopped = false;
    let pollTimer = null;
    let inFlight = false;

    /** Stop for good. A finished pass has nothing further to report. */
    function stop() {
        stopped = true;
        window.clearTimeout(pollTimer);
        pollTimer = null;
    }

    /** Remove the line from the flow once the pass ends with nothing to say. */
    function retire() {
        bar.remove();
    }

    function setStatusText(text) {
        if (statusLine) statusLine.textContent = text;
    }

    /** Announce moved-in albums as a count plus a reload, never by inserting. */
    function announceMovedIn(count) {
        const albums = count === 1 ? 'album' : 'albums';
        const were = count === 1 ? 'was' : 'were';
        setStatusText(`${count} ${albums} first released in your filter ${were} found.`);
        if (reloadLink) reloadLink.classList.remove('hidden');
    }

    /**
     * Mark one row in place.
     *
     * The note goes inside the release cell, under the date, because that cell
     * is shorter than the row's artwork: a second line there changes nothing
     * about where any row sits. Only a moved-out album is marked -- a
     * confirmed one tells the reader nothing they cannot already see, and an
     * album MusicBrainz could not date has no correction to disclose.
     */
    function markRow(album) {
        const row = document.querySelector(
            `#results-table tbody tr[data-album-key="${CSS.escape(album.key)}"]`
        );
        if (!row || row.dataset.releaseCheck === album.state) return;
        row.dataset.releaseCheck = album.state;
        if (album.state !== 'moved_out' || !album.original_release_date) return;

        const cell = row.querySelector('.release-date-cell');
        if (!cell || cell.querySelector('.release-check-note')) return;

        const original = String(album.original_release_date);
        const year = original.slice(0, 4);
        const value = cell.querySelector('.release-date-value');
        if (value) value.textContent = original.slice(0, 7);
        row.classList.add('is-release-corrected');

        const note = document.createElement('a');
        note.className = 'release-check-note';
        note.href = '/unmatched';
        note.textContent = 'first released';
        note.setAttribute(
            'aria-label',
            `${row.dataset.album} was first released in ${year}, outside this filter. ` +
            'See the unmatched report for the reason.'
        );
        cell.appendChild(note);
    }

    /** Apply one reply: the counting line, the markers, then the ending. */
    function apply(payload) {
        const status = String(payload.status || '');
        const albums = Array.isArray(payload.albums) ? payload.albums : [];
        albums.forEach(markRow);

        const movedIn = Number(payload.moved_in) || 0;
        const live = LIVE_STATES.includes(status);

        if (live) {
            const total = Number(payload.total) || 0;
            const checked = Number(payload.checked) || 0;
            setStatusText(
                total > 0 ? `Checking original release years: ${checked} of ${total}` : ''
            );
            return;
        }

        stop();
        if (movedIn > 0) {
            announceMovedIn(movedIn);
            return;
        }
        retire();
    }

    async function poll() {
        if (stopped || inFlight || document.hidden) return;
        inFlight = true;
        try {
            const response = await fetch(
                `/api/release_checks?job_id=${encodeURIComponent(jobId)}`
            );
            const payload = await response.json();
            inFlight = false;
            if (stopped) return;
            if (!response.ok) {
                // A job that has expired or gone is not coming back, and the
                // corrections it found are already cached for the next reader.
                stop();
                retire();
                return;
            }
            apply(payload);
            schedule();
        } catch (error) {
            // A correction pass is an enhancement over results the reader can
            // already see, so a failed request retires the line rather than
            // showing an error the reader can do nothing about.
            inFlight = false;
            console.error('Release-check polling stopped:', error);
            stop();
            retire();
        }
    }

    /**
     * Queue the next poll.
     *
     * setTimeout, never setInterval: F-B21-33 was a pair of overlapping
     * interval polls on this same page applying replies out of order.
     */
    function schedule() {
        if (stopped) return;
        window.clearTimeout(pollTimer);
        pollTimer = window.setTimeout(poll, POLL_MS);
    }

    // A hidden tab is a reader who is not looking. The worker keeps going
    // either way -- its findings go to the cache, not to this page -- so
    // pausing costs nothing and the next reply carries everything missed.
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            window.clearTimeout(pollTimer);
            return;
        }
        if (!stopped) poll();
    });

    poll();
});
