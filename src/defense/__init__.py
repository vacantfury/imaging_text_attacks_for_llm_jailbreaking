"""
Defense package: baseline defense strategies for comparison with IRC.

Provides SAGE (prompt-wrapping) and SemanticSmooth (summarize + vote) defenders.
"""
from .defender_factory import create_defender

__all__ = ["create_defender"]
