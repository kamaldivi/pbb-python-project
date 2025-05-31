import logging
import re
from pathlib import Path
from typing import List, Dict, Optional, Generator
from dataclasses import dataclass
from datetime import datetime

import PyPDF2
import pdfplumber
import fitz  # PyMuPDF

try:
    import pikepdf
    PIKEPDF_AVAILABLE = True
except ImportError:
    PIKEPDF_AVAILABLE = False

try:
    from pdfminer.high_level import extract_text
    from pdfminer.layout import LAParams
    PDFMINER_AVAILABLE = True
except ImportError:
    PDFMINER_AVAILABLE = False

try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

from src.utils.text_processor import TextProcessor

logger = logging.getLogger('pbb_parser.pdf_parser')

@dataclass
class BookChapter:
    title: str
    content: str
    page_start: int
    page_end: int
    paragraphs: List[str]

@dataclass
class BookContent:
    title: str
    author: str
    language: str
    total_pages: int
    chapters: List[BookChapter]
    metadata: Dict
    file_path: str
    processed_timestamp: datetime

class PDFParser:
    """Enhanced PDF parser specifically designed for spiritual books."""
    
    def __init__(self, text_processor: Optional[TextProcessor] = None):
        self.text_processor = text_processor or TextProcessor()
        
    def parse_pdf(self, pdf_path: Path, password: str = None) -> BookContent:
        """Parse a PDF file and extract structured content."""
        logger.info(f"Starting to parse PDF: {pdf_path}")
        
        try:
            # Try multiple parsing methods in order of reliability
            content = ""
            
            # 1. Try PyMuPDF first (often most reliable)
            logger.info("Attempting PyMuPDF extraction...")
            content = self._parse_with_pymupdf(pdf_path, password)
            
            # 2. If insufficient, try pdfplumber
            if not content or len(content.strip()) < 100:
                logger.info("PyMuPDF insufficient, trying PDFPlumber...")
                content = self._parse_with_pdfplumber(pdf_path, password)
            
            # 3. If still insufficient, try pdfminer
            if (not content or len(content.strip()) < 100) and PDFMINER_AVAILABLE:
                logger.info("PDFPlumber insufficient, trying pdfminer...")
                content = self._parse_with_pdfminer(pdf_path)
            
            # 4. Try pikepdf if available and we have a password
            if (not content or len(content.strip()) < 100) and PIKEPDF_AVAILABLE and password:
                logger.info("Trying pikepdf...")
                content = self._parse_with_pikepdf(pdf_path, password)
            
            # 6. Finally try OCR if available and no text found
            if (not content or len(content.strip()) < 100) and OCR_AVAILABLE:
                logger.info("Trying OCR extraction...")
                content = self._parse_with_ocr(pdf_path)
            
            if not content or len(content.strip()) < 100:
                logger.warning("All parsing methods failed - PDF may be corrupted or heavily protected")
                logger.warning("This PDF may have security restrictions like 'Page Extraction: Not Allowed'")
                logger.warning("Try using qpdf to remove restrictions: qpdf --decrypt input.pdf output.pdf")
                # Create minimal content so processing doesn't fail completely
                content = f"Unable to extract text from {pdf_path.name} - PDF may have security restrictions preventing text extraction"
            
            # Extract metadata
            metadata = self._extract_metadata(pdf_path, password)
            
            # Debug: Check content before processing
            logger.info(f"Raw content length: {len(content)} characters")
            logger.info(f"Raw content word count: {len(content.split())}")
            
            # Process and structure the content
            book_content = self._structure_content(
                content, 
                pdf_path, 
                metadata
            )
            
            logger.info(f"Successfully parsed PDF with {len(book_content.chapters)} chapters")
            return book_content
            
        except Exception as e:
            logger.error(f"Error parsing PDF {pdf_path}: {str(e)}")
            raise
    
    def _parse_with_pymupdf(self, pdf_path: Path, password: str = None) -> str:
        """Parse PDF using PyMuPDF (good for complex layouts)."""
        content = []
        
        try:
            doc = fitz.open(pdf_path)
            logger.info(f"PyMuPDF opened PDF with {len(doc)} pages")
            
            # Handle password-protected PDFs
            if doc.needs_pass:
                if password:
                    auth_result = doc.authenticate(password)
                    if not auth_result:
                        logger.error("Invalid password for PyMuPDF")
                        doc.close()
                        return ""
                    logger.info("PDF decrypted successfully with PyMuPDF")
                else:
                    logger.error("PDF requires password but none provided")
                    doc.close()
                    return ""
            
            total_chars = 0
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                if text:
                    content.append(f"\n--- PAGE {page_num + 1} ---\n")
                    content.append(text)
                    total_chars += len(text)
                    logger.debug(f"Page {page_num + 1}: extracted {len(text)} characters")
            
            doc.close()
            
            result = "\n".join(content)
            logger.info(f"PyMuPDF extraction completed: {total_chars} characters, {len(result.split())} words")
            return result
            
        except Exception as e:
            logger.error(f"PyMuPDF parsing failed: {str(e)}")
            return ""
    
    def _parse_with_pdfplumber(self, pdf_path: Path, password: str = None) -> str:
        """Parse PDF using pdfplumber (best for text extraction)."""
        content = []
        
        try:
            kwargs = {}
            if password:
                kwargs['password'] = password
                
            with pdfplumber.open(pdf_path, **kwargs) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        # Add page marker for reference
                        content.append(f"\n--- PAGE {page_num} ---\n")
                        content.append(text)
                        
        except Exception as e:
            logger.error(f"PDFPlumber parsing failed: {str(e)}")
            return ""
            
        return "\n".join(content)
    
    def _parse_with_pdfminer(self, pdf_path: Path) -> str:
        """Parse PDF using pdfminer.six (good for complex layouts and problematic PDFs)."""
        if not PDFMINER_AVAILABLE:
            return ""
        
        try:
            # Configure layout analysis parameters
            laparams = LAParams(
                detect_vertical=True,
                word_margin=0.1,
                char_margin=2.0,
                line_margin=0.5,
                boxes_flow=0.5
            )
            
            # Extract text with page breaks
            text = extract_text(str(pdf_path), laparams=laparams)
            
            if text:
                # Add basic page markers (pdfminer doesn't provide page numbers directly)
                # We'll estimate based on form feeds or large gaps
                pages = text.split('\f')  # Form feed character often indicates page breaks
                content = []
                
                for page_num, page_text in enumerate(pages, 1):
                    if page_text.strip():
                        content.append(f"\n--- PAGE {page_num} ---\n")
                        content.append(page_text.strip())
                
                return "\n".join(content)
            
        except Exception as e:
            logger.error(f"pdfminer parsing failed: {str(e)}")
            
        return ""
    
    def _parse_with_pikepdf(self, pdf_path: Path, password: str) -> str:
        """Parse PDF using pikepdf (best for encrypted PDFs)."""
        if not PIKEPDF_AVAILABLE:
            return ""
        
        content = []
        
        try:
            # Open encrypted PDF with pikepdf
            with pikepdf.open(pdf_path, password=password) as pdf:
                logger.info(f"Successfully opened encrypted PDF with pikepdf: {len(pdf.pages)} pages")
                
                # Convert to temporary unencrypted PDF for other parsers
                temp_pdf_path = pdf_path.parent / f"temp_{pdf_path.name}"
                pdf.save(temp_pdf_path)
                
                # Now use pdfplumber on the unencrypted version
                try:
                    with pdfplumber.open(temp_pdf_path) as plumber_pdf:
                        for page_num, page in enumerate(plumber_pdf.pages, 1):
                            text = page.extract_text()
                            if text:
                                content.append(f"\n--- PAGE {page_num} ---\n")
                                content.append(text)
                finally:
                    # Clean up temporary file
                    if temp_pdf_path.exists():
                        temp_pdf_path.unlink()
                        
        except Exception as e:
            logger.error(f"pikepdf parsing failed: {str(e)}")
            return ""
            
        return "\n".join(content)
    
    def _parse_with_pypdf2(self, pdf_path: Path, password: str = None) -> str:
        """Parse PDF using PyPDF2 (fallback method)."""
        content = []
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Handle encrypted PDFs
                if pdf_reader.is_encrypted:
                    if password:
                        decrypt_result = pdf_reader.decrypt(password)
                        if decrypt_result == 0:
                            logger.error("Invalid password for PyPDF2")
                            return ""
                        logger.info("PDF decrypted successfully with PyPDF2")
                    else:
                        logger.error("PDF is encrypted but no password provided")
                        return ""
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    text = page.extract_text()
                    if text:
                        content.append(f"\n--- PAGE {page_num} ---\n")
                        content.append(text)
                        
        except Exception as e:
            logger.error(f"PyPDF2 parsing failed: {str(e)}")
            return ""
            
        return "\n".join(content)
    
    def _parse_with_ocr(self, pdf_path: Path) -> str:
        """Parse PDF using OCR (for scanned/image-based PDFs)."""
        if not OCR_AVAILABLE:
            return ""
        
        content = []
        
        try:
            logger.info("Converting PDF to images for OCR...")
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=300)
            
            logger.info(f"OCR processing {len(images)} pages...")
            for page_num, image in enumerate(images, 1):
                # Use OCR to extract text
                text = pytesseract.image_to_string(image, lang='eng')
                if text.strip():
                    content.append(f"\n--- PAGE {page_num} ---\n")
                    content.append(text.strip())
            
            logger.info(f"OCR completed for {len(images)} pages")
            
        except Exception as e:
            logger.error(f"OCR parsing failed: {str(e)}")
            return ""
            
        return "\n".join(content)
    
    def _extract_metadata(self, pdf_path: Path, password: str = None) -> Dict:
        """Extract metadata from PDF."""
        metadata = {
            'file_name': pdf_path.name,
            'file_size': pdf_path.stat().st_size,
            'creation_date': None,
            'modification_date': None,
            'title': None,
            'author': None,
            'subject': None
        }
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Handle encrypted PDFs
                if pdf_reader.is_encrypted and password:
                    pdf_reader.decrypt(password)
                
                if pdf_reader.metadata:
                    metadata.update({
                        'title': pdf_reader.metadata.get('/Title', ''),
                        'author': pdf_reader.metadata.get('/Author', ''),
                        'subject': pdf_reader.metadata.get('/Subject', ''),
                        'creation_date': pdf_reader.metadata.get('/CreationDate', ''),
                        'modification_date': pdf_reader.metadata.get('/ModDate', '')
                    })
        except Exception as e:
            logger.warning(f"Could not extract metadata: {str(e)}")
            
        return metadata
    
    def _structure_content(self, raw_content: str, pdf_path: Path, metadata: Dict) -> BookContent:
        """Structure the raw content into chapters and paragraphs."""
        
        logger.info(f"Structuring content: {len(raw_content)} characters")
        
        # Clean the content
        cleaned_content = self.text_processor.clean_text(raw_content)
        logger.info(f"After cleaning: {len(cleaned_content)} characters")
        
        # Detect book title and author
        title = self._detect_book_title(cleaned_content, metadata)
        author = self._detect_author(cleaned_content, metadata)
        language = self._detect_language(cleaned_content)
        
        logger.info(f"Detected - Title: '{title}', Author: '{author}', Language: '{language}'")
        
        # Split into chapters
        chapters = self._detect_chapters(cleaned_content)
        
        # Count total pages
        page_markers = re.findall(r'--- PAGE (\d+) ---', raw_content)
        total_pages = len(page_markers) if page_markers else 0
        
        logger.info(f"Final stats - Chapters: {len(chapters)}, Pages: {total_pages}")
        
        return BookContent(
            title=title,
            author=author,
            language=language,
            total_pages=total_pages,
            chapters=chapters,
            metadata=metadata,
            file_path=str(pdf_path),
            processed_timestamp=datetime.now()
        )
    
    def _detect_book_title(self, content: str, metadata: Dict) -> str:
        """Detect the book title from content or metadata."""
        # Try metadata first
        if metadata.get('title') and len(metadata['title'].strip()) > 3:
            return metadata['title'].strip()
        
        # Try to find title in first few pages
        lines = content.split('\n')[:50]  # First 50 lines
        
        # Look for lines that might be titles (all caps, centered, etc.)
        for line in lines:
            line = line.strip()
            if (len(line) > 10 and len(line) < 100 and 
                (line.isupper() or 
                 any(term in line.lower() for term in ['sri', 'srila', 'maharaj', 'by']))):
                if not re.match(r'^\d+$', line):  # Not just a page number
                    return line
        
        return "Unknown Title"
    
    def _detect_author(self, content: str, metadata: Dict) -> str:
        """Detect the author from content or metadata."""
        # Try metadata first
        if metadata.get('author') and len(metadata['author'].strip()) > 3:
            return metadata['author'].strip()
        
        # Look for "by" patterns in content
        by_patterns = [
            r'by\s+([A-Z][a-zA-Z\s]+(?:Maharaj|Prabhu|Das|Devi))',
            r'(?:Srila|Sri)\s+([A-Z][a-zA-Z\s]+Maharaj)',
            r'([A-Z][a-zA-Z\s]+Maharaj)'
        ]
        
        for pattern in by_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Srila Narayan Maharaj"  # Default assumption
    
    def _detect_language(self, content: str) -> str:
        """Detect the primary language of the content."""
        # Simple heuristic - count English vs non-English characters
        english_chars = sum(1 for c in content if c.isascii() and c.isalpha())
        total_chars = sum(1 for c in content if c.isalpha())
        
        if total_chars > 0 and english_chars / total_chars > 0.8:
            return "English"
        else:
            return "Mixed/Sanskrit"
    
    def _detect_chapters(self, content: str) -> List[BookChapter]:
        """Detect and extract chapters from the content."""
        chapters = []
        
        # Common chapter patterns in spiritual books AND academic papers
        chapter_patterns = [
            # Academic paper patterns
            r'^(\d+\.?\s+[A-Z][A-Za-z\s]+)$',  # "1. Introduction", "2 Related Work"
            r'^([A-Z][A-Z\s]{5,50})$',  # All caps section headers
            r'^(Abstract|Introduction|Related Work|Method|Results|Conclusion|References|Acknowledgments)$',
            r'^(\d+\.\d+\.?\s+.+)$',  # "2.1 Background", "3.2.1 Method"
            
            # Original spiritual book patterns
            r'(?:CHAPTER|Chapter)\s+(\d+|[IVX]+)[\s\-:]*(.+?)(?=\n)',
            r'(?:Chapter|CHAPTER)\s+(.+?)(?=\n)',
            r'^\d+\.\s+(.+?)(?=\n)',  # Numbered sections
        ]
        
        lines = content.split('\n')
        current_chapter = None
        current_content = []
        current_page = 1
        
        logger.info(f"Chapter detection processing {len(lines)} lines")
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Check for page markers
            page_match = re.match(r'--- PAGE (\d+) ---', line)
            if page_match:
                current_page = int(page_match.group(1))
                continue
            
            # Skip empty lines
            if not line:
                if current_chapter:
                    current_content.append("")
                continue
            
            # Check if this line is a chapter title
            is_chapter_title = False
            chapter_title = ""
            
            for pattern in chapter_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match and len(line) > 3 and len(line) < 100:
                    chapter_title = match.group(1) if match.lastindex == 1 else f"{match.group(1)} {match.group(2) if match.lastindex >= 2 else ''}"
                    is_chapter_title = True
                    logger.debug(f"Found potential chapter: '{chapter_title}' from line: '{line}'")
                    break
            
            if is_chapter_title and chapter_title:
                # Save previous chapter
                if current_chapter and current_content:
                    current_chapter.content = '\n'.join(current_content)
                    current_chapter.paragraphs = self.text_processor.split_into_paragraphs(current_chapter.content)
                    current_chapter.page_end = current_page - 1
                    chapters.append(current_chapter)
                    logger.info(f"Completed chapter: '{current_chapter.title}' with {len(current_chapter.content)} chars")
                
                # Start new chapter
                current_chapter = BookChapter(
                    title=chapter_title.strip(),
                    content="",
                    page_start=current_page,
                    page_end=current_page,
                    paragraphs=[]
                )
                current_content = []
                logger.info(f"Started new chapter: '{chapter_title.strip()}'")
            else:
                # Add to current chapter content
                if current_chapter:
                    current_content.append(line)
        
        # Don't forget the last chapter
        if current_chapter and current_content:
            current_chapter.content = '\n'.join(current_content)
            current_chapter.paragraphs = self.text_processor.split_into_paragraphs(current_chapter.content)
            current_chapter.page_end = current_page
            chapters.append(current_chapter)
            logger.info(f"Completed final chapter: '{current_chapter.title}' with {len(current_chapter.content)} chars")
        
        # If no chapters detected, create one big chapter with all content
        if not chapters:
            logger.info("No chapters detected, creating single chapter with all content")
            # Remove only page markers, keep everything else
            content_lines = []
            for line in lines:
                if not re.match(r'--- PAGE \d+ ---', line.strip()):
                    content_lines.append(line)
            
            all_content = '\n'.join(content_lines)
            logger.info(f"Single chapter content: {len(all_content)} characters, {len(all_content.split())} words")
            
            paragraphs = self.text_processor.split_into_paragraphs(all_content)
            logger.info(f"Single chapter paragraphs: {len(paragraphs)}")
            
            chapters.append(BookChapter(
                title="Full Content",
                content=all_content,
                page_start=1,
                page_end=current_page,
                paragraphs=paragraphs
            ))
            logger.info(f"Single chapter created with {len(all_content)} characters and {len(paragraphs)} paragraphs")
        
        logger.info(f"Chapter detection complete: {len(chapters)} chapters detected")
        return chapters