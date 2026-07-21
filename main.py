from __future__ import annotations

import argparse
import logging
import sys
from collections import Counter
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
    for source in config.get("sources", {}).values():
        if source.get("adapter") == "local_transcript":
            base_path = Path(source.get("base_path", "."))
            source["base_path"] = str(base_path if base_path.is_absolute() else base / base_path)
    return config


def run_source(
    adapter,
    writer,
    sentence_filter,
    dedup,
    since,
    limit,
    type_counts: Counter[str],
    max_per_type: int | None,
) -> RunStats:
    stats = RunStats()
    content_type = adapter.config.get("content_type", "news")
    urls = adapter.list_article_urls(since=since)
    if limit:
        urls = urls[:limit]
    stats.articles_discovered = len(urls)
    for url in urls:
        if writer.article_seen(url, include_failed=not adapter.config.get("retry_failed", True)):
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
                if max_per_type is not None and type_counts[content_type] >= max_per_type:
                    stats.quota_skipped += 1
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
                        "content_type": content_type,
                        "url": article.url,
                        "published_date": article.published_date,
                        "title": article.title,
                        **article.metadata,
                    },
                )
                type_counts[content_type] += 1
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
    parser.add_argument("--content-types", nargs="+")
    parser.add_argument("--since", type=date.fromisoformat)
    parser.add_argument("--max-articles", type=int)
    parser.add_argument("--max-sentences-per-type", type=int)
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
    selected_types = set(args.content_types or ())
    sources = {
        name: source
        for name, source in config["sources"].items()
        if ((not selected and source.get("enabled", False)) or name in selected)
        and (not selected_types or source.get("content_type", "news") in selected_types)
    }
    if args.list_sources:
        for name, source in config["sources"].items():
            state = "enabled" if source.get("enabled") else "disabled"
            print(f"{name:28} {state:8} {source.get('content_type', 'news')}")
        return 0
    if not sources:
        raise SystemExit("No sources selected or enabled")

    fetcher = PoliteFetcher(config)
    total = RunStats()
    with CorpusWriter(config["output"]["jsonl_path"], config["output"]["state_db_path"]) as writer:
        dedup = Deduplicator(config["dedup"], writer.known_hashes())
        type_counts = writer.content_type_counts()
        quota = args.max_sentences_per_type or config.get("balance", {}).get("max_sentences_per_type")
        for source_id, source_config in sources.items():
            LOGGER.info("Starting %s (%s)", source_id, source_config.get("content_type", "news"))
            adapter = build_adapter(source_id, source_config, fetcher)
            filter_config = {**config["filter"], **source_config.get("filter", {})}
            sentence_filter = SentenceFilter(filter_config)
            stats = run_source(
                adapter,
                writer,
                sentence_filter,
                dedup,
                args.since,
                args.max_articles,
                type_counts,
                quota,
            )
            total.add(stats)
            LOGGER.info(
                "%s: fetched=%d written=%d rejected=%d quota=%d duplicates=%d failed=%d",
                source_id,
                stats.articles_fetched,
                stats.sentences_written,
                stats.sentences_rejected,
                stats.quota_skipped,
                stats.duplicates_dropped,
                stats.articles_failed,
            )
        if args.sample:
            print("\nQA sample:")
            for record in writer.sample(args.sample):
                label = record.get("content_type", "news")
                print(f"[{label}/{record['source']} | {record['word_count']} words] {record['sentence']}")
        print("\nContent totals:")
        for content_type, count in sorted(type_counts.items()):
            print(f"  {content_type}: {count}")

    print(
        "Summary: "
        f"discovered={total.articles_discovered} fetched={total.articles_fetched} "
        f"skipped={total.articles_skipped} failed={total.articles_failed} "
        f"extracted={total.sentences_extracted} rejected={total.sentences_rejected} "
        f"quota={total.quota_skipped} duplicates={total.duplicates_dropped} "
        f"added={total.sentences_written}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


