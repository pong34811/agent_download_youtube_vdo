"""Tests for youtube_downloader.batch module."""
import unittest
from unittest.mock import patch, call

from youtube_downloader.batch import run_batch


class TestRunBatch(unittest.TestCase):
    URL1 = "https://www.youtube.com/watch?v=aaa"
    URL2 = "https://www.youtube.com/watch?v=bbb"
    URL3 = "https://www.youtube.com/watch?v=ccc"

    def test_all_success_returns_all_true(self):
        with patch("youtube_downloader.batch.run_download", return_value=True):
            result = run_batch([self.URL1, self.URL2])
        self.assertEqual(result, {self.URL1: True, self.URL2: True})

    def test_one_failure_continues_rest(self):
        side_effects = [False, True]
        with patch("youtube_downloader.batch.run_download", side_effect=side_effects):
            result = run_batch([self.URL1, self.URL2])
        self.assertEqual(result[self.URL1], False)
        self.assertEqual(result[self.URL2], True)

    def test_runs_in_order(self):
        with patch("youtube_downloader.batch.run_download", return_value=True) as mock_dl:
            run_batch([self.URL1, self.URL2, self.URL3])
        mock_dl.assert_has_calls([
            call(self.URL1, no_update=False),
            call(self.URL2, no_update=False),
            call(self.URL3, no_update=False),
        ])

    def test_no_update_flag_forwarded(self):
        with patch("youtube_downloader.batch.run_download", return_value=True) as mock_dl:
            run_batch([self.URL1], no_update=True)
        mock_dl.assert_called_once_with(self.URL1, no_update=True)

    def test_empty_batch_returns_empty_dict(self):
        with patch("youtube_downloader.batch.run_download", return_value=True) as mock_dl:
            result = run_batch([])
        mock_dl.assert_not_called()
        self.assertEqual(result, {})

    def test_run_batch_passes_output_dir_to_run_download(self):
        with patch("youtube_downloader.batch.run_download", return_value=True) as mock_dl:
            run_batch([self.URL1], output_dir="custom_date")
        mock_dl.assert_called_once_with(self.URL1, no_update=False, output_dir="custom_date")

    def test_run_batch_updates_queue_progress(self):
        queue_data = {
            "created_at": "2026-09-29T00:00:00",
            "output_dir": "2026-09-29",
            "items": [
                {"url": self.URL1, "status": "pending"},
                {"url": self.URL2, "status": "pending"},
            ],
        }
        with patch("youtube_downloader.batch.run_download", side_effect=[True, False]), \
             patch("youtube_downloader.batch.update_item_status") as mock_update, \
             patch("youtube_downloader.batch.clear_queue") as mock_clear:
            run_batch([self.URL1, self.URL2], queue_data=queue_data)

            mock_update.assert_has_calls([
                call(queue_data, self.URL1, "completed"),
                call(queue_data, self.URL2, "failed"),
            ])
            mock_clear.assert_not_called()

    def test_run_batch_clears_queue_on_all_success(self):
        queue_data = {
            "created_at": "2026-09-29T00:00:00",
            "output_dir": "2026-09-29",
            "items": [
                {"url": self.URL1, "status": "pending"},
            ],
        }
        with patch("youtube_downloader.batch.run_download", return_value=True), \
             patch("youtube_downloader.batch.clear_queue") as mock_clear, \
             patch("youtube_downloader.queue.save_queue"):
            run_batch([self.URL1], queue_data=queue_data)
            mock_clear.assert_called_once()

    def test_run_batch_handles_keyboard_interrupt(self):
        queue_data = {
            "created_at": "2026-09-29T00:00:00",
            "output_dir": "2026-09-29",
            "items": [
                {"url": self.URL1, "status": "pending"},
                {"url": self.URL2, "status": "pending"},
            ],
        }
        with patch("youtube_downloader.batch.run_download", side_effect=[True, KeyboardInterrupt]), \
             patch("youtube_downloader.batch.update_item_status") as mock_update, \
             patch("youtube_downloader.batch.clear_queue") as mock_clear:
            results = run_batch([self.URL1, self.URL2], queue_data=queue_data)

            mock_update.assert_has_calls([
                call(queue_data, self.URL1, "completed"),
                call(queue_data, self.URL2, "pending"),
            ])
            mock_clear.assert_not_called()
            self.assertEqual(results, {self.URL1: True})


if __name__ == "__main__":
    unittest.main()
