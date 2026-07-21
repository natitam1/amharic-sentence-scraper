# Source Adapters

Every adapter implements `BaseAdapter.list_article_urls(since=None)` and `BaseAdapter.fetch_article(url)`. The latter returns a `RawArticle` containing URL, title, publication date, and body text.

The generic news adapter supports RSS, sitemap, and category-page discovery. Prefer adding selectors and URL patterns in `config.yaml` before creating source-specific code.

To add a source, review its terms and robots policy, locate an official feed or sitemap, add the source disabled, define restrictive article patterns and body selectors, then run a three-article test with a 20-sentence sample. Enable it only after manual output review.

Future caption, Telegram, and transcript adapters should return their text through the same `RawArticle` contract so the shared pipeline remains unchanged.
