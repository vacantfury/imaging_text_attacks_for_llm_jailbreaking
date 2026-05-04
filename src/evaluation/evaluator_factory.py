from typing import Optional, Dict, Any
from .base_evaluator import BaseEvaluator
from .harmbench_evaluation.evaluator import HarmBenchEvaluator
from .jailbreakbench_evaluation.evaluator import JailbreakBenchEvaluator
from .jailbreakbench_refusal_evaluation.evaluator import JailbreakBenchRefusalEvaluator
from .orbench_evaluation.evaluator import ORBenchEvaluator
from src.llm_utils import LLMModel

class EvaluatorFactory:
    """
    Factory for creating evaluators.
    """
    
    @staticmethod
    def create(method: str = "harmbench", model: Optional[LLMModel] = None, **kwargs) -> BaseEvaluator:
        """
        Create an evaluator instance.
        
        Args:
            method: Evaluation method ('harmbench', 'jailbreakbench', or 'refusal').
            model: The LLM model to use for evaluation.
            **kwargs: Additional arguments required by specific evaluators.
            
        Returns:
            An instance of a class inheriting from BaseEvaluator.
            
        Raises:
            ValueError: If the method is unknown.
        """
        method = method.lower().strip()
        
        if method == "harmbench":
            return HarmBenchEvaluator(model=model, **kwargs)
        elif method == "jailbreakbench" or method == "jbb":
            return JailbreakBenchEvaluator(model=model, **kwargs)
        elif method == "refusal":
            return JailbreakBenchRefusalEvaluator(model=model, **kwargs)
        elif method == "orbench":
            return ORBenchEvaluator(model=model, **kwargs)
        else:
            raise ValueError(
                f"Unknown evaluation method: {method}. "
                "Supported: 'harmbench', 'jailbreakbench', 'refusal', 'orbench'"
            )
