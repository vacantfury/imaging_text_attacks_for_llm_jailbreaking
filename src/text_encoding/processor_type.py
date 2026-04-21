"""
Processor type enumeration.

Defines all available prompt processors with type-safe enum.
"""
from enum import Enum


class ProcessorType(str, Enum):
    """
    Enumeration of available prompt processors.
    
    Provides type-safe processor selection with IDE autocomplete.
    Inherits from str to allow direct string comparison and JSON serialization.
    
    Naming convention:
    - LLM_*: Processors that use language models
    - NON_LLM_*: Rule-based processors that don't use LLMs
    """
    
    # =============================================================================
    # LLM-based processors
    # =============================================================================
    
    LLM_SET_THEORY = "llm_set_theory"
    """LLM-based set theory transformation (MathPrompt approach)."""
    
    LLM_MARKOV_CHAIN = "llm_markov_chain"
    """LLM-based Markov chain transformation (Stochastic processes approach)."""
    
    LLM_REPHRASE = "llm_rephrase"
    """LLM-based rephrasing to avoid direct harmful keywords while maintaining intent."""
    
    # =============================================================================
    # Rule-based processors (non-LLM)
    # =============================================================================
    
    NON_LLM_ADDITION_EQUATION_SPLIT_REASSEMBLE = "non_llm_addition_equation_split_reassemble"
    """Split prompt into parts and reassemble as mathematical summation."""
    
    NON_LLM_CONDITIONAL_PROBABILITY = "non_llm_conditional_probability"
    """Format prompt as conditional probability equation."""
    
    NON_LLM_SYMBOL_INJECTION = "non_llm_symbol_injection"
    """Inject mathematical and special symbols randomly and evenly into the prompt."""

    NON_LLM_BASELINE = "non_llm_baseline"
    """Passthrough processor that returns input unchanged (replaces old baseline mode)."""

    LLM_QUANTUM_MECHANICS = "llm_quantum_mechanics"
    """LLM-based Quantum Mechanics transformation."""

    LLM_FORMAL_LOGIC = "llm_formal_logic"
    """LLM-based Formal Logic transformation (first-order logic and proof theory)."""

    NON_LLM_REPEAT = "non_llm_repeat"
    """Replay exact processed prompts from a previous experiment (controlled repeat)."""

