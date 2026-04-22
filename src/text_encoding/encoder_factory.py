"""
Encoder factory for creating and managing prompt encoders.
"""
from typing import Dict, Optional, Union
from src.utils.logger import get_logger

# Import encoder enum
from .encoder_type import EncoderType

# Import all built-in encoders
from .encoders.llm_set_theory_encoder import SetTheoryLLMEncoder
from .encoders.non_llm_addition_equation_split_reassemble_encoder import AdditionEquationEncoder
from .encoders.non_llm_conditional_probability_encoder import ConditionalProbabilityEncoder
from .encoders.non_llm_symbol_injection_encoder import SymbolInjectionEncoder
from .encoders.llm_quantum_mechanics_encoder import QuantumMechanicsLLMEncoder
from .encoders.llm_formal_logic_encoder import FormalLogicLLMEncoder
from .encoders.non_llm_baseline_encoder import BaselineEncoder


logger = get_logger(__name__)


# =============================================================================
# Encoder Registry
# =============================================================================

# Built-in processors registry
# Maps processor names (enum values) to their implementation classes
ENCODERS: Dict[str, type] = {
    EncoderType.LLM_SET_THEORY: SetTheoryLLMEncoder,
    EncoderType.NON_LLM_ADDITION_EQUATION_SPLIT_REASSEMBLE: AdditionEquationEncoder,
    EncoderType.NON_LLM_CONDITIONAL_PROBABILITY: ConditionalProbabilityEncoder,
    EncoderType.NON_LLM_SYMBOL_INJECTION: SymbolInjectionEncoder,
    EncoderType.LLM_QUANTUM_MECHANICS: QuantumMechanicsLLMEncoder,
    EncoderType.LLM_FORMAL_LOGIC: FormalLogicLLMEncoder,
    EncoderType.NON_LLM_BASELINE: BaselineEncoder,
}


def register_encoder(name: str, encoder_class: type):
    """
    Register a new prompt encoder.
    
    Args:
        name: Name for the processor
        encoder_class: Encoder class (must inherit from BaseEncoder)
    
    Example:
        ```python
        from src.text_encoding import BaseEncoder, register_encoder
        
        class MyCustomEncoder(BaseEncoder):
            def process(self, prompt: str, **kwargs) -> str:
                return f"Custom: {prompt}"
        
        register_encoder('my_custom', MyCustomEncoder)
        ```
    """
    ENCODERS[name] = encoder_class
    logger.info(f"Registered processor: {name}")


def get_encoder(name: str) -> Optional[type]:
    """
    Get a processor class by name.
    
    Args:
        name: Encoder name
        
    Returns:
        Encoder class or None if not found
    """
    return ENCODERS.get(name)


def list_encoders() -> list[str]:
    """
    List all registered processor names.
    
    Returns:
        List of processor names
    """
    return list(ENCODERS.keys())


def create_encoder(name: Union[str, EncoderType], **kwargs):
    """
    Factory function to create a processor instance by name or enum.
    
    This is the main factory method that handles processor creation with
    the appropriate parameters for each processor type.
    
    Args:
        name: Encoder name as string or EncoderType enum
              (e.g., EncoderType.LLM_SET_THEORY or 'llm_set_theory')
        **kwargs: Encoder-specific parameters
        
    Returns:
        Encoder instance
        
    Raises:
        ValueError: If processor name not found
        
    Examples:
        >>> # Recommended: Use enum for type safety and IDE autocomplete
        >>> from src.llm_utils import LLMModel
        >>> processor = create_encoder(EncoderType.LLM_SET_THEORY, model=LLMModel.GPT_4O)
        
        >>> # Alternative: Use string (for dynamic processor selection)
        >>> processor = create_encoder('llm_set_theory', model=LLMModel.GPT_4O)
        
        >>> # Rule-based processor
        >>> processor = create_encoder(EncoderType.NON_LLM_ADDITION_EQUATION_SPLIT_REASSEMBLE, num_parts=6)
    """
    # Convert enum to string if needed
    encoder_name = name.value if isinstance(name, EncoderType) else name
    
    if encoder_name not in ENCODERS:
        available = ", ".join(list_encoders())
        raise ValueError(f"Unknown processor '{encoder_name}'. Available: {available}")
    
    encoder_class = ENCODERS[encoder_name]
    
    try:
        return encoder_class(**kwargs)
    except Exception as e:
        logger.error(f"Error creating processor '{encoder_name}': {e}")
        raise

