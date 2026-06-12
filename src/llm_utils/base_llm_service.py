"""
Base abstract class for LLM services with usage tracking.

All services implement a single public method: ``batch_chat``.
"""

import asyncio
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Any, Awaitable, Callable, List, Optional, Tuple, TypeVar

from src.utils.logger import get_logger

logger = get_logger(__name__)

_T = TypeVar("_T")


# Substrings we treat as rate-limit / quota errors (case-insensitive).
# Covers OpenAI 429s, Google RESOURCE_EXHAUSTED, Anthropic 429s, and
# vLLM rate-limit responses. Extend here if a new provider surfaces a
# different message format.
_RATE_LIMIT_PATTERNS = (
    "429",
    "rate limit",
    "rate_limit",
    "ratelimit",
    "rate-limit",
    "too many requests",
    "resource_exhausted",
    "resource exhausted",
    "quota exceeded",
    "quota_exceeded",
    "overloaded",
    "throttle",
)


def is_rate_limit_error(exc: BaseException) -> bool:
    """Heuristic: does the exception look like a rate-limit / quota error?"""
    err = str(exc).lower()
    return any(p in err for p in _RATE_LIMIT_PATTERNS)


# ---------------------------------------------------------------------------
# Mechanism-error sentinel
# ---------------------------------------------------------------------------
# A response wrapped with this sentinel marks a genuine MECHANISM / processing
# failure: the API call did NOT produce a valid model output (context-overflow,
# network/connection error, timeout, rate-limit exhaustion, a failed/missing
# batch item). This is *not* a refusal — a refusal is a successful call that
# returns refusal text (or empty content). Services emit it only from their
# failure paths (the `except` handler, or an errored batch item). Downstream,
# rows whose response carries this sentinel are flagged
# `is_correctly_processed=False` and EXCLUDED from metric denominators, so an
# untestable prompt is never miscounted as a defeated attack.
#
# The null byte makes the marker impossible to confuse with real model output.
MECHANISM_ERROR_SENTINEL = "\x00__MECHANISM_ERROR__\x00"


def make_mechanism_error(message: str) -> str:
    """Wrap a failure message as a mechanism-error sentinel response."""
    return f"{MECHANISM_ERROR_SENTINEL}{message}"


def is_mechanism_error(response: Any) -> bool:
    """True iff `response` is a mechanism-error sentinel (a real processing
    failure, NOT a refusal)."""
    return isinstance(response, str) and response.startswith(
        MECHANISM_ERROR_SENTINEL)


def strip_mechanism_error(response: str) -> str:
    """Return the human-readable failure message (sentinel prefix removed)."""
    if is_mechanism_error(response):
        return response[len(MECHANISM_ERROR_SENTINEL):]
    return response


def _backoff_seconds(attempt: int, base: float = 2.0, max_wait: float = 60.0) -> float:
    """Exponential backoff with jitter, capped at `max_wait`."""
    return min(base ** attempt + random.random() * 2, max_wait)


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

    # ------------------------------------------------------------------
    # Rate-limit retry helpers (shared across all services).
    # ------------------------------------------------------------------

    def _retry_rate_limit_sync(
        self,
        fn: Callable[[], _T],
        label: str,
        *,
        max_retries: Optional[int] = None,
        max_wait_seconds: float = 60.0,
    ) -> _T:
        """Call `fn()`; on rate-limit error, sleep + retry up to max_retries.

        Used by batch-API services (Google, Anthropic) whose `client.batches.*`
        calls are blocking. Non-rate-limit exceptions propagate immediately.
        """
        retries = self.max_retries if max_retries is None else max_retries
        for attempt in range(retries + 1):
            try:
                return fn()
            except Exception as e:
                if is_rate_limit_error(e) and attempt < retries:
                    wait = _backoff_seconds(attempt, max_wait=max_wait_seconds)
                    logger.warning(
                        f"{label}: rate-limit, retry {attempt + 1}/{retries} "
                        f"after {wait:.1f}s — {str(e)[:120]}")
                    time.sleep(wait)
                    continue
                raise
        # Unreachable — loop either returns or raises.
        raise RuntimeError(f"{label}: exhausted retries")

    async def _retry_rate_limit_async(
        self,
        fn: Callable[[], Awaitable[_T]],
        label: str,
        *,
        max_retries: Optional[int] = None,
        max_wait_seconds: float = 60.0,
    ) -> _T:
        """Async variant of `_retry_rate_limit_sync` for per-call async services
        (OpenAI, vLLM/NU_CLUSTER)."""
        retries = self.max_retries if max_retries is None else max_retries
        for attempt in range(retries + 1):
            try:
                return await fn()
            except Exception as e:
                if is_rate_limit_error(e) and attempt < retries:
                    wait = _backoff_seconds(attempt, max_wait=max_wait_seconds)
                    logger.warning(
                        f"{label}: rate-limit, retry {attempt + 1}/{retries} "
                        f"after {wait:.1f}s — {str(e)[:120]}")
                    await asyncio.sleep(wait)
                    continue
                raise
        raise RuntimeError(f"{label}: exhausted retries")

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
