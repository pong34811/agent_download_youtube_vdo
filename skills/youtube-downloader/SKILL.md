---
name: youtube-downloader
version: 0.0.2
description: Download up to ten YouTube videos sequentially using the local CLI with queue persistence and resume support. Collects URLs, validates them, runs the downloader, and reports per-item results.
---

# YouTube Downloader Skill

Use this skill when the user asks to download one or more YouTube videos (up to 10 at a time), or to resume an interrupted download session.

## How to use

1. Collect up to ten YouTube URLs from the user (`youtube.com` or `youtu.be`, HTTP/HTTPS only).
2. Do not accept more than ten URLs in one batch — ask the user to split if needed.
3. Run the downloader CLI from the repository root:
   - Single URL: `python downloader.py <URL>`
   - Multiple URLs: `python downloader.py <URL1> <URL2> ...`
   - Resume interrupted download: `python downloader.py --resume`
   - Skip auto-update: add `--no-update` before the URLs or flag
4. Stream the output so the user can see yt-dlp progress in real time.
5. After all downloads finish, report per-item success or failure clearly.

## URL rules

- Only `http://` or `https://` scheme.
- Host must be `youtube.com`, any subdomain of `youtube.com` (e.g. `music.youtube.com`), or `youtu.be`.
- Playlist URLs are blocked (`--no-playlist` is always passed).

## Rules

- Never expose or print cookie file contents.
- Never modify authentication logic to bypass access restrictions.
- If a URL is invalid or not a YouTube URL, tell the user before running anything.
- If a download fails (403, 401, unavailable), report the error and continue with remaining URLs.
- Downloads are saved to a folder named with the session creation date (`YYYY-MM-DD/`) in the current working directory.
- Download progress and queue state are tracked in `.download_queue.json`. When resuming via `--resume`, the original session folder is preserved so yt-dlp resumes partially downloaded `.part` files rather than starting over.
- When all items in the batch complete successfully, the queue is cleared automatically.
- The tool auto-updates `yt-dlp` once per invocation unless `--no-update` is passed.

## Example invocations

```bash
# Single video
python downloader.py https://www.youtube.com/watch?v=dQw4w9WgXcQ

# Multiple videos (up to 10)
python downloader.py https://youtu.be/abc123 https://youtu.be/def456

# Resume an interrupted session
python downloader.py --resume

# Skip auto-update
python downloader.py --no-update https://www.youtube.com/watch?v=abc123

# Interactive mode (no URL args)
python downloader.py
# > paste one URL per line, blank line to start
```

## Exit codes

- `0` — all requested unique videos downloaded successfully (or `--resume` found no pending items).
- `1` — invalid input OR at least one video failed.

