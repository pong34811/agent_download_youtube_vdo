# YouTube Downloader Project Snapshot

Generated: 2026-10-05

## Overview
Python CLI for downloading individual YouTube videos with yt-dlp.
- Python 3.10+
- Runtime dep: yt-dlp
- Entry points: `python downloader.py` and `download` command
- MP4 merge, best video up to 1080p, saved under YYYY-MM-DD/ or `--output-dir`
- Batch limit: 22 unique URLs after playlist expansion, deduplication
- Queue: `.download_queue.json`, `--resume` supports pending/failed items
- Cookies: cookies.txt > Edge browser cookies fallback

## Key Files
- pyproject.toml
- AGENTS.md
- downloader.py
- youtube_downloader/__init__.py
- youtube_downloader/cli.py
- youtube_downloader/validator.py
- youtube_downloader/batch.py
- youtube_downloader/runner.py
- youtube_downloader/queue.py
- youtube_downloader/playlist.py
- skills/youtube-downloader/SKILL.md
- tests/*

## Current Queue State
File: .download_queue.json
Status: 19 completed, 3 failed (Video unavailable)

## Skill Version
youtube-downloader 0.0.4
Description: Download up to 22 unique YouTube video URLs sequentially with queue persistence, playlist expansion, output-dir support, auto detection and resume.
