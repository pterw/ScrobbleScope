// static/js/results.js

document.addEventListener('DOMContentLoaded', () => {
    function escapeHtml(value) {
        if (value === null || value === undefined) return '';
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

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
        toast.innerHTML = `
            <div class="font-mono text-xs uppercase tracking-wider text-[var(--ss-text-muted,#6c6676)] font-bold">${kicker}</div>
            <div class="font-sans text-xs text-[var(--color-base-content,#1a1820)]">${escapeHtml(message)}</div>
        `;
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

                    let metric = '';
                    const desktopVal = tr.querySelector('.desktop-val');
                    if (desktopVal && desktopVal.offsetParent !== null) {
                        metric = desktopVal.textContent.trim();
                    } else {
                        const metricCell = tr.querySelector('.metric-value-cell');
                        metric = metricCell ? metricCell.textContent.trim() : (tr.dataset.playCount || '');
                    }

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
            if (!targetElement || typeof html2canvas === 'undefined') {
                showToast('Could not save image.', 'error');
                return;
            }

            const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
            const isDark = currentTheme === 'dark';
            const bgColor = isDark ? '#0e0c12' : '#faf8f3';

            html2canvas(targetElement, {
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

    // Leaderboard Metric Segmented Toggle: Bidirectional In-Place Reordering
    function setLeaderboardMetric(mode, showNotification = true) {
        const table = document.getElementById('results-table');
        const tbody = table ? table.querySelector('tbody') : null;
        if (!tbody) return;

        const rows = Array.from(tbody.querySelectorAll('tr'));
        if (mode === 'playtime') {
            rows.sort((a, b) => {
                const secA = parseFloat(a.dataset.playTimeSeconds || 0);
                const secB = parseFloat(b.dataset.playTimeSeconds || 0);
                return secB - secA;
            });
        } else {
            rows.sort((a, b) => {
                const countA = parseInt(a.dataset.playCount || 0, 10);
                const countB = parseInt(b.dataset.playCount || 0, 10);
                return countB - countA;
            });
        }

        rows.forEach((row, idx) => {
            tbody.appendChild(row);
            const rankNumEl = row.querySelector('.rank-num, .rank-link, td:first-child a, td:first-child span');
            if (rankNumEl) {
                const newRank = idx + 1;
                rankNumEl.textContent = newRank < 100 ? String(newRank).padStart(2, '0') : String(newRank);
            }

            const metricCell = row.querySelector('.metric-value-cell');
            if (metricCell) {
                metricCell.className = 'py-3 px-3 md:px-4 text-right align-middle whitespace-nowrap metric-value-cell';
                if (mode === 'playtime') {
                    const playTime = row.dataset.playTime || '';
                    const playTimeMobile = row.dataset.playTimeMobile || playTime;
                    metricCell.innerHTML = `
                        <span class="metric-value metric-val-playtime">
                            <span class="desktop-val hidden md:inline">${escapeHtml(playTime)}</span>
                            <span class="mobile-val inline md:hidden">${escapeHtml(playTimeMobile)}</span>
                        </span>
                    `;
                } else {
                    const playCount = row.dataset.playCount || '0';
                    metricCell.innerHTML = `
                        <span class="metric-value metric-val-plays">
                            ${escapeHtml(playCount)}
                        </span>
                    `;
                }
            }
        });

        const headerLabel = document.getElementById('metric-header-label');
        if (headerLabel) {
            headerLabel.textContent = mode === 'playtime' ? 'Listening Time' : 'Track Plays';
        }

        const rankingSubtitle = document.getElementById('results-ranking-subtitle');
        if (rankingSubtitle) {
            const year = window.APP_DATA?.year || '';
            rankingSubtitle.textContent = mode === 'playtime'
                ? `${year} · Ranked by listening time`
                : `${year} · Ranked by play count`;
        }

        const btnPlays = document.getElementById('toggle-sort-plays');
        const btnPlaytime = document.getElementById('toggle-sort-playtime');
        const activeClasses = ['bg-[var(--ss-accent-soft)]', 'text-[var(--color-primary)]', 'font-normal'];
        const inactiveClasses = ['text-[var(--ss-text-muted)]'];

        if (mode === 'playtime') {
            if (btnPlaytime) {
                btnPlaytime.classList.add(...activeClasses);
                btnPlaytime.classList.remove(...inactiveClasses);
            }
            if (btnPlays) {
                btnPlays.classList.remove(...activeClasses);
                btnPlays.classList.add(...inactiveClasses);
            }
            if (showNotification) {
                showToast('Leaderboard ranked by Spotify listening time.', 'info');
            }
        } else {
            if (btnPlays) {
                btnPlays.classList.add(...activeClasses);
                btnPlays.classList.remove(...inactiveClasses);
            }
            if (btnPlaytime) {
                btnPlaytime.classList.remove(...activeClasses);
                btnPlaytime.classList.add(...inactiveClasses);
            }
            if (showNotification) {
                showToast('Leaderboard ranked by track play count.', 'info');
            }
        }
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

    // Rotate a stable five-artist sample while Spotify portraits hydrate in parallel.
    function startArtistSpotlightRotation() {
        const card = document.getElementById('artist-spotlight-card');
        if (!card) return;
        const candidates = Array.isArray(window.APP_DATA?.spotlight_artists)
            ? window.APP_DATA.spotlight_artists.map(artist => ({ ...artist }))
            : [];
        if (candidates.length === 0) return;

        const contentEl = document.getElementById('spotlight-card-content');
        const nameEl = document.getElementById('spotlight-artist-name');
        const imgEl = document.getElementById('spotlight-artist-img');
        const linkEl = document.getElementById('spotlight-spotify-link');
        const playtimeBadge = document.getElementById('spotlight-playtime-badge');
        const playtimeSep = document.getElementById('spotlight-playtime-sep');
        const scrobbleText = document.getElementById('spotlight-scrobble-text');
        const positionEl = document.getElementById('spotlight-artist-rank');
        const prefersReducedMotion = window.matchMedia
            && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        const year = window.APP_DATA?.year || '';
        let currentIndex = 0;
        let imageLoadRevision = 0;

        const renderCandidate = (index, animate = true) => {
            const candidate = candidates[index];
            if (!candidate) return;

            const applyCandidate = () => {
                card.dataset.artist = candidate.name;
                card.dataset.spotlightIndex = String(index);
                card.style.display = '';

                if (nameEl) {
                    nameEl.textContent = candidate.name;
                    nameEl.title = candidate.name;
                }
                if (positionEl) {
                    positionEl.textContent = `${String(index + 1).padStart(2, '0')} / ${String(candidates.length).padStart(2, '0')}`;
                }
                if (scrobbleText) {
                    const albumWord = candidate.album_count === 1 ? 'album' : 'albums';
                    scrobbleText.textContent = `${Number(candidate.scrobbles).toLocaleString()} scrobbles across ${candidate.album_count} ${albumWord} in ${year}`;
                }
                if (playtimeBadge && playtimeSep) {
                    if (candidate.play_time_seconds > 0) {
                        playtimeBadge.textContent = candidate.play_time
                            || formatDurationMobile(candidate.play_time_seconds);
                        playtimeBadge.classList.remove('hidden');
                        playtimeSep.classList.remove('hidden');
                    } else {
                        playtimeBadge.classList.add('hidden');
                        playtimeSep.classList.add('hidden');
                    }
                }
                if (imgEl) {
                    const revision = ++imageLoadRevision;
                    if (candidate.image_url) {
                        const preloader = new Image();
                        preloader.onload = () => {
                            if (revision !== imageLoadRevision || currentIndex !== index) return;
                            imgEl.src = candidate.image_url;
                            imgEl.alt = `Photograph of ${candidate.name}`;
                            imgEl.classList.remove('hidden', 'opacity-0');
                            imgEl.style.opacity = '1';
                            contentEl?.classList.remove('spotlight-no-image');
                        };
                        preloader.onerror = () => {
                            if (revision !== imageLoadRevision || currentIndex !== index) return;
                            imgEl.removeAttribute('src');
                            imgEl.classList.add('hidden');
                            contentEl?.classList.add('spotlight-no-image');
                        };
                        preloader.src = candidate.image_url;
                    } else {
                        imgEl.removeAttribute('src');
                        imgEl.classList.add('hidden');
                        contentEl?.classList.add('spotlight-no-image');
                    }
                }
                if (linkEl) {
                    if (candidate.spotify_url) {
                        linkEl.href = candidate.spotify_url;
                        linkEl.classList.remove('hidden');
                        linkEl.setAttribute(
                            'aria-label',
                            `View ${candidate.name} on Spotify (opens in new tab)`,
                        );
                    } else {
                        linkEl.removeAttribute('href');
                        linkEl.classList.add('hidden');
                    }
                }
            };

            if (!animate || prefersReducedMotion || !contentEl) {
                applyCandidate();
                return;
            }
            contentEl.style.opacity = '0.15';
            setTimeout(() => {
                applyCandidate();
                contentEl.style.opacity = '1';
            }, 150);
        };

        const hydrateCandidate = async (candidate, index) => {
            const expectedName = candidate.name;
            try {
                const response = await fetch(
                    `/api/artist_spotlight?artist=${encodeURIComponent(expectedName)}`,
                );
                if (!response.ok || candidates[index].name !== expectedName) return;
                const data = await response.json();
                if (candidates[index].name !== expectedName) return;
                candidates[index] = {
                    ...candidate,
                    image_url: data.image_url || candidate.image_url,
                    spotify_url: data.spotify_url || '',
                };
                if (currentIndex === index) renderCandidate(index, false);
            } catch (error) {
                console.warn(`Could not hydrate artist spotlight for ${expectedName}:`, error);
            }
        };

        renderCandidate(currentIndex, false);
        candidates.forEach((candidate, index) => {
            hydrateCandidate(candidate, index);
        });

        if (!prefersReducedMotion && candidates.length > 1) {
            setInterval(() => {
                if (document.hidden) return;
                currentIndex = (currentIndex + 1) % candidates.length;
                renderCandidate(currentIndex);
            }, 7000);
        }
    }
    startArtistSpotlightRotation();
});
