// Dark mode persistence and switch sync
const darkSwitch = document.getElementById('darkSwitch');
const prefersDark = localStorage.getItem('darkMode') === 'true';

if (prefersDark) {
    document.body.classList.add('dark-mode');
    darkSwitch.checked = true;
}

darkSwitch.addEventListener('change', () => {
    const isDark = darkSwitch.checked;
    document.body.classList.toggle('dark-mode', isDark);
    localStorage.setItem('darkMode', isDark);

    const svgElement = document.querySelector('#logo-wrapper svg');
    if (svgElement) {
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

    if (isDark) {
        document.querySelectorAll('.table tbody tr td, .table tbody tr th').forEach(cell => {
            cell.style.color = '#f8f9fa';
        });
        document.querySelectorAll('.table thead th').forEach(header => {
            header.style.color = '#ffffff';
            header.style.backgroundColor = '#343a40';
        });
    } else {
        document.querySelectorAll('.table tbody tr td, .table tbody tr th').forEach(cell => {
            cell.style.color = '';
        });
        document.querySelectorAll('.table thead th').forEach(header => {
            header.style.color = '';
            header.style.backgroundColor = '';
        });
    }
});

if (prefersDark) {
    document.querySelectorAll('.table tbody tr td, .table tbody tr th').forEach(cell => {
        cell.style.color = '#f8f9fa';
    });
    document.querySelectorAll('.table thead th').forEach(header => {
        header.style.color = '#ffffff';
        header.style.backgroundColor = '#343a40';
    });
}
