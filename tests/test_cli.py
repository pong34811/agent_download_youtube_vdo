"""Tests for youtube_downloader.cli entry point."""
import sys
import unittest
from io import StringIO
from unittest.mock import patch, MagicMock


VALID = "https://www.youtube.com/watch?v=abc123"
VALID2 = "https://www.youtube.com/watch?v=def456"


def _make_exit(captured: list):
    """Return a sys.exit mock that records the code AND raises SystemExit."""
    def _exit(code=0):
        captured.append(code)
        raise SystemExit(code)
    return _exit


class TestCliArgParsing(unittest.TestCase):
    """Test CLI parsing, validation, and exit codes."""

    def _run_main(self, argv: list[str], batch_results: dict | None = None):
        if batch_results is None:
            batch_results = {VALID: True}
        import youtube_downloader.cli as cli_module
        exit_codes: list[int] = []
        with patch("sys.argv", ["downloader"] + argv), \
             patch("youtube_downloader.cli.auto_update_ytdlp") as mock_update, \
             patch("youtube_downloader.cli.run_batch", return_value=batch_results) as mock_batch, \
             patch("sys.stdout", new_callable=StringIO):
            try:
                cli_module.main()
            except SystemExit as exc:
                exit_codes.append(exc.code)
        return mock_batch, exit_codes, mock_update

    def test_single_url_arg_calls_batch(self):
        mock_batch, _, _ = self._run_main([VALID])
        mock_batch.assert_called_once()
        args, _ = mock_batch.call_args
        self.assertIn(VALID, args[0])

    def test_invalid_url_exits_nonzero(self):
        _, codes, _ = self._run_main(["https://vimeo.com/123"])
        self.assertEqual(codes, [1])

    def test_invalid_url_does_not_call_batch(self):
        mock_batch, _, _ = self._run_main(["https://vimeo.com/123"])
        mock_batch.assert_not_called()

    def test_eleven_urls_exits_nonzero(self):
        urls = [f"https://www.youtube.com/watch?v=v{i}" for i in range(11)]
        _, codes, _ = self._run_main(urls)
        self.assertEqual(codes, [1])

    def test_all_success_exits_zero(self):
        _, codes, _ = self._run_main([VALID], {VALID: True})
        self.assertEqual(codes, [0])

    def test_any_failure_exits_nonzero(self):
        _, codes, _ = self._run_main([VALID], {VALID: False})
        self.assertEqual(codes, [1])

    def test_no_update_flag_skips_auto_update(self):
        _, _, mock_update = self._run_main(["--no-update", VALID])
        mock_update.assert_not_called()

    def test_no_update_flag_forwarded_to_batch(self):
        mock_batch, _, _ = self._run_main(["--no-update", VALID])
        _, kwargs = mock_batch.call_args
        self.assertTrue(kwargs.get("no_update") is True)

    def test_multiple_urls_all_passed_to_batch(self):
        results = {VALID: True, VALID2: True}
        mock_batch, _, _ = self._run_main([VALID, VALID2], results)
        args, _ = mock_batch.call_args
        self.assertIn(VALID, args[0])
        self.assertIn(VALID2, args[0])

    def test_auto_update_called_by_default(self):
        _, _, mock_update = self._run_main([VALID])
        mock_update.assert_called_once()


if __name__ == "__main__":
    unittest.main()
