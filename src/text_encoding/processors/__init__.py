"""
Concrete prompt processors for transformation.

This package contains implementations of different prompt transformation techniques.
Each processor is in its own file for easy maintenance and extension.

To add a new processor:
1. Create a new file in this directory (e.g., llm_my_processor.py or non_llm_my_processor.py)
2. Create a class inheriting from BaseProcessor
3. Implement the process() method
4. Optionally override _batch_process_core() for custom batching
5. Register it in processor_factory.py
"""

# Import concrete processors
from .llm_set_theory_processor import SetTheoryLLMProcessor
from .llm_markov_chain_processor import MarkovChainLLMProcessor
from .llm_rephrase_processor import RephraseLLMProcessor
from .non_llm_addition_equation_split_reassemble_processor import AdditionEquationProcessor
from .non_llm_conditional_probability_processor import ConditionalProbabilityProcessor
from .non_llm_symbol_injection_processor import SymbolInjectionProcessor
from .non_llm_repeat_processor import RepeatProcessor


# Export all
__all__ = [
    # Concrete processors
    'SetTheoryLLMProcessor',
    'MarkovChainLLMProcessor',
    'RephraseLLMProcessor',
    'AdditionEquationProcessor',
    'ConditionalProbabilityProcessor',
    'SymbolInjectionProcessor',
    'RepeatProcessor',
]
