from typing import Dict, Any, Union, List
from azure.ai.documentintelligence.models import AnalyzeResult
import re
import spacy
from transformers import AutoTokenizer, AutoModel
import torch

from ..core.interfaces.text_preprocessor import TextPreprocessor
from ..core.exceptions import PreprocessingError

class AdvancedPreprocessor(TextPreprocessor):
    """Advanced implementation of the TextPreprocessor interface.
    
    Enhances basic preprocessing with:
    1. NLP-based entity recognition
    2. Semantic section detection
    3. Advanced table structure preservation
    4. Layout-aware text formatting
    5. Contextual token embedding
    """
    
    def __init__(self, 
                 spacy_model: str = "en_core_web_sm",
                 transformer_model: str = "sentence-transformers/all-mpnet-base-v2",
                 max_length: int = 512):
        """Initialize the advanced preprocessor.
        
        Args:
            spacy_model: SpaCy model for NLP tasks
            transformer_model: Transformer model for embeddings
            max_length: Maximum sequence length for transformer
        """
        self.nlp = spacy.load(spacy_model)
        self.tokenizer = AutoTokenizer.from_pretrained(transformer_model)
        self.model = AutoModel.from_pretrained(transformer_model)
        self.max_length = max_length

    def process(self, content: Union[str, AnalyzeResult]) -> str:
        """Process and format the extracted text with advanced NLP."""
        try:
            if isinstance(content, str):
                return self._process_text(content)
            elif isinstance(content, AnalyzeResult):
                return self._process_analyze_result(content)
            else:
                raise PreprocessingError(f"Unsupported content type: {type(content)}")
        except Exception as e:
            raise PreprocessingError(f"Advanced preprocessing failed: {str(e)}")

    def _process_text(self, text: str) -> str:
        """Process text with NLP enhancements."""
        # Basic cleaning
        cleaned = self._basic_clean(text)
        
        # NLP processing
        doc = self.nlp(cleaned)
        
        # Entity recognition and formatting
        entities = self._format_entities(doc)
        
        # Section detection
        sections = self._detect_sections(doc)
        
        # Combine processed components
        return self._combine_components(entities, sections)

    def _detect_sections(self, doc) -> List[Dict[str, Any]]:
        """Detect semantic sections in the document."""
        sections = []
        current_section = {"title": "", "content": [], "confidence": 0.0}
        
        for sent in doc.sents:
            # Use transformer embeddings for section classification
            embeddings = self._get_embeddings(sent.text)
            section_type = self._classify_section(embeddings)
            
            if section_type != current_section["title"]:
                if current_section["content"]:
                    sections.append(current_section)
                current_section = {
                    "title": section_type,
                    "content": [sent.text],
                    "confidence": float(embeddings.max())
                }
            else:
                current_section["content"].append(sent.text)
        
        return sections

    def _get_embeddings(self, text: str) -> torch.Tensor:
        """Get contextual embeddings using transformer model."""
        inputs = self.tokenizer(text, return_tensors="pt", 
                              max_length=self.max_length, truncation=True)
        with torch.no_grad():
            outputs = self.model(**inputs)
        return outputs.last_hidden_state.mean(dim=1)

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'AdvancedPreprocessor':
        """Create preprocessor from configuration."""
        return cls(
            spacy_model=config.get('spacy_model', 'en_core_web_sm'),
            transformer_model=config.get('transformer_model', 
                'sentence-transformers/all-mpnet-base-v2'),
            max_length=config.get('max_length', 512)
        )

    @property
    def supported_formats(self) -> list[str]:
        """List of supported input formats."""
        return ['raw_text', 'azure_result']
