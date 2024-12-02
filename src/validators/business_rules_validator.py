from typing import Dict, Any, List, Tuple
from datetime import date, timedelta, datetime
from pathlib import Path
import yaml

from ..core.interfaces.validator import Validator
from ..core.models.invoice import Invoice, Determinant, Charge
from ..core.exceptions import ValidationError

class BusinessRulesValidator(Validator):
    """Validates invoice data against business rules and industry standards."""
    
    def __init__(self, rules_file: str = None):
        """Initialize the validator with business rules.
        
        Args:
            rules_file: Optional path to custom rules YAML file
        """
        if rules_file:
            self.rules_path = Path(rules_file)
        else:
            self.rules_path = Path(__file__).parent.parent / "core" / "rules" / "business_rules.yaml"
            
        if not self.rules_path.exists():
            raise ValueError(f"Rules file not found: {self.rules_path}")
            
        with open(self.rules_path) as f:
            self._rules = yaml.safe_load(f)
            
        # Convert day counts to timedelta
        self._rules['determinants']['date_rules']['max_period'] = timedelta(
            days=self._rules['determinants']['date_rules']['max_period_days']
        )
        self._rules['determinants']['date_rules']['future_tolerance'] = timedelta(
            days=self._rules['determinants']['date_rules']['future_tolerance_days']
        )

    def validate(self, invoice: Invoice) -> Tuple[bool, List[str]]:
        """Validate the extracted invoice data."""
        errors = []
        
        # Basic date validations
        errors.extend(self._validate_dates(invoice))
        
        # Component validations
        errors.extend(self.validate_determinants(invoice.determinants))
        errors.extend(self.validate_charges(invoice.charges, invoice.determinants))
        
        # Financial validations
        if hasattr(invoice, 'subtotals') and hasattr(invoice, 'total_amount'):
            errors.extend(self.validate_totals(
                invoice.charges,
                invoice.subtotals,
                invoice.total_amount
            ))
            
        return len(errors) == 0, errors

    def _validate_dates(self, invoice: Invoice) -> List[str]:
        """Validate invoice dates for consistency and reasonableness."""
        errors = []
        today = date.today()
        
        # Invoice date validations
        if invoice.invoice_date > today + self._rules['determinants']['date_rules']['future_tolerance']:
            errors.append(f"Invoice date {invoice.invoice_date} is too far in the future")
            
        # Billing period validations
        period_length = invoice.billing_period_end - invoice.billing_period_start
        if period_length > self._rules['determinants']['date_rules']['max_period']:
            errors.append(f"Billing period {period_length.days} days exceeds maximum allowed")
            
        if invoice.billing_period_end < invoice.billing_period_start:
            errors.append("Billing period end date precedes start date")
            
        return errors

    def validate_determinants(self, determinants: List[Determinant]) -> List[str]:
        """Validate extracted determinants."""
        errors = []
        
        for det in determinants:
            # Unit validation
            if det.unit not in self._rules['allowed_units']:
                errors.append(f"Invalid unit '{det.unit}' for determinant {det.name}")
                
            # Value range validation
            try:
                value = float(det.value)
                value_range = self._rules['determinants']['value_ranges']
                if value < value_range['min'] or value > value_range['max']:
                    errors.append(
                        f"Determinant {det.name} value {value} outside "
                        f"allowed range [{value_range['min']}, {value_range['max']}]"
                    )
            except ValueError:
                errors.append(f"Non-numeric value for determinant: {det.name}")
                
            # Date validation if present
            if det.start_date and det.end_date:
                try:
                    start = datetime.strptime(det.start_date, '%Y-%m-%d').date()
                    end = datetime.strptime(det.end_date, '%Y-%m-%d').date()
                    
                    # Check period length
                    period = end - start
                    if period > self._rules['determinants']['date_rules']['max_period']:
                        errors.append(
                            f"Billing period {period.days} days exceeds maximum "
                            f"allowed {self._rules['determinants']['date_rules']['max_period_days']} days"
                        )
                        
                    # Check for future dates
                    today = date.today()
                    future_tolerance = self._rules['determinants']['date_rules']['future_tolerance']
                    if end > today + future_tolerance:
                        errors.append(f"End date {end} is too far in the future")
                        
                except ValueError:
                    errors.append(f"Invalid date format for determinant: {det.name}")
                    
        return errors

    def validate_charges(self, 
                        charges: List[Charge], 
                        determinants: List[Determinant]
                        ) -> List[str]:
        """Validate charges and their relationships to determinants."""
        errors = []
        
        for charge in charges:
            # Category validation
            if charge.category not in self._rules['charges']['categories']:
                errors.append(f"Invalid category '{charge.category}' for charge {charge.name}")
                
            # Unit rate validation
            if charge.unit_rate and charge.determinant:
                commodity = self._get_commodity_from_unit(charge.determinant.unit)
                if commodity in self._rules['charges']['rate_ranges']:
                    rate_range = self._rules['charges']['rate_ranges'][commodity]
                    if not (rate_range['min'] <= charge.unit_rate <= rate_range['max']):
                        errors.append(
                            f"Unit rate {charge.unit_rate} for {charge.name} "
                            f"outside typical range [{rate_range['min']}, {rate_range['max']}]"
                        )
                        
            # Charge calculation validation
            if charge.determinant and charge.unit_rate:
                expected = round(charge.determinant.value * charge.unit_rate, 2)
                if abs(charge.amount - expected) > self._rules['totals']['tolerance']:
                    errors.append(
                        f"Charge amount {charge.amount} doesn't match "
                        f"calculation {expected} for {charge.name}"
                    )
                    
        return errors

    def validate_totals(self,
                       charges: List[Charge],
                       subtotals: Dict[str, float],
                       total_amount: float
                       ) -> List[str]:
        """Validate financial totals and subtotals."""
        errors = []
        tolerance = self._rules['totals']['tolerance']
        
        # Group charges by category
        category_totals = {}
        for charge in charges:
            if charge.category not in category_totals:
                category_totals[charge.category] = 0
            category_totals[charge.category] += charge.amount
            
        # Validate category subtotals
        for category, total in category_totals.items():
            if category in subtotals:
                if abs(total - subtotals[category]) > tolerance:
                    errors.append(
                        f"{category} charges sum ({total}) doesn't match "
                        f"subtotal ({subtotals[category]})"
                    )
                    
        # Validate total amount
        calculated_total = sum(subtotals.values())
        if abs(calculated_total - total_amount) > tolerance:
            errors.append(
                f"Subtotals sum ({calculated_total}) doesn't match "
                f"total amount ({total_amount})"
            )
            
        return errors

    def _get_commodity_from_unit(self, unit: str) -> str:
        """Helper to determine commodity type from unit."""
        for commodity, units in self._rules['determinants']['allowed_units'].items():
            if unit in units:
                return commodity
        return "unknown"

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'BusinessRulesValidator':
        """Create validator from configuration."""
        rules_file = config.get('rules_file')
        return cls(rules_file=rules_file)

    @property
    def validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Return the current validation rules configuration."""
        return self._rules
