"""
LLM model definitions with provider information and pricing.
"""
from enum import Enum


class Provider(str, Enum):
    """Enum for LLM service providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"
    NU_CLUSTER = "nu_cluster"


class LLMModel(Enum):
    """
    Enum for LLM models.
    
    Each model has:
    - model_id: The actual model identifier string
    - provider: Which service implementation to use
    - input_price: Cost per 1M input tokens (USD)
    - output_price: Cost per 1M output tokens (USD)
    """
    
    # OpenAI models (model_id, provider, input_$/M, output_$/M)
    GPT_3_5_TURBO = ("gpt-3.5-turbo", Provider.OPENAI, 0.50, 1.50)
    GPT_4 = ("gpt-4", Provider.OPENAI, 30.00, 60.00)
    GPT_4_TURBO = ("gpt-4-turbo", Provider.OPENAI, 10.00, 30.00)
    GPT_4O = ("gpt-4o", Provider.OPENAI, 2.50, 10.00)
    GPT_4O_MINI = ("gpt-4o-mini", Provider.OPENAI, 0.15, 0.60)
    GPT_4_1 = ("gpt-4.1", Provider.OPENAI, 2.00, 8.00)
    GPT_4_1_MINI = ("gpt-4.1-mini", Provider.OPENAI, 0.40, 1.60)
    GPT_4_1_NANO = ("gpt-4.1-nano", Provider.OPENAI, 0.10, 0.40)
    GPT_4_NANO = ("gpt-4-nano", Provider.OPENAI, 0.10, 0.40)
    GPT_O3 = ("gpt-o3", Provider.OPENAI, 2.00, 8.00)
    GPT_O4_MINI = ("gpt-o4-mini", Provider.OPENAI, 1.10, 4.40)
    GPT_5 = ("gpt-5", Provider.OPENAI, 2.50, 10.00)
    GPT_5_MINI = ("gpt-5-mini", Provider.OPENAI, 0.75, 3.00)
    GPT_5_NANO = ("gpt-5-nano", Provider.OPENAI, 0.20, 1.25)
    GPT_5_2 = ("gpt-5.2-2025-12-11", Provider.OPENAI, 1.75, 14.00)
    GPT_5_2_PRO = ("gpt-5.2-pro-2025-12-11", Provider.OPENAI, 21.00, 168.00)

   
    # Anthropic models
    CLAUDE_3_HAIKU = ("claude-3-haiku-20240307", Provider.ANTHROPIC, 0.25, 1.25)
    CLAUDE_3_SONNET = ("claude-3-sonnet-20240229", Provider.ANTHROPIC, 3.00, 15.00)
    CLAUDE_3_5_HAIKU = ("claude-3-5-haiku-20241022", Provider.ANTHROPIC, 0.80, 4.00)
    CLAUDE_3_7_SONNET = ("claude-3-7-sonnet-20250219", Provider.ANTHROPIC, 3.00, 15.00)
    CLAUDE_4_1_OPUS = ("claude-opus-4-1", Provider.ANTHROPIC, 15.00, 75.00)
    CLAUDE_4_5_OPUS = ("claude-opus-4-5-20251101", Provider.ANTHROPIC, 5.00, 25.00)
    CLAUDE_4_5_SONNET = ("claude-sonnet-4-5-20250929", Provider.ANTHROPIC, 3.00, 15.00)
    # cheapest among the newest claude models
    CLAUDE_4_5_HAIKU = ("claude-haiku-4-5-20251001", Provider.ANTHROPIC, 1.00, 5.00)
    
    # Google models
    GEMINI_1_5_FLASH = ("gemini-1.5-flash", Provider.GOOGLE, 0.075, 0.30)
    GEMINI_1_5_FLASH_8B = ("gemini-1.5-flash-8b", Provider.GOOGLE, 0.0375, 0.15)
    GEMINI_1_5_PRO = ("gemini-1.5-pro", Provider.GOOGLE, 1.25, 5.00)
    GEMINI_2_0_FLASH = ("gemini-2.0-flash", Provider.GOOGLE, 0.10, 0.40)
    GEMINI_2_0_FLASH_LITE = ("gemini-2.0-flash-lite", Provider.GOOGLE, 0.075, 0.30)
    GEMINI_2_5_FLASH = ("gemini-2.5-flash", Provider.GOOGLE, 0.30, 2.50)
    GEMINI_2_5_FLASH_LITE = ("gemini-2.5-flash-lite", Provider.GOOGLE, 0.075, 0.30)
    GEMINI_2_5_PRO = ("gemini-2.5-pro", Provider.GOOGLE, 1.25, 10.00)
    GEMINI_3_FLASH_PREVIEW = ("gemini-3-flash-preview", Provider.GOOGLE, 0.50, 3.00)
    GEMINI_3_PRO_PREVIEW = ("gemini-3-pro-preview", Provider.GOOGLE, 1.25, 10.00)
    
    # Local models (no cost)
    LLAMA3 = ("llama3", Provider.LOCAL, 0.0, 0.0)
    LLAMA3_1 = ("llama3.1", Provider.LOCAL, 0.0, 0.0)
    LLAMA3_8B = ("meta-llama/Meta-Llama-3-8B-Instruct", Provider.LOCAL, 0.0, 0.0)
    LLAMA3_2_1B = ("meta-llama/Llama-3.2-1B-Instruct", Provider.LOCAL, 0.0, 0.0)
    LLAMA3_2_3B = ("meta-llama/Llama-3.2-3B-Instruct", Provider.LOCAL, 0.0, 0.0)
    MISTRAL_7B = ("mistralai/Mistral-7B-Instruct-v0.2", Provider.LOCAL, 0.0, 0.0)
    PHI_3_MINI = ("microsoft/Phi-3-mini-4k-instruct", Provider.LOCAL, 0.0, 0.0)
    
    # NU Cluster models via vLLM (no cost)
    LLAMA3_1_8B_CLUSTER = ("meta-llama/Llama-3.1-8B-Instruct", Provider.NU_CLUSTER, 0.0, 0.0)
    LLAMA3_8B_CLUSTER = ("meta-llama/Meta-Llama-3-8B-Instruct", Provider.NU_CLUSTER, 0.0, 0.0)
    VICUNA_13B_CLUSTER = ("lmsys/vicuna-13b-v1.5", Provider.NU_CLUSTER, 0.0, 0.0)
    PIXTRAL_12B = ("mistralai/Pixtral-12B-2409", Provider.NU_CLUSTER, 0.0, 0.0)
    LLAVA_7B = ("llava-hf/llava-1.5-7b-hf", Provider.NU_CLUSTER, 0.0, 0.0)
    
    @property
    def model_id(self) -> str:
        """Get the model identifier string."""
        return self.value[0]
    
    @property
    def provider(self) -> Provider:
        """Get the provider for this model."""
        return self.value[1]
    
    @property
    def input_price(self) -> float:
        """Get cost per 1M input tokens (USD)."""
        return self.value[2]
    
    @property
    def output_price(self) -> float:
        """Get cost per 1M output tokens (USD)."""
        return self.value[3]
    
    @classmethod
    def from_string(cls, model_str: str) -> "LLMModel":
        """
        Get LLMModel enum from a string (model_id or enum name).
        
        Args:
            model_str: Model identifier string (e.g., "gpt-5-nano") or 
                      enum name (e.g., "GPT_5_NANO")
        
        Returns:
            Matching LLMModel enum
        
        Raises:
            ValueError: If no matching model found
        """
        # Try by model_id first
        for model in cls:
            if model.model_id == model_str:
                return model
        
        # Try by enum name (case insensitive)
        model_str_upper = model_str.upper().replace("-", "_").replace(".", "_")
        for model in cls:
            if model.name == model_str_upper:
                return model
        
        # List available models for error message
        available = [m.model_id for m in cls]
        raise ValueError(f"Unknown model: '{model_str}'. Available: {available[:10]}...")    
