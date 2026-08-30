# Design Spec: Usability Improvements & Date-Based Directory Exports

This design document outlines the enhancements for the YouTube Downloader project to improve usability, introduce automatic daily folder exports, and support easier execution on Windows.

## 1. Overview
The goal is to make downloading YouTube videos easier for Windows users and group downloads automatically into folders categorized by the download date (`YYYY-MM-DD`).

## 2. Requirements
- **Directory Structure:** Saved videos must be placed in a directory formatted as `YYYY-MM-DD` based on the download date, containing the video file (e.g. `2026-07-01/video_name.mp4`).
- **Command Line Arguments:** Users should be able to pass the video URL as a command-line argument directly (e.g., `python downloader.py <URL>`).
- **Interactive Fallback:** If no argument is passed, prompt the user for the URL via standard input as usual.
- **Easy Windows Execution:** Provide a `run.bat` helper script so Windows users can double-click to run the script interactively without opening a terminal beforehand, and prevent the terminal window from closing instantly upon completion.

## 3. Proposed Changes

### A. Modifying `downloader.py`
We will update `downloader.py` to:
1. Fetch the current date (`YYYY-MM-DD`) using Python's `datetime`.
2. Construct the output template path `f"{download_date}/%(title)s.%(ext)s"`.
3. Support running with CLI arguments via `sys.argv`.

### B. Creating `run.bat`
Create a batch file `run.bat` at the repository root:
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

## 4. Verification Plan
- **Verification of Directory Creation:** Run the downloader with a test video, verify it creates a folder named with today's date, and saves the MP4 inside it.
- **Verification of CLI Arguments:** Run `python downloader.py <URL>` to ensure it downloads without prompting.
- **Verification of run.bat:** Double-click or run `run.bat` to verify it prompts for the URL and pauses at the end.
