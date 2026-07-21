"""Export sentence strings from a JSONL corpus to UTF-8 text."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("input", type=Path)
parser.add_argument("output", type=Path)
parser.add_argument("--min-words", type=int, default=0)
parser.add_argument("--max-words", type=int)
args = parser.parse_args()
args.output.parent.mkdir(parents=True, exist_ok=True)
written = 0
with args.input.open(encoding="utf-8") as source, args.output.open("w", encoding="utf-8") as destination:
    for line in source:
        if not line.strip():
            continue
        record = json.loads(line)
        count = int(record["word_count"])
        if count < args.min_words or (args.max_words is not None and count > args.max_words):
            continue
        destination.write(record["sentence"] + "\n")
        written += 1
print(f"Wrote {written} sentences to {args.output}")
