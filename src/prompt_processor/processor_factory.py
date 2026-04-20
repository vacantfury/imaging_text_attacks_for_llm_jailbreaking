"""
Processor factory for creating and managing prompt processors.
"""
from typing import Dict, Optional, Union
from src.utils.logger import get_logger

# Import processor enum
from .processor_type import ProcessorType

# Import all built-in processors
from .processors.llm_set_theory_processor import SetTheoryLLMProcessor
from .processors.llm_markov_chain_processor import MarkovChainLLMProcessor
from .processors.llm_rephrase_processor import RephraseLLMProcessor
from .processors.non_llm_addition_equation_split_reassemble_processor import AdditionEquationProcessor
from .processors.non_llm_conditional_probability_processor import ConditionalProbabilityProcessor
from .processors.non_llm_symbol_injection_processor import SymbolInjectionProcessor
from .processors.llm_quantum_mechanics_processor import QuantumMechanicsLLMProcessor
from .processors.llm_formal_logic_processor import FormalLogicLLMProcessor
from .processors.non_llm_baseline_processor import BaselineProcessor
from .processors.non_llm_repeat_processor import RepeatProcessor

logger = get_logger(__name__)


# =============================================================================
# Processor Registry
# =============================================================================

# Built-in processors registry
# Maps processor names (enum values) to their implementation classes
PROCESSORS: Dict[str, type] = {
    ProcessorType.LLM_SET_THEORY: SetTheoryLLMProcessor,
    ProcessorType.LLM_MARKOV_CHAIN: MarkovChainLLMProcessor,
    ProcessorType.LLM_REPHRASE: RephraseLLMProcessor,
    ProcessorType.NON_LLM_ADDITION_EQUATION_SPLIT_REASSEMBLE: AdditionEquationProcessor,
    ProcessorType.NON_LLM_CONDITIONAL_PROBABILITY: ConditionalProbabilityProcessor,
    ProcessorType.NON_LLM_SYMBOL_INJECTION: SymbolInjectionProcessor,
    ProcessorType.LLM_QUANTUM_MECHANICS: QuantumMechanicsLLMProcessor,
    ProcessorType.LLM_FORMAL_LOGIC: FormalLogicLLMProcessor,
    ProcessorType.NON_LLM_BASELINE: BaselineProcessor,
    ProcessorType.NON_LLM_REPEAT: RepeatProcessor,
}


def register_processor(name: str, processor_class: type):
    """
    Register a new prompt processor.
    
    Args:
        name: Name for the processor
        processor_class: Processor class (must inherit from BaseProcessor)
    
    Example:
        ```python
        from src.prompt_processor import BaseProcessor, register_processor
        
        class MyCustomProcessor(BaseProcessor):
            def process(self, prompt: str, **kwargs) -> str:
                return f"Custom: {prompt}"
        
        register_processor('my_custom', MyCustomProcessor)
        ```
    """
    PROCESSORS[name] = processor_class
    logger.info(f"Registered processor: {name}")


def get_processor(name: str) -> Optional[type]:
    """
    Get a processor class by name.
    
    Args:
        name: Processor name
        
    Returns:
        Processor class or None if not found
    """
    return PROCESSORS.get(name)


def list_processors() -> list[str]:
    """
    List all registered processor names.
    
    Returns:
        List of processor names
    """
    return list(PROCESSORS.keys())


def create_processor(name: Union[str, ProcessorType], **kwargs):
    """
    Factory function to create a processor instance by name or enum.
    
    This is the main factory method that handles processor creation with
    the appropriate parameters for each processor type.
    
    Args:
        name: Processor name as string or ProcessorType enum
              (e.g., ProcessorType.LLM_SET_THEORY or 'llm_set_theory')
        **kwargs: Processor-specific parameters
        
    Returns:
        Processor instance
        
    Raises:
        ValueError: If processor name not found
        
    Examples:
        >>> # Recommended: Use enum for type safety and IDE autocomplete
        >>> from src.llm_utils import LLMModel
        >>> processor = create_processor(ProcessorType.LLM_SET_THEORY, model=LLMModel.GPT_4O)
        
        >>> # Alternative: Use string (for dynamic processor selection)
        >>> processor = create_processor('llm_set_theory', model=LLMModel.GPT_4O)
        
        >>> # Rule-based processor
        >>> processor = create_processor(ProcessorType.NON_LLM_ADDITION_EQUATION_SPLIT_REASSEMBLE, num_parts=6)
    """
    # Convert enum to string if needed
    processor_name = name.value if isinstance(name, ProcessorType) else name
    
    if processor_name not in PROCESSORS:
        available = ", ".join(list_processors())
        raise ValueError(f"Unknown processor '{processor_name}'. Available: {available}")
    
    processor_class = PROCESSORS[processor_name]
    
    try:
        return processor_class(**kwargs)
    except Exception as e:
        logger.error(f"Error creating processor '{processor_name}': {e}")
        raise

