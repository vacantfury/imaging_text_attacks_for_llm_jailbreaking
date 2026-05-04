"""
OpenAI service — uses ``AsyncOpenAI`` + ``asyncio.gather`` for concurrent
request processing.
"""
import asyncio
import random
from typing import Any, Dict, List, Optional, Tuple

from openai import AsyncOpenAI

from ..base_llm_service import BaseLLMService
from ..llm_model import LLMModel
from ..constants import (
    OPENAI_API_KEY,
    MODELS_USING_MAX_COMPLETION_TOKENS,
    MODELS_WITHOUT_TEMPERATURE_SUPPORT,
)
from ..media_utils import encode_image_to_b64
from ...utils.logger import get_logger

logger = get_logger(__name__)


class OpenAIService(BaseLLMService):
    """Service for OpenAI models (GPT-4o, GPT-5, etc.)."""

    def __init__(self, model: LLMModel, config=None, **kwargs):
        super().__init__(
            max_concurrency=kwargs.pop("max_concurrency", 20),
            max_retries=kwargs.pop("max_retries", 5),
            batch_poll_interval=kwargs.pop("batch_poll_interval", 30),
            batch_timeout=kwargs.pop("batch_timeout", 3600),
        )
        self.model = model
        self.api_key = kwargs.get("api_key") or OPENAI_API_KEY
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY in .env or pass api_key parameter"
            )
        self.temperature = kwargs.get("temperature", 0.0)
        self.max_tokens = kwargs.get("max_tokens", 4096)

        self.async_client = AsyncOpenAI(api_key=self.api_key)
        logger.info(f"Initialized OpenAI service with {model.model_id}")

    # ------------------------------------------------------------------
    # Model-specific helpers
    # ------------------------------------------------------------------

    def _build_api_params(
        self, messages: List[Dict], temperature: float, max_tokens: int,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"model": self.model.model_id, "messages": messages}

        if self.model not in MODELS_WITHOUT_TEMPERATURE_SUPPORT:
            params["temperature"] = temperature

        if self.model in MODELS_USING_MAX_COMPLETION_TOKENS:
            params["max_completion_tokens"] = max_tokens
        else:
            params["max_tokens"] = max_tokens

        return params

    @staticmethod
    def _extract_response(response) -> str:
        choice = response.choices[0]
        text = choice.message.content
        if not text or not text.strip():
            return f"[LLM response filtered out due to: {choice.finish_reason}]"
        return text

    # ------------------------------------------------------------------
    # Message formatting
    # ------------------------------------------------------------------

    @staticmethod
    def _format_conversation(
        messages: List[Tuple[str, Optional[Any]]], system_message: Optional[str],
    ) -> List[Dict[str, Any]]:
        openai_msgs: List[Dict[str, Any]] = []
        if system_message:
            openai_msgs.append({"role": "system", "content": system_message})

        for text, image in messages:
            if image is None:
                openai_msgs.append({"role": "user", "content": text})
            else:
                images = image if isinstance(image, list) else [image]
                content: list = [{"type": "text", "text": text}]
                for img in images:
                    if img is not None:
                        b64, mime = encode_image_to_b64(img)
                        content.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{b64}"},
                        })
                openai_msgs.append({"role": "user", "content": content})
        return openai_msgs

    # ------------------------------------------------------------------
    # Async execution
    # ------------------------------------------------------------------

    async def _one_call(
        self,
        sem: asyncio.Semaphore,
        messages: List[Dict],
        temperature: float,
        max_tokens: int,
        is_test: bool,
    ) -> str:
        async with sem:
            for attempt in range(self.max_retries + 1):
                try:
                    params = self._build_api_params(messages, temperature, max_tokens)
                    response = await self.async_client.chat.completions.create(**params)

                    if hasattr(response, "usage") and response.usage:
                        in_tok = response.usage.prompt_tokens or 0
                        out_tok = response.usage.completion_tokens or 0
                        cost = (
                            in_tok * self.model.input_price
                            + out_tok * self.model.output_price
                        ) / 1_000_000
                        self._record_usage(in_tok, out_tok, cost, is_test)

                    return self._extract_response(response)

                except Exception as e:
                    err = str(e)
                    if ("429" in err or "rate" in err.lower()) and attempt < self.max_retries:
                        wait = (2 ** attempt) + random.random()
                        logger.warning(
                            f"Rate limit hit, retry {attempt + 1}/{self.max_retries} "
                            f"in {wait:.1f}s"
                        )
                        await asyncio.sleep(wait)
                        continue
                    self._check_fatal_error(e, self.model.model_id)
                    logger.error(f"OpenAI API error: {err}")
                    return f"Error: {err}"
        return "Error: unreachable"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def batch_chat(
        self,
        conversations: List[Tuple[str, List[Tuple[str, Optional[Any]]]]],
        system_message: Optional[str] = None,
        is_test: bool = False,
        **kwargs,
    ) -> List[Tuple[str, str]]:
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)

        prepared = [
            (cid, self._format_conversation(msgs, system_message))
            for cid, msgs in conversations
        ]

        logger.info(
            f"Sending {len(prepared)} requests async (concurrency={self.max_concurrency})"
        )

        async def _run() -> List[str]:
            sem = asyncio.Semaphore(self.max_concurrency)
            tasks = [
                self._one_call(sem, msgs, temperature, max_tokens, is_test)
                for _, msgs in prepared
            ]
            return await asyncio.gather(*tasks)

        responses = asyncio.run(_run())
        return [(cid, resp) for (cid, _), resp in zip(prepared, responses)]
