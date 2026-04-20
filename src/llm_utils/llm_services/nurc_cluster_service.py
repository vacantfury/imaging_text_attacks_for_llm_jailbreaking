"""
NURC Cluster service via vLLM OpenAI-compatible HTTP server.

This service uses the ClusterModelServerManager's dynamic endpoint pool.
Before each batch call, it acquires an endpoint; after the call, it releases it.
This allows multiple tasks to share a pool of vLLM servers.
"""
from typing import List, Tuple, Optional, Any

from ..base_llm_service import BaseLLMService
from ..llm_model import LLMModel
from ...utils.logger import get_logger
from types import SimpleNamespace

logger = get_logger(__name__)

_DEFAULT_CONFIG = SimpleNamespace(temperature=0.0, max_tokens=0)


class NURCClusterService(BaseLLMService):
    """
    Service for models running on NURC cluster via vLLM HTTP server.
    
    Requires a ClusterModelServerManager with running/pending servers.
    Acquires an endpoint from the pool for each batch call, releases after completion.
    
    Args (via kwargs):
        server_manager: Required. The ClusterModelServerManager instance.
    """
    
    def __init__(self, model: LLMModel, config=None, **kwargs):
        server_manager = kwargs.pop("server_manager", None)
        if not server_manager:
            raise ValueError(
                "NURCClusterService requires 'server_manager' kwarg. "
                "Use ClusterModelServerManager to start the vLLM server first."
            )
        
        super().__init__()
        self.model = model
        self.config = config or _DEFAULT_CONFIG
        self.temperature = kwargs.get('temperature', self.config.temperature)
        self.max_tokens = kwargs.get('max_tokens', self.config.max_tokens)
        self.server_manager = server_manager
        
        logger.info(f"Initialized cluster service for {model.model_id} (dynamic pool)")
    
    def _create_client(self, server_url: str):
        """Create an OpenAI client pointed at the given vLLM endpoint."""
        try:
            import httpx
            from openai import OpenAI
            return OpenAI(
                base_url=server_url,
                api_key="unused",  # vLLM doesn't require an API key
                http_client=httpx.Client(
                    trust_env=False,  # Bypass cluster Squid proxy
                    timeout=httpx.Timeout(600.0, connect=60.0),
                ),
            )
        except ImportError:
            raise ImportError(
                "openai package is required for NURCClusterService. "
                "Install with: pip install openai"
            )
    
    def batch_generate(
        self,
        prompts: List[Tuple[str, str]],
        system_message: Optional[str] = None,
        is_test: bool = False,
        **kwargs
    ) -> List[Tuple[str, str]]:
        """Generate text responses via vLLM server."""
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        
        # Acquire endpoint from pool
        endpoint = self.server_manager.acquire_endpoint(self.model)
        client = self._create_client(endpoint)
        
        try:
            results = []
            total = len(prompts)
            log_interval = max(1, total // 10)
            
            for idx, (prompt_id, prompt_text) in enumerate(prompts, 1):
                try:
                    if idx == 1 or idx % log_interval == 0 or idx == total:
                        logger.info(f"Processing request {idx}/{total} ({idx*100//total}%)")
                    
                    messages = []
                    if system_message:
                        messages.append({"role": "system", "content": system_message})
                    messages.append({"role": "user", "content": prompt_text})
                    
                    response = client.chat.completions.create(
                        model=self.model.model_id,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    
                    response_text = response.choices[0].message.content or ""
                    if not response_text.strip():
                        response_text = f"[Empty response from vLLM server]"
                    
                    # Track usage (vLLM returns OpenAI-compatible usage)
                    if hasattr(response, 'usage') and response.usage:
                        in_tok = response.usage.prompt_tokens or 0
                        out_tok = response.usage.completion_tokens or 0
                        self._record_usage(in_tok, out_tok, 0.0, is_test)
                    
                    results.append((prompt_id, response_text))
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"vLLM API error for prompt {prompt_id}: {error_msg}")
                    results.append((prompt_id, f"Error: {error_msg}"))
            
            return results
        finally:
            self.server_manager.release_endpoint(self.model, endpoint)
    
    def batch_chat(
        self,
        conversations: List[Tuple[str, List[Tuple[str, Optional[Any]]]]],
        is_test: bool = False,
        **kwargs
    ) -> List[Tuple[str, str]]:
        """Generate responses for chat conversations via vLLM server."""
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        
        # Acquire endpoint from pool
        endpoint = self.server_manager.acquire_endpoint(self.model)
        client = self._create_client(endpoint)
        
        try:
            results = []
            total = len(conversations)
            log_interval = max(1, total // 10)
            
            for idx, (conv_id, messages) in enumerate(conversations, 1):
                try:
                    if idx == 1 or idx % log_interval == 0 or idx == total:
                        logger.info(f"Processing conversation {idx}/{total} ({idx*100//total}%)")
                    
                    # Build OpenAI-format messages
                    openai_messages = []
                    for msg in messages:
                        text = msg[0]
                        openai_messages.append({"role": "user", "content": text})
                    
                    response = client.chat.completions.create(
                        model=self.model.model_id,
                        messages=openai_messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    
                    response_text = response.choices[0].message.content or ""
                    
                    # Track usage (vLLM returns OpenAI-compatible usage)
                    if hasattr(response, 'usage') and response.usage:
                        in_tok = response.usage.prompt_tokens or 0
                        out_tok = response.usage.completion_tokens or 0
                        self._record_usage(in_tok, out_tok, 0.0, is_test)
                    
                    results.append((conv_id, response_text))
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"vLLM API error for conversation {conv_id}: {error_msg}")
                    results.append((conv_id, f"Error: {error_msg}"))
            
            return results
        finally:
            self.server_manager.release_endpoint(self.model, endpoint)
