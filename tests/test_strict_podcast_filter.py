import unittest

from scraper.pipeline.filter import SentenceFilter


class StrictPodcastFilterTests(unittest.TestCase):
    def setUp(self):
        self.filter = SentenceFilter({
            "min_words": 12,
            "max_words": 90,
            "min_ethiopic_ratio": 0.90,
            "require_terminal_punctuation": True,
            "max_url_email_hashtag_ratio": 0.2,
            "max_latin_words": 0,
            "reject_caption_artifacts": True,
            "reject_repeated_words": True,
            "blocklist": [],
        })

    def test_rejects_latin_words(self):
        accepted, reason = self.filter.passes(
            "ይህ ረጅም የአማርኛ ዓረፍተ ነገር business የሚለውን የእንግሊዝኛ ቃል በውስጡ ይዞ ለአንባቢው ግልጽ መልዕክት ያቀርባል።"
        )
        self.assertFalse(accepted)
        self.assertEqual(reason, "latin_words")

    def test_rejects_short_caption_fragment(self):
        accepted, reason = self.filter.passes("ይህ በጣም አጭር የንግግር ቁራጭ ነው።")
        self.assertFalse(accepted)
        self.assertEqual(reason, "length")

    def test_rejects_caption_artifacts(self):
        accepted, reason = self.filter.passes(
            "ይህ በቂ ርዝመት ያለው ነገር ግን [ሙዚቃ] የሚለውን የካፕሽን ምልክት በውስጡ ይዟል።"
        )
        self.assertFalse(accepted)
        self.assertEqual(reason, "caption_artifact")


if __name__ == "__main__":
    unittest.main()

