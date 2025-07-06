## Phase 1: Pre-Refactoring Optimization (Optional)

Only follow this step before beginning the major rewrite if there are no issues with 429/Thundering herd.

 - **(CRITICAL) Implement Concurrent API Calls in process_albums**
    - **Goal**: Drastically reduce the ~30-minute processing time for large libraries by running Spotify API calls in parallel.
    - **Action**: In a new branch, refactor `process_albums` to use `asyncio.gather` to parallelize the Spotify API calls. Specifically, modify the `for` loop to use `asyncio.gather`. Create a list of all `fetch_spotify_album_release_date` tasks and then await them all at once to improve performance. Consider using Semaphore, however this has led to many thundering herd issues and 429. Please carefully review documentation on the Spotify API. BE MINDFUL OF THUNDERING HERD PROBLEM. 


## Phase 2: Core Backend Refactoring (The Big Rewrite)

#### TO-DO during rewrite

 - Docstrings/Comments: Write these as functions move into their new files during the refactor. It's more efficient than writing them now and then moving them.

#### Architectural overall planned. Proposed module structure included.

- **(CRITICAL) Establish Application Factory & Configuration**
    - **Goal**: Create a scalable Flask application structure  
    - **Action**: Create `app/` directory, `app/__init__.py` with `create_app()`, and `config.py` for settings.

- **(CRITICAL) Modularize with Blueprints and Services**
    - **Goal**: Separate concerns to make the code maintainable.
    - **Actions**:
        - Move routes into Flask Blueprints (`app/routes/`).
        - Move API-calling logic into `app/services/spotify_client.py` and `app/services/lastfm_client.py`.
        - Move helper functions (`normalize_name`, `format_seconds`) into `app/utils.py`.
        - Move `background_task` into `app/tasks.py`.

- (*HIGH*) Implement Persistent Cache
    - Goal: Make caching survive application restarts.
    - Action: Create `app/cache.py` using `Flask-Caching` and replace the global `REQUEST_CACHE` dictionary.

## Phase 3: High-Value UX & Frontend Improvements

Once the backend is clean, build these features on a solid foundation.

- **(CRITICAL) Username & Year Validation on Homepage**
    - **Goal**: Prevent users from starting invalid searches, acts as error prevention.
    - **Action** : Create a small new API endpoint that checks if a username is valid and returns their registration year. Use `JavaScript` on `index.html` to call this onblur from the username field and dynamically populate the year dropdown.

- (*HIGH*) Master HTML Template
    - Goal: Reduce code duplication on the frontend.
    - Action: Create `base.html` and have all other templates `{% extends %}` it.

- (*HIGH*) Link to Spotify from Results
    - Goal: Add a simple, high-value UX feature.
    - Action: In `results.html`, wrap the album title in an `<a>` tag pointing to `https://open.spotify.com/album/{album.id}`.

- (MEDIUM) Finalize Static File Separation
    - Goal: Complete the separation of `HTML`, `CSS`, and `JS`.
    - Action: Move any remaining inline `<style>` and `<script>` blocks to external files.

## Phase 4: Advanced Features & Future Polish

These can be implemented incrementally once the core application is rebuilt and stable.

- (MEDIUM) Fix "King of Limbs" Bug: Implement the string similarity check using thefuzz in your Spotify service module.
- (MEDIUM) CSV Encoding Fix: Implement the `encoding='utf-8-sig'` fix.
- (low) "All Years" Filter: Add the option to select all years for album sorting and associated logic.
- (LOW) Track-Level Details (Modal/Tooltip): A great feature for "v2.0". It will require modifying the data structures again to pass track-specific data to the template.
- (LOW) Stop/Restart Button on Loading Page: An advanced feature requiring client-side JS and a backend endpoint for task management.

- Another thing I found strange, was for albums *not* on Spotify, yet their metadata was fetched. I can account for one case here:

 

    - "The King of Limbs Live at the Basement", which is *not* on Spotify. I have this album scrobbled from being played in Foobar2k with my local library. Thus - *no metadata should be found* for this album by Radiohead. Yet, in the `unmatched_view` I see this:




**Albums released in 1997 instead of 2018**


| #   | *artist*          | *album*                  |

|-----|-------------------|--------------------------|

| 1   | Elliott Smith     | Either/Or                |

| *n* | . . .             | . . .                    |

| 7   | Radiohead         | OK Computer              |

| 8   | The King of Limbs | **The King of Limbs**    |




* This album is not on Spotify, so I’m confused how it received a `1997` release date. Could this be an incorrect match (e.g., falling back to a similarly named Radiohead release)? I suspect fallback logic or fuzzy matching may have misattributed it to OK Computer or The King of Limbs (Studio). Could you check the matching heuristics used in this case?


# Additional Elements, Checks, and QA


1. Exporting to CSV with albums with special characters or non-latin script creates issues where they break, I think a CSV UTF-8 BOM patch is needed to force UTF-8 w/ BOM for Excel.



2. I need to optimize metadata fetching and Scrobble fetching. Am I using multi-threading or parallel tasks with `concurrent.futures`? Are my rate limiters well optimized as well?



3. Is the debug log output logic properly done and how can I confirm this?



5. Finally, I want to know before moving to Phase 3, if anything on the roadmap should be done *now* or after modularization / in flask blueprints. Here's some of the roadmap, and elements I think would be useful.



### Let me know if any of these would be best to do *now* before Phase 3.

 For those that would be simple implementation and allow for a more seamless transition to modularization, I'd like to know how we should work on these prior to moving to Phase 3 to have as few hiccups as possible.


**Critical Changes prior to Phase 3**


- Write more comprehensive backend function docstrings and comments in app.py.


- Improve responsive design, especially for mobile devices.


- Implement planned log rotation for app_debug.log to oldlogs/. This is something I think would be critical as I don't want to have an extremely bloated app_debug.log.


- Optimize network usage, multi-threading or parallel requests. Batching is already done for pulling last.fm data.



 Then, these following elements seem relevant to Phase 3, but I am not sure if I am thinking of modules for the app properly - I wonder if this logic for different `.py` files is a sound structure. I'd love your input.



#### Conceptualized Phase 3 Plan:

(Please review this and check logic and feasability, or if other modules and blueprints are best. I want the optimal route that allows for modularity, upkeep, and updates with new features.)


- Modularize API calls into services/ modules (lastfm.py, spotify.py, and cache.py).


- Use Flask Blueprints to organize routes.


- Consolidate helper functions into utils.py.


- Move background processing to tasks.py or a dedicated task queue.


- Separate configuration into config.py for cleaner imports.


**Table:**


| File         | Responsibility                       |

| ------------ | ------------------------------------ |

| `lastfm.py`  | Last.fm API calls and utilities      |

| `spotify.py` | Spotify metadata lookups and parsing |

| `cache.py`   | Caching logic and memoization        |

| `utils.py`   | General-purpose helpers              |

| `tasks.py`   | Background/long-running processing   |

| `config.py`  | Centralized app configuration        |

| `routes/`    | Flask Blueprints for page routing    |



## Ideas for better UX and feature rich app:


### What may need tweaks to front and back end but enrich features:



-  Mouseover tooltips with track/genre info. Since the app is already fetching metadata, hovering over an album in a row would allow users to see their most played track from that album.



     * This would be in the `results` page table. I assume, this requires new backend logic to store the song from an album that plays the most, but I am not sure if the backend already has the capacity to do this with minimal function changes, because if the playtime sort function is well-defined and working as intended, it should ONLY be calculating playtime based off what songs the *user* played. Not any other tracks.

     

     This would *also* help me understand if the sort by play time is actually working.



 * If this is the case regarding the playtime sorting, I'm assuming that this would mean the mouseover tooltip to see the *most played* song in that album would be simple. Perhaps simply displaying "Top Track: {top track} | {play count}/{play time}" would be non-intrusive yet informative.


     * **ALTERNATIVELY:** I should already have the album ID. Linking to https://open.spotify.com/album/{id} should be simple in a Jinja template and gives huge UX juice with almost no added complexity - this is what I think, I don't know how true it is.



     * **ALTERNATIVELY:** Allow users to enable a function where they can click a row/album to display a modal where the tracked Scrobbles for their album are listed. This could be a "switch" or button on the `results.html`, where enabling it, would allow users to go further than just the single track tooltip mouse-over. Clicking a row, would display an informative modal with their listens from that album.



         * (e.g. If a user has "In Rainbows" in their results page, clicking the row would pop up a modal that would be a simple, structured table, perhaps like this:




        #### EXAMPLE: Tracks from {album name} you listened to: (better title and layout, this is a concept)



        | **Track**            | **Plays** OR **Play Time** |

        |----------------------|----------------------------|

        | (track name)         | (play count/play time)     |

        | Videotape            | 28                         |

        | Reckoner             | 19                         |

        | Weird Fishes Arpeggi | 16                         |





### There are elements for the front-end that I also would want to implement according to my roadmap, and some would also require back-end changes:



- *(Critical)* Check if username exists before executing filtering and leaving the homepage, and change the way the drop-down for "listening year" appears. It absolutely should *not* display years where the user's account did not exist. For example, at the moment, the drop-down starts at 2005 (When last.fm was first created), to {current year}. However this is bad UX. Users should NOT be able to click invalid years for the username, as this will start the back-end logic, and return an error. Improving this would prevent errors regarding an invalid year, or invalid username from appearing.



- Finalize moving all inline CSS styles and JS scripts into `static/js` and `static/css` for each template. Some are already done - there are just a few templates left.


- Create master HTML templates to reduce duplication and refactor template code to utilize the master HTML template.


- Improve the landing page (`index.html`) copy to be more descriptive for new users.


- (*Considering*) Helvetica Neue for body & headings, but maybe a monospace (IBM Plex Mono? JetBrains Mono?) for smaller data bits like album thresholds, errors, or API notes.


- Handle ALL cases of errors gracefully so no traceback calls are shown in the `error.html`


- Add a `Stop` button to the `loading.html` card which when pressed would pause (or interrupt) the backend runtime gracefully, without producing an error. The goal would be to allow users to then either return to the homepage or restart the filter without having to re-input info in `index.html` if they simply for whatever reason, want to restart. The stop button would, ideally, slide to the left-hand side of the card as two new buttons fade-fin on the card. A `Home` button for returning to the `index.html`, and a `Restart` button which would re-execute the exact filter without returning to `index.html`, simply reload.



     - (*Critical*): At the very least, allow users to return to the home-page with one button in `loading.html` card, in case the back-end is taking too long for their liking, or the user incorrectly selected filters and wants to modify them before waiting for processing and restarting.



- Add "All Years" filter for users to see *all* albums from *all years* appear in their selected listening year.*



    * *Note: While last.fm allows you to see all your most played album per year and sorts by play count, it does NOT sort by play time. Adding this feature, would also help me understand if the app is behaving properly, matching the play counts seen on last.fm for albums where metadata is available on spotify.



    * *Ideally*, selecting "All Years" would disable the user's ability to define album thresholds so they can't set "1 play 1 track" or a permissive threshold as this would hammer the API and take far too long. It should therefore, keep the default defined threshold and lock the slider for defining album thresholds grayed out. 
    