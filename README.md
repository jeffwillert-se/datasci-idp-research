# Invoice Data Extraction System

A modular and extensible system for extracting structured data from energy invoices using OCR, text preprocessing, and Large Language Models (LLMs).

## Overview

This system provides an end-to-end pipeline for processing energy invoices and extracting relevant data into structured formats. It supports multiple OCR engines, text preprocessing methods, and LLM providers, allowing for flexible configuration based on specific needs.

## Features

- **Modular Architecture**: Mix and match different components for each stage of the extraction process
- **Multiple OCR/Text Extraction Options**:
  - Azure Document Intelligence
  - LlamaParse
  - (Additional extractors can be easily integrated)
- **Configurable Text Preprocessing**
- **Support for Multiple LLM Providers**:
  - OpenAI
  - Anthropic
  - (Extensible for other providers)
- **Comprehensive Validation**:
  - JSON schema validation
  - Business rules validation
  - Automatic correction and retry mechanisms

## Installation

```bash
git clone https://github.com/yourusername/invoice-extractor.git
cd invoice-extractor
pip install -r requirements.txt
```

## Quick Start

```python
from invoice_extractor.pipeline import ExtractionPipeline
from invoice_extractor.extractors import AzureExtractor
from invoice_extractor.preprocessors import BasicPreprocessor
from invoice_extractor.llm_extractors import OpenAIExtractor
from invoice_extractor.validators import BusinessRulesValidator

# Initialize components
extractor = AzureExtractor()
preprocessor = BasicPreprocessor()
llm_extractor = OpenAIExtractor()
validator = BusinessRulesValidator()

# Create pipeline
pipeline = ExtractionPipeline(
    text_extractor=extractor,
    preprocessor=preprocessor,
    data_extractor=llm_extractor,
    validator=validator
)

# Process an invoice
result = pipeline.process("path/to/invoice.pdf")
```

## Architecture

The system is built around four main components:

1. **Text Extraction**: Converts invoice documents (PDF, images) into raw text
2. **Text Preprocessing**: Prepares extracted text for LLM processing
3. **Data Extraction**: Uses LLMs to extract structured data from preprocessed text
4. **Validation**: Ensures extracted data meets format and business rule requirements

## Project Structure
invoice_extractor/
│
├── src/
│   ├── init.py
│   │
│   ├── core/                      # Core interfaces and models
│   │   ├── init.py
│   │   ├── interfaces/            # Abstract base classes
│   │   │   ├── init.py
│   │   │   ├── text_extractor.py  # Text extraction interface
│   │   │   ├── text_preprocessor.py
│   │   │   ├── data_extractor.py
│   │   │   └── validator.py
│   │   │
│   │   └── models/               # Data models
│   │       ├── init.py
│   │       ├── invoice.py        # Invoice data structure
│   │       └── extraction_result.py
│   │
│   ├── extractors/               # Text extraction implementations
│   │   ├── init.py
│   │   ├── azure_extractor.py    # Azure Document Intelligence
│   │   └── llama_parse_extractor.py
│   │
│   ├── preprocessors/            # Text preprocessing implementations
│   │   ├── init.py
│   │   ├── basic_preprocessor.py
│   │   └── advanced_preprocessor.py
│   │
│   ├── llm_extractors/          # LLM-based extraction implementations
│   │   ├── init.py
│   │   ├── openai_extractor.py
│   │   └── anthropic_extractor.py
│   │
│   ├── validators/              # Validation implementations
│   │   ├── init.py
│   │   ├── json_validator.py
│   │   └── business_rules_validator.py
│   │
│   └── pipeline/               # Pipeline orchestration
│       ├── init.py
│       └── extraction_pipeline.py
│
├── tests/                      # Test suite
│   ├── init.py
│   ├── test_extractors/
│   ├── test_preprocessors/
│   ├── test_llm_extractors/
│   ├── test_validators/
│   └── test_pipeline/
│
├── config/                     # Configuration files
│   ├── init.py
│   └── settings.py
│
├── examples/                   # Usage examples
│   ├── sample_invoices/
│   └── usage_examples.py
│
└── requirements.txt

### Key Directory Descriptions

- **src/core/**: Contains the fundamental interfaces and data models that define the system's architecture
- **src/extractors/**: Implementations of different text extraction methods (OCR, parsing)
- **src/preprocessors/**: Text preprocessing implementations for preparing text for LLM processing
- **src/llm_extractors/**: Different LLM implementations for extracting structured data
- **src/validators/**: Validation implementations for ensuring data quality
- **src/pipeline/**: Pipeline orchestration for combining components
- **tests/**: Comprehensive test suite mirroring the src/ structure
- **config/**: Configuration files and settings
- **examples/**: Example implementations and sample data

