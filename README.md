# YouTube Downloader

A Python command-line tool that downloads individual YouTube videos with `yt-dlp`.

## Requirements

- Python 3.10 or newer
- Internet access
- `yt-dlp` (installed by the project setup below)

## Install

From the repository root:

```bash
python -m pip install -e .
```

For development/testing, no extra test dependencies are required.

## Use

Download a single video:

```bash
python downloader.py https://www.youtube.com/watch?v=VIDEO_ID
```

Download a batch (up to 10 unique URLs):

```bash
python downloader.py https://youtu.be/VIDEO_ID_1 https://youtu.be/VIDEO_ID_2
```

Interactive input (one URL per line, blank line to start):

```bash
python downloader.py
```

```bash
python downloader.py https://www.youtube.com/playlist?list=PLD1wi10rj474
```

Skip the automatic `yt-dlp` upgrade for this invocation:

```bash
python downloader.py --no-update https://youtu.be/VIDEO_ID
```

Resume an interrupted batch:

```bash
python downloader.py --resume
```

If a new invocation finds an unfinished queue, it asks whether to resume it first. Choosing “no” clears that saved queue before starting the new input.

An installed console command is also available after installation:

```bash
download https://youtu.be/VIDEO_ID
```

## Behavior

- Accepts HTTP(S) URLs on `youtube.com`, its subdomains, and `youtu.be`; duplicate URLs are removed; playlist URLs expand to their individual videos before the 10-item limit.
- Processes URLs sequentially, selecting the best available video up to 1080p and merging output to MP4.
- Writes downloads into a `YYYY-MM-DD/` folder relative to the current working directory.
- Attempts to upgrade `yt-dlp` once per invocation unless `--no-update` is used. An upgrade failure is reported as a warning; the download proceeds.
- Uses `cookies.txt` from the current working directory if present. Otherwise it attempts Microsoft Edge browser cookies and, if that attempt fails, retries without browser cookies.
- Saves queue state in `.download_queue.json` in the current working directory. Failed items remain eligible for resume; a successful complete batch clears the queue.
- Exit code `0` means all requested downloads succeeded (or there was nothing to resume); `1` indicates invalid input, cancellation, or one or more failed downloads.

Only download content you are authorized to access. Respect copyright and YouTube's terms. Never share `cookies.txt` or expose cookie contents.

## Tests

Run the standard-library test suite from the repository root:

```bash
python -m unittest discover -v
```
