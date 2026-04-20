"""
Local language model service using HuggingFace Transformers.

This service runs models locally on your hardware and automatically detects:
- MPS (Apple Silicon M1/M2/M3/M4)
- CUDA (NVIDIA GPUs)
- CPU (fallback)
"""
from typing import List, Tuple, Optional, Dict, Any, Union
from pathlib import Path

from ..base_llm_service import BaseLLMService
from ..llm_model import LLMModel
from ..constants import HUGGINGFACE_TOKEN, DEFAULT_LOCAL_BATCH_SIZE
from ...utils.logger import get_logger
from types import SimpleNamespace

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

logger = get_logger(__name__)

_DEFAULT_CONFIG = SimpleNamespace(temperature=0.0, max_tokens=0)


class LocalLMService(BaseLLMService):
    """
    Service for local models using HuggingFace Transformers.
    
    Automatically uses the best available device:
    - MPS on M4 Mac
    - CUDA on Linux cluster with NVIDIA GPUs
    - CPU as fallback
    """
    
    def __init__(self, model: LLMModel, config=None, **kwargs):
        """
        Initialize local LM service.
        
        Args:
            model: The LLM model to use
            config: Optional config with default parameters
            **kwargs: Additional parameters
                - temperature (float): Sampling temperature
                - max_tokens (int): Maximum tokens to generate
                - device (str): Force specific device ('cuda', 'mps', 'cpu')
                               If not specified, auto-detects best available
        """
        super().__init__()
        self.model = model
        self.config = config or _DEFAULT_CONFIG
        self.temperature = kwargs.get('temperature', self.config.temperature)
        self.max_tokens = kwargs.get('max_tokens', self.config.max_tokens)
        
        # Import required libraries
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
            self.torch = torch
            self.AutoModelForCausalLM = AutoModelForCausalLM
            self.AutoTokenizer = AutoTokenizer
            self.pipeline_fn = pipeline
        except ImportError:
            raise ImportError(
                "Required packages not installed. Install with: "
                "pip install torch transformers"
            )
        
        # Detect or set device
        self.device = kwargs.get('device') or self._detect_device()
        logger.info(f"Using device: {self.device}")
        
        # Load model and tokenizer
        logger.info(f"Loading model: {model.model_id}")
        self._load_model()
        logger.info(f"Model loaded successfully")
    
    def _detect_device(self) -> str:
        """Detect best available device."""
        if self.torch.cuda.is_available():
            return "cuda"
        elif hasattr(self.torch.backends, 'mps') and self.torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    def _load_model(self):
        """Load model and tokenizer."""
        model_id = self.model.model_id
        
        # Use HuggingFace token if available (for gated models like Llama)
        hf_token = HUGGINGFACE_TOKEN
        
        # Load tokenizer
        self.tokenizer = self.AutoTokenizer.from_pretrained(
            model_id,
            token=hf_token
        )
        
        # Set pad token if not set
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # CRITICAL: Set padding side to LEFT for decoder-only models (like Llama)
        # Right-padding can cause generation to hang or produce incorrect results
        self.tokenizer.padding_side = 'left'
        logger.info(f"Set tokenizer padding_side to 'left' for decoder-only model")
        
        # Load model with appropriate settings
        if self.device == "cuda":
            # Use float16 for GPU
            self.model_instance = self.AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=self.torch.float16,
                device_map="auto",
                token=hf_token
            )
        elif self.device == "mps":
            # MPS works best with float16
            self.model_instance = self.AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=self.torch.float16,
                token=hf_token
            )
            self.model_instance = self.model_instance.to(self.device)
        else:
            # CPU - use full precision
            self.model_instance = self.AutoModelForCausalLM.from_pretrained(
                model_id,
                token=hf_token
            )
            self.model_instance = self.model_instance.to(self.device)
        
        # Create pipeline for easier generation
        # Note: Override model's default generation_config to avoid warnings
        self.model_instance.generation_config.temperature = None
        self.model_instance.generation_config.top_p = None
        self.model_instance.generation_config.do_sample = None
        
        self.pipeline = self.pipeline_fn(
            "text-generation",
            model=self.model_instance,
            tokenizer=self.tokenizer,
            device=self.device if self.device != "auto" else None
        )
    
    @staticmethod
    def _prepare_prompt(
        prompt_data: Tuple[str, str],
        system_message: Optional[str]
    ) -> Tuple[str, str]:
        """
        Prepare a single prompt (CPU-bound preprocessing).
        
        Args:
            prompt_data: (id, prompt_text) tuple
            system_message: Optional system message
        
        Returns:
            (id, formatted_prompt) tuple
        """
        prompt_id, prompt_text = prompt_data
        if system_message:
            full_prompt = f"{system_message}\n\n{prompt_text}"
        else:
            full_prompt = prompt_text
        return (prompt_id, full_prompt)
    
    def _prepare_prompts(
        self,
        prompts: List[Tuple[str, str]],
        system_message: Optional[str] = None,
    ) -> List[Tuple[str, str]]:
        """Prepare multiple prompts for batch inference."""
        return [self._prepare_prompt(p, system_message) for p in prompts]
    
    def batch_generate(
        self,
        prompts: List[Tuple[str, str]],
        system_message: Optional[str] = None,
        is_test: bool = False,
        **kwargs
    ) -> List[Tuple[str, str]]:
        """
        Generate text responses for multiple prompts using GPU batch inference.

        Args:
            prompts: List of (id, prompt) tuples
            system_message: Optional system message
            **kwargs: Additional parameters (temperature, max_tokens, top_p, batch_size)

        Returns:
            List of (id, response) tuples. On errors, returns (id, error_message_string).
        """
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        top_p = kwargs.get('top_p', self.config.top_p)
        batch_size = kwargs.get('batch_size', DEFAULT_LOCAL_BATCH_SIZE)

        # MPS workaround: force batch_size=1 to avoid hanging
        if self.device == "mps" and batch_size > 1:
            logger.info(f"MPS device: reducing batch_size to 1 for stability")
            batch_size = 1

        prepared = self._prepare_prompts(prompts, system_message)
        
        # Step 2: Native GPU batch inference with progress bar
        prompt_ids = [pid for pid, _ in prepared]
        formatted_prompts = [prompt for _, prompt in prepared]
        
        pbar = None  # Initialize to avoid UnboundLocalError
        
        try:
            # Process in chunks to show progress
            logger.info(f"Running batch inference on {len(formatted_prompts)} prompts (device: {self.device}, batch_size: {batch_size})")
            
            results = []
            
            # Create chunks based on batch_size
            total_prompts = len(formatted_prompts)
            
            # Setup progress bar
            if TQDM_AVAILABLE:
                pbar = tqdm(
                    total=total_prompts,
                    desc=f"GPU Batch Inference ({self.device})",
                    unit="prompt",
                    bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]'
                )
            else:
                logger.info(f"Processing {total_prompts} prompts on {self.device}")
                pbar = None
            
            # Process in batches
            for i in range(0, total_prompts, batch_size):
                batch_end = min(i + batch_size, total_prompts)
                batch_ids = prompt_ids[i:batch_end]
                batch_prompts = formatted_prompts[i:batch_end]
                
                # Prepare generation config
                gen_kwargs = {
                    'max_new_tokens': max_tokens,
                    'pad_token_id': self.tokenizer.pad_token_id,
                    'return_full_text': False,
                    'batch_size': batch_size
                }
                
                # Handle sampling: only set temperature/top_p if sampling is enabled
                if temperature > 0:
                    gen_kwargs['do_sample'] = True
                    gen_kwargs['temperature'] = temperature
                    gen_kwargs['top_p'] = top_p
                else:
                    gen_kwargs['do_sample'] = False
                    # Don't set temperature or top_p when not sampling
                
                # Process this batch on GPU
                batch_outputs = self.pipeline(batch_prompts, **gen_kwargs)
                
                # Collect results
                for prompt_id, output, prompt_text in zip(batch_ids, batch_outputs, batch_prompts):
                    response_text = output[0]['generated_text']
                    # Track usage via tokenizer (cost=0 for local)
                    in_tok = len(self.tokenizer.encode(prompt_text))
                    out_tok = len(self.tokenizer.encode(response_text))
                    self._record_usage(in_tok, out_tok, 0.0, is_test)
                    results.append((prompt_id, response_text))
                
                # Update progress
                if pbar:
                    pbar.update(len(batch_ids))
            
            if pbar:
                pbar.close()
            
            return results
            
        except Exception as e:
            # Close progress bar if it exists
            if pbar:
                pbar.close()
            
            # Fallback to sequential processing if batch inference fails
            logger.warning(f"Batch inference failed: {e}. Falling back to sequential processing.")
            results = []

            # Setup progress bar for fallback
            iterator = prepared
            if TQDM_AVAILABLE:
                iterator = tqdm(
                    prepared,
                    desc="Sequential Inference (fallback)",
                    unit="prompt"
                )
            else:
                logger.info(f"Sequential fallback: processing {len(prepared)} prompts")
            
            for prompt_id, formatted_prompt in iterator:
                try:
                    # Prepare generation config
                    gen_kwargs = {
                        'max_new_tokens': max_tokens,
                        'pad_token_id': self.tokenizer.pad_token_id,
                        'return_full_text': False
                    }

                    if temperature > 0:
                        gen_kwargs['do_sample'] = True
                        gen_kwargs['temperature'] = temperature
                        gen_kwargs['top_p'] = top_p
                    else:
                        gen_kwargs['do_sample'] = False

                    output = self.pipeline(formatted_prompt, **gen_kwargs)
                    response_text = output[0]['generated_text']
                    # Track usage via tokenizer (cost=0 for local)
                    in_tok = len(self.tokenizer.encode(formatted_prompt))
                    out_tok = len(self.tokenizer.encode(response_text))
                    self._record_usage(in_tok, out_tok, 0.0, is_test)
                    results.append((prompt_id, response_text))
                except Exception as e2:
                    logger.error(f"Generation error for prompt {prompt_id}: {str(e2)}")
                    results.append((prompt_id, f"Error: {str(e2)}"))
            
            return results
    
    @staticmethod
    def _get_image_name(image: Any) -> str:
        """Get a descriptive name for an image."""
        try:
            from PIL import Image
            if isinstance(image, Image.Image):
                return f"PIL_Image_{image.size[0]}x{image.size[1]}"
        except ImportError:
            pass
        
        if isinstance(image, (str, Path)):
            return Path(image).name
        
        return "unknown_image"

    @staticmethod
    def _prepare_conversation(
        conversation_data: Tuple[str, List[Tuple[str, Any]]]
    ) -> Tuple[str, str]:
        """
        Prepare a single conversation (CPU-bound preprocessing).
        
        Args:
            conversation_data: (id, messages) tuple with (text, image) messages
                where image can be: None, file path string, PIL Image, or list of images
        
        Returns:
            (id, formatted_conversation) tuple
        """
        conv_id, messages = conversation_data
        conversation_parts = []
        has_images = False
        
        for prompt_text, image in messages:
            if image is not None:
                has_images = True
                # Normalize to list of images
                images = image if isinstance(image, list) else [image]
                image_names = [LocalLMService._get_image_name(img) for img in images if img is not None]
                if image_names:
                    conversation_parts.append(f"{prompt_text} [Images: {', '.join(image_names)}]")
                else:
                    conversation_parts.append(prompt_text)
            else:
                conversation_parts.append(prompt_text)
        
        full_prompt = "\n".join(conversation_parts)
        
        if has_images:
            # Add warning about image support
            full_prompt += "\n[Note: This model doesn't support image inputs directly]"
        
        return (conv_id, full_prompt)
    
    def _prepare_conversations(
        self,
        conversations: List[Tuple[str, List[Tuple[str, Any]]]],
    ) -> List[Tuple[str, str]]:
        """Prepare multiple conversations for batch inference."""
        return [self._prepare_conversation(c) for c in conversations]
    
    def batch_chat(
        self,
        conversations: List[Tuple[str, List[Tuple[str, Any]]]],
        is_test: bool = False,
        **kwargs
    ) -> List[Tuple[str, str]]:
        """
        Generate responses for multiple chat conversations using GPU batch inference.

        Note: Most local models don't support images natively. Images are converted
        to text placeholders.

        Args:
            conversations: List of (id, messages) tuples, where messages is
                a list of (prompt, image) tuples. Image can be file path, PIL Image, or list.
            **kwargs: Additional parameters (temperature, max_tokens, top_p, batch_size)

        Returns:
            List of (id, response) tuples. On errors, returns (id, error_message_string).
        """
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        top_p = kwargs.get('top_p', self.config.top_p)
        batch_size = kwargs.get('batch_size', DEFAULT_LOCAL_BATCH_SIZE)

        # MPS workaround: force batch_size=1 to avoid hanging
        if self.device == "mps" and batch_size > 1:
            logger.info(f"MPS device: reducing batch_size to 1 for stability")
            batch_size = 1

        prepared = self._prepare_conversations(conversations)
        
        # Step 2: Native GPU batch inference with progress bar
        conv_ids = [cid for cid, _ in prepared]
        formatted_conversations = [conv for _, conv in prepared]
        
        pbar = None  # Initialize to avoid UnboundLocalError
        
        try:
            # Process in chunks to show progress
            logger.info(f"Running batch inference on {len(formatted_conversations)} conversations (device: {self.device}, batch_size: {batch_size})")
            
            results = []
            
            # Create chunks based on batch_size
            total_conversations = len(formatted_conversations)
            
            # Setup progress bar
            if TQDM_AVAILABLE:
                pbar = tqdm(
                    total=total_conversations,
                    desc=f"GPU Batch Inference ({self.device})",
                    unit="conv",
                    bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]'
                )
            else:
                logger.info(f"Processing {total_conversations} conversations on {self.device}")
                pbar = None

            # Process in batches
            for i in range(0, total_conversations, batch_size):
                batch_end = min(i + batch_size, total_conversations)
                batch_ids = conv_ids[i:batch_end]
                batch_conversations = formatted_conversations[i:batch_end]
                
                # Prepare generation config
                gen_kwargs = {
                    'max_new_tokens': max_tokens,
                    'pad_token_id': self.tokenizer.pad_token_id,
                    'return_full_text': False,
                    'batch_size': batch_size
                }
                
                if temperature > 0:
                    gen_kwargs['do_sample'] = True
                    gen_kwargs['temperature'] = temperature
                    gen_kwargs['top_p'] = top_p
                else:
                    gen_kwargs['do_sample'] = False

                # Process this batch on GPU
                batch_outputs = self.pipeline(batch_conversations, **gen_kwargs)
                
                # Collect results
                for conv_id, output, conv_text in zip(batch_ids, batch_outputs, batch_conversations):
                    response_text = output[0]['generated_text']
                    # Track usage via tokenizer (cost=0 for local)
                    in_tok = len(self.tokenizer.encode(conv_text))
                    out_tok = len(self.tokenizer.encode(response_text))
                    self._record_usage(in_tok, out_tok, 0.0, is_test)
                    results.append((conv_id, response_text))
                
                # Update progress
                if pbar:
                    pbar.update(len(batch_ids))
            
            if pbar:
                pbar.close()
            
            return results
            
        except Exception as e:
            # Close progress bar if it exists
            if pbar:
                pbar.close()
            
            # Fallback to sequential processing if batch inference fails
            logger.warning(f"Batch inference failed: {e}. Falling back to sequential processing.")
            results = []

            # Setup progress bar for fallback
            iterator = prepared
            if TQDM_AVAILABLE:
                iterator = tqdm(
                    prepared,
                    desc="Sequential Inference (fallback)",
                    unit="conv"
                )
            else:
                logger.info(f"Sequential fallback: processing {len(prepared)} conversations")

            for conv_id, formatted_conv in iterator:
                try:
                    # Prepare generation config
                    gen_kwargs = {
                        'max_new_tokens': max_tokens,
                        'pad_token_id': self.tokenizer.pad_token_id,
                        'return_full_text': False
                    }

                    if temperature > 0:
                        gen_kwargs['do_sample'] = True
                        gen_kwargs['temperature'] = temperature
                        gen_kwargs['top_p'] = top_p
                    else:
                        gen_kwargs['do_sample'] = False

                    output = self.pipeline(formatted_conv, **gen_kwargs)
                    response_text = output[0]['generated_text']
                    # Track usage via tokenizer (cost=0 for local)
                    in_tok = len(self.tokenizer.encode(formatted_conv))
                    out_tok = len(self.tokenizer.encode(response_text))
                    self._record_usage(in_tok, out_tok, 0.0, is_test)
                    results.append((conv_id, response_text))
                except Exception as e2:
                    logger.error(f"Generation error for conversation {conv_id}: {str(e2)}")
                    results.append((conv_id, f"Error: {str(e2)}"))
            
            return results
