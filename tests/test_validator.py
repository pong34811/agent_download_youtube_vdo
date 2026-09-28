"""Tests for youtube_downloader.validator module."""
import unittest
from youtube_downloader.validator import is_valid_youtube_url, validate_batch


class TestIsValidYoutubeUrl(unittest.TestCase):
    def test_youtube_com_watch_accepted(self):
        self.assertTrue(is_valid_youtube_url("https://www.youtube.com/watch?v=abc123"))

    def test_youtu_be_accepted(self):
        self.assertTrue(is_valid_youtube_url("https://youtu.be/abc123"))

    def test_subdomain_youtube_accepted(self):
        self.assertTrue(is_valid_youtube_url("https://music.youtube.com/watch?v=abc123"))

    def test_http_accepted(self):
        self.assertTrue(is_valid_youtube_url("http://youtube.com/watch?v=abc123"))

    def test_non_youtube_rejected(self):
        self.assertFalse(is_valid_youtube_url("https://vimeo.com/123"))

    def test_ftp_rejected(self):
        self.assertFalse(is_valid_youtube_url("ftp://youtube.com/watch?v=abc123"))

    def test_empty_rejected(self):
        self.assertFalse(is_valid_youtube_url(""))

    def test_plain_string_rejected(self):
        self.assertFalse(is_valid_youtube_url("not a url"))


class TestValidateBatch(unittest.TestCase):
    VALID = "https://www.youtube.com/watch?v=abc123"
    VALID2 = "https://www.youtube.com/watch?v=def456"

    def test_single_valid_url_accepted(self):
        urls, errors = validate_batch([self.VALID])
        self.assertEqual(urls, [self.VALID])
        self.assertEqual(errors, [])

    def test_ten_valid_urls_accepted(self):
        urls = [f"https://www.youtube.com/watch?v=vid{i}" for i in range(10)]
        result, errors = validate_batch(urls)
        self.assertEqual(len(result), 10)
        self.assertEqual(errors, [])

    def test_eleven_urls_rejected(self):
        urls = [f"https://www.youtube.com/watch?v=vid{i}" for i in range(11)]
        _, errors = validate_batch(urls)
        self.assertTrue(any("10" in e for e in errors))

    def test_invalid_url_produces_error(self):
        _, errors = validate_batch(["https://vimeo.com/123"])
        self.assertTrue(len(errors) > 0)

    def test_duplicate_removed(self):
        result, errors = validate_batch([self.VALID, self.VALID])
        self.assertEqual(result, [self.VALID])
        self.assertEqual(errors, [])

    def test_empty_list_produces_error(self):
        _, errors = validate_batch([])
        self.assertTrue(len(errors) > 0)

    def test_dedup_then_count_checked(self):
        # 11 identical URLs dedup to 1 → no over-limit error
        urls = ["https://www.youtube.com/watch?v=abc123"] * 11
        result, errors = validate_batch(urls)
        self.assertEqual(errors, [])
        self.assertEqual(result, ["https://www.youtube.com/watch?v=abc123"])


if __name__ == "__main__":
    unittest.main()
