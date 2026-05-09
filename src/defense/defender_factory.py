"""
Factory for creating defense strategy instances.
"""
from typing import Any

from src.utils.logger import get_logger
from .base_defender import BaseDefender
from .defenders.sage_defender import SAGEDefender
from .defenders.semantic_smooth_defender import SemanticSmoothDefender

logger = get_logger(__name__)

DEFENDERS: dict[str, type[BaseDefender]] = {
    "sage": SAGEDefender,
    "semantic_smooth": SemanticSmoothDefender,
}


def create_defender(name: str, **kwargs: Any) -> BaseDefender:
    """
    Create a defender instance by name.

    Args:
        name: Defense method name ("sage", "semantic_smooth").
        **kwargs: Method-specific configuration passed to the constructor.

    Returns:
        Configured BaseDefender instance.

    Raises:
        ValueError: If name is not a registered defender.
    """
    if name not in DEFENDERS:
        available = sorted(DEFENDERS.keys())
        raise ValueError(f"Unknown defense method '{name}'. Available: {available}")

    defender_cls = DEFENDERS[name]
    defender = defender_cls(**kwargs)
    logger.info(f"Created defender: {name} ({defender_cls.__name__})")
    return defender
