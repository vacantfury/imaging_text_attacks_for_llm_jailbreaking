"""
Prompt Encoder Package

Provides prompt transformation processors using different techniques (LLM-based and rule-based).

Main Components:
- BaseEncoder: Abstract base for all processors
- Built-in processors: SetTheoryLLMEncoder, ConditionalProbabilityEncoder, AdditionEquationEncoder
- Factory: create_encoder() for creating processor instances

Usage:
    >>> from src.text_encoding import create_encoder, EncoderType
    >>> from src.llm_utils import LLMModel
    >>> 
    >>> # LLM-based processing (MathPrompt approach)
    >>> processor = create_encoder(
    ...     EncoderType.LLM_SET_THEORY,
    ...     model=LLMModel.GPT_4O
    ... )
    >>> processed = processor.batch_process(prompts)
    >>> 
    >>> # Rule-based processing
    >>> processor = create_encoder(
    ...     EncoderType.NON_LLM_ADDITION_EQUATION_SPLIT_REASSEMBLE,
    ...     num_parts=6
    ... )
    >>> processed = processor.batch_process(prompts)
"""

# Import base
from .base_encoder import BaseEncoder, split_into_parts

# Import processor types enum
from .encoder_type import EncoderType

# Import concrete processors
from .encoders import (
    SetTheoryLLMEncoder,
    AdditionEquationEncoder,
    ConditionalProbabilityEncoder,
)

# Import factory functions
from .encoder_factory import (
    ENCODERS,
    register_encoder,
    get_encoder,
    list_encoders,
    create_encoder,
)


__all__ = [
    # Base
    'BaseEncoder',
    'split_into_parts',
    
    # Encoder types enum
    'EncoderType',
    
    # Concrete processors
    'SetTheoryLLMEncoder',
    'AdditionEquationEncoder',
    'ConditionalProbabilityEncoder',
    'QuantumMechanicsLLMEncoder',
    
    # Factory functions
    'ENCODERS',
    'register_encoder',
    'get_encoder',
    'list_encoders',
    'create_encoder',
]
