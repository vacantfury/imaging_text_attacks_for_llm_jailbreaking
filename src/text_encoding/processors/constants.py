"""
Constants for processing strategies.

This module defines constants used by different processing strategies,
including LLM-based and non-LLM-based strategies.

Note: Temperature and max_tokens are NOT defined here - let llm_utils handle those.
"""
from typing import Final, List
from src.llm_utils import LLMModel

# Export list for strategy implementations
__all__ = [
    'DEFAULT_PROCESSING_MODEL',
    'DEFAULT_PARTS_NUM',
    'DEFAULT_NON_LLM_PARAMETERS',
    'BOUNDARY_WINDOW_PERCENT',
    'SENTENCE_BOUNDARY_SCORE',
    'PHRASE_BOUNDARY_SCORE',
    'WORD_BOUNDARY_SCORE',
    'MIN_CONTENT_WORD_LENGTH',
    'MIN_WORDS_PER_PART',
    'SENTENCE_ENDERS',
    'PHRASE_ENDERS',
    'DEFAULT_TEMPLATES',
    'DEFAULT_KEYWORDS',
    'MATH_FORMAT_PREFIX',
    'DEFINITION_FORMAT',
    'DEFAULT_INJECTION_NUM_SYMBOLS',
    'DEFAULT_INJECTION_SYMBOLS',
]

# =============================================================================
# Default Processing Model
# =============================================================================

# Default model for LLM-based processors if none is specified
DEFAULT_PROCESSING_MODEL: Final[LLMModel] = LLMModel.GPT_4O

# =============================================================================
# Non-LLM Strategy Constants
# =============================================================================

# Default parameters for non-LLM processing
DEFAULT_PARTS_NUM: Final[int] = 6

DEFAULT_NON_LLM_PARAMETERS: Final[dict] = {
    "parts_num": DEFAULT_PARTS_NUM
}

# =============================================================================
# Split-Reassemble Strategy Parameters
# =============================================================================

# Boundary adjustment parameters
BOUNDARY_WINDOW_PERCENT: Final[float] = 0.1  # Look within ±10% of target size
SENTENCE_BOUNDARY_SCORE: Final[int] = 3  # Priority score for sentence boundaries
PHRASE_BOUNDARY_SCORE: Final[int] = 2  # Priority score for phrase boundaries
WORD_BOUNDARY_SCORE: Final[int] = 1  # Priority score for word boundaries

# Content analysis
MIN_CONTENT_WORD_LENGTH: Final[int] = 4  # Minimum length for content words
MIN_WORDS_PER_PART: Final[int] = 2  # Minimum words per part when splitting

# Sentence and phrase boundary indicators
SENTENCE_ENDERS: Final[List[str]] = [".", "!", "?", ";", ":"]
PHRASE_ENDERS: Final[List[str]] = [",", "-", ")", "]", "}", '"']

# =============================================================================
# Template-Based Processing (for future extension)
# =============================================================================

# Templates for template-based processing
DEFAULT_TEMPLATES: Final[List[str]] = [
    "Let's think about this mathematically: {prompt}",
    "From a mathematical perspective: {prompt}",
    "Using abstract algebra concepts: {prompt}",
    "In terms of set theory: {prompt}",
    "Through the lens of symbolic logic: {prompt}",
    "As a mathematics problem: {prompt}",
    "Representing this with mathematical notation: {prompt}",
    "If we formalize this mathematically: {prompt}"
]

# Keywords for keyword-based processing (future extension)
DEFAULT_KEYWORDS: Final[dict] = {
    "how": ["process", "method", "procedure", "steps", "technique"],
    "what": ["definition", "concept", "idea", "meaning", "description"],
    "why": ["reason", "explanation", "cause", "rationale", "justification"],
    "when": ["timing", "occurrence", "circumstance", "situation", "event"],
    "where": ["location", "position", "place", "setting", "environment"]
}

# Format for mathematical notation (future extension)
MATH_FORMAT_PREFIX: Final[str] = "Mathematical inquiry: "

# Format for definition conversion (future extension)
DEFINITION_FORMAT: Final[str] = """
Definition: Let's define a concept X as follows:
Given a set S = {{ {prompt} }},
For all elements e ∈ S, 
We say that X(e) holds iff e satisfies the conditions specified.

Theorem: The property X has interesting mathematical properties.

Proof: Let's analyze the elements of S...
"""

# =============================================================================
# Symbol Injection Strategy Parameters
# =============================================================================

# Default number of symbols to inject into prompts
DEFAULT_INJECTION_NUM_SYMBOLS: Final[int] = 10

# Default symbols for injection (mathematical and special symbols)
DEFAULT_INJECTION_SYMBOLS: Final[List[str]] = [
    # Mathematical operators
    "∀", "∃", "∈", "∉", "⊂", "⊆", "∪", "∩", "∅", "×", "÷", "±", "∞", "≈", "≠", "≤", "≥",
    "∫", "∑", "∏", "∂", "∇", "√", "∛", "∜", "∝", "∧", "∨", "¬", "⇒", "⇔", "→", "←", "↔",
    # Greek letters
    "α", "β", "γ", "δ", "ε", "ζ", "η", "θ", "λ", "μ", "π", "ρ", "σ", "τ", "φ", "χ", "ψ", "ω",
    "Α", "Β", "Γ", "Δ", "Ε", "Ζ", "Η", "Θ", "Λ", "Μ", "Π", "Ρ", "Σ", "Τ", "Φ", "Χ", "Ψ", "Ω",
    # Other special symbols
    "†", "‡", "§", "¶", "•", "◦", "○", "●", "★", "☆", "♠", "♣", "♥", "♦", "◊", "■", "□", "▪",
    "▫", "▲", "△", "▼", "▽", "◀", "▶", "⊕", "⊗", "⊙", "⋅", "∘", "·", "…", "⋯", "⋮", "⋰", "⋱"
]

