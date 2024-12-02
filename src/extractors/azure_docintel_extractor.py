from typing import Dict, Any
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult

from ..core.interfaces.text_extractor import TextExtractor
from ..core.models.extraction_result import ExtractionResult
from ..preprocessors.basic_preprocessor import BasicPreprocessor

class AzureDocIntelExtractor(TextExtractor):
    """Azure Document Intelligence implementation of the TextExtractor interface."""
    
    def __init__(self, endpoint: str, key: str):
        """Initialize the Azure Document Intelligence client.
        
        Args:
            endpoint: Azure Document Intelligence endpoint
            key: Azure Document Intelligence API key
        """
        self.client = DocumentIntelligenceClient(
            endpoint=endpoint, 
            credential=AzureKeyCredential(key)
        )
        self.preprocessor = BasicPreprocessor()

    def extract(self, file_path: str) -> ExtractionResult:
        """Extract text and layout information from a document.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            ExtractionResult containing the extracted text and metadata
        """
        # Read and analyze document
        with open(file_path, "rb") as f:
            poller = self.client.begin_analyze_document(
                "prebuilt-layout",
                analyze_request=f,
                content_type="application/octet-stream"
            )
        result = poller.result()

        # Preprocess the result to format tables and text
        processed_text = self.preprocessor.process(result)

        # Create extraction result
        return ExtractionResult(
            raw_text=processed_text,
            metadata={
                "page_count": len(result.pages),
                "language": result.languages[0] if result.languages else "unknown",
                "file_path": file_path
            },
            raw_response=result
        )

    @staticmethod
    def from_config(config: Dict[str, Any]) -> 'AzureDocIntelExtractor':
        """Create an extractor instance from configuration.
        
        Args:
            config: Dictionary containing 'endpoint' and 'key'
            
        Returns:
            Configured AzureDocIntelExtractor instance
        """
        required_keys = ['endpoint', 'key']
        if not all(k in config for k in required_keys):
            raise ValueError(f"Config must contain: {required_keys}")
            
        return AzureDocIntelExtractor(
            endpoint=config['endpoint'],
            key=config['key']
        )

    @property
    def supported_formats(self) -> list[str]:
        """Return list of supported file formats.
        
        Returns:
            List of supported file extensions
        """
        return ['pdf', 'jpeg', 'jpg', 'png', 'tiff', 'tif', 'bmp']
