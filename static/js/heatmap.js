// static/js/heatmap.js -- Heatmap pill switching, AJAX submission,
// polling, SVG grid rendering, tooltips, and dark mode support.
// No innerHTML with user data (XSS criterion F-B18-9).
(function () {
  'use strict';

  // ----------------------------------------------------------------
  // Constants
  // ----------------------------------------------------------------
  const POLL_INTERVAL_MS = 1000;

  //: The heatmap window. Named because the daily average divides by it.
  const WINDOW_DAYS = 365;
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
  const CELL_SIZE  = 14;
  const CELL_GAP   = 2;
  const STEP       = CELL_SIZE + CELL_GAP;
  const LEFT_PAD   = 32;  // space for day-of-week labels
  const TOP_PAD    = 20;  // space for month labels
  const CORNER_R   = 2;   // rect corner radius
  const MOBILE_TARGET_CELL_SIZE = 22;
  const MOBILE_MIN_CELL_SIZE = 18;
  const MOBILE_MAX_CELL_SIZE = 28;
  const MOBILE_MIN_COLUMNS = 10;
  const MOBILE_MAX_COLUMNS = 28;
  const MOBILE_GAP = 1;
  // The design mandates one breakpoint. static/css/heatmap.css moved to it in
  // WP-3 and this file did not, so a band of widths got the mobile frame with
  // the desktop grid scaled into it, and crossing the boundary never
  // re-rendered. Named once, because two copies is how they drifted.
  const MOBILE_MAX_WIDTH = 860;

  // Input Mono Narrow, not Input Mono. Full-width Input at 9-11px with this
  // much tracking overflows its row and clips. Named here rather than read
  // from var(--font-mono-narrow), because these land on an SVG presentation
  // attribute, where a custom property does not resolve.
  const LABEL_FONT_STACK =
    '"input-mono-narrow", "input-mono", ui-monospace, monospace';

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

  /**
   * Zero-scrobble cell fill based on dark mode.
   *
   * The two values are --heatmap-empty from the theme. They are repeated as
   * literals because this fill goes on an SVG attribute, where var() does not
   * resolve. static/css/tailwind.src.css stays the definition; change both.
   *
   * The marker read here is body.dark-mode, not the data-theme attribute on
   * html. static/js/theme.js still writes both, and WP-8 owns retiring the
   * older one -- do not switch this ahead of it.
   */
  function zeroFill() {
    return document.body.classList.contains('dark-mode') ? '#262230' : '#e8e2d6';
  }

  /** Build the rocket_r CSS gradient string for the legend bar. */
  function legendGradient() {
    const stops = ROCKET_STOPS.map(function (s) {
      return 'rgb(' + s.r + ',' + s.g + ',' + s.b + ') ' + Math.round(s.pos * 100) + '%';
    });
    return 'linear-gradient(to right, ' + stops.join(', ') + ')';
  }

  function clearChildren(el) {
    while (el.firstChild) {
      el.removeChild(el.firstChild);
    }
  }

  function formatMonthDayUpper(d) {
    return MONTH_NAMES[d.getMonth()].toUpperCase() + ' ' + d.getDate();
  }

  function computeStreak(dailyCounts, toDate) {
    var d = new Date(toDate);
    // If today has no scrobble yet, allow a streak ending yesterday.  Common
    // case: user opens the page in the morning before scrobbling anything.
    // Strict "must include today" semantics killed yesterday-active streaks
    // and was the most-reported confusion in PR #152 review.
    if (!dailyCounts[isoDate(d)]) {
      d.setDate(d.getDate() - 1);
    }
    var streak = 0;
    while (dailyCounts[isoDate(d)]) {
      streak++;
      d.setDate(d.getDate() - 1);
    }
    return streak;
  }

  /**
   * Write the result headline.
   *
   * "A year of <name>", not the old possessive range sentence.
   * The eyebrow above it states the range now, so the headline does not have
   * to, and a short serif line survives a long username without shrinking.
   *
   * The accent is only ever the reader's own data. Never the year: the year
   * is a filter, so a fixed one becomes a lie the moment someone changes it.
   */
  function renderHeadline(username) {
    clearChildren(resultHeadline);
    resultHeadline.style.fontSize = '';
    resultHeadline.style.whiteSpace = '';

    var nameSpan = document.createElement('span');
    nameSpan.className = 'heatmap-headline-username';
    nameSpan.textContent = username || '';

    resultHeadline.appendChild(nameSpan);
    resultHeadline.appendChild(
      document.createTextNode('\u2019s last 365 days of scrobbling')
    );
  }

  function revealHeatmapResult() {
    setHeatmapStageActive(true);
    hideElement(heatmapLoading);
    fadeIn(resultHeadline);
    fadeIn(resultFrame);
    fadeIn(heatmapResult);
  }

  function appendKpi(label, value, subLabel) {
    var item = document.createElement('div');
    item.className = 'heatmap-kpi';

    var labelEl = document.createElement('span');
    labelEl.className = 'heatmap-kpi-label';
    labelEl.textContent = label;

    var valueEl = document.createElement('span');
    valueEl.className = 'heatmap-kpi-value';
    valueEl.textContent = value;

    item.appendChild(labelEl);
    item.appendChild(valueEl);

    if (subLabel) {
      var subEl = document.createElement('span');
      subEl.className = 'heatmap-kpi-sub';
      subEl.textContent = subLabel;
      item.appendChild(subEl);
    }

    kpiRow.appendChild(item);
  }

  function renderKpis(data, dailyCounts, toDate) {
    clearChildren(kpiRow);

    var total = Number(data.total_scrobbles || 0);
    var dayKeys = Object.keys(dailyCounts);
    var bestDate = dayKeys.length > 0
      ? dayKeys.reduce(function (a, b) {
          return dailyCounts[a] >= dailyCounts[b] ? a : b;
        })
      : isoDate(toDate);
    var bestCount = dailyCounts[bestDate] || 0;
    var bestLabel = formatMonthDayUpper(parseLocalDate(bestDate));
    var streak = computeStreak(dailyCounts, toDate);

    // The four the design names. Daily average replaced active days on
    // 2026-08-24; it is scrobbles over the whole 365-day window, not over
    // the days with a scrobble in them, so a quiet month pulls it down.
    // One decimal, always. Math.round showed 0 for anyone under 183
    // scrobbles in the window -- a positive total reported as no listening
    // at all, which is the one number this KPI must never say. It also read
    // 49.9 as 50. A fixed decimal keeps the column aligned.
    var dailyAverage = (total / WINDOW_DAYS).toLocaleString(undefined, {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    });

    appendKpi('SCROBBLES', total.toLocaleString(), '');
    appendKpi('DAILY AVERAGE', dailyAverage, '');
    appendKpi('BEST DAY', String(bestCount), bestLabel);
    appendKpi('CURRENT STREAK', String(streak), 'DAYS');
  }


  // ----------------------------------------------------------------
  // Save image
  // ----------------------------------------------------------------

  //: Drawn at 2x so the grid stays crisp on a high-density screen and when
  //: the file is opened larger than it was on the page.
  const EXPORT_SCALE = 2;
  const EXPORT_PAD = 28;

  //: Export header geometry. Every one of these used to be a literal inside
  //: the drawing code, and the header height was a flat 150 that no longer
  //: matched what was drawn into it: the KPI row ends at 166 and the legend
  //: at 154, so the grid was painted over both. Named here because the canvas
  //: has to be sized before anything is drawn, so the sizing pass and the
  //: drawing pass have to agree on the same numbers.
  const EXPORT_KPI_STEP = 190;      // widest a KPI column ever gets
  const EXPORT_KPI_ROW_H = 62;      // label, value and sub-label together
  const EXPORT_KPI_GUTTER = 14;     // smallest gap between two columns
  const EXPORT_LEGEND_W = 90;
  const EXPORT_LEGEND_H = 8;
  const EXPORT_HEAD_GAP = 16;       // air between the header and the grid

  /**
   * Read a CSS custom property as a resolved colour.
   *
   * getPropertyValue can hand back the unresolved var(--other) text, so the
   * value is painted onto a probe and read back from the cascade instead.
   */
  function resolvedColour(token) {
    var probe = document.createElement('div');
    probe.style.color = 'var(' + token + ')';
    document.body.appendChild(probe);
    var value = getComputedStyle(probe).color;
    probe.remove();
    return value;
  }

  /**
   * Turn the on-screen grid into an image the canvas can draw.
   *
   * The SVG is cloned, given explicit pixel dimensions -- it renders at
   * width="100%" on the page, which means nothing outside a layout -- and
   * its label font is pinned to a plain monospace stack. The Adobe kit does
   * not load inside a serialized SVG, so leaving the kit families there
   * would let the renderer pick any fallback it liked. Pinning it makes the
   * saved file the same everywhere.
   */
  function gridAsImage(svg, width, height) {
    var clone = svg.cloneNode(true);
    clone.setAttribute('width', String(width));
    clone.setAttribute('height', String(height));
    clone.setAttribute('xmlns', SVG_NS);
    Array.prototype.forEach.call(
      clone.querySelectorAll('.heatmap-month-label, .heatmap-day-label'),
      function (node) {
        node.setAttribute('font-family', 'monospace');
        node.setAttribute('fill', resolvedColour('--ss-text-muted'));
      }
    );
    var markup = new XMLSerializer().serializeToString(clone);
    var image = new Image();
    image.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(markup);
    return image;
  }

  const KPI_LABEL_FONT = '10px "input-mono-narrow", "input-mono", monospace';
  const KPI_VALUE_FONT = '24px "gotham", sans-serif';

  /** The KPI blocks on the page, as plain text. */
  function kpiTexts() {
    return Array.prototype.map.call(
      document.querySelectorAll('.heatmap-kpi'),
      function (item) {
        var pick = function (sel) {
          var node = item.querySelector(sel);
          return node ? node.textContent : '';
        };
        return {
          label: pick('.heatmap-kpi-label'),
          value: pick('.heatmap-kpi-value'),
          sub: pick('.heatmap-kpi-sub'),
        };
      }
    );
  }

  /**
   * Decide how the export header lays out at this width.
   *
   * Measured, not assumed. A single row of four columns needs about 90px
   * each for the labels alone, and the mobile grid is only ~340px wide, so
   * four columns ran "DAILY AVERAGE" straight into "BEST DAY". The columns
   * wrap instead, and the header grows to whatever it actually needs -- the
   * old flat 150 was shorter than the content, which is why the grid painted
   * over the legend and the streak's DAYS label.
   */
  function exportHeaderLayout(ctx, gridWidth, items) {
    var widest = 0;
    items.forEach(function (item) {
      ctx.font = KPI_LABEL_FONT;
      widest = Math.max(widest, ctx.measureText(item.label).width);
      widest = Math.max(widest, ctx.measureText(item.sub).width);
      ctx.font = KPI_VALUE_FONT;
      widest = Math.max(widest, ctx.measureText(item.value).width);
    });
    var needed = widest + EXPORT_KPI_GUTTER;

    // Four across, else two, else stacked. Two keeps a four-item row square
    // rather than leaving one orphan on a second line.
    var columns = Math.max(items.length, 1);
    while (columns > 1 && gridWidth / columns < needed) {
      columns = columns > 2 ? 2 : 1;
    }

    var top = EXPORT_PAD + 76;
    var step = Math.min(EXPORT_KPI_STEP, gridWidth / columns);
    var rows = Math.ceil(Math.max(items.length, 1) / columns);
    var kpiBottom = top + rows * EXPORT_KPI_ROW_H;

    // The legend keeps its place beside the KPIs when there is honestly room
    // for it, and takes a row of its own when there is not.
    var width = gridWidth + EXPORT_PAD * 2;
    var besideX = width - EXPORT_PAD - EXPORT_LEGEND_W;
    var kpiRight = EXPORT_PAD + columns * step;
    var beside = besideX >= kpiRight + EXPORT_KPI_GUTTER;
    var legendY = beside ? top + 42 : kpiBottom + 4;

    return {
      columns: columns,
      step: step,
      kpiTop: top,
      kpiBottom: kpiBottom,
      legendX: beside ? besideX : EXPORT_PAD,
      legendY: legendY,
      headHeight:
        Math.max(kpiBottom, legendY + EXPORT_LEGEND_H) + EXPORT_HEAD_GAP,
    };
  }

  /** Draw the KPI blocks into the space exportHeaderLayout set aside. */
  function drawKpis(ctx, items, layout) {
    var muted = resolvedColour('--ss-text-muted');
    var ink = resolvedColour('--color-base-content');

    items.forEach(function (item, index) {
      var left = EXPORT_PAD + (index % layout.columns) * layout.step;
      var top =
        layout.kpiTop + Math.floor(index / layout.columns) * EXPORT_KPI_ROW_H;

      ctx.fillStyle = muted;
      ctx.font = KPI_LABEL_FONT;
      ctx.fillText(item.label, left, top);

      ctx.fillStyle = ink;
      ctx.font = KPI_VALUE_FONT;
      ctx.fillText(item.value, left, top + 28);

      if (item.sub) {
        ctx.fillStyle = muted;
        ctx.font = KPI_LABEL_FONT;
        ctx.fillText(item.sub, left, top + 46);
      }
    });
  }

  /** Draw the rocket ramp, so the file carries its own legend. */
  function drawLegend(ctx, x, y, width) {
    var gradient = ctx.createLinearGradient(x, 0, x + width, 0);
    ROCKET_STOPS.forEach(function (stop) {
      gradient.addColorStop(
        stop.pos, 'rgb(' + stop.r + ',' + stop.g + ',' + stop.b + ')');
    });
    ctx.fillStyle = gradient;
    ctx.fillRect(x, y, width, EXPORT_LEGEND_H);
  }

  /**
   * Save the heatmap as a JPEG.
   *
   * The canvas is drawn by hand rather than captured from the page. The
   * results page uses html2canvas for the same job and carries about ninety
   * lines of workarounds for colours it renders wrongly; the heatmap is an
   * SVG on a flat background, so none of that is needed and no library is
   * loaded onto a migrated page.
   *
   * Canvas text uses the kit faces, because it draws in this document where
   * they are already loaded. Only the labels inside the serialized SVG fall
   * back -- see gridAsImage.
   *
   * Known deviation: the design asks for the desktop 53x7 grid even when the
   * reader is on a phone. This saves whatever layout is on screen.
   */
  function saveHeatmapImage() {
    var svg = gridContainer ? gridContainer.querySelector('svg') : null;
    if (!svg) return;

    var svgBox = svg.getBoundingClientRect();
    var gridWidth = Math.round(svgBox.width);
    var gridHeight = Math.round(svgBox.height);
    if (!gridWidth || !gridHeight) return;

    var width = gridWidth + EXPORT_PAD * 2;

    var canvas = document.createElement('canvas');
    var ctx = canvas.getContext('2d');

    // Measure first, then size the canvas. Setting width or height clears the
    // canvas and resets the context, so the scale is applied afterwards.
    var items = kpiTexts();
    var layout = exportHeaderLayout(ctx, gridWidth, items);
    var headHeight = layout.headHeight;
    var height = headHeight + gridHeight + EXPORT_PAD;

    canvas.width = width * EXPORT_SCALE;
    canvas.height = height * EXPORT_SCALE;
    ctx.scale(EXPORT_SCALE, EXPORT_SCALE);
    ctx.textBaseline = 'alphabetic';

    ctx.fillStyle = resolvedColour('--heatmap-surface');
    ctx.fillRect(0, 0, width, height);

    ctx.fillStyle = resolvedColour('--ss-text-muted');
    ctx.font = '10px "input-mono-narrow", "input-mono", monospace';
    ctx.fillText(
      'LISTENING HEATMAP \u00b7 LAST 365 DAYS', EXPORT_PAD, EXPORT_PAD + 10);

    var lead = 'A year of ';
    ctx.fillStyle = resolvedColour('--color-base-content');
    ctx.font = '26px "instrument-serif", Georgia, serif';
    ctx.fillText(lead, EXPORT_PAD, EXPORT_PAD + 42);
    var leadWidth = ctx.measureText(lead).width;
    ctx.fillStyle = resolvedColour('--color-primary');
    ctx.font = 'italic 26px "instrument-serif", Georgia, serif';
    ctx.fillText(lastUsername, EXPORT_PAD + leadWidth, EXPORT_PAD + 42);

    drawKpis(ctx, items, layout);
    drawLegend(ctx, layout.legendX, layout.legendY, EXPORT_LEGEND_W);

    var image = gridAsImage(svg, gridWidth, gridHeight);
    image.onload = function () {
      ctx.drawImage(image, EXPORT_PAD, headHeight, gridWidth, gridHeight);
      var link = document.createElement('a');
      link.href = canvas.toDataURL('image/jpeg', 0.95);
      link.download =
        'scrobblescope_' + (lastUsername || 'heatmap') + '_heatmap.jpg';
      document.body.appendChild(link);
      link.click();
      link.remove();
    };
  }

  // ----------------------------------------------------------------
  // DOM references (set on DOMContentLoaded)
  // ----------------------------------------------------------------
  var pills, albumSection, heatmapSection, heatmapLoading, indexGrid,
      heroBlocks,
      heatmapResult, heatmapForm, heatmapUsernameInput,
      progressText, progressBar, progressTrack, errorContainer, errorMessage,
      loadingDetail, loadingStats, loadingUsername,
      loadingStatPages, loadingStatScrobbles, loadingStatDays,
      retryBtn, searchAgainBtn, saveImageBtn, resultHeadline, resultFrame,
      kpiRow, gridContainer, legendBar, tooltip;

  // ----------------------------------------------------------------
  // State
  // ----------------------------------------------------------------
  var pollTimer = null;
  var currentJobId = null;
  var lastUsername = '';
  var savedHeatmapJobId = null;
  var savedHeatmapUsername = '';
  var lastHeatmapData = null;
  var lastRenderMobile = null;
  var resizeTimer = null;
  var heroTransitionToken = 0;
  var heroAnimations = [];

  // ----------------------------------------------------------------
  // Pill switching
  // ----------------------------------------------------------------
  function replaceCanonicalPath(path, activeHref) {
    if (window.location.pathname + window.location.search !== path) {
      window.history.replaceState({}, '', path);
    }
    document.querySelectorAll('.site-header__nav-link').forEach(function (link) {
      var isCurrent = link.getAttribute('href') === activeHref;
      link.classList.toggle('active', isCurrent);
      if (isCurrent) {
        link.setAttribute('aria-current', 'page');
      } else {
        link.removeAttribute('aria-current');
      }
    });
  }

  function initPills() {
    pills = document.querySelectorAll('.mode-pill');
    albumSection   = document.getElementById('album-form-section');
    heatmapSection = document.getElementById('heatmap-form-section');
    indexGrid      = document.getElementById('index-grid');
    heroBlocks     = document.querySelectorAll('[data-mode-hero]');

    pills.forEach(function (pill) {
      pill.addEventListener('click', function () {
        var mode = this.getAttribute('data-mode');
        var canonicalPath = mode === 'heatmap' ? '/?mode=heatmap' : '/';
        replaceCanonicalPath(canonicalPath, '/');
        var self = this;
        pills.forEach(function (p) {
          p.classList.toggle('active', p === self);
          p.setAttribute('aria-selected', p === self ? 'true' : 'false');
        });

        // The hero names the mode in its eyebrow and its headline, so it
        // switches with the form. Both blocks are in the page; one is hidden.
        switchModeHero(mode);

        setHeatmapStageActive(false);
        hideElement(mode === 'heatmap' ? albumSection : heatmapSection);
        showElement(mode === 'heatmap' ? heatmapSection : albumSection);
        hideElement(heatmapLoading);
        hideElement(heatmapResult);
        showElement(indexGrid);
      });
    });
  }

  // The pills are real <button> elements now, so Enter and Space already
  // activate them. The keydown handler that stood in for that on
  // span[role="button"] is gone with the spans -- F-B18-12 and one of the
  // three items in F-B21-5.

  // ----------------------------------------------------------------
  // Show/hide helpers with optional fade
  // ----------------------------------------------------------------
  function showElement(el) {
    el.classList.remove('hidden');
  }

  function hideElement(el) {
    el.classList.add('hidden');
  }

  function setHeatmapStageActive(isActive) {
    document.body.classList.toggle('heatmap-stage-active', isActive);
  }

  function switchModeHero(mode) {
    var nextHero = null;
    var currentHero = null;
    heroTransitionToken += 1;
    var transitionToken = heroTransitionToken;

    heroAnimations.forEach(function (animation) {
      animation.cancel();
    });
    heroAnimations = [];

    heroBlocks.forEach(function (hero) {
      hero.style.opacity = '';
      if (hero.getAttribute('data-mode-hero') === mode) nextHero = hero;
      if (!hero.classList.contains('hidden')) currentHero = hero;
    });
    if (!nextHero) return;

    if (nextHero === currentHero) {
      heroBlocks.forEach(function (hero) {
        if (hero !== nextHero) hideElement(hero);
      });
      return;
    }

    var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (
      reducedMotion ||
      !currentHero ||
      typeof currentHero.animate !== 'function'
    ) {
      if (currentHero) hideElement(currentHero);
      showElement(nextHero);
      return;
    }

    var exitAnimation = currentHero.animate(
      [{ opacity: 1 }, { opacity: 0 }],
      {
        duration: 110,
        easing: 'cubic-bezier(0.4, 0, 1, 1)',
        fill: 'forwards'
      }
    );
    heroAnimations = [exitAnimation];

    exitAnimation.onfinish = function () {
      if (transitionToken !== heroTransitionToken) return;
      hideElement(currentHero);
      exitAnimation.cancel();
      showElement(nextHero);

      var enterAnimation = nextHero.animate(
        [{ opacity: 0 }, { opacity: 1 }],
        {
          duration: 180,
          easing: 'cubic-bezier(0.16, 1, 0.3, 1)',
          fill: 'forwards'
        }
      );
      heroAnimations = [enterAnimation];
      enterAnimation.onfinish = function () {
        if (transitionToken !== heroTransitionToken) return;
        enterAnimation.cancel();
        heroAnimations = [];
      };
    };
  }

  function readSavedHeatmap() {
    var config = document.getElementById('heatmap-session-config');
    if (!config) return;
    try {
      var saved = JSON.parse(config.textContent || 'null');
      if (saved && saved.job_id) {
        savedHeatmapJobId = saved.job_id;
        savedHeatmapUsername = saved.username || '';
      }
    } catch (error) {
      savedHeatmapJobId = null;
      savedHeatmapUsername = '';
    }
  }

  function resumeSavedHeatmap() {
    if (!savedHeatmapJobId || !heatmapLoading) return false;

    stopPolling();
    currentJobId = savedHeatmapJobId;
    lastUsername = savedHeatmapUsername;
    setHeatmapStageActive(true);
    if (heatmapUsernameInput) heatmapUsernameInput.value = lastUsername;
    hideElement(indexGrid);
    hideElement(heatmapSection);
    hideElement(heatmapResult);
    hideElement(errorContainer);
    if (progressBar) progressBar.style.width = '0%';
    if (progressTrack) hideElement(progressTrack);
    progressText.textContent = 'Restoring your latest heatmap...';
    resetLoadingDetails(lastUsername);
    fadeIn(heatmapLoading);
    pollProgress();
    startPolling();
    return true;
  }

  function fadeIn(el) {
    el.classList.add('heatmap-fade', 'fading-out');
    el.classList.remove('hidden');
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
    feedback.className = 'field__error';
    heatmapUsernameInput.parentNode.appendChild(feedback);
    var validationGeneration = 0;

    heatmapUsernameInput.addEventListener('input', function () {
      validationGeneration += 1;
      this.classList.remove('is-valid', 'is-invalid');
      this.setCustomValidity('');
      // .field__error hides only while it is empty. Bootstrap's
      // .invalid-feedback keyed off a sibling class and hid stale text for
      // free; this replacement has to be emptied by hand.
      feedback.textContent = '';
    });

    heatmapUsernameInput.addEventListener('blur', function () {
      var username = heatmapUsernameInput.value.trim();
      var generation = ++validationGeneration;
      if (!username) {
        heatmapUsernameInput.classList.remove('is-valid', 'is-invalid');
        return;
      }

      // The answer belongs to the username that was asked about. Edit the
      // field while the request is in flight and the reply lands on whatever
      // is in the box by then, so a rejected name could mark a good one
      // invalid -- and since the submit guard reads checkValidity, that
      // rejection would hold until the next blur, which pressing Enter never
      // fires. Discard a reply the field has moved on from.
      fetch('/validate_user?username=' + encodeURIComponent(username))
        .then(function (res) {
          return res.json().then(function (data) {
            return { data: data, transient: res.status >= 500 };
          });
        })
        .then(function (answer) {
          var data = answer.data;
          if (
            generation !== validationGeneration ||
            heatmapUsernameInput.value.trim() !== username
          ) return;
          // A 5xx is the service failing, not a verdict about the username.
          // The route returns one as {valid: false, "Validation service
          // unavailable. Try again."}, which read here as "no such account"
          // and set a validity error -- so the submit guard below refused
          // every attempt, and trying again was the one thing the message
          // told the reader to do that could not work. The network-error
          // path already clears validity for exactly this reason.
          if (answer.transient) {
            heatmapUsernameInput.classList.remove('is-valid', 'is-invalid');
            heatmapUsernameInput.setCustomValidity('');
            feedback.textContent =
              data.message || 'Validation service unavailable. Try again.';
            return;
          }
          if (data.valid) {
            heatmapUsernameInput.classList.remove('is-invalid');
            heatmapUsernameInput.classList.add('is-valid');
            heatmapUsernameInput.setCustomValidity('');
            feedback.textContent = '';
          } else {
            heatmapUsernameInput.classList.remove('is-valid');
            heatmapUsernameInput.classList.add('is-invalid');
            feedback.textContent = data.message || 'Username not found on Last.fm';
            heatmapUsernameInput.setCustomValidity(data.message || 'Username not found on Last.fm');
          }
        })
        .catch(function () {
          if (
            generation !== validationGeneration ||
            heatmapUsernameInput.value.trim() !== username
          ) return;
          heatmapUsernameInput.classList.remove('is-valid', 'is-invalid');
          heatmapUsernameInput.setCustomValidity('');
          feedback.textContent = 'Validation service unavailable. Try again.';
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
    progressBar    = document.getElementById('heatmap-progress-bar');
    progressTrack  = document.getElementById('heatmap-progress-track');
    errorContainer = document.getElementById('heatmap-error');
    errorMessage   = document.getElementById('heatmap-error-message');
    loadingDetail  = document.getElementById('heatmap-loading-detail');
    loadingStats   = document.getElementById('heatmap-loading-stats');
    loadingUsername = document.getElementById('heatmap-loading-username');
    loadingStatPages = document.getElementById('heatmap-stat-pages');
    loadingStatScrobbles = document.getElementById('heatmap-stat-scrobbles');
    loadingStatDays = document.getElementById('heatmap-stat-days');
    retryBtn       = document.getElementById('heatmap-retry-btn');
    searchAgainBtn = document.getElementById('heatmap-search-again');
    saveImageBtn   = document.getElementById('heatmap-save-image');
    resultHeadline = document.getElementById('heatmap-result-headline');
    resultFrame    = document.getElementById('heatmap-result-frame');
    kpiRow         = document.getElementById('heatmap-kpi-row');
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
      // The blur validator calls setCustomValidity, but the form carries
      // novalidate, so the browser never consults it. Without this the page
      // ran a second Last.fm lookup and showed the loading screen for a
      // username it had already been told does not exist.
      if (!heatmapUsernameInput.checkValidity()) {
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

    if (saveImageBtn) {
      saveImageBtn.addEventListener('click', saveHeatmapImage);
    }

    searchAgainBtn.addEventListener('click', function () {
      window.location.assign('/?mode=heatmap');
    });
  }

  function submitHeatmap(username) {
    // Reset UI: show loading, hide form + result + error
    stopPolling();
    setHeatmapStageActive(true);
    // The grid is 53 weeks wide and cannot fit the form column, so the whole
    // two-column hero steps aside while the heatmap is on screen.
    hideElement(indexGrid);
    hideElement(heatmapSection);
    hideElement(heatmapResult);
    hideElement(errorContainer);
    progressText.textContent = 'Initializing...';
    resetLoadingDetails(username);
    if (progressBar) progressBar.style.width = '0%';
    if (progressTrack) {
      progressTrack.setAttribute('aria-valuenow', '0');
      hideElement(progressTrack);
    }
    // Show spinner wrapper if hidden
    var spinnerWrapper = heatmapLoading.querySelector('.wait-panel__mark');
    if (spinnerWrapper) spinnerWrapper.style.display = '';
    fadeIn(heatmapLoading);

    startHeatmapRequest(username, true);
  }

  function parseJsonResponse(res) {
    return res.text().then(function (body) {
      var data;
      try {
        data = JSON.parse(body);
      } catch (error) {
        data = { error: true, message: 'The server returned an unreadable response.' };
      }
      return { status: res.status, data: data };
    });
  }

  function refreshCsrfToken() {
    return fetch('/csrf-token')
      .then(parseJsonResponse)
      .then(function (result) {
        if (result.status !== 200 || !result.data.csrf_token) {
          throw new Error('Could not refresh the request token.');
        }
        var meta = document.querySelector('meta[name="csrf-token"]');
        if (meta) meta.setAttribute('content', result.data.csrf_token);
        document.querySelectorAll('input[name="csrf_token"]').forEach(function (input) {
          input.value = result.data.csrf_token;
        });
      });
  }

  function startHeatmapRequest(username, mayRefreshToken) {
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
    .then(parseJsonResponse)
    .then(function (result) {
      if (
        mayRefreshToken &&
        result.status === 400 &&
        result.data.error_code === 'csrf_invalid'
      ) {
        progressText.textContent = 'Refreshing your session...';
        return refreshCsrfToken().then(function () {
          return startHeatmapRequest(username, false);
        });
      }
      if (result.status === 202 && result.data.job_id) {
        currentJobId = result.data.job_id;
        savedHeatmapJobId = currentJobId;
        savedHeatmapUsername = username;
        replaceCanonicalPath('/heatmap', '/heatmap');
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
        updateLoadingDetails(data.stats || {});
        if (typeof data.progress === 'number' && progressBar && progressTrack) {
          var progress = Math.max(0, Math.min(100, data.progress));
          progressBar.style.width = progress + '%';
          progressTrack.setAttribute('aria-valuenow', String(progress));
          showElement(progressTrack);
        }

        if (data.error) {
          stopPolling();
          showError(data.message || 'An error occurred.', data.retryable);
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

  function resetLoadingDetails(username) {
    if (loadingDetail) {
      loadingDetail.textContent = 'Preparing the last 365 days of listening.';
    }
    if (loadingUsername) loadingUsername.textContent = username || 'Last.fm profile';
    if (loadingStats) loadingStats.classList.add('hidden');
    [loadingStatPages, loadingStatScrobbles, loadingStatDays].forEach(function (node) {
      if (node && node.closest('.heatmap-loading__stat')) {
        node.closest('.heatmap-loading__stat').classList.add('hidden');
      }
    });
  }

  function revealLoadingStat(node, text) {
    if (!node || text === null || text === undefined) return false;
    node.textContent = text;
    var item = node.closest('.heatmap-loading__stat');
    if (item) item.classList.remove('hidden');
    return true;
  }

  function updateLoadingDetails(stats) {
    if (!stats) return;
    var shown = false;
    var received = stats.pages_received;
    var expected = stats.pages_expected;
    if (received !== undefined && expected !== undefined) {
      shown = revealLoadingStat(
        loadingStatPages,
        Number(received).toLocaleString() + ' / ' + Number(expected).toLocaleString()
      ) || shown;
      if (loadingDetail) loadingDetail.textContent = 'Reading your Last.fm history.';
    }
    if (stats.total_scrobbles !== undefined) {
      shown = revealLoadingStat(
        loadingStatScrobbles,
        Number(stats.total_scrobbles).toLocaleString()
      ) || shown;
      if (loadingDetail) loadingDetail.textContent = 'Building one day at a time.';
    }
    if (stats.active_days !== undefined) {
      shown = revealLoadingStat(
        loadingStatDays,
        Number(stats.active_days).toLocaleString()
      ) || shown;
    }
    if (shown && loadingStats) loadingStats.classList.remove('hidden');
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
    var spinnerWrapper = heatmapLoading.querySelector('.wait-panel__mark');
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
    lastHeatmapData = data;
    lastRenderMobile = window.innerWidth < MOBILE_MAX_WIDTH;
    if (lastRenderMobile) {
      renderHeatmapMobile(data);
    } else {
      renderHeatmapDesktop(data);
    }
  }

  function renderHeatmapDesktop(data) {
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
    clearChildren(gridContainer);
    renderHeadline(data.username);
    renderKpis(data, dailyCounts, toDate);

    var svg = document.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('viewBox', '0 0 ' + svgWidth + ' ' + svgHeight);
    svg.setAttribute('width', '100%');
    svg.setAttribute('data-layout', 'desktop');
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
      txt.setAttribute('font-size', '9.5');
      txt.setAttribute('font-family', LABEL_FONT_STACK);
      txt.setAttribute('font-variant', 'small-caps');
      txt.setAttribute('letter-spacing', '0.12em');
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
          mTxt.setAttribute('font-size', '9.5');
          mTxt.setAttribute('font-family', LABEL_FONT_STACK);
          mTxt.setAttribute('font-variant', 'small-caps');
          mTxt.setAttribute('letter-spacing', '0.12em');
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

    // Transition: loading -> result
    revealHeatmapResult();

    // Attach tooltip handlers
    initTooltips(svg, cellData);
  }

  function renderHeatmapMobile(data) {
    var fromDate    = parseLocalDate(data.from_date);
    var toDate      = parseLocalDate(data.to_date);
    var dailyCounts = data.daily_counts;
    var maxCount    = data.max_count || 0;
    var totalDays   = Math.round((toDate - fromDate) / 86400000) + 1;

    var viewportWidth = window.innerWidth || document.documentElement.clientWidth || 320;
    var containerWidth = gridContainer.clientWidth || Math.max(220, viewportWidth - 48);
    var columns = Math.floor(
      (containerWidth + MOBILE_GAP) / (MOBILE_TARGET_CELL_SIZE + MOBILE_GAP)
    );
    columns = Math.max(MOBILE_MIN_COLUMNS, Math.min(MOBILE_MAX_COLUMNS, columns));

    var mCellSize = Math.floor((containerWidth - (columns - 1) * MOBILE_GAP) / columns);
    mCellSize = Math.max(MOBILE_MIN_CELL_SIZE, Math.min(MOBILE_MAX_CELL_SIZE, mCellSize));

    var mStep = mCellSize + MOBILE_GAP;
    var rows = Math.ceil(totalDays / columns);
    var svgWidth = columns * mCellSize + (columns - 1) * MOBILE_GAP;
    var svgHeight = rows * mCellSize + (rows - 1) * MOBILE_GAP;

    clearChildren(gridContainer);
    renderHeadline(data.username);
    renderKpis(data, dailyCounts, toDate);

    var svg = document.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('viewBox', '0 0 ' + svgWidth + ' ' + svgHeight);
    svg.setAttribute('width', '100%');
    svg.setAttribute('data-layout', 'mobile');
    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label',
      'Scrobble activity strip for ' + data.username + ': ' +
      data.total_scrobbles + ' scrobbles from ' +
      data.from_date + ' to ' + data.to_date);

    var cellData = [];
    for (var i = 0; i < totalDays; i++) {
      var d = addDays(fromDate, i);
      var key = isoDate(d);
      var count = dailyCounts[key] || 0;
      var col = i % columns;
      var row = Math.floor(i / columns);

      var x = col * mStep;
      var y = row * mStep;

      var rect = document.createElementNS(SVG_NS, 'rect');
      rect.setAttribute('x', x);
      rect.setAttribute('y', y);
      rect.setAttribute('width', mCellSize);
      rect.setAttribute('height', mCellSize);
      rect.setAttribute('rx', CORNER_R);
      rect.setAttribute('ry', CORNER_R);
      rect.setAttribute('class', 'heatmap-cell');

      var fill = count > 0
        ? rocketColor(countToNorm(count, maxCount))
        : zeroFill();
      rect.setAttribute('fill', fill);

      rect.setAttribute('data-date', key);
      rect.setAttribute('data-count', count);
      cellData.push({ el: rect, date: d, count: count, x: x, y: y });

      svg.appendChild(rect);
    }

    gridContainer.appendChild(svg);
    legendBar.style.background = legendGradient();

    revealHeatmapResult();

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
    var placeholders = document.querySelectorAll('.heatmap-cell-placeholder');
    placeholders.forEach(function (cell) {
      cell.setAttribute('fill', fill);
    });
  }

  function handleResize() {
    if (resizeTimer) {
      window.clearTimeout(resizeTimer);
    }

    resizeTimer = window.setTimeout(function () {

      if (!lastHeatmapData || !heatmapResult || heatmapResult.classList.contains('hidden')) {
        return;
      }

      var shouldRenderMobile = window.innerWidth < MOBILE_MAX_WIDTH;
      if (shouldRenderMobile !== lastRenderMobile) {
        renderHeatmap(lastHeatmapData);
      }
    }, 100);
  }

  // ----------------------------------------------------------------
  // Init on DOMContentLoaded
  // ----------------------------------------------------------------
  /**
   * Paint the heatmap-mode preview ramp.
   *
   * The ramp shows the reader the colour scale before there is any data. It
   * reads ROCKET_STOPS through the same helper the legend uses, so the two
   * cannot drift. The CSS deliberately does not carry the seven stops: one
   * copy of the ramp, and this file owns it.
   */
  function initPreviewRamp() {
    var ramp = document.querySelector('.hm-preview__ramp');
    if (ramp) ramp.style.backgroundImage = legendGradient();
  }

  document.addEventListener('DOMContentLoaded', function () {
    initPreviewRamp();
    readSavedHeatmap();
    initUsernameValidation();
    initForm();
    initPills();
    initDarkModeObserver();
    window.addEventListener('resize', handleResize);
    if (window.location.pathname === '/heatmap') resumeSavedHeatmap();
  });

})();
