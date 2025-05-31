import fitz  # PyMuPDF
import os
from typing import Optional, List, Dict

# Sanskrit text processing
try:
    from sanskrit_text import SanskritText
    from sanskrit_text.transliteration import transliterate
    from sanskrit_text.encoding import detect_encoding, normalize_text
    SANSKRIT_TEXT_AVAILABLE = True
except ImportError:
    print("Warning: sanskrit-text library not found. Install with: pip install sanskrit-text")
    SANSKRIT_TEXT_AVAILABLE = False


class SanskritPDFReader:
    """
    A specialized PDF reader for Sanskrit texts using PyMuPDF
    Handles encoding issues common in Sanskrit/Devanagari PDFs
    """
    
    def __init__(self, pdf_path: str):
        """
        Initialize the PDF reader with path to the PDF file
        
        Args:
            pdf_path (str): Path to the PDF file
        """
        self.pdf_path = pdf_path
        self.doc = None
        self.total_pages = 0
        self.sanskrit_char_map = {
            'ß': 'ṣ',  # Specific case mentioned
            'à': 'ā',
            'á': 'ā', 
            'ñ': 'ñ',
            'Þ': 'ṭ',
            'è': 'ī',
            'ì': 'ī',
            '¥': 'ṅ',
            'ð': 'ḍ',
            'ý': 'ñ',
            'þ': 'ṭ',
            'ø': 'ṛ',
            'ü': 'ū',
            # Add more mappings as discovered
        }
        
        self._load_pdf()
    
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
            print(f"Successfully loaded PDF: {self.pdf_path}")
            print(f"Total pages: {self.total_pages}")
            return True
            
        except Exception as e:
            print(f"Error loading PDF: {e}")
            return False
    
    def fix_sanskrit_encoding(self, text: str) -> str:
        """
        Fix common Sanskrit character encoding issues using multiple approaches
        
        Args:
            text (str): Raw extracted text
            
        Returns:
            str: Text with corrected Sanskrit characters
        """
        if not text:
            return ""
        
        # Method 1: Use sanskrit-text library if available
        if SANSKRIT_TEXT_AVAILABLE:
            try:
                # Detect and normalize encoding
                normalized_text = normalize_text(text)
                
                # Create SanskritText object for advanced processing
                sanskrit_obj = SanskritText(normalized_text)
                
                # Get properly encoded text
                processed_text = sanskrit_obj.text
                
                # If the library processing improved the text, use it
                if len(processed_text.strip()) > 0:
                    text = processed_text
                    
            except Exception as e:
                print(f"Sanskrit-text processing failed: {e}, falling back to manual mapping")
        
        # Method 2: Manual character mappings (fallback or additional processing)
        for wrong, correct in self.sanskrit_char_map.items():
            text = text.replace(wrong, correct)
        
        return text
    
    def extract_page(self, page_num: int, fix_encoding: bool = True) -> Optional[str]:
        """
        Extract text from a specific page
        
        Args:
            page_num (int): Page number (1-indexed)
            fix_encoding (bool): Whether to apply Sanskrit encoding fixes
            
        Returns:
            Optional[str]: Extracted text or None if error
        """
        if not self.doc:
            print("PDF not loaded")
            return None
        
        if page_num < 1 or page_num > self.total_pages:
            print(f"Invalid page number. Must be between 1 and {self.total_pages}")
            return None
        
        try:
            # Convert to 0-indexed for PyMuPDF
            page = self.doc[page_num - 1]
            text = page.get_text()
            
            if fix_encoding:
                text = self.fix_sanskrit_encoding(text)
            
            return text
            
        except Exception as e:
            print(f"Error extracting page {page_num}: {e}")
            return None
    
    def print_page(self, page_num: int, fix_encoding: bool = True, max_chars: int = 2000):
        """
        Print content of a specific page to console
        
        Args:
            page_num (int): Page number (1-indexed)
            fix_encoding (bool): Whether to apply Sanskrit encoding fixes
            max_chars (int): Maximum characters to display (for readability)
        """
        print(f"\n{'='*60}")
        print(f"PAGE {page_num} CONTENT")
        print(f"{'='*60}")
        
        text = self.extract_page(page_num, fix_encoding)
        
        if text:
            # Truncate if too long
            if len(text) > max_chars:
                text = text[:max_chars] + "\n... (truncated)"
            
            print(text)
        else:
            print("No content found or error occurred")
        
        print(f"{'='*60}\n")
    
    def extract_all_pages(self, fix_encoding: bool = True) -> List[str]:
        """
        Extract text from all pages
        
        Args:
            fix_encoding (bool): Whether to apply Sanskrit encoding fixes
            
        Returns:
            List[str]: List of extracted text from each page
        """
        if not self.doc:
            print("PDF not loaded")
            return []
        
        all_pages = []
        print(f"Extracting text from all {self.total_pages} pages...")
        
        for page_num in range(1, self.total_pages + 1):
            text = self.extract_page(page_num, fix_encoding)
            all_pages.append(text or "")
            
            # Show progress for large PDFs
            if page_num % 10 == 0:
                print(f"Processed {page_num}/{self.total_pages} pages")
        
        return all_pages
    
    def transliterate_text(self, text: str, target_scheme: str = "IAST") -> Optional[str]:
        """
        Transliterate Sanskrit text to different schemes using sanskrit-text library
        
        Args:
            text (str): Sanskrit text to transliterate
            target_scheme (str): Target transliteration scheme (IAST, Harvard-Kyoto, etc.)
            
        Returns:
            Optional[str]: Transliterated text or None if library not available
        """
        if not SANSKRIT_TEXT_AVAILABLE:
            print("sanskrit-text library not available for transliteration")
            return None
        
        try:
            # Create SanskritText object
            sanskrit_obj = SanskritText(text)
            
            # Transliterate to target scheme
            transliterated = transliterate(sanskrit_obj.text, target_scheme)
            return transliterated
            
        except Exception as e:
            print(f"Transliteration failed: {e}")
            return None
    
    def detect_sanskrit_encoding(self, text: str) -> Dict:
        """
        Detect encoding information about the Sanskrit text
        
        Args:
            text (str): Text to analyze
            
        Returns:
            Dict: Encoding detection results
        """
        if not SANSKRIT_TEXT_AVAILABLE:
            return {"error": "sanskrit-text library not available"}
        
        try:
            # Detect encoding using sanskrit-text
            encoding_info = detect_encoding(text)
            
            # Additional analysis
            sanskrit_obj = SanskritText(text)
            
            return {
                "detected_encoding": encoding_info,
                "has_devanagari": any('\u0900' <= char <= '\u097F' for char in text),
                "has_iast": any(char in 'āīūṛṝḷṝēōṃḥṅñṭḍṇśṣ' for char in text),
                "character_count": len(text),
                "sanskrit_text_valid": len(sanskrit_obj.text.strip()) > 0
            }
            
        except Exception as e:
            return {"error": f"Detection failed: {e}"}
        """
        Search for text across all pages
        
        Args:
            search_term (str): Text to search for
            case_sensitive (bool): Whether search should be case sensitive
            
        Returns:
            List[Dict]: List of dictionaries with page number and matching text context
        """
        if not self.doc:
            print("PDF not loaded")
            return []
        
        results = []
        search_term_processed = search_term if case_sensitive else search_term.lower()
        
        for page_num in range(1, self.total_pages + 1):
            text = self.extract_page(page_num, fix_encoding=True)
            if not text:
                continue
            
            text_processed = text if case_sensitive else text.lower()
            
            if search_term_processed in text_processed:
                # Find context around the match
                index = text_processed.find(search_term_processed)
                start = max(0, index - 50)
                end = min(len(text), index + len(search_term) + 50)
                context = text[start:end].strip()
                
                results.append({
                    'page': page_num,
                    'context': context
                })
        
        return results
    
    def get_pdf_info(self) -> Dict:
        """
        Get PDF metadata and information
        
        Returns:
            Dict: PDF information
        """
        if not self.doc:
            return {}
        
        metadata = self.doc.metadata
        return {
            'title': metadata.get('title', 'Unknown'),
            'author': metadata.get('author', 'Unknown'),
            'subject': metadata.get('subject', 'Unknown'),
            'total_pages': self.total_pages,
            'file_path': self.pdf_path,
            'file_size_mb': round(os.path.getsize(self.pdf_path) / (1024*1024), 2)
        }
    
    def close(self):
        """Close the PDF document"""
        if self.doc:
            self.doc.close()
            print("PDF document closed")
    
    def __del__(self):
        """Destructor to ensure PDF is closed"""
        self.close()


def main():
    """
    Main function to test the SanskritPDFReader class
    """
    pdf_path = "data/pdfs/Bhakti-Rasamrta-Sindhu-Bindu.pdf"
    
    print("Sanskrit PDF Reader Test")
    print("=" * 50)
    
    # Initialize the PDF reader
    reader = SanskritPDFReader(pdf_path)
    
    if reader.doc is None:
        print("Failed to load PDF. Please check the file path.")
        return
    
    # Test 1: Get PDF information
    print("\n1. PDF Information:")
    pdf_info = reader.get_pdf_info()
    for key, value in pdf_info.items():
        print(f"   {key.title()}: {value}")
    
    # Test 2: Print page 257 (likely has Sanskrit content)
    test_page = 257
    if reader.total_pages >= test_page:
        print(f"\n2. Testing page extraction (Page {test_page}):")
        reader.print_page(test_page)
    else:
        print(f"\n2. Page {test_page} not available. Total pages: {reader.total_pages}")
        print("Testing with last available page instead:")
        reader.print_page(reader.total_pages)
    
    # Test 4: Sanskrit-text library features
    if SANSKRIT_TEXT_AVAILABLE:
        print("\n4. Sanskrit-text library features:")
        # Use page 257 for testing Sanskrit features
        test_page = min(257, reader.total_pages)
        text_sample = reader.extract_page(test_page, fix_encoding=True)
        if text_sample:
            # Encoding detection
            encoding_info = reader.detect_sanskrit_encoding(text_sample)
            print(f"\nEncoding Analysis for Page {test_page}:")
            for key, value in encoding_info.items():
                print(f"   {key}: {value}")
            
            # Transliteration test
            print(f"\nTransliteration Test (Page {test_page}, first 300 chars):")
            sample_text = text_sample[:300].strip()
            if sample_text:
                transliterated = reader.transliterate_text(sample_text, "IAST")
                print(f"   Original: {sample_text}")
                if transliterated:
                    print(f"   IAST: {transliterated}")
                else:
                    print("   IAST: Transliteration failed")
    
    # Test 5: Compare with and without encoding fixes
    test_num = 5 if SANSKRIT_TEXT_AVAILABLE else 4
    test_page = min(257, reader.total_pages)
    print(f"\n{test_num}. Encoding comparison test (Page {test_page}):")
    print("\nWithout encoding fixes:")
    print("-" * 30)
    text_raw = reader.extract_page(test_page, fix_encoding=False)
    if text_raw:
        sample_raw = text_raw[:500] + "..." if len(text_raw) > 500 else text_raw
        print(sample_raw)
        # Highlight potential encoding issues
        if 'ß' in text_raw or 'à' in text_raw or 'Þ' in text_raw:
            print("\n⚠️  Potential encoding issues detected (ß, à, Þ, etc.)")
    
    print("\nWith encoding fixes:")
    print("-" * 30)
    text_fixed = reader.extract_page(test_page, fix_encoding=True)
    if text_fixed:
        sample_fixed = text_fixed[:500] + "..." if len(text_fixed) > 500 else text_fixed
        print(sample_fixed)
        # Show improvements
        if text_raw and text_fixed != text_raw:
            print("\n✅ Encoding fixes applied successfully")
    
    # Close the PDF
    reader.close()
    print("\nTest completed!")


if __name__ == "__main__":
    main()