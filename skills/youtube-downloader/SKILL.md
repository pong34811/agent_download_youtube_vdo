---
name: youtube-downloader
version: 0.0.3
description: Download up to ten unique YouTube video URLs sequentially with queue persistence, automatic queue detection, and resume support.
---

# YouTube Downloader Skill

Use this skill when the user asks to download YouTube videos (up to 10 unique URLs per batch) or resume an interrupted batch. Only download content the user is authorized to access.

## Requirements and entry points

- Python 3.10+ and the `yt-dlp` package (`python -m pip install -e .` from the repository root).
- Preferred launcher: `python downloader.py`; installed console entry point: `download`.
- Downloads use best available video up to 1080p, merged to MP4, under a `YYYY-MM-DD/` folder in the current working directory.

## Workflow

1. Collect up to 10 YouTube URLs (individual `watch?v=ID` pages, or a `playlist?list=...` URL). The CLI resolves playlist URLs into individual video URLs before validation, deduplication, and the 10-item batch limit.
2. If there is an unfinished `.download_queue.json`, the CLI asks whether to resume before processing the new input. Accept to continue the old queue, or decline to discard its state and proceed with the new batch. For non-interactive resumption, run `python downloader.py --resume`.
3. Run from the repository root, passing URLs as arguments when available:
   - Single: `python downloader.py <URL>`
   - Batch: `python downloader.py <URL1> <URL2> ...`
   - Resume: `python downloader.py --resume`
   - Skip automatic `yt-dlp` upgrade for this invocation: `python downloader.py --no-update <URL...>` (also works with `--resume` or interactive mode).
4. Keep stdout/stderr visible so the user can follow `yt-dlp` progress and the per-item summary.
5. Report success/failure per URL and note that failed items remain resumable. A failed URL does not stop later URLs from being attempted.

## Input and queue behavior

- Only HTTP(S) URLs on `youtube.com`, its subdomains, or `youtu.be` are accepted.
- Duplicate URLs are removed preserving input order; the 10-item limit applies after deduplication.
- Playlists are disabled (`--no-playlist`).
- Invalid input rejects the entire batch before downloads start.
- `.download_queue.json` is stored in the current working directory and records each URL's status plus the original output directory. `--resume` retries pending and failed items in that same directory.
- Successful completion of every queue item clears the queue. Failed or interrupted batches preserve it; Ctrl+C during a download marks that item pending so it can be resumed.
- Unless `--no-update` is provided, the CLI attempts to upgrade `yt-dlp` once per invocation. An update failure is a warning and downloading continues.

## Cookie and safety rules

- The downloader uses `cookies.txt` in the working directory when present; otherwise it attempts to read Microsoft Edge browser cookies, then retries without browser cookies if that attempt fails.
- Never expose or print cookie contents, copy cookies elsewhere, or modify authentication to bypass access restrictions. Do not ask the user to provide secrets in chat.
- If content is unavailable or access is denied, report the failure; do not attempt circumvention.

## Exit codes

- `0`: all requested downloads succeeded, or resume found no pending items.
- `1`: invalid input, user cancelled interactive input, or at least one download failed.

## Examples

```bash
python downloader.py https://www.youtube.com/watch?v=dQw4w9WgXcQ
python downloader.py https://youtu.be/abc123 https://youtu.be/def456
python downloader.py --no-update https://www.youtube.com/watch?v=abc123
python downloader.py --resume
python downloader.py
```

