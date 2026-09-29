# Download Resume and Queue Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable pausing, computer shutdowns, and resumption of YouTube video downloads without restarting progress from 0% or re-entering URLs, by preserving target folders across calendar days and persisting queue states in `.download_queue.json`.

**Architecture:** A lightweight `youtube_downloader/queue.py` module manages serializing and updating queue state in `.download_queue.json`. `runner.py` accepts explicit `output_dir` so yt-dlp checks the original folder where `.part` files exist. `batch.py` updates queue item status and catches `KeyboardInterrupt` for graceful pauses. `cli.py` adds a `--resume` flag and interactive resume detection.

**Tech Stack:** Python 3.9+, `yt-dlp` subprocess CLI, standard library (`json`, `pathlib`, `unittest`).

**Spec:** `docs/superpowers/specs/2026-09-29-download-resume-and-queue-persistence-design.md`

## Global Constraints

- Python `>=3.9` compatibility (`from __future__ import annotations` in all files).
- Subprocess invocations must keep `shell=False`.
- Passwords, cookies, and secret contents must never be logged.
- Queue file must be stored in current working directory / repo root as `.download_queue.json` and ignored in `.gitignore`.
- Tests must use standard-library `unittest` with mocking (no live network requests).

## Review Focus

- Corrupted or partial `.download_queue.json` does not crash the program and is safely discarded with a warning.
- `KeyboardInterrupt` (`Ctrl+C`) leaves the queue file in a valid state with the interrupted item marked `pending`.
- Passing `--resume` when no queue exists prints an informational message and exits code 0.
- When all items in the queue succeed, `.download_queue.json` is automatically deleted.
- Resuming on a subsequent day retains the original batch's `output_dir` instead of creating a new date folder.

---

### Task 1: Queue Persistence Module (`youtube_downloader/queue.py`) & `.gitignore`

**Files:**
- Create: `youtube_downloader/queue.py`
- Modify: `.gitignore`
- Create: `tests/test_queue.py`

**Interfaces:**
- Produces:
  - `get_queue_path() -> Path`
  - `load_queue() -> dict | None`
  - `save_queue(queue_data: dict) -> None`
  - `clear_queue() -> None`
  - `create_queue(urls: list[str], output_dir: str | None = None) -> dict`
  - `get_pending_urls(queue_data: dict) -> list[str]`
  - `update_item_status(queue_data: dict, url: str, status: str) -> None`

- [ ] **Step 1: Add `.download_queue.json` to `.gitignore`**
  Add `.download_queue.json` to `.gitignore`.

- [ ] **Step 2: Write failing tests in `tests/test_queue.py`**
  Write tests covering:
  - `test_create_and_save_queue`: verifies schema, `created_at`, `output_dir` (defaulting to YYYY-MM-DD), items initialized to `pending`.
  - `test_load_queue_when_missing`: returns `None`.
  - `test_load_queue_corrupt_json`: returns `None` and does not raise exception.
  - `test_clear_queue`: removes file cleanly.
  - `test_get_pending_urls`: returns only items with status `pending` or `failed`.
  - `test_update_item_status`: updates item status and calls `save_queue`.

- [ ] **Step 3: Run test to verify it fails**
  Run: `python -m unittest tests/test_queue.py -v`
  Expected: FAIL with `ModuleNotFoundError: No module named 'youtube_downloader.queue'`

- [ ] **Step 4: Implement `youtube_downloader/queue.py`**
  Implement the queue management functions with atomic file write (`tempfile` + `replace` or direct flush).

- [ ] **Step 5: Run tests to verify they pass**
  Run: `python -m unittest tests/test_queue.py -v`
  Expected: PASS

- [ ] **Step 6: Commit**
  ```bash
  git add .gitignore youtube_downloader/queue.py tests/test_queue.py
  git commit -m "feat: add download queue persistence module"
  ```

---

### Task 2: Runner Output Directory Parameter (`youtube_downloader/runner.py`)

**Files:**
- Modify: `youtube_downloader/runner.py`
- Modify: `tests/test_runner.py`

**Interfaces:**
- Consumes: none
- Produces:
  - `build_command(url: str, no_update: bool = False, use_browser_cookies: bool = True, output_dir: str | None = None) -> list[str]`
  - `run_download(url: str, no_update: bool = False, output_dir: str | None = None) -> bool`

- [ ] **Step 1: Write failing tests in `tests/test_runner.py`**
  Add tests:
  - `test_build_command_with_custom_output_dir`: verifies `-o` uses `f"{output_dir}/%(title)s.%(ext)s"`.
  - `test_build_command_default_output_dir`: verifies `-o` falls back to today's date `YYYY-MM-DD`.
  - `test_run_download_passes_output_dir`: verifies `subprocess.run` receives custom `output_dir`.

- [ ] **Step 2: Run test to verify it fails**
  Run: `python -m unittest tests/test_runner.py -v`
  Expected: FAIL (custom `output_dir` not recognized or applied).

- [ ] **Step 3: Implement `output_dir` support in `youtube_downloader/runner.py`**
  Update `build_command` and `run_download` to accept `output_dir: str | None = None`. If provided, use it for `-o`, else calculate `datetime.now().strftime("%Y-%m-%d")`.

- [ ] **Step 4: Run test to verify it passes**
  Run: `python -m unittest tests/test_runner.py -v`
  Expected: PASS

- [ ] **Step 5: Commit**
  ```bash
  git add youtube_downloader/runner.py tests/test_runner.py
  git commit -m "feat: support custom output directory in download runner"
  ```

---

### Task 3: Batch Queue Integration & Graceful Interrupt (`youtube_downloader/batch.py`)

**Files:**
- Modify: `youtube_downloader/batch.py`
- Modify: `tests/test_batch.py`

**Interfaces:**
- Consumes: `youtube_downloader.queue`, `youtube_downloader.runner`
- Produces:
  - `run_batch(urls: list[str], no_update: bool = False, queue_data: dict | None = None, output_dir: str | None = None) -> dict[str, bool]`

- [ ] **Step 1: Write failing tests in `tests/test_batch.py`**
  Add tests:
  - `test_run_batch_updates_queue_progress`: with `queue_data`, updates item status as each finishes.
  - `test_run_batch_clears_queue_on_all_success`: when all items succeed, `clear_queue()` is invoked.
  - `test_run_batch_leaves_queue_on_failure`: when an item fails, queue is not cleared.
  - `test_run_batch_handles_keyboard_interrupt`: when `KeyboardInterrupt` is raised during `run_download`, marks current item as `pending`, saves queue, prints pause message, and returns partial results without crashing.

- [ ] **Step 2: Run test to verify it fails**
  Run: `python -m unittest tests/test_batch.py -v`
  Expected: FAIL

- [ ] **Step 3: Implement queue integration and `KeyboardInterrupt` handling in `youtube_downloader/batch.py`**
  Update `run_batch` to:
  - Pass `output_dir` to `run_download`.
  - Update `queue_data` on each item and persist via `save_queue`.
  - Wrap loop in `try...except KeyboardInterrupt`, update current item to `pending`, call `save_queue`, print pause message, and break.
  - Call `clear_queue()` if and only if all items in `queue_data` have status `completed`.

- [ ] **Step 4: Run test to verify it passes**
  Run: `python -m unittest tests/test_batch.py -v`
  Expected: PASS

- [ ] **Step 5: Commit**
  ```bash
  git add youtube_downloader/batch.py tests/test_batch.py
  git commit -m "feat: integrate queue tracking and graceful interrupt into run_batch"
  ```

---

### Task 4: CLI `--resume` Flag, Interactive Detection & Graceful Pause (`youtube_downloader/cli.py`)

**Files:**
- Modify: `youtube_downloader/cli.py`
- Modify: `tests/test_cli.py`

**Interfaces:**
- Consumes: `youtube_downloader.queue`, `youtube_downloader.batch`, `youtube_downloader.validator`
- Produces:
  - `main() -> None`

- [ ] **Step 1: Write failing tests in `tests/test_cli.py`**
  Add tests:
  - `test_resume_flag_no_queue_prints_info_and_exits_zero`: `python downloader.py --resume` prints `[INFO] No unfinished download session found.` and exits with 0.
  - `test_resume_flag_with_queue_resumes_pending_urls`: loads queue, calls `run_batch` with pending URLs and saved `output_dir`.
  - `test_cli_auto_detects_queue_and_user_accepts`: user enters `y` or Enter to prompt, resumes existing queue.
  - `test_cli_auto_detects_queue_and_user_declines`: user enters `n`, queue is cleared, user inputs new URLs.
  - `test_cli_handles_keyboard_interrupt_gracefully`: exiting batch on interrupt exits with code 130 or 0 cleanly.

- [ ] **Step 2: Run test to verify it fails**
  Run: `python -m unittest tests/test_cli.py -v`
  Expected: FAIL

- [ ] **Step 3: Implement `--resume` and auto-detect logic in `youtube_downloader/cli.py`**
  Update `main()` to:
  - Parse `--resume` from `raw_args`.
  - Handle explicit `--resume` flow.
  - If `--resume` not given, check `load_queue()`. If pending items exist, prompt `Found unfinished download session from <created_at> (<N> items pending). Resume? [Y/n]: `.
  - If starting fresh, initialize `queue_data = create_queue(urls)`.
  - Pass `queue_data` and `output_dir` to `run_batch`.

- [ ] **Step 4: Run test to verify it passes**
  Run: `python -m unittest tests/test_cli.py -v`
  Expected: PASS

- [ ] **Step 5: Commit**
  ```bash
  git add youtube_downloader/cli.py tests/test_cli.py
  git commit -m "feat: add CLI --resume flag and queue auto-detection"
  ```

---

### Task 5: Agent Skill & Documentation Update and Full Regression Suite

**Files:**
- Modify: `skills/youtube-downloader/SKILL.md`
- Run: Full test suite

- [ ] **Step 1: Update `skills/youtube-downloader/SKILL.md`**
  Add `--resume` flag usage to instructions and examples. Explain queue persistence and resume behavior.

- [ ] **Step 2: Run full regression test suite**
  Run: `python -m unittest discover -s tests -v`
  Expected: All tests PASS with code 0.

- [ ] **Step 3: Commit**
  ```bash
  git add skills/youtube-downloader/SKILL.md
  git commit -m "docs: document --resume flag and queue persistence in Agent Skill"
  ```
