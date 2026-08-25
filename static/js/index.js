// static/js/index.js
document.addEventListener('DOMContentLoaded', () => {
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
    updateFilterTags();
  });

  /* ---------- Username & year validation ---------- */
  const usernameInput    = document.getElementById('username');
  const yearSelect       = document.getElementById('year');
  const releaseYearInput = document.getElementById('release_year');
  const yearHint         = document.getElementById('year-hint');
  const usernameError    = document.createElement('div');
  // field__error is ours. The Bootstrap classes this used to carry
  // (invalid-feedback, form-text, text-danger) left the page with Bootstrap.
  usernameError.className = 'field__error';
  usernameInput.parentNode.appendChild(usernameError);

  // Year inline warning (no green/checkmark — only shows on error)
  const yearWarning = document.createElement('div');
  yearWarning.className = 'field__error';
  yearWarning.style.display = 'none';
  if (yearSelect) yearSelect.parentNode.appendChild(yearWarning);

  // Custom Release Year inline warning
  const releaseYearWarning = document.createElement('div');
  releaseYearWarning.className = 'field__error';
  releaseYearWarning.style.display = 'none';
  if (releaseYearInput) releaseYearInput.parentNode.appendChild(releaseYearWarning);

  let registeredYear = null;
  let validationTimeout = null;

  // What the year field says before any account is known. Captured at load
  // so a second username can be given the page back exactly as it started.
  const defaultYearMin = yearSelect ? yearSelect.min : '';
  const defaultYearHint = yearHint ? yearHint.textContent : '';

  /** Forget everything the last validated account taught us about years.
   *
   * The join year is a property of one account. Left in place it becomes a
   * claim about the next one: a second, valid username kept the first
   * account's "joined 2002" hint, its minimum, and the error text naming a
   * year that account never joined in.
   */
  function clearRegistrationState() {
    registeredYear = null;
    if (yearSelect) yearSelect.min = defaultYearMin;
    if (yearHint) yearHint.textContent = defaultYearHint;
    // The warning on screen is part of what the last account taught us, and
    // the docstring above already promised to clear it. It names that
    // account's join year, so leaving it up contradicts the hint and the
    // minimum this function has just reset: the field reads "2002-2026"
    // while the error under it demands 2015 or later.
    //
    // Re-derive rather than clear. "Year cannot be in the future" is still
    // true about whatever is in the box and has to survive; only the part
    // that belonged to the old account goes.
    validateYear();
  }

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
  decadeWarning.className = 'field__error';
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
    // Bootstrap's .invalid-feedback was hidden unless a sibling carried
    // .is-invalid, so dropping the class hid stale text for free. The
    // replacement is hidden only while it is empty, so it has to be emptied.
    usernameError.textContent = '';
    clearRegistrationState();
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
        // A 5xx is the service failing, not a verdict about the username.
        // This form carries no novalidate, so a custom validity error from a
        // transient outage makes the browser refuse the submit outright --
        // the same trap the heatmap form hits through its explicit guard.
        // Show what happened and leave the field submittable; the catch
        // below already treats a network failure this way.
        if (res.status >= 500) {
          if (usernameInput.value.trim() !== username) return;
          usernameInput.classList.remove('is-valid', 'is-invalid');
          usernameInput.setCustomValidity('');
          usernameError.textContent =
            data.message || 'Validation service unavailable. Try again.';
          return;
        }
        // The answer belongs to the username that was asked about. Editing
        // the field while the request is in flight would otherwise land a
        // rejection on whatever is in the box by then, and this form uses
        // native validation, so a stale setCustomValidity blocks the real
        // submit until the next blur.
        if (usernameInput.value.trim() !== username) return;
        if (data.valid) {
          usernameInput.classList.remove('is-invalid');
          usernameInput.classList.add('is-valid');
          usernameInput.setCustomValidity('');
          usernameError.textContent = '';

          // A valid account with no registration data still has to clear the
          // last one's, or it inherits a join year it never had.
          if (!data.registered_year) {
            clearRegistrationState();
            updateDecadePills();
          }

          // Dynamically set year min based on registration date
          if (data.registered_year && yearSelect) {
            registeredYear = data.registered_year;
            yearSelect.min = registeredYear;
            // The hint carries the join year once we know it. It is the whole
            // reason the field no longer needs a "?" popover: the range shown
            // is the range this account can actually answer for.
            if (yearHint) {
              yearHint.textContent = `joined ${registeredYear}`;
            }
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

  /* ---------- Thresholds: steppers, summary, reset ---------- */
  // The two minimums are real number inputs now, not selects of fixed values.
  // The buttons only move the input; every reader listens to its input event,
  // so keyboard entry and the buttons take the same path.
  const minPlays  = document.getElementById('min_plays');
  const minTracks = document.getElementById('min_tracks');
  const thresholdSummary = document.getElementById('threshold-summary');
  const thresholdReset   = document.getElementById('threshold_reset');
  const limitResults     = document.getElementById('limit_results');

  function clampToBounds(input) {
    const min = parseInt(input.min, 10);
    const max = parseInt(input.max, 10);
    let value = parseInt(input.value, 10);
    if (Number.isNaN(value)) value = min;
    return Math.min(max, Math.max(min, value));
  }

  function nudge(input, step) {
    input.value = String(Math.min(
      parseInt(input.max, 10),
      Math.max(parseInt(input.min, 10), clampToBounds(input) + step)
    ));
    input.dispatchEvent(new Event('input', { bubbles: true }));
  }

  document.querySelectorAll('.stepper__btn').forEach((button) => {
    button.addEventListener('click', () => {
      const target = document.getElementById(button.dataset.target);
      if (target) nudge(target, parseInt(button.dataset.step, 10));
    });
  });

  // The steppers reach 1, and "1 tracks" is the kind of small wrongness that
  // makes a careful interface look careless.
  function countOf(value, noun) {
    return `≥${value} ${noun}${value === 1 ? '' : 's'}`;
  }

  function updateThresholdSummary() {
    if (!thresholdSummary || !minPlays || !minTracks) return;
    // ≥ is the greater-or-equal glyph the content rules require.
    thresholdSummary.textContent = [
      countOf(clampToBounds(minPlays), 'play'),
      countOf(clampToBounds(minTracks), 'track'),
    ].join(' · ');
  }

  [minPlays, minTracks].forEach((input) => {
    if (!input) return;
    input.addEventListener('input', () => {
      updateThresholdSummary();
      updateFilterTags();
    });
    // A typed value outside the range is only corrected when the field is
    // left, so the user can still type "1" on the way to "15".
    input.addEventListener('blur', () => {
      input.value = String(clampToBounds(input));
      updateThresholdSummary();
      updateFilterTags();
    });
  });

  if (thresholdReset) {
    thresholdReset.addEventListener('click', () => {
      if (minPlays) minPlays.value = '10';
      if (minTracks) minTracks.value = '3';
      updateThresholdSummary();
      updateFilterTags();
    });
  }

  /* ---------- Invalid fields inside a closed disclosure ---------- */
  // Both thresholds are required, so clearing one and pressing Enter is now
  // refused instead of sending "" to the server, which failed at int("") and
  // reported it as a bad year. But the fields live inside a closed <details>,
  // and Chromium does not open it to report the message -- measured: the
  // submit is blocked, the disclosure stays shut, and the reader sees a
  // button that does nothing. Open it so the message has somewhere to land.
  //
  // Capture phase, because the invalid event does not bubble.
  const albumForm = document.querySelector('#album-form-section form');
  if (albumForm) {
    albumForm.addEventListener(
      'invalid',
      (event) => {
        const disclosure = event.target.closest('details');
        if (disclosure) disclosure.open = true;
      },
      true
    );
  }

  /* ---------- Filter tags ---------- */
  // A read-only echo of the four settings that change what comes back. It
  // saves reopening the disclosure to check what is set.
  const filterTags = document.getElementById('filter-tags');

  function tagText(name) {
    const year = parseInt(yearSelect.value, 10);
    if (name === 'year') {
      return Number.isNaN(year) ? 'no year' : String(year);
    }
    if (name === 'scope') {
      if (scope.value === 'all') return 'all years';
      if (scope.value === 'decade') {
        const checked = document.querySelector('.decade-radio:checked');
        return checked ? checked.value : 'no decade';
      }
      if (scope.value === 'custom') {
        return releaseYearInput.value ? `release ${releaseYearInput.value}` : 'any release';
      }
      if (Number.isNaN(year)) return 'release year';
      return `release ${scope.value === 'previous' ? year - 1 : year}`;
    }
    if (name === 'sort') {
      const checked = document.querySelector('input[name="sort_by"]:checked');
      return checked && checked.value === 'playtime' ? 'play time' : 'play count';
    }
    return countOf(clampToBounds(minPlays), 'play');
  }

  function updateFilterTags() {
    if (!filterTags) return;
    filterTags.querySelectorAll('[data-tag]').forEach((tag) => {
      tag.textContent = tagText(tag.dataset.tag);
    });
  }

  document.querySelectorAll('input[name="sort_by"]').forEach((radio) => {
    radio.addEventListener('change', updateFilterTags);
  });
  document.querySelectorAll('.decade-radio').forEach((radio) => {
    radio.addEventListener('change', updateFilterTags);
  });
  if (yearSelect) yearSelect.addEventListener('input', updateFilterTags);
  if (releaseYearInput) releaseYearInput.addEventListener('input', updateFilterTags);
  if (limitResults) limitResults.addEventListener('change', updateFilterTags);

  /* ---------- Initial state sync ---------- */
  toggleReleaseOptions();           // set decade/custom vis on first load
  updateThresholdSummary();
  updateFilterTags();
});
