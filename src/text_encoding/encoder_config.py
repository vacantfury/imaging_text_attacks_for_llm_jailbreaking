"""
Configuration for prompt encoders.

Note: This module is currently unused. Encoder configuration is handled
via Hydra/OmegaConf dicts loaded by experiment.config.load_conf().
Kept as a reference for potential future typed-config migration.
"""
from dataclasses import dataclass, field
from typing import Any, Optional

from src.llm_utils.llm_model import LLMModel


@dataclass
class LLMModelConfig:
    """Minimal LLM config for encoder use."""
    model: LLMModel = LLMModel.GPT_4_1_MINI
    temperature: float = 0.7
    max_tokens: int = 2048

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LLMModelConfig":
        """Create from a dictionary."""
        if not data:
            return cls()
        data = data.copy()
        if "model" in data and isinstance(data["model"], str):
            data["model"] = LLMModel.from_string(data["model"])
        return cls(**data)


@dataclass
class EncoderConfig:
    """
    Configuration for prompt encoders.
    
    Contains fields for ALL processor types with sensible defaults.
    Each processor picks the fields it needs; unused fields are ignored.
    
    Attributes:
        strategy: Encoder strategy name (single string).
        model_config: LLM configuration for LLM-based processors.
                      Defaults to GPT-4.1-mini (sufficient for encoding).
                      Ignored by non-LLM processors.
        use_few_shot: Whether to include few-shot examples (LLM processors).
        num_parts: Number of parts for split-based processors
                   (AdditionEquation, ConditionalProbability).
        num_symbols: Number of symbols for SymbolInjection processor.
        rephrase_first: If True, rephrase prompts before core processing.
        is_repeating: If True, repeat the processed output.
    """
    strategy: str = "llm_set_theory"
    model_config: LLMModelConfig = field(default_factory=LLMModelConfig)
    use_few_shot: bool = True
    num_parts: int = 6
    num_symbols: int = 10
    rephrase_first: bool = False
    is_repeating: bool = False
    experiment_dir: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EncoderConfig":
        """Create EncoderConfig from a dictionary."""
        if not data:
            return cls()
        
        data = data.copy()
        
        if "model_config" in data and isinstance(data["model_config"], dict):
            data["model_config"] = LLMModelConfig.from_dict(data["model_config"])
        
        return cls(**data)
