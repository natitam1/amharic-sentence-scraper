#!/usr/bin/env python3
"""Deep analysis of long lines - look at context around periods."""
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

INPUT_FILE = r"data\new_pro_backup.txt"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    lines = f.readlines()

# For the first 15 long lines, show the full text so we can see what's happening
count = 0
for i, line in enumerate(lines):
    stripped = line.strip()
    words = stripped.split()
    if len(words) > 30:
        count += 1
        if count <= 15:
            print(f"=== LINE {i+1} ({len(words)} words) ===")
            # Show positions of all periods
            positions = [j for j, ch in enumerate(stripped) if ch == '\u1362']
            print(f"Period positions: {positions}")
            print(f"Line length: {len(stripped)}")
            # Show 10 chars around each period
            for pos in positions:
                start = max(0, pos-15)
                end = min(len(stripped), pos+15)
                context = stripped[start:end]
                print(f"  Around pos {pos}: ...{context}...")
            print(f"Full text: {stripped}")
            print()
