// static/js/index.js
document.addEventListener('DOMContentLoaded', () => {
  /* ---------- Dark-mode toggle ---------- */
  const darkSwitch = document.getElementById('darkSwitch');

  // Apply saved preference
  if (localStorage.getItem('darkMode') === 'true') {
    document.body.classList.add('dark-mode');
    darkSwitch.checked = true;
  }

  // Live toggle
  darkSwitch.addEventListener('change', () => {
    document.body.classList.toggle('dark-mode', darkSwitch.checked);
    localStorage.setItem('darkMode', darkSwitch.checked);
  });

  /* ---------- Release-scope dropdowns ---------- */
  const scope            = document.getElementById('release_scope');
  const decadeDropdown   = document.getElementById('decade_dropdown');
  const releaseYearGroup = document.getElementById('release_year_group');

  const toggleReleaseOptions = () => {
    decadeDropdown.style.display   = scope.value === 'decade' ? 'block' : 'none';
    releaseYearGroup.style.display = scope.value === 'custom' ? 'block' : 'none';
  };

  scope.addEventListener('change', toggleReleaseOptions);

  /* ---------- Threshold settings ---------- */
  const thresholdSwitch   = document.getElementById('thresholdSwitch');
  const thresholdSettings = document.getElementById('thresholdSettings');

  thresholdSwitch.addEventListener('change', () => {
    thresholdSettings.style.display = thresholdSwitch.checked ? 'block' : 'none';
  });

  /* ---------- Initial state sync ---------- */
  toggleReleaseOptions();           // set decade/custom vis on first load
});
