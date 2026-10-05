# AGENTS.md

## Project

Python CLI for downloading individual YouTube videos with `yt-dlp`.

- Supported Python: 3.10+ (`pyproject.toml`).
- Runtime dependency: `yt-dlp`.
- Entry points: `python downloader.py` (compatibility launcher) and installed `download` command.
- Downloads: MP4 merge output, best available video up to 1080p, saved under a `YYYY-MM-DD/` folder in the working directory, or user-specified `--output-dir`.
- Batches: up to 22 unique HTTP(S) YouTube URLs, processed sequentially; playlist URLs expand to individual videos before limit, deduplication, and queue are applied.
- Queue state: `.download_queue.json` in working directory; `--resume` resumes pending/failed items in original output folder. New run detects unfinished queue and asks to resume.
- Cookies: uses local `cookies.txt` if present; otherwise attempts Microsoft Edge browser cookies, then retries without browser cookies. Never expose cookie contents or bypass access restrictions.
- Playlists: playlist?list=... URL expands to individual videos before batch limit, deduplication, and queue.

## Development

- Install: `python -m pip install -e .`
- Run: `python downloader.py [--no-update] [--resume] [--output-dir <dir>] [URL ...]`
- Test: `python -m unittest discover -v`
- No formatter/linter/CI configured; do not claim one is configured.
- Preserve conventions and avoid committing downloaded media, cookies, or local queue state.
