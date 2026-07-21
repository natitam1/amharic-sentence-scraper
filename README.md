# Amharic Sentence Scraper

Amharic Sentence Scraper is an open-source Python pipeline that discovers Amharic news articles and converts them into clean, standalone sentences for language-model and text-to-speech text datasets.

It writes UTF-8 JSONL, records source attribution, estimates duration through word count, removes exact and near duplicates, respects `robots.txt`, rate-limits each domain, and remembers completed articles so scheduled runs can resume safely.

This repository contains software, not a redistributed news corpus. Users are responsible for reviewing every source's current terms, robots policy, copyright restrictions, and permitted data uses.

## Features

- Amharic-aware boundaries for `።`, `፡፡`, `!`, and `?`
- Configurable 5 to 90 word default range
- Ethiopic Unicode script-ratio validation
- Boilerplate, link, email, hashtag, and fragment rejection
- Exact SHA-256 and bounded near-duplicate detection
- RSS, sitemap, and category-page URL discovery
- Configurable HTML body and removal selectors
- Per-domain delays, retries, timeouts, and robots enforcement
- JSONL records with source, URL, dates, word count, and character count
- SQLite state for article and sentence idempotency
- Per-source summaries and random QA samples
- Shared adapter contract for future captions and transcripts

## Requirements

- Python 3.11 or newer
- Internet access for live collection
- Disk space for JSONL output and SQLite state
- A real contact address in the crawler User-Agent

## Installation

```bash
git clone https://github.com/natitam1/amharic-sentence-scraper.git
cd amharic-sentence-scraper
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Linux or macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Verify the installation:

```bash
python main.py --list-sources
python -m unittest discover -s tests -v
```

## Configure Before Running

Edit `config.yaml` and replace the example contact address:

```yaml
user_agent: "AmharicSentenceResearchBot/1.0 (+mailto:you@example.com)"
```

Do not impersonate a browser. A descriptive User-Agent lets site operators identify and contact the crawler.

List configured sources and their enabled state:

```bash
python main.py --list-sources
```

Some source definitions are disabled because their live terms, robots rules, discovery endpoints, URL patterns, and HTML selectors require manual review before use.

## First Safe Collection

Start with one source and a small limit:

```bash
python main.py --sources bbc_amharic --max-articles 3 --sample 20
```

This command checks robots policy, discovers URLs, fetches no more than three unprocessed articles, extracts text, segments Amharic sentences, applies quality filters, removes duplicates, writes JSONL records, updates SQLite state, and prints a random sample.

## Collection Commands

Run all enabled sources, limiting each source to 25 discovered articles:

```bash
python main.py --max-articles 25
```

Run selected sources:

```bash
python main.py --sources bbc_amharic voa_amharic dw_amharic --max-articles 50
```

Filter feed entries by date when the feed provides usable dates:

```bash
python main.py --since 2026-07-01 --max-articles 100
```

Print detailed logs:

```bash
python main.py --verbose --max-articles 10
```

Use another configuration file:

```bash
python main.py --config path/to/config.yaml --max-articles 5
```

`--max-articles` applies separately to every selected source.

## Where the Sentences Are

The default corpus is:

```text
data/amharic_sentences.jsonl
```

Each line is one complete UTF-8 JSON object:

```json
{"sentence":"ኢትዮጵያ አዲስ የምርምር ፕሮግራም ዛሬ ይፋ አደረገች።","source":"bbc_amharic","url":"https://www.bbc.com/amharic/articles/example","published_date":"2026-07-21","word_count":9,"char_count":55,"scraped_at":"2026-07-21T10:04:00Z"}
```

The persistent state database is:

```text
data/scraper_state.sqlite3
```

Keep both files together. The database prevents processed articles and known sentence hashes from being collected again.

## Get Plain Sentences

Export every JSONL sentence to a UTF-8 text file with one sentence per line:

```bash
python examples/export_text.py data/amharic_sentences.jsonl data/sentences.txt
```

Export exactly 1,000 sentences:

```bash
python examples/export_text.py data/amharic_sentences.jsonl data/sentences_1000.txt --limit 1000
```

Export only sentences containing 20 to 90 words:

```bash
python examples/export_text.py data/amharic_sentences.jsonl data/sentences_20_90.txt --min-words 20 --max-words 90
```

Read the corpus directly in Python:

```python
import json

with open("data/amharic_sentences.jsonl", encoding="utf-8") as corpus:
    for line in corpus:
        record = json.loads(line)
        print(record["sentence"], record["word_count"])
```

## Sentence Length and Duration

`filter.min_words` and `filter.max_words` in `config.yaml` control accepted length. Defaults are 5 and 90 whitespace-delimited words. Short complete sentences are retained. The upper bound approximates a 30-second spoken ceiling.

Long sentences are discarded, never truncated or merged. Every record includes `word_count` and `char_count`, allowing downstream duration buckets without another crawl. Word-count duration is an estimate, not an audio timestamp.

## Resuming and Repeated Runs

Run the same collection command later to collect newly discovered articles:

```bash
python main.py --max-articles 100
```

Processed URLs are skipped. Failed URLs remain eligible for another attempt. Sentence hashes persist across runs.

Back up these together before moving collection to another machine:

```text
data/amharic_sentences.jsonl
data/scraper_state.sqlite3
```

Deleting the database causes known article URLs to be fetched again. Starting with a fresh database does not automatically import hashes from an existing JSONL file.

## Quality Assurance

Request a random sample after collection:

```bash
python main.py --max-articles 20 --sample 20
```

Review samples for grammatical completeness, correct Amharic script, terminal punctuation, sensible word counts, and absence of menus, captions, subscription prompts, copyright text, URLs, emails, and social tags.

A source that suddenly produces almost no accepted sentences usually needs updated discovery URLs or HTML selectors.

## Important Configuration Values

- `filter.min_words`: minimum sentence words
- `filter.max_words`: maximum sentence words
- `filter.min_ethiopic_ratio`: required Ethiopic share among letters
- `filter.blocklist`: site chrome and boilerplate phrases
- `dedup.similarity_threshold`: near-duplicate strictness
- `http.default_delay_seconds`: fallback delay per domain
- `http.robots.fail_closed`: block fetching when robots policy is unavailable
- `sources.*.body_selectors`: ordered article-body selectors
- `sources.*.remove_selectors`: unwanted page elements

See `docs/CONFIGURATION.md` for details.

## Scheduling

Linux cron example for a daily run at 02:15:

```cron
15 2 * * * cd /path/to/amharic-sentence-scraper && .venv/bin/python main.py --max-articles 100 >> data/scraper.log 2>&1
```

Windows Task Scheduler settings:

```text
Program: C:\path\to\amharic-sentence-scraper\.venv\Scripts\python.exe
Arguments: main.py --max-articles 100
Start in: C:\path\to\amharic-sentence-scraper
```

Do not overlap runs that write to the same JSONL and SQLite files.

## Adding a News Source

Prefer the generic adapter for RSS, sitemap, or category discovery. Add a source block to `config.yaml` with `enabled: false`, verify current terms and robots rules, use restrictive article URL patterns, add article-body selectors, and test with a small limit and QA sample before enabling it.

Create a new adapter only when source-specific discovery or extraction cannot be represented in configuration. Every adapter returns `RawArticle`, allowing future YouTube, Telegram, and podcast sources to reuse segmentation, filtering, normalization, deduplication, and storage.

## YouTube Podcast Collection

The `youtube_playlist` adapter supports playlist and channel video-tab URLs through `yt-dlp`. It downloads captions only and never downloads video or audio.

```bash
python main.py --sources meri_podcast_videos --max-articles 1 --sample 20
python examples/export_text.py data/amharic_sentences.jsonl data/meri_podcast_1000_words.txt --sources meri_podcast_videos --content-types podcast --max-total-words 1000
```

See `docs/YOUTUBE.md` for metadata, caption behavior, authentication, and responsible-use notes.

## Testing

Run the offline suite:

```bash
python -m unittest discover -s tests -v
```

Live checks should always begin with a small `--max-articles` value.

## Troubleshooting

Start with:

```bash
python main.py --verbose --sources SOURCE_ID --max-articles 1
```

Common failures include changed feeds, changed article markup, restrictive robots policy, JavaScript-rendered content, temporary HTTP errors, and selectors that no longer target the article body.

## Natural and Mixed Sources

Place authorized UTF-8 podcast, interview, radio, story, lecture, drama, educational, or community transcripts under the matching `input/` folder. TXT, JSONL, SRT, and VTT are supported.

```bash
python main.py --sources local_podcast_transcripts --sample 20
python main.py --content-types podcast interview radio story --max-sentences-per-type 5000
```

Every new record includes `content_type`. Existing records are treated as `news`. Export selected categories with:

```bash
python examples/export_text.py data/amharic_sentences.jsonl data/natural.txt --content-types podcast interview radio story --limit 10000
```

See `docs/MIXED_SOURCES.md` for folder layout, permissions, balancing, and transcript preparation.

## Project Structure

```text
scraper/
  adapters/       Source discovery and article adapters
  pipeline/       Fetch, extract, segment, normalize, filter, deduplicate
  storage/        JSONL and SQLite persistence
config.yaml       Source and pipeline settings
main.py           Command-line orchestration
examples/         Corpus export utilities
tests/            Offline regression tests
docs/             Detailed configuration and output guides
```

## Legal and Ethical Use

Respect source terms, robots policy, request capacity, copyright, and dataset restrictions. Prefer official feeds and APIs. Do not bypass access controls. Keep request rates conservative. Sentence-level storage with attribution does not remove the user's responsibility to assess whether collection and downstream use are permitted.

## Contributing and Security

Read `CONTRIBUTING.md` before opening a pull request. Report sensitive vulnerabilities according to `SECURITY.md`. Community participation is governed by `CODE_OF_CONDUCT.md`.

## License

The software is available under the MIT License. See `LICENSE`.

