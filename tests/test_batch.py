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


if __name__ == "__main__":
    unittest.main()
