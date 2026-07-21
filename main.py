from __future__ import annotations

import argparse
import logging
import sys
from datetime import date
from pathlib import Path

import yaml

from scraper.adapters.registry import build_adapter
from scraper.models import RunStats
from scraper.pipeline.dedup import Deduplicator
from scraper.pipeline.fetch import PoliteFetcher
from scraper.pipeline.filter import SentenceFilter
from scraper.pipeline.normalize import clean
from scraper.pipeline.segment import split_sentences
from scraper.storage.writer import CorpusWriter

LOGGER = logging.getLogger("amharic_scraper")


def load_config(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    base = path.parent
    for key in ("jsonl_path", "state_db_path"):
        value = Path(config["output"][key])
        config["output"][key] = str(value if value.is_absolute() else base / value)
    return config


def run_source(adapter, writer, sentence_filter, dedup, since, limit) -> RunStats:
    stats = RunStats()
    urls = adapter.list_article_urls(since=since)
    if limit:
        urls = urls[:limit]
    stats.articles_discovered = len(urls)
    for url in urls:
        if writer.article_seen(url):
            stats.articles_skipped += 1
            continue
        try:
            article = adapter.fetch_article(url)
            stats.articles_fetched += 1
            sentences = split_sentences(article.body_text)
            stats.sentences_extracted += len(sentences)
            for raw_sentence in sentences:
                sentence = clean(raw_sentence)
                accepted, _reason = sentence_filter.passes(sentence)
                if not accepted:
                    stats.sentences_rejected += 1
                    continue
                duplicate, digest = dedup.is_duplicate(sentence)
                if duplicate:
                    stats.duplicates_dropped += 1
                    continue
                writer.append(
                    sentence,
                    digest,
                    {
                        "source": adapter.source_id,
                        "url": article.url,
                        "published_date": article.published_date,
                    },
                )
                stats.sentences_written += 1
            writer.mark_article(url, adapter.source_id)
        except (PermissionError, OSError, ValueError) as exc:
            stats.articles_failed += 1
            LOGGER.warning("%s failed: %s", url, exc)
            writer.mark_article(url, adapter.source_id, status="failed")
    return stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("config.yaml"))
    parser.add_argument("--sources", nargs="+")
    parser.add_argument("--since", type=date.fromisoformat)
    parser.add_argument("--max-articles", type=int)
    parser.add_argument("--sample", type=int, default=0)
    parser.add_argument("--list-sources", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )
    config = load_config(args.config)
    selected = set(args.sources or ())
    sources = {
        name: source
        for name, source in config["sources"].items()
        if (not selected and source.get("enabled", False)) or name in selected
    }
    if args.list_sources:
        for name, source in config["sources"].items():
            print(f"{name:20} {'enabled' if source.get('enabled') else 'disabled'}")
        return 0
    if not sources:
        raise SystemExit("No sources selected or enabled")

    fetcher = PoliteFetcher(config)
    sentence_filter = SentenceFilter(config["filter"])
    total = RunStats()
    with CorpusWriter(config["output"]["jsonl_path"], config["output"]["state_db_path"]) as writer:
        dedup = Deduplicator(config["dedup"], writer.known_hashes())
        for source_id, source_config in sources.items():
            LOGGER.info("Starting %s", source_id)
            adapter = build_adapter(source_id, source_config, fetcher)
            stats = run_source(
                adapter, writer, sentence_filter, dedup, args.since, args.max_articles
            )
            total.add(stats)
            LOGGER.info(
                "%s: fetched=%d written=%d rejected=%d duplicates=%d failed=%d",
                source_id,
                stats.articles_fetched,
                stats.sentences_written,
                stats.sentences_rejected,
                stats.duplicates_dropped,
                stats.articles_failed,
            )
        if args.sample:
            print("\nQA sample:")
            for record in writer.sample(args.sample):
                print(f"[{record['source']} | {record['word_count']} words] {record['sentence']}")

    print(
        "Summary: "
        f"discovered={total.articles_discovered} fetched={total.articles_fetched} "
        f"skipped={total.articles_skipped} failed={total.articles_failed} "
        f"extracted={total.sentences_extracted} rejected={total.sentences_rejected} "
        f"duplicates={total.duplicates_dropped} added={total.sentences_written}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



