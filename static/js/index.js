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

  /* ---------- Username validation ---------- */
  const usernameInput = document.getElementById('username');
  const yearSelect = document.getElementById('year');
  const usernameError = document.createElement('div');
  usernameError.className = 'invalid-feedback';
  usernameInput.parentNode.appendChild(usernameError);

  let validationTimeout = null;

  usernameInput.addEventListener('blur', async () => {
    const username = usernameInput.value.trim();

    if (!username) {
      usernameInput.classList.remove('is-valid', 'is-invalid');
      return;
    }

    clearTimeout(validationTimeout);
    validationTimeout = setTimeout(async () => {
      try {
        const res = await fetch(`/validate_user?username=${encodeURIComponent(username)}`);
        const data = await res.json();
        if (data.valid) {
          usernameInput.classList.remove('is-invalid');
          usernameInput.classList.add('is-valid');
        } else {
          usernameInput.classList.remove('is-valid');
          usernameInput.classList.add('is-invalid');
          usernameError.textContent = data.message || 'Username not found on Last.fm';
        }
      } catch (e) {
        // Silently fail — validation is a nicety, not a blocker
      }
    }, 300);
  });

  /* ---------- Welcome modal (first visit) ---------- */
  const welcomeModal = document.getElementById('welcomeModal');
  if (welcomeModal && !localStorage.getItem('seenWelcome')) {
    const modal = new bootstrap.Modal(welcomeModal);
    modal.show();
    welcomeModal.addEventListener('hidden.bs.modal', () => {
      localStorage.setItem('seenWelcome', 'true');
    }, { once: true });
  }

  /* ---------- Bootstrap popovers ---------- */
  const popoverTriggers = document.querySelectorAll('[data-bs-toggle="popover"]');
  popoverTriggers.forEach(el => {
    new bootstrap.Popover(el, { placement: 'top', container: 'body' });
  });

  /* ---------- Initial state sync ---------- */
  toggleReleaseOptions();           // set decade/custom vis on first load
});
