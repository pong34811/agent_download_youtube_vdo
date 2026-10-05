"""Tests for youtube_downloader.playlist module."""
import json
import unittest
from unittest.mock import patch, MagicMock

from youtube_downloader.playlist import resolve_playlist, is_playlist_url


class TestIsPlaylistUrl(unittest.TestCase):
    def test_playlist_url_accepted(self):
        self.assertTrue(is_playlist_url("https://www.youtube.com/playlist?list=PLD1wi10rj474"))

    def test_single_video_rejected(self):
        self.assertFalse(is_playlist_url("https://www.youtube.com/watch?v=abc123"))

    def test_youtu_be_rejected(self):
        self.assertFalse(is_playlist_url("https://youtu.be/abc123"))

    def test_http_playlist_accepted(self):
        self.assertTrue(is_playlist_url("http://youtube.com/playlist?list=PLx"))

    def test_subdomain_playlist_accepted(self):
        self.assertTrue(is_playlist_url("https://music.youtube.com/playlist?list=PLx"))


class TestResolvePlaylist(unittest.TestCase):
    def test_resolve_returns_video_urls(self):
        json_line = json.dumps({
            "_type": "url", "url": "https://www.youtube.com/watch?v=vid1",
            "id": "vid1", "title": "Video 1",
        })
        with patch("youtube_downloader.playlist.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=json_line + "\n")
            result = resolve_playlist("https://www.youtube.com/playlist?list=PLx")
        self.assertEqual(result, ["https://www.youtube.com/watch?v=vid1"])

    def test_resolve_returns_multiple_urls(self):
        lines = "\n".join(
            json.dumps({"_type": "url", "url": f"https://www.youtube.com/watch?v=v{i}", "id": f"v{i}"})
            for i in range(3)
        )
        with patch("youtube_downloader.playlist.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=lines + "\n")
            result = resolve_playlist("https://www.youtube.com/playlist?list=PLx")
        self.assertEqual(len(result), 3)
        self.assertTrue(all("watch?v=" in u for u in result))

    def test_nonzero_exit_raises(self):
        with patch("youtube_downloader.playlist.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
            with self.assertRaises(RuntimeError):
                resolve_playlist("https://www.youtube.com/playlist?list=PLx")

    def test_uses_flat_playlist_flag(self):
        with patch("youtube_downloader.playlist.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            resolve_playlist("https://www.youtube.com/playlist?list=PLx")
        cmd = mock_run.call_args[0][0]
        self.assertIn("--flat-playlist", cmd)
        self.assertIn("--dump-json", cmd)

    def test_uses_sys_executable(self):
        import sys
        with patch("youtube_downloader.playlist.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            resolve_playlist("https://www.youtube.com/playlist?list=PLx")
        cmd = mock_run.call_args[0][0]
        self.assertEqual(cmd[0], sys.executable)

    def test_shell_false_enforced(self):
        with patch("youtube_downloader.playlist.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            resolve_playlist("https://www.youtube.com/playlist?list=PLx")
        _, kwargs = mock_run.call_args
        self.assertFalse(kwargs.get("shell", False))

    def test_url_is_last_argument(self):
        url = "https://www.youtube.com/playlist?list=PLx"
        with patch("youtube_downloader.playlist.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            resolve_playlist(url)
        cmd = mock_run.call_args[0][0]
        self.assertEqual(cmd[-1], url)

    def test_skips_blank_lines(self):
        lines = "\n\n" + json.dumps({"_type": "url", "url": "https://www.youtube.com/watch?v=v1", "id": "v1"}) + "\n\n"
        with patch("youtube_downloader.playlist.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=lines)
            result = resolve_playlist("https://www.youtube.com/playlist?list=PLx")
        self.assertEqual(result, ["https://www.youtube.com/watch?v=v1"])

    def test_skips_entries_without_url_or_id(self):
        lines = "\n".join([
            json.dumps({"_type": "playlist", "id": "PLx", "title": "Playlist"}),
            json.dumps({"_type": "url", "url": "https://www.youtube.com/watch?v=v1", "id": "v1"}),
        ])
        with patch("youtube_downloader.playlist.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=lines)
            result = resolve_playlist("https://www.youtube.com/playlist?list=PLx")
        self.assertEqual(result, ["https://www.youtube.com/watch?v=v1"])

    def test_playlist_header_entry_not_turned_into_url(self):
        # Regression: the playlist header entry ("_type": "playlist") has an
        # "id" of "PLx" — it must NOT be expanded into watch?v=PLx.
        lines = json.dumps({"_type": "playlist", "id": "PLx", "title": "Playlist"})
        with patch("youtube_downloader.playlist.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=lines)
            result = resolve_playlist("https://www.youtube.com/playlist?list=PLx")
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()