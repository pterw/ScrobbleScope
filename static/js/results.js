// static/js/results.js

document.addEventListener('DOMContentLoaded', () => {
    const resultsPage = document.querySelector('.results-page');

    /** Scale the bounded Results composition from its authored rem baseline.
     * A numeric custom property works in both browser engines. Native layout
     * still owns wrapping and document height; the shared header is outside
     * this scope. Small screens retain scale 1, including without JavaScript.
     */
    function syncResultsScale() {
        if (!resultsPage) return;
        const rootSize = parseFloat(getComputedStyle(document.documentElement).fontSize);
        const baseRem = parseFloat(getComputedStyle(resultsPage).getPropertyValue('--results-base-rem'));
        const baseWidth = rootSize * baseRem;
        if (!(baseWidth > 0)) return;
        const scale = Math.max(1, resultsPage.getBoundingClientRect().width / baseWidth);
        resultsPage.style.setProperty('--results-scale', String(scale));
    }

    if (resultsPage) {
        syncResultsScale();
        new ResizeObserver(syncResultsScale).observe(resultsPage);
        window.addEventListener('resize', syncResultsScale);
    }

    /** Build text-bearing nodes without interpreting API or dataset values as HTML. */
    function textNode(tag, className, text) {
        const node = document.createElement(tag);
        node.className = className;
        node.textContent = text;
        return node;
    }

    // Toast Notification (daisyUI stack + 3px tone rule and mono kicker)
    function showToast(message, type = 'info', duration = 3000) {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toast = document.createElement('div');
        let borderClass = 'border-l-[3px] border-l-[var(--color-primary)]';
        let kicker = 'INFO';
        if (type === 'error') {
            borderClass = 'border-l-[3px] border-l-[var(--ss-bad,#b03434)]';
            kicker = 'ERROR';
        } else if (type === 'success') {
            borderClass = 'border-l-[3px] border-l-[var(--ss-good,#2f7a4a)]';
            kicker = 'EXPORTED';
        }

        toast.className = `alert shadow-lg bg-[var(--ss-surface-card,#ffffff)] border border-[var(--ss-border-default,#e5dfd1)] ${borderClass} rounded-[var(--radius-sm,8px)] p-3 flex flex-col items-start gap-1 min-w-[260px] max-w-sm transition-all duration-300 transform translate-y-2 opacity-0 z-50`;
        toast.setAttribute('role', type === 'error' ? 'alert' : 'status');
        toast.append(
            textNode('div', 'font-mono text-xs uppercase tracking-wider text-[var(--ss-text-muted,#6c6676)] font-bold', kicker),
            textNode('div', 'font-sans text-xs text-[var(--color-base-content,#1a1820)]', message),
        );
        container.appendChild(toast);

        requestAnimationFrame(() => {
            toast.classList.remove('translate-y-2', 'opacity-0');
            toast.classList.add('translate-y-0', 'opacity-100');
        });

        setTimeout(() => {
            toast.classList.remove('translate-y-0', 'opacity-100');
            toast.classList.add('translate-y-2', 'opacity-0');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    // CSV Export Logic (preserving day precision via data-export attribute)
    const exportCsvBtn = document.getElementById('export-csv');
    if (exportCsvBtn) {
        exportCsvBtn.addEventListener('click', function() {
            try {
                const table = document.querySelector('#results-table') || document.querySelector('.results-table') || document.querySelector('.table');
                if (!table) {
                    showToast('No data available to export.', 'error');
                    return;
                }

                const csvContent = [];
                csvContent.push('"#","Album","Artist","Track Plays / Listening Time","Release Date"');

                const rows = table.querySelectorAll('tbody tr');
                rows.forEach(tr => {
                    const rank = tr.dataset.rank || tr.querySelector('.rank-num')?.textContent.trim() || '';
                    const album = tr.dataset.album || tr.querySelector('.album-link, .album-info span')?.textContent.trim() || '';
                    const artist = tr.dataset.artist || tr.querySelector('.artist-name')?.textContent.trim() || '';

                    const metric = table.dataset.metric === 'playtime'
                        ? (tr.dataset.playTime || '')
                        : (tr.dataset.playCount || '0');

                    const releaseCell = tr.querySelector('.release-date-cell');
                    const release = releaseCell?.getAttribute('data-export') || releaseCell?.textContent.trim() || '';

                    const clean = (val) => '"' + String(val).replace(/\s+/g, ' ').replace(/"/g, '""').trim() + '"';
                    csvContent.push([clean(rank), clean(album), clean(artist), clean(metric), clean(release)].join(','));
                });

                const link = document.createElement('a');
                link.href = URL.createObjectURL(new Blob([csvContent.join('\n')], { type: 'text/csv;charset=utf-8;' }));
                const username = window.APP_DATA?.username || 'user';
                const year = window.APP_DATA?.year || 'all';
                link.download = `scrobblescope_${username}_${year}_albums.csv`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                showToast('CSV file downloaded successfully!', 'success');
            } catch (error) {
                console.error('Error exporting CSV:', error);
                showToast('Error creating CSV file.', 'error');
            }
        });
    }

    // JPEG Image Export Logic (mobile desktop-forcing via onclone)
    const saveImageBtn = document.getElementById('save-image');
    if (saveImageBtn) {
        saveImageBtn.addEventListener('click', function() {
            showToast('Creating leaderboard image... please wait.');
            const targetElement = document.getElementById('results-table-wrapper');
            if (!targetElement || typeof window.html2canvas !== 'function') {
                showToast('Could not save image.', 'error');
                return;
            }

            const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
            const bgColor = getComputedStyle(document.body).backgroundColor;

            window.html2canvas(targetElement, {
                scale: 3,
                useCORS: true,
                backgroundColor: bgColor,
                windowWidth: 1200,
                scrollX: 0,
                scrollY: 0,
                onclone: (clonedDoc) => {
                    const clonedWrapper = clonedDoc.getElementById('results-table-wrapper');
                    if (clonedWrapper) {
                        clonedWrapper.style.overflow = 'visible';
                        clonedWrapper.style.width = '1200px';
                        clonedWrapper.style.maxWidth = '1200px';
                    }

                    // Preserve theme attribute
                    clonedDoc.documentElement.setAttribute('data-theme', currentTheme);

                    // Force desktop text elements
                    clonedWrapper?.querySelectorAll('.desktop-val, .desktop-date, .d-md-inline').forEach(el => {
                        el.style.display = 'inline';
                    });
                    clonedWrapper?.querySelectorAll('.mobile-val, .mobile-date, .d-md-none').forEach(el => {
                        el.style.display = 'none';
                    });

                    // Force unhide rank numbers
                    clonedWrapper?.querySelectorAll('.rank-num').forEach(el => {
                        el.style.display = 'inline-block';
                    });
                },
            }).then(canvas => {
                const link = document.createElement('a');
                link.href = canvas.toDataURL('image/jpeg', 0.95);
                const username = window.APP_DATA?.username || 'user';
                const year = window.APP_DATA?.year || 'all';
                link.download = `scrobblescope_${username}_${year}.jpg`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                showToast('Image saved successfully!', 'success');
            }).catch(err => {
                console.error('Error creating image:', err);
                showToast('Failed to create image.', 'error');
            });
        });
    }

    /** Render one metric from the row's canonical export data. */
    function renderMetric(row, mode) {
        const cell = row.querySelector('.metric-value-cell');
        if (!cell) return;
        const value = textNode('span', 'metric-value', '');
        value.classList.add(mode === 'playtime' ? 'metric-val-playtime' : 'metric-val-plays');
        if (mode === 'playtime') {
            const duration = row.dataset.playTime || '';
            value.append(
                textNode('span', 'desktop-val hidden md:inline', duration),
                textNode('span', 'mobile-val inline md:hidden', row.dataset.playTimeMobile || duration),
            );
        } else {
            value.textContent = row.dataset.playCount || '0';
        }
        cell.replaceChildren(value);
    }

    /** Keep selection styling and accessible state in sync with the sort mode. */
    function updateMetricButtons(mode) {
        for (const [buttonMode, id] of [['plays', 'toggle-sort-plays'], ['playtime', 'toggle-sort-playtime']]) {
            const button = document.getElementById(id);
            if (!button) continue;
            const active = mode === buttonMode;
            button.classList.toggle('bg-[var(--ss-accent-soft)]', active);
            button.classList.toggle('text-[var(--color-primary)]', active);
            button.classList.toggle('text-[var(--ss-text-muted)]', !active);
            button.setAttribute('aria-pressed', String(active));
        }
    }

    /** Reorder existing rows and update their visible and exported ranks together. */
    function setLeaderboardMetric(mode, showNotification = true) {
        const table = document.getElementById('results-table');
        const tbody = table?.querySelector('tbody');
        if (!tbody) return;
        table.dataset.metric = mode;
        const key = mode === 'playtime' ? 'playTimeSeconds' : 'playCount';
        const rows = Array.from(tbody.querySelectorAll('tr'));
        rows.sort((a, b) => Number(b.dataset[key] || 0) - Number(a.dataset[key] || 0));
        rows.forEach((row, index) => {
            tbody.appendChild(row);
            row.dataset.rank = String(index + 1);
            const rank = row.querySelector('.rank-num, .rank-link, td:first-child a, td:first-child span');
            if (rank) rank.textContent = String(index + 1).padStart(2, '0');
            renderMetric(row, mode);
        });
        const label = document.getElementById('metric-header-label');
        if (label) label.textContent = mode === 'playtime' ? 'Listening Time' : 'Track Plays';
        const subtitle = document.getElementById('results-ranking-subtitle');
        if (subtitle) {
            const ranking = mode === 'playtime' ? 'listening time' : 'play count';
            subtitle.textContent = `${window.APP_DATA?.year || ''} \u00b7 Ranked by ${ranking}`;
        }
        updateMetricButtons(mode);
        if (showNotification) {
            showToast(mode === 'playtime'
                ? 'Leaderboard ranked by Spotify listening time.'
                : 'Leaderboard ranked by track play count.');
        }
    }

    const resultsTable = document.getElementById('results-table');
    if (resultsTable) {
        resultsTable.dataset.metric = window.APP_DATA?.sort_by === 'playtime' ? 'playtime' : 'plays';
        updateMetricButtons(resultsTable.dataset.metric);
    }

    const togglePlaysBtn = document.getElementById('toggle-sort-plays');
    if (togglePlaysBtn) {
        togglePlaysBtn.addEventListener('click', () => setLeaderboardMetric('plays', true));
    }

    const togglePlaytimeBtn = document.getElementById('toggle-sort-playtime');
    if (togglePlaytimeBtn) {
        togglePlaytimeBtn.addEventListener('click', () => setLeaderboardMetric('playtime', true));
    }

    const railBackToTopBtn = document.getElementById('rail-back-to-top');
    if (railBackToTopBtn) {
        railBackToTopBtn.addEventListener('click', (e) => {
            e.preventDefault();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

});
