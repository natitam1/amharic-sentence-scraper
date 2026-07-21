# Configuration Reference

The scraper reads `config.yaml`. Use `--config PATH` to select another file.

## HTTP and robots

Replace the example `user_agent` email with a monitored address before sustained use. `timeout_seconds`, `retries`, and `backoff_seconds` control bounded request recovery. `default_delay_seconds` is the fallback per-domain delay, while each source may set a slower delay.

Keep `robots.enabled` and `robots.fail_closed` true. When robots policy cannot be established, fail-closed mode prevents fetching.

## Filters

`min_words` and `max_words` define the accepted range. Defaults are 5 and 90. `min_ethiopic_ratio` requires most letters to be in the Ethiopic Unicode block. `require_terminal_punctuation` requires a complete ending. Add site chrome, subscription prompts, captions, and copyright phrases to `blocklist`.

## Deduplication

Exact duplicates use SHA-256 over normalized text. Near duplicates use character trigram Jaccard similarity in bounded length and prefix buckets. A higher similarity threshold preserves more variants; a lower value removes more similar sentences.

## Sources

Each source defines an ID, enabled flag, adapter, base URL, discovery type, discovery URLs, article URL patterns, body selectors, removal selectors, and delay. Generic discovery supports `rss`, `sitemap`, and `category`. Test disabled sources manually before enabling them.
