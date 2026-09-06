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
                const headers = Array.from(table.querySelectorAll('thead th')).map(header => 
                    '"' + header.textContent.trim().replace(/"/g, '""') + '"'
                );
                csvContent.push(headers.join(','));

                const rows = table.querySelectorAll('tbody tr');
                rows.forEach(tr => {
                    const rowData = [];
                    const cells = Array.from(tr.querySelectorAll('th, td'));
                    cells.forEach((cell, index) => {
                        let content = '';
                        // Day precision: check data-export on cell or descendant
                        const exportAttr = cell.getAttribute('data-export');
                        if (exportAttr !== null && exportAttr !== '') {
                            content = exportAttr;
                        } else if (cell.classList.contains('album-title-cell') || cell.classList.contains('album-title')) {
                            const albumInfo = cell.querySelector('.album-info');
                            content = albumInfo ? albumInfo.textContent.trim() : cell.textContent.trim();
                        } else {
                            const desktopSpan = cell.querySelector('.desktop-val') || cell.querySelector('.desktop-date') || cell.querySelector('.d-md-inline');
                            if (desktopSpan) {
                                content = desktopSpan.textContent.trim();
                            } else {
                                content = cell.textContent.trim();
                            }
                        }
                        content = content.replace(/\s+/g, ' ').replace(/"/g, '""');
                        rowData.push(`"${content}"`);
                    });
                    csvContent.push(rowData.join(','));
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

    // Playtime Discovery CTA: Immediate In-Place Reordering
    const rankPlaytimeBtn = document.getElementById('cta-rank-playtime');
    if (rankPlaytimeBtn) {
        rankPlaytimeBtn.addEventListener('click', function() {
            const table = document.getElementById('results-table');
            const tbody = table ? table.querySelector('tbody') : null;
            if (!tbody) return;

            const rows = Array.from(tbody.querySelectorAll('tr'));
            // Re-sort rows in descending order by play_time_seconds
            rows.sort((a, b) => {
                const secA = parseFloat(a.dataset.playTimeSeconds || 0);
                const secB = parseFloat(b.dataset.playTimeSeconds || 0);
                return secB - secA;
            });

            // Re-append rows in sorted order and update rank numbers & metrics
            rows.forEach((row, idx) => {
                tbody.appendChild(row);
                const rankNumEl = row.querySelector('.rank-num');
                if (rankNumEl) {
                    const newRank = idx + 1;
                    rankNumEl.textContent = newRank < 100 ? String(newRank).padStart(2, '0') : String(newRank);
                }

                const metricCell = row.querySelector('.metric-value-cell');
                if (metricCell) {
                    const playTime = row.dataset.playTime || '';
                    const playTimeMobile = row.dataset.playTimeMobile || playTime;
                    metricCell.innerHTML = `
                        <span class="desktop-val hidden md:inline">${escapeHtml(playTime)}</span>
                        <span class="mobile-val inline md:hidden">${escapeHtml(playTimeMobile)}</span>
                    `;
                }
            });

            // Update column header
            const headerLabel = document.getElementById('metric-header-label');
            if (headerLabel) {
                headerLabel.textContent = 'Listening Time';
            }

            // Update banner appearance to indicate active state
            const ctaBanner = document.getElementById('playtime-cta-banner');
            if (ctaBanner) {
                ctaBanner.classList.add('opacity-80');
                rankPlaytimeBtn.disabled = true;
                rankPlaytimeBtn.textContent = 'Ranked by Listening Time ✓';
                rankPlaytimeBtn.classList.remove('btn-primary');
                rankPlaytimeBtn.classList.add('btn-ghost');
            }

            showToast('Leaderboard re-ranked by actual listening time.', 'info');
        });
    }
});
