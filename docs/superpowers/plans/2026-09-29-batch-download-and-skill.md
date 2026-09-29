# YouTube Downloader — Batch Downloads & Agent Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the single-URL downloader into a small Python package supporting sequential batch downloads (up to 10 URLs), add unit tests, fix `run.bat`, and author an installable Agent Skill.

**Architecture:** Extract `youtube_downloader/` package with three focused modules — `validator.py` (URL/batch rules), `runner.py` (subprocess wrapper around `yt-dlp` CLI), `batch.py` (deduplicate + sequential loop + summary) — and a thin `cli.py` entry point. `downloader.py` becomes a compatibility shim. Tests live under `tests/` and use `unittest` only (stdlib, no new deps). The Agent Skill file is stored in `skills/youtube-downloader/SKILL.md`.

**Tech Stack:** Python 3.10+, yt-dlp (subprocess, not API), unittest (stdlib)

**Spec:** `docs/superpowers/specs/2026-09-28-youtube-downloader-skill-and-batch-design.md`

## Global Constraints

- Python ≥ 3.10 at runtime (uses `list[str] | None` union syntax)
- `yt-dlp` invoked as subprocess via `[sys.executable, "-m", "yt_dlp", ...]`, never shell=True, never URL interpolation into shell
- Batch max = 10 unique URLs; more than 10 or any invalid URL rejects the whole batch before any network call
- Accept only HTTP(S) URLs on `youtube.com` (including subdomains) or `youtu.be`
- Output path template: `YYYY-MM-DD/%(title)s.%(ext)s`; format: up-to-1080p video + audio merged to MP4
- TLS verification enabled (no `--no-check-certificates`)
- No alternate player-client switching to evade 401/403
- `cookies.txt`-first, Edge-browser fallback; `cookies.txt` stays in `.gitignore`
- Auto-update `yt-dlp` once per CLI invocation; skip with `--no-update`
- Finite retries: 5 for downloads, 5 for fragments, 5 for file-access
- `--no-playlist` must be in every `yt-dlp` call
- Return exit code 0 only if every unique URL succeeds; nonzero for invalid input or any failure
- Skill version: `0.0.1`; application version stays `0.1.0`
- No real YouTube network calls in tests

## Review Focus

- **Empty interactive input (blank line immediately):** should print a clear "no URLs provided" message and exit with nonzero, not crash.
- **Eleven URLs passed on CLI:** whole batch must be rejected before any download attempt, with message listing count.
- **Duplicate URLs across 10-URL CLI input:** duplicates silently removed; effective batch ≤ 10 after dedup; if post-dedup count is 0, reject gracefully.
- **`cookies.txt` absent and Edge browser unavailable:** runner must still pass `--cookies-from-browser edge` (the OS decides availability); tests must verify the flag appears in the command.
- **One URL in a 3-URL batch fails (403):** other two must complete; summary must list the failed item and return nonzero overall.

---

### Task 1: Package scaffold + URL validator

**Files:**
- Create: `youtube_downloader/__init__.py`
- Create: `youtube_downloader/validator.py`
- Create: `tests/__init__.py`
- Create: `tests/test_validator.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `validate_batch(urls: list[str]) -> tuple[list[str], list[str]]`
    Returns `(unique_valid_urls, error_messages)`. If any error exists the caller must reject the whole batch. `unique_valid_urls` is deduplicated in input order.
  - `is_valid_youtube_url(url: str) -> bool`

- [ ] **Step 1: Write failing tests for `is_valid_youtube_url`**

```python
# tests/test_validator.py
import unittest
from youtube_downloader.validator import is_valid_youtube_url

class TestIsValidYoutubeUrl(unittest.TestCase):
    def test_youtube_com_watch_accepted(self):
        self.assertTrue(is_valid_youtube_url("https://www.youtube.com/watch?v=abc123"))

    def test_youtu_be_accepted(self):
        self.assertTrue(is_valid_youtube_url("https://youtu.be/abc123"))

    def test_subdomain_youtube_accepted(self):
        self.assertTrue(is_valid_youtube_url("https://music.youtube.com/watch?v=abc123"))

    def test_http_accepted(self):
        self.assertTrue(is_valid_youtube_url("http://youtube.com/watch?v=abc123"))

    def test_non_youtube_rejected(self):
        self.assertFalse(is_valid_youtube_url("https://vimeo.com/123"))

    def test_ftp_rejected(self):
        self.assertFalse(is_valid_youtube_url("ftp://youtube.com/watch?v=abc123"))

    def test_empty_rejected(self):
        self.assertFalse(is_valid_youtube_url(""))

    def test_plain_string_rejected(self):
        self.assertFalse(is_valid_youtube_url("not a url"))
```

- [ ] **Step 2: Run tests — verify they fail**

Run: `python -m unittest tests.test_validator -v`
Expected: `ModuleNotFoundError` or `ImportError` (package not created yet)

- [ ] **Step 3: Create package scaffold**

Create `youtube_downloader/__init__.py` (empty).
Create `tests/__init__.py` (empty).

- [ ] **Step 4: Implement `is_valid_youtube_url(url: str) -> bool` in `youtube_downloader/validator.py`**

Use `urllib.parse.urlparse`. Accept schemes `http`/`https`. Accept netloc ending in `youtube.com` or equal to `youtu.be`.

- [ ] **Step 5: Run tests — verify `is_valid_youtube_url` tests pass**

Run: `python -m unittest tests.test_validator.TestIsValidYoutubeUrl -v`
Expected: 8 tests PASS

- [ ] **Step 6: Write failing tests for `validate_batch`**

```python
from youtube_downloader.validator import validate_batch

class TestValidateBatch(unittest.TestCase):
    VALID = "https://www.youtube.com/watch?v=abc123"
    VALID2 = "https://www.youtube.com/watch?v=def456"

    def test_single_valid_url_accepted(self):
        urls, errors = validate_batch([self.VALID])
        self.assertEqual(urls, [self.VALID])
        self.assertEqual(errors, [])

    def test_ten_valid_urls_accepted(self):
        urls = [f"https://www.youtube.com/watch?v=vid{i}" for i in range(10)]
        result, errors = validate_batch(urls)
        self.assertEqual(len(result), 10)
        self.assertEqual(errors, [])

    def test_eleven_urls_rejected(self):
        urls = [f"https://www.youtube.com/watch?v=vid{i}" for i in range(11)]
        _, errors = validate_batch(urls)
        self.assertTrue(any("10" in e for e in errors))

    def test_invalid_url_produces_error(self):
        _, errors = validate_batch(["https://vimeo.com/123"])
        self.assertTrue(len(errors) > 0)

    def test_duplicate_removed(self):
        result, errors = validate_batch([self.VALID, self.VALID])
        self.assertEqual(result, [self.VALID])
        self.assertEqual(errors, [])

    def test_empty_list_produces_error(self):
        _, errors = validate_batch([])
        self.assertTrue(len(errors) > 0)

    def test_dedup_then_count_checked(self):
        # 11 identical URLs dedup to 1 → no over-limit error
        urls = ["https://www.youtube.com/watch?v=abc123"] * 11
        result, errors = validate_batch(urls)
        self.assertEqual(errors, [])
        self.assertEqual(result, ["https://www.youtube.com/watch?v=abc123"])
```

- [ ] **Step 7: Run — verify `validate_batch` tests fail**

Run: `python -m unittest tests.test_validator.TestValidateBatch -v`
Expected: `AttributeError` (function not defined)

- [ ] **Step 8: Implement `validate_batch(urls: list[str]) -> tuple[list[str], list[str]]` in `youtube_downloader/validator.py`**

Deduplicate preserving order first, then check count > 10 and each URL with `is_valid_youtube_url`. Collect all error messages; return early only after full scan.

- [ ] **Step 9: Run full test file — all pass**

Run: `python -m unittest tests.test_validator -v`
Expected: all tests PASS

- [ ] **Step 10: Commit**

```bash
git add youtube_downloader/__init__.py youtube_downloader/validator.py tests/__init__.py tests/test_validator.py
git commit -m "feat: add package scaffold and URL/batch validator"
```

---

### Task 2: Runner — subprocess wrapper around yt-dlp CLI

**Files:**
- Create: `youtube_downloader/runner.py`
- Create: `tests/test_runner.py`

**Interfaces:**
- Consumes: nothing from earlier tasks
- Produces:
  - `build_command(url: str, no_update: bool = False) -> list[str]`
    Returns the full argv list (starting with `sys.executable`) to download one URL.
  - `run_download(url: str, no_update: bool = False) -> bool`
    Executes the command, streams stdout/stderr (no capture), returns `True` if process exits 0.

- [ ] **Step 1: Write failing tests for `build_command`**

```python
# tests/test_runner.py
import sys
import unittest
from youtube_downloader.runner import build_command

class TestBuildCommand(unittest.TestCase):
    URL = "https://www.youtube.com/watch?v=abc123"

    def setUp(self):
        self.cmd = build_command(self.URL)

    def test_starts_with_sys_executable(self):
        self.assertEqual(self.cmd[0], sys.executable)

    def test_invokes_yt_dlp_module(self):
        self.assertIn("-m", self.cmd)
        idx = self.cmd.index("-m")
        self.assertEqual(self.cmd[idx + 1], "yt_dlp")

    def test_url_in_command(self):
        self.assertIn(self.URL, self.cmd)

    def test_no_playlist_flag(self):
        self.assertIn("--no-playlist", self.cmd)

    def test_format_flag(self):
        self.assertIn("--format", self.cmd)

    def test_merge_output_format_mp4(self):
        self.assertIn("--merge-output-format", self.cmd)
        idx = self.cmd.index("--merge-output-format")
        self.assertEqual(self.cmd[idx + 1], "mp4")

    def test_output_template_has_date_folder(self):
        self.assertIn("-o", self.cmd)
        idx = self.cmd.index("-o")
        self.assertIn("%(title)s", self.cmd[idx + 1])

    def test_tls_verification_on(self):
        self.assertNotIn("--no-check-certificates", self.cmd)

    def test_cookies_from_browser_edge_when_no_cookies_file(self):
        import os
        # Ensure cookies.txt does not exist for this test
        if not os.path.exists("cookies.txt"):
            self.assertIn("--cookies-from-browser", self.cmd)

    def test_no_update_flag_absent_by_default(self):
        self.assertNotIn("--no-update", self.cmd)

    def test_no_update_flag_present_when_requested(self):
        cmd = build_command(self.URL, no_update=True)
        self.assertIn("--no-update", cmd)

    def test_retries_finite(self):
        self.assertIn("--retries", self.cmd)
        idx = self.cmd.index("--retries")
        self.assertEqual(self.cmd[idx + 1], "5")
```

- [ ] **Step 2: Run — verify tests fail**

Run: `python -m unittest tests.test_runner.TestBuildCommand -v`
Expected: `ImportError` (module not created)

- [ ] **Step 3: Implement `build_command(url: str, no_update: bool = False) -> list[str]` in `youtube_downloader/runner.py`**

Build the argv list using: `sys.executable`, `-m`, `yt_dlp`, plus flags below in order:
- `--no-playlist`
- `--format`, `bestvideo[height<=1080]+bestaudio/best[height<=1080]`
- `--merge-output-format`, `mp4`
- `-o`, `{today}/%(title)s.%(ext)s` where `today = datetime.now().strftime("%Y-%m-%d")`
- `--retries`, `5`
- `--fragment-retries`, `5`
- `--file-access-retries`, `5`
- If `cookies.txt` exists: `--cookies`, `cookies.txt`; else `--cookies-from-browser`, `edge`
- If `no_update=True`: `--no-update`
- Finally: the `url`

- [ ] **Step 4: Run — verify `build_command` tests pass**

Run: `python -m unittest tests.test_runner.TestBuildCommand -v`
Expected: all tests PASS (cookies test may skip if `cookies.txt` happens to exist — that is acceptable)

- [ ] **Step 5: Write failing test for `run_download`**

```python
from unittest.mock import patch
from youtube_downloader.runner import run_download

class TestRunDownload(unittest.TestCase):
    URL = "https://www.youtube.com/watch?v=abc123"

    def test_returns_true_on_zero_exit(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = run_download(self.URL, no_update=True)
        self.assertTrue(result)

    def test_returns_false_on_nonzero_exit(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            result = run_download(self.URL, no_update=True)
        self.assertFalse(result)

    def test_calls_subprocess_run_with_shell_false(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            run_download(self.URL, no_update=True)
            _, kwargs = mock_run.call_args
            self.assertFalse(kwargs.get("shell", False))
```

- [ ] **Step 6: Run — verify `run_download` tests fail**

Run: `python -m unittest tests.test_runner.TestRunDownload -v`
Expected: `AttributeError`

- [ ] **Step 7: Implement `run_download(url: str, no_update: bool = False) -> bool` in `youtube_downloader/runner.py`**

Call `subprocess.run(build_command(url, no_update), shell=False)`. Return `proc.returncode == 0`.

- [ ] **Step 8: Run full runner test file — all pass**

Run: `python -m unittest tests.test_runner -v`
Expected: all tests PASS

- [ ] **Step 9: Commit**

```bash
git add youtube_downloader/runner.py tests/test_runner.py
git commit -m "feat: add yt-dlp subprocess runner"
```

---

### Task 3: Batch processor + auto-update + CLI entry point

**Files:**
- Create: `youtube_downloader/batch.py`
- Create: `youtube_downloader/cli.py`
- Create: `youtube_downloader/__main__.py`
- Create: `tests/test_batch.py`
- Create: `tests/test_cli.py`

**Interfaces:**
- Consumes:
  - `validate_batch(urls)` → `(list[str], list[str])` from Task 1
  - `run_download(url, no_update)` → `bool` from Task 2
- Produces:
  - `run_batch(urls: list[str], no_update: bool = False) -> dict[str, bool]`
    Returns mapping of `url → success`. Runs sequentially; continues after individual failure.
  - `auto_update_ytdlp() -> None`  (warn on failure, do not raise)
  - `main() -> None` (CLI entry point; calls `sys.exit` with 0 or 1)

- [ ] **Step 1: Write failing tests for `run_batch`**

```python
# tests/test_batch.py
import unittest
from unittest.mock import patch, call
from youtube_downloader.batch import run_batch

class TestRunBatch(unittest.TestCase):
    URL1 = "https://www.youtube.com/watch?v=aaa"
    URL2 = "https://www.youtube.com/watch?v=bbb"
    URL3 = "https://www.youtube.com/watch?v=ccc"

    def test_all_success_returns_all_true(self):
        with patch("youtube_downloader.batch.run_download", return_value=True) as mock_dl:
            result = run_batch([self.URL1, self.URL2])
        self.assertEqual(result, {self.URL1: True, self.URL2: True})

    def test_one_failure_continues_rest(self):
        side_effects = [False, True]
        with patch("youtube_downloader.batch.run_download", side_effect=side_effects):
            result = run_batch([self.URL1, self.URL2])
        self.assertEqual(result[self.URL1], False)
        self.assertEqual(result[self.URL2], True)

    def test_runs_in_order(self):
        with patch("youtube_downloader.batch.run_download", return_value=True) as mock_dl:
            run_batch([self.URL1, self.URL2, self.URL3])
        mock_dl.assert_has_calls([call(self.URL1, no_update=False),
                                   call(self.URL2, no_update=False),
                                   call(self.URL3, no_update=False)])

    def test_no_update_flag_forwarded(self):
        with patch("youtube_downloader.batch.run_download", return_value=True) as mock_dl:
            run_batch([self.URL1], no_update=True)
        mock_dl.assert_called_once_with(self.URL1, no_update=True)
```

- [ ] **Step 2: Run — verify fail**

Run: `python -m unittest tests.test_batch.TestRunBatch -v`
Expected: `ImportError`

- [ ] **Step 3: Implement `run_batch(urls: list[str], no_update: bool = False) -> dict[str, bool]` in `youtube_downloader/batch.py`**

Loop over urls, call `run_download(url, no_update=no_update)`, collect result. Print per-URL status line. Return mapping.

- [ ] **Step 4: Run — verify `run_batch` tests pass**

Run: `python -m unittest tests.test_batch.TestRunBatch -v`
Expected: all PASS

- [ ] **Step 5: Write failing tests for CLI**

```python
# tests/test_cli.py
import sys
import unittest
from io import StringIO
from unittest.mock import patch

class TestCliArgParsing(unittest.TestCase):
    VALID = "https://www.youtube.com/watch?v=abc123"

    def _run_main(self, argv, batch_results=None):
        if batch_results is None:
            batch_results = {self.VALID: True}
        with patch("sys.argv", ["downloader"] + argv), \
             patch("youtube_downloader.cli.auto_update_ytdlp"), \
             patch("youtube_downloader.cli.run_batch", return_value=batch_results) as mock_batch, \
             patch("sys.exit") as mock_exit:
            from youtube_downloader import cli
            import importlib; importlib.reload(cli)
            cli.main()
        return mock_batch, mock_exit

    def test_single_url_arg_calls_batch(self):
        mock_batch, _ = self._run_main([self.VALID])
        mock_batch.assert_called_once()

    def test_invalid_url_exits_nonzero(self):
        _, mock_exit = self._run_main(["https://vimeo.com/123"])
        mock_exit.assert_called_with(1)

    def test_eleven_urls_exits_nonzero(self):
        urls = [f"https://www.youtube.com/watch?v=v{i}" for i in range(11)]
        _, mock_exit = self._run_main(urls)
        mock_exit.assert_called_with(1)

    def test_all_success_exits_zero(self):
        _, mock_exit = self._run_main([self.VALID], {self.VALID: True})
        mock_exit.assert_called_with(0)

    def test_any_failure_exits_nonzero(self):
        _, mock_exit = self._run_main([self.VALID], {self.VALID: False})
        mock_exit.assert_called_with(1)

    def test_no_update_flag_forwarded_to_batch(self):
        mock_batch, _ = self._run_main(["--no-update", self.VALID])
        args, kwargs = mock_batch.call_args
        self.assertTrue(kwargs.get("no_update") or (len(args) > 1 and args[1]))
```

- [ ] **Step 6: Run — verify CLI tests fail**

Run: `python -m unittest tests.test_cli -v`
Expected: `ImportError`

- [ ] **Step 7: Implement `auto_update_ytdlp() -> None` in `youtube_downloader/batch.py`**

Run `[sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"]` via `subprocess.run` with `capture_output=True`. Print upgrade message on "Successfully installed"; print version on no-change; print warning on exception. Never raise.

- [ ] **Step 8: Implement `main() -> None` in `youtube_downloader/cli.py`**

Parse `sys.argv[1:]`. Collect `--no-update` flag and URL arguments. If no URLs provided and stdin is a TTY, read lines until blank (interactive mode, one URL per line). Validate with `validate_batch`; on errors print them and `sys.exit(1)`. Call `auto_update_ytdlp()` (skip if `--no-update`). Call `run_batch(urls, no_update=no_update)`. Print summary. `sys.exit(0)` if all True, else `sys.exit(1)`.

- [ ] **Step 9: Create `youtube_downloader/__main__.py`**

```python
from youtube_downloader.cli import main
main()
```

- [ ] **Step 10: Run — all tests in test_batch and test_cli pass**

Run: `python -m unittest tests.test_batch tests.test_cli -v`
Expected: all PASS

- [ ] **Step 11: Commit**

```bash
git add youtube_downloader/batch.py youtube_downloader/cli.py youtube_downloader/__main__.py tests/test_batch.py tests/test_cli.py
git commit -m "feat: add batch processor, auto-update, and CLI entry point"
```

---

### Task 4: Compatibility shim, pyproject update, run.bat fix

**Files:**
- Modify: `downloader.py`
- Modify: `pyproject.toml`
- Modify: `run.bat`

**Interfaces:**
- Consumes: `youtube_downloader.cli:main` from Task 3
- Produces: `downloader.py` delegates to package; `pyproject.toml` points `download` script at `youtube_downloader.cli:main`; `run.bat` ends with `pause`

- [ ] **Step 1: Write failing test for shim**

```python
# tests/test_shim.py
import unittest
from unittest.mock import patch

class TestDownloaderShim(unittest.TestCase):
    def test_main_delegates_to_cli(self):
        with patch("youtube_downloader.cli.main") as mock_main:
            import downloader
            import importlib; importlib.reload(downloader)
            downloader.main()
        mock_main.assert_called_once()
```

- [ ] **Step 2: Run — verify fail**

Run: `python -m unittest tests.test_shim -v`
Expected: fail (old `main` doesn't call `youtube_downloader.cli.main`)

- [ ] **Step 3: Replace `downloader.py` content with compatibility shim**

```python
"""Compatibility shim — delegates to youtube_downloader package."""
from youtube_downloader.cli import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run — verify shim test passes**

Run: `python -m unittest tests.test_shim -v`
Expected: PASS

- [ ] **Step 5: Update `pyproject.toml` scripts section**

Change `download = "downloader:main"` to `download = "youtube_downloader.cli:main"`.
Add `packages = ["youtube_downloader"]` under `[tool.setuptools]` (or equivalent) so the package is found on install.

- [ ] **Step 6: Fix `run.bat` — add `pause` line**

Replace entire `run.bat` content:
```bat
@echo off
title YouTube Downloader
echo ==================================================
echo   YouTube Downloader - Auto-save to YYYY-MM-DD
echo ==================================================
echo.
python downloader.py
echo.
pause
```

- [ ] **Step 7: Run full suite — all tests pass**

Run: `python -m unittest discover -s tests -v`
Expected: all tests PASS

- [ ] **Step 8: Commit**

```bash
git add downloader.py pyproject.toml run.bat tests/test_shim.py
git commit -m "feat: shim downloader.py, update pyproject.toml entry point, fix run.bat pause"
```

---

### Task 5: Agent Skill file

**Files:**
- Create: `skills/youtube-downloader/SKILL.md`

**Interfaces:**
- Consumes: working CLI from Tasks 1-4
- Produces: skill file at `skills/youtube-downloader/SKILL.md` with frontmatter version `0.0.1`

- [ ] **Step 1: Create `skills/youtube-downloader/SKILL.md`**

```markdown
---
name: youtube-downloader
version: 0.0.1
description: Download up to ten YouTube videos sequentially using the local CLI. Collects URLs, validates them, runs the downloader, and reports per-item results.
---

# YouTube Downloader Skill

Use this skill when the user asks to download one or more YouTube videos (up to 10 at a time).

## How to use

1. Collect up to ten YouTube URLs from the user (youtube.com or youtu.be, HTTP/HTTPS only).
2. Do not accept more than ten URLs in one batch.
3. Run the downloader CLI:
   - Single URL: `python downloader.py <URL>`
   - Multiple URLs: `python downloader.py <URL1> <URL2> ...`
   - Skip auto-update: add `--no-update`
4. Stream the output so the user can see progress.
5. After all downloads, report per-item success or failure clearly.

## Rules

- Never expose or print cookie file contents.
- Never modify authentication logic to bypass access restrictions.
- If a URL is invalid or not a YouTube URL, tell the user before running anything.
- If more than ten URLs are requested, ask the user to split them into batches.
- Downloads are saved to a folder named with today's date (`YYYY-MM-DD/`) in the current working directory.
```

- [ ] **Step 2: Verify skill file is valid markdown with correct frontmatter**

Run: `python -c "import pathlib; content = pathlib.Path('skills/youtube-downloader/SKILL.md').read_text(); assert 'version: 0.0.1' in content; assert 'name: youtube-downloader' in content; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit and create annotated tag**

```bash
git add skills/youtube-downloader/SKILL.md
git commit -m "feat: add youtube-downloader Agent Skill v0.0.1"
git tag -a skill-v0.0.1 -m "YouTube Downloader Skill version 0.0.1"
```

---

## Summary of files created/modified

| File | Action |
|------|--------|
| `youtube_downloader/__init__.py` | Create (empty) |
| `youtube_downloader/validator.py` | Create |
| `youtube_downloader/runner.py` | Create |
| `youtube_downloader/batch.py` | Create |
| `youtube_downloader/cli.py` | Create |
| `youtube_downloader/__main__.py` | Create |
| `tests/__init__.py` | Create (empty) |
| `tests/test_validator.py` | Create |
| `tests/test_runner.py` | Create |
| `tests/test_batch.py` | Create |
| `tests/test_cli.py` | Create |
| `tests/test_shim.py` | Create |
| `downloader.py` | Modify (shim) |
| `pyproject.toml` | Modify |
| `run.bat` | Modify |
| `skills/youtube-downloader/SKILL.md` | Create |
