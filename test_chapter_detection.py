#!/usr/bin/env python3
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.text_processor import TextProcessor
from src.parsers.pdf_parser import PDFParser
import fitz

def test_chapter_detection(pdf_path):
    print("Testing chapter detection...")
    
    # Extract and process text like the parser does
    doc = fitz.open(pdf_path)
    raw_text = ""
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        raw_text += f"\n--- PAGE {page_num + 1} ---\n"
        raw_text += text
    doc.close()
    
    processor = TextProcessor()
    cleaned_text = processor.clean_text(raw_text)
    
    print(f"Input to chapter detection: {len(cleaned_text)} characters, {len(cleaned_text.split())} words")
    
    # Test chapter detection
    parser = PDFParser(processor)
    chapters = parser._detect_chapters(cleaned_text)
    
    print(f"Chapters detected: {len(chapters)}")
    
    for i, chapter in enumerate(chapters):
        print(f"\nChapter {i+1}: '{chapter.title}'")
        print(f"  Content length: {len(chapter.content)} characters")
        print(f"  Word count: {len(chapter.content.split())} words")
        print(f"  Paragraphs: {len(chapter.paragraphs)}")
        print(f"  Pages: {chapter.page_start} to {chapter.page_end}")
        if chapter.content:
            print(f"  Sample: {chapter.content[:200]}...")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_chapter_detection.py path/to/pdf")
        sys.exit(1)
    
    test_chapter_detection(sys.argv[1])
