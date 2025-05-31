# PBB-Python-Project: Spiritual Book Content Parser

A Python application for parsing PDF books by Srila Narayan Maharaj and indexing them in OpenSearch for powerful searchability.

## Features

- **Multi-format PDF parsing** using PyPDF2, PDFPlumber, and PyMuPDF
- **Intelligent content structuring** with chapter and paragraph detection
- **OpenSearch integration** for fast, full-text search
- **Spiritual text optimization** with Sanskrit term preservation
- **Batch processing** for multiple books
- **Advanced search** with highlighting and filtering

## Prerequisites

- Python 3.8+
- OpenSearch running in Docker
- WSL Ubuntu (if on Windows)

## Installation

1. **Clone and setup the project:**
```bash
cd ~/python-projects/PBB-Python-Project
source venv/bin/activate
```

2. **Install dependencies:**
```bash
pip install PyPDF2 pdfplumber pymupdf4llm
pip install opensearch-py
pip install python-dotenv
pip install nltk spacy
pip install requests beautifulsoup4
pip install regex unicodedata2
pip install colorlog  # Optional for colored logging

# Save requirements
pip freeze > requirements.txt
```

3. **Start OpenSearch in Docker:**
```bash
docker run -d \
  --name opensearch \
  -p 9200:9200 -p 9600:9600 \
  -e "discovery.type=single-node" \
  -e "OPENSEARCH_INITIAL_ADMIN_PASSWORD=YourPassword123!" \
  opensearchproject/opensearch:latest
```

4. **Initialize the application:**
```bash
python src/main.py setup
```

## Quick Start

### 1. Setup OpenSearch Index
```bash
python src/main.py setup
```

### 2. Add PDF Books
Place your PDF files of Srila Narayan Maharaj's books in the `data/pdfs/` directory:
```bash
cp /path/to/your/book.pdf data/pdfs/
```

### 3. Process Books
```bash
# Process all PDFs
python src/main.py process

# Process specific PDF
python src/main.py process --pdf "book-name.pdf"

# Force reprocess (if already processed)
python src/main.py process --force
```

### 4. Search Content
```bash
# Basic search
python src/main.py search --query "Krishna prema"

# Limited results
python src/main.py search --query "bhakti" --max-results 5
```

### 5. View Statistics
```bash
python src/main.py stats
```

## Usage Examples

### Processing Books
```bash
# Process all PDFs in data/pdfs/
python src/main.py process

# Process specific book with force reprocessing
python src/main.py process --pdf "Bhakti-Rasamrta-Sindhu.pdf" --force
```

### Searching Content
```bash
# Search for spiritual topics
python src/main.py search --query "Radha Krishna"
python src/main.py search --query "Vrindavan lila"
python src/main.py search --query "guru disciple relationship"

# Search with result limits
python src/main.py search --query "prema bhakti" --max-results 3
```

### Managing Content
```bash
# View index statistics
python src/main.py stats

# Delete a specific book from index
python src/main.py delete --book "Book Title Here"
```

## Project Structure

```
PBB-Python-Project/
├── src/
│   ├── main.py                 # Main application
│   ├── parsers/
│   │   └── pdf_parser.py       # PDF parsing logic
│   ├── indexers/
│   │   └── opensearch_indexer.py # OpenSearch integration
│   └── utils/
│       └── text_processor.py   # Text cleaning & processing
├── config/
│   └── settings.py             # Configuration settings
├── data/
│   ├── pdfs/                   # Place PDF files here
│   └── processed/              # Processing markers
├── tests/                      # Test files
├── logs/                       # Application logs
├── .env                        # Environment variables
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Configuration

### OpenSearch Settings
Edit `.env` file to configure your OpenSearch connection:
```bash
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=YourPassword123!
```

### Text Processing
The application includes special handling for:
- Sanskrit/Devanagari text preservation
- Spiritual terminology recognition
- Chapter and verse detection
- OCR error correction for spiritual texts

## Features in Detail

### PDF Processing
- **Multi-parser approach**: Uses PyPDF2, PDFPlumber, and PyMuPDF for best text extraction
- **Chapter detection**: Automatically identifies chapters and sections
- **Paragraph segmentation**: Splits content into searchable paragraphs
- **Metadata extraction**: Captures book title, author, and other metadata

### Text Processing
- **Spiritual term preservation**: Maintains proper spelling of Sanskrit terms
- **OCR error correction**: Fixes common scanning errors in spiritual texts
- **Content cleaning**: Removes headers, footers, and formatting artifacts
- **Tag generation**: Automatically generates relevant tags for content

### Search Features
- **Full-text search**: Search across all book content
- **Phrase matching**: Find exact phrases with boosted relevance
- **Fuzzy search**: Handles typos and variations
- **Highlighting**: Shows matching text snippets
- **Filtering**: Filter by book, author, or tags

## API Usage (Python)

You can also use the components programmatically:

```python
from pathlib import Path
from src.parsers.pdf_parser import PDFParser
from src.indexers.opensearch_indexer import OpenSearchIndexer
from src.utils.text_processor import TextProcessor
from config.settings import OPENSEARCH_CONFIG, INDEX_CONFIG

# Initialize components
text_processor = TextProcessor()
pdf_parser = PDFParser(text_processor)
indexer = OpenSearchIndexer(OPENSEARCH_CONFIG, text_processor)

# Process a PDF
pdf_path = Path("data/pdfs/your-book.pdf")
book_content = pdf_parser.parse_pdf(pdf_path)

# Index the content
indexer.create_index(INDEX_CONFIG)
indexer.index_book(book_content)

# Search
results = indexer.search("Krishna prema", size=5)
print(f"Found {results['total_hits']} results")
```

## Troubleshooting

### OpenSearch Connection Issues
```bash
# Check if OpenSearch is running
curl -X GET "localhost:9200"

# Check logs
docker logs opensearch
```

### PDF Processing Issues
- **Empty content**: Try different PDF parsers or check if PDF is text-based
- **Encoding errors**: Ensure PDFs contain actual text, not just images
- **Memory issues**: Process large PDFs one at a time

### Search Issues
- **No results**: Check if content was indexed properly using `stats` command
- **Poor results**: Try different search terms or check content tags

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Adding New Features
1. Text processing enhancements: Edit `src/utils/text_processor.py`
2. PDF parsing improvements: Edit `src/parsers/pdf_parser.py`
3. Search features: Edit `src/indexers/opensearch_indexer.py`

### Logging
Logs are written to `logs/pbb_parser.log`. Adjust log level in `config/settings.py`.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Spiritual Context

This project is designed specifically for the works of Srila Narayan Maharaj, a renowned spiritual teacher in the Gaudiya Vaishnava tradition. The text processing includes:

- Recognition of Sanskrit terms and names
- Proper handling of spiritual concepts
- Preservation of traditional spellings
- Context-aware content organization

## License

This project is intended for spiritual study and research purposes.

## Support

For issues and questions:
1. Check the logs in `logs/pbb_parser.log`
2. Verify OpenSearch is running and accessible
3. Ensure PDF files are text-based (not scanned images)
4. Check that all dependencies are installed correctly