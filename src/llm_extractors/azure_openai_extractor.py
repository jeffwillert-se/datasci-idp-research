from typing import Dict, Any, List, Optional
from datetime import datetime
from openai import AzureOpenAI
import json
import yaml
import logging
from pathlib import Path

from ..core.interfaces.data_extractor import DataExtractor
from ..core.models.invoice import Invoice, Determinant, Charge
from ..core.exceptions import ExtractionError, ValidationError

class AzureOpenAIExtractor(DataExtractor):
    """Azure OpenAI implementation of the DataExtractor interface."""
    
    DEFAULT_PROMPTS_DIR = Path(__file__).parent.parent / "core" / "prompts" / "azure_openai"
    
    def __init__(self, 
                 api_key: str, 
                 endpoint: str, 
                 deployment: str,
                 prompts_dir: Optional[Path] = None):
        """Initialize the Azure OpenAI client.
        
        Args:
            api_key: Azure OpenAI API key
            endpoint: Azure OpenAI endpoint URL
            deployment: Model deployment name
            prompts_dir: Optional custom directory containing prompt YAML files
        """
        self.client = AzureOpenAI(
            api_key=api_key,
            api_version="2024-02-01",
            azure_endpoint=endpoint
        )
        self.deployment = deployment
        self.prompts_dir = prompts_dir or self.DEFAULT_PROMPTS_DIR
        self.prompts = self._load_prompts()
    
    def _load_prompts(self) -> Dict[str, Dict[str, str]]:
        """Load prompts from YAML files."""
        prompts = {}
        for yaml_file in self.prompts_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                prompts[yaml_file.stem] = yaml.safe_load(f)
        return prompts
    
    def set_prompt(self, prompt_name: str, prompt_content: Dict[str, str]) -> None:
        """Override a prompt configuration.
        
        Args:
            prompt_name: Name of the prompt to override (e.g., 'account_info')
            prompt_content: Dictionary containing prompt configuration
        """
        self.prompts[prompt_name] = prompt_content

    def _call_azure_openai(self, prompt_name: str, content: str) -> str:
        """Make API call to Azure OpenAI using named prompt."""
        if prompt_name not in self.prompts:
            raise ValueError(f"Unknown prompt: {prompt_name}")
            
        prompt = self.prompts[prompt_name]
        try:
            # Log the prompt and user content
            logging.info(f"\nPrompt '{prompt_name}':")
            logging.info(f"System: {prompt['system']}")
            logging.info(f"User: {content}\n")
            
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": prompt["system"]},
                    {"role": "user", "content": "INVOICE TEXT: \n\n" + content}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            print("RESPONSE:", response)
            response_content = response.choices[0].message.content
            
            # Log the response
            logging.info(f"Response from {prompt_name}:")
            logging.info(f"{response_content}\n")
            
            return response_content
        except Exception as e:
            raise ExtractionError(f"Azure OpenAI API call failed: {str(e)}")

    def extract(self, text: str, source_file: str) -> Invoice:
        """Extract structured data from preprocessed text."""
        # Extract components in sequence
        account_info = self.extract_account_info(text)
        determinants = self.extract_determinants(text)
        charges = self.extract_charges(text, determinants)
        
        # Create Invoice object
        return Invoice(
            **account_info,
            determinants=determinants,
            charges=charges,
            source_file=source_file,
            extraction_date=datetime.now().date(),
            validation_errors=[]  # Will be populated by validator
        )

    def extract_account_info(self, text: str) -> Dict[str, Any]:
        """Extract account and billing information."""
        try:
            response = self._call_azure_openai('account_info', text)
            account_data = self._parse_json_response(response)
            
            # Convert date strings to datetime.date objects
            date_fields = ['invoice_date', 'billing_period_start', 'billing_period_end']
            for field in date_fields:
                if field in account_data:
                    account_data[field] = datetime.strptime(account_data[field], '%Y-%m-%d').date()
            
            # Required fields for Invoice model
            required_fields = {
                'account_number', 'invoice_number', 'invoice_date',
                'billing_period_start', 'billing_period_end', 'vendor_name',
                'customer_name', 'service_address', 'meter_numbers',
                'subtotals', 'total_amount', 'commodities'
            }
            
            # Validate all required fields are present
            missing_fields = required_fields - set(account_data.keys())
            if missing_fields:
                raise ExtractionError(f"Missing required account info fields: {missing_fields}")
            
            return account_data
        except Exception as e:
            raise ExtractionError(f"Failed to extract account info: {str(e)}")

    def extract_determinants(self, text: str) -> List[Determinant]:
        """Extract measured quantities used for billing calculations."""
        try:
            response = self._call_azure_openai('determinants', text)
            determinants_data = self._parse_json_response(response)
            
            # Handle wrapped response
            if isinstance(determinants_data, dict):
                if 'determinants' in determinants_data:
                    determinants_data = determinants_data['determinants']
                elif len(determinants_data) == 1:
                    determinants_data = list(determinants_data.values())[0]
            
            # Ensure we have a list
            if not isinstance(determinants_data, list):
                determinants_data = [determinants_data]
            
            # Create Determinant objects with numeric conversion
            determinants = []
            for d in determinants_data:
                try:
                    # Convert value to float, handling potential string formats
                    value = d.get('value')
                    if isinstance(value, str):
                        value = float(value.replace(',', ''))
                    
                    determinants.append(Determinant(
                        name=d.get('name'),
                        value=value,
                        unit=d.get('unit', 'N/A'),
                        commodity=d.get('commodity'),
                        meter=d.get('meter_number', 'N/A')
                    ))
                except (ValueError, TypeError) as e:
                    raise ExtractionError(f"Invalid determinant value format: {d.get('value')}")
            
            return determinants
        except Exception as e:
            raise ExtractionError(f"Failed to extract determinants: {str(e)}")

    def extract_charges(self, text: str, determinants: List[Determinant]) -> List[Charge]:
        """Extract billing charges and associate with determinants."""
        determinant_context = "\n".join(
            f"- {d.name}: {d.value} {d.unit}" for d in determinants
        )
        
        try:
            response = self._call_azure_openai('charges', f"{determinant_context}\n\n{text}")
            charges_data = self._parse_json_response(response)
            
            # Handle wrapped response
            if isinstance(charges_data, dict):
                if 'charges' in charges_data:
                    charges_data = charges_data['charges']
                elif len(charges_data) == 1:
                    charges_data = list(charges_data.values())[0]
            
            # Ensure we have a list
            if not isinstance(charges_data, list):
                charges_data = [charges_data]
            
            charges = []
            for charge_data in charges_data:
                # All keys should already be lowercase from the prompt
                cleaned_data = {
                    'name': charge_data.get('name'),
                    'amount': charge_data.get('amount'),
                    'category': charge_data.get('category'),
                    'commodity': charge_data.get('commodity'),
                    'meter_number': charge_data.get('meter_number'),
                    'currency': charge_data.get('currency', 'USD'),
                }
                
                # Remove None values
                cleaned_data = {k: v for k, v in cleaned_data.items() if v is not None}
                
                # Validate required fields
                required_fields = {'name', 'amount', 'category', 'commodity'}
                missing_fields = required_fields - set(cleaned_data.keys())
                if missing_fields:
                    raise ExtractionError(f"Missing required fields for charge: {missing_fields}")
                
                # Handle determinant association
                if det_name := charge_data.get('determinant_name'):
                    cleaned_data['determinant'] = next(
                        (d for d in determinants if d.name == det_name), None
                    )
                
                charges.append(Charge(**cleaned_data))
            
            # Normalize charge names
            charges = self._normalize_charge_names(charges)
            
            return charges
        except Exception as e:
            raise ExtractionError(f"Failed to extract charges: {str(e)}")

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate JSON response."""
        try:
            data = json.loads(response)
            
            # If we got a single object, wrap it in a list
            if isinstance(data, dict):
                if not any(key in data for key in ['charges', 'determinants', 'subtotals']):
                    data = [data]
                    
            return data
        except json.JSONDecodeError as e:
            raise ExtractionError(f"Failed to parse JSON response: {str(e)}")

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'AzureOpenAIExtractor':
        """Create an extractor instance from configuration."""
        required = {'api_key', 'endpoint', 'deployment'}
        if not all(k in config for k in required):
            raise ValueError(f"Config must contain: {required}")
        
        # Handle custom prompts directory
        prompts_dir = None
        if 'prompts_dir' in config:
            prompts_dir = Path(config['prompts_dir'])
            if not prompts_dir.exists():
                raise ValueError(f"Prompts directory not found: {prompts_dir}")
            
        return cls(
            api_key=config['api_key'],
            endpoint=config['endpoint'],
            deployment=config['deployment'],
            prompts_dir=prompts_dir
        )

    @property
    def supported_fields(self) -> Dict[str, Dict[str, str]]:
        """Dictionary of supported extraction fields by category."""
        return {
            'account_info': {
                'account_number': 'Customer account identifier',
                'invoice_number': 'Unique invoice identifier',
                'billing_period': 'Start and end dates for billing cycle',
                'vendor_name': 'Utility or supplier name',
                'customer_name': 'Account holder name',
                'service_address': 'Service location address'
            },
            'determinants': {
                'usage': 'Total consumption quantity',
                'demand': 'Peak demand reading',
                'time_of_use': 'Usage by time period (peak/off-peak)'
            },
            'charges': {
                'energy_charge': 'Cost per unit of consumption',
                'demand_charge': 'Cost per unit of peak demand',
                'fixed_charge': 'Monthly service charges',
                'taxes': 'Applicable taxes and fees'
            }
        }

    def _get_structured_response(self, text: str, prompt_template: str) -> Any:
        """Get structured data from LLM response."""
        try:
            # Call Azure OpenAI with the prompt
            response = self._call_azure_openai('structured', text, prompt_template)
            
            # Parse the response
            return self._parse_json_response(response)
        except Exception as e:
            raise ExtractionError(f"Failed to get structured response: {str(e)}")

    def _parse_json_response(self, response: str) -> Any:
        """Parse JSON response from LLM."""
        try:
            import json
            # Clean the response - remove any markdown code block markers
            cleaned = response.replace('```json', '').replace('```', '').strip()
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            # If JSON parsing fails, return the raw string
            return response

    def _normalize_charge_names(self, charges: List[Charge]) -> List[Charge]:
        """Normalize charge names using LLM to standardize formatting."""
        if not charges:
            return charges
        
        # Extract all unique charge names
        charge_names = list({charge.name for charge in charges})
        
        try:
            # Call LLM to normalize names
            response = self._call_azure_openai(
                'normalize_charges', 
                json.dumps(charge_names)
            )
            name_mapping = self._parse_json_response(response)
            
            # Create new charges with normalized names
            normalized_charges = []
            for charge in charges:
                new_charge = Charge(
                    name=name_mapping.get(charge.name, charge.name),
                    amount=charge.amount,
                    category=charge.category,
                    commodity=charge.commodity,
                    currency=charge.currency,
                    determinant=charge.determinant,
                    unit_rate=charge.unit_rate,
                    meter_number=charge.meter_number,
                    notes=charge.notes
                )
                normalized_charges.append(new_charge)
            
            return normalized_charges
        
        except Exception as e:
            logging.warning(f"Charge name normalization failed: {str(e)}")
            return charges  # Return original charges if normalization fails
