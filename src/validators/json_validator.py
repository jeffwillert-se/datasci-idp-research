from typing import List, Dict, Tuple, Any
from jsonschema import validate, ValidationError as JsonSchemaError
from datetime import datetime
import yaml

from ..core.interfaces.validator import Validator
from ..core.models.invoice import Invoice, Determinant, Charge
from ..core.exceptions import ValidationError

class JSONValidator(Validator):
    """JSON Schema validator for invoice data."""
    
    DETERMINANT_SCHEMA = {
        "type": "object",
        "required": ["name", "value", "unit"],
        "properties": {
            "name": {"type": "string"},
            "value": {"type": "number"},
            "unit": {"type": "string"},
            "meter_number": {"type": "string"},
            "reading_type": {"type": "string"},
            "start_date": {"type": "string", "format": "date"},
            "end_date": {"type": "string", "format": "date"}
        }
    }
    
    CHARGE_SCHEMA = {
        "type": "object",
        "required": ["name", "amount", "category"],
        "properties": {
            "name": {"type": "string"},
            "amount": {"type": "number"},
            "category": {
                "type": "string",
                "enum": ["Usage", "Demand", "Fixed", "Tax"]
            },
            "unit_rate": {"type": "number"},
            "meter_number": {"type": "string"},
            "determinant": {
                "type": "object",
                "properties": DETERMINANT_SCHEMA["properties"]
            }
        }
    }
    
    INVOICE_SCHEMA = {
        "type": "object",
        "required": [
            "account_number",
            "invoice_number",
            "invoice_date",
            "due_date",
            "vendor_name",
            "customer_name",
            "determinants",
            "charges"
        ],
        "properties": {
            "account_number": {"type": "string"},
            "invoice_number": {"type": "string"},
            "invoice_date": {"type": "string", "format": "date"},
            "due_date": {"type": "string", "format": "date"},
            "vendor_name": {"type": "string"},
            "customer_name": {"type": "string"},
            "service_address": {"type": "string"},
            "billing_address": {"type": "string"},
            "determinants": {
                "type": "array",
                "items": DETERMINANT_SCHEMA
            },
            "charges": {
                "type": "array",
                "items": CHARGE_SCHEMA
            }
        }
    }

    def __init__(self):
        """Initialize validator with business rules."""
        with open('src/core/rules/business_rules.yaml', 'r') as f:
            self.rules = yaml.safe_load(f)
    
    def validate_unit(self, unit: str) -> bool:
        """Validate that a unit is in the allowed list."""
        return unit.upper() in [u.upper() for u in self.rules['allowed_units']]
    
    def validate(self, invoice: Invoice) -> Tuple[bool, List[str]]:
        """Validate the extracted invoice data."""
        errors = []
        
        try:
            # Validate against JSON schema
            validate(instance=invoice.dict(), schema=self.INVOICE_SCHEMA)
            
            # Validate components
            errors.extend(self.validate_determinants(invoice.determinants))
            errors.extend(self.validate_charges(invoice.charges, invoice.determinants))
            
            # Validate totals if available
            if hasattr(invoice, 'subtotals') and hasattr(invoice, 'total_amount'):
                errors.extend(self.validate_totals(
                    invoice.charges,
                    invoice.subtotals,
                    invoice.total_amount
                ))
                
        except JsonSchemaError as e:
            errors.append(f"Schema validation failed: {str(e)}")
            
        return len(errors) == 0, errors

    def validate_determinants(self, determinants: List[Determinant]) -> List[str]:
        """Validate extracted determinants."""
        errors = []
        
        for det in determinants:
            try:
                # Schema validation
                validate(instance=det.dict(), schema=self.DETERMINANT_SCHEMA)
                
                # Unit validation
                if not self.validate_unit(det.unit):
                    errors.append(f"Invalid unit '{det.unit}' for determinant: {det.name}")
                
                # Value validation
                try:
                    value = float(det.value)
                    if value < 0:
                        errors.append(f"Negative value for determinant: {det.name}")
                except ValueError:
                    errors.append(f"Non-numeric value for determinant: {det.name}")
                
                # Date validation if present
                if det.start_date and det.end_date:
                    try:
                        start = datetime.strptime(det.start_date, '%Y-%m-%d').date()
                        end = datetime.strptime(det.end_date, '%Y-%m-%d').date()
                        if start > end:
                            errors.append(
                                f"Invalid date range for {det.name}: "
                                f"{det.start_date} > {det.end_date}"
                            )
                    except ValueError:
                        errors.append(f"Invalid date format for determinant: {det.name}")
                
            except JsonSchemaError as e:
                errors.append(f"Invalid determinant {det.name}: {str(e)}")
        
        return errors

    def validate_charges(self, 
                        charges: List[Charge], 
                        determinants: List[Determinant]
                        ) -> List[str]:
        """Validate charges and their relationships to determinants."""
        errors = []
        
        for charge in charges:
            try:
                validate(instance=charge.dict(), schema=self.CHARGE_SCHEMA)
                
                # Validate determinant reference if present
                if charge.determinant:
                    if charge.determinant not in determinants:
                        errors.append(
                            f"Charge {charge.name} references unknown "
                            f"determinant: {charge.determinant.name}"
                        )
                        
                    # Validate unit rate calculation
                    if charge.unit_rate:
                        expected_amount = (
                            charge.unit_rate * charge.determinant.value
                        )
                        if not abs(charge.amount - expected_amount) <= 0.01:
                            errors.append(
                                f"Charge amount mismatch for {charge.name}: "
                                f"got {charge.amount}, expected {expected_amount}"
                            )
                            
            except JsonSchemaError as e:
                errors.append(f"Invalid charge {charge.name}: {str(e)}")
                
        return errors

    def validate_totals(self,
                       charges: List[Charge],
                       subtotals: Dict[str, float],
                       total_amount: float
                       ) -> List[str]:
        """Validate financial totals and subtotals."""
        errors = []
        
        # Validate charges sum to subtotals
        charge_sum = sum(c.amount for c in charges)
        subtotal_sum = sum(subtotals.values())
        
        if not abs(charge_sum - subtotal_sum) <= 0.01:
            errors.append(
                f"Charge sum ({charge_sum}) does not match "
                f"subtotal sum ({subtotal_sum})"
            )
            
        # Validate subtotals sum to total
        if not abs(subtotal_sum - total_amount) <= 0.01:
            errors.append(
                f"Subtotal sum ({subtotal_sum}) does not match "
                f"total amount ({total_amount})"
            )
            
        return errors

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'JSONValidator':
        """Create validator from configuration."""
        return cls()
