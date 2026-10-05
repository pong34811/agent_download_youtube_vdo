# GitHub Release v0.0.4

## Description
Update youtube-downloader skill to v0.0.4 with batch limit 22, playlist expansion, and --output-dir support.

## Changes
- Update youtube-downloader skill to v0.0.4
- Batch limit increased to 22 unique URLs
- Playlist expansion before validation and limit
- Add --output-dir support in CLI and skill docs
- Update AGENTS.md for new options
- Add PROJECT_SNAPSHOT.md

## Files changed
- skills/youtube-downloader/SKILL.md
- AGENTS.md
- PROJECT_SNAPSHOT.md
- youtube_downloader/runner.py
- tests/test_runner.py
- RELEASE_NOTES.md

## Assets
No binary assets. Source only.

## Installation
```bash
python -m pip install -e .
python downloader.py --help
```

Tag: v0.0.4
