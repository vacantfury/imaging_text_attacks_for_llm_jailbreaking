"""
OpenAI service implementation.
"""
from typing import List, Tuple, Optional, Dict, Any, Union
from pathlib import Path
import base64
import io

from ..base_llm_service import BaseLLMService
from ..llm_model import LLMModel
from ..constants import (
    OPENAI_API_KEY,
    MODELS_USING_MAX_COMPLETION_TOKENS,
    MODELS_WITHOUT_TEMPERATURE_SUPPORT,
)
from ...utils.logger import get_logger
from types import SimpleNamespace

logger = get_logger(__name__)

_DEFAULT_CONFIG = SimpleNamespace(temperature=0.0, max_tokens=0)


class OpenAIService(BaseLLMService):
    """Service for OpenAI models (GPT-3.5, GPT-4, etc.)."""
    
    def __init__(self, model: LLMModel, config=None, **kwargs):
        """
        Initialize OpenAI service.
        
        Args:
            model: The LLM model to use
            config: Optional config with default parameters
            **kwargs: Additional parameters
                - api_key (str): OpenAI API key (optional, will load from env)
                - temperature (float): Sampling temperature
                - max_tokens (int): Maximum tokens to generate
        """
        super().__init__()
        self.model = model
        self.config = config or _DEFAULT_CONFIG
        self.api_key = kwargs.get('api_key') or OPENAI_API_KEY
        if not self.api_key:
            logger.error("OpenAI API key not found")
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY in .env or pass api_key parameter")
        self.temperature = kwargs.get('temperature', self.config.temperature)
        self.max_tokens = kwargs.get('max_tokens', self.config.max_tokens)
        
        # Initialize OpenAI client
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"Initialized OpenAI service with {model.model_id}")
        except ImportError:
            logger.error("OpenAI package not installed")
            raise ImportError("OpenAI package not installed. Install with: pip install openai")
    
    def _uses_max_completion_tokens(self) -> bool:
        """
        Check if this model uses max_completion_tokens instead of max_tokens.
        
        Newer models (GPT-4.1+, GPT-5, GPT-O series) use max_completion_tokens.
        Older models (GPT-3.5, GPT-4, GPT-4-turbo, GPT-4o) use max_tokens.
        
        Uses the MODELS_USING_MAX_COMPLETION_TOKENS set from constants for
        accurate model-specific behavior.
        
        Returns:
            True if model uses max_completion_tokens, False if it uses max_tokens
        """
        return self.model in MODELS_USING_MAX_COMPLETION_TOKENS
    
    def _supports_temperature(self) -> bool:
        """
        Check if this model supports custom temperature values.
        
        Some newer models (e.g., GPT-5-Nano) only support the default temperature (1.0)
        and will error if you try to set a custom value.
        
        Uses the MODELS_WITHOUT_TEMPERATURE_SUPPORT set from constants for
        accurate model-specific behavior.
        
        Returns:
            True if model supports custom temperature, False if it only accepts default
        """
        return self.model not in MODELS_WITHOUT_TEMPERATURE_SUPPORT
    
    @staticmethod
    def _prepare_prompt(
        prompt_data: Tuple[str, str],
        system_message: Optional[str]
    ) -> Tuple[str, List[Dict[str, str]]]:
        """
        Prepare a single prompt for API call (CPU-bound preprocessing).
        
        Args:
            prompt_data: (id, prompt_text) tuple
            system_message: Optional system message
        
        Returns:
            (id, messages) tuple ready for API call
        """
        prompt_id, prompt_text = prompt_data
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt_text})
        return (prompt_id, messages)
    
    @staticmethod
    def _encode_image(image) -> Tuple[str, str]:
        """
        Encode an image to base64 and determine its MIME type.
        
        Args:
            image: Either a file path (str/Path) or a PIL Image object
            
        Returns:
            (base64_data, mime_type) tuple
        """
        import io
        
        # Check if it's a PIL Image
        try:
            from PIL import Image
            if isinstance(image, Image.Image):
                # It's a PIL Image - encode directly
                buffer = io.BytesIO()
                img_format = image.format or 'PNG'
                mime_type = {
                    'JPEG': 'image/jpeg',
                    'JPG': 'image/jpeg', 
                    'PNG': 'image/png',
                    'GIF': 'image/gif',
                    'WEBP': 'image/webp'
                }.get(img_format.upper(), 'image/png')
                image.save(buffer, format=img_format if img_format != 'JPG' else 'JPEG')
                image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
                return image_data, mime_type
        except ImportError:
            pass
        
        # It's a file path - read from disk
        image_path = str(image)
        with open(image_path, 'rb') as img_file:
            image_data = base64.b64encode(img_file.read()).decode('utf-8')
        
        ext = Path(image_path).suffix.lower()
        mime_type = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }.get(ext, 'image/jpeg')
        
        return image_data, mime_type
    
    @staticmethod
    def _prepare_conversation(
        conversation_data: Tuple[str, List[Tuple[str, Any]]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Prepare a single conversation for API call (CPU-bound preprocessing).
        
        Args:
            conversation_data: (id, messages) tuple with (text, image) messages
                where image can be: None, file path string, PIL Image, or list of images
        
        Returns:
            (id, formatted_messages) tuple ready for API call
        """
        conv_id, messages = conversation_data
        openai_messages = []
        
        for prompt_text, image in messages:
            if image is None:
                # Text-only message
                openai_messages.append({
                    "role": "user",
                    "content": prompt_text
                })
            else:
                # Multimodal message with image(s)
                try:
                    # Normalize to list of images
                    images = image if isinstance(image, list) else [image]
                    
                    content = [{"type": "text", "text": prompt_text}]
                    for img in images:
                        if img is not None:
                            image_data, mime_type = OpenAIService._encode_image(img)
                            content.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_data}"
                                }
                            })
                    
                    openai_messages.append({
                        "role": "user",
                        "content": content
                    })
                except Exception as e:
                    # If image loading fails, send text only
                    logger.warning(f"Image load error: {str(e)}")
                    openai_messages.append({
                        "role": "user",
                        "content": f"{prompt_text} [Image load error: {str(e)}]"
                    })
        
        return (conv_id, openai_messages)
    
    def _prepare_prompts(
        self,
        prompts: List[Tuple[str, str]],
        system_message: Optional[str] = None,
    ) -> List[Tuple[str, List[Dict[str, str]]]]:
        """Prepare multiple prompts for batch API submission."""
        return [self._prepare_prompt(p, system_message) for p in prompts]
    
    def _prepare_conversations(
        self,
        conversations: List[Tuple[str, List[Tuple[str, Optional[Any]]]]],
    ) -> List[Tuple[str, List[Dict[str, Any]]]]:
        """Prepare multiple conversations for batch API submission."""
        return [self._prepare_conversation(c) for c in conversations]
    
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
            prompts: List of (id, prompt) tuples
            system_message: Optional system message
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
        Returns:
            List of (id, response) tuples
        """
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        
        prepared = self._prepare_prompts(prompts, system_message)
        
        # Sequential API calls (or submit prepared batch to OpenAI Batch API)
        results = []
        total = len(prepared)
        for idx, (prompt_id, messages) in enumerate(prepared, 1):
            try:
                logger.debug(f"Processing request {idx}/{total} (ID: {prompt_id})")
                # Use appropriate parameters based on model capabilities
                api_params = {
                    "model": self.model.model_id,
                    "messages": messages,
                }
                
                # Only add temperature if model supports it
                if self._supports_temperature():
                    api_params["temperature"] = temperature
                # else: Use default temperature (1.0) implicitly
                
                # Newer models use max_completion_tokens, older use max_tokens
                if self._uses_max_completion_tokens():
                    api_params["max_completion_tokens"] = max_tokens
                else:
                    api_params["max_tokens"] = max_tokens
                
                response = self.client.chat.completions.create(**api_params)
                
                # Track usage
                if hasattr(response, 'usage') and response.usage:
                    in_tok = response.usage.prompt_tokens or 0
                    out_tok = response.usage.completion_tokens or 0
                    cost = (in_tok * self.model.input_price + out_tok * self.model.output_price) / 1_000_000
                    self._record_usage(in_tok, out_tok, cost, is_test)
                
                # Extract response and check for safety filtering
                choice = response.choices[0]
                response_text = choice.message.content
                finish_reason = choice.finish_reason
                
                # Log raw response details for debugging
                logger.debug(f"Prompt {prompt_id}: finish_reason={finish_reason}, content_length={len(response_text) if response_text else 0}")
                
                # Handle empty/None responses due to safety filters
                if not response_text or response_text.strip() == "":
                    filter_msg = f"[LLM response filtered out due to: {finish_reason}"
                    
                    # Check for additional safety information
                    if hasattr(response, 'system_fingerprint'):
                        filter_msg += f", system_fingerprint={response.system_fingerprint}"
                    
                    # Log the full response object for debugging
                    logger.warning(f"Empty response for prompt {prompt_id}. Finish reason: {finish_reason}")
                    logger.debug(f"Full response object: {response.model_dump_json() if hasattr(response, 'model_dump_json') else str(response)}")
                    
                    filter_msg += "]"
                    response_text = filter_msg
                
                results.append((prompt_id, response_text))
                logger.debug(f"Completed request {idx}/{total} (ID: {prompt_id})")
            except Exception as e:
                # Check for fatal model errors (404 Not Found)
                error_str = str(e).lower()
                if "not found" in error_str or "does not exist" in error_str or (hasattr(e, 'status_code') and e.status_code == 404):
                    logger.critical(f"FATAL: Model ID {self.model.model_id} not found/unrecognized.")
                    from src.utils.exceptions import FatalModelError
                    raise FatalModelError(f"Model {self.model.model_id} not found") from e
                    
                error_msg = str(e)
                logger.error(f"OpenAI API error for prompt {prompt_id} (request {idx}/{total}): {error_msg}")
                results.append((prompt_id, f"Error: {error_msg}"))
        
        return results
    
    def batch_chat(
        self,
        conversations: List[Tuple[str, List[Tuple[str, Optional[Any]]]]],
        is_test: bool = False,
        **kwargs
    ) -> List[Tuple[str, str]]:
        """
        Generate responses for multiple chat conversations.
        
        Args:
            conversations: List of (id, messages) tuples, where messages is
                a list of (prompt, image) tuples. Image can be file path or PIL Image.
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
        Returns:
            List of (id, response) tuples
        """
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        
        prepared = self._prepare_conversations(conversations)
        
        # Sequential API calls (or submit prepared batch to OpenAI Batch API)
        results = []
        total = len(prepared)
        log_interval = max(1, total // 10)  # Log every 10% or at least every request
        for idx, (conv_id, openai_messages) in enumerate(prepared, 1):
            try:
                if idx == 1 or idx % log_interval == 0 or idx == total:
                    logger.info(f"Processing request {idx}/{total} ({idx*100//total}%)")
                logger.debug(f"Processing conversation {idx}/{total} (ID: {conv_id})")
                # Use appropriate parameters based on model capabilities
                api_params = {
                    "model": self.model.model_id,
                    "messages": openai_messages,
                }
                
                # Only add temperature if model supports it
                if self._supports_temperature():
                    api_params["temperature"] = temperature
                # else: Use default temperature (1.0) implicitly
                
                # Newer models use max_completion_tokens, older use max_tokens
                if self._uses_max_completion_tokens():
                    api_params["max_completion_tokens"] = max_tokens
                else:
                    api_params["max_tokens"] = max_tokens
                
                response = self.client.chat.completions.create(**api_params)
                
                # Track usage
                if hasattr(response, 'usage') and response.usage:
                    in_tok = response.usage.prompt_tokens or 0
                    out_tok = response.usage.completion_tokens or 0
                    cost = (in_tok * self.model.input_price + out_tok * self.model.output_price) / 1_000_000
                    self._record_usage(in_tok, out_tok, cost, is_test)
                
                # Extract response and check for safety filtering
                choice = response.choices[0]
                response_text = choice.message.content
                finish_reason = choice.finish_reason
                
                # Log raw response details for debugging
                logger.debug(f"Conversation {conv_id}: finish_reason={finish_reason}, content_length={len(response_text) if response_text else 0}")
                
                # Handle empty/None responses due to safety filters
                if not response_text or response_text.strip() == "":
                    filter_msg = f"[LLM response filtered out due to: {finish_reason}"
                    
                    # Check for additional safety information
                    if hasattr(response, 'system_fingerprint'):
                        filter_msg += f", system_fingerprint={response.system_fingerprint}"
                    
                    # Log the full response object for debugging
                    logger.warning(f"Empty response for conversation {conv_id}. Finish reason: {finish_reason}")
                    logger.debug(f"Full response object: {response.model_dump_json() if hasattr(response, 'model_dump_json') else str(response)}")
                    
                    filter_msg += "]"
                    response_text = filter_msg
                
                results.append((conv_id, response_text))
                logger.debug(f"Completed conversation {idx}/{total} (ID: {conv_id})")
            except Exception as e:
                # Check for fatal model errors (404 Not Found)
                error_str = str(e).lower()
                if "not found" in error_str or "does not exist" in error_str or (hasattr(e, 'status_code') and e.status_code == 404):
                    logger.critical(f"FATAL: Model ID {self.model.model_id} not found/unrecognized.")
                    from src.utils.exceptions import FatalModelError
                    raise FatalModelError(f"Model {self.model.model_id} not found") from e
                    
                error_msg = str(e)
                logger.error(f"OpenAI API error for conversation {conv_id} (request {idx}/{total}): {error_msg}")
                results.append((conv_id, f"Error: {error_msg}"))
        
        return results
