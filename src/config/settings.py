from pathlib import Path
from typing import Dict, Any
import yaml

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
PROMPTS_DIR = BASE_DIR / "core" / "prompts"
RULES_DIR = BASE_DIR / "core" / "rules"

# Default configuration paths
DEFAULT_CONFIG_PATH = BASE_DIR / "config" / "default_config.yaml"
DEFAULT_RULES_PATH = RULES_DIR / "business_rules.yaml"

class Settings:
    """Global settings and configuration management."""
    
    def __init__(self, config_path: str = None):
        self._config_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
        self._load_config()
        
    def _load_config(self):
        """Load configuration from YAML file."""
        if not self._config_path.exists():
            raise ValueError(f"Configuration file not found: {self._config_path}")
            
        with open(self._config_path) as f:
            self._config = yaml.safe_load(f)
            
    @property
    def extractors(self) -> Dict[str, Any]:
        """Extractor configurations."""
        return self._config.get('extractors', {})
        
    @property
    def preprocessors(self) -> Dict[str, Any]:
        """Preprocessor configurations."""
        return self._config.get('preprocessors', {})
        
    @property
    def llm_extractors(self) -> Dict[str, Any]:
        """LLM extractor configurations."""
        return self._config.get('llm_extractors', {})
        
    @property
    def validators(self) -> Dict[str, Any]:
        """Validator configurations."""
        return self._config.get('validators', {})
        
    @property
    def azure(self) -> Dict[str, Any]:
        """Azure-specific settings."""
        return self._config.get('azure', {})
        
    @property
    def openai(self) -> Dict[str, Any]:
        """OpenAI-specific settings."""
        return self._config.get('openai', {})
        
    @property
    def anthropic(self) -> Dict[str, Any]:
        """Anthropic-specific settings."""
        return self._config.get('anthropic', {})
        
    @property
    def logging(self) -> Dict[str, Any]:
        """Logging configuration."""
        return self._config.get('logging', {})
        
    def get_extractor_config(self, name: str) -> Dict[str, Any]:
        """Get configuration for specific extractor."""
        return self.extractors.get(name, {})
        
    def get_validator_config(self, name: str) -> Dict[str, Any]:
        """Get configuration for specific validator."""
        return self.validators.get(name, {})
        
    def get_llm_config(self, provider: str) -> Dict[str, Any]:
        """Get configuration for specific LLM provider."""
        return getattr(self, provider.lower(), {})

# Global settings instance
settings = Settings()

__all__ = ['settings', 'Settings'] 