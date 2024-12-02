from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple
from ..models.invoice import Invoice, Determinant, Charge

class DataExtractor(ABC):
    """Abstract base class for LLM-based data extraction implementations.
    
    This interface defines the contract for extracting structured data from
    preprocessed text using Large Language Models. Implementations should
    handle the three main components of utility invoices:
    1. Account Information
    2. Determinants (measured quantities)
    3. Charges (fees, rates, and calculations)
    """
    
    @abstractmethod
    def extract(self, text: str, source_file: str) -> Invoice:
        """Extract structured data from preprocessed text."""
        pass

    @abstractmethod
    def extract_account_info(self, text: str) -> Dict[str, Any]:
        """Extract account and billing information.
        
        Args:
            text: Preprocessed text containing invoice information
            
        Returns:
            Dictionary containing account details (numbers, dates, addresses)
            
        Raises:
            ExtractionError: If critical account info is missing
        """
        pass

    @abstractmethod
    def extract_determinants(self, text: str) -> List[Determinant]:
        """Extract measured quantities used for billing calculations.
        
        Args:
            text: Preprocessed text containing invoice information
            
        Returns:
            List of Determinant objects with quantities and units
            
        Raises:
            ExtractionError: If determinant parsing fails
            ValidationError: If determinant values are invalid
        """
        pass

    @abstractmethod
    def extract_charges(self, text: str, determinants: List[Determinant]) -> List[Charge]:
        """Extract billing charges and associate with determinants where applicable.
        
        Args:
            text: Preprocessed text containing invoice information
            determinants: List of extracted determinants for charge association
            
        Returns:
            List of Charge objects with amounts and categories
            
        Raises:
            ExtractionError: If charge parsing fails
            ValidationError: If charge calculations are invalid
        """
        pass

    @abstractmethod
    def from_config(cls, config: Dict[str, Any]) -> 'DataExtractor':
        """Create an extractor instance from configuration."""
        pass

    @property
    @abstractmethod
    def supported_fields(self) -> Dict[str, Dict[str, str]]:
        """Dictionary of supported extraction fields by category.
        
        Returns:
            Dictionary with categories and their supported fields:
            {
                'account_info': {
                    'account_number': 'Customer account identifier',
                    'billing_period': 'Start and end dates for billing cycle'
                },
                'determinants': {
                    'usage': 'Total consumption quantity',
                    'demand': 'Peak demand reading'
                },
                'charges': {
                    'energy_charge': 'Cost per unit of consumption',
                    'demand_charge': 'Cost per unit of peak demand'
                }
            }
        """
        pass
