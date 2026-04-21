"""
Prompt Processor Package

Provides prompt transformation processors using different techniques (LLM-based and rule-based).

Main Components:
- BaseProcessor: Abstract base for all processors
- Built-in processors: SetTheoryLLMProcessor, ConditionalProbabilityProcessor, AdditionEquationProcessor
- Factory: create_processor() for creating processor instances

Usage:
    >>> from src.prompt_processor import create_processor, ProcessorType
    >>> from src.llm_utils import LLMModel
    >>> 
    >>> # LLM-based processing (MathPrompt approach)
    >>> processor = create_processor(
    ...     ProcessorType.LLM_SET_THEORY,
    ...     model=LLMModel.GPT_4O
    ... )
    >>> processed = processor.batch_process(prompts)
    >>> 
    >>> # Rule-based processing
    >>> processor = create_processor(
    ...     ProcessorType.NON_LLM_ADDITION_EQUATION_SPLIT_REASSEMBLE,
    ...     num_parts=6
    ... )
    >>> processed = processor.batch_process(prompts)
"""

# Import base
from .base_processor import BaseProcessor, split_into_parts

# Import processor types enum
from .processor_type import ProcessorType

# Import concrete processors
from .processors import (
    SetTheoryLLMProcessor,
    AdditionEquationProcessor,
    ConditionalProbabilityProcessor,
)

# Import factory functions
from .processor_factory import (
    PROCESSORS,
    register_processor,
    get_processor,
    list_processors,
    create_processor,
)


__all__ = [
    # Base
    'BaseProcessor',
    'split_into_parts',
    
    # Processor types enum
    'ProcessorType',
    
    # Concrete processors
    'SetTheoryLLMProcessor',
    'AdditionEquationProcessor',
    'ConditionalProbabilityProcessor',
    'QuantumMechanicsLLMProcessor',
    
    # Factory functions
    'PROCESSORS',
    'register_processor',
    'get_processor',
    'list_processors',
    'create_processor',
]
