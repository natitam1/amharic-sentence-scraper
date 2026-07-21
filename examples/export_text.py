"""Export filtered sentence strings from a JSONL corpus to UTF-8 text."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("input", type=Path)
parser.add_argument("output", type=Path)
parser.add_argument("--min-words", type=int, default=0)
parser.add_argument("--max-words", type=int)
parser.add_argument("--limit", type=int, help="Maximum number of sentences to export")
parser.add_argument("--max-total-words", type=int, help="Maximum total words without truncating sentences")
parser.add_argument("--sources", nargs="+", help="Only export these source IDs")
parser.add_argument("--content-types", nargs="+", help="Only export these content types")
args = parser.parse_args()
if args.limit is not None and args.limit < 1:
    parser.error("--limit must be at least 1")
source_filter = set(args.sources or ())
type_filter = set(args.content_types or ())
args.output.parent.mkdir(parents=True, exist_ok=True)
written = 0
total_words = 0
with args.input.open(encoding="utf-8") as source, args.output.open("w", encoding="utf-8") as destination:
    for line in source:
        if not line.strip():
            continue
        record = json.loads(line)
        count = int(record["word_count"])
        content_type = record.get("content_type", "news")
        if count < args.min_words or (args.max_words is not None and count > args.max_words):
            continue
        if source_filter and record.get("source") not in source_filter:
            continue
        if type_filter and content_type not in type_filter:
            continue
        if args.max_total_words is not None and total_words + count > args.max_total_words:
            continue
        destination.write(record["sentence"] + "\n")
        written += 1
        total_words += count
        if args.limit is not None and written >= args.limit:
            break
print(f"Wrote {written} sentences and {total_words} words to {args.output}")
