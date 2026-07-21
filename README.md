# Amharic Sentence Scraper

A polite, restart-safe Python pipeline for collecting standalone Amharic
sentences from news sites into JSONL.

## Setup

```powershell
cd C:\Users\lead\Desktop\amharic-sentence-scraper
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

Inspect configured sources without fetching articles:

```powershell
python main.py --list-sources
```

Run enabled sources:

```powershell
python main.py --max-articles 25
```

Run selected sources and print a random QA sample:

```powershell
python main.py --sources bbc_amharic voa_amharic --max-articles 20 --sample 20
```

The crawler checks `robots.txt` before every URL, applies a per-domain delay,
uses bounded retries, and skips previously processed articles. Output defaults
to `data/amharic_sentences.jsonl`; persistent state is stored in
`data/scraper_state.sqlite3`.

Source URLs, extraction selectors, rate limits, filter thresholds, and
boilerplate patterns are all maintained in `config.yaml`.

## Tests

```powershell
python -m unittest discover -s tests -v
```

## Notes

- A source is skipped when robots policy cannot be established and
  `robots.fail_closed` is enabled.
- Review each site's terms before enabling it. RSS permission does not
  automatically imply permission to scrape linked article pages.
- Site selectors and feed endpoints change. A sudden near-zero yield is
  reported and usually means the source config needs updating.

