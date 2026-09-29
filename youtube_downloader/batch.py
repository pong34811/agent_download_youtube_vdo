"""Batch processor and auto-update helper for the YouTube downloader."""
from __future__ import annotations

import subprocess
import sys

from youtube_downloader.queue import clear_queue, update_item_status
from youtube_downloader.runner import run_download


def auto_update_ytdlp() -> None:
    """Upgrade yt-dlp via pip once per invocation.

    Prints the result to stdout.  Never raises — a failed update is reported
    as a warning and the run continues with the installed version.
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if "Successfully installed" in result.stdout:
            # Try to report new version without a hard import dependency
            try:
                import importlib
                import yt_dlp  # noqa: F401
                import yt_dlp.version as _v
                importlib.reload(_v)
                print(f"[INFO] yt-dlp updated to version {_v.__version__}")
            except Exception:
                print("[INFO] yt-dlp updated successfully")
        else:
            print("[INFO] yt-dlp is up to date")
    except Exception as exc:
        print(f"[WARNING] Could not update yt-dlp: {exc}")


def run_batch(
    urls: list[str],
    no_update: bool = False,
    queue_data: dict | None = None,
    output_dir: str | None = None,
) -> dict[str, bool]:
    """Download each URL sequentially.  Returns a mapping of url → success.

    A failed individual download is logged and the batch continues.
    If queue_data is provided, progress is saved to disk and KeyboardInterrupt
    is caught gracefully.
    """
    if output_dir is None and queue_data is not None:
        output_dir = queue_data.get("output_dir")

    results: dict[str, bool] = {}
    total = len(urls)
    interrupted = False

    for i, url in enumerate(urls, start=1):
        print(f"\n[{i}/{total}] {url}")
        try:
            if output_dir is not None:
                success = run_download(url, no_update=no_update, output_dir=output_dir)
            else:
                success = run_download(url, no_update=no_update)
            results[url] = success
            if queue_data:
                status = "completed" if success else "failed"
                update_item_status(queue_data, url, status)

            if success:
                print("  [OK] Download complete")
            else:
                print("  [FAIL] Download failed")
        except KeyboardInterrupt:
            interrupted = True
            if queue_data:
                update_item_status(queue_data, url, "pending")
            print("\n\n[PAUSED] Download paused safely.")
            print("To resume later, run: python downloader.py --resume")
            break

    if queue_data and not interrupted:
        all_completed = all(
            item.get("status") == "completed"
            for item in queue_data.get("items", [])
        )
        if all_completed:
            clear_queue()

    return results
