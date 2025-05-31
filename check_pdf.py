#!/usr/bin/env python3
import sys
from pathlib import Path
import PyPDF2
import fitz

def check_pdf(pdf_path):
    print(f"Analyzing PDF: {pdf_path}")
    print(f"File size: {Path(pdf_path).stat().st_size} bytes")
    
    # Check with PyPDF2
    print("\n=== PyPDF2 Analysis ===")
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            print(f"Pages: {len(reader.pages)}")
            print(f"Encrypted: {reader.is_encrypted}")
            
            # Try to extract text from first page
            if len(reader.pages) > 0:
                first_page_text = reader.pages[0].extract_text()
                print(f"First page text length: {len(first_page_text)}")
                if first_page_text:
                    print(f"Sample text: {first_page_text[:200]}...")
                else:
                    print("No text extracted from first page")
                    
            if reader.metadata:
                print(f"Title: {reader.metadata.get('/Title', 'N/A')}")
                print(f"Author: {reader.metadata.get('/Author', 'N/A')}")
    except Exception as e:
        print(f"PyPDF2 error: {e}")
    
    # Check with PyMuPDF
    print("\n=== PyMuPDF Analysis ===")
    try:
        doc = fitz.open(pdf_path)
        print(f"Pages: {len(doc)}")
        print(f"Needs password: {doc.needs_pass}")
        print(f"Is PDF: {doc.is_pdf}")
        
        # Check first page for content type
        if len(doc) > 0:
            page = doc[0]
            text = page.get_text()
            images = page.get_images()
            print(f"First page text length: {len(text)}")
            print(f"First page images: {len(images)}")
            if len(text) > 0:
                print(f"Sample text: {text[:200]}...")
            else:
                print("No extractable text found - might be scanned/image-based")
        
        doc.close()
    except Exception as e:
        print(f"PyMuPDF error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_pdf.py path/to/pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    if not Path(pdf_path).exists():
        print(f"File not found: {pdf_path}")
        sys.exit(1)
    
    check_pdf(pdf_path)
