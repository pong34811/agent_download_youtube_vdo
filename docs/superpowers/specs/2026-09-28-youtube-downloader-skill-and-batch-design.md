# Design Spec: YouTube Downloader Skill and Sequential Batch Downloads

**Status:** Written for user review; implementation has not started.

## 1. Goal

Add a reusable YouTube-download Agent Skill and improve the existing Windows-focused Python CLI so a user or agent can submit up to ten video URLs in one batch. The batch runs sequentially, reports each result, and continues after an individual failure.

The tool is for videos the user owns or is otherwise authorized to download and can access. It will not add methods to bypass authentication, access controls, or platform restrictions.

## 2. Current Project Analysis

- `downloader.py` currently combines CLI handling, `yt-dlp` configuration, package auto-update, cookies selection, and download/retry behavior. It handles one URL at a time.
- Downloads are configured for up to 1080p, merged to MP4, and placed under a date-named directory.
- The current working-tree change adds alternate YouTube player-client retries, unbounded retries, disabled TLS certificate checks, and the `ejs:github` remote component. Those changes are not committed.
- `pyproject.toml` declares `yt-dlp`, a `download` console script, app version `0.1.0`, and Python `>=3.9`; the current edited code uses `list[str] | None`, which requires Python 3.10 at runtime unless annotations are postponed.
- `run.bat` starts the interactive CLI but does not pause after it exits. `get_cookies.ps1` only checks whether the Edge cookie database exists; it does not export cookies. `.gitignore` excludes `cookies.txt`.
- No automated tests or linter configuration exist. The active Python reported is 3.14.7, but `python -m pip show yt-dlp` returned no package information. The active interpreter and `pip` are known to differ in this environment.
- Git is on `master`, has pre-existing edits to `downloader.py` and an untracked `IDEA.md`, and has no configured remote.

## 3. Approved Architecture

Use a small Python package with the existing script as a compatibility entry point, and invoke `yt-dlp` as a subprocess rather than using its Python API.

Proposed files:

- `youtube_downloader/cli.py`: parse arguments, collect interactive input, validate the batch, and choose the process exit status.
- `youtube_downloader/batch.py`: deduplicate URLs, run items in order, and aggregate per-item results.
- `youtube_downloader/runner.py`: build and execute one `sys.executable -m yt_dlp ...` command per URL.
- `youtube_downloader/__init__.py` and `youtube_downloader/__main__.py`: package initialization and `python -m youtube_downloader` entry point.
- `downloader.py`: compatibility shim that delegates to the package CLI.
- `pyproject.toml`: point the `download` script at `youtube_downloader.cli:main` and configure package building as needed.
- `tests/`: standard-library `unittest` coverage; no new test dependency is required.
- `skills/youtube-downloader/SKILL.md`: canonical, versioned-in-repository skill source; install the same content into the active Hermes profile after it passes skill checks.

The subprocess command is built as an argument list and uses `shell=False`. Its stdout/stderr remain visible so users can see `yt-dlp` progress. A failed process becomes a failed item result; the batch loop continues.

## 4. Batch Interface and Behavior

- `python downloader.py URL` remains valid for one URL.
- `python downloader.py URL1 URL2 ... URL10` accepts up to ten positional URLs.
- With no URL arguments, interactive mode accepts one URL per line; a blank line finishes input and starts the batch.
- Accept only HTTP(S) URLs on `youtube.com` (including its subdomains) or `youtu.be`.
- Validate the complete input before starting any network operation. More than ten entries or any invalid URL rejects the entire batch.
- Remove exact duplicate URLs and report that they were skipped.
- Process the remaining URLs sequentially in input order. A failed clip does not prevent later clips from running.
- Prevent playlist expansion so one input URL cannot unexpectedly turn into an unbounded playlist download.
- Preserve the date-based output directory, up-to-1080p video/audio selection, and MP4 merge behavior.
- Print a final success/failure summary. Return zero only when every requested unique video succeeds; return nonzero for invalid input or any failed item.

## 5. Download Reliability and Security

- Keep the current automatic `yt-dlp` upgrade behavior, but run it once per CLI invocation before processing the batch; do not rerun it per URL. Add `--no-update` so users can opt out. If the update fails, warn and attempt to use the installed version.
- Use finite retry limits (initial proposal: five attempts for whole downloads, fragments, and file access) so a blocked item cannot hang the queue indefinitely.
- Keep TLS certificate verification enabled; remove the `--no-check-certificates` behavior.
- Do not implement alternate player-client switching to work around 401/403 or sign-in requirements. Report the failure and rely only on normal, user-authorized cookies/browser authentication.
- Preserve the existing `cookies.txt`-first, Edge-browser fallback, without reading or printing secret cookie contents. Keep `cookies.txt` ignored by Git.
- Preserve the `ejs:github` remote component only if the installed `yt-dlp` CLI explicitly supports it; verify the option against the installed CLI before implementation is considered complete. It must not be used to circumvent access restrictions.
- Use the installed interpreter for both update and download commands (`sys.executable`) and never interpolate URLs into a shell command.
- Add a `pause` after the `run.bat` invocation so the final status remains visible in the Windows console.

## 6. Skill Design and Installation

- Skill name: `youtube-downloader`; skill version: `0.0.1`.
- Store the canonical skill at `skills/youtube-downloader/SKILL.md` in this repository.
- Install an identical skill into the active Hermes profile using Hermes' supported skill-management path. Do not modify another profile.
- The skill instructs the agent to collect up to ten URLs, run the local CLI with safe argument handling, explain per-item results, and avoid exposing cookies or bypassing access restrictions.
- Test the skill as a usage/reference skill with a baseline task scenario before authoring it and the same application scenario after installation. Verify it can be discovered and loaded in Hermes.

## 7. Verification Plan

Use the standard library test runner:

```bash
python -m unittest discover -s tests -v
```

Tests must cover:

- URL scheme/host validation, empty input, duplicate handling, and the ten-URL limit.
- Full-batch preflight rejection before invoking the runner.
- Sequential call order and continuation after a subprocess failure.
- Command construction for output format, date output path, cookies, finite retries, TLS verification, and playlist suppression.
- `--no-update`, update-once behavior, result summaries, and exit codes.
- The legacy `python downloader.py URL` entry point and installed `download` entry point.
- Skill discovery/load and correct application to an up-to-ten-URL request.

Run all tests without real YouTube requests or cookies. Confirm the installed dependency using `python -m yt_dlp --version`. No real-download smoke test is planned because the user has not supplied a video URL for it.

After tests pass, request an isolated Hermes subagent code review (Ponytail was not available in this environment), address valid findings with tests, and rerun the full suite.

## 8. Release Plan and Constraints

- Set the Skill frontmatter version to `0.0.1` and create the annotated Git tag `skill-v0.0.1`; keep the application version in `pyproject.toml` at `0.1.0`.
- Create the tag and push only after the full test suite and review are clean.
- The repository currently has no remote, so push is blocked until a remote is configured.
- Preserve `IDEA.md` as untracked and do not include it in the release. The pre-existing `downloader.py` edits are in scope for review; no unrelated existing changes should be staged.
- Do not commit or push at the design-review gate. The implementation plan and release remain blocked until the user approves this written spec.

## 9. Scope Exclusions

- No real YouTube download during automated tests.
- No playlist expansion, parallel clip downloading, database index, caption/metadata archive, or video library search in this release.
- No automatic retry strategy that switches player clients to evade access restrictions.
- No application-version bump; this release tag versions the Skill only.
