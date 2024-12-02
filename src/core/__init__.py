from pathlib import Path

from .interfaces.text_extractor import TextExtractor
from .interfaces.text_preprocessor import TextPreprocessor
from .interfaces.data_extractor import DataExtractor
from .interfaces.validator import Validator

from .models.invoice import Invoice
from .models.extraction_result import ExtractionResult

from .exceptions import (
    InvoiceExtractorError,
    PreprocessingError,
    ExtractionError,
    ValidationError
)

# Constants used across the application
TABLE_START_TOKEN = "<TABLE>"
TABLE_END_TOKEN = "</TABLE>"
PAGE_TOKEN = "<PAGE>"

# Paths
PROMPTS_DIR = Path(__file__).parent / "prompts"
AZURE_OPENAI_PROMPTS_DIR = PROMPTS_DIR / "azure_openai"

__all__ = [
    # Interfaces
    'TextExtractor',
    'TextPreprocessor',
    'DataExtractor',
    'Validator',
    
    # Models
    'Invoice',
    'ExtractionResult',
    
    # Exceptions
    'InvoiceExtractorError',
    'PreprocessingError',
    'ExtractionError',
    'ValidationError',
    
    # Constants
    'TABLE_START_TOKEN',
    'TABLE_END_TOKEN',
    'PAGE_TOKEN',
    
    # Paths
    'PROMPTS_DIR',
    'AZURE_OPENAI_PROMPTS_DIR',
]
