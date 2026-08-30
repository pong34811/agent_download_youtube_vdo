# YouTube Downloader Usability Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enhance the YouTube Downloader script to output downloaded videos into a `YYYY-MM-DD` folder based on the download date, support command line arguments for URLs, and create a `run.bat` helper script for easy execution on Windows.

**Architecture:** 
- Obtain the current date inside `downloader.py` using Python's standard `datetime` module and format it as `YYYY-MM-DD`.
- Configure `yt_dlp`'s `outtmpl` parameter to export files inside a directory named with the current date.
- Modify `main()` to check `sys.argv` for an input URL before prompting via `input()`.
- Create a `run.bat` file in the root workspace to run the script and pause upon completion.

**Tech Stack:** Python 3.9+, yt-dlp

## Global Constraints
- Saved videos must be placed in a directory formatted as `YYYY-MM-DD` based on the download date.
- Users should be able to pass the video URL as a command-line argument directly.
- Provide a `run.bat` helper script.

---

### Task 1: Update `downloader.py` with date folder and CLI argument support

**Files:**
- Modify: `downloader.py`

**Interfaces:**
- Consumes: None
- Produces: Updates script behavior to support CLI args and saves to `YYYY-MM-DD` subdirectories.

- [ ] **Step 1: Modify `downloader.py` to add date formatting and argument parsing**

In `downloader.py`, import `sys` and `datetime`. Update `download_video` and `main` functions to the following:

```python
import os
import sys
from datetime import datetime
import yt_dlp


def download_video(url: str) -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    ydl_opts = {
        "format": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]",
        "merge_output_format": "mp4",
        "outtmpl": f"{today}/%(title)s.%(ext)s",
        "retries": 50,
        "fragment_retries": 50,
        "concurrent_fragment_downloads": 5,
        "continuedl": True,
    }
    if os.path.exists("cookies.txt"):
        ydl_opts["cookiefile"] = "cookies.txt"
    else:
        ydl_opts["cookiesfrombrowser"] = ("edge",)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def main() -> None:
    if len(sys.argv) > 1:
        url = sys.argv[1].strip()
    else:
        url = input("กรุณาวาง URL: ").strip().removeprefix("\ufeff")
        
    if not url:
        print("URL ว่างเปล่า กรุณาวาง URL อีกครั้ง")
        return

    print("กำลังดาวน์โหลด...")
    try:
        download_video(url)
        print("✅ ดาวน์โหลดเสร็จแล้ว!")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify code runs interactively without arguments**

Run the following command and verify it asks for input:
Run: `python downloader.py`
Expected output: Prompts `กรุณาวาง URL: `

Press Ctrl+C or enter an empty line to exit.

- [ ] **Step 3: Verify code runs with command-line argument**

Run with a sample/invalid URL to verify it tries to download without prompting:
Run: `python downloader.py https://www.youtube.com/watch?v=dQw4w9WgXcQ`
Expected: Tries to download and does not prompt for URL.

- [ ] **Step 4: Commit changes**

Run:
```bash
git add downloader.py
git commit -m "feat: add date-based folder output and CLI argument support"
```

---

### Task 2: Create Windows Helper Script `run.bat`

**Files:**
- Create: `run.bat`

**Interfaces:**
- Consumes: `downloader.py` behavior.
- Produces: `run.bat` executable on Windows.

- [ ] **Step 1: Write `run.bat`**

Create `run.bat` with the following content:

```cmd
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

- [ ] **Step 2: Verify `run.bat` execution**

Run the batch file from terminal or double-click it.
Run: `.\run.bat`
Expected: Prints headers, prompts `กรุณาวาง URL: `, and pauses upon input submission or cancellation.

- [ ] **Step 3: Commit changes**

Run:
```bash
git add run.bat
git commit -m "feat: add run.bat helper script for easy execution"
```
