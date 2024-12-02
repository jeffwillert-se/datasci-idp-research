# Invoice Data Extraction System

A modular and extensible system for extracting structured data from energy invoices using OCR, text preprocessing, and Large Language Models (LLMs).

## Overview

This system provides an end-to-end pipeline for processing energy invoices and extracting relevant data into structured formats. It supports multiple OCR engines, text preprocessing methods, and LLM providers, allowing for flexible configuration based on specific needs.

## Features

Note - this is not implemented as a web-service currently!

- **Modular Architecture**: Mix and match different components for each stage of the extraction process
- **Multiple OCR/Text Extraction Options**:
  - Azure Document Intelligence
  - LlamaParse (NOT IMPLEMENTED)
  - (Additional extractors can be easily integrated)
- **Configurable Text Preprocessing**
- **Support for Multiple LLM Providers**:
  - OpenAI
  - Anthropic (NOT IMPLEMENTED)
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

Review the file /src/main.py for an example of running this capability.  
```bash
python -m src.main
```

## Architecture

The system is built around four main components:

1. **Text Extraction**: Converts invoice documents (PDF, images) into raw text
2. **Text Preprocessing**: Prepares extracted text for LLM processing
3. **Data Extraction**: Uses LLMs to extract structured data from preprocessed text
4. **Validation**: Ensures extracted data meets format and business rule requirements

## Project Structure
```
datasci-idp-research/
├── src/
│ ├── core/
│ │ ├── interfaces/ # Abstract base classes
│ │ │ ├── text_extractor.py
│ │ │ ├── text_preprocessor.py
│ │ │ ├── data_extractor.py
│ │ │ └── validator.py
│ │ ├── models/ # Data models
│ │ │ ├── invoice.py
│ │ │ └── extraction_result.py
│ │ └── prompts/ # LLM prompts
│ │ └── azure_openai/
│ │ ├── account_info.yaml
│ │ ├── charges.yaml
│ │ ├── determinants.yaml
│ │ └── normalize_charges.yaml
│ ├── extractors/ # Text extraction implementations
│ │ └── azure_docintel_extractor.py
│ ├── preprocessors/ # Text preprocessing
│ │ ├── basic_preprocessor.py
│ │ └── advanced_preprocessor.py
│ ├── llm_extractors/ # LLM-based extraction
│ │ └── azure_openai_extractor.py
│ ├── validators/ # Validation implementations
│ │ └── business_rules_validator.py
│ ├── config/ # Configuration
│ │ ├── default_config.yaml
│ │ └── settings.py
│ └── main.py # Main entry point
├── tests/ # Test suite
└── requirements.txt
```

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

