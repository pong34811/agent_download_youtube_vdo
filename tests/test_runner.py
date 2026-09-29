"""Tests for youtube_downloader.runner module."""
import sys
import unittest
from unittest.mock import patch

from youtube_downloader.runner import build_command, run_download


class TestBuildCommand(unittest.TestCase):
    URL = "https://www.youtube.com/watch?v=abc123"

    def setUp(self):
        # Patch os.path.exists so cookies.txt is always absent for consistency
        patcher = patch("youtube_downloader.runner.os.path.exists", return_value=False)
        self.addCleanup(patcher.stop)
        patcher.start()
        self.cmd = build_command(self.URL)

    def test_starts_with_sys_executable(self):
        self.assertEqual(self.cmd[0], sys.executable)

    def test_invokes_yt_dlp_module(self):
        self.assertIn("-m", self.cmd)
        idx = self.cmd.index("-m")
        self.assertEqual(self.cmd[idx + 1], "yt_dlp")

    def test_url_in_command(self):
        self.assertIn(self.URL, self.cmd)

    def test_no_playlist_flag(self):
        self.assertIn("--no-playlist", self.cmd)

    def test_format_flag(self):
        self.assertIn("--format", self.cmd)

    def test_merge_output_format_mp4(self):
        self.assertIn("--merge-output-format", self.cmd)
        idx = self.cmd.index("--merge-output-format")
        self.assertEqual(self.cmd[idx + 1], "mp4")

    def test_output_template_has_date_folder(self):
        self.assertIn("-o", self.cmd)
        idx = self.cmd.index("-o")
        self.assertIn("%(title)s", self.cmd[idx + 1])

    def test_tls_verification_on(self):
        self.assertNotIn("--no-check-certificates", self.cmd)

    def test_cookies_from_browser_edge_when_no_cookies_file(self):
        self.assertIn("--cookies-from-browser", self.cmd)
        idx = self.cmd.index("--cookies-from-browser")
        self.assertEqual(self.cmd[idx + 1], "edge")

    def test_cookies_file_used_when_present(self):
        with patch("youtube_downloader.runner.os.path.exists", return_value=True):
            cmd = build_command(self.URL)
        self.assertIn("--cookies", cmd)
        self.assertNotIn("--cookies-from-browser", cmd)

    def test_no_update_flag_absent_by_default(self):
        self.assertNotIn("--no-update", self.cmd)

    def test_no_update_flag_present_when_requested(self):
        with patch("youtube_downloader.runner.os.path.exists", return_value=False):
            cmd = build_command(self.URL, no_update=True)
        self.assertIn("--no-update", cmd)

    def test_retries_finite(self):
        self.assertIn("--retries", self.cmd)
        idx = self.cmd.index("--retries")
        self.assertEqual(self.cmd[idx + 1], "5")

    def test_fragment_retries_finite(self):
        self.assertIn("--fragment-retries", self.cmd)
        idx = self.cmd.index("--fragment-retries")
        self.assertEqual(self.cmd[idx + 1], "5")


    def test_build_command_with_custom_output_dir(self):
        cmd = build_command(self.URL, output_dir="custom_folder")
        idx = cmd.index("-o")
        self.assertEqual(cmd[idx + 1], "custom_folder/%(title)s.%(ext)s")

    def test_build_command_default_output_dir(self):
        cmd = build_command(self.URL)
        idx = cmd.index("-o")
        import datetime
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        self.assertEqual(cmd[idx + 1], f"{today}/%(title)s.%(ext)s")


class TestRunDownload(unittest.TestCase):
    URL = "https://www.youtube.com/watch?v=abc123"

    def test_run_download_passes_output_dir(self):
        with patch("youtube_downloader.runner.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            run_download(self.URL, no_update=True, output_dir="saved_folder")
            cmd = mock_run.call_args[0][0]
            idx = cmd.index("-o")
            self.assertEqual(cmd[idx + 1], "saved_folder/%(title)s.%(ext)s")

    def test_returns_true_on_zero_exit(self):
        with patch("youtube_downloader.runner.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = run_download(self.URL, no_update=True)
        self.assertTrue(result)

    def test_returns_false_on_nonzero_exit(self):
        with patch("youtube_downloader.runner.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            result = run_download(self.URL, no_update=True)
        self.assertFalse(result)

    def test_calls_subprocess_run_with_shell_false(self):
        with patch("youtube_downloader.runner.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            run_download(self.URL, no_update=True)
            _, kwargs = mock_run.call_args
            self.assertFalse(kwargs.get("shell", False))

    def test_falls_back_without_browser_cookies_if_initial_fails(self):
        with patch("youtube_downloader.runner.subprocess.run") as mock_run, \
             patch("youtube_downloader.runner.os.path.exists", return_value=False):
            mock_run.side_effect = [
                unittest.mock.MagicMock(returncode=1),
                unittest.mock.MagicMock(returncode=0),
            ]
            result = run_download(self.URL, no_update=True)
            self.assertTrue(result)
            self.assertEqual(mock_run.call_count, 2)
            second_cmd = mock_run.call_args_list[1][0][0]
            self.assertNotIn("--cookies-from-browser", second_cmd)


if __name__ == "__main__":
    unittest.main()
