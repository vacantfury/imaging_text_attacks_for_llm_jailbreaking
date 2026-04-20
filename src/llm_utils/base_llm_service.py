"""
Base abstract class for LLM services with usage tracking.
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
        """Record usage from a single inference call."""
        self.inference_count += 1
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.cost += cost
    
    def to_dict(self) -> dict:
        """Convert to dict for logging/serialization."""
        return asdict(self)


class BaseLLMService(ABC):
    """Abstract base class for LLM services with usage tracking.
    
    Tracks two usage accumulators:
    - algorithm_usage: only non-test calls (optimization algorithm cost)
    - total_usage: all calls (algorithm + test evaluation)
    """
    
    def __init__(self):
        self.algorithm_usage = UsageStats()
        self.total_usage = UsageStats()
    
    def _record_usage(self, input_tokens: int, output_tokens: int, cost: float, is_test: bool) -> None:
        """Record usage for an inference call.
        
        Args:
            input_tokens: Number of input tokens consumed
            output_tokens: Number of output tokens generated
            cost: Dollar cost of this call
            is_test: If True, only total_usage is incremented
        """
        self.total_usage.record(input_tokens, output_tokens, cost)
        if not is_test:
            self.algorithm_usage.record(input_tokens, output_tokens, cost)
    
    def get_usage(self) -> dict:
        """Get usage stats as a dict with both accumulators."""
        return {
            "algorithm": self.algorithm_usage.to_dict(),
            "total": self.total_usage.to_dict(),
        }
    
    def reset_usage(self) -> None:
        """Reset all usage counters."""
        self.algorithm_usage = UsageStats()
        self.total_usage = UsageStats()
    
    @abstractmethod
    def batch_generate(
        self,
        prompts: List[Tuple[str, str]],
        system_message: Optional[str] = None,
        is_test: bool = False,
        **kwargs
    ) -> List[Tuple[str, str]]:
        """
        Generate text responses for multiple prompts.
        
        Args:
            prompts: List of (id, prompt) tuples where id is a unique identifier
            system_message: Optional system message/instruction
            is_test: If True, usage is only counted in total (not algorithm)
            **kwargs: Additional model-specific parameters (temperature, max_tokens, etc.)
        
        Returns:
            List of (id, response) tuples
        """
        raise NotImplementedError
    
    @abstractmethod
    def batch_chat(
        self,
        conversations: List[Tuple[str, List[Tuple[str, Optional[Any]]]]],
        is_test: bool = False,
        **kwargs
    ) -> List[Tuple[str, str]]:
        """
        Generate responses for multiple chat conversations.
        
        Args:
            conversations: List of (id, messages) tuples, where id is a unique identifier
                and messages is a list of (text, images) tuples. images can be:
                - None for text-only messages
                - PIL.Image object
                - List of PIL.Image objects
                - URL string
            is_test: If True, usage is only counted in total (not algorithm)
            **kwargs: Additional model-specific parameters
        
        Returns:
            List of (id, response) tuples
        """
        raise NotImplementedError
