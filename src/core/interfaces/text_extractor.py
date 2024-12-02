from abc import ABC, abstractmethod
from typing import Dict, Any
from ..models.extraction_result import ExtractionResult

class TextExtractor(ABC):
    """Abstract base class for text extraction implementations.
    
    This interface defines the contract for extracting text and layout information
    from documents. Implementations should handle different document formats (PDF, images)
    and maintain spatial/layout information where possible.
    """
    
    @abstractmethod
    def extract(self, file_path: str) -> ExtractionResult:
        """Extract text and layout information from a document.
        
        Args:
            file_path: Path to the document file to process
            
        Returns:
            ExtractionResult containing:
                - raw_text: Processed text with layout information preserved
                - metadata: Document metadata (page count, language, etc.)
                - raw_response: Original extraction response for further processing
                
        Raises:
            FileNotFoundError: If the document file cannot be found
            ExtractionError: If text extraction fails
        """
        pass

    @abstractmethod
    def from_config(cls, config: Dict[str, Any]) -> 'TextExtractor':
        """Create an extractor instance from configuration.
        
        Args:
            config: Dictionary containing implementation-specific configuration
                   (e.g., API keys, endpoints, model settings)
            
        Returns:
            Configured TextExtractor instance
            
        Raises:
            ValueError: If required configuration is missing or invalid
        """
        pass

    @property
    @abstractmethod
    def supported_formats(self) -> list[str]:
        """List of supported document formats (e.g., ['pdf', 'png', 'jpg']).
        
        Returns:
            List of file extensions this extractor can process
        """
        pass
