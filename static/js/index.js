// Dark mode toggle
const darkSwitch = document.getElementById('darkSwitch');

// Check for saved dark mode preference
if (localStorage.getItem('darkMode') === 'true') {
  document.body.classList.add('dark-mode');
  darkSwitch.checked = true;
}

// Add event listener for dark mode toggle
darkSwitch.addEventListener('change', function() {
  document.body.classList.toggle('dark-mode', this.checked);
  localStorage.setItem('darkMode', this.checked);
});

// Release filter options
const scope = document.getElementById('release_scope');
const decadeDropdown = document.getElementById('decade_dropdown');
const releaseYearGroup = document.getElementById('release_year_group');

// Display appropriate fields based on release scope
function toggleReleaseOptions() {
  decadeDropdown.style.display = (scope.value === 'decade') ? 'block' : 'none';
  releaseYearGroup.style.display = (scope.value === 'custom') ? 'block' : 'none';
}

// Attach event listener for release options
scope.addEventListener('change', toggleReleaseOptions);

// Threshold settings toggle
const thresholdSwitch = document.getElementById('thresholdSwitch');
const thresholdSettings = document.getElementById('thresholdSettings');

thresholdSwitch.addEventListener('change', function() {
  thresholdSettings.style.display = this.checked ? 'block' : 'none';
});

// Initialize form state after DOM loads
document.addEventListener('DOMContentLoaded', function() {
  toggleReleaseOptions();
});
