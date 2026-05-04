"""
Encoder factory for creating and managing prompt encoders.

Name resolution (in order):
1. EncoderType enum values (e.g., 'llm_set_theory')
2. ENCODING_ALIASES: shorthands (e.g., 'set_theory' → 'llm_set_theory')
3. Classical language auto-resolution: checks if a YAML config exists in
   conf/text_encoding/classical_language/{name}.yaml. Supports '_literary'
   suffix to set strategy='literary' (e.g., 'latin_literary').
"""
from pathlib import Path
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
from .encoders.llm_classical_language_encoder import LLMClassicalLanguageEncoder


logger = get_logger(__name__)

# Path to classical language YAML configs
_CLASSICAL_LANG_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "conf" / "text_encoding" / "classical_language"
)

# Strategy suffix convention for classical languages
_LITERARY_SUFFIX = "_literary"


# =============================================================================
# Encoder Registry
# =============================================================================

# Maps encoder_type values to their implementation classes.
ENCODERS: Dict[str, type] = {
    EncoderType.LLM_SET_THEORY: SetTheoryLLMEncoder,
    EncoderType.NON_LLM_ADDITION_EQUATION_SPLIT_REASSEMBLE: AdditionEquationEncoder,
    EncoderType.NON_LLM_CONDITIONAL_PROBABILITY: ConditionalProbabilityEncoder,
    EncoderType.NON_LLM_SYMBOL_INJECTION: SymbolInjectionEncoder,
    EncoderType.LLM_QUANTUM_MECHANICS: QuantumMechanicsLLMEncoder,
    EncoderType.LLM_FORMAL_LOGIC: FormalLogicLLMEncoder,
    EncoderType.NON_LLM_BASELINE: BaselineEncoder,
    EncoderType.LLM_CLASSICAL_LANGUAGE: LLMClassicalLanguageEncoder,
}


# =============================================================================
# User-Facing Aliases (true shorthands only)
# =============================================================================

# Maps user-friendly shorthand names to their canonical encoder_type values.
# Only needed when the shorthand differs from the YAML filename / encoder_type.
ENCODING_ALIASES: Dict[str, str] = {
    "plain": "non_llm_baseline",
    "set_theory": "llm_set_theory",
    "formal_logic": "llm_formal_logic",
    "quantum": "llm_quantum_mechanics",
    "addition_equation": "non_llm_addition_equation_split_reassemble",
    "conditional_probability": "non_llm_conditional_probability",
    "symbol_injection": "non_llm_symbol_injection",
}


# =============================================================================
# Name Resolution
# =============================================================================

def _resolve_classical_language(name: str) -> Optional[tuple[str, dict]]:
    """
    Check if `name` matches a classical language YAML config.
    
    Supports the '_literary' suffix convention:
      - 'latin'          → language='latin', strategy='direct'
      - 'latin_literary'  → language='latin', strategy='literary'
    
    Returns:
        (encoder_type, extra_kwargs) if matched, None otherwise.
    """
    strategy = "direct"
    lang = name
    if name.endswith(_LITERARY_SUFFIX):
        strategy = "literary"
        lang = name[: -len(_LITERARY_SUFFIX)]
    
    yaml_path = _CLASSICAL_LANG_DIR / f"{lang}.yaml"
    if yaml_path.exists():
        return "llm_classical_language", {"language": lang, "strategy": strategy}
    
    return None


def resolve_encoding_name(name: str) -> tuple[str, dict]:
    """
    Resolve a user-facing encoding name to an encoder_type and extra kwargs.
    
    Resolution order:
      1. Simple aliases (ENCODING_ALIASES): 'set_theory' → 'llm_set_theory'
      2. Direct encoder_type match: 'llm_set_theory' → as-is
      3. Classical language YAML: 'latin_literary' → 'llm_classical_language'
         + {language: 'latin', strategy: 'literary'}
    
    Args:
        name: User-facing encoding name
    
    Returns:
        Tuple of (encoder_type_value, extra_kwargs)
    
    Raises:
        ValueError: If name cannot be resolved
    """
    # 1. Simple aliases
    if name in ENCODING_ALIASES:
        return ENCODING_ALIASES[name], {}
    
    # 2. Direct encoder_type
    if name in ENCODERS:
        return name, {}
    
    # 3. Classical language auto-resolution from YAML directory
    result = _resolve_classical_language(name)
    if result is not None:
        return result
    
    # Not found
    classical_langs = [
        p.stem for p in _CLASSICAL_LANG_DIR.glob("*.yaml")
    ] if _CLASSICAL_LANG_DIR.exists() else []
    available = sorted(
        set(list(ENCODING_ALIASES.keys()) + list(ENCODERS.keys()) + classical_langs)
    )
    raise ValueError(f"Unknown encoding '{name}'. Available: {available}")


# =============================================================================
# Public API
# =============================================================================

def register_encoder(name: str, encoder_class: type):
    """
    Register a new prompt encoder.
    
    Args:
        name: Name for the processor
        encoder_class: Encoder class (must inherit from BaseEncoder)
    """
    ENCODERS[name] = encoder_class
    logger.info(f"Registered processor: {name}")


def get_encoder(name: str) -> Optional[type]:
    """Get a processor class by name. Returns None if not found."""
    return ENCODERS.get(name)


def list_encoders() -> list[str]:
    """List all registered processor names."""
    return list(ENCODERS.keys())


def create_encoder(name: Union[str, EncoderType], **kwargs):
    """
    Create an encoder instance by name, enum, or user-facing alias.
    
    Supports:
      - EncoderType enum:  create_encoder(EncoderType.LLM_SET_THEORY)
      - Alias shorthand:   create_encoder('set_theory')
      - Classical language: create_encoder('latin_literary')
    
    For classical languages, language/strategy kwargs are auto-resolved
    from the encoding name and can be overridden via explicit kwargs.
    
    Args:
        name: Encoder name (string, enum, or alias)
        **kwargs: Encoder-specific parameters (override auto-resolved defaults)
        
    Returns:
        Encoder instance
        
    Raises:
        ValueError: If encoder name not found
    """
    encoder_name = name.value if isinstance(name, EncoderType) else name
    
    # Resolve name → encoder_type + auto-kwargs
    encoder_type, extra_kwargs = resolve_encoding_name(encoder_name)
    
    if encoder_type not in ENCODERS:
        raise ValueError(
            f"Unknown encoder type '{encoder_type}'. "
            f"Available: {', '.join(list_encoders())}")
    
    # User kwargs override auto-resolved kwargs
    merged_kwargs = {**extra_kwargs, **kwargs}
    encoder_class = ENCODERS[encoder_type]
    
    try:
        return encoder_class(**merged_kwargs)
    except Exception as e:
        logger.error(f"Error creating encoder '{encoder_name}': {e}")
        raise
