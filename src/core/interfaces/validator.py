from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional
from ..models.invoice import Invoice, Determinant, Charge

class Validator(ABC):
    """Abstract base class for validation implementations.
    
    This interface defines the contract for validating extracted invoice data.
    Implementations should handle:
    1. Schema validation (required fields, data types)
    2. Business rules (calculations, relationships)
    3. Commodity-specific validations
    4. Cross-field validations (determinants vs charges)
    """
    
    @abstractmethod
    def validate(self, invoice: Invoice) -> Tuple[bool, List[str]]:
        """Validate the extracted invoice data.
        
        Args:
            invoice: Invoice object containing extracted data
            
        Returns:
            Tuple containing:
                - bool: True if validation passed, False otherwise
                - List[str]: List of validation error messages
        """
        pass

    @abstractmethod
    def validate_determinants(self, determinants: List[Determinant]) -> List[str]:
        """Validate extracted determinants.
        
        Args:
            determinants: List of extracted determinants
            
        Returns:
            List of validation error messages (empty if valid)
            
        Validation includes:
            - Required fields (name, value, unit)
            - Valid units for each determinant type
            - Reasonable value ranges
            - Date consistency
        """
        pass

    @abstractmethod
    def validate_charges(self, 
                        charges: List[Charge], 
                        determinants: List[Determinant]
                        ) -> List[str]:
        """Validate charges and their relationships to determinants.
        
        Args:
            charges: List of extracted charges
            determinants: List of determinants for cross-validation
            
        Returns:
            List of validation error messages (empty if valid)
            
        Validation includes:
            - Required fields (name, amount)
            - Charge calculations using determinants
            - Unit rate consistency
            - Subtotal reconciliation
        """
        pass

    @abstractmethod
    def validate_totals(self, 
                       charges: List[Charge],
                       subtotals: Dict[str, float],
                       total_amount: float
                       ) -> List[str]:
        """Validate financial totals and subtotals.
        
        Args:
            charges: List of all charges
            subtotals: Dictionary of subtotals by category
            total_amount: Total invoice amount
            
        Returns:
            List of validation error messages (empty if valid)
            
        Validation includes:
            - Charges sum to subtotals by category
            - Subtotals sum to total amount
            - Previous balance and payment reconciliation
        """
        pass

    @abstractmethod
    def from_config(cls, config: Dict[str, Any]) -> 'Validator':
        """Create a validator instance from configuration."""
        pass

    @property
    @abstractmethod
    def validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Dictionary of validation rules by category.
        
        Returns:
            Nested dictionary of validation rules:
            {
                'determinants': {
                    'allowed_units': {
                        'electricity': ['kWh', 'MWh'],
                        'demand': ['kW', 'MW'],
                        'gas': ['therms', 'CCF', 'MCF']
                    },
                    'value_ranges': {
                        'min': 0,
                        'max': 1000000
                    }
                },
                'charges': {
                    'required_fields': ['name', 'amount', 'category'],
                    'categories': ['Usage', 'Demand', 'Fixed', 'Tax']
                },
                'totals': {
                    'tolerance': 0.01,  # For floating point comparisons
                    'require_subtotal_match': True
                }
            }
        """
        pass
