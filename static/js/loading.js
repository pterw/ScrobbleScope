// Album loading state. The backend owns progress copy and percentages; this
// file renders them and moves a completed browser session to /results.
const {
  job_id,
  username,
  year,
  sort_by,
  include_unmatched,
  release_scope,
  decade,
  release_year,
  min_plays,
  min_tracks,
  limit_results
} = window.SCROBBLE || {};

const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
const progressBar = document.getElementById('progress-bar');
const progressTrack = document.getElementById('progress-track');
const stepText = document.getElementById('step-text');
const stepDetails = document.getElementById('step-details');
const errorContainer = document.getElementById('error-container');
const errorText = document.getElementById('error-text');
const errorSource = document.getElementById('error-source');
const retryButton = document.getElementById('retry-button');
const liveStatsContainer = document.getElementById('live-stats');
const statScrobbles = document.getElementById('stat-scrobbles');
const statPages = document.getElementById('stat-pages');
const statCacheHits = document.getElementById('stat-cache-hits');
const statToSearch = document.getElementById('stat-to-search');

let errorDetected = false;
let latestAppliedPollSeq = 0;
let pollSeq = 0;
let pollInFlight = false;
let previousPhaseKey = null;

function createHiddenInput(name, value) {
  const input = document.createElement('input');
  input.type = 'hidden';
  input.name = name;
  input.value = value;
  return input;
}

function revealStat(element, value) {
  if (!element || value === undefined || value === null) return false;
  element.textContent = Number(value).toLocaleString();
  element.closest('.loading-stat')?.classList.remove('hidden');
  return true;
}

function updateLiveStats(stats) {
  if (!stats || !liveStatsContainer) return;

  const hasAny = [
    revealStat(statScrobbles, stats.total_scrobbles),
    revealStat(statPages, stats.pages_fetched),
    // Cache hits and albums to search split the albums that passed the
    // thresholds, so no two figures in the row repeat each other.
    revealStat(statCacheHits, stats.cache_hits),
    revealStat(statToSearch, stats.albums_to_search)
  ].some(Boolean);

  if (hasAny) liveStatsContainer.classList.remove('hidden');

  const partialWarning = document.getElementById('partial-warning');
  const partialWarningText = document.getElementById('partial-warning-text');
  if (stats.partial_data_warning && partialWarning && partialWarningText) {
    partialWarningText.textContent = stats.partial_data_warning;
    partialWarning.classList.remove('hidden');
  }
}

function updateProgress(progressData) {
  if (window.ScrobbleProgress) {
    window.ScrobbleProgress.update({
      track: progressTrack,
      bar: progressBar,
      phaseText: stepText,
      payload: progressData,
      previousPhaseKey: previousPhaseKey,
    });
    previousPhaseKey =
      (progressData && progressData.phase && progressData.phase.key) || null;
  } else {
    const value = Number(progressData && progressData.progress);
    if (typeof value !== 'number' || !progressBar || !progressTrack) return;
    const progress = Math.max(0, Math.min(100, value));
    progressBar.style.transform = `scaleX(${progress / 100})`;
    progressTrack.setAttribute('aria-valuenow', String(progress));
    progressTrack.classList.remove('hidden');
    if (stepText && progressData.message) stepText.textContent = progressData.message;
  }
}

/**
 * Upstream names a failure may cite; any other source shows no source line.
 * A Map, not an object literal, so an inherited key such as 'constructor'
 * finds nothing instead of a prototype member.
 */
const ERROR_SOURCE_LABELS = new Map([['lastfm', 'Last.fm'], ['spotify', 'Spotify']]);

/** Render a job failure and name its upstream source when there is one. */
function showFailure(message, source) {
  errorDetected = true;
  progressBar?.classList.add('is-error');
  errorContainer?.classList.remove('hidden');
  if (errorText) errorText.textContent = message;
  // The alert below announces the failure; leaving it in the polite phase line
  // too would read it out twice.
  if (stepText) stepText.textContent = '';

  if (errorSource) {
    // A fault that is ours ('internal') is not blamed on an upstream.
    const label = ERROR_SOURCE_LABELS.get(source);
    errorSource.textContent = label ? `Source: ${label}` : '';
    errorSource.classList.toggle('hidden', !label);
  }
}

/**
 * Keep the three-second reading delay, then open the results page. A message,
 * when given, says why the page is moving on.
 */
function scheduleResultsRedirect(message) {
  if (message && stepDetails) stepDetails.textContent = message;
  setTimeout(redirectToResults, 3000);
}

/** Render a job failure and choose retry or redirect; report whether handled. */
function handleProgressError(progressData) {
  if (!progressData.error) return false;

  showFailure(
    progressData.message || 'The search could not be completed.',
    progressData.error_source
  );

  if (progressData.retryable && retryButton) {
    retryButton.classList.remove('hidden');
    retryButton.onclick = function () {
      retryButton.disabled = true;
      retryButton.textContent = 'Retrying\u2026';
      retryCurrentSearch();
    };
    if (stepDetails) stepDetails.textContent = 'Retry the search or return home.';
    return true;
  }

  scheduleResultsRedirect('Opening the results page\u2026');
  return true;
}

/** Continue only while the job is incomplete and no failure has stopped it. */
function shouldPollAgain(progress) {
  return progress < 100 && !errorDetected;
}

async function fetchProgress() {
  if (pollInFlight || errorDetected) return;

  const currentSeq = ++pollSeq;
  pollInFlight = true;

  try {
    const response = await fetch(`/progress?job_id=${encodeURIComponent(job_id)}`);
    const progressData = await response.json();
    pollInFlight = false;

    if (currentSeq < latestAppliedPollSeq || errorDetected) return;
    latestAppliedPollSeq = currentSeq;

    updateProgress(progressData);
    updateLiveStats(progressData.stats || {});

    if (handleProgressError(progressData)) return;

    const progress = Number(progressData.progress);
    if (shouldPollAgain(progress)) {
      setTimeout(fetchProgress, 1000);
      return;
    }

    // The phase line already says the run is done; a second line saying the
    // results are opening only repeated it (owner, 2026-10-22).
    if (!errorDetected) scheduleResultsRedirect();
  } catch (error) {
    pollInFlight = false;
    console.error('Error fetching progress:', error);
    showFailure('The progress service could not be reached.');
    if (stepText) stepText.textContent = 'Progress connection interrupted';
    if (stepDetails) stepDetails.textContent = 'Try the connection again or return home.';
    if (retryButton) {
      retryButton.classList.remove('hidden');
      retryButton.onclick = function () {
        errorDetected = false;
        progressBar?.classList.remove('is-error');
        errorContainer?.classList.add('hidden');
        retryButton.classList.add('hidden');
        fetchProgress();
      };
    }
  }
}

// replace(), not assign(): the finished loading page leaves history, so Back
// from the results goes to the form instead of reloading a done job that
// redirects forward again (owner, 2026-10-25).
function redirectToResults() {
  window.location.replace('/results');
}

function retryCurrentSearch() {
  const form = document.createElement('form');
  form.method = 'POST';
  form.action = '/results_loading';

  form.appendChild(createHiddenInput('csrf_token', csrfToken));
  form.appendChild(createHiddenInput('username', username));
  form.appendChild(createHiddenInput('year', year));
  form.appendChild(createHiddenInput('sort_by', sort_by));
  if (include_unmatched) form.appendChild(createHiddenInput('include_unmatched', '1'));
  form.appendChild(createHiddenInput('release_scope', release_scope));
  if (decade) form.appendChild(createHiddenInput('decade', decade));
  if (release_year) form.appendChild(createHiddenInput('release_year', release_year));
  form.appendChild(createHiddenInput('min_plays', min_plays));
  form.appendChild(createHiddenInput('min_tracks', min_tracks));
  form.appendChild(createHiddenInput('limit_results', limit_results || 'all'));

  document.body.appendChild(form);
  form.submit();
}

if (!job_id) {
  if (stepText) stepText.textContent = 'Missing job identifier';
  if (stepDetails) stepDetails.textContent = 'Return home and start a new search.';
} else {
  fetchProgress();
}
