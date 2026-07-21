# Corpus Output

The default corpus is `data/amharic_sentences.jsonl`. Every UTF-8 line is an independent JSON object containing `sentence`, `source`, `url`, `published_date`, `word_count`, `char_count`, and `scraped_at`.

The default state database is `data/scraper_state.sqlite3`. It stores processed article URLs and sentence hashes. Keep it with the corpus so repeated runs remain idempotent.

## Read JSONL

```python
import json

with open("data/amharic_sentences.jsonl", encoding="utf-8") as corpus:
    records = [json.loads(line) for line in corpus if line.strip()]

print(len(records))
print(records[0]["sentence"])
```

## Export text only

```bash
python examples/export_text.py data/amharic_sentences.jsonl data/sentences.txt
```

Use `--min-words` and `--max-words` to create approximate duration buckets. Word counts are duration estimates and are not audio timestamps.
