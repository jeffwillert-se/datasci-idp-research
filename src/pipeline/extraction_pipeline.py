from typing import Optional, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

from ..core.interfaces.text_extractor import TextExtractor
from ..core.interfaces.text_preprocessor import TextPreprocessor
from ..core.interfaces.data_extractor import DataExtractor
from ..core.interfaces.validator import Validator
from ..core.models.extraction_result import ExtractionResult
from ..core.models.invoice import Invoice
from ..core.exceptions import ExtractionError, PreprocessingError, ValidationError

class ExtractionPipeline:
    """Orchestrates the invoice data extraction process.
    
    Coordinates the four main components:
    1. Text extraction from documents
    2. Text preprocessing
    3. Data extraction using LLMs
    4. Validation of extracted data
    """
    
    def __init__(
        self,
        text_extractor: TextExtractor,
        preprocessor: TextPreprocessor,
        data_extractor: DataExtractor,
        validator: Optional[Validator] = None
    ):
        """Initialize the extraction pipeline.
        
        Args:
            text_extractor: Component for extracting text from documents
            preprocessor: Component for preprocessing extracted text
            data_extractor: Component for extracting structured data
            validator: Optional component for validating extracted data
        """
        self.text_extractor = text_extractor
        self.preprocessor = preprocessor
        self.data_extractor = data_extractor
        self.validator = validator

    def process(self, file_path: str) -> Invoice:
        """Process an invoice file through the extraction pipeline.
        
        Args:
            file_path: Path to the invoice document
            
        Returns:
            Invoice object containing extracted and validated data
            
        Raises:
            FileNotFoundError: If document file cannot be found
            ExtractionError: If text or data extraction fails
            PreprocessingError: If text preprocessing fails
            ValidationError: If extracted data fails validation
        """
        try:
            # Extract text from document
            extraction_result = self.text_extractor.extract(file_path)
            
            # Preprocess extracted text
            processed_text = self.preprocessor.process(extraction_result)
            
            # Extract structured data with source file path
            invoice = self.data_extractor.extract(processed_text, file_path)
            
            # Validate if validator provided
            if self.validator:
                is_valid, validation_errors = self.validator.validate(invoice)
                invoice.validation_errors = validation_errors
                
            return invoice
            
        except Exception as e:
            logger.error(f"Pipeline processing failed: {str(e)}")
            raise

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'ExtractionPipeline':
        """Create a pipeline instance from configuration.
        
        Args:
            config: Dictionary containing component configurations
            
        Returns:
            Configured ExtractionPipeline instance
        """
        # Create components from their configs
        text_extractor = TextExtractor.from_config(config.get('text_extractor', {}))
        preprocessor = TextPreprocessor.from_config(config.get('preprocessor', {}))
        data_extractor = DataExtractor.from_config(config.get('data_extractor', {}))
        
        validator = None
        if validator_config := config.get('validator'):
            validator = Validator.from_config(validator_config)
            
        return cls(
            text_extractor=text_extractor,
            preprocessor=preprocessor,
            data_extractor=data_extractor,
            validator=validator
        )
