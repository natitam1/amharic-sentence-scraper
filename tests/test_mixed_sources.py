import json
import tempfile
import unittest
from pathlib import Path

from scraper.adapters.local_transcript import LocalTranscriptAdapter
from scraper.storage.writer import CorpusWriter


class MixedSourceTests(unittest.TestCase):
    def test_local_vtt_removes_cues_and_duplicate_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            transcript = root / "episode.vtt"
            transcript.write_text(
                "WEBVTT\n\n00:00:01.000 --> 00:00:03.000\n"
                "Speaker: ይህ የተፈጥሮ ውይይት ሙከራ ነው።\n\n"
                "00:00:03.000 --> 00:00:05.000\n"
                "Speaker: ይህ የተፈጥሮ ውይይት ሙከራ ነው።\n",
                encoding="utf-8",
            )
            adapter = LocalTranscriptAdapter(
                "podcast",
                {
                    "base_path": str(root),
                    "paths": ["*.vtt"],
                    "strip_speaker_labels": True,
                },
                None,
            )
            urls = adapter.list_article_urls()
            self.assertEqual(len(urls), 1)
            article = adapter.fetch_article(urls[0])
            self.assertEqual(article.body_text, "ይህ የተፈጥሮ ውይይት ሙከራ ነው።")
            self.assertEqual(article.url, transcript.as_uri())

    def test_jsonl_uses_configured_text_field(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            transcript = root / "posts.jsonl"
            transcript.write_text(
                json.dumps({"body": "ይህ የማህበረሰብ ጽሑፍ ሙከራ ነው።"}, ensure_ascii=False),
                encoding="utf-8",
            )
            adapter = LocalTranscriptAdapter(
                "community",
                {"base_path": str(root), "paths": ["*.jsonl"], "text_field": "body"},
                None,
            )
            article = adapter.fetch_article(adapter.list_article_urls()[0])
            self.assertIn("የማህበረሰብ", article.body_text)

    def test_content_counts_treat_legacy_records_as_news(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus.jsonl"
            corpus.write_text(
                json.dumps({"sentence": "legacy"}) + "\n"
                + json.dumps({"sentence": "new", "content_type": "podcast"}) + "\n",
                encoding="utf-8",
            )
            with CorpusWriter(str(corpus), str(root / "state.db")) as writer:
                counts = writer.content_type_counts()
            self.assertEqual(counts["news"], 1)
            self.assertEqual(counts["podcast"], 1)


if __name__ == "__main__":
    unittest.main()
