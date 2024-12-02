from dataclasses import dataclass, field
from datetime import date
from typing import List, Dict, Optional, Union, Any
import json
import os
from pathlib import Path
from deepdiff import DeepDiff

@dataclass
class Determinant:
    """Measured quantity used for billing calculations."""
    def __init__(self,
                 name: str,
                 value: str,
                 unit: str = 'N/A',
                 meter: str = 'N/A',
                 commodity: str = 'N/A',
                 reading_type: Optional[str] = None,
                 start_date: Optional[str] = None,
                 end_date: Optional[str] = None):
        self.name = name
        self.value = value
        self.unit = unit
        self.meter = meter
        self.commodity = commodity
        self.reading_type = reading_type
        self.start_date = start_date
        self.end_date = end_date

@dataclass
class Charge:
    """Represents a billing charge or fee."""
    name: str
    amount: float
    category: str  # e.g., "Usage", "Demand", "Fixed", "Tax"
    commodity: str
    currency: str = "USD"
    determinant: Optional[Determinant] = None
    unit_rate: Optional[float] = None
    meter_number: Optional[str] = None
    notes: Optional[str] = None

@dataclass
class Invoice:
    """Data model representing an extracted energy invoice."""
    
    # Required fields (no defaults)
    account_number: str
    invoice_number: str
    invoice_date: date
    billing_period_start: date
    billing_period_end: date
    vendor_name: str
    customer_name: str
    service_address: str
    meter_numbers: List[str]
    determinants: List[Determinant]
    charges: List[Charge]
    subtotals: Dict[str, float]
    total_amount: float
    source_file: str
    extraction_date: date
    commodities: List[str]  # List of commodities present in invoice (e.g., ["Electric Power", "Natural Gas"])
    
    # Optional fields (with defaults)
    due_date: Optional[date] = None
    billing_address: Optional[str] = None
    previous_balance: Optional[float] = None
    payments: Optional[float] = None
    late_fees: Optional[float] = None
    currency: str = "USD"
    confidence_score: Optional[float] = None
    validation_errors: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        """Return a formatted string representation of the invoice."""
        lines = []
        
        # Header
        lines.append("=" * 80)
        lines.append(f"INVOICE DETAILS - {self.vendor_name}")
        lines.append("=" * 80)
        
        # Account Information
        lines.append("\nACCOUNT INFORMATION:")
        lines.append("-" * 20)
        lines.append(f"Account Number: {self.account_number}")
        lines.append(f"Invoice Number: {self.invoice_number}")
        lines.append(f"Customer Name: {self.customer_name}")
        lines.append(f"Service Address: {self.service_address}")
        lines.append(f"Invoice Date: {self.invoice_date}")
        lines.append(f"Billing Period: {self.billing_period_start} to {self.billing_period_end}")
        
        # Group determinants and charges by commodity
        for commodity in self.commodities:
            lines.append(f"\n{commodity.upper()}:")
            lines.append("=" * len(f"{commodity.upper()}:"))
            
            # Determinants for this commodity
            lines.append("\nDETERMINANTS:")
            lines.append("-" * 20)
            commodity_determinants = [d for d in self.determinants if d.commodity.lower() == commodity.lower()]
            if commodity_determinants:
                for det in commodity_determinants:
                    lines.append(f"{det.name}: {det.value} {det.unit}")
                    if det.meter != "N/A":
                        lines.append(f"  Meter: {det.meter}")
            else:
                lines.append("No determinants found")
            
            # Charges for this commodity
            lines.append("\nCHARGES:")
            lines.append("-" * 20)
            commodity_charges = [c for c in self.charges if c.commodity.lower() == commodity.lower()]
            if commodity_charges:
                for charge in commodity_charges:
                    lines.append(f"{charge.name}: ${charge.amount:.2f}")
                    if charge.unit_rate:
                        lines.append(f"  Rate: ${charge.unit_rate:.4f} per unit")
            else:
                lines.append("No charges found")
                
            # Subtotal for this commodity
            if commodity in self.subtotals:
                lines.append(f"\nSubtotal: ${self.subtotals[commodity]:.2f}")
        
        # Total Amount
        lines.append("\nTOTAL AMOUNT:")
        lines.append("-" * 20)
        lines.append(f"${self.total_amount:.2f}")
        
        # Validation Errors (if any)
        if self.validation_errors:
            lines.append("\nVALIDATION WARNINGS:")
            lines.append("-" * 20)
            for error in self.validation_errors:
                lines.append(f"- {error}")
        
        return "\n".join(lines)

    def to_json(self) -> dict:
        """Convert invoice data to a JSON-serializable dictionary."""
        return {
            "account_info": {
                "account_number": self.account_number,
                "invoice_number": self.invoice_number,
                "invoice_date": self.invoice_date.isoformat(),
                "billing_period_start": self.billing_period_start.isoformat(),
                "billing_period_end": self.billing_period_end.isoformat(),
                "vendor_name": self.vendor_name,
                "customer_name": self.customer_name,
                "service_address": self.service_address,
                "meter_numbers": self.meter_numbers,
                "due_date": self.due_date.isoformat() if self.due_date else None,
                "billing_address": self.billing_address,
                "source_file": self.source_file,
                "extraction_date": self.extraction_date.isoformat()
            },
            "determinants": [
                {
                    "name": det.name,
                    "value": det.value,
                    "unit": det.unit,
                    "meter": det.meter,
                    "commodity": det.commodity,
                    "reading_type": det.reading_type,
                    "start_date": det.start_date,
                    "end_date": det.end_date
                } for det in self.determinants
            ],
            "charges": [
                {
                    "name": charge.name,
                    "amount": charge.amount,
                    "category": charge.category,
                    "commodity": charge.commodity,
                    "currency": charge.currency,
                    "unit_rate": charge.unit_rate,
                    "meter_number": charge.meter_number,
                    "notes": charge.notes
                } for charge in self.charges
            ],
            "summary": {
                "subtotals": self.subtotals,
                "total_amount": self.total_amount,
                "previous_balance": self.previous_balance,
                "payments": self.payments,
                "late_fees": self.late_fees,
                "currency": self.currency,
                "commodities": self.commodities
            },
            "metadata": {
                "confidence_score": self.confidence_score,
                "validation_errors": self.validation_errors
            }
        }

    def save_json(self, output_dir: Optional[str] = None) -> str:
        """Save invoice data to JSON file.
        
        Args:
            output_dir: Optional directory to save JSON file. If None,
                       uses same directory as source file.
                       
        Returns:
            Path to saved JSON file
        """
        # Get source file path and name
        source_path = Path(self.source_file)
        file_stem = source_path.stem
        
        # Determine output directory
        if output_dir:
            out_path = Path(output_dir)
        else:
            out_path = source_path.parent
            
        # Create output directory if it doesn't exist
        out_path.mkdir(parents=True, exist_ok=True)
            
        # Create output filename: original_name_extracted.json
        json_path = out_path / f"{file_stem}_extracted.json"
        
        # Save JSON file
        with open(json_path, 'w') as f:
            json.dump(self.to_json(), f, indent=2)
            
        return str(json_path)
    
    @classmethod
    def load_json(cls, json_path: str) -> 'Invoice':
        """Load invoice data from JSON file.
        
        Args:
            json_path: Path to JSON file
            
        Returns:
            Invoice object
        """
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        # Convert dates from ISO format strings
        for date_field in ['invoice_date', 'billing_period_start', 'billing_period_end', 
                          'due_date', 'extraction_date']:
            if date_field in data['account_info'] and data['account_info'][date_field]:
                data['account_info'][date_field] = datetime.strptime(
                    data['account_info'][date_field], 
                    '%Y-%m-%d'
                ).date()
                
        # Create Determinant objects
        determinants = [Determinant(**d) for d in data['determinants']]
        
        # Create Charge objects
        charges = [Charge(**c) for c in data['charges']]
        
        # Create Invoice object
        return cls(
            **data['account_info'],
            determinants=determinants,
            charges=charges,
            **data['summary'],
            **data['metadata']
        )
    
    def compare_to_verified(self, verified_path: str) -> Dict[str, Any]:
        """Compare extraction results to verified data.
        
        Args:
            verified_path: Path to verified JSON file
            
        Returns:
            Dictionary containing comparison results and differences
        """
        try:
            # Load verified data
            verified = self.load_json(verified_path)
            
            # Convert both invoices to dictionaries for comparison
            current_data = self.to_json()
            verified_data = verified.to_json()
            
            # Compare using DeepDiff
            diff = DeepDiff(verified_data, current_data, ignore_order=True)
            
            # Calculate accuracy metrics
            total_fields = self._count_fields(verified_data)
            correct_fields = total_fields - len(diff.get('values_changed', {}))
            accuracy = correct_fields / total_fields if total_fields > 0 else 0
            
            return {
                'accuracy': accuracy,
                'total_fields': total_fields,
                'correct_fields': correct_fields,
                'differences': diff,
                'has_differences': bool(diff)
            }
            
        except Exception as e:
            return {
                'error': f"Comparison failed: {str(e)}",
                'accuracy': 0,
                'has_differences': True
            }
    
    def _count_fields(self, data: Dict) -> int:
        """Helper method to count total fields in nested dictionary."""
        count = 0
        for key, value in data.items():
            if isinstance(value, dict):
                count += self._count_fields(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        count += self._count_fields(item)
                    else:
                        count += 1
            else:
                count += 1
        return count
