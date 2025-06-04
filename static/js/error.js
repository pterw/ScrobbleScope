
// Dark mode persistence + switch sync
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
            
// Manually update SVG colors when dark mode changes
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
});
        
// Initialize SVG colors based on current theme
window.addEventListener('DOMContentLoaded', () => {
    const isDark = document.body.classList.contains('dark-mode');
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
});