import pytest
from pathlib import Path
from datetime import date
from unittest.mock import Mock, patch

from ..core.interfaces.text_extractor import TextExtractor
from ..core.models.invoice import Invoice, Determinant, Charge
from ..core.exceptions import ExtractionError
from ..extractors.azure_docintel_extractor import AzureExtractor

# Test data
SAMPLE_PDF = Path(__file__).parent / "data" / "sample_invoice.pdf"
SAMPLE_TEXT = """
UTILITY BILL
Account: 123456789
Amount Due: $150.00
Due Date: 2024-03-15

Usage Details:
Electricity: 1000 kWh
Rate: $0.15/kWh
"""

@pytest.fixture
def mock_azure_client():
    with patch('azure.ai.formrecognizer.DocumentAnalysisClient') as mock:
        client = Mock()
        client.begin_analyze_document.return_value.result.return_value = {
            'content': SAMPLE_TEXT
        }
        mock.return_value = client
        yield mock

@pytest.fixture
def azure_extractor(mock_azure_client):
    return AzureExtractor(
        endpoint="https://test.cognitiveservices.azure.com/",
        key="test-key"
    )

def test_azure_extractor_initialization():
    """Test AzureExtractor initialization with config."""
    config = {
        'endpoint': 'https://test.cognitiveservices.azure.com/',
        'key': 'test-key'
    }
    extractor = AzureExtractor.from_config(config)
    assert isinstance(extractor, TextExtractor)
    assert extractor.endpoint == config['endpoint']
    assert extractor.key == config['key']

def test_azure_extractor_missing_config():
    """Test AzureExtractor initialization with missing config."""
    with pytest.raises(ValueError):
        AzureExtractor.from_config({})

def test_azure_extractor_extract_text(azure_extractor):
    """Test successful text extraction."""
    text = azure_extractor.extract(str(SAMPLE_PDF))
    assert "Account: 123456789" in text
    assert "Amount Due: $150.00" in text

def test_azure_extractor_invalid_file(azure_extractor):
    """Test extraction with invalid file."""
    with pytest.raises(ExtractionError):
        azure_extractor.extract("nonexistent.pdf")

def test_azure_extractor_service_error(mock_azure_client):
    """Test handling of Azure service errors."""
    mock_azure_client.return_value.begin_analyze_document.side_effect = Exception("Service error")
    extractor = AzureExtractor(endpoint="https://test.com", key="test-key")
    
    with pytest.raises(ExtractionError) as exc:
        extractor.extract(str(SAMPLE_PDF))
    assert "Service error" in str(exc.value)

def test_azure_extractor_supported_formats():
    """Test supported file format checking."""
    extractor = AzureExtractor(endpoint="https://test.com", key="test-key")
    assert extractor.supports_format("pdf")
    assert extractor.supports_format("jpeg")
    assert not extractor.supports_format("doc")

def test_azure_extractor_batch_processing(azure_extractor):
    """Test batch processing of multiple files."""
    files = [str(SAMPLE_PDF), str(SAMPLE_PDF)]
    results = azure_extractor.extract_batch(files)
    
    assert len(results) == 2
    for text in results:
        assert "Account: 123456789" in text 