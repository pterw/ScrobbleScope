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

  scope.addEventListener('change', () => {
    toggleReleaseOptions();
    updateDecadePills();
  });

  /* ---------- Threshold settings ---------- */
  const thresholdSwitch   = document.getElementById('thresholdSwitch');
  const thresholdSettings = document.getElementById('thresholdSettings');

  thresholdSwitch.addEventListener('change', () => {
    thresholdSettings.style.display = thresholdSwitch.checked ? 'block' : 'none';
  });

  /* ---------- Username & year validation ---------- */
  const usernameInput    = document.getElementById('username');
  const yearSelect       = document.getElementById('year');
  const releaseYearInput = document.getElementById('release_year');
  const usernameError    = document.createElement('div');
  usernameError.className = 'invalid-feedback';
  usernameInput.parentNode.appendChild(usernameError);

  // Year inline warning (no green/checkmark — only shows on error)
  const yearWarning = document.createElement('div');
  yearWarning.className = 'form-text text-danger';
  yearWarning.style.display = 'none';
  if (yearSelect) yearSelect.parentNode.appendChild(yearWarning);

  // Custom Release Year inline warning
  const releaseYearWarning = document.createElement('div');
  releaseYearWarning.className = 'form-text text-danger';
  releaseYearWarning.style.display = 'none';
  if (releaseYearInput) releaseYearInput.parentNode.appendChild(releaseYearWarning);

  let registeredYear = null;
  let validationTimeout = null;

  // Helper: check if a string contains any non-numeric characters (besides leading minus)
  function hasNonNumeric(str) {
    return /[^0-9]/.test(str);
  }

  function clearYearValidation() {
    if (!yearSelect) return;
    yearSelect.classList.remove('is-invalid', 'is-valid');
    yearWarning.textContent = '';
    yearWarning.style.display = 'none';
  }

  function validateYear() {
    if (!yearSelect) return;
    const raw = yearSelect.value;

    // Non-numeric input: warn immediately
    if (raw && hasNonNumeric(raw)) {
      yearSelect.classList.add('is-invalid');
      yearWarning.textContent = 'Please enter a valid year (numbers only).';
      yearWarning.style.display = 'block';
      return;
    }

    // Empty or fewer than 4 digits: clear any warnings silently
    if (!raw || raw.length < 4) {
      clearYearValidation();
      return;
    }

    // 4+ digits — validate bounds
    const val = parseInt(raw, 10);
    const max = parseInt(yearSelect.max, 10);
    const min = registeredYear || parseInt(yearSelect.min, 10);

    if (val < min) {
      yearSelect.classList.add('is-invalid');
      if (registeredYear) {
        yearWarning.textContent = `This user joined Last.fm in ${registeredYear}. Year must be ${registeredYear} or later.`;
      } else {
        yearWarning.textContent = `Year must be ${min} or later.`;
      }
      yearWarning.style.display = 'block';
    } else if (val > max) {
      yearSelect.classList.add('is-invalid');
      yearWarning.textContent = 'Year cannot be in the future.';
      yearWarning.style.display = 'block';
    } else {
      // Valid — just clear, no green styling
      clearYearValidation();
      updateDecadePills();
    }
  }

  function clearReleaseYearValidation() {
    if (!releaseYearInput) return;
    releaseYearInput.classList.remove('is-invalid', 'is-valid');
    releaseYearWarning.textContent = '';
    releaseYearWarning.style.display = 'none';
  }

  function validateReleaseYear() {
    if (!releaseYearInput) return;
    const raw = releaseYearInput.value;

    if (raw && hasNonNumeric(raw)) {
      releaseYearInput.classList.add('is-invalid');
      releaseYearWarning.textContent = 'Please enter a valid year (numbers only).';
      releaseYearWarning.style.display = 'block';
      return;
    }

    if (!raw || raw.length < 4) {
      clearReleaseYearValidation();
      return;
    }

    const val = parseInt(raw, 10);
    const min = parseInt(releaseYearInput.min, 10);
    const max = parseInt(releaseYearInput.max, 10);

    if (val < min) {
      releaseYearInput.classList.add('is-invalid');
      releaseYearWarning.textContent = `Release year must be ${min} or later.`;
      releaseYearWarning.style.display = 'block';
    } else if (val > max) {
      releaseYearInput.classList.add('is-invalid');
      releaseYearWarning.textContent = 'Release year cannot be in the future.';
      releaseYearWarning.style.display = 'block';
    } else {
      clearReleaseYearValidation();
    }
  }

  if (yearSelect) {
    yearSelect.addEventListener('input', validateYear);
  }
  if (releaseYearInput) {
    releaseYearInput.addEventListener('input', validateReleaseYear);
  }

  /* ---------- Decade cross-validation ---------- */
  const decadePills  = document.querySelectorAll('.decade-radio');
  const decadeLabels = document.querySelectorAll('.decade-pill');

  // Decade warning shown below the pills
  const decadeWarning = document.createElement('div');
  decadeWarning.className = 'form-text text-danger mt-1';
  decadeWarning.style.display = 'none';
  if (decadeDropdown) decadeDropdown.appendChild(decadeWarning);

  function getDecadeStart(decadeValue) {
    // "2020s" → 2020, "1990s" → 1990
    return parseInt(decadeValue.replace('s', ''), 10);
  }

  function updateDecadePills() {
    if (!yearSelect) return;
    const listeningYear = parseInt(yearSelect.value, 10);
    // Only apply logic if we have a valid 4-digit listening year
    if (!listeningYear || yearSelect.value.length < 4) {
      // Reset all pills to enabled
      decadePills.forEach((radio, i) => {
        radio.disabled = false;
        decadeLabels[i].classList.remove('decade-pill-disabled');
      });
      decadeWarning.style.display = 'none';
      return;
    }

    let selectedDisabled = false;
    decadePills.forEach((radio, i) => {
      const decadeStart = getDecadeStart(radio.value);
      // A decade is impossible if it starts AFTER the listening year
      // e.g. listening in 2016, "2020s" starts at 2020 — impossible
      const impossible = decadeStart > listeningYear;
      radio.disabled = impossible;
      decadeLabels[i].classList.toggle('decade-pill-disabled', impossible);

      if (impossible && radio.checked) {
        selectedDisabled = true;
      }
    });

    // If the currently selected decade became impossible, auto-select the first valid one
    if (selectedDisabled) {
      for (const radio of decadePills) {
        if (!radio.disabled) {
          radio.checked = true;
          break;
        }
      }
      decadeWarning.textContent = 'Selected decade was adjusted — albums from that decade couldn\'t exist in your listening year.';
      decadeWarning.style.display = 'block';
    } else {
      decadeWarning.style.display = 'none';
    }
  }

  // Re-validate decades when listening year changes
  if (yearSelect) {
    yearSelect.addEventListener('input', updateDecadePills);
  }

  /* ---------- Username validation (blur) ---------- */
  // Clear validation block while the user is still typing
  usernameInput.addEventListener('input', () => {
    usernameInput.setCustomValidity('');
    usernameInput.classList.remove('is-valid', 'is-invalid');
  });

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
          usernameInput.setCustomValidity('');

          // Dynamically set year min based on registration date
          if (data.registered_year && yearSelect) {
            registeredYear = data.registered_year;
            yearSelect.min = registeredYear;
            validateYear();
            updateDecadePills();
          }
        } else {
          usernameInput.classList.remove('is-valid');
          usernameInput.classList.add('is-invalid');
          usernameError.textContent = data.message || 'Username not found on Last.fm';
          usernameInput.setCustomValidity(data.message || 'Username not found on Last.fm');
        }
      } catch (e) {
        // Network error — clear validity so the server can handle it
        usernameInput.setCustomValidity('');
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
