"""
Base abstract class for LLM services with usage tracking.

All services implement a single public method: ``batch_chat``.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Any, List, Tuple, Optional


@dataclass
class UsageStats:
    """Tracks inference count, token usage, and cost."""
    inference_count: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0

    def record(self, input_tokens: int, output_tokens: int, cost: float) -> None:
        self.inference_count += 1
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.cost += cost

    def to_dict(self) -> dict:
        return asdict(self)


class BaseLLMService(ABC):
    """Abstract base class for LLM services.

    Tracks two usage accumulators:
    - algorithm_usage: only non-test calls (optimization algorithm cost)
    - total_usage: all calls (algorithm + test evaluation)
    """

    def __init__(
        self,
        max_concurrency: int = 20,
        max_retries: int = 5,
        batch_poll_interval: int = 30,
        batch_timeout: int = 3600,
    ):
        self.max_concurrency = max_concurrency
        self.max_retries = max_retries
        self.batch_poll_interval = batch_poll_interval
        self.batch_timeout = batch_timeout
        self.algorithm_usage = UsageStats()
        self.total_usage = UsageStats()

    def _record_usage(
        self, input_tokens: int, output_tokens: int, cost: float, is_test: bool,
    ) -> None:
        self.total_usage.record(input_tokens, output_tokens, cost)
        if not is_test:
            self.algorithm_usage.record(input_tokens, output_tokens, cost)

    def _check_fatal_error(self, error: Exception, model_id: str) -> None:
        """Raise ``FatalModelError`` for 404 / model-not-found errors."""
        error_str = str(error).lower()
        if "not found" in error_str or "does not exist" in error_str or "404" in str(error):
            from src.utils.exceptions import FatalModelError
            raise FatalModelError(f"Model {model_id} not found") from error

    def get_usage(self) -> dict:
        return {
            "algorithm": self.algorithm_usage.to_dict(),
            "total": self.total_usage.to_dict(),
        }

    def reset_usage(self) -> None:
        self.algorithm_usage = UsageStats()
        self.total_usage = UsageStats()

    @abstractmethod
    def batch_chat(
        self,
        conversations: List[Tuple[str, List[Tuple[str, Optional[Any]]]]],
        system_message: Optional[str] = None,
        is_test: bool = False,
        **kwargs,
    ) -> List[Tuple[str, str]]:
        """Process conversations in batch.

        Args:
            conversations: List of ``(id, messages)`` tuples where *messages*
                is a list of ``(text, image_or_None)`` tuples.
            system_message: Optional system instruction prepended to each
                conversation.
            is_test: If True usage is only counted in ``total_usage``.
            **kwargs: Model-specific overrides (temperature, max_tokens …).

        Returns:
            List of ``(id, response_text)`` tuples in the same order as input.
        """
        raise NotImplementedError
