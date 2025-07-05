// Read "template variables" injected on the page as window.SCROBBLE
const {
  username,
  year,
  sort_by,
  release_scope,
  decade,
  release_year,
  min_plays,
  min_tracks
} = window.SCROBBLE || {};

// DARK MODE TOGGLE LOGIC
// Find the checkbox in the DOM
const darkSwitch = document.getElementById('darkSwitch');

// If the user has a saved preference for dark mode, apply it on load
const prefersDark = localStorage.getItem('darkMode') === 'true';
if (prefersDark) {
  document.body.classList.add('dark-mode');
  if (darkSwitch) {
    darkSwitch.checked = true;
  }
}

// Whenever the user flips the switch, toggle the .dark-mode class and persist the choice
if (darkSwitch) {
  darkSwitch.addEventListener('change', () => {
    const isDark = darkSwitch.checked;
    document.body.classList.toggle('dark-mode', isDark);
    localStorage.setItem('darkMode', isDark);

    // If there's an inline SVG logo, update its colors manually
    const svgElement = document.querySelector('#logo-wrapper svg');
    if (svgElement) {
      const bars = svgElement.querySelectorAll('.cls-1');
      const textPaths = svgElement.querySelectorAll('#logo-text path, #tagline path');

      if (isDark) {
        bars.forEach(bar => bar.setAttribute('stroke', '#9370DB'));
        textPaths.forEach(path => path.setAttribute('fill', '#f8f9fa'));
      } else {
        bars.forEach(bar => bar.setAttribute('stroke', '#6a4baf'));
        textPaths.forEach(path => path.setAttribute('fill', '#333333'));
      }
    }
  });
}

// PROGRESS BAR & POLLING LOGIC
// Grab all the relevant DOM elements
const progressBar     = document.getElementById('progress-bar');
const stepText        = document.getElementById('step-text');
const stepDetails     = document.getElementById('step-details');
const errorContainer  = document.getElementById('error-container');
const errorText       = document.getElementById('error-text');

let errorDetected = false;

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

async function fetchProgress() {
  try {
    const response     = await fetch('/progress');
    const progressData = await response.json();
    const p            = progressData.progress;  // numeric progress (0–100)

    // Update the progress bar width
    if (progressBar) {
      progressBar.style.width = p + '%';
    }
    // Update the main “message” line (often same as stepDetails)
    if (stepText) {
      stepText.textContent = progressData.message;
    }

    // If the back end signaled an error, show it and redirect after 3s
    if (progressData.error) {
      errorDetected = true;
      if (progressBar) {
        progressBar.classList.remove('bg-primary');
        progressBar.classList.add('bg-danger');
      }
      if (stepDetails) {
        stepDetails.textContent = "An error occurred. Redirecting shortly…";
      }
      if (errorContainer) {
        errorContainer.classList.remove('d-none');
      }
      if (errorText) {
        errorText.textContent = progressData.message;
      }
      setTimeout(() => {
        redirectToResults();
      }, 3000);
      return;
    }

    // Bucketed stepDetails + rotator integration
    if (stepDetails) {
    if (p < 10) {
        // 0–9%: show static text, cancel any rotator
        stopRotatingMessages();
        stepDetails.textContent = "Connecting to last.fm…";

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
          await fetch('/reset_progress', { method: 'POST' });
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

  document.body.appendChild(form);
  form.submit();
}

// Start polling as soon as this script loads
fetchProgress();
