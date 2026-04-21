from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
from src.llm_utils import LLMModel


class BaseEvaluator(ABC):
    """
    Abstract base class for evaluators.
    
    Evaluators receive pre-generated target model responses and classify them.
    They do NOT generate responses themselves — that is the Task's responsibility.
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
                - detailed_df: DataFrame with per-prompt results (id, original_prompt, 
                  processed_prompt, response, judge_output, is_jailbroken, label, category)
                - statistics: Dict with aggregate metrics (attack_success_rate, success_count, total_evaluated)
        """
        pass
