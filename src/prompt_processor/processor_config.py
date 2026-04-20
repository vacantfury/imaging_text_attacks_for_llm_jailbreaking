"""
Configuration for prompt processors.
"""
from dataclasses import dataclass, field
from typing import Any, Optional

from src.llm_utils.llm_config import LLMConfig
from src.llm_utils.llm_model import LLMModel


@dataclass
class ProcessorConfig:
    """
    Configuration for prompt processors.
    
    Contains fields for ALL processor types with sensible defaults.
    Each processor picks the fields it needs; unused fields are ignored.
    
    Attributes:
        strategy: Processor strategy name (single string).
        model_config: LLM configuration for LLM-based processors.
                      Defaults to GPT-4o-mini (sufficient for encoding).
                      Ignored by non-LLM processors.
        use_few_shot: Whether to include few-shot examples (LLM processors).
        num_parts: Number of parts for split-based processors
                   (AdditionEquation, ConditionalProbability).
        num_symbols: Number of symbols for SymbolInjection processor.
        rephrase_first: If True, rephrase prompts before core processing.
        is_repeating: If True, repeat the processed output.
    """
    strategy: str = "llm_set_theory"
    model_config: LLMConfig = field(default_factory=lambda: LLMConfig(
        model=LLMModel.GPT_4_1_MINI,
    ))
    use_few_shot: bool = True
    num_parts: int = 6
    num_symbols: int = 10
    rephrase_first: bool = False
    is_repeating: bool = False
    experiment_dir: Optional[str] = None  # Source experiment dir for RepeatProcessor
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProcessorConfig":
        """Create ProcessorConfig from a dictionary."""
        if not data:
            return cls()
        
        data = data.copy()
        
        # Parse nested model_config
        if "model_config" in data and isinstance(data["model_config"], dict):
            data["model_config"] = LLMConfig.from_dict(data["model_config"])
        
        return cls(**data)
