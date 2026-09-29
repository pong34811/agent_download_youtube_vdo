# Design Spec: Download Resume and Queue Persistence

**Status:** Written for user review; implementation has not started.

## 1. Goal

Enable users and agents to pause, interrupt (e.g. computer shutdown, `Ctrl+C`, network loss), and resume downloading YouTube videos without restarting already-downloaded videos or partial downloads from 0%.

Specifically:
1. Preserve download target directories across calendar days so that yt-dlp's native chunk/fragment resume (`.part` files) finds existing partial downloads even when the machine is shut down and restarted days later.
2. Provide a persistent queue state mechanism (`.download_queue.json`) tracking each URL's status (`pending`, `completed`, `failed`).
3. Support a `--resume` CLI flag to resume interrupted queues directly without re-entering URLs.
4. Auto-detect an unfinished queue when running the interactive CLI or providing new inputs, giving the user a prompt to resume or start fresh.
5. Handle `Ctrl+C` (`KeyboardInterrupt`) gracefully by preserving queue progress and providing a clear message to the user.
6. Update the Agent Skill (`skills/youtube-downloader/SKILL.md`) to reflect the `--resume` option and queue behavior.

## 2. Current Project Analysis

- `youtube_downloader/runner.py`:
  - `build_command` currently hardcodes `today = datetime.now().strftime("%Y-%m-%d")` and `-o f"{today}/%(title)s.%(ext)s"`.
  - If a download starts on day 1 and is interrupted, running again on day 2 looks into day 2's folder, losing reference to `.part` files in day 1's folder.
  - By default, yt-dlp uses `-c` (`--continue`) and `--part`, meaning resumption is fully supported if and only if the destination folder and filename template match.
- `youtube_downloader/batch.py`:
  - Iterates over URLs sequentially. Does not persist state across process restarts.
  - Does not catch `KeyboardInterrupt` specifically to save state or output helpful resumption instructions.
- `youtube_downloader/cli.py`:
  - Parses flags `--no-update` and positional URL arguments.
  - Does not support `--resume` flag.
  - Does not check for existing unfinished queues.
- `.gitignore`:
  - Currently ignores `cookies.txt`, `__pycache__`, etc., but does not ignore `.download_queue.json`.

## 3. Architecture & Data Model

### 3.1 Queue File Location & Git Exclusion
- File path: `.download_queue.json` in the current working directory / repository root.
- Added to `.gitignore` to prevent committing local queue state.

### 3.2 Queue Schema
```json
{
  "created_at": "2026-09-29T23:30:00",
  "output_dir": "2026-09-29",
  "items": [
    {
      "url": "https://www.youtube.com/watch?v=abc123",
      "status": "completed"
    },
    {
      "url": "https://www.youtube.com/watch?v=def456",
      "status": "pending"
    }
  ]
}
```
- `output_dir`: Fixed string directory name (defaults to `YYYY-MM-DD` of when the queue was created).
- `items`: List of items, each with `url` (normalized/validated string) and `status` (`pending`, `completed`, `failed`).

### 3.3 New Module: `youtube_downloader/queue.py`
Functions provided:
- `get_queue_path() -> Path`: Return path to `.download_queue.json`.
- `load_queue() -> dict | None`: Read and validate JSON. If missing, return `None`. If corrupted/invalid schema, log a warning and return `None`.
- `save_queue(queue_data: dict) -> None`: Safely write queue JSON to file (atomic write via temporary file or direct dump with flush).
- `clear_queue() -> None`: Remove `.download_queue.json` if it exists.
- `create_queue(urls: list[str], output_dir: str | None = None) -> dict`: Initialize a new queue dict with all URLs set to `pending`.
- `get_pending_urls(queue_data: dict) -> list[str]`: Extract URLs whose status is `pending` or `failed`.
- `update_item_status(queue_data: dict, url: str, status: str) -> None`: Update item status and persist to disk.

### 3.4 Updates to `youtube_downloader/runner.py`
- Modify `build_command(url: str, no_update: bool = False, use_browser_cookies: bool = True, output_dir: str | None = None) -> list[str]`:
  - If `output_dir` is provided and non-empty, use `output_dir`.
  - Otherwise, default to `datetime.now().strftime("%Y-%m-%d")`.
  - Output template: `f"{target_dir}/%(title)s.%(ext)s"`.
- Modify `run_download(url: str, no_update: bool = False, output_dir: str | None = None) -> bool`:
  - Pass `output_dir` to `build_command`.

### 3.5 Updates to `youtube_downloader/batch.py`
- Modify `run_batch(urls: list[str], no_update: bool = False, queue_data: dict | None = None, output_dir: str | None = None) -> dict[str, bool]`:
  - If `queue_data` is provided:
    - As each URL finishes, update `queue_data` item status (`completed` if True, `failed` if False) and call `save_queue`.
  - Handle `KeyboardInterrupt`:
    - Catch `KeyboardInterrupt` during loop.
    - Mark current in-progress URL as `pending` (since it did not finish).
    - Save queue to disk via `save_queue`.
    - Print clear pause message:
      ```text
      [PAUSED] Download paused safely.
      To resume later, run: python downloader.py --resume
      ```
    - Return partial `results` collected so far.
  - If all items in queue are `completed`: call `clear_queue()`.
  - If any items remain `pending` or `failed`: keep queue file on disk.

### 3.6 Updates to `youtube_downloader/cli.py`
- Parse `--resume` flag.
- **When `--resume` is explicitly passed:**
  - Call `load_queue()`.
  - If no queue or no pending/failed items:
    - Print `[INFO] No unfinished download session found.`
    - Exit 0.
  - If queue exists:
    - Extract pending URLs.
    - Run auto-update if not `--no-update`.
    - Run batch with the recorded `output_dir`.
- **When `--resume` is NOT passed:**
  - Check `load_queue()`.
  - If an unfinished queue exists:
    - Prompt user: `Found unfinished download session from <date> (<N> items pending). Resume? [Y/n]: `
    - If user enters 'y', 'yes', or empty enter: proceed with resuming the existing queue.
    - If user enters 'n' or 'no': clear existing queue and proceed to normal input collection.
  - If no queue exists, collect URLs normally, create new queue with current date as `output_dir`, and execute batch.
- Clean exit handling:
  - If interrupted by `Ctrl+C`, exit with 0 or 130 without printing unhandled traceback.

## 4. Agent Skill Updates

In `skills/youtube-downloader/SKILL.md`:
- Document `--resume` option in CLI usage: `python downloader.py --resume`.
- Explain queue persistence and how agent can check or resume incomplete downloads.

## 5. Testing & Verification Plan

All tests will use `unittest` with mocking (no external network or live YouTube calls).

### 5.1 New Tests: `tests/test_queue.py`
- Test queue file creation, serialization, and retrieval.
- Test corrupt JSON recovery (warns and returns `None`).
- Test item status updates and atomic writes.
- Test queue cleanup (`clear_queue`).
- Test `get_pending_urls` filtering.

### 5.2 Updates to `tests/test_runner.py`
- Test `build_command` uses custom `output_dir` when provided.
- Test `build_command` defaults to current date when `output_dir` is None.

### 5.3 Updates to `tests/test_batch.py`
- Test `run_batch` updates queue items on each download success/failure.
- Test `run_batch` handles `KeyboardInterrupt`, sets current item status, saves queue, and exits gracefully.
- Test `run_batch` deletes queue when all items succeed.

### 5.4 Updates to `tests/test_cli.py`
- Test `--resume` flag with no queue outputs `No unfinished download session found` and exits 0.
- Test `--resume` flag with unfinished queue calls batch with pending items and saved `output_dir`.
- Test interactive prompt on existing queue: accepting 'Y' resumes queue.
- Test interactive prompt on existing queue: declining 'n' clears queue and accepts new URLs.

## 6. Scope Exclusions

- No multi-queue management (single active queue `.download_queue.json` is sufficient for up to 10 URLs).
- No background daemon process (resuming is user/agent triggered).
- No modification of third-party yt-dlp internals or authentication logic.
