import logging
from pathlib import Path
from typing import Dict, Any
import json
import yaml
from azure.identity import DefaultAzureCredential

from .core.interfaces.text_extractor import TextExtractor
from .core.interfaces.text_preprocessor import TextPreprocessor
from .core.interfaces.data_extractor import DataExtractor
from .core.interfaces.validator import Validator

from .extractors.azure_docintel_extractor import AzureDocIntelExtractor
from .preprocessors.basic_preprocessor import BasicPreprocessor
from .llm_extractors.azure_openai_extractor import AzureOpenAIExtractor
from .validators.business_rules_validator import BusinessRulesValidator
from .pipeline.extraction_pipeline import ExtractionPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Path to invoice file (update this for your use case)
FILE_PATH = "./files/PSE - Gas Electric 1.pdf"

def load_config() -> Dict[str, Any]:
    """Load configuration from yaml file."""
    config_path = Path(__file__).parent / "config" / "default_config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found at {config_path}. "
            "Please copy default_config.yaml to local.yaml and update settings."
        )
    
    with open(config_path) as f:
        return yaml.safe_load(f)

def main():
    try:
        # Load configuration
        config = load_config()
        
        # Initialize pipeline components
        text_extractor = AzureDocIntelExtractor.from_config(config['azure_docint'])
        preprocessor = BasicPreprocessor()
        data_extractor = AzureOpenAIExtractor.from_config(config['azure_openai'])
        validator = BusinessRulesValidator()
        
        # Create pipeline
        pipeline = ExtractionPipeline(
            text_extractor=text_extractor,
            preprocessor=preprocessor,
            data_extractor=data_extractor,
            validator=validator
        )
        
        # Process invoice
        logger.info(f"Processing invoice: {FILE_PATH}")
        invoice = pipeline.process(FILE_PATH)
        
        # Log results
        logger.info("Extraction completed successfully")
        logger.info(f"Account Number: {invoice.account_number}")
        logger.info(f"Total Amount: ${invoice.total_amount:.2f}")
        
        if invoice.validation_errors:
            logger.warning("Validation warnings:")
            for error in invoice.validation_errors:
                logger.warning(f"  - {error}")
        
        return invoice
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        raise

if __name__ == "__main__":
    # Get absolute path of input file
    file_path = Path(FILE_PATH).resolve()
    
    invoice = main()
    
    # Print extraction results to terminal
    print("\nExtraction Results:")
    print(invoice)
    
    # Save extraction results
    json_path = invoice.save_json()
    print(f"\nExtraction results saved to: {json_path}")
    
    # Compare to verified results if available
    verified_path = Path(invoice.source_file).parent / "verified" / Path(invoice.source_file).name.replace('.pdf', '_verified.json')
    if verified_path.exists():
        comparison = invoice.compare_to_verified(str(verified_path))
        print("\nComparison to verified data:")
        print(f"Accuracy: {comparison['accuracy']:.2%}")
        print(f"Correct fields: {comparison['correct_fields']} / {comparison['total_fields']}")
        
        if comparison['has_differences']:
            print("\nDifferences found:")
            for change_type, changes in comparison['differences'].items():
                print(f"\n{change_type}:")
                for change in changes:
                    print(f"  {change}") 