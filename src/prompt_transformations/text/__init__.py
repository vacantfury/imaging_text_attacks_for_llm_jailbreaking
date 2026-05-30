"""Text-to-text prompt transformations.

Encoders (set_theory, formal_logic, classical_chinese, semantic_camo, baseline,
addition_equation, conditional_probability, symbol_injection, quantum_mechanics)
and template attacks (deep_inception, code_attack).

Each submodule's @register_transformation calls fire on import here.
"""
from . import wrappers  # noqa: F401  — 9 legacy encoders
from . import deep_inception  # noqa: F401
from .encoders import code_attack  # noqa: F401
