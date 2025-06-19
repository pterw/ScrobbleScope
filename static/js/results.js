// Dark mode toggle
const darkSwitch = document.getElementById('darkSwitch');
if (localStorage.getItem('darkMode') === 'true') {
    document.body.classList.add('dark-mode');
    darkSwitch.checked = true;
}

darkSwitch.addEventListener('change', function () {
    document.body.classList.toggle('dark-mode', this.checked);
    localStorage.setItem('darkMode', this.checked);

    const svgElement = document.querySelector('#logo-wrapper svg');
    if (svgElement) {
        const bars = svgElement.querySelectorAll('.cls-1');
        const textPaths = svgElement.querySelectorAll('#logo-text path, #tagline path');

        if (this.checked) {
            bars.forEach(bar => bar.setAttribute('stroke', '#9370DB'));
            textPaths.forEach(path => path.setAttribute('fill', '#f8f9fa'));
        } else {
            bars.forEach(bar => bar.setAttribute('stroke', '#6a4baf'));
            textPaths.forEach(path => path.setAttribute('fill', '#333333'));
        }
    }
});

function showToast(message, type = 'info', duration = 3000) {
    const toastContainer = document.getElementById('toastContainer');
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast show" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header${type === 'error' ? ' bg-danger text-white' : ''}">
                <strong class="me-auto">ScrobbleScope</strong>
                <small>Just now</small>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body${type === 'error' ? ' bg-danger text-white' : ''}">
                ${message}
            </div>
        </div>
    `;
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    setTimeout(() => {
        const toast = document.getElementById(toastId);
        if (toast) {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 500);
        }
    }, duration);
}

function fetchUnmatchedAlbums() {
    const unmatchedList = document.getElementById('unmatched-list');
    fetch('/unmatched')
        .then(response => response.json())
        .then(unmatchedData => {
            let html = '';
            if (!unmatchedData || Object.keys(unmatchedData.data || unmatchedData).length === 0) {
                html = '<p>No unmatched albums found.</p>';
            } else {
                const data = unmatchedData.data || unmatchedData;
                const count = unmatchedData.count || Object.keys(data).length;
                html = `<p>Found ${count} unmatched albums:</p>`;
                html += '<div class="table-responsive"><table class="table table-sm">';
                html += '<thead><tr><th>Artist</th><th>Album</th><th>Reason</th></tr></thead><tbody>';
                for (const key in data) {
                    const item = data[key];
                    html += `<tr><td>${item.artist}</td><td>${item.album}</td><td>${item.reason}</td></tr>`;
                }
                html += '</tbody></table></div>';
            }
            unmatchedList.innerHTML = html;
        })
        .catch(error => {
            unmatchedList.innerHTML = `<div class="alert alert-danger">Error loading unmatched albums: ${error}</div>`;
        });
}

document.getElementById('view-unmatched-quick').addEventListener('click', fetchUnmatchedAlbums);
if (document.getElementById('view-unmatched')) {
    document.getElementById('view-unmatched').addEventListener('click', fetchUnmatchedAlbums);
}

document.getElementById('export-csv').addEventListener('click', function () {
    try {
        const table = document.querySelector('.table');
        if (!table) {
            showToast('No data available to export', 'error');
            return;
        }
        let csvContent = [];
        const headerRow = [];
        const headers = table.querySelectorAll('thead th');
        headers.forEach(header => {
            headerRow.push('"' + header.textContent.trim().replace(/"/g, '""') + '"');
        });
        csvContent.push(headerRow.join(','));
        const rows = table.querySelectorAll('tbody tr');
        for (let i = 0; i < rows.length; i++) {
            const row = [];
            const cells = Array.from(rows[i].querySelectorAll('th, td'));
            for (let j = 0; j < cells.length; j++) {
                let content = '';
                if (j === 1 && cells[j].classList.contains('album-title')) {
                    const albumInfo = cells[j].querySelector('.album-info');
                    content = albumInfo ? albumInfo.textContent.trim() : '';
                } else {
                    content = cells[j].textContent.trim();
                }
                content = content.replace(/\s+/g, ' ');
                if (content.includes(',') || content.includes('"') || content.includes('\n')) {
                    content = '"' + content.replace(/"/g, '""') + '"';
                }
                row.push(content);
            }
            csvContent.push(row.join(','));
        }
        const csvString = csvContent.join('\n');
        const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        const username = window.RESULTS.username;
        const year = window.RESULTS.year;
        link.setAttribute('href', url);
        link.setAttribute('download', `scrobblescope_${username}_${year}_albums.csv`);
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        showToast('CSV file downloaded successfully!');
    } catch (error) {
        console.error('Error exporting CSV:', error);
        showToast('Error creating CSV file: ' + error.message, 'error');
    }
});

document.getElementById('save-image').addEventListener('click', function () {
    showToast('Creating image... Please wait.');
    const targetElement = document.getElementById('results-table-wrapper');
    if (!targetElement) {
        showToast('No content to save as image', 'error');
        return;
    }
    const isDarkMode = document.body.classList.contains('dark-mode');
    html2canvas(targetElement, {
        backgroundColor: isDarkMode ? '#121212' : '#ffffff',
        allowTaint: true,
        useCORS: true,
        scale: 2,
        onclone: function(clonedDoc) {
            const clonedTable = clonedDoc.querySelector('.table');
            if (clonedTable && isDarkMode) {
                clonedTable.style.color = '#f8f9fa';
                clonedTable.style.backgroundColor = '#121212';
                clonedTable.querySelectorAll('tr').forEach((row, index) => {
                    if (index % 2 === 1) {
                        row.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                    } else if (index > 0) {
                        row.style.backgroundColor = 'rgba(30, 30, 30, 0.7)';
                    }
                    row.querySelectorAll('th, td').forEach(cell => {
                        cell.style.color = '#f8f9fa';
                        cell.style.borderColor = 'rgba(255, 255, 255, 0.1)';
                    });
                });
                const header = clonedTable.querySelector('thead');
                if (header) {
                    header.style.backgroundColor = '#343a40';
                    header.style.color = '#ffffff';
                }
            }
        }
    }).then(function(canvas) {
        try {
            const link = document.createElement('a');
            const username = window.RESULTS.username;
            const year = window.RESULTS.year;
            link.download = `scrobblescope_${username}_${year}.jpg`;
            link.href = canvas.toDataURL('image/jpeg', 0.95);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            showToast('Image saved successfully!');
        } catch (err) {
            console.error('Error saving image:', err);
            showToast('Failed to save image: ' + err.message, 'error');
        }
    }).catch(function(err) {
        console.error('Error capturing image:', err);
        showToast('Failed to create image: ' + err.message, 'error');
    });
});
