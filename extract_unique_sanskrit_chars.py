
import fitz  # PyMuPDF
import json
import unicodedata
from collections import defaultdict
from pathlib import Path

# Inline list of non-Sanskrit punctuation or symbols to exclude
EXCLUDE_CHARS = set([
    '•', '’', '“', '”', '`', '~', '@', '&', '|', '<', '>', '=', '_', '¬', '^', '°', '¶',
    '–', '—', '-', '…', '©', '®', '™', '′', '″', '‹', '›', '§', '†', '‡', '·',
    '×', '÷', '¤', '€', '$', '#', '%', '*', '±'
])

SAFE_PUNCTUATION = set(".,:;!?()[]{}\"'")

def is_sanskrit_char(c):
    if c in EXCLUDE_CHARS:
        return False
    if c.isascii() and (c.isalnum() or c in SAFE_PUNCTUATION):
        return False
    if unicodedata.category(c).startswith('C'):  # control characters
        return False
    return True

def collect_unique_chars(pdf_path):
    doc = fitz.open(pdf_path)
    char_data = defaultdict(lambda: {"count": 0, "samples": set()})

    for page in doc:
        text = page.get_text()
        for i, c in enumerate(text):
            if is_sanskrit_char(c):
                char_data[c]["count"] += 1
                snippet = text[i:i+10].strip().replace("\n", " ")
                if snippet:
                    char_data[c]["samples"].add(snippet)

    for c in char_data:
        char_data[c]["samples"] = list(char_data[c]["samples"])[:5]

    return char_data

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Extract unique non-ASCII Sanskrit chars from PDFs")
    parser.add_argument("input_dir", help="Folder containing PDF files")
    parser.add_argument("output_file", help="Path to save JSON output")
    args = parser.parse_args()

    input_path = Path(args.input_dir)
    all_chars = {}

    for pdf_file in input_path.glob("*.pdf"):
        print(f"Processing: {pdf_file.name}")
        chars = collect_unique_chars(pdf_file)
        for c, meta in chars.items():
            if c not in all_chars:
                all_chars[c] = {"count": 0, "samples": []}
            all_chars[c]["count"] += meta["count"]
            all_chars[c]["samples"].extend(meta["samples"])

    for c in all_chars:
        all_chars[c]["samples"] = list(set(all_chars[c]["samples"]))[:5]

    with open(args.output_file, "w", encoding="utf-8") as f:
        json.dump(all_chars, f, ensure_ascii=False, indent=2)

    print(f"✅ Unique character map written to {args.output_file}")

if __name__ == "__main__":
    main()
