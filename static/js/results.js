// static/js/results.js

document.addEventListener('DOMContentLoaded', () => {
    const jobId = window.APP_DATA?.job_id;

    function escapeHtml(value) {
        if (value === null || value === undefined) return '';
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    // Toast Notification Helper
    function showToast(message, type = 'info', duration = 3000) {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) return;

        const toast = document.createElement('div');
        toast.className = 'toast show';
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');

        const header = document.createElement('div');
        header.className = 'toast-header' + (type === 'error' ? ' bg-danger text-white' : '');
        const title = document.createElement('strong');
        title.className = 'me-auto';
        title.textContent = 'ScrobbleScope';
        const closeBtn = document.createElement('button');
        closeBtn.type = 'button';
        closeBtn.className = 'btn-close';
        closeBtn.setAttribute('data-bs-dismiss', 'toast');
        closeBtn.setAttribute('aria-label', 'Close');
        header.appendChild(title);
        header.appendChild(closeBtn);

        const body = document.createElement('div');
        body.className = 'toast-body';
        body.textContent = message;

        toast.appendChild(header);
        toast.appendChild(body);
        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 500);
        }, duration);
    }

    // Fetch Unmathced Albums
    function fetchUnmatchedAlbums() {
        const unmatchedList = document.getElementById('unmatched-list');
        if (!unmatchedList) return;
        
        // Show a spinner while loading
        unmatchedList.innerHTML = `
            <div class="d-flex justify-content-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>`;

        if (!jobId) {
            unmatchedList.innerHTML = '<div class="alert alert-warning">Missing job identifier.</div>';
            return;
        }

        fetch(`/unmatched?job_id=${encodeURIComponent(jobId)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server error: ${response.status}`);
                }
                return response.json();
            })
            .then(unmatchedData => {
                let html = '';
                const data = unmatchedData.data || {};
                const count = unmatchedData.count || Object.keys(data).length;

                if (count === 0) {
                    html = '<p>No unmatched albums found.</p>';
                } else {
                    html = `<p>Found ${count} unmatched albums:</p>
                            <div class="table-responsive">
                                <table class="table table-sm">
                                    <thead><tr><th>Artist</th><th>Album</th><th>Reason</th></tr></thead>
                                    <tbody>`;
                    for (const key in data) {
                        const item = data[key];
                        html += `<tr><td>${escapeHtml(item.artist)}</td><td>${escapeHtml(item.album)}</td><td>${escapeHtml(item.reason)}</td></tr>`;
                    }
                    html += `</tbody></table></div>`;
                }
                unmatchedList.innerHTML = html;
            })
            .catch(error => {
                const safeError = escapeHtml(error && error.message ? error.message : String(error));
                unmatchedList.innerHTML = `<div class="alert alert-danger">Error loading unmatched albums: ${safeError}</div>`;
            });
    }

    const quickViewBtn = document.getElementById('view-unmatched-quick');
    const noMatchesLink = document.getElementById('view-unmatched');

    if(quickViewBtn) quickViewBtn.addEventListener('click', fetchUnmatchedAlbums);
    if(noMatchesLink) noMatchesLink.addEventListener('click', fetchUnmatchedAlbums);


    // CSV
    const exportCsvBtn = document.getElementById('export-csv');
    if (exportCsvBtn) {
        exportCsvBtn.addEventListener('click', function() {
            try {
                const table = document.querySelector('.table');
                if (!table) {
                    showToast('No data available to export.', 'error');
                    return;
                }
                
                let csvContent = [];
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
                        if (index === 1 && cell.classList.contains('album-title')) {
                            const albumInfo = cell.querySelector('.album-info');
                            content = albumInfo ? albumInfo.textContent.trim() : '';
                        } else {
                            // When a cell has responsive spans, extract only
                            // the desktop (.d-md-inline) text to avoid
                            // concatenating both spans (e.g. "2024-03-152024-03").
                            const desktopSpan = cell.querySelector('.d-md-inline');
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
                // Read username and year from the global APP_DATA object
                link.download = `scrobblescope_${APP_DATA.username}_${APP_DATA.year}_albums.csv`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                showToast('CSV file downloaded successfully!');
            } catch (error) {
                console.error('Error exporting CSV:', error);
                showToast('Error creating CSV file.', 'error');
            }
        });
    }


    // Save as JPEG Image Logic
    const saveImageBtn = document.getElementById('save-image');
    if (saveImageBtn) {
        saveImageBtn.addEventListener('click', function() {
            showToast('Creating image... please wait.');
            const targetElement = document.getElementById('results-table-wrapper');
            if (!targetElement || typeof html2canvas === 'undefined') {
                showToast('Could not save image.', 'error');
                return;
            }
            
            const el = targetElement;
            const isDark = document.body.classList.contains('dark-mode');
            // windowWidth:1200 forces desktop CSS layout (hides mobile media queries),
            // scale:3 produces a high-resolution image regardless of device pixel ratio.
            // Read --bg-color from <body> (not <html>) so the dark-mode override
            // (#121212) is picked up; :root still holds the light-mode fallback.
            html2canvas(el, {
                scale: 3,
                useCORS: true,
                backgroundColor: getComputedStyle(document.body).getPropertyValue('--bg-color').trim() || '#ffffff',
                windowWidth: 1200,
                scrollX: 0,
                scrollY: 0,
                onclone: (clonedDoc) => {
                    // Remove overflow clip in the clone so the full table renders
                    const w = clonedDoc.getElementById('results-table-wrapper');
                    if (w) { w.style.overflow = 'visible'; }

                    // Ensure dark-mode class transfers to cloned body
                    if (isDark) {
                        clonedDoc.body.classList.add('dark-mode');
                    }

                    // Force desktop layout in the clone: show desktop spans,
                    // hide mobile spans, and unhide rank columns. html2canvas
                    // captures computed styles at clone time -- on mobile
                    // viewports, d-none d-md-inline elements are already
                    // display:none and windowWidth cannot override that.
                    w?.querySelectorAll('.d-md-inline').forEach(el => {
                        el.style.display = 'inline';
                    });
                    w?.querySelectorAll('.d-md-none').forEach(el => {
                        el.style.display = 'none';
                    });
                    // Unhide rank column (hidden on mobile via CSS)
                    const table = w?.querySelector('.results-table');
                    if (table) {
                        table.querySelectorAll('th:first-child, td:first-child').forEach(el => {
                            el.style.display = '';
                        });
                    }

                    // Dark-mode: inline resolved colours so html2canvas
                    // renders them correctly.  html2canvas 1.x mishandles
                    // Bootstrap's --bs-table-accent-bg on striped odd rows,
                    // causing light text on a near-white composited background.
                    if (isDark && table) {
                        const txt = '#f8f9fa';
                        const accent = '#9370DB';

                        table.style.color = txt;
                        table.style.borderColor = 'transparent';

                        // Force text colour on every cell and neutralise
                        // Bootstrap's --bs-table-accent-bg variable.
                        table.querySelectorAll('th, td').forEach(c => {
                            c.style.setProperty('color', txt, 'important');
                            c.style.setProperty('--bs-table-accent-bg', 'transparent');
                            c.style.borderLeftColor = 'transparent';
                            c.style.borderRightColor = 'transparent';
                        });

                        // Alternate row backgrounds (mirrors results.css)
                        table.querySelectorAll('tbody > tr').forEach((row, i) => {
                            row.style.backgroundColor = (i % 2 === 0)
                                ? 'rgba(255,255,255,0.1)'
                                : 'rgba(30,30,30,0.7)';
                        });

                        // Accent elements
                        w?.querySelectorAll('.album-link').forEach(a => {
                            a.style.color = accent;
                        });
                        w?.querySelectorAll('.release-badge').forEach(b => {
                            b.style.backgroundColor = accent;
                            b.style.color = 'white';
                        });
                    }
                },
            }).then(canvas => {
                const link = document.createElement('a');
                link.href = canvas.toDataURL('image/jpeg', 0.95);
                // Read username and year from the global APP_DATA object
                link.download = `scrobblescope_${APP_DATA.username}_${APP_DATA.year}.jpg`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                showToast('Image saved successfully!');
            }).catch(err => {
                console.error('Error creating image:', err);
                showToast('Failed to create image.', 'error');
            });
        });
    }

});
