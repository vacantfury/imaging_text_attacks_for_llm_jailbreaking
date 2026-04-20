"""
Constants for LLM configurations and endpoints.
"""
import os
from typing import Final, Optional, TYPE_CHECKING

# Load .env file if python-dotenv is available
from dotenv import load_dotenv

# Import LLMModel for type annotations
if TYPE_CHECKING:
    from .llm_model import LLMModel

load_dotenv()


# API Keys (loaded from environment variables)
OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
HUGGINGFACE_TOKEN: Optional[str] = os.getenv("HUGGINGFACE_TOKEN")

# API endpoints
OPENAI_API_URL: Final[str] = "https://api.openai.com/v1"
OLLAMA_BASE_URL: Final[str] = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_VERSION_URL: Final[str] = f"{OLLAMA_BASE_URL}/api/version"
OLLAMA_CHAT_URL: Final[str] = f"{OLLAMA_BASE_URL}/api/chat"
OLLAMA_GENERATE_URL: Final[str] = f"{OLLAMA_BASE_URL}/api/generate"

DEFAULT_SYSTEM_MESSAGE: Final[str] = "You are a helpful assistant."


# =============================================================================
# OpenAI Model-Specific Parameters
# =============================================================================
# OpenAI changed parameter naming in newer models for clarity:
#
# max_tokens (older models):
#   - Used by: GPT-3.5-Turbo, GPT-4, GPT-4-Turbo, GPT-4o
#   - Limits the number of tokens in the completion (response only)
#   - Despite the generic name, it doesn't include prompt tokens
#
# max_completion_tokens (newer models):
#   - Used by: GPT-4.1+, GPT-5, O-series
#   - Same functionality but more explicit naming
#   - Makes it clearer it's just the completion length, not total tokens
#
# Functionally equivalent, just different parameter names for API compatibility.

# Models that use max_completion_tokens (newer models)
# All other OpenAI models use max_tokens (older models)

# Import at runtime to avoid circular dependency issues
from .llm_model import LLMModel  # noqa: E402

MODELS_USING_MAX_COMPLETION_TOKENS: Final[set[LLMModel]] = {
    # GPT-4.1 series
    LLMModel.GPT_4_1,
    LLMModel.GPT_4_1_MINI,
    LLMModel.GPT_4_1_NANO,
    
    # GPT-5 series
    LLMModel.GPT_5,
    LLMModel.GPT_5_MINI,
    LLMModel.GPT_5_NANO,
    
    # O-series models
    LLMModel.GPT_O3,
    LLMModel.GPT_O4_MINI,
}

# Note: GPT-3.5-Turbo, GPT-4, GPT-4-Turbo, and GPT-4o use 'max_tokens'


# =============================================================================
# OpenAI Temperature Support
# =============================================================================
# Some newer models don't support custom temperature values
# They only accept the default (temperature=1.0) and will error if you try to set it

MODELS_WITHOUT_TEMPERATURE_SUPPORT: Final[set[LLMModel]] = {
    # GPT-5 series (nano variant)
    LLMModel.GPT_5_NANO,
    
    # Note: Add other models here if they don't support custom temperature
    # GPT-5 and GPT-5-Mini may support temperature, but GPT-5-Nano doesn't
}


# =============================================================================
# Batch processing settings
# =============================================================================

# API batch processing (OpenAI, Claude)
# Note: Currently for documentation purposes. Use when implementing async batch API calls.
DEFAULT_API_BATCH_SIZE: Final[int] = 300  # Max API requests in a batch

# Local model GPU batch inference (HuggingFace Transformers)
# Adjust based on your model size and GPU:
# - Large models (7B-8B) on MPS: 1-2 (can hang, use sequential)
# - Small models (1B-3B) on MPS: 4-8
# - CUDA GPUs (RTX 3090, 4090): 8-16
# - High-end GPUs (A100, H100): 32-64
# Note: 1B models work well with batch_size=4, larger models may need batch_size=1
DEFAULT_LOCAL_BATCH_SIZE: Final[int] = 4  # Good for 1B models on MPS


# =============================================================================
# Vision-Language Model Support
# =============================================================================
# vLLM's llm.chat() handles images automatically via structured messages.
# No model-specific placeholders needed - just pass PIL.Image in the content:
#   {"type": "image_url", "image_url": {"url": pil_image}}
