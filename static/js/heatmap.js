// static/js/heatmap.js -- Heatmap pill switching, AJAX submission,
// polling, SVG grid rendering, tooltips, and dark mode support.
// No innerHTML with user data (XSS criterion F-B18-9).
(function () {
  'use strict';

  // ----------------------------------------------------------------
  // Constants
  // ----------------------------------------------------------------
  const POLL_INTERVAL_MS = 1000;
  const SVG_NS = 'http://www.w3.org/2000/svg';

  // rocket_r palette stops (sampled from matplotlib/seaborn rocket_r).
  const ROCKET_STOPS = [
    { pos: 0.00, r: 3,   g: 5,   b: 26  },  // #03051a (near-black)
    { pos: 0.17, r: 42,  g: 15,  b: 78  },  // #2a0f4e (deep purple)
    { pos: 0.33, r: 106, g: 23,  b: 110 },  // #6a176e (purple-red)
    { pos: 0.50, r: 166, g: 44,  b: 92  },  // #a62c5c (red)
    { pos: 0.67, r: 212, g: 78,  b: 65  },  // #d44e41 (orange-red)
    { pos: 0.83, r: 240, g: 144, b: 58  },  // #f0903a (orange)
    { pos: 1.00, r: 249, g: 213, b: 118 },  // #f9d576 (cream-gold)
  ];

  // Grid geometry
  const CELL_SIZE  = 13;
  const CELL_GAP   = 3;
  const STEP       = CELL_SIZE + CELL_GAP;
  const LEFT_PAD   = 32;  // space for day-of-week labels
  const TOP_PAD    = 20;  // space for month labels
  const CORNER_R   = 2;   // rect corner radius

  const MONTH_NAMES = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
  ];

  const DAY_LABELS = [
    { row: 0, text: 'Mon' },
    { row: 2, text: 'Wed' },
    { row: 4, text: 'Fri' },
  ];

  // ----------------------------------------------------------------
  // Helpers
  // ----------------------------------------------------------------

  /** Convert JS Date getDay() (Sun=0) to Mon=0..Sun=6. */
  function mondayIndex(d) {
    return (d.getDay() + 6) % 7;
  }

  /** Parse 'YYYY-MM-DD' as a local Date (avoids timezone shift). */
  function parseLocalDate(s) {
    const parts = s.split('-');
    return new Date(+parts[0], +parts[1] - 1, +parts[2]);
  }

  /** Format a date as "Sunday 1 March 2026". */
  function formatDateLong(d) {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday',
                  'Thursday', 'Friday', 'Saturday'];
    const months = ['January', 'February', 'March', 'April', 'May', 'June',
                    'July', 'August', 'September', 'October', 'November', 'December'];
    return days[d.getDay()] + ' ' + d.getDate() + ' ' + months[d.getMonth()] + ' ' + d.getFullYear();
  }

  /** Add N days to a Date (returns new Date). */
  function addDays(d, n) {
    const r = new Date(d);
    r.setDate(r.getDate() + n);
    return r;
  }

  /** Format date as YYYY-MM-DD. */
  function isoDate(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    return y + '-' + m + '-' + dd;
  }

  /** Interpolate between rocket_r stops for a value in [0, 1]. */
  function rocketColor(t) {
    t = Math.max(0, Math.min(1, t));
    for (let i = 0; i < ROCKET_STOPS.length - 1; i++) {
      const a = ROCKET_STOPS[i];
      const b = ROCKET_STOPS[i + 1];
      if (t >= a.pos && t <= b.pos) {
        const f = (t - a.pos) / (b.pos - a.pos);
        const r = Math.round(a.r + f * (b.r - a.r));
        const g = Math.round(a.g + f * (b.g - a.g));
        const bl = Math.round(a.b + f * (b.b - a.b));
        return 'rgb(' + r + ',' + g + ',' + bl + ')';
      }
    }
    const last = ROCKET_STOPS[ROCKET_STOPS.length - 1];
    return 'rgb(' + last.r + ',' + last.g + ',' + last.b + ')';
  }

  /** Map a count to [0, 1] using log scale. */
  function countToNorm(count, maxCount) {
    if (count <= 0 || maxCount <= 0) return 0;
    return Math.log10(count + 1) / Math.log10(maxCount + 1);
  }

  /** Zero-scrobble cell fill based on dark mode. */
  function zeroFill() {
    return document.body.classList.contains('dark-mode') ? '#2a2a2a' : '#e0e0e0';
  }

  /** Build the rocket_r CSS gradient string for the legend bar. */
  function legendGradient() {
    const stops = ROCKET_STOPS.map(function (s) {
      return 'rgb(' + s.r + ',' + s.g + ',' + s.b + ') ' + Math.round(s.pos * 100) + '%';
    });
    return 'linear-gradient(to right, ' + stops.join(', ') + ')';
  }

  // ----------------------------------------------------------------
  // DOM references (set on DOMContentLoaded)
  // ----------------------------------------------------------------
  var pills, albumSection, heatmapSection, heatmapLoading,
      heatmapResult, heatmapForm, heatmapUsernameInput,
      progressText, errorContainer, errorMessage,
      retryBtn, searchAgainBtn, resultTitle, resultSubtitle,
      gridContainer, legendBar, tooltip;

  // ----------------------------------------------------------------
  // State
  // ----------------------------------------------------------------
  var pollTimer = null;
  var currentJobId = null;
  var lastUsername = '';

  // ----------------------------------------------------------------
  // Pill switching
  // ----------------------------------------------------------------
  function initPills() {
    pills = document.querySelectorAll('.mode-pill');
    albumSection   = document.getElementById('album-form-section');
    heatmapSection = document.getElementById('heatmap-form-section');

    pills.forEach(function (pill) {
      pill.addEventListener('click', function () {
        var mode = this.getAttribute('data-mode');
        pills.forEach(function (p) { p.classList.remove('active'); });
        this.classList.add('active');

        if (mode === 'heatmap') {
          albumSection.classList.add('d-none');
          heatmapSection.classList.remove('d-none');
          // Hide result/loading if showing
          hideElement(heatmapLoading);
          hideElement(heatmapResult);
        } else {
          heatmapSection.classList.add('d-none');
          albumSection.classList.remove('d-none');
          hideElement(heatmapLoading);
          hideElement(heatmapResult);
        }
      });

      // Keyboard accessibility: Enter/Space toggles pill
      pill.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          this.click();
        }
      });
    });
  }

  // ----------------------------------------------------------------
  // Show/hide helpers with optional fade
  // ----------------------------------------------------------------
  function showElement(el) {
    el.classList.remove('d-none');
  }

  function hideElement(el) {
    el.classList.add('d-none');
  }

  function fadeIn(el) {
    el.classList.add('heatmap-fade', 'fading-out');
    el.classList.remove('d-none');
    // Force reflow then remove fading-out
    void el.offsetWidth;
    el.classList.remove('fading-out');
  }

  // ----------------------------------------------------------------
  // Username validation (blur)
  // ----------------------------------------------------------------
  function initUsernameValidation() {
    heatmapUsernameInput = document.getElementById('heatmap-username');
    if (!heatmapUsernameInput) return;

    var feedback = document.createElement('div');
    feedback.className = 'invalid-feedback';
    heatmapUsernameInput.parentNode.appendChild(feedback);

    heatmapUsernameInput.addEventListener('input', function () {
      this.classList.remove('is-valid', 'is-invalid');
      this.setCustomValidity('');
    });

    heatmapUsernameInput.addEventListener('blur', function () {
      var username = heatmapUsernameInput.value.trim();
      if (!username) {
        heatmapUsernameInput.classList.remove('is-valid', 'is-invalid');
        return;
      }

      fetch('/validate_user?username=' + encodeURIComponent(username))
        .then(function (res) { return res.json(); })
        .then(function (data) {
          if (data.valid) {
            heatmapUsernameInput.classList.remove('is-invalid');
            heatmapUsernameInput.classList.add('is-valid');
            heatmapUsernameInput.setCustomValidity('');
          } else {
            heatmapUsernameInput.classList.remove('is-valid');
            heatmapUsernameInput.classList.add('is-invalid');
            feedback.textContent = data.message || 'Username not found on Last.fm';
            heatmapUsernameInput.setCustomValidity(data.message || 'Username not found on Last.fm');
          }
        })
        .catch(function () {
          heatmapUsernameInput.setCustomValidity('');
        });
    });
  }

  // ----------------------------------------------------------------
  // CSRF token helper
  // ----------------------------------------------------------------
  function getCsrfToken() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
  }

  // ----------------------------------------------------------------
  // Form submission + polling
  // ----------------------------------------------------------------
  function initForm() {
    heatmapForm    = document.getElementById('heatmap-form');
    heatmapLoading = document.getElementById('heatmap-loading');
    heatmapResult  = document.getElementById('heatmap-result');
    progressText   = document.getElementById('heatmap-progress-text');
    errorContainer = document.getElementById('heatmap-error');
    errorMessage   = document.getElementById('heatmap-error-message');
    retryBtn       = document.getElementById('heatmap-retry-btn');
    searchAgainBtn = document.getElementById('heatmap-search-again');
    resultTitle    = document.getElementById('heatmap-result-title');
    resultSubtitle = document.getElementById('heatmap-result-subtitle');
    gridContainer  = document.getElementById('heatmap-grid');
    legendBar      = document.getElementById('heatmap-legend-bar');

    if (!heatmapForm) return;

    heatmapForm.addEventListener('submit', function (e) {
      e.preventDefault();
      var username = heatmapUsernameInput.value.trim();
      if (!username) {
        heatmapUsernameInput.classList.add('is-invalid');
        heatmapUsernameInput.focus();
        return;
      }
      lastUsername = username;
      submitHeatmap(username);
    });

    retryBtn.addEventListener('click', function () {
      if (lastUsername) {
        submitHeatmap(lastUsername);
      }
    });

    searchAgainBtn.addEventListener('click', function () {
      hideElement(heatmapResult);
      heatmapSection.classList.remove('d-none');
      heatmapUsernameInput.value = lastUsername;
      heatmapUsernameInput.classList.remove('is-valid', 'is-invalid');
      heatmapUsernameInput.focus();
    });
  }

  function submitHeatmap(username) {
    // Reset UI: show loading, hide form + result + error
    stopPolling();
    hideElement(heatmapSection);
    hideElement(heatmapResult);
    hideElement(errorContainer);
    progressText.textContent = 'Initializing...';
    // Show spinner wrapper if hidden
    var spinnerWrapper = heatmapLoading.querySelector('.heatmap-spinner-wrapper');
    if (spinnerWrapper) spinnerWrapper.style.display = '';
    fadeIn(heatmapLoading);

    var csrfToken = getCsrfToken();
    var body = new URLSearchParams();
    body.append('username', username);
    body.append('csrf_token', csrfToken);

    fetch('/heatmap_loading', {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: body.toString(),
    })
    .then(function (res) {
      return res.json().then(function (data) {
        return { status: res.status, data: data };
      });
    })
    .then(function (result) {
      if (result.status === 202 && result.data.job_id) {
        currentJobId = result.data.job_id;
        startPolling();
      } else {
        showError(result.data.message || 'Failed to start heatmap.', result.data.retryable);
      }
    })
    .catch(function () {
      showError('Network error. Please check your connection and try again.', true);
    });
  }

  function startPolling() {
    pollTimer = setInterval(pollProgress, POLL_INTERVAL_MS);
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  function pollProgress() {
    if (!currentJobId) return;

    fetch('/progress?job_id=' + encodeURIComponent(currentJobId))
      .then(function (res) { return res.json(); })
      .then(function (data) {
        // Update progress text
        if (data.message) {
          progressText.textContent = data.message;
        }

        if (data.error) {
          stopPolling();
          showError(data.message || 'An error occurred.', true);
          return;
        }

        if (data.progress >= 100) {
          stopPolling();
          fetchHeatmapData();
        }
      })
      .catch(function () {
        // Transient network error; keep polling
      });
  }

  function fetchHeatmapData() {
    progressText.textContent = 'Rendering heatmap...';

    fetch('/heatmap_data?job_id=' + encodeURIComponent(currentJobId))
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (data.error) {
          showError(data.message || 'Failed to load heatmap data.', data.retryable);
          return;
        }
        if (data.ready) {
          renderHeatmap(data);
        } else {
          // Still processing -- restart polling briefly
          startPolling();
        }
      })
      .catch(function () {
        showError('Failed to fetch heatmap results.', true);
      });
  }

  function showError(message, retryable) {
    // Hide spinner
    var spinnerWrapper = heatmapLoading.querySelector('.heatmap-spinner-wrapper');
    if (spinnerWrapper) spinnerWrapper.style.display = 'none';
    progressText.textContent = '';

    errorMessage.textContent = message;
    showElement(errorContainer);
    retryBtn.style.display = retryable ? '' : 'none';
  }

  // ----------------------------------------------------------------
  // SVG grid rendering
  // ----------------------------------------------------------------
  function renderHeatmap(data) {
    var fromDate    = parseLocalDate(data.from_date);
    var toDate      = parseLocalDate(data.to_date);
    var dailyCounts = data.daily_counts;
    var maxCount    = data.max_count || 0;
    var totalDays   = Math.round((toDate - fromDate) / 86400000) + 1;

    // Compute grid dimensions
    var startDow = mondayIndex(fromDate);
    var numCols  = Math.floor((startDow + totalDays - 1) / 7) + 1;
    var svgWidth  = LEFT_PAD + numCols * STEP;
    var svgHeight = TOP_PAD + 7 * STEP;

    // Clear previous content
    gridContainer.innerHTML = '';

    var svg = document.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('viewBox', '0 0 ' + svgWidth + ' ' + svgHeight);
    svg.setAttribute('width', '100%');
    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label',
      'Scrobble heatmap for ' + data.username + ': ' +
      data.total_scrobbles + ' scrobbles from ' +
      data.from_date + ' to ' + data.to_date);

    // -- Day-of-week labels (Mon, Wed, Fri) --
    DAY_LABELS.forEach(function (dl) {
      var txt = document.createElementNS(SVG_NS, 'text');
      txt.setAttribute('x', LEFT_PAD - 6);
      txt.setAttribute('y', TOP_PAD + dl.row * STEP + CELL_SIZE * 0.75);
      txt.setAttribute('text-anchor', 'end');
      txt.setAttribute('font-size', '9');
      txt.setAttribute('fill', 'currentColor');
      txt.setAttribute('class', 'heatmap-day-label');
      txt.textContent = dl.text;
      svg.appendChild(txt);
    });

    // -- Month labels --
    var monthLabelPlaced = {};
    for (var i = 0; i < totalDays; i++) {
      var d = addDays(fromDate, i);
      if (d.getDate() >= 1 && d.getDate() <= 7) {
        var mKey = d.getFullYear() + '-' + d.getMonth();
        if (!monthLabelPlaced[mKey]) {
          var offset = startDow + i;
          var col = Math.floor(offset / 7);
          var mTxt = document.createElementNS(SVG_NS, 'text');
          mTxt.setAttribute('x', LEFT_PAD + col * STEP);
          mTxt.setAttribute('y', TOP_PAD - 5);
          mTxt.setAttribute('font-size', '9');
          mTxt.setAttribute('fill', 'currentColor');
          mTxt.setAttribute('class', 'heatmap-month-label');
          mTxt.textContent = MONTH_NAMES[d.getMonth()];
          svg.appendChild(mTxt);
          monthLabelPlaced[mKey] = true;
        }
      }
    }

    // -- Grid cells --
    var cellData = [];  // store for tooltip lookups
    for (var i = 0; i < totalDays; i++) {
      var d = addDays(fromDate, i);
      var key = isoDate(d);
      var count = dailyCounts[key] || 0;
      var offset = startDow + i;
      var col = Math.floor(offset / 7);
      var row = offset % 7;

      var x = LEFT_PAD + col * STEP;
      var y = TOP_PAD + row * STEP;

      var rect = document.createElementNS(SVG_NS, 'rect');
      rect.setAttribute('x', x);
      rect.setAttribute('y', y);
      rect.setAttribute('width', CELL_SIZE);
      rect.setAttribute('height', CELL_SIZE);
      rect.setAttribute('rx', CORNER_R);
      rect.setAttribute('ry', CORNER_R);
      rect.setAttribute('class', 'heatmap-cell');

      var fill = count > 0
        ? rocketColor(countToNorm(count, maxCount))
        : zeroFill();
      rect.setAttribute('fill', fill);

      // Store data for tooltip
      rect.setAttribute('data-date', key);
      rect.setAttribute('data-count', count);
      cellData.push({ el: rect, date: d, count: count, x: x, y: y });

      svg.appendChild(rect);
    }

    gridContainer.appendChild(svg);

    // -- Legend gradient --
    legendBar.style.background = legendGradient();

    // -- Result header --
    resultTitle.textContent = data.username + "'s Scrobble Heatmap";
    var fromStr = formatDateLong(fromDate);
    var toStr   = formatDateLong(toDate);
    resultSubtitle.textContent = fromStr + ' -- ' + toStr +
      ' | ' + data.total_scrobbles.toLocaleString() + ' scrobbles';

    // Transition: loading -> result
    hideElement(heatmapLoading);
    fadeIn(heatmapResult);

    // Attach tooltip handlers
    initTooltips(svg, cellData);
  }

  // ----------------------------------------------------------------
  // Tooltips
  // ----------------------------------------------------------------
  function initTooltips(svg, cellData) {
    // Create or reuse tooltip div
    if (!tooltip) {
      tooltip = document.createElement('div');
      tooltip.className = 'heatmap-tooltip';
      document.body.appendChild(tooltip);
    }

    var svgContainer = gridContainer;

    cellData.forEach(function (cd) {
      cd.el.addEventListener('mouseenter', function (e) {
        showTooltip(cd, e);
      });
      cd.el.addEventListener('mouseleave', function () {
        hideTooltip();
      });
      cd.el.addEventListener('touchstart', function (e) {
        e.preventDefault();
        showTooltip(cd, e.touches[0]);
      }, { passive: false });
    });

    document.addEventListener('touchend', hideTooltip);
    document.addEventListener('scroll', hideTooltip, true);
  }

  function showTooltip(cd, event) {
    var dateStr = formatDateLong(cd.date);
    var countStr = cd.count === 0
      ? 'No scrobbles'
      : cd.count + ' scrobble' + (cd.count !== 1 ? 's' : '');
    tooltip.textContent = dateStr + ' -- ' + countStr;
    tooltip.classList.add('visible');

    // Position near the cell
    var rect = cd.el.getBoundingClientRect();
    var ttWidth  = tooltip.offsetWidth;
    var ttHeight = tooltip.offsetHeight;

    var left = rect.left + rect.width / 2 - ttWidth / 2;
    var top  = rect.top - ttHeight - 8;

    // Flip below if too close to top
    if (top < 4) {
      top = rect.bottom + 8;
    }
    // Keep within viewport horizontally
    if (left < 4) left = 4;
    if (left + ttWidth > window.innerWidth - 4) {
      left = window.innerWidth - ttWidth - 4;
    }

    tooltip.style.left = left + window.scrollX + 'px';
    tooltip.style.top  = top + window.scrollY + 'px';
  }

  function hideTooltip() {
    if (tooltip) {
      tooltip.classList.remove('visible');
    }
  }

  // ----------------------------------------------------------------
  // Dark mode observer
  // ----------------------------------------------------------------
  function initDarkModeObserver() {
    // When dark mode toggles, update zero-scrobble cells
    var observer = new MutationObserver(function (mutations) {
      mutations.forEach(function (m) {
        if (m.attributeName === 'class') {
          updateZeroFills();
        }
      });
    });
    observer.observe(document.body, { attributes: true, attributeFilter: ['class'] });
  }

  function updateZeroFills() {
    var fill = zeroFill();
    var cells = document.querySelectorAll('.heatmap-cell');
    cells.forEach(function (cell) {
      if (parseInt(cell.getAttribute('data-count'), 10) === 0) {
        cell.setAttribute('fill', fill);
      }
    });
  }

  // ----------------------------------------------------------------
  // Init on DOMContentLoaded
  // ----------------------------------------------------------------
  document.addEventListener('DOMContentLoaded', function () {
    initPills();
    initUsernameValidation();
    initForm();
    initDarkModeObserver();
  });

})();
