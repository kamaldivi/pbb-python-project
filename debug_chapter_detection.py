#!/usr/bin/env python3
import sys
from pathlib import Path
import re

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.text_processor import TextProcessor
import fitz

def debug_chapter_detection(pdf_path):
    print("Debugging chapter detection...")
    
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
    
    print(f"Cleaned text length: {len(cleaned_text)}")
    
    # Test the patterns manually
    chapter_patterns = [
        r'^(\d+\.?\s+[A-Z][A-Za-z\s]+)$',
        r'^([A-Z][A-Z\s]{5,50})$',
        r'^(Abstract|Introduction|Related Work|Method|Results|Conclusion|References|Acknowledgments)$',
        r'^(\d+\.\d+\.?\s+.+)$',
        r'(?:CHAPTER|Chapter)\s+(\d+|[IVX]+)[\s\-:]*(.+?)(?=\n)',
        r'(?:Chapter|CHAPTER)\s+(.+?)(?=\n)',
        r'^\d+\.\s+(.+?)(?=\n)',
    ]
    
    lines = cleaned_text.split('\n')
    print(f"Total lines: {len(lines)}")
    
    # Look for potential chapter headers in first 50 lines
    print("\nFirst 50 lines (looking for chapter headers):")
    potential_headers = []
    
    for i, line in enumerate(lines[:50]):
        line = line.strip()
        if not line or line.startswith('--- PAGE'):
            continue
            
        print(f"Line {i+1}: '{line}'")
        
        # Test each pattern
        for j, pattern in enumerate(chapter_patterns):
            try:
                match = re.match(pattern, line, re.IGNORECASE)
                if match and len(line) > 3 and len(line) < 100:
                    potential_headers.append((line, f"Pattern {j+1}"))
                    print(f"  ✅ MATCHES Pattern {j+1}: {pattern}")
                    break
            except Exception as e:
                print(f"  ❌ Pattern {j+1} error: {e}")
    
    print(f"\nPotential headers found: {len(potential_headers)}")
    for header, pattern in potential_headers:
        print(f"  - '{header}' (matched by {pattern})")
    
    # Check if fallback creates content correctly  
    print(f"\nTesting fallback single chapter creation...")
    all_content = '\n'.join(line for line in lines if not re.match(r'--- PAGE \d+ ---', line))
    print(f"Fallback content length: {len(all_content)} characters")
    print(f"Fallback word count: {len(all_content.split())} words")
    if all_content:
        print(f"Sample fallback content: {all_content[:200]}...")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_chapter_detection.py path/to/pdf")
        sys.exit(1)
    
    debug_chapter_detection(sys.argv[1])