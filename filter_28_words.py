import os
import glob

def process_file(filepath):
    print(f"Processing {filepath}...")
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    filtered = []
    for line in lines:
        sentence = line.strip()
        if not sentence:
            continue
        # Count words (strip trailing punctuation)
        words = sentence.rstrip(' ።').strip().split()
        if 15 <= len(words) <= 28:
            filtered.append(sentence)
            
    # Remove duplicates while preserving order
    filtered = list(dict.fromkeys(filtered))
    
    # Formulate output filename
    base_name = os.path.basename(filepath)
    if "15_to_50_words" in base_name:
        new_name = base_name.replace("15_to_50_words", "15_to_28_words")
    elif "20_to_50_words" in base_name:
        new_name = base_name.replace("20_to_50_words", "15_to_28_words")
    else:
        new_name = base_name.rsplit(".", 1)[0] + "_15_to_28_words.txt"
        
    out_path = os.path.join(os.path.dirname(filepath), new_name)
    with open(out_path, "w", encoding="utf-8") as f:
        for s in filtered:
            f.write(s + "\n")
            
    print(f"Saved {len(filtered)} sentences to {out_path}")

def main():
    target_files = glob.glob("data/*_15_to_50_words.txt") + glob.glob("data/*_20_to_50_words.txt")
    for filepath in target_files:
        process_file(filepath)

if __name__ == "__main__":
    main()
