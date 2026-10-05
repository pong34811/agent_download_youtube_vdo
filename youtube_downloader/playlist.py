"""Playlist resolution — extract individual video URLs from a YouTube playlist.

A playlist URL (e.g. ``https://www.youtube.com/playlist?list=PL...``) is
expanded into its constituent video URLs before the rest of the pipeline
treats each item as a single video.  This keeps queue persistence,
deduplication, the 10-item batch limit, and resume all working at the
per-video level.
"""
from __future__ import annotations

import json
import subprocess
import sys
from typing import List


def is_playlist_url(url: str) -> bool:
    """Return True if *url* points at a YouTube playlist page."""
    return "/playlist?" in url and ("youtube.com" in url or "youtu.be" in url)


def resolve_playlist(url: str) -> List[str]:
    """Return a list of individual video URLs for every video in *url*.

    Uses ``yt-dlp --flat-playlist --dump-json`` so each playlist entry is
    emitted as a single JSON line with ``_type: "url"`` and a ``url`` field
    pointing at the individual ``watch?v=ID`` page.  Raises ``RuntimeError``
    if yt-dlp exits non-zero (network failure, private playlist, etc.).
    """
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--flat-playlist",
        "--dump-json",
        "--no-playlist",
        url,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, shell=False)
    if proc.returncode != 0:
        raise RuntimeError(f"yt-dlp playlist extraction failed: {proc.stderr.strip()}")

    video_urls: List[str] = []
    for line in proc.stdout.strip().splitlines():
        if not line:
            continue
        entry = json.loads(line)
        # Only "_type": "url" entries are individual videos.  The playlist
        # header entry ("_type": "playlist") carries the playlist id, which
        # must NOT be turned into a watch?v= URL.
        if entry.get("_type") == "url" and entry.get("url"):
            video_urls.append(entry["url"])
    return video_urls