"""
Concrete prompt encoders for transformation.

This package contains implementations of different prompt transformation techniques.
Each encoder is in its own file for easy maintenance and extension.

To add a new encoder:
1. Create a new file in this directory (e.g., llm_my_encoder.py or non_llm_my_encoder.py)
2. Create a class inheriting from BaseEncoder
3. Implement the process() method
4. Optionally override _batch_process_core() for custom batching
5. Register it in encoder_factory.py
"""

# Import concrete encoders
from .llm_set_theory_encoder import SetTheoryLLMEncoder
from .llm_markov_chain_encoder import MarkovChainLLMEncoder
from .llm_rephrase_encoder import RephraseLLMEncoder
from .non_llm_addition_equation_split_reassemble_encoder import AdditionEquationEncoder
from .non_llm_conditional_probability_encoder import ConditionalProbabilityEncoder
from .non_llm_symbol_injection_encoder import SymbolInjectionEncoder
from .non_llm_repeat_encoder import RepeatEncoder


# Export all
__all__ = [
    'SetTheoryLLMEncoder',
    'MarkovChainLLMEncoder',
    'RephraseLLMEncoder',
    'AdditionEquationEncoder',
    'ConditionalProbabilityEncoder',
    'SymbolInjectionEncoder',
    'RepeatEncoder',
]
