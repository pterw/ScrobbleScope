"""Aggregate and select artist spotlight presentation data without I/O."""

import random

from scrobblescope.utils import format_seconds_mobile


def select_spotlight_artists(results, job_id):
    """Return a stable random sample of five aggregate artists from the top ten."""
    by_artist = {}
    for album in results:
        artist_name = (album.get("artist") or "").strip()
        if not artist_name:
            continue

        key = artist_name.casefold()
        artist = by_artist.setdefault(
            key,
            {
                "name": artist_name,
                "scrobbles": 0,
                "album_count": 0,
                "play_time_seconds": 0,
                "play_time": "",
                "image_url": "",
                "spotify_url": "",
            },
        )
        artist["scrobbles"] += album.get("play_count", 0) or 0
        artist["album_count"] += 1
        artist["play_time_seconds"] += album.get("play_time_seconds", 0) or 0
        if not artist["image_url"] and album.get("album_image"):
            artist["image_url"] = album["album_image"]

    ranked = sorted(
        by_artist.values(),
        key=lambda artist: (
            -artist["scrobbles"],
            -artist["play_time_seconds"],
            artist["name"].casefold(),
        ),
    )[:10]
    for artist in ranked:
        if artist["play_time_seconds"]:
            artist["play_time"] = format_seconds_mobile(artist["play_time_seconds"])

    if len(ranked) <= 5:
        return ranked
    # random is a deterministic shuffler here, not a secret source: seeding
    # on the job ID makes the same job always show the same five spotlight
    # artists (asserted by
    # test_results_page_samples_five_unique_artists_from_aggregate_top_ten).
    # Cryptographic unpredictability would defeat the intent, so bandit's
    # B311 warning does not apply.
    return random.Random(str(job_id)).sample(ranked, 5)  # nosec B311
