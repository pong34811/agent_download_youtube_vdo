# AGENTS.md

## Project

Python CLI for downloading individual YouTube videos with `yt-dlp`.

- Supported Python: 3.10+ (`pyproject.toml`).
- Runtime dependency: `yt-dlp`.
- Entry points: `python downloader.py` (compatibility launcher) and installed `download` command.
- Downloads: MP4 merge output, best available video up to 1080p, saved under a `YYYY-MM-DD/` folder in the working directory.
- Batches: up to 10 unique HTTP(S) YouTube URLs, processed sequentially; playlist URLs expand to their individual videos before the limit, deduplication, and queue are applied.
- Queue state: `.download_queue.json` in the working directory; `--resume` resumes pending/failed items in the original output folder. Starting a new run detects an unfinished queue and asks whether to resume it.
- Cookies: uses local `cookies.txt` if present; otherwise attempts Microsoft Edge browser cookies, then retries without browser cookies if that attempt fails. Never expose cookie contents or bypass access restrictions.
- Playlists: a `playlist?list=...` URL expands to its individual videos before the batch limit, deduplication, and queue are applied.

## Development

- Install: `python -m pip install -e .`
- Run: `python downloader.py [--no-update] [--resume] [URL ...]`
- Test: `python -m unittest discover -v`
- There is no configured formatter, linter, or CI workflow; do not claim one is configured.
- Preserve existing project conventions and avoid committing downloaded media, cookies, or local queue state.
