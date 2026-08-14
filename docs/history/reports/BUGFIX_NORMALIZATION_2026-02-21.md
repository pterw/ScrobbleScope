# Normalization Bug Fixes (2026-02-21)

Date: 2026-02-21
Triggered by: Third-party audit review (Gemini Pro analysis of domain.py)
Implemented by: Claude Sonnet 4.6

---

## 1. Summary

A static analysis review identified four correctness defects in `scrobblescope/domain.py`
and a coverage gap in `scrobblescope/lastfm.py`. Three were confirmed as production bugs
with real-world impact. All four were fixed and covered by new tests. The fixes were
validated against the owner's listening history, including a non-Latin-script album
("betcover!!" / Japanese-title release from 2025) that had previously been silently
excluded from results.

---

## 2. Bugs found and confirmed

### Bug 1 (Critical): normalize_track_name destroys non-Latin characters

**File:** `scrobblescope/domain.py:normalize_track_name`

**Root cause:**
The function used `unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()`.
NFKD decomposition cannot decompose Japanese kana/kanji, Cyrillic, Korean hangul, Arabic,
or most non-Latin scripts into ASCII equivalents. The `encode("ascii", "ignore")` call
then stripped all such characters entirely, returning an empty string for any purely
non-Latin track name.

**Impact (production):**
In `fetch_top_albums_async`, track names from Last.fm scrobbles are normalized via
`normalize_track_name` and accumulated in a `track_counts` dict:

```python
normalized = normalize_track_name(name)
albums[key]["track_counts"][normalized] += 1
```

If every track on an album normalized to `""`, the dict had exactly one key regardless
of how many distinct tracks the user had played. The `min_tracks` filter then rejected
the album:

```python
filtered = {
    k: v for k, v in albums.items()
    if v["play_count"] >= min_plays and len(v["track_counts"]) >= min_tracks
}
```

A Japanese album with 10 distinct tracks and 50 total plays would silently fail
`len(track_counts) >= 3` because `len({"": 50}) == 1`. The album never reached
`process_albums` and was not placed in the unmatched list either -- it vanished
without a trace.

Secondary impact: even if an album had reached `process_albums`, the playtime
calculation:

```python
play_time_sec = sum(
    track_durations.get(track, 0) * count
    for track, count in original_data["track_counts"].items()
)
```

...would have produced zero for any album with non-Latin tracks, because
`track_durations` (built from Spotify track names via the same `normalize_track_name`)
would also have collapsed to `{"": duration_of_last_track}`. The mismatch between
all-`""` counts and a single `""` duration key made `play_time_seconds` unreliable.

**Contrast with normalize_name:**
`normalize_name` already used `unicodedata.normalize("NFKC", text)` without ASCII
encoding, correctly preserving non-Latin characters. This was explicitly noted in a
comment added in 2025. `normalize_track_name` was never updated to match, creating
an undocumented schism between the two normalization paths.

**Fix:**
Replace `NFKD + encode("ascii", "ignore")` with `NFKC` (same as `normalize_name`):

```python
# Before
n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()

# After
n = unicodedata.normalize("NFKC", name).lower()
```

---

### Bug 2 (High): normalize_name applies metadata word-stripping to artist names

**File:** `scrobblescope/domain.py:normalize_name`

**Root cause:**
`normalize_name` had a single `clean()` closure that included a `safe_to_remove_words`
set (`{"deluxe", "edition", "remastered", "special", "bonus", "tracks", "ep", ...}`).
This same closure was called identically for both the artist and album arguments:

```python
return clean(artist), clean(album)
```

These words are release-metadata suffixes that belong only in album titles (e.g.
"Album Name (Deluxe Edition)" should strip to "Album Name"). They are not inherently
metadata when they appear in artist names.

**Impact:**
Any artist whose name contained one of these words had their normalized key corrupted:

- "New Edition" (real R&B group) -> "new" (loses identity)
- "Special" (artist name) -> "" (empty key)
- "Bonus" (artist name) -> "" (empty key)
- "EP" (artist name) -> "" (empty key)

Empty artist keys caused a further problem: two completely unrelated artists could
collide on the same dict key. For example:

- `normalize_name("Bonus", "Tracks")` -> `("", "")` ("tracks" also in removal set)
- `normalize_name("Special", "Edition")` -> `("", "")` ("special" and "edition" both in set)

Both scrobble groups would be merged into the same `albums` dict entry in
`fetch_top_albums_async`, silently combining play counts and track lists from two
different artists into one result entry.

**Fix:**
Rename the set to `album_metadata_words` and refactor `clean()` to accept an optional
`remove_words` parameter (defaulting to `frozenset()`). Apply the set to the album
argument only:

```python
def clean(text, remove_words=frozenset()):
    ...
    filtered_words = [word for word in words if word not in remove_words]
    ...

return clean(artist), clean(album, album_metadata_words)
```

The album deduplication use case is fully preserved: "Album Name (Deluxe Edition)"
and "Album Name" still both normalize to "album name" because the album string still
receives the full removal pass.

---

### Bug 3 (Medium): Punctuation inconsistency between normalize_name and normalize_track_name

**File:** `scrobblescope/domain.py:normalize_track_name`

**Root cause:**
`normalize_name` used `str.maketrans(string.punctuation, " " * len(string.punctuation))`
to replace all 32 ASCII punctuation characters with spaces. `normalize_track_name` used
a manually hardcoded list of 13 specific characters:

```python
for char in [":", "-", "(", ")", "[", "]", "/", "\\", ".", ",", "!", "?", "'"]:
    n = n.replace(char, " ")
```

Characters omitted from the track name path include `&`, `@`, `#`, `*`, `~`, `+`,
`;`, `<`, `>`, `=`, `^`, `_`, `` ` ``, `{`, `|`, `}`.

**Impact:**
A track titled "Rock & Roll" would normalize to "rock & roll" (ampersand retained),
while an album titled "Rock & Roll" normalized to "rock  roll" (ampersand stripped).
Because track matching compares Last.fm scrobble names against Spotify track names
(both going through `normalize_track_name`), the practical impact on matching was
lower than for album/artist keys. However, the inconsistency was a latent correctness
risk for any track name containing these characters.

**Fix:**
Replace the hardcoded loop with `str.maketrans(string.punctuation, ...)` to match
`normalize_name`:

```python
translator = str.maketrans(string.punctuation, " " * len(string.punctuation))
n = n.translate(translator)
```

---

### Bug 4 (Coverage gap): fetch_top_albums_async had zero test coverage

**File:** `scrobblescope/lastfm.py:fetch_top_albums_async`

**Root cause:**
The function was never tested. It contains the most complex business logic in the
codebase: timestamp-boundary enforcement, per-album play-count aggregation, per-album
distinct-track counting, `min_plays` and `min_tracks` threshold filtering, and job-stat
reporting. A logic error in any of these would silently corrupt results for all users.

Existing tests in `test_lastfm_service.py` covered only `check_user_exists` (happy
path and 404) and `fetch_recent_tracks_page_async` (429 retry and 404 error).

**Fix:** See Section 4.

---

## 3. Relationship between bugs

Bugs 1 and 2 share a common root cause: both functions were missing context-awareness
about what they were normalizing. `normalize_track_name` did not know it needed to
preserve the character set used by `normalize_name` (the album key path). `normalize_name`
did not distinguish between artist-context and album-context word removal.

Together, these two bugs made ScrobbleScope systematically incorrect for any user who
listens primarily to non-Latin-script music. The album key was generated correctly
(NFKC, Bug 1 fix already in `normalize_name`), but the track names used to populate
`track_counts` were all collapsed to `""`, causing the `min_tracks` filter to silently
reject the album before it ever reached Spotify.

---

## 4. Fixes applied

**`scrobblescope/domain.py`** -- both functions rewritten:

1. `normalize_track_name`: Changed normalization from `NFKD + encode("ascii","ignore")`
   to `NFKC` (11 characters changed). Replaced hardcoded 13-char punctuation loop with
   `str.maketrans(string.punctuation, ...)` for full consistency with `normalize_name`.
   Docstring updated to explain the rationale and the previous regression.

2. `normalize_name`: Renamed `safe_to_remove_words` to `album_metadata_words`. Added
   `remove_words=frozenset()` parameter to the `clean()` closure. Changed the return
   statement to pass the word set to the album call only. Docstring updated to document
   the context-aware behavior. Inline comment updated to explain why artist receives
   no word removal.

No behavior change for ASCII-only input. All existing tests continued to pass.

---

## 5. New tests added

### tests/test_domain.py (9 new tests, total 15)

| Test | Verifies |
|------|----------|
| `test_normalize_track_name_preserves_japanese` | Katakana track name survives normalization (regression guard for NFKD bug) |
| `test_normalize_track_name_preserves_cyrillic` | Cyrillic track name lowercased and preserved |
| `test_normalize_track_name_fullwidth_punctuation_converted` | NFKC converts full-width punctuation (U+FF01) to ASCII then strips it |
| `test_normalize_track_name_strips_ampersand` | `&` and other previously-omitted ASCII punctuation now stripped |
| `test_normalize_name_preserves_artist_edition_word` | "New Edition" artist key retains "edition" |
| `test_normalize_name_strips_edition_from_album_not_artist` | "edition" stripped from album, preserved in artist (same call) |
| `test_normalize_name_ep_preserved_in_artist_stripped_from_album` | "EP" as artist = "ep"; "EP" as album = "" |
| `test_normalize_name_no_collision_after_artist_fix` | ("Bonus","Tracks") and ("Special","Edition") produce distinct keys |
| `test_normalize_name_and_track_name_agree_on_non_latin` | Both functions produce non-empty output for Japanese input (cross-function parity test) |

### tests/services/test_lastfm_logic.py (7 new tests, new file)

| Test | Verifies |
|------|----------|
| `test_fetch_top_albums_aggregates_play_counts` | play_count and distinct track_counts are correct across multiple tracks |
| `test_fetch_top_albums_min_plays_filter` | Album below min_plays threshold is excluded |
| `test_fetch_top_albums_min_tracks_filter` | Album below min_tracks threshold is excluded |
| `test_fetch_top_albums_skips_out_of_bounds_timestamps` | Scrobbles from a different year do not inflate play counts |
| `test_fetch_top_albums_skips_now_playing_track` | Last.fm "now playing" sentinel (no date field) is excluded; play_count not inflated |
| `test_fetch_top_albums_non_latin_tracks_counted_distinctly` | Japanese track names counted as 3 distinct keys, not collapsed to 1; album passes min_tracks filter |
| `test_fetch_top_albums_sets_job_stats` | total_scrobbles, unique_albums, albums_passing_filter are reported correctly |

---

## 6. Real-world validation

**Test case used by owner (flounder14):**
- Artist: betcover!!
- Album: Japanese-title 2025 release (previously excluded)
- Listening year: 2025
- Filter: Same as release year
- Tracks: 7 distinct tracks, minimum 3 plays each

**Before fix:** Album was absent from results with no unmatched entry. It failed the
`min_tracks` filter silently because all 7 Japanese track names normalized to `""`,
making `len(track_counts) == 1`.

**After fix:** Album appears in results with correct play count and track count.
Playtime calculation also receives correct non-empty track keys from the Spotify
track detail response, enabling accurate duration matching.

Second validation:
- Artist: betcover!!
- Album: Japanese-title 2021 release (10 unique tracks, 68 plays in 2021)
- Listening year: 2021
- Filter: Same as release year
- Result: Appeared correctly with all 10 unique tracks counted.

---

## 7. Impact and forward guidance

The `normalize_track_name` fix is a correctness restoration for any user whose listening
history includes albums in non-Latin scripts. The error was silent -- no exception, no
unmatched entry, no log warning. Users affected by this would have seen systematically
incomplete results without any indication of why.

The `normalize_name` artist-stripping fix is low-probability in practice (requires an
artist name that exactly matches a metadata word) but is mathematically guaranteed to
corrupt results when it does occur.

The `fetch_top_albums_async` test gap is now closed. The new test file
`tests/services/test_lastfm_logic.py` should be extended if the aggregation logic
changes in future feature work (e.g., top-songs feature).

No changes to API contracts, database schema, routes, or templates. No migration needed.
