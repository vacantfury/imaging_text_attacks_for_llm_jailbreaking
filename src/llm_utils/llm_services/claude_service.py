"""
Anthropic Claude service implementation.
"""
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path
import base64
import io

from ..base_llm_service import BaseLLMService
from ..llm_model import LLMModel
from ..constants import ANTHROPIC_API_KEY
from ...utils.logger import get_logger
from types import SimpleNamespace

logger = get_logger(__name__)

_DEFAULT_CONFIG = SimpleNamespace(temperature=0.0, max_tokens=0)


class ClaudeService(BaseLLMService):
    """Service for Anthropic Claude models."""
    
    def __init__(self, model: LLMModel, config=None, **kwargs):
        """
        Initialize Claude service.
        
        Args:
            model: The LLM model to use
            config: Optional config with default parameters
            **kwargs: Additional parameters
                - api_key (str): Anthropic API key (optional, will load from env)
                - temperature (float): Sampling temperature
                - max_tokens (int): Maximum tokens to generate
        """
        super().__init__()
        self.model = model
        self.config = config or _DEFAULT_CONFIG
        self.api_key = kwargs.get('api_key') or ANTHROPIC_API_KEY
        if not self.api_key:
            logger.error("Anthropic API key not found")
            raise ValueError("Anthropic API key not found. Set ANTHROPIC_API_KEY in .env or pass api_key parameter")
        self.temperature = kwargs.get('temperature', self.config.temperature)
        self.max_tokens = kwargs.get('max_tokens', self.config.max_tokens)
        
        # Initialize Anthropic client
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
            logger.info(f"Initialized Claude service with {model.model_id}")
        except ImportError:
            logger.error("Anthropic package not installed")
            raise ImportError("Anthropic package not installed. Install with: pip install anthropic")
    
    @staticmethod
    def _prepare_prompt(
        prompt_data: Tuple[str, str],
        system_message: Optional[str]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Prepare a single prompt for API call (CPU-bound preprocessing).
        
        Args:
            prompt_data: (id, prompt_text) tuple
            system_message: Optional system message
        
        Returns:
            (id, params_dict) tuple ready for API call
        """
        prompt_id, prompt_text = prompt_data
        params = {
            "messages": [{"role": "user", "content": prompt_text}]
        }
        if system_message:
            params["system"] = system_message
        return (prompt_id, params)
    
    @staticmethod
    def _encode_image(image: Any) -> Tuple[str, str]:
        """
        Encode an image to base64 and determine its media type.
        
        Args:
            image: Either a file path (str/Path) or a PIL Image object
            
        Returns:
            (base64_data, media_type) tuple
        """
        # Check if it's a PIL Image
        try:
            from PIL import Image
            if isinstance(image, Image.Image):
                # It's a PIL Image - encode directly
                buffer = io.BytesIO()
                img_format = image.format or 'PNG'
                media_type = {
                    'JPEG': 'image/jpeg',
                    'JPG': 'image/jpeg',
                    'PNG': 'image/png',
                    'GIF': 'image/gif',
                    'WEBP': 'image/webp'
                }.get(img_format.upper(), 'image/png')
                image.save(buffer, format=img_format if img_format != 'JPG' else 'JPEG')
                image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
                return image_data, media_type
        except ImportError:
            pass
        
        # It's a file path - read from disk
        image_path = str(image)
        with open(image_path, 'rb') as img_file:
            image_data = base64.b64encode(img_file.read()).decode('utf-8')
        
        ext = Path(image_path).suffix.lower()
        media_type = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }.get(ext, 'image/jpeg')
        
        return image_data, media_type

    @staticmethod
    def _prepare_conversation(
        conversation_data: Tuple[str, List[Tuple[str, Any]]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Prepare a single conversation for API call.
        
        Args:
            conversation_data: (id, messages) tuple with (text, image) messages
                where image can be: None, file path string, PIL Image, or list of images
        
        Returns:
            (id, formatted_messages) tuple ready for API call
        """
        conv_id, messages = conversation_data
        anthropic_messages = []
        
        for prompt_text, image in messages:
            if image is None:
                # Text-only message
                anthropic_messages.append({
                    "role": "user",
                    "content": prompt_text
                })
            else:
                # Multimodal message with image(s)
                try:
                    # Normalize to list of images
                    images = image if isinstance(image, list) else [image]
                    
                    content = []
                    for img in images:
                        if img is not None:
                            image_data, media_type = ClaudeService._encode_image(img)
                            content.append({
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data
                                }
                            })
                    content.append({"type": "text", "text": prompt_text})
                    
                    anthropic_messages.append({
                        "role": "user",
                        "content": content
                    })
                except Exception as e:
                    # If image loading fails, send text only
                    logger.warning(f"Image load error: {str(e)}")
                    anthropic_messages.append({
                        "role": "user",
                        "content": f"{prompt_text} [Image load error: {str(e)}]"
                    })
        
        return (conv_id, anthropic_messages)
    
    def _prepare_prompts(
        self,
        prompts: List[Tuple[str, str]],
        system_message: Optional[str] = None,
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """Prepare multiple prompts for batch API submission."""
        return [self._prepare_prompt(p, system_message) for p in prompts]
    
    def _prepare_conversations(
        self,
        conversations: List[Tuple[str, List[Tuple[str, Any]]]],
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
        
        # Sequential API calls (or submit prepared batch to Anthropic Message Batches API)
        results = []
        for prompt_id, params_dict in prepared:
            try:
                params = {
                    "model": self.model.model_id,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    **params_dict
                }
                
                response = self.client.messages.create(**params)
                
                # Track usage
                if hasattr(response, 'usage') and response.usage:
                    in_tok = response.usage.input_tokens or 0
                    out_tok = response.usage.output_tokens or 0
                    cost = (in_tok * self.model.input_price + out_tok * self.model.output_price) / 1_000_000
                    self._record_usage(in_tok, out_tok, cost, is_test)
                
                response_text = response.content[0].text
                results.append((prompt_id, response_text))
            except Exception as e:
                # Check for fatal model errors (404 Not Found)
                error_str = str(e).lower()
                if "not found" in error_str or (hasattr(e, 'status_code') and e.status_code == 404):
                    logger.critical(f"FATAL: Model ID {self.model.model_id} not found/unrecognized.")
                    from src.utils.exceptions import FatalModelError
                    raise FatalModelError(f"Model {self.model.model_id} not found") from e
                
                logger.error(f"Claude API error for prompt {prompt_id}: {str(e)}")
                results.append((prompt_id, f"Error: {str(e)}"))
        
        return results
    
    def batch_chat(
        self,
        conversations: List[Tuple[str, List[Tuple[str, Any]]]],
        is_test: bool = False,
        **kwargs
    ) -> List[Tuple[str, str]]:
        """
        Generate responses for multiple chat conversations.
        
        Args:
            conversations: List of (id, messages) tuples, where messages is
                a list of (prompt, image) tuples. Image can be file path, PIL Image, or list.
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
        Returns:
            List of (id, response) tuples
        """
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        
        prepared = self._prepare_conversations(conversations)
        
        # Sequential API calls (or submit prepared batch to Anthropic Message Batches API)
        results = []
        total = len(prepared)
        log_interval = max(1, total // 10)  # Log every 10% or at least every request
        for idx, (conv_id, anthropic_messages) in enumerate(prepared, 1):
            try:
                if idx == 1 or idx % log_interval == 0 or idx == total:
                    logger.info(f"Processing request {idx}/{total} ({idx*100//total}%)")
                response = self.client.messages.create(
                    model=self.model.model_id,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=anthropic_messages
                )
                
                # Track usage
                if hasattr(response, 'usage') and response.usage:
                    in_tok = response.usage.input_tokens or 0
                    out_tok = response.usage.output_tokens or 0
                    cost = (in_tok * self.model.input_price + out_tok * self.model.output_price) / 1_000_000
                    self._record_usage(in_tok, out_tok, cost, is_test)
                
                response_text = response.content[0].text
                results.append((conv_id, response_text))
            except Exception as e:
                # Check for fatal model errors (404 Not Found)
                error_str = str(e).lower()
                if "not found" in error_str or (hasattr(e, 'status_code') and e.status_code == 404):
                    logger.critical(f"FATAL: Model ID {self.model.model_id} not found/unrecognized.")
                    from src.utils.exceptions import FatalModelError
                    raise FatalModelError(f"Model {self.model.model_id} not found") from e
                
                logger.error(f"Claude API error for conversation {conv_id}: {str(e)}")
                results.append((conv_id, f"Error: {str(e)}"))
        
        return results
