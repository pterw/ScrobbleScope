// Read "template variables" injected on the page as window.SCROBBLE
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

// CSRF token for all JS-initiated POST requests (injected by server via meta tag)
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';

// PROGRESS BAR & POLLING LOGIC
// Grab all the relevant DOM elements
const progressBar      = document.getElementById('progress-bar');
const stepText         = document.getElementById('step-text');
const stepDetails      = document.getElementById('step-details');
const errorContainer   = document.getElementById('error-container');
const errorText        = document.getElementById('error-text');
const liveStatsContainer = document.getElementById('live-stats');
const statScrobbles    = document.getElementById('stat-scrobbles');
const statPages        = document.getElementById('stat-pages');
const statAlbums       = document.getElementById('stat-albums');
const statCache        = document.getElementById('stat-cache');
const statSpotify      = document.getElementById('stat-spotify');

let errorDetected = false;

// SCROBBLE CYCLING: alternates between "Scanned N" and "That's N/365 per day"
let scrobbleCycleTimeoutId = null;
let scrobbleCycleActive    = false;

function startScrobbleCycle(count) {
  if (scrobbleCycleActive || !statScrobbles) return;
  scrobbleCycleActive = true;
  const avgPerDay = Math.round(count / 365);
  const avgText  = `Average: ~${avgPerDay.toLocaleString()} scrobbles/day in ${year}`;
  const scanText = `Scanned ${count.toLocaleString()} scrobbles in ${year}`;

  function fadeTo(text, thenCb, thenDelay) {
    // Clear the CSS entrance animation so JS transition takes full control
    statScrobbles.style.animation = 'none';
    statScrobbles.style.opacity = '1';  // lock starting opacity before transition
    requestAnimationFrame(() => {
      statScrobbles.style.transition = 'opacity 0.6s ease';
      statScrobbles.style.opacity = '0';
      setTimeout(() => {
        statScrobbles.textContent = text;
        statScrobbles.style.opacity = '1';
        if (thenCb) scrobbleCycleTimeoutId = setTimeout(thenCb, thenDelay);
      }, 650);
    });
  }

  function showAvg()  { fadeTo(avgText,  showScan, 5000); }
  function showScan() { fadeTo(scanText, showAvg,  4000); }

  // Begin cycle after 6 s (user needs time to read the initial stat)
  scrobbleCycleTimeoutId = setTimeout(showAvg, 6000);
}

function stopScrobbleCycle() {
  scrobbleCycleActive = false;
  if (scrobbleCycleTimeoutId !== null) {
    clearTimeout(scrobbleCycleTimeoutId);
    scrobbleCycleTimeoutId = null;
  }
  // Restore opacity in case a fade-out was in progress
  if (statScrobbles) statScrobbles.style.opacity = '1';
}

// ROTATOR: wait 5 sec in [40,60) before cycling messages
let rotateTimeoutId   = null;
let rotatorIntervalId = null;

// Messages to rotate through after the initial 5 sec delay
const rotatingMessages = [  
  "Crunching metadata in the background…",
  "Hang tight, this may take a moment…",
  "Still working on your albums…",
  "Checking album data, please wait…",
  "Almost done compiling your albums…",
  "Just a bit longer, we're finalizing your results…",
];

// Called after the 5 sec delay; begins 7 sec‐interval rotation
function startRotatingMessages() {
  let idx = 0;
  if (stepDetails) stepDetails.textContent = rotatingMessages[idx];
  rotatorIntervalId = setInterval(() => {
    idx = (idx + 1) % rotatingMessages.length;
    if (stepDetails) stepDetails.textContent = rotatingMessages[idx];
  }, 7000);
}

// Cancels both the pending 5 sec timeout and any running interval
function stopRotatingMessages() {
  if (rotateTimeoutId !== null) {
    clearTimeout(rotateTimeoutId);
    rotateTimeoutId = null;
  }
  if (rotatorIntervalId !== null) {
    clearInterval(rotatorIntervalId);
    rotatorIntervalId = null;
  }
}

// Utility to create a hidden input for form‐redirect
function createHiddenInput(name, value) {
  const input = document.createElement('input');
  input.type  = 'hidden';
  input.name  = name;
  input.value = value;
  return input;
}

function updateLiveStats(stats) {
  if (!stats || !liveStatsContainer) return;
  let hasAny = false;

  if (stats.total_scrobbles && statScrobbles) {
    // Only update text while cycle is idle; cycle owns the element once started
    if (!scrobbleCycleActive) {
      statScrobbles.textContent = `Scanned ${stats.total_scrobbles.toLocaleString()} scrobbles in ${year}`;
      statScrobbles.classList.remove('d-none');
      startScrobbleCycle(stats.total_scrobbles);
    }
    hasAny = true;
  }
  if (stats.pages_fetched && statPages) {
    statPages.textContent = `Fetched ${stats.pages_fetched} pages of scrobbles`;
    statPages.classList.remove('d-none');
    hasAny = true;
  }
  if (stats.albums_passing_filter && statAlbums) {
    statAlbums.textContent = `${stats.albums_passing_filter} albums passed your thresholds (out of ${stats.unique_albums.toLocaleString()} unique)`;
    statAlbums.classList.remove('d-none');
    hasAny = true;
  }
  if (stats.cache_hits && statCache) {
    statCache.textContent = `${stats.cache_hits.toLocaleString()} albums loaded from cache`;
    statCache.classList.remove('d-none');
    hasAny = true;
  }
  if (stats.spotify_matched && statSpotify) {
    statSpotify.textContent = `Matched ${stats.spotify_matched} albums on Spotify`;
    statSpotify.classList.remove('d-none');
    hasAny = true;
  }
  if (hasAny) { liveStatsContainer.classList.remove('d-none'); }

  // Show partial data warning if present
  const partialWarning = document.getElementById('partial-warning');
  const partialWarningText = document.getElementById('partial-warning-text');
  if (stats.partial_data_warning && partialWarning && partialWarningText) {
    partialWarningText.textContent = stats.partial_data_warning;
    partialWarning.classList.remove('d-none');
  }
}

async function fetchProgress() {
  try {
    const response = await fetch(`/progress?job_id=${encodeURIComponent(job_id)}`);
    const progressData = await response.json();
    const p            = progressData.progress;  // numeric progress (0–100)

    // Update the progress bar width
    if (progressBar) {
      progressBar.style.width = p + '%';
    }
    // Update the main "message" line (often same as stepDetails)
    if (stepText) {
      stepText.textContent = progressData.message;
    }

    // Update personalized live stats
    updateLiveStats(progressData.stats || {});

    // If the back end signaled an error, show it with appropriate actions
    if (progressData.error) {
      errorDetected = true;
      stopRotatingMessages();
      stopScrobbleCycle();

      if (progressBar) {
        progressBar.classList.remove('bg-primary');
        progressBar.classList.add('bg-danger');
      }
      if (errorContainer) {
        errorContainer.classList.remove('d-none');
      }
      if (errorText) {
        errorText.textContent = progressData.message;
      }

      // Show error source if available
      const errorSource = document.getElementById('error-source');
      if (errorSource && progressData.error_source) {
        const sourceLabel = progressData.error_source === 'lastfm' ? 'Last.fm' : 'Spotify';
        errorSource.textContent = `Source: ${sourceLabel}`;
        errorSource.classList.remove('d-none');
      }

      // Show retry button for retryable errors, auto-redirect for non-retryable
      const retryButton = document.getElementById('retry-button');
      if (progressData.retryable && retryButton) {
        retryButton.classList.remove('d-none');
        retryButton.addEventListener('click', () => {
          retryButton.disabled = true;
          retryButton.textContent = 'Retrying\u2026';
          retryCurrentSearch();
        }, { once: true });

        if (stepDetails) {
          stepDetails.textContent = "You can retry or return home.";
        }
      } else {
        // Non-retryable error (e.g., user not found): auto-redirect
        if (stepDetails) {
          stepDetails.textContent = "Redirecting shortly\u2026";
        }
        setTimeout(() => {
          redirectToResults();
        }, 3000);
      }
      return;
    }

    // Bucketed stepDetails + rotator integration
    if (stepDetails) {
    if (p < 10) {
        // 0–9%: clear any rotator; leave details blank while initializing
        stopRotatingMessages();
        stepDetails.textContent = "";

    } else if (p < 20) {
        // 10–19%: show static text, cancel any rotator
        stopRotatingMessages();
        stepDetails.textContent = "Getting your tracks…";   
    } else if (p < 30) {
        // 20–29%: show static text, cancel any rotator
        stopRotatingMessages();
        stepDetails.textContent = "Getting ready…";             

    } else if (p < 40) {
        // 30–39%: static text, cancel any rotator
        stopRotatingMessages();
        stepDetails.textContent = "Putting your albums together…";

    } else if (p < 60) {
        // 40–59%: schedule the rotator to start after 5 sec (if not already)
        if (!rotatorIntervalId && rotateTimeoutId === null) {
        rotateTimeoutId = setTimeout(() => {
            startRotatingMessages();
            rotateTimeoutId = null;
        }, 5000);
        }
        // (Optional) If you want to show a placeholder until 5 sec elapse:
        //stepDetails.textContent = "Preparing to work on your albums…";

    } else if (p < 80) {
        // 60–79%: cancel rotator, show static text
        stopRotatingMessages();
        stepDetails.textContent = "Compiling your top album list…";

    } else if (p < 100) {
        // 80–99%: cancel rotator, show static text
        stopRotatingMessages();
        stepDetails.textContent = "Almost there! Finalizing results…";

    } else {
        // p === 100: final message, cancel rotator
        stopRotatingMessages();
        stepDetails.textContent = "All done! Redirecting in 3 seconds…";
    }
    }

    // Poll again if not yet at 100 and no error:
    if (p < 100 && !errorDetected) {
      setTimeout(fetchProgress, 1000);
    }
    // Final redirect on successful 100%
    else if (p >= 100 && !errorDetected) {
      stopScrobbleCycle();
      setTimeout(() => {
        redirectToResults();
      }, 3000);
    }
  }
  catch (error) {
    console.error('Error fetching progress:', error);
    if (stepText) {
      stepText.textContent = 'An error occurred while checking progress.';
    }
    if (stepDetails) {
      stepDetails.textContent = 'Please try refreshing the page or return to the homepage.';
    }
    if (progressBar) {
      progressBar.classList.remove('bg-primary');
      progressBar.classList.add('bg-danger');
    }
    if (errorContainer) {
      errorContainer.classList.remove('d-none');
    }
    if (errorText) {
      errorText.textContent = "Failed to connect to the server. Please try again.";
    }

    // Insert a “Reset and Try Again” button if not already present
    if (!document.querySelector('.reset-button')) {
      const resetButton = document.createElement('button');
      resetButton.textContent = 'Reset and Try Again';
      resetButton.classList.add('btn', 'btn-primary', 'mt-3');
      resetButton.addEventListener('click', async () => {
        try {
          if (job_id) {
            await fetch('/reset_progress', {
              method: 'POST',
              headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': csrfToken },
              body: new URLSearchParams({ job_id }).toString()
            });
          }
          window.location.href = '/';
        } catch (e) {
          console.error('Failed to reset progress:', e);
        }
      });

      const container = document.querySelector('.loading-container');
      if (container) {
        resetButton.classList.add('reset-button');
        container.appendChild(resetButton);
      }
    }
  }
}

//Helper to build and submit the POST form to /results_complete
function redirectToResults() {
  const form = document.createElement('form');
  form.method = 'POST';
  form.action = '/results_complete';

  form.appendChild(createHiddenInput('csrf_token', csrfToken));
  form.appendChild(createHiddenInput('job_id', job_id));
  form.appendChild(createHiddenInput('username', username));
  form.appendChild(createHiddenInput('year', year));
  form.appendChild(createHiddenInput('sort_by', sort_by));
  form.appendChild(createHiddenInput('release_scope', release_scope));

  if (decade) {
    form.appendChild(createHiddenInput('decade', decade));
  }
  if (release_year) {
    form.appendChild(createHiddenInput('release_year', release_year));
  }

  form.appendChild(createHiddenInput('min_plays', min_plays));
  form.appendChild(createHiddenInput('min_tracks', min_tracks));
  form.appendChild(createHiddenInput('limit_results', limit_results || 'all'));

  document.body.appendChild(form);
  form.submit();
}

// Resubmit the original search to /results_loading (creates a fresh job)
function retryCurrentSearch() {
  const form = document.createElement('form');
  form.method = 'POST';
  form.action = '/results_loading';

  form.appendChild(createHiddenInput('csrf_token', csrfToken));
  form.appendChild(createHiddenInput('username', username));
  form.appendChild(createHiddenInput('year', year));
  form.appendChild(createHiddenInput('sort_by', sort_by));
  form.appendChild(createHiddenInput('release_scope', release_scope));

  if (decade) {
    form.appendChild(createHiddenInput('decade', decade));
  }
  if (release_year) {
    form.appendChild(createHiddenInput('release_year', release_year));
  }

  form.appendChild(createHiddenInput('min_plays', min_plays));
  form.appendChild(createHiddenInput('min_tracks', min_tracks));
  form.appendChild(createHiddenInput('limit_results', limit_results || 'all'));

  document.body.appendChild(form);
  form.submit();
}

// Start polling as soon as this script loads
if (!job_id) {
  if (stepText) {
    stepText.textContent = 'Missing job identifier.';
  }
  if (stepDetails) {
    stepDetails.textContent = 'Please return home and start a new search.';
  }
} else {
  fetchProgress();
}
