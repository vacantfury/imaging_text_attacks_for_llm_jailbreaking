"""
SemanticCamo attack encoder — multi-step semantic camouflage.

Implements the A_PLAN1 strategy from:
  "SemanticCamo: Jailbreaking Large Language Models through Semantic Camouflage"
  (Jiang et al., 2025)

Pipeline per prompt:
  1. Extract key components (des1, action1) from the harmful prompt via LLM
  2. Step 1: Extract semantic features of des1 into structured JSON
  3. Step 2: Given semantic features + action1, reconstruct harmful instructions

All prompt templates are loaded from conf/text_encoding/semantic_camo.yaml.
"""
from typing import Optional, List

from src.llm_utils import LLMServiceFactory, BaseLLMService
from src.utils.logger import get_logger
from ..base_encoder import BaseEncoder
from ..prompt_loader import load_prompt_template

logger = get_logger(__name__)


class SemanticCamoEncoder(BaseEncoder):
    """
    Multi-step semantic camouflage attack.

    Uses LLM to decompose harmful prompts into semantic features,
    then reconstructs them in a way that bypasses safety filters.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ):
        if model is None:
            raise ValueError("model is required — set it in conf/text_encoding/default.yaml")

        super().__init__(model=model, **kwargs)

        config = load_prompt_template("semantic_camo.yaml")
        self.extraction_prompt = config["extraction_prompt"].strip()
        self.step1_prompt = config["step1_prompt"].strip()
        self.step2_prompt = config["step2_prompt"].strip()

        self.service: BaseLLMService = LLMServiceFactory.create(model)
        if temperature is not None:
            self.service.temperature = temperature
        if max_tokens is not None:
            self.service.max_tokens = max_tokens

        logger.info(f"Initialized SemanticCamoEncoder with model: {model}")

    def _extract_components(self, prompt: str) -> tuple[str, str]:
        """Extract des1 (harmful description) and action1 (action type) from prompt."""
        message = self.extraction_prompt.format(prompt=prompt)
        results = self.service.batch_chat(
            conversations=[("extract", [(message, None)])],
            is_test=False,
        )
        response = results[0][1] if results else ""

        # Parse "des1: ...\naction1: ..." format
        des1 = prompt
        action1 = "guide"
        for line in response.strip().splitlines():
            line_lower = line.strip().lower()
            if line_lower.startswith("des1:"):
                des1 = line.split(":", 1)[1].strip().strip('"').strip("'")
            elif line_lower.startswith("action1:"):
                action1 = line.split(":", 1)[1].strip().strip('"').strip("'")

        return des1, action1

    def _step1_semantic_features(self, des1: str) -> str:
        """Step 1: Extract semantic features of the harmful description."""
        message = self.step1_prompt.format(des1=des1)
        results = self.service.batch_chat(
            conversations=[("step1", [(message, None)])],
            is_test=False,
        )
        return results[0][1] if results else ""

    def _step2_reconstruct(self, semantic_features: str, action1: str) -> str:
        """Step 2: Reconstruct instructions from semantic features."""
        message = self.step2_prompt.format(
            step1=semantic_features, action1=action1
        )
        results = self.service.batch_chat(
            conversations=[("step2", [(message, None)])],
            is_test=False,
        )
        return results[0][1] if results else ""

    def process(self, prompt: str, **kwargs) -> str:
        """Transform a harmful prompt via semantic camouflage."""
        des1, action1 = self._extract_components(prompt)
        logger.debug(f"Extracted: des1='{des1[:50]}...', action1='{action1}'")

        semantic_features = self._step1_semantic_features(des1)
        if not semantic_features:
            logger.warning("Step 1 returned empty; falling back to raw prompt")
            return prompt

        reconstructed = self._step2_reconstruct(semantic_features, action1)
        if not reconstructed:
            logger.warning("Step 2 returned empty; falling back to semantic features")
            return semantic_features

        return reconstructed
