# Contributing

Contributions that improve correctness, source coverage, documentation, or corpus quality are welcome.

## Setup

```bash
python -m venv .venv
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Create a branch from `main` and keep changes focused. When adding or repairing a source, verify its current terms, `robots.txt`, feed or sitemap, URL patterns, and extraction selectors. Prefer configuration changes when the generic adapter is sufficient. Add a source-specific adapter only when its discovery or extraction behavior requires code.

Pull requests must explain the behavior changed, verification performed, and expected corpus impact. Add regression tests for segmentation, filtering, deduplication, storage, or extraction changes. Never commit collected corpus data, state databases, credentials, cookies, or private source URLs.
