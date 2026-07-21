# Troubleshooting

## No discovered URLs

Run with `--verbose`. Confirm that the feed or sitemap exists and that `article_url_patterns` match current links.

## Robots blocks a URL

Do not bypass the policy. Verify the path and configured User-Agent against the current `robots.txt`, or use an official API or feed that permits the intended access.

## Articles produce zero sentences

Update `body_selectors` after inspecting current HTML. The fetcher does not execute JavaScript, so client-rendered article bodies require another permitted source mechanism.

## Output looks corrupted

Use a UTF-8 terminal and open JSONL or text output explicitly as UTF-8. The CLI configures Windows standard output for UTF-8.

## Old failures run again

Only successfully processed URLs are skipped. Failed URLs remain eligible so temporary network and server errors can recover.
