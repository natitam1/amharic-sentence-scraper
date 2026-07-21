import unittest

from scraper.adapters.youtube_playlist import YouTubePlaylistAdapter


class YouTubeAdapterTests(unittest.TestCase):
    def test_prefers_manual_amharic_vtt(self):
        adapter = YouTubePlaylistAdapter(
            "documentary",
            {"subtitle_languages": ["am", "am-ET"]},
            None,
        )
        info = {
            "subtitles": {"am": [{"ext": "vtt", "url": "manual"}]},
            "automatic_captions": {"am": [{"ext": "vtt", "url": "automatic"}]},
        }
        language, track, automatic = adapter._select_subtitle(info)
        self.assertEqual(language, "am")
        self.assertEqual(track["url"], "manual")
        self.assertFalse(automatic)

    def test_uses_automatic_caption_fallback(self):
        adapter = YouTubePlaylistAdapter(
            "documentary",
            {"subtitle_languages": ["am"]},
            None,
        )
        info = {
            "subtitles": {},
            "automatic_captions": {"am-ET": [{"ext": "vtt", "url": "automatic"}]},
        }
        language, track, automatic = adapter._select_subtitle(info)
        self.assertEqual(language, "am-ET")
        self.assertEqual(track["url"], "automatic")
        self.assertTrue(automatic)

    def test_rejects_non_amharic_tracks(self):
        adapter = YouTubePlaylistAdapter(
            "documentary",
            {"subtitle_languages": ["am"]},
            None,
        )
        self.assertEqual(adapter._select_subtitle({"subtitles": {"en": []}}), (None, None, False))


if __name__ == "__main__":
    unittest.main()
