"""Batch processor and auto-update helper for the YouTube downloader."""
from __future__ import annotations

import subprocess
import sys

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


def run_batch(urls: list[str], no_update: bool = False) -> dict[str, bool]:
    """Download each URL sequentially.  Returns a mapping of url → success.

    A failed individual download is logged and the batch continues.
    """
    results: dict[str, bool] = {}
    total = len(urls)
    for i, url in enumerate(urls, start=1):
        print(f"\n[{i}/{total}] {url}")
        success = run_download(url, no_update=no_update)
        results[url] = success
        if success:
            print(f"  [OK] Download complete")
        else:
            print(f"  [FAIL] Download failed")
    return results
