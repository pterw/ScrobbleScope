// static/js/error.js
document.addEventListener('DOMContentLoaded', () => {
  /* ---------- dark-mode toggle ---------- */
  const darkSwitch   = document.getElementById('darkSwitch');
  const svgElement   = document.querySelector('#logo-wrapper svg');

  const updateSvgColors = (isDark) => {
    if (!svgElement) return;
    const bars       = svgElement.querySelectorAll('.cls-1');
    const textPaths  = svgElement.querySelectorAll('#logo-text path, #tagline path');

    const barStroke  = isDark ? '#9370DB' : '#6a4baf';
    const textFill   = isDark ? '#f8f9fa' : '#333333';

    bars.forEach(b => b.setAttribute('stroke', barStroke));
    textPaths.forEach(p => p.setAttribute('fill', textFill));
  };

  // Apply saved preference → set initial UI + SVG
  const prefersDark = localStorage.getItem('darkMode') === 'true';
  if (prefersDark) {
    document.body.classList.add('dark-mode');
    darkSwitch.checked = true;
  }
  updateSvgColors(prefersDark);

  // Toggle handler
  darkSwitch.addEventListener('change', () => {
    const isDark = darkSwitch.checked;
    document.body.classList.toggle('dark-mode', isDark);
    localStorage.setItem('darkMode', isDark);
    updateSvgColors(isDark);
  });
});
