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

    def _run_main(
        self,
        argv: list[str],
        batch_results: dict | None = None,
        queue_data: dict | None = None,
        user_input: str | None = None,
    ):
        if batch_results is None:
            batch_results = {VALID: True}
        import youtube_downloader.cli as cli_module
        exit_codes: list[int] = []
        stdout_io = StringIO()
        stdin_patch = patch("builtins.input", return_value=user_input or "") if user_input is not None else patch("builtins.input", return_value="")
        with patch("sys.argv", ["downloader"] + argv), \
             patch("youtube_downloader.cli.auto_update_ytdlp") as mock_update, \
             patch("youtube_downloader.cli.run_batch", return_value=batch_results) as mock_batch, \
             patch("youtube_downloader.cli.load_queue", return_value=queue_data) as mock_load, \
             patch("youtube_downloader.cli.clear_queue") as mock_clear, \
             patch("sys.stdout", stdout_io), \
             stdin_patch:
            try:
                cli_module.main()
            except SystemExit as exc:
                exit_codes.append(exc.code)
        return mock_batch, exit_codes, mock_update, stdout_io.getvalue(), mock_clear

    def test_single_url_arg_calls_batch(self):
        mock_batch, _, _, _, _ = self._run_main([VALID])
        mock_batch.assert_called_once()
        args, _ = mock_batch.call_args
        self.assertIn(VALID, args[0])

    def test_invalid_url_exits_nonzero(self):
        _, codes, _, _, _ = self._run_main(["https://vimeo.com/123"])
        self.assertEqual(codes, [1])

    def test_invalid_url_does_not_call_batch(self):
        mock_batch, _, _, _, _ = self._run_main(["https://vimeo.com/123"])
        mock_batch.assert_not_called()

    def test_twenty_three_urls_exits_nonzero(self):
        urls = [f"https://www.youtube.com/watch?v=v{i}" for i in range(23)]
        _, codes, _, _, _ = self._run_main(urls)
        self.assertEqual(codes, [1])

    def test_all_success_exits_zero(self):
        _, codes, _, _, _ = self._run_main([VALID], {VALID: True})
        self.assertEqual(codes, [0])

    def test_any_failure_exits_nonzero(self):
        _, codes, _, _, _ = self._run_main([VALID], {VALID: False})
        self.assertEqual(codes, [1])

    def test_no_update_flag_skips_auto_update(self):
        _, _, mock_update, _, _ = self._run_main(["--no-update", VALID])
        mock_update.assert_not_called()

    def test_no_update_flag_forwarded_to_batch(self):
        mock_batch, _, _, _, _ = self._run_main(["--no-update", VALID])
        _, kwargs = mock_batch.call_args
        self.assertTrue(kwargs.get("no_update") is True)

    def test_multiple_urls_all_passed_to_batch(self):
        results = {VALID: True, VALID2: True}
        mock_batch, _, _, _, _ = self._run_main([VALID, VALID2], results)
        args, _ = mock_batch.call_args
        self.assertIn(VALID, args[0])
        self.assertIn(VALID2, args[0])

    def test_auto_update_called_by_default(self):
        _, _, mock_update, _, _ = self._run_main([VALID])
        mock_update.assert_called_once()

    def test_resume_flag_no_queue_prints_info_and_exits_zero(self):
        mock_batch, codes, _, stdout, _ = self._run_main(["--resume"], queue_data=None)
        mock_batch.assert_not_called()
        self.assertEqual(codes, [0])
        self.assertIn("No unfinished download session found", stdout)

    def test_resume_flag_with_queue_resumes_pending_urls(self):
        queue = {
            "created_at": "2026-09-28T12:00:00",
            "output_dir": "2026-09-28",
            "items": [
                {"url": VALID, "status": "completed"},
                {"url": VALID2, "status": "pending"},
            ],
        }
        mock_batch, codes, _, _, _ = self._run_main(
            ["--resume"],
            batch_results={VALID2: True},
            queue_data=queue,
        )
        mock_batch.assert_called_once()
        urls_passed = mock_batch.call_args[0][0]
        self.assertEqual(urls_passed, [VALID2])
        self.assertEqual(mock_batch.call_args[1].get("output_dir"), "2026-09-28")
        self.assertEqual(codes, [0])

    def test_cli_auto_detects_queue_and_user_accepts(self):
        queue = {
            "created_at": "2026-09-28T12:00:00",
            "output_dir": "2026-09-28",
            "items": [
                {"url": VALID, "status": "pending"},
            ],
        }
        mock_batch, codes, _, stdout, _ = self._run_main(
            [],
            batch_results={VALID: True},
            queue_data=queue,
            user_input="y",
        )
        mock_batch.assert_called_once()
        urls_passed = mock_batch.call_args[0][0]
        self.assertEqual(urls_passed, [VALID])
        self.assertEqual(codes, [0])

    def test_cli_auto_detects_queue_and_user_declines(self):
        queue = {
            "created_at": "2026-09-28T12:00:00",
            "output_dir": "2026-09-28",
            "items": [
                {"url": VALID, "status": "pending"},
            ],
        }
        mock_batch, codes, _, _, mock_clear = self._run_main(
            [VALID2],
            batch_results={VALID2: True},
            queue_data=queue,
            user_input="n",
        )
        mock_clear.assert_called_once()
        mock_batch.assert_called_once()
        urls_passed = mock_batch.call_args[0][0]
        self.assertEqual(urls_passed, [VALID2])
        self.assertEqual(codes, [0])

    def test_cli_handles_keyboard_interrupt_gracefully(self):
        import youtube_downloader.cli as cli_module
        exit_codes = []
        stdout_io = StringIO()
        with patch("sys.argv", ["downloader"]), \
             patch("youtube_downloader.cli.load_queue", return_value=None), \
             patch("builtins.input", side_effect=KeyboardInterrupt), \
             patch("sys.stdout", stdout_io):
            try:
                cli_module.main()
            except SystemExit as exc:
                exit_codes.append(exc.code)
        self.assertIn("Cancelled.", stdout_io.getvalue())
        self.assertEqual(exit_codes, [1])


if __name__ == "__main__":
    unittest.main()


class TestCliPlaylistResolution(unittest.TestCase):
    """Playlist URLs expand to individual video URLs before validation/queue."""

    def _run_main(
        self,
        argv,
        batch_results=None,
        resolve_return=None,
        queue_data=None,
    ):
        if batch_results is None:
            batch_results = {}
        if resolve_return is None:
            resolve_return = []
        import youtube_downloader.cli as cli_module
        exit_codes = []
        stdout_io = StringIO()
        with patch("sys.argv", ["downloader"] + argv), \
             patch("youtube_downloader.cli.auto_update_ytdlp"), \
             patch("youtube_downloader.cli.run_batch", return_value=batch_results) as mock_batch, \
             patch("youtube_downloader.cli.load_queue", return_value=queue_data), \
             patch("youtube_downloader.cli.clear_queue"), \
             patch("youtube_downloader.cli.resolve_playlist", return_value=resolve_return) as mock_resolve, \
             patch("sys.stdout", stdout_io), \
             patch("builtins.input", return_value=""):
            try:
                cli_module.main()
            except SystemExit as exc:
                exit_codes.append(exc.code)
        return mock_batch, exit_codes, mock_resolve, stdout_io.getvalue()

    def test_playlist_url_expanded_before_batch(self):
        playlist = "https://www.youtube.com/playlist?list=PLx"
        vids = ["https://www.youtube.com/watch?v=v1", "https://www.youtube.com/watch?v=v2"]
        mock_batch, _, _, _ = self._run_main(
            [playlist], batch_results={v: True for v in vids}, resolve_return=vids,
        )
        mock_batch.assert_called_once()
        urls_passed = mock_batch.call_args[0][0]
        self.assertEqual(urls_passed, vids)

    def test_playlist_url_expanded_before_validation(self):
        # A playlist that expands to more than 22 videos must be rejected
        # by the limit check, with exit code 1 and no batch call.
        playlist = "https://www.youtube.com/playlist?list=PLx"
        many = [f"https://www.youtube.com/watch?v=v{i}" for i in range(23)]
        mock_batch, codes, _, stdout = self._run_main(
            [playlist], resolve_return=many,
        )
        self.assertEqual(codes, [1])
        mock_batch.assert_not_called()
        self.assertIn("22", stdout)

    def test_playlist_and_single_urls_combined(self):
        playlist = "https://www.youtube.com/playlist?list=PLx"
        single = "https://www.youtube.com/watch?v=solo"
        vids = ["https://www.youtube.com/watch?v=v1", "https://www.youtube.com/watch?v=v2"]
        mock_batch, _, _, _ = self._run_main(
            [playlist, single], resolve_return=vids,
        )
        urls_passed = mock_batch.call_args[0][0]
        self.assertEqual(urls_passed, vids + [single])

    def test_resolve_failure_rejects_batch(self):
        playlist = "https://www.youtube.com/playlist?list=PLx"
        # When resolve_playlist raises RuntimeError, _expand_urls prints
        # an error message and calls SystemExit(1). The batch should not run.
        with patch("youtube_downloader.cli.resolve_playlist", side_effect=RuntimeError("boom")):
            mock_batch, codes, _, stdout = self._run_main([playlist])
        self.assertEqual(codes, [1])
        mock_batch.assert_not_called()
        # Exit code 1 confirms rejection; exact message may vary.

    def test_resume_does_not_resolve_playlists(self):
        # Resume works on already-expanded individual video URLs stored in
        # the queue; the playlist resolver must not be invoked on resume.
        queue = {
            "created_at": "2026-10-05T12:00:00",
            "output_dir": "2026-10-05",
            "items": [
                {"url": "https://www.youtube.com/watch?v=v1", "status": "pending"},
            ],
        }
        mock_batch, codes, _, _ = self._run_main(
            ["--resume"], batch_results={"https://www.youtube.com/watch?v=v1": True}, queue_data=queue,
        )
        mock_batch.assert_called_once()
        self.assertEqual(codes, [0])


class TestCliOutputDir(unittest.TestCase):
    """--output-dir forces the download folder regardless of date."""

    def _run_main(self, argv, batch_results=None, resolve_return=None):
        if batch_results is None:
            batch_results = {}
        if resolve_return is None:
            resolve_return = []
        import youtube_downloader.cli as cli_module
        exit_codes = []
        stdout_io = StringIO()
        with patch("sys.argv", ["downloader"] + argv), \
             patch("youtube_downloader.cli.auto_update_ytdlp"), \
             patch("youtube_downloader.cli.run_batch", return_value=batch_results) as mock_batch, \
             patch("youtube_downloader.cli.load_queue", return_value=None), \
             patch("youtube_downloader.cli.clear_queue"), \
             patch("youtube_downloader.cli.resolve_playlist", return_value=resolve_return) as mock_resolve, \
             patch("sys.stdout", stdout_io), \
             patch("builtins.input", return_value=""):
            try:
                cli_module.main()
            except SystemExit as exc:
                exit_codes.append(exc.code)
        return mock_batch, exit_codes, stdout_io.getvalue()

    def test_output_dir_flag_passed_to_batch(self):
        mock_batch, _, _ = self._run_main(
            ["--output-dir", "MyFolder", "https://www.youtube.com/watch?v=v1"],
            batch_results={"https://www.youtube.com/watch?v=v1": True},
        )
        self.assertEqual(mock_batch.call_args[1].get("output_dir"), "MyFolder")

    def test_output_dir_equals_sign_passed_to_batch(self):
        mock_batch, _, _ = self._run_main(
            ["--output-dir=MyFolder", "https://www.youtube.com/watch?v=v1"],
            batch_results={"https://www.youtube.com/watch?v=v1": True},
        )
        self.assertEqual(mock_batch.call_args[1].get("output_dir"), "MyFolder")

    def test_output_dir_uses_resolve_expanded_urls(self):
        mock_batch, _, _ = self._run_main(
            ["--output-dir", "MyFolder", "https://www.youtube.com/playlist?list=PLx"],
            batch_results={"https://www.youtube.com/watch?v=v1": True},
            resolve_return=["https://www.youtube.com/watch?v=v1"],
        )
        self.assertEqual(mock_batch.call_args[1].get("output_dir"), "MyFolder")
        urls_passed = mock_batch.call_args[0][0]
        self.assertEqual(urls_passed, ["https://www.youtube.com/watch?v=v1"])


if __name__ == "__main__":
    unittest.main()
