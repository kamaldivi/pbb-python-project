
from pdfminer.high_level import extract_text
import sys
from pathlib import Path

class SanskritPDFExtractor:
    def __init__(self, pdf_path):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"File not found: {self.pdf_path}")

    def extract_text_from_pages(self, start_page=0, end_page=None):
        """Extracts text from a range of pages using pdfminer.six (0-indexed)."""
        if end_page is None:
            text = extract_text(str(self.pdf_path), page_numbers=[start_page])
        else:
            pages = list(range(start_page, end_page + 1))
            text = extract_text(str(self.pdf_path), page_numbers=pages)
        return text

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Extract Sanskrit text using pdfminer.six")
    parser.add_argument("pdf_file", help="Path to the PDF file")
    parser.add_argument("--start", type=int, default=266, help="Start page (0-indexed)")
    parser.add_argument("--end", type=int, default=272, help="End page (0-indexed, inclusive)")
    args = parser.parse_args()

    extractor = SanskritPDFExtractor(args.pdf_file)
    text = extractor.extract_text_from_pages(args.start, args.end)
    print("\n--- Extracted Text ---\n")
    print(text)

if __name__ == "__main__":
    main()
