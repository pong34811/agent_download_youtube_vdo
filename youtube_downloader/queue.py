"""Download queue persistence module for tracking and resuming batch downloads."""
from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import tempfile

QUEUE_FILENAME = ".download_queue.json"


def get_queue_path() -> Path:
    """Return the Path to the download queue file in current working directory."""
    return Path(QUEUE_FILENAME)


def load_queue() -> dict | None:
    """Load and validate the download queue from disk.

    Returns the queue dict if valid, or None if missing or corrupt.
    """
    path = get_queue_path()
    if not path.is_file():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            print("[WARNING] Existing queue file format is invalid; ignoring.")
            return None
        if "items" not in data or "output_dir" not in data:
            print("[WARNING] Existing queue file schema is invalid; ignoring.")
            return None
        return data
    except Exception as exc:
        print(f"[WARNING] Could not read existing queue file ({exc}); ignoring.")
        return None


def save_queue(queue_data: dict) -> None:
    """Safely persist the queue dictionary to disk using an atomic replace."""
    path = get_queue_path()
    parent_dir = path.parent
    try:
        # Atomic write via temporary file
        with tempfile.NamedTemporaryFile("w", dir=parent_dir, delete=False, encoding="utf-8") as tf:
            json.dump(queue_data, tf, indent=2)
            temp_name = tf.name
        os.replace(temp_name, path)
    except Exception as exc:
        print(f"[WARNING] Failed to save download queue: {exc}")


def clear_queue() -> None:
    """Remove the queue file if it exists."""
    path = get_queue_path()
    try:
        if path.exists():
            path.unlink()
    except Exception as exc:
        print(f"[WARNING] Failed to remove download queue file: {exc}")


def create_queue(urls: list[str], output_dir: str | None = None) -> dict:
    """Initialize a new queue dictionary from a list of URLs."""
    if not output_dir:
        output_dir = datetime.now().strftime("%Y-%m-%d")

    return {
        "created_at": datetime.now().isoformat(),
        "output_dir": output_dir,
        "items": [{"url": url, "status": "pending"} for url in urls],
    }


def get_pending_urls(queue_data: dict) -> list[str]:
    """Return a list of URLs that are pending or failed."""
    items = queue_data.get("items", [])
    return [
        item["url"]
        for item in items
        if item.get("status") in ("pending", "failed")
    ]


def update_item_status(queue_data: dict, url: str, status: str) -> None:
    """Update status of a URL in the queue data and save to disk."""
    for item in queue_data.get("items", []):
        if item.get("url") == url:
            item["status"] = status
            break
    save_queue(queue_data)
