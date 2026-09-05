// Album loading state. The backend owns progress copy and percentages; this
// file renders them and moves a completed browser session to /results.
const {
  job_id,
  username,
  year,
  sort_by,
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
const statAlbums = document.getElementById('stat-albums');
const statCache = document.getElementById('stat-cache');
const statSpotify = document.getElementById('stat-spotify');

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
    revealStat(statAlbums, stats.albums_passing_filter),
    revealStat(statSpotify, stats.spotify_matched)
  ].some(Boolean);

  if (hasAny) liveStatsContainer.classList.remove('hidden');

  if (stats.cache_hits && statCache) {
    statCache.textContent = `${Number(stats.cache_hits).toLocaleString()} albums loaded from cache`;
    statCache.classList.remove('hidden');
  }

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

function showFailure(message, source) {
  errorDetected = true;
  progressBar?.classList.add('is-error');
  errorContainer?.classList.remove('hidden');
  if (errorText) errorText.textContent = message;

  if (errorSource && source) {
    errorSource.textContent = `Source: ${source === 'lastfm' ? 'Last.fm' : 'Spotify'}`;
    errorSource.classList.remove('hidden');
  }
}

/** Explain the pending navigation and retain the three-second reading delay. */
function scheduleResultsRedirect(message) {
  if (stepDetails) stepDetails.textContent = message;
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

    if (!errorDetected) scheduleResultsRedirect('Opening your results\u2026');
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

function redirectToResults() {
  window.location.assign('/results');
}

function retryCurrentSearch() {
  const form = document.createElement('form');
  form.method = 'POST';
  form.action = '/results_loading';

  form.appendChild(createHiddenInput('csrf_token', csrfToken));
  form.appendChild(createHiddenInput('username', username));
  form.appendChild(createHiddenInput('year', year));
  form.appendChild(createHiddenInput('sort_by', sort_by));
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
