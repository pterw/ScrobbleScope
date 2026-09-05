/**
 * Shared progress and phase display helper for ScrobbleScope.
 * Computes display percentages and labels from backend progress and phase payloads,
 * manages progress bar transform and ARIA attributes, and handles instant resets on phase transitions.
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.ScrobbleProgress = factory();
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  function displayPercent(payload) {
    var phase = payload && payload.phase;
    if (
      phase &&
      Number.isFinite(phase.current) &&
      Number.isFinite(phase.total) &&
      phase.total > 0
    ) {
      return Math.max(0, Math.min(100, (phase.current / phase.total) * 100));
    }
    return Math.max(0, Math.min(100, Number(payload && payload.progress) || 0));
  }

  function label(payload) {
    var phase = payload && payload.phase;
    if (!phase) return (payload && payload.message) || 'Initializing...';
    var prefix = String(phase.label || '').toUpperCase();
    return Number.isFinite(phase.current) &&
      Number.isFinite(phase.total) &&
      phase.total > 0
      ? prefix +
          ' \u00b7 ' +
          String(phase.unit || '').toUpperCase() +
          ' ' +
          phase.current +
          ' / ' +
          phase.total
      : prefix;
  }

  function update(options) {
    if (!options) return { percent: 0, label: 'Initializing...' };
    var track = options.track;
    var bar = options.bar;
    var phaseText = options.phaseText;
    var payload = options.payload || {};
    var previousPhaseKey = options.previousPhaseKey;

    var pct = displayPercent(payload);
    var roundedPct = Math.round(pct);
    var currentLabel = label(payload);

    if (phaseText) {
      phaseText.textContent = currentLabel;
    }

    if (track) {
      track.classList.remove('hidden');
      track.setAttribute('aria-valuenow', String(roundedPct));
      track.setAttribute('aria-valuemin', '0');
      track.setAttribute('aria-valuemax', '100');
      track.setAttribute('aria-valuetext', currentLabel);
    }

    if (bar) {
      bar.setAttribute('aria-valuenow', String(roundedPct));
      bar.setAttribute('aria-valuemin', '0');
      bar.setAttribute('aria-valuemax', '100');
      bar.setAttribute('aria-valuetext', currentLabel);

      var currentPhaseKey =
        (payload && payload.phase && payload.phase.key) || null;
      var phaseChanged =
        previousPhaseKey !== undefined &&
        previousPhaseKey !== null &&
        currentPhaseKey !== previousPhaseKey;

      if (phaseChanged) {
        bar.style.transition = 'none';
        bar.style.transform = 'scaleX(0)';
        if (typeof requestAnimationFrame === 'function') {
          requestAnimationFrame(function () {
            requestAnimationFrame(function () {
              if (bar) {
                bar.style.transition = '';
                bar.style.transform = 'scaleX(' + pct / 100 + ')';
              }
            });
          });
        } else {
          bar.style.transform = 'scaleX(' + pct / 100 + ')';
        }
      } else {
        bar.style.transform = 'scaleX(' + pct / 100 + ')';
      }
    }

    return {
      percent: pct,
      label: currentLabel,
    };
  }

  return {
    displayPercent: displayPercent,
    label: label,
    update: update,
  };
});
