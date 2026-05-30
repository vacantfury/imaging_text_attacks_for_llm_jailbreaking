"""Defenses for the defense+evaluate stage.

A Defense owns the target-model interaction loop. Provided implementations:
  - no_defense        : pure baseline, pass-through to the target model
  - sage              : prepends a self-discrimination safety instruction
  - semantic_smooth   : N paraphrase summaries + majority vote
  - ecso              : 3-call response-coupled defense (TELL → CAP → safe-gen)
"""
from .base import Defense, build_conversation_message
from .defender_factory import (
    DEFENSES,
    create_defense,
    create_defender,
    list_defenses,
    register_defense,
)

__all__ = [
    "Defense",
    "build_conversation_message",
    "DEFENSES",
    "create_defense",
    "create_defender",
    "list_defenses",
    "register_defense",
]
