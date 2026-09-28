"""Compatibility shim — delegates to the youtube_downloader package.

This file is kept for backwards compatibility: ``python downloader.py``
continues to work after the code moved into the package.
"""
from youtube_downloader.cli import main

if __name__ == "__main__":
    main()
