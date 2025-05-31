#!/usr/bin/env python3
"""
PBB-Python-Project: Spiritual Book Content Parser and Indexer
Main application for parsing PDF books by Srila Narayan Maharaj and indexing them in OpenSearch
"""

import logging
import logging.config
import argparse
import sys
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import our modules
from config.settings import (
    OPENSEARCH_CONFIG, INDEX_CONFIG, PDF_DIR, 
    PROCESSED_DIR, LOGGING_CONFIG
)
from src.parsers.pdf_parser import PDFParser
from src.indexers.opensearch_indexer import OpenSearchIndexer
from src.utils.text_processor import TextProcessor

# Setup logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('pbb_parser')

class PBBApplication:
    """Main application class for the Spiritual Book Parser."""
    
    def __init__(self):
        self.text_processor = TextProcessor()
        self.pdf_parser = PDFParser(self.text_processor)
        self.indexer = OpenSearchIndexer(OPENSEARCH_CONFIG, self.text_processor)
        
        logger.info("PBB Application initialized")
    
    def setup_opensearch(self) -> bool:
        """Initialize OpenSearch index."""
        try:
            logger.info("Setting up OpenSearch index...")
            
            # Check OpenSearch connection
            health = self.indexer.health_check()
            if not health.get('connection_healthy'):
                logger.error(f"OpenSearch connection failed: {health.get('error')}")
                return False
            
            logger.info(f"OpenSearch cluster status: {health.get('cluster_status')}")
            
            # Create index if needed
            success = self.indexer.create_index(INDEX_CONFIG)
            if success:
                logger.info("OpenSearch index ready")
                return True
            else:
                logger.error("Failed to create OpenSearch index")
                return False
                
        except Exception as e:
            logger.error(f"Error setting up OpenSearch: {str(e)}")
            return False
    
    def process_pdf(self, pdf_path: Path, force_reprocess: bool = False) -> bool:
        """Process a single PDF file."""
        try:
            logger.info(f"Processing PDF: {pdf_path}")
            
            # Check if already processed
            processed_marker = PROCESSED_DIR / f"{pdf_path.stem}.processed"
            if processed_marker.exists() and not force_reprocess:
                logger.info(f"PDF already processed: {pdf_path.name}. Use --force to reprocess.")
                return True
            
            # Parse the PDF
            book_content = self.pdf_parser.parse_pdf(pdf_path)
            
            # Get text statistics
            total_content = ' '.join([chapter.content for chapter in book_content.chapters])
            stats = self.text_processor.get_text_stats(total_content)
            
            logger.info(f"Parsed book: '{book_content.title}' by {book_content.author}")
            logger.info(f"Stats: {stats['words']} words, {stats['paragraphs']} paragraphs, {len(book_content.chapters)} chapters")
            
            # Index in OpenSearch
            success = self.indexer.index_book(book_content)
            
            if success:
                # Mark as processed
                processed_marker.write_text(f"Processed on: {datetime.now().isoformat()}")
                logger.info(f"Successfully processed and indexed: {book_content.title}")
                return True
            else:
                logger.error(f"Failed to index book: {book_content.title}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
            return False
    
    def process_all_pdfs(self, force_reprocess: bool = False) -> None:
        """Process all PDF files in the PDF directory."""
        pdf_files = list(PDF_DIR.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {PDF_DIR}")
            return
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        successful = 0
        failed = 0
        
        for pdf_file in pdf_files:
            try:
                if self.process_pdf(pdf_file, force_reprocess):
                    successful += 1
                else:
                    failed += 1
            except KeyboardInterrupt:
                logger.info("Processing interrupted by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error processing {pdf_file}: {str(e)}")
                failed += 1
        
        logger.info(f"Processing complete: {successful} successful, {failed} failed")
    
    def search_content(self, query: str, max_results: int = 10, filters: Optional[dict] = None) -> None:
        """Search the indexed content."""
        try:
            logger.info(f"Searching for: '{query}'")
            
            results = self.indexer.search(query, size=max_results, filters=filters)
            
            if results.get('error'):
                logger.error(f"Search error: {results['error']}")
                return
            
            total_hits = results['total_hits']
            logger.info(f"Found {total_hits} results")
            
            if total_hits == 0:
                print("No results found.")
                return
            
            print(f"\n=== Search Results for '{query}' ===")
            print(f"Total hits: {total_hits}\n")
            
            for i, result in enumerate(results['results'], 1):
                print(f"{i}. {result['book_title']} - {result['chapter_title']}")
                print(f"   Author: {result['author']} | Page: {result['page_number']} | Score: {result['score']:.2f}")
                
                if result['highlights']:
                    print("   Highlights:")
                    for highlight in result['highlights'][:2]:  # Show top 2 highlights
                        print(f"   - ...{highlight}...")
                else:
                    # Show content preview if no highlights
                    content_preview = result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
                    print(f"   Preview: {content_preview}")
                
                if result['tags']:
                    print(f"   Tags: {', '.join(result['tags'][:5])}")  # Show first 5 tags
                
                print()
                
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
    
    def show_stats(self) -> None:
        """Display statistics about the indexed content."""
        try:
            stats = self.indexer.get_book_stats()
            
            if stats.get('error'):
                logger.error(f"Error getting stats: {stats['error']}")
                return
            
            print("\n=== OpenSearch Index Statistics ===")
            print(f"Total documents: {stats['total_documents']}")
            print(f"Unique books: {stats['unique_books']}")
            print(f"Unique authors: {stats['unique_authors']}")
            
            if stats['books']:
                print(f"\nBooks indexed:")
                for book in stats['books']:
                    print(f"  - {book}")
            
            if stats['authors']:
                print(f"\nAuthors:")
                for author in stats['authors']:
                    print(f"  - {author}")
                    
        except Exception as e:
            logger.error(f"Error showing stats: {str(e)}")
    
    def delete_book(self, book_title: str) -> None:
        """Delete a book from the index."""
        try:
            success = self.indexer.delete_book(book_title)
            if success:
                logger.info(f"Successfully deleted book: {book_title}")
                
                # Remove processed marker
                processed_marker = PROCESSED_DIR / f"{book_title}.processed"
                if processed_marker.exists():
                    processed_marker.unlink()
                    
            else:
                logger.error(f"Failed to delete book: {book_title}")
                
        except Exception as e:
            logger.error(f"Error deleting book: {str(e)}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="PBB: Spiritual Book Content Parser and Indexer"
    )
    
    parser.add_argument(
        'action',
        choices=['setup', 'process', 'search', 'stats', 'delete'],
        help='Action to perform'
    )
    
    parser.add_argument(
        '--pdf',
        type=str,
        help='Specific PDF file to process (for process action)'
    )
    
    parser.add_argument(
        '--query',
        type=str,
        help='Search query (for search action)'
    )
    
    parser.add_argument(
        '--book',
        type=str,
        help='Book title to delete (for delete action)'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force reprocessing of already processed files'
    )
    
    parser.add_argument(
        '--max-results',
        type=int,
        default=10,
        help='Maximum number of search results to return'
    )
    
    args = parser.parse_args()
    
    # Initialize application
    try:
        app = PBBApplication()
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        sys.exit(1)
    
    # Execute requested action
    try:
        if args.action == 'setup':
            success = app.setup_opensearch()
            if success:
                print("✅ OpenSearch setup completed successfully!")
                print(f"You can now place PDF files in: {PDF_DIR}")
                print("Then run: python src/main.py process")
            else:
                print("❌ OpenSearch setup failed. Check logs for details.")
                sys.exit(1)
        
        elif args.action == 'process':
            if not app.setup_opensearch():
                print("❌ OpenSearch setup failed. Run 'setup' first.")
                sys.exit(1)
            
            if args.pdf:
                pdf_path = Path(args.pdf)
                if not pdf_path.exists():
                    pdf_path = PDF_DIR / args.pdf
                
                if not pdf_path.exists():
                    print(f"❌ PDF file not found: {args.pdf}")
                    sys.exit(1)
                
                success = app.process_pdf(pdf_path, args.force)
                if success:
                    print(f"✅ Successfully processed: {pdf_path.name}")
                else:
                    print(f"❌ Failed to process: {pdf_path.name}")
            else:
                app.process_all_pdfs(args.force)
        
        elif args.action == 'search':
            if not args.query:
                print("❌ Search query required. Use --query 'your search terms'")
                sys.exit(1)
            
            app.search_content(args.query, args.max_results)
        
        elif args.action == 'stats':
            app.show_stats()
        
        elif args.action == 'delete':
            if not args.book:
                print("❌ Book title required. Use --book 'Book Title'")
                sys.exit(1)
            
            app.delete_book(args.book)
    
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()