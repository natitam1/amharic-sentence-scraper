"""Export filtered, unique sentences from one YouTube video's captions."""
from __future__ import annotations

import argparse
from pathlib import Path

from scraper.adapters.youtube_playlist import YouTubePlaylistAdapter
from scraper.pipeline.filter import SentenceFilter
from scraper.pipeline.normalize import clean
from scraper.pipeline.segment import split_sentences


class _UnusedFetcher:
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("output", type=Path)
    parser.add_argument("--limit", type=int, default=3000)
    parser.add_argument("--min-words", type=int, default=5)
    parser.add_argument("--max-words", type=int, default=50)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    adapter = YouTubePlaylistAdapter(
        "single_youtube_video",
        {
            "subtitle_languages": ["am-orig", "am", "am-ET"],
            "strip_speaker_labels": True,
            "player_clients": ["android"],
            "request_delay_seconds": 0,
            "subtitle_retries": 3,
            "subtitle_backoff_seconds": 10,
        },
        _UnusedFetcher(),
    )
    sentence_filter = SentenceFilter(
        {
            "min_words": args.min_words,
            "max_words": args.max_words,
            "min_ethiopic_ratio": 0.55,
            "require_terminal_punctuation": True,
            "max_url_email_hashtag_ratio": 0.20,
            "reject_caption_artifacts": True,
            "reject_repeated_words": True,
            "blocklist": [],
        }
    )

    article = adapter.fetch_article(args.url)
    sentences: list[str] = []
    seen: set[str] = set()
    for raw_sentence in split_sentences(article.body_text):
        sentence = clean(raw_sentence)
        accepted, _reason = sentence_filter.passes(sentence)
        if not accepted or sentence in seen:
            continue
        seen.add(sentence)
        sentences.append(sentence)
        if len(sentences) >= args.limit:
            break

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(f"{sentence}\n" for sentence in sentences),
        encoding="utf-8",
    )
    print(
        f"Wrote {len(sentences)} sentences to {args.output} "
        f"(requested {args.limit}, {args.min_words}-{args.max_words} words each)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
