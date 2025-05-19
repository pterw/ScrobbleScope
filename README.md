# ScrobbleScope - Your Last.fm Listening Habits, Visualized

[![Status](https://img.shields.io/badge/status-work_in_progress-yellow.svg)](https://github.com/pterw/ScrobbleScopehttps://github.com/pterw/ScrobbleScope#readme)
ScrobbleScope is a web application designed for Last.fm users to get a deeper insight into their music listening habits. It fetches your track scrobbles for a selected year, processes them with various filters, and enriches album data with metadata from the Spotify API. The primary goal is to help you visualize your top albums, especially for creating "Album of the Year" (AOTY) lists or simply exploring your musical journey.

This project was initially built to identify top albums released in a specific year that were also listened to in that same year but has since been refactored into a more feature-rich web app.

## ✨ Features

* **Last.fm Integration:** Fetches your listening history for a specified year.
* **Spotify Metadata:** Enriches album data with release dates, cover art, and track runtimes from Spotify.
* **Flexible Filtering:**
    * Filter albums by listening year.
    * Filter albums by their release date:
        * Same as the listening year.
        * Previous year.
        * Specific decades.
        * Custom specific release year.
    * Define album listening thresholds (minimum track plays and minimum unique tracks per album). *(Note: Custom threshold filtering beyond defaults is currently under development; defaults of 10 plays/3 unique tracks are applied if options are changed).*
* **Advanced Sorting:**
    * Sort your top albums by **total track play count**.
    * Sort by **total listening time** (calculated from the runtime of tracks you've listened to). *(Note: Playtime sorting is currently undergoing refinement for accuracy).*
* **Dynamic UI:**
    * User-friendly interface with options that appear dynamically based on your selections.
    * Light and Dark mode support for comfortable viewing (toggle available on all pages).
    * Responsive design for usability on various devices. *(Note: Ongoing improvements for mobile responsiveness).*
* **Data Export:**
    * Export your filtered album list to a `.csv` file.
    * Save a snapshot of your results table as a `.jpeg` image.
* **Unmatched Album Insights:**
    * View a quick list of albums that were in your listening history but didn't match your selected filters via a modal.
    * Access a detailed report categorizing why albums were excluded (sticky navigation bar for easy access on this page).
* **User Feedback:**
    * Loading indicators with progress updates during data fetching and processing.
    * Clear error messages and redirection for invalid inputs or API issues.

## 📸 Screenshots

Here's a glimpse of ScrobbleScope in action:

**1. Main Input Form (Dark Mode)**
*Configure your search with various listening and release date filters. Options for decades and custom thresholds (shown with defaults selected) appear dynamically based on user choices.*
![ScrobbleScope Input Form - Dark Mode](docs/images/index_dark_thresholds_decade.png) 
**2. Results Page - Album List (Light Mode)**
*View your filtered and sorted albums, here shown sorted by play count. Includes album art, artist, play count, and release date. Buttons for data export and accessing unmatched albums are visible.*
![ScrobbleScope Results - Light Mode](docs/images/results_light_playcount.png) 
**3. Results Page - Quick Unmatched Modal (Dark Mode)**
*Easily access a quick view of albums that didn't meet your filter criteria directly from the results page, shown here in dark mode.*
![ScrobbleScope Results with Unmatched Modal - Dark Mode](docs/images/results_dark_modal.png) 
**4. Detailed Unmatched Albums Report (Dark Mode)**
*Get a comprehensive list of albums that were excluded, categorized by the reason for exclusion. The filter summary at the top provides context for the excluded items.*
![ScrobbleScope Detailed Unmatched Report - Dark Mode](docs/images/unmatched_dark_top.png) "

## 🛠️ Tech Stack & Implementation Details

ScrobbleScope is built with a focus on asynchronous operations for API interactions and a clean user experience.

**Core Technologies:**

* **Backend:** Python 3.x, Flask
* **Frontend:** HTML5, CSS3, JavaScript (ES6+), Bootstrap 5 for responsive layout & components.
* **APIs:**
    * Last.fm API: `user.getrecenttracks` is used to gather scrobbles, paginated until the specified year's cutoff.
    * Spotify API: Used to search each album and fetch `release_date` for filtering, as well as artwork and track runtimes.
* **Core Python Libraries:**
    * `aiohttp` & `aiolimiter`: For asynchronous API calls. Rate limits are managed (Last.fm & Spotify: 20 requests/sec) with built-in retries.
    * `python-dotenv`: For managing API keys and configuration from a `.env` file (which also controls an optional `DEBUG_MODE`).
    * `Jinja2`: For server-side HTML templating.
    * `Flask`: Micro web framework.

**Key Implementation Highlights:**

* **Configuration:** API credentials and an optional `DEBUG_MODE` are controlled via a `.env` file.
* **Data Normalization:** Artist and album names are cleaned of punctuation and common suffixes (e.g., "deluxe edition", "remastered") for more robust matching between Last.fm data and Spotify search queries.
* **Caching:** An in-memory request cache (`REQUEST_CACHE` in `app.py` with a 1-hour TTL) is used to minimize redundant API calls and improve performance during a user session.
* **Styling & UX:**
    * **Dark Mode:** A toggle switch allows users to switch themes, with preferences persisted via `localStorage`. CSS custom properties (`--var`) are used for dynamic color adjustments.
    * **Animations:** Subtle fade-in animations are used for the logo, progress bar elements, and result cards to enhance visual feedback. The main logo is an animated SVG emulating a waveform.
    * **Accessibility:** Efforts have been made to improve accessibility, such as using `aria-labels` on SVGs and interactive elements.

## 🚀 Getting Started (Work in Progress)

This project is currently a work in progress. However, if you wish to run it locally:

**Prerequisites:**

* Python (3.9+ recommended)
* Pip (Python package installer)
* Git

**Setup:**

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/]https://github.com/pterw/ScrobbleScope.git
    cd [ScrobbleScope]
    ```
2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    ```
    Activate it:
    * Windows (Command Prompt): `venv\Scripts\activate`
    * Windows (PowerShell): `.\venv\Scripts\Activate.ps1`
        *(If script execution is disabled, you may need to run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`)*
    * macOS/Linux (bash/zsh): `source venv/bin/activate`
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set up environment variables:**
    * Create a `.env` file in the root directory of the project.
    * Add your API keys to this file. **Do NOT commit this file to Git.**
        ```env
        LASTFM_API_KEY="your_lastfm_api_key_here"
        SPOTIFY_CLIENT_ID="your_spotify_client_id_here"
        SPOTIFY_CLIENT_SECRET="your_spotify_client_secret_here"
        # Optional: For enabling more verbose logging
        # DEBUG_MODE="1"
        ```
5.  **Run the application:**
    ```bash
    python app.py
    ```
    The application should then be accessible at `http://127.0.0.1:5000/`.

**Project File Structure:**
```
│  .env                 # API keys & configuration (not committed)
│  .gitignore           # Specifies intentionally untracked files
│  app.py               # Main Flask application logic
│  requirements.txt     # Python package dependencies
│  README.md            # This file
│
├───logs/               # Application logs (e.g., app_debug.log - not committed)
│
├───templates/          # Jinja2 HTML templates
│   │  error.html       # Custom error page
│   │  index.html       # Home page / filter submission form
│   │  loading.html     # Progress display page
│   │  results.html     # Page to display filtered album results
│   │  unmatched.html   # Page for albums that didn't meet filters
│   │
│   └───inline/
│           scrobble_scope_inline.svg # Inline SVG logo asset
│
└───static/             # (Placeholder for future dedicated CSS/JS if not using inline/CDN)
└───css/
└───js/
└───images/         # (Placeholder for other static images, not README screenshots)
```
## 🚧 Current Status & Future Plans

ScrobbleScope is nearing its initial launch phase but is still under active development.

**Key areas for improvement and upcoming features:**

* [ ] Refine and thoroughly test the playtime sorting calculation.
* [ ] Fully implement and test custom album threshold filtering functionality.
* [ ] Enhance the `loading.html` page with dynamic "fun facts" about the user's listening year.
* [ ] Further optimize performance for users with very large listening histories.
* [ ] Improve responsive design, especially for mobile devices.
* [ ] Write more comprehensive backend function docstrings and comments in `app.py`.
* [ ] Conduct thorough QA testing across different browsers and use cases.
* [ ] Improve the landing page (`index.html`) copy to be more descriptive for new users.
* [ ] Deploy to a cloud platform (e.g., Heroku or Vercel).
* [ ] Implement planned log rotation for `app_debug.log` to `oldlogs/`.

## 🤝 Contributing (Optional)

While this is currently a personal project, feedback and suggestions are welcome! If you encounter any issues or have ideas for improvement, please feel free to open an issue in this repository.

## 📜 License (Optional)

## 🙏 Acknowledgements

* Last.fm API
* Spotify API
* Bootstrap
* Flask & the Flask community
* Contributors to the Python libraries used in this project.

---

Created by Peter Wiercioch
