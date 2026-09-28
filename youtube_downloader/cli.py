"""CLI entry point for the YouTube downloader package."""
from __future__ import annotations

import sys

from youtube_downloader.batch import auto_update_ytdlp, run_batch
from youtube_downloader.validator import validate_batch


def _print_summary(results: dict[str, bool]) -> None:
    """Print a per-item summary and return overall success flag."""
    total = len(results)
    passed = sum(1 for ok in results.values() if ok)
    print(f"\n--- Summary: {passed}/{total} succeeded ---")
    for url, ok in results.items():
        status = "[OK]" if ok else "[FAIL]"
        print(f"  {status} {url}")


def main() -> None:
    """Parse CLI arguments, validate the batch, and run downloads."""
    raw_args = sys.argv[1:]

    # Extract flags
    no_update = "--no-update" in raw_args
    url_args = [a for a in raw_args if not a.startswith("--")]

    # Interactive mode: no URLs supplied on command line
    if not url_args:
        print("YouTube Downloader — paste one URL per line, blank line to start")
        print("(Ctrl+C to cancel)")
        try:
            while True:
                line = input("> ").strip().removeprefix("\ufeff")
                if not line:
                    break
                url_args.append(line)
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
            sys.exit(1)

    urls, errors = validate_batch(url_args)

    if errors:
        print("Input rejected:")
        for msg in errors:
            print(f"  - {msg}")
        sys.exit(1)

    if not no_update:
        auto_update_ytdlp()

    results = run_batch(urls, no_update=no_update)
    _print_summary(results)

    if all(results.values()):
        sys.exit(0)
    else:
        sys.exit(1)
