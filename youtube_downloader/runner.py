"""Subprocess runner — wraps the yt-dlp CLI to download a single YouTube URL."""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime


def build_command(url: str, no_update: bool = False) -> list[str]:
    """Build the argv list to download *url* via yt-dlp.

    The command uses ``sys.executable -m yt_dlp`` so the same interpreter and
    virtual-environment that runs this code also runs yt-dlp.  ``shell=False``
    is enforced by never joining into a single string; the URL is always the
    last positional argument and is never interpolated into a shell string.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    cmd: list[str] = [
        sys.executable, "-m", "yt_dlp",
        "--no-playlist",
        "--format", "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "--merge-output-format", "mp4",
        "-o", f"{today}/%(title)s.%(ext)s",
        "--retries", "5",
        "--fragment-retries", "5",
        "--file-access-retries", "5",
    ]
    if os.path.exists("cookies.txt"):
        cmd += ["--cookies", "cookies.txt"]
    else:
        cmd += ["--cookies-from-browser", "edge"]
    if no_update:
        cmd.append("--no-update")
    cmd.append(url)
    return cmd


def run_download(url: str, no_update: bool = False) -> bool:
    """Run yt-dlp for *url* and return True if it exits with code 0.

    stdout and stderr are not captured so the user sees yt-dlp's progress
    output in real time.
    """
    proc = subprocess.run(build_command(url, no_update=no_update), shell=False)
    return proc.returncode == 0
