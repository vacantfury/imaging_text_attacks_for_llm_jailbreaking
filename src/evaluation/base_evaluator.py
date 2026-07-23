from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
from llm_utils import LLMModel


class BaseEvaluator(ABC):
    """
    Abstract base class for evaluators.

    Concrete evaluators (HarmBench, JailbreakBench, ORBench, JBB-Refusal) hard-bind
    their canonical judge model in their own `constants.py` and do NOT accept a
    `model` argument from the caller. This prevents methodologically incorrect
    judge substitutions (e.g. using a generic GPT model as the HarmBench judge).

    The base accepts a `model` parameter only for the abstract API; subclasses
    ignore it and assign their own model in `__init__`.
    """

    def __init__(self, model: Optional[LLMModel] = None, **kwargs):
        self.model = model
        self.kwargs = kwargs

    @abstractmethod
    def evaluate(
        self,
        prompts: List[Dict[str, Any]],
        processed_prompts: List[str],
        responses: Dict[str, str],
        baseline_responses: Optional[Dict[str, str]] = None,
        verbose: bool = False,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Evaluate the effectiveness of a jailbreak attack on pre-generated responses.

        Args:
            prompts: List of original prompt dictionaries (must contain 'prompt' key).
            processed_prompts: List of processed/jailbroken prompt strings.
            responses: Dict mapping prompt_id -> target model response text.
            baseline_responses: Optional dict mapping prompt_id -> baseline response text.
            verbose: Whether to log detailed progress.

        Returns:
            Tuple of:
                - detailed_df: DataFrame with per-prompt results
                - statistics: Dict with aggregate metrics
        """
        pass
