#!/usr/bin/env python3
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.text_processor import TextProcessor
import fitz

def test_text_processing(pdf_path):
    print("Testing text processing pipeline...")
    
    # Extract raw text
    doc = fitz.open(pdf_path)
    raw_text = ""
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        raw_text += f"\n--- PAGE {page_num + 1} ---\n"
        raw_text += text
    doc.close()
    
    print(f"Raw text: {len(raw_text)} characters, {len(raw_text.split())} words")
    
    # Test text processor
    processor = TextProcessor()
    cleaned_text = processor.clean_text(raw_text)
    
    print(f"Cleaned text: {len(cleaned_text)} characters, {len(cleaned_text.split())} words")
    print(f"Sample cleaned text: {cleaned_text[:300]}...")
    
    # Test paragraph splitting
    paragraphs = processor.split_into_paragraphs(cleaned_text)
    print(f"Paragraphs: {len(paragraphs)}")
    
    if paragraphs:
        print(f"First paragraph length: {len(paragraphs[0])}")
        print(f"First paragraph: {paragraphs[0][:200]}...")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_text_processor.py path/to/pdf")
        sys.exit(1)
    
    test_text_processing(sys.argv[1])
