from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class ExtractionResult:
    """Data model representing the result of text extraction from a document.
    
    This class stores both the processed text output and metadata about the
    extraction process, including the original response from the extraction
    service for potential further processing.
    """
    
    # The processed text with preserved layout information
    raw_text: str
    
    # Document and extraction metadata
    metadata: Dict[str, Any]
    
    # Original extraction response (e.g., Azure AnalyzeResult)
    raw_response: Optional[Any] = None
    
    def __post_init__(self):
        """Validate required metadata fields."""
        required_fields = {'page_count', 'language', 'file_path'}
        if not all(field in self.metadata for field in required_fields):
            raise ValueError(f"Metadata must contain: {required_fields}")
