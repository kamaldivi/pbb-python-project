import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / '.env')

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
PDF_DIR = DATA_DIR / "pdfs"
PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
PDF_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# OpenSearch Configuration
OPENSEARCH_CONFIG = {
    'host': os.getenv('OPENSEARCH_HOST', 'localhost'),
    'port': int(os.getenv('OPENSEARCH_PORT', 9200)),
    'use_ssl': os.getenv('OPENSEARCH_USE_SSL', 'false').lower() == 'true',
    'verify_certs': os.getenv('OPENSEARCH_VERIFY_CERTS', 'false').lower() == 'true',
    'ssl_assert_hostname': False,
    'ssl_show_warn': False,
    'username': os.getenv('OPENSEARCH_USERNAME', 'admin'),
    'password': os.getenv('OPENSEARCH_PASSWORD', 'admin'),
}

# Index Configuration
INDEX_CONFIG = {
    'index_name': 'srila-narayan-maharaj-books',
    'settings': {
        'number_of_shards': 1,
        'number_of_replicas': 0,
        'analysis': {
            'analyzer': {
                'spiritual_text_analyzer': {
                    'type': 'custom',
                    'tokenizer': 'standard',
                    'filter': [
                        'lowercase',
                        'stop',
                        'porter_stem'
                    ]
                }
            }
        }
    },
    'mappings': {
        'properties': {
            'book_title': {
                'type': 'text',
                'analyzer': 'spiritual_text_analyzer',
                'fields': {
                    'keyword': {
                        'type': 'keyword'
                    }
                }
            },
            'chapter_title': {
                'type': 'text',
                'analyzer': 'spiritual_text_analyzer'
            },
            'content': {
                'type': 'text',
                'analyzer': 'spiritual_text_analyzer'
            },
            'page_number': {
                'type': 'integer'
            },
            'paragraph_id': {
                'type': 'keyword'
            },
            'author': {
                'type': 'keyword'
            },
            'language': {
                'type': 'keyword'
            },
            'tags': {
                'type': 'keyword'
            },
            'timestamp': {
                'type': 'date'
            },
            'file_path': {
                'type': 'keyword'
            }
        }
    }
}

# Text Processing Configuration
TEXT_PROCESSING = {
    'min_paragraph_length': 50,
    'max_paragraph_length': 5000,
    'clean_patterns': [
        r'\s+',  # Multiple whitespaces
        r'^\s*\d+\s*$',  # Lines with only numbers (page numbers)
        r'^[\s\-_=]+$',  # Lines with only separators
    ],
    'spiritual_terms': [
        'Krishna', 'Krsna', 'Radha', 'Gopis', 'Vrindavan', 'Vraja',
        'Gurudeva', 'Srila', 'Maharaj', 'Prabhu', 'Devi', 'Das',
        'Bhakti', 'Prema', 'Raga', 'Vaidhi', 'Sadhana', 'Siddha',
        'Hari', 'Hare', 'Rama', 'Govinda', 'Gopala', 'Madhava'
    ]
}

# Logging Configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'simple': {
            'format': '%(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'simple'
        },
        'file': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': str(LOGS_DIR / 'pbb_parser.log'),
            'mode': 'a'
        }
    },
    'loggers': {
        'pbb_parser': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
            'propagate': False
        }
    }
}