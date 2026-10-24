#!/usr/bin/env python3
"""
Script to split long lines (>30 words) in an Amharic text file.
Splits at Amharic sentence-ending punctuation marks.
Each split part replaces the original long line in place.
"""

import re
import sys
import os

INPUT_FILE = r"data\new_pro.txt"
OUTPUT_FILE = r"data\new_pro.txt"

WORD_THRESHOLD = 30
MIN_WORDS_PER_PART = 4  # Don't create parts shorter than this


def count_words(text):
    """Count words in text."""
    return len(text.split())


def try_split(line, pattern):
    """
    Try to split a line using a regex pattern that matches a delimiter.
    The delimiter stays attached to the text BEFORE it.
    Returns list of parts, or [line] if splitting isn't useful.
    """
    # Use re.split but keep the delimiter
    # We split on the pattern, keeping the delimiter with the left side
    parts = re.split(pattern, line)
    
    if len(parts) <= 1:
        return [line]
    
    # re.split with a capturing group alternates text and delimiters
    # Recombine: attach delimiter to preceding text
    combined = []
    i = 0
    while i < len(parts):
        if i + 1 < len(parts):
            combined.append(parts[i] + parts[i+1])
            i += 2
        else:
            combined.append(parts[i])
            i += 1
    
    # Filter empty
    combined = [p.strip() for p in combined if p.strip()]
    
    if len(combined) <= 1:
        return [line]
    
    # Merge very short parts with the next one
    merged = []
    buf = combined[0]
    for j in range(1, len(combined)):
        if count_words(buf) < MIN_WORDS_PER_PART:
            buf = buf + " " + combined[j]
        else:
            merged.append(buf)
            buf = combined[j]
    merged.append(buf)
    
    if len(merged) <= 1:
        return [line]
    
    return merged


def split_line(line):
    """
    Split a long line at sentence boundaries.
    Priority:
    1. Split at \u1362 (Amharic full stop) followed by space
    2. Split at ? or ! followed by space
    3. Split at \u1364 (Amharic semicolon) followed by space
    4. Split at \u1363 (Amharic comma) followed by space
    """
    line = line.strip()
    if not line:
        return [line]
    
    # Try primary split: Amharic full stop
    # Pattern: capture the \u1362 as delimiter
    parts = try_split(line, r'(\u1362)\s+')
    
    # If we got a good split, check if any part is still too long
    if len(parts) > 1:
        final = []
        for p in parts:
            if count_words(p) > WORD_THRESHOLD:
                # Try secondary split on this part
                sub = try_split(p, r'([?!])\s+')
                if len(sub) > 1:
                    final.extend(sub)
                else:
                    sub = try_split(p, r'(\u1364)\s+')
                    if len(sub) > 1:
                        final.extend(sub)
                    else:
                        sub = try_split(p, r'(\u1363)\s+')
                        if len(sub) > 1:
                            final.extend(sub)
                        else:
                            final.append(p)
            else:
                final.append(p)
        return final
    
    # No full stop split worked, try ? or !
    parts = try_split(line, r'([?!])\s+')
    if len(parts) > 1:
        return parts
    
    # Try semicolon
    parts = try_split(line, r'(\u1364)\s+')
    if len(parts) > 1:
        return parts
    
    # Try comma
    parts = try_split(line, r'(\u1363)\s+')
    if len(parts) > 1:
        return parts
    
    # Can't split
    return [line]


def main():
    # Read the file
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    total_lines = len(lines)
    long_line_count = 0
    split_count = 0
    new_lines = []
    
    for i, line in enumerate(lines):
        stripped = line.rstrip('\r\n')
        
        # Detect line ending
        if line.endswith('\r\n'):
            ending = '\r\n'
        elif line.endswith('\n'):
            ending = '\n'
        elif line.endswith('\r'):
            ending = '\r'
        else:
            ending = '\n'
        
        word_count = count_words(stripped)
        
        if word_count > WORD_THRESHOLD:
            long_line_count += 1
            parts = split_line(stripped)
            if len(parts) > 1:
                split_count += 1
                for part in parts:
                    new_lines.append(part + ending)
            else:
                new_lines.append(stripped + ending)
        else:
            new_lines.append(stripped + ending)
    
    # Write output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    
    # Use ascii-safe output for Windows console
    print(f"Total lines processed: {total_lines}")
    print(f"Lines with > {WORD_THRESHOLD} words: {long_line_count}")
    print(f"Lines successfully split: {split_count}")
    print(f"New total lines: {len(new_lines)}")
    print(f"Output written to: {OUTPUT_FILE}")
    
    # Show some stats about remaining long lines
    remaining_long = 0
    for nl in new_lines:
        if count_words(nl.strip()) > WORD_THRESHOLD:
            remaining_long += 1
    print(f"Remaining lines still > {WORD_THRESHOLD} words: {remaining_long}")


if __name__ == "__main__":
    main()
