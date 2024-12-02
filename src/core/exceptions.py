class InvoiceExtractorError(Exception):
    """Base exception class for invoice extractor errors."""
    pass

class PreprocessingError(InvoiceExtractorError):
    """Raised when text preprocessing fails."""
    pass

class ExtractionError(InvoiceExtractorError):
    """Raised when data extraction fails."""
    pass

class ValidationError(InvoiceExtractorError):
    """Raised when data validation fails."""
    pass 