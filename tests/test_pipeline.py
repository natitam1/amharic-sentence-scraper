import tempfile
import unittest
from pathlib import Path

from scraper.pipeline.dedup import Deduplicator
from scraper.pipeline.filter import SentenceFilter
from scraper.pipeline.normalize import clean
from scraper.pipeline.segment import split_sentences
from scraper.storage.writer import CorpusWriter


FILTER_CONFIG = {
    "min_words": 5,
    "max_words": 90,
    "min_ethiopic_ratio": 0.55,
    "require_terminal_punctuation": True,
    "max_url_email_hashtag_ratio": 0.2,
    "blocklist": ["ተጨማሪ ያንብቡ"],
}

DEDUP_CONFIG = {
    "similarity_threshold": 0.9,
    "rolling_window": 100,
    "length_bucket_size": 10,
    "prefix_chars": 8,
}


class PipelineTests(unittest.TestCase):
    def test_segment_keeps_terminal_punctuation(self):
        text = "ዛሬ አየሩ በጣም ጥሩ ነው። ሕዝቡ ወደ ሥራው ተመለሰ?"
        self.assertEqual(
            split_sentences(text),
            ["ዛሬ አየሩ በጣም ጥሩ ነው።", "ሕዝቡ ወደ ሥራው ተመለሰ?"],
        )

    def test_filter_accepts_short_complete_amharic_sentence(self):
        accepted, reason = SentenceFilter(FILTER_CONFIG).passes(
            "መንግሥት አዲስ ዕቅድ ዛሬ አስታወቀ።"
        )
        self.assertTrue(accepted, reason)

    def test_filter_rejects_latin_boilerplate(self):
        accepted, _ = SentenceFilter(FILTER_CONFIG).passes(
            "Subscribe to our newsletter for more daily updates."
        )
        self.assertFalse(accepted)

    def test_normalize_removes_numbering_and_spaces(self):
        self.assertEqual(clean("  1.  ይህ  አዲስ  የዜና ዘገባ ነው። "), "ይህ አዲስ የዜና ዘገባ ነው።")

    def test_exact_dedup(self):
        dedup = Deduplicator(DEDUP_CONFIG)
        first, _ = dedup.is_duplicate("መንግሥት አዲስ ዕቅድ ዛሬ አስታወቀ።")
        second, _ = dedup.is_duplicate("መንግሥት   አዲስ ዕቅድ ዛሬ አስታወቀ።")
        self.assertFalse(first)
        self.assertTrue(second)

    def test_writer_is_persistent(self):
        with tempfile.TemporaryDirectory() as directory:
            jsonl = Path(directory) / "corpus.jsonl"
            db = Path(directory) / "state.db"
            with CorpusWriter(str(jsonl), str(db)) as writer:
                writer.append(
                    "መንግሥት አዲስ ዕቅድ ዛሬ አስታወቀ።",
                    "abc",
                    {"source": "test", "url": "https://example.com/a", "published_date": None},
                )
                writer.mark_article("https://example.com/a", "test")
            with CorpusWriter(str(jsonl), str(db)) as writer:
                self.assertIn("abc", writer.known_hashes())
                self.assertTrue(writer.article_seen("https://example.com/a"))


if __name__ == "__main__":
    unittest.main()

