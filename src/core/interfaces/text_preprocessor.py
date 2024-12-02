from abc import ABC, abstractmethod
from typing import Dict, Any, Union
from azure.ai.documentintelligence.models import AnalyzeResult

class TextPreprocessor(ABC):
    """Abstract base class for text preprocessing implementations.
    
    This interface defines the contract for preprocessing extracted text
    to prepare it for LLM processing. Implementations should handle
    formatting, cleaning, and structuring of text while preserving
    important layout information.
    """
    
    @abstractmethod
    def process(self, content: Union[str, AnalyzeResult]) -> str:
        """Process and format the extracted text.
        
        Args:
            content: Raw text or AnalyzeResult from document extraction
                    Can be either plain text or structured data from extractors
            
        Returns:
            Preprocessed text with preserved layout information
            
        Raises:
            PreprocessingError: If text preprocessing fails
        """
        pass

    @abstractmethod
    def from_config(cls, config: Dict[str, Any]) -> 'TextPreprocessor':
        """Create a preprocessor instance from configuration.
        
        Args:
            config: Dictionary containing implementation-specific configuration
                   (e.g., formatting rules, table handling settings)
            
        Returns:
            Configured TextPreprocessor instance
            
        Raises:
            ValueError: If required configuration is missing or invalid
        """
        pass

    @property
    @abstractmethod
    def supported_formats(self) -> list[str]:
        """List of supported input formats (e.g., ['raw_text', 'azure_result']).
        
        Returns:
            List of input format types this preprocessor can handle
        """
        pass
