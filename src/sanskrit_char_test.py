import fitz  # PyMuPDF
import os
from typing import Optional, Dict, List
import re


class PDFUtils:
    """
    Utility functions for PDF text processing, especially Sanskrit character corrections
    """
    
    @staticmethod
    def char_map(text: str) -> str:
        """
        Replace special Sanskrit characters with proper Unicode equivalents
        
        Args:
            text (str): Raw text with encoding issues
            
        Returns:
            str: Text with corrected Sanskrit characters
        """
        corrections = {
            # Vowels and diacritics
            'å': 'ā',          # long a
            'î': 'ī',          # long i
            'ü': 'ū',          # long u
            'Å': 'Ā',          # long A
            'Î': 'Ī',          # long I
            'Ü': 'Ū',          # long U
            
            # Consonants
            '√': 'v',          # v sound
            'ç': 'ś',          # sha
            'Ç': 'Ś',          # Sha
            'ß': 'ṣ',          # retroflex s (your original issue)
            'þ': 'ṭ',          # retroflex t
            'Þ': 'Ṭ',          # retroflex T
            'ð': 'ḍ',          # retroflex d
            'Ð': 'Ḍ',          # retroflex D
            'ñ': 'ñ',          # nya (already correct, but ensuring)
            'Ñ': 'Ñ',          # Nya
            
            # Nasals and special chars
            '¤': 'ṅ',          # nga
            '¥': 'ṅ',          # alternative nga
            'õ': 'ṃ',          # anusvara
            'Õ': 'Ṃ',          # Anusvara
            '×': 'ḥ',          # visarga
            '¿': 'ḥ',          # alternative visarga
            
            # R-related
            'æ': 'ṛ',          # vocalic r
            'Æ': 'Ṛ',          # vocalic R
            'è': 'ṝ',          # long vocalic r
            'È': 'Ṝ',          # long vocalic R
            
            # L-related
            'ø': 'ḷ',          # vocalic l
            'Ø': 'Ḷ',          # vocalic L
            
            # Common misencoded characters
            'à': 'ā',          # alternative long a
            'á': 'ā',          # another alternative
            'ì': 'ī',          # alternative long i
            'í': 'ī',          # another alternative
            'ù': 'ū',          # alternative long u
            'ú': 'ū',          # another alternative
            
            # Special symbols that might appear
            '¢': 'c',          # cent symbol misread as c
            '£': 'ḷ',          # pound symbol as l
            '§': 'ṣ',          # section symbol as retroflex s
            '¨': 'ü',          # diaeresis
            '©': 'c',          # copyright as c
            '®': 'r',          # registered as r
            '°': 'o',          # degree as o
            '²': '2',          # superscript 2
            '³': '3',          # superscript 3
            
            # Common punctuation fixes
            '"': '"',          # smart quote start
            '"': '"',          # smart quote end
            ''': "'",          # smart apostrophe start  
            ''': "'",          # smart apostrophe end
            '–': '-',          # en dash
            '—': '-',          # em dash
            '…': '...',        # ellipsis
        }
        
        if not text:
            return ""
        
        # Apply all corrections
        corrected_text = text
        for wrong, correct in corrections.items():
            corrected_text = corrected_text.replace(wrong, correct)
        
        return corrected_text
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Additional text cleaning for spiritual texts
        
        Args:
            text (str): Text to clean
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page headers/footers that might be artifacts
        text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
        
        # Clean up common PDF artifacts
        text = text.replace('\x0c', '')  # Form feed
        text = text.replace('\x00', '')  # Null character
        
        return text.strip()


class SpiritualPDFExtractor:
    """
    PDF text extractor specialized for spiritual/Sanskrit texts using page labels
    """
    
    def __init__(self, pdf_name: str, pdf_folder: str = "data/pdfs"):
        """
        Initialize the PDF extractor
        
        Args:
            pdf_name (str): Name of the PDF file (with or without .pdf extension)
            pdf_folder (str): Relative folder path containing PDFs
        """
        self.pdf_name = pdf_name if pdf_name.endswith('.pdf') else f"{pdf_name}.pdf"
        self.pdf_path = os.path.join(pdf_folder, self.pdf_name)
        self.doc = None
        self.page_labels = {}  # Map page labels to page numbers
        self.total_pages = 0
        
        self._load_pdf()
        self._extract_page_labels()
    
    def _load_pdf(self) -> bool:
        """
        Load the PDF document
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(self.pdf_path):
                print(f"Error: PDF file not found at {self.pdf_path}")
                return False
            
            self.doc = fitz.open(self.pdf_path)
            self.total_pages = len(self.doc)
            print(f"Successfully loaded: {self.pdf_name}")
            print(f"Total pages: {self.total_pages}")
            return True
            
        except Exception as e:
            print(f"Error loading PDF: {e}")
            return False
    
    def _extract_page_labels(self):
        """
        Extract page labels from the PDF if available
        Maps page labels to actual page numbers (0-indexed internally)
        """
        if not self.doc:
            return
        
        try:
            # Get page labels if they exist
            labels = self.doc.get_page_labels()
            
            if labels:
                for i, label in enumerate(labels):
                    self.page_labels[label] = i
                print(f"Found {len(labels)} page labels")
                
                # Show some examples
                sample_labels = list(self.page_labels.keys())[:10]
                print(f"Sample labels: {sample_labels}")
            else:
                # Create default numeric labels
                for i in range(self.total_pages):
                    self.page_labels[str(i + 1)] = i
                print("No page labels found, using page numbers")
                
        except Exception as e:
            print(f"Error extracting page labels: {e}")
            # Fallback to page numbers
            for i in range(self.total_pages):
                self.page_labels[str(i + 1)] = i
    
    def get_available_labels(self) -> List[str]:
        """
        Get list of available page labels
        
        Returns:
            List[str]: Available page labels
        """
        return list(self.page_labels.keys())
    
    def find_page_by_label(self, page_label: str) -> Optional[int]:
        """
        Find page number by label
        
        Args:
            page_label (str): Page label to search for
            
        Returns:
            Optional[int]: Page number (0-indexed) or None if not found
        """
        # Direct match
        if page_label in self.page_labels:
            return self.page_labels[page_label]
        
        # Try case-insensitive match
        for label, page_num in self.page_labels.items():
            if label.lower() == page_label.lower():
                return page_num
        
        # Try partial match
        matches = [label for label in self.page_labels.keys() if page_label.lower() in label.lower()]
        if matches:
            print(f"Partial matches found: {matches}")
            return self.page_labels[matches[0]]
        
        return None
    
    def extract_by_label(self, page_label: str, apply_corrections: bool = True) -> Optional[str]:
        """
        Extract text from a page using its label
        
        Args:
            page_label (str): Page label (e.g., "257", "xvii", "Introduction")
            apply_corrections (bool): Whether to apply Sanskrit character corrections
            
        Returns:
            Optional[str]: Extracted and corrected text
        """
        page_num = self.find_page_by_label(page_label)
        
        if page_num is None:
            print(f"Page label '{page_label}' not found")
            print(f"Available labels: {self.get_available_labels()[:20]}...")
            return None
        
        try:
            page = self.doc[page_num]
            text = page.get_text()
            
            if apply_corrections:
                # Apply Sanskrit character corrections
                text = PDFUtils.char_map(text)
                text = PDFUtils.clean_text(text)
            
            return text
            
        except Exception as e:
            print(f"Error extracting page with label '{page_label}': {e}")
            return None
    
    def extract_range_by_labels(self, start_label: str, end_label: str, apply_corrections: bool = True) -> Optional[str]:
        """
        Extract text from a range of pages using labels
        
        Args:
            start_label (str): Starting page label
            end_label (str): Ending page label
            apply_corrections (bool): Whether to apply Sanskrit character corrections
            
        Returns:
            Optional[str]: Combined extracted text
        """
        start_page = self.find_page_by_label(start_label)
        end_page = self.find_page_by_label(end_label)
        
        if start_page is None or end_page is None:
            print(f"Could not find range: {start_label} to {end_label}")
            return None
        
        if start_page > end_page:
            start_page, end_page = end_page, start_page
            print(f"Swapped range order: now extracting from {end_label} to {start_label}")
        
        combined_text = []
        
        for page_num in range(start_page, end_page + 1):
            try:
                page = self.doc[page_num]
                text = page.get_text()
                
                if apply_corrections:
                    text = PDFUtils.char_map(text)
                    text = PDFUtils.clean_text(text)
                
                if text.strip():
                    combined_text.append(f"--- Page {page_num + 1} ---\n{text}")
                    
            except Exception as e:
                print(f"Error extracting page {page_num + 1}: {e}")
                continue
        
        return "\n\n".join(combined_text)
    
    def print_page_by_label(self, page_label: str, max_chars: int = 2000):
        """
        Print content of a page identified by label
        
        Args:
            page_label (str): Page label
            max_chars (int): Maximum characters to display
        """
        page_num = self.find_page_by_label(page_label)
        
        if page_num is None:
            print(f"Page label '{page_label}' not found")
            return
        
        print(f"\n{'='*60}")
        print(f"PAGE LABEL: {page_label} (Physical Page: {page_num + 1})")
        print(f"{'='*60}")
        
        text = self.extract_by_label(page_label, apply_corrections=True)
        
        if text:
            if len(text) > max_chars:
                text = text[:max_chars] + "\n... (truncated)"
            print(text)
        else:
            print("No content found or error occurred")
        
        print(f"{'='*60}\n")
    
    def search_by_content(self, search_term: str, apply_corrections: bool = True) -> List[Dict]:
        """
        Search for content and return page labels where found
        
        Args:
            search_term (str): Term to search for
            apply_corrections (bool): Whether to apply corrections before searching
            
        Returns:
            List[Dict]: Results with page labels and context
        """
        results = []
        search_term_lower = search_term.lower()
        
        # Reverse lookup: page number to label
        num_to_label = {v: k for k, v in self.page_labels.items()}
        
        for page_num in range(self.total_pages):
            try:
                page = self.doc[page_num]
                text = page.get_text()
                
                if apply_corrections:
                    text = PDFUtils.char_map(text)
                
                if search_term_lower in text.lower():
                    # Find context
                    index = text.lower().find(search_term_lower)
                    start = max(0, index - 50)
                    end = min(len(text), index + len(search_term) + 50)
                    context = text[start:end].strip()
                    
                    page_label = num_to_label.get(page_num, str(page_num + 1))
                    
                    results.append({
                        'page_label': page_label,
                        'page_number': page_num + 1,
                        'context': context
                    })
                    
            except Exception as e:
                print(f"Error searching page {page_num + 1}: {e}")
                continue
        
        return results
    
    def close(self):
        """Close the PDF document"""
        if self.doc:
            self.doc.close()
            print("PDF document closed")


def main():
    """
    Main function to test the SpiritualPDFExtractor
    """
    print("Spiritual PDF Text Extractor")
    print("=" * 50)
    
    # Get PDF name from user
    pdf_name = input("Enter PDF name (without .pdf extension): ").strip()
    if not pdf_name:
        pdf_name = "Bhakti-Rasamrta-Sindhu-Bindu"  # Default
        print(f"Using default: {pdf_name}")
    
    # Initialize extractor
    extractor = SpiritualPDFExtractor(pdf_name)
    
    if extractor.doc is None:
        print("Failed to load PDF. Exiting.")
        return
    
    # Show available labels
    labels = extractor.get_available_labels()
    print(f"\nAvailable page labels (showing first 20): {labels[:20]}")
    if len(labels) > 20:
        print(f"... and {len(labels) - 20} more")
    
    # Test character mapping function
    print(f"\n1. Testing character mapping function:")
    test_text = "Kßobha råga î ç √ þ ð ñ"
    corrected = PDFUtils.char_map(test_text)
    print(f"   Original: {test_text}")
    print(f"   Corrected: {corrected}")
    
    # Interactive testing
    print(f"\n2. Interactive page extraction:")
    
    try:
        while True:
            page_label = input(f"\nEnter page label (e.g., '257', 'xvii') or 'q' to quit: ").strip()
            
            if page_label.lower() == 'q':
                break
            
            if not page_label:
                continue
            
            # Show both raw and corrected versions
            print("\n--- RAW TEXT (no corrections) ---")
            raw_text = extractor.extract_by_label(page_label, apply_corrections=False)
            if raw_text:
                preview = raw_text[:500] + "..." if len(raw_text) > 500 else raw_text
                print(preview)
            
            print("\n--- CORRECTED TEXT (with Sanskrit fixes) ---")
            extractor.print_page_by_label(page_label, max_chars=1500)
            
            # Search test
            search_test = input("Enter search term to test (or press Enter to skip): ").strip()
            if search_test:
                results = extractor.search_by_content(search_test)
                if results:
                    print(f"\nFound '{search_test}' on {len(results)} page(s):")
                    for result in results[:3]:
                        print(f"   Page {result['page_label']}: ...{result['context']}...")
                else:
                    print(f"'{search_test}' not found")
                    
    except KeyboardInterrupt:
        print("\nExiting...")
    
    # Close the PDF
    extractor.close()
    print("\nTest completed!")


if __name__ == "__main__":
    main()