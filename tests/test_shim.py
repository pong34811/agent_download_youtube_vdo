"""Test that downloader.py shim delegates to youtube_downloader.cli.main."""
import unittest
from unittest.mock import patch


class TestDownloaderShim(unittest.TestCase):
    def test_main_delegates_to_cli(self):
        with patch("youtube_downloader.cli.main") as mock_main:
            import downloader
            import importlib
            importlib.reload(downloader)
            downloader.main()
        mock_main.assert_called_once()


if __name__ == "__main__":
    unittest.main()
