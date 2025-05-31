import re
import logging
from typing import List, Dict, Set
import unicodedata

logger = logging.getLogger('pbb_parser.text_processor')

class TextProcessor:
    """Advanced text processing for spiritual book content."""
    
    def __init__(self):
        # Common patterns to clean from spiritual texts
        self.cleanup_patterns = [
            (r'\s+', ' '),  # Multiple spaces to single space (but this removes ALL newlines!)
            (r'\n\s*\n\s*\n+', '\n\n'),  # Multiple newlines to double newline
            (r'^[\s\-_=•]+$', ''),  # Lines with only separators
            (r'^\s*\d+\s*$', ''),  # Lines with only page numbers
            (r'^\s*Page\s+\d+\s*$', ''),  # "Page X" lines
            (r'^\s*Chapter\s+\d+\s*$', '')  # Standalone "Chapter X" lines
        ]
        
        # Sanskrit/Devanagari character preservation
        self.preserve_unicode = True
        
        # Common spiritual terms that should be preserved exactly
        self.spiritual_terms = {
            'Krishna', 'Krsna', 'Kṛṣṇa', 'Radha', 'Rādhā', 'Radhika', 'Rādhikā',
            'Vrindavan', 'Vṛndāvana', 'Vraja', 'Mathura', 'Dwarka', 'Dvārakā',
            'Gurudeva', 'Śrīla', 'Srila', 'Maharaj', 'Mahārāja', 'Prabhu',
            'Bhakti', 'Prema', 'Raga', 'Rāga', 'Vaidhi', 'Sadhana', 'Sādhana',
            'Gopī', 'Gopi', 'Vrajavāsī', 'Brajabasi', 'Hari', 'Govinda', 'Gopāla'
        }
        
    def clean_text(self, text: str) -> str:
        """Clean and normalize text while preserving spiritual terminology."""
        if not text:
            return ""
        
        # Normalize Unicode
        if self.preserve_unicode:
            text = unicodedata.normalize('NFC', text)
        
        # Apply cleanup patterns
        for pattern, replacement in self.cleanup_patterns:
            text = re.sub(pattern, replacement, text, flags=re.MULTILINE)
        
        # Remove headers and footers (common in spiritual books)
        text = self._remove_headers_footers(text)
        
        # Fix common OCR errors in spiritual texts
        text = self._fix_spiritual_ocr_errors(text)
        
        # Clean up extra whitespace
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs to single space
        text = re.sub(r'\n +', '\n', text)   # Remove spaces at start of lines
        text = re.sub(r' +\n', '\n', text)   # Remove spaces at end of lines
        
        return text.strip()
    
    def _remove_headers_footers(self, text: str) -> str:
        """Remove common headers and footers from spiritual books."""
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip common header/footer patterns
            if (re.match(r'^\d+$', line) or  # Just page numbers
                re.match(r'^Page \d+', line, re.IGNORECASE) or
                re.match(r'^Chapter \d+$', line, re.IGNORECASE) or
                re.match(r'^[\-_=•\s]+$', line) or  # Separator lines
                len(line) < 3):  # Very short lines
                continue
                
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _fix_spiritual_ocr_errors(self, text: str) -> str:
        """Fix common OCR errors in spiritual texts."""
        # Common OCR mistakes in spiritual books
        ocr_fixes = {
            r'\bKrsna\b': 'Krishna',  # Common variation
            r'\bRadha\b': 'Radha',
            r'\bVrndavana\b': 'Vrindavan',
            r'\bgurudeva\b': 'Gurudeva',
            r'\bsrila\b': 'Srila',
            r'\bmaharaj\b': 'Maharaj',
            r'\bbhakti\b': 'bhakti',
            r'\bprema\b': 'prema',
            # Fix punctuation issues
            r'(\w)\.(\w)': r'\1. \2',  # Missing space after period
            r'(\w),(\w)': r'\1, \2',   # Missing space after comma
            r'(\w);(\w)': r'\1; \2',   # Missing space after semicolon
        }
        
        for pattern, replacement in ocr_fixes.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def split_into_paragraphs(self, text: str, min_length: int = 50) -> List[str]:
        """Split text into meaningful paragraphs."""
        if not text:
            return []
        
        # Split by double newlines first
        raw_paragraphs = re.split(r'\n\s*\n', text)
        
        paragraphs = []
        for para in raw_paragraphs:
            para = para.strip()
            
            # Skip very short paragraphs (likely artifacts)
            if len(para) < min_length:
                continue
            
            # Further split very long paragraphs by sentence groups
            if len(para) > 2000:
                sub_paras = self._split_long_paragraph(para)
                paragraphs.extend(sub_paras)
            else:
                paragraphs.append(para)
        
        return [p for p in paragraphs if p.strip()]
    
    def _split_long_paragraph(self, paragraph: str, max_length: int = 1500) -> List[str]:
        """Split overly long paragraphs into smaller chunks."""
        if len(paragraph) <= max_length:
            return [paragraph]
        
        # Split by sentences
        sentences = re.split(r'(?<=[.!?])\s+', paragraph)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # If adding this sentence would exceed max_length, start new chunk
            if current_length + len(sentence) > max_length and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_length = len(sentence)
            else:
                current_chunk.append(sentence)
                current_length += len(sentence) + 1  # +1 for space
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def extract_spiritual_terms(self, text: str) -> Set[str]:
        """Extract spiritual terms and names from the text."""
        terms = set()
        
        # Find all capitalized words that might be spiritual terms
        words = re.findall(r'\b[A-Z][a-zA-Z]+\b', text)
        
        for word in words:
            # Check if it's a known spiritual term or follows spiritual naming patterns
            if (word in self.spiritual_terms or
                word.endswith(('ji', 'maharaj', 'prabhu', 'devi', 'das')) or
                word.startswith(('Sri', 'Srila', 'Guru')) or
                len(word) > 6 and any(char in word for char in 'āīūṛḷṃḥ')):  # Sanskrit chars
                terms.add(word)
        
        return terms
    
    def generate_tags(self, text: str) -> List[str]:
        """Generate relevant tags for the content."""
        tags = []
        
        # Extract spiritual terms as tags
        spiritual_terms = self.extract_spiritual_terms(text)
        tags.extend(list(spiritual_terms)[:10])  # Limit to top 10
        
        # Add topic-based tags
        topic_keywords = {
            'bhakti': ['bhakti', 'devotion', 'love', 'worship'],
            'krishna': ['krishna', 'krsna', 'govinda', 'gopala'],
            'radha': ['radha', 'radhika', 'divine feminine'],
            'vrindavan': ['vrindavan', 'vraja', 'braj', 'mathura'],
            'philosophy': ['philosophy', 'spiritual', 'teaching', 'wisdom'],
            'story': ['story', 'lila', 'pastime', 'narrative'],
            'prayer': ['prayer', 'meditation', 'chanting', 'mantra'],
            'guru': ['guru', 'teacher', 'guide', 'instruction']
        }
        
        text_lower = text.lower()
        for tag, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                tags.append(tag)
        
        return list(set(tags))  # Remove duplicates
    
    def clean_for_search(self, text: str) -> str:
        """Clean text specifically for search indexing."""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but preserve Sanskrit
        if self.preserve_unicode:
            # Keep Unicode letters, numbers, and basic punctuation
            text = re.sub(r'[^\w\s\u0900-\u097F.,;:!?()-]', ' ', text)
        else:
            text = re.sub(r'[^\w\s.,;:!?()-]', ' ', text)
        
        return text.strip()
    
    def get_text_stats(self, text: str) -> Dict[str, int]:
        """Get basic statistics about the text."""
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        paragraphs = text.split('\n\n')
        
        return {
            'characters': len(text),
            'words': len(words),
            'sentences': len([s for s in sentences if s.strip()]),
            'paragraphs': len([p for p in paragraphs if p.strip()]),
            'unique_words': len(set(word.lower() for word in words if word.isalpha()))
        }