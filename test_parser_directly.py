#!/usr/bin/env python3
import sys
from pathlib import Path
import fitz

def test_direct_parsing(pdf_path):
    print(f"Testing direct parsing of: {pdf_path}")
    
    try:
        doc = fitz.open(pdf_path)
        print(f"Opened PDF with {len(doc)} pages")
        
        all_text = ""
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            print(f"Page {page_num + 1} extracted {len(text)} characters")
            if text:
                print(f"Sample from page {page_num + 1}: {text[:100]}...")
                all_text += text
        
        print(f"\nTotal text extracted: {len(all_text)} characters")
        print(f"Word count: {len(all_text.split())}")
        
        doc.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_parser_directly.py path/to/pdf")
        sys.exit(1)
    
    test_direct_parsing(sys.argv[1])
