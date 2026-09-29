"""Subprocess runner — wraps the yt-dlp CLI to download a single YouTube URL."""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime


def build_command(
    url: str,
    no_update: bool = False,
    use_browser_cookies: bool = True,
    output_dir: str | None = None,
) -> list[str]:
    """Build the argv list to download *url* via yt-dlp.

    The command uses ``sys.executable -m yt_dlp`` so the same interpreter and
    virtual-environment that runs this code also runs yt-dlp.  ``shell=False``
    is enforced by never joining into a single string; the URL is always the
    last positional argument and is never interpolated into a shell string.
    """
    target_dir = output_dir or datetime.now().strftime("%Y-%m-%d")
    cmd: list[str] = [
        sys.executable, "-m", "yt_dlp",
        "--no-playlist",
        "--format", "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "--merge-output-format", "mp4",
        "-o", f"{target_dir}/%(title)s.%(ext)s",
        "--retries", "5",
        "--fragment-retries", "5",
        "--file-access-retries", "5",
    ]
    if os.path.exists("cookies.txt"):
        cmd += ["--cookies", "cookies.txt"]
    elif use_browser_cookies:
        cmd += ["--cookies-from-browser", "edge"]
    if no_update:
        cmd.append("--no-update")
    cmd.append(url)
    return cmd


_browser_cookies_supported: bool = True


def run_download(url: str, no_update: bool = False, output_dir: str | None = None) -> bool:
    """Run yt-dlp for *url* and return True if it exits with code 0.

    stdout and stderr are not captured so the user sees yt-dlp's progress
    output in real time. If the initial run fails and browser cookies were used,
    retries once without browser cookies as a fallback and remembers the failure
    for the rest of the batch.
    """
    global _browser_cookies_supported

    proc = subprocess.run(
        build_command(
            url,
            no_update=no_update,
            use_browser_cookies=_browser_cookies_supported,
            output_dir=output_dir,
        ),
        shell=False,
    )
    if proc.returncode == 0:
        return True

    if not os.path.exists("cookies.txt") and _browser_cookies_supported:
        _browser_cookies_supported = False
        print("  [INFO] Retrying without browser cookies...")
        proc_retry = subprocess.run(
            build_command(url, no_update=no_update, use_browser_cookies=False, output_dir=output_dir),
            shell=False,
        )
        return proc_retry.returncode == 0

    return False
