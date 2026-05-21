from .base_evaluator import BaseEvaluator
from .harmbench_evaluation.evaluator import HarmBenchEvaluator
from .jailbreakbench_evaluation.evaluator import JailbreakBenchEvaluator
from .jailbreakbench_refusal_evaluation.evaluator import JailbreakBenchRefusalEvaluator
from .orbench_evaluation.evaluator import ORBenchEvaluator


class EvaluatorFactory:
    """
    Factory for creating canonical benchmark evaluators.

    Each evaluator hard-binds its own canonical judge model via its own
    `constants.py`. The factory does NOT accept a `model` argument — passing one
    would be a methodological error (e.g. using a generic GPT judge for HarmBench
    prompts). Extra kwargs flow through to the LLM service for non-canonical
    settings (timeouts, retries) but `model`, `temperature`, and `max_tokens` are
    stripped inside each evaluator.
    """

    @staticmethod
    def create(method: str = "harmbench", **kwargs) -> BaseEvaluator:
        """
        Create an evaluator instance.

        Args:
            method: Evaluation method ('harmbench', 'jailbreakbench', 'jbb_refusal', 'orbench').
            **kwargs: Forwarded to the evaluator; canonical params (model, temperature,
                max_tokens) are ignored inside the evaluator and replaced with constants.

        Returns:
            An instance of a class inheriting from BaseEvaluator.

        Raises:
            ValueError: If the method is unknown.
        """
        method = method.lower().strip()

        if method == "harmbench":
            return HarmBenchEvaluator(**kwargs)
        if method in ("jailbreakbench", "jbb"):
            return JailbreakBenchEvaluator(**kwargs)
        if method in ("jbb_refusal", "refusal"):
            return JailbreakBenchRefusalEvaluator(**kwargs)
        if method == "orbench":
            return ORBenchEvaluator(**kwargs)

        raise ValueError(
            f"Unknown evaluation method: {method}. "
            "Supported: 'harmbench', 'jailbreakbench', 'jbb_refusal', 'orbench'"
        )
