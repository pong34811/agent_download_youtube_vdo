"""Unit tests for the download queue persistence module."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from youtube_downloader.queue import (
    clear_queue,
    create_queue,
    get_pending_urls,
    get_queue_path,
    load_queue,
    save_queue,
    update_item_status,
)


class TestQueuePersistence(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.queue_file = Path(self.temp_dir.name) / ".download_queue.json"
        self.patcher = patch("youtube_downloader.queue.get_queue_path", return_value=self.queue_file)
        self.patcher.start()

    def tearDown(self) -> None:
        self.patcher.stop()
        self.temp_dir.cleanup()

    def test_create_and_save_queue(self) -> None:
        urls = ["https://www.youtube.com/watch?v=aaa", "https://www.youtube.com/watch?v=bbb"]
        queue = create_queue(urls, output_dir="2026-09-29")
        self.assertEqual(queue["output_dir"], "2026-09-29")
        self.assertIn("created_at", queue)
        self.assertEqual(len(queue["items"]), 2)
        self.assertEqual(queue["items"][0], {"url": urls[0], "status": "pending"})
        self.assertEqual(queue["items"][1], {"url": urls[1], "status": "pending"})

        save_queue(queue)
        self.assertTrue(self.queue_file.exists())

        loaded = load_queue()
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded["output_dir"], "2026-09-29")
        self.assertEqual(len(loaded["items"]), 2)

    def test_create_queue_defaults_output_dir_to_date(self) -> None:
        urls = ["https://www.youtube.com/watch?v=aaa"]
        queue = create_queue(urls)
        self.assertTrue(len(queue["output_dir"]) == 10)  # YYYY-MM-DD
        self.assertTrue(queue["output_dir"].count("-") == 2)

    def test_load_queue_when_missing(self) -> None:
        self.assertFalse(self.queue_file.exists())
        loaded = load_queue()
        self.assertIsNone(loaded)

    def test_load_queue_corrupt_json(self) -> None:
        self.queue_file.write_text("{ broken json ...", encoding="utf-8")
        loaded = load_queue()
        self.assertIsNone(loaded)

    def test_clear_queue(self) -> None:
        self.queue_file.write_text("{}", encoding="utf-8")
        self.assertTrue(self.queue_file.exists())
        clear_queue()
        self.assertFalse(self.queue_file.exists())
        # Clearing when missing should not raise
        clear_queue()

    def test_get_pending_urls(self) -> None:
        queue = {
            "created_at": "2026-09-29T23:00:00",
            "output_dir": "2026-09-29",
            "items": [
                {"url": "https://www.youtube.com/watch?v=url1", "status": "completed"},
                {"url": "https://www.youtube.com/watch?v=url2", "status": "pending"},
                {"url": "https://www.youtube.com/watch?v=url3", "status": "failed"},
            ],
        }
        pending = get_pending_urls(queue)
        self.assertEqual(pending, [
            "https://www.youtube.com/watch?v=url2",
            "https://www.youtube.com/watch?v=url3",
        ])

    def test_update_item_status(self) -> None:
        urls = ["https://www.youtube.com/watch?v=url1", "https://www.youtube.com/watch?v=url2"]
        queue = create_queue(urls, output_dir="2026-09-29")
        save_queue(queue)

        update_item_status(queue, urls[0], "completed")
        self.assertEqual(queue["items"][0]["status"], "completed")

        loaded = load_queue()
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded["items"][0]["status"], "completed")
        self.assertEqual(loaded["items"][1]["status"], "pending")


if __name__ == "__main__":
    unittest.main()
