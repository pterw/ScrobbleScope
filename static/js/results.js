// static/js/results.js

document.addEventListener('DOMContentLoaded', () => {
    //Dark Mode Logic
    const darkSwitch = document.getElementById('darkSwitch');
    if (localStorage.getItem('darkMode') === 'true') {
        document.body.classList.add('dark-mode');
        if (darkSwitch) darkSwitch.checked = true;
    }
    if (darkSwitch) {
        darkSwitch.addEventListener('change', function() {
            document.body.classList.toggle('dark-mode', this.checked);
            localStorage.setItem('darkMode', this.checked);
            updateSvgColors(this.checked);
        });
    }

    function updateSvgColors(isDark) {
        const svgElement = document.querySelector('#logo-wrapper svg');
        if (!svgElement) return;
        const bars = svgElement.querySelectorAll('.cls-1');
        const textPaths = svgElement.querySelectorAll('#logo-text path, #tagline path');
        if (isDark) {
            bars.forEach(bar => bar.setAttribute('stroke', '#9370DB'));
            textPaths.forEach(path => path.setAttribute('fill', '#f8f9fa'));
        } else {
            bars.forEach(bar => bar.setAttribute('stroke', '#6a4baf'));
            textPaths.forEach(path => path.setAttribute('fill', '#333333'));
        }
    }
    // Initial SVG color update on page load
    updateSvgColors(darkSwitch ? darkSwitch.checked : false);


    // Toast Notification Helper
    function showToast(message, type = 'info', duration = 3000) {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) return;
        const toastId = 'toast-' + Date.now();
        const toastHtml = `
            <div id="${toastId}" class="toast show" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header${type === 'error' ? ' bg-danger text-white' : ''}">
                    <strong class="me-auto">ScrobbleScope</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>`;
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        setTimeout(() => {
            const toast = document.getElementById(toastId);
            if (toast) toast.classList.remove('show');
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

        fetch('/unmatched')
            .then(response => response.json())
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
                        html += `<tr><td>${item.artist}</td><td>${item.album}</td><td>${item.reason}</td></tr>`;
                    }
                    html += `</tbody></table></div>`;
                }
                unmatchedList.innerHTML = html;
            })
            .catch(error => {
                unmatchedList.innerHTML = `<div class="alert alert-danger">Error loading unmatched albums: ${error}</div>`;
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
                            content = cell.textContent.trim();
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
            
            html2canvas(targetElement, {
                scale: 2,
                useCORS: true,
                backgroundColor: document.body.classList.contains('dark-mode') ? '#121212' : '#ffffff',
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