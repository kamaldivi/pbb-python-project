import logging
import json
from typing import Dict, List, Optional, Generator
from datetime import datetime
from dataclasses import asdict

from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy.exceptions import ConnectionError, RequestError

from src.parsers.pdf_parser import BookContent, BookChapter
from src.utils.text_processor import TextProcessor

logger = logging.getLogger('pbb_parser.opensearch_indexer')

class OpenSearchIndexer:
    """OpenSearch indexer for spiritual book content."""
    
    def __init__(self, config: Dict, text_processor: Optional[TextProcessor] = None):
        self.config = config
        self.text_processor = text_processor or TextProcessor()
        self.client = None
        self.index_name = config.get('index_name', 'srila-narayan-maharaj-books')
        
        # Initialize OpenSearch client
        self._connect()
    
    def _connect(self):
        """Initialize connection to OpenSearch."""
        try:
            opensearch_config = self.config.copy()
            # Remove our custom keys that OpenSearch client doesn't need
            opensearch_config.pop('index_name', None)
            
            # Build connection parameters
            use_ssl = opensearch_config.get('use_ssl', False)
            verify_certs = opensearch_config.get('verify_certs', False)
            
            connection_params = {
                'hosts': [{
                    'host': opensearch_config.get('host', 'localhost'),
                    'port': opensearch_config.get('port', 9200)
                }],
                'use_ssl': use_ssl,
                'verify_certs': verify_certs,
                'ssl_assert_hostname': opensearch_config.get('ssl_assert_hostname', False),
                'ssl_show_warn': opensearch_config.get('ssl_show_warn', False),
                'connection_class': RequestsHttpConnection,
                'timeout': 30
            }
            
            # Only add auth if username and password are provided
            username = opensearch_config.get('username', '').strip()
            password = opensearch_config.get('password', '').strip()
            
            if username and password:
                connection_params['http_auth'] = (username, password)
                logger.info(f"Using authentication for OpenSearch (SSL: {use_ssl})")
            else:
                logger.info(f"Connecting to OpenSearch without authentication (SSL: {use_ssl})")
            
            # Additional SSL handling for self-signed certificates
            if use_ssl and not verify_certs:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                logger.info("SSL certificate verification disabled")
            
            self.client = OpenSearch(**connection_params)
            
            # Test connection
            info = self.client.info()
            logger.info(f"✅ Connected to OpenSearch: {info['version']['number']}")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to OpenSearch: {str(e)}")
            logger.error(f"Connection details: host={opensearch_config.get('host')}, port={opensearch_config.get('port')}, ssl={use_ssl}")
            raise ConnectionError(f"Cannot connect to OpenSearch: {str(e)}")
    
    def create_index(self, index_config: Dict) -> bool:
        """Create the index with proper mapping for spiritual content."""
        try:
            if self.client.indices.exists(index=self.index_name):
                logger.info(f"Index '{self.index_name}' already exists")
                return True
            
            # Create index with mapping
            response = self.client.indices.create(
                index=self.index_name,
                body={
                    'settings': index_config.get('settings', {}),
                    'mappings': index_config.get('mappings', {})
                }
            )
            
            logger.info(f"Created index '{self.index_name}': {response}")
            return True
            
        except RequestError as e:
            if 'resource_already_exists_exception' in str(e):
                logger.info(f"Index '{self.index_name}' already exists")
                return True
            else:
                logger.error(f"Error creating index: {str(e)}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error creating index: {str(e)}")
            return False
    
    def index_book(self, book_content: BookContent) -> bool:
        """Index a complete book with all its chapters and paragraphs."""
        try:
            logger.info(f"Starting to index book: {book_content.title}")
            
            indexed_count = 0
            
            # Index each chapter as separate documents for better searchability
            for chapter_idx, chapter in enumerate(book_content.chapters):
                chapter_docs = self._create_chapter_documents(
                    book_content, chapter, chapter_idx
                )
                
                for doc in chapter_docs:
                    success = self._index_document(doc)
                    if success:
                        indexed_count += 1
            
            logger.info(f"Successfully indexed {indexed_count} documents from '{book_content.title}'")
            return indexed_count > 0
            
        except Exception as e:
            logger.error(f"Error indexing book '{book_content.title}': {str(e)}")
            return False
    
    def _create_chapter_documents(self, book: BookContent, chapter: BookChapter, chapter_idx: int) -> List[Dict]:
        """Create multiple documents from a chapter (one per paragraph for better search granularity)."""
        documents = []
        
        # Create base document data
        base_doc = {
            'book_title': book.title,
            'author': book.author,
            'language': book.language,
            'chapter_title': chapter.title,
            'chapter_number': chapter_idx + 1,
            'page_start': chapter.page_start,
            'page_end': chapter.page_end,
            'file_path': book.file_path,
            'timestamp': book.processed_timestamp.isoformat(),
            'total_pages': book.total_pages
        }
        
        # Create one document per paragraph for better search granularity
        for para_idx, paragraph in enumerate(chapter.paragraphs):
            if len(paragraph.strip()) < 50:  # Skip very short paragraphs
                continue
            
            # Clean paragraph for indexing
            clean_content = self.text_processor.clean_for_search(paragraph)
            
            # Generate tags for this paragraph
            tags = self.text_processor.generate_tags(paragraph)
            
            # Calculate approximate page number for this paragraph
            para_position = para_idx / len(chapter.paragraphs) if chapter.paragraphs else 0
            approx_page = chapter.page_start + int((chapter.page_end - chapter.page_start) * para_position)
            
            doc = {
                **base_doc,
                'content': clean_content,
                'paragraph_id': f"{book.title}_{chapter_idx}_{para_idx}",
                'paragraph_number': para_idx + 1,
                'page_number': approx_page,
                'tags': tags,
                'content_length': len(clean_content),
                'word_count': len(clean_content.split())
            }
            
            documents.append(doc)
        
        # Also create a chapter summary document
        chapter_summary = {
            **base_doc,
            'content': self.text_processor.clean_for_search(chapter.content[:1000]),  # First 1000 chars
            'paragraph_id': f"{book.title}_{chapter_idx}_summary",
            'paragraph_number': 0,  # 0 indicates summary
            'page_number': chapter.page_start,
            'tags': self.text_processor.generate_tags(chapter.content),
            'content_length': len(chapter.content),
            'word_count': len(chapter.content.split()),
            'is_summary': True
        }
        
        documents.append(chapter_summary)
        
        return documents
    
    def _index_document(self, document: Dict) -> bool:
        """Index a single document."""
        try:
            doc_id = document['paragraph_id']
            
            response = self.client.index(
                index=self.index_name,
                id=doc_id,
                body=document,
                refresh=True  # Make immediately searchable
            )
            
            logger.debug(f"Indexed document {doc_id}: {response['result']}")
            return response['result'] in ['created', 'updated']
            
        except Exception as e:
            logger.error(f"Error indexing document {document.get('paragraph_id', 'unknown')}: {str(e)}")
            return False
    
    def search(self, query: str, size: int = 10, filters: Optional[Dict] = None) -> Dict:
        """Search the indexed spiritual content."""
        try:
            # Build search query
            search_body = {
                "size": size,
                "query": {
                    "bool": {
                        "should": [
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": [
                                        "content^2",  # Content gets higher weight
                                        "book_title^1.5",
                                        "chapter_title^1.3",
                                        "tags^1.2"
                                    ],
                                    "type": "best_fields",
                                    "fuzziness": "AUTO"
                                }
                            },
                            {
                                "match_phrase": {
                                    "content": {
                                        "query": query,
                                        "boost": 2
                                    }
                                }
                            }
                        ],
                        "minimum_should_match": 1
                    }
                },
                "highlight": {
                    "fields": {
                        "content": {
                            "fragment_size": 150,
                            "number_of_fragments": 3
                        }
                    }
                },
                "_source": [
                    "book_title", "chapter_title", "content", "page_number",
                    "author", "tags", "paragraph_number"
                ],
                "sort": [
                    {"_score": {"order": "desc"}}
                ]
            }
            
            # Add filters if provided
            if filters:
                filter_conditions = []
                
                if filters.get('book_title'):
                    filter_conditions.append({
                        "term": {"book_title.keyword": filters['book_title']}
                    })
                
                if filters.get('author'):
                    filter_conditions.append({
                        "term": {"author.keyword": filters['author']}
                    })
                
                if filters.get('tags'):
                    filter_conditions.append({
                        "terms": {"tags": filters['tags']}
                    })
                
                if filter_conditions:
                    search_body["query"]["bool"]["filter"] = filter_conditions
            
            response = self.client.search(
                index=self.index_name,
                body=search_body
            )
            
            # Format results
            results = {
                'total_hits': response['hits']['total']['value'],
                'max_score': response['hits']['max_score'],
                'results': []
            }
            
            for hit in response['hits']['hits']:
                result = {
                    'score': hit['_score'],
                    'book_title': hit['_source']['book_title'],
                    'chapter_title': hit['_source']['chapter_title'],
                    'content': hit['_source']['content'][:300] + '...' if len(hit['_source']['content']) > 300 else hit['_source']['content'],
                    'page_number': hit['_source']['page_number'],
                    'author': hit['_source']['author'],
                    'tags': hit['_source'].get('tags', []),
                    'highlights': hit.get('highlight', {}).get('content', [])
                }
                results['results'].append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching: {str(e)}")
            return {'total_hits': 0, 'results': [], 'error': str(e)}
    
    def get_book_stats(self) -> Dict:
        """Get statistics about indexed books."""
        try:
            # Get total document count
            count_response = self.client.count(index=self.index_name)
            total_docs = count_response['count']
            
            # Get unique books
            books_agg = self.client.search(
                index=self.index_name,
                body={
                    "size": 0,
                    "aggs": {
                        "unique_books": {
                            "terms": {
                                "field": "book_title.keyword",
                                "size": 100
                            }
                        },
                        "unique_authors": {
                            "terms": {
                                "field": "author.keyword",
                                "size": 50
                            }
                        }
                    }
                }
            )
            
            books = [bucket['key'] for bucket in books_agg['aggregations']['unique_books']['buckets']]
            authors = [bucket['key'] for bucket in books_agg['aggregations']['unique_authors']['buckets']]
            
            return {
                'total_documents': total_docs,
                'unique_books': len(books),
                'unique_authors': len(authors),
                'books': books,
                'authors': authors
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {'error': str(e)}
    
    def delete_book(self, book_title: str) -> bool:
        """Delete all documents for a specific book."""
        try:
            response = self.client.delete_by_query(
                index=self.index_name,
                body={
                    "query": {
                        "term": {
                            "book_title.keyword": book_title
                        }
                    }
                }
            )
            
            deleted_count = response['deleted']
            logger.info(f"Deleted {deleted_count} documents for book '{book_title}'")
            return deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting book '{book_title}': {str(e)}")
            return False
    
    def health_check(self) -> Dict:
        """Check the health of OpenSearch connection and index."""
        try:
            # Check cluster health
            cluster_health = self.client.cluster.health()
            
            # Check index health
            index_exists = self.client.indices.exists(index=self.index_name)
            
            if index_exists:
                index_stats = self.client.indices.stats(index=self.index_name)
                doc_count = index_stats['indices'][self.index_name]['total']['docs']['count']
            else:
                doc_count = 0
            
            return {
                'cluster_status': cluster_health['status'],
                'cluster_name': cluster_health['cluster_name'],
                'index_exists': index_exists,
                'document_count': doc_count,
                'connection_healthy': True
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                'connection_healthy': False,
                'error': str(e)
            }