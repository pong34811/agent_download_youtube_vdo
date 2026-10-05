"""CLI entry point for the YouTube downloader package."""
from __future__ import annotations

import sys

from youtube_downloader.batch import auto_update_ytdlp, run_batch
from youtube_downloader.queue import (
    clear_queue,
    create_queue,
    get_pending_urls,
    load_queue,
)
from youtube_downloader.validator import validate_batch
from youtube_downloader.playlist import resolve_playlist, is_playlist_url


def _expand_urls(urls: list[str]) -> list[str]:
    """Resolve any playlist URLs into individual video URLs.

    Playlist URLs are expanded *before* validation and queue creation so
    that the queue, deduplication, the 10-item batch limit, and resume all
    operate at the per-video level.  A resolution failure rejects the whole
    batch with a clear message.
    """
    expanded: list[str] = []
    for url in urls:
        if is_playlist_url(url):
            try:
                expanded.extend(resolve_playlist(url))
            except RuntimeError as exc:
                print(f"[ERROR] Could not resolve playlist {url}: {exc}")
                raise SystemExit(1)
        else:
            expanded.append(url)
    return expanded


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
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(errors="replace")
            sys.stderr.reconfigure(errors="replace")
        except Exception:
            pass

    raw_args = sys.argv[1:]

    # Extract flags
    no_update = "--no-update" in raw_args
    resume = "--resume" in raw_args
    url_args = [a for a in raw_args if not a.startswith("--")]

    # 1. Explicit --resume flow
    if resume:
        queue_data = load_queue()
        if not queue_data:
            print("[INFO] No unfinished download session found.")
            sys.exit(0)

        pending_urls = get_pending_urls(queue_data)
        if not pending_urls:
            print("[INFO] No unfinished download session found.")
            clear_queue()
            sys.exit(0)

        if not no_update:
            auto_update_ytdlp()

        output_dir = queue_data.get("output_dir")
        results = run_batch(
            pending_urls,
            no_update=no_update,
            queue_data=queue_data,
            output_dir=output_dir,
        )
        _print_summary(results)
        sys.exit(0 if all(results.values()) else 1)

    # 2. Check for unfinished queue before starting a new batch
    existing_queue = load_queue()
    if existing_queue:
        pending_urls = get_pending_urls(existing_queue)
        if pending_urls:
            created = existing_queue.get("created_at", "earlier session")
            count = len(pending_urls)
            try:
                ans = input(
                    f"Found unfinished download session from {created} ({count} items pending). Resume? [Y/n]: "
                ).strip().lower()
            except (KeyboardInterrupt, EOFError):
                print("\nCancelled.")
                sys.exit(0)

            if ans in ("", "y", "yes"):
                if not no_update:
                    auto_update_ytdlp()
                output_dir = existing_queue.get("output_dir")
                results = run_batch(
                    pending_urls,
                    no_update=no_update,
                    queue_data=existing_queue,
                    output_dir=output_dir,
                )
                _print_summary(results)
                sys.exit(0 if all(results.values()) else 1)
            else:
                clear_queue()
        else:
            clear_queue()

    # 3. Interactive mode: no URLs supplied on command line
    if not url_args:
        print("YouTube Downloader - paste one URL per line, blank line to start")
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

    urls = _expand_urls(urls)
    urls, errors = validate_batch(urls)

    if errors:
        print("Input rejected:")
        for msg in errors:
            print(f"  - {msg}")
        sys.exit(1)

    if not no_update:
        auto_update_ytdlp()

    queue_data = create_queue(urls)
    output_dir = queue_data.get("output_dir")
    results = run_batch(
        urls,
        no_update=no_update,
        queue_data=queue_data,
        output_dir=output_dir,
    )
    _print_summary(results)

    if all(results.values()):
        sys.exit(0)
    else:
        sys.exit(1)
