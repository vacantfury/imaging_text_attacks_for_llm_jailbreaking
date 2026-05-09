"""
Base class for all defense strategies.

Each defender takes encoded prompts and a target model service,
applies its defense mechanism, and returns (id, response) pairs.
The task runner handles judging and result persistence.
"""
from abc import ABC, abstractmethod
from typing import Any

from src.llm_utils.base_llm_service import BaseLLMService
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BaseDefender(ABC):
    """
    Abstract base for defense strategies.

    Subclasses implement defend_and_query() which:
      1. Applies the defense transformation to prompts
      2. Queries the target model
      3. Returns (id, response) pairs

    The caller (_run_defense in task.py) handles ASR judging.
    """

    def __init__(self, **kwargs):
        self._extra_config = kwargs

    @abstractmethod
    def defend_and_query(
        self,
        prompts: list[dict[str, str]],
        service: BaseLLMService,
        system_message: str | None = None,
    ) -> list[tuple[str, str]]:
        """
        Apply defense and query target model.

        Args:
            prompts: List of dicts with keys 'id' and 'encoded' (the attack text).
            service: Target model LLM service for querying.
            system_message: Optional system message for the model.

        Returns:
            List of (id, response_text) tuples.
        """
        raise NotImplementedError

    def get_usage(self) -> dict[str, Any] | None:
        """Return any additional LLM usage from the defense (e.g., perturbation calls)."""
        return None
