"""
LLM model registry — every static fact about a model lives here.

The shape: each LLMModel enum value is a frozen `ModelSpec` dataclass.

  LLMModel.GPT_5.value
      → ModelSpec(model_id="gpt-5", provider=OPENAI, input_price=2.5,
                  output_price=10.0, max_context_len=None,
                  quirks={USES_MAX_COMPLETION_TOKENS, NO_CUSTOM_TEMPERATURE})

What lives here (static, code-time facts about the model):
  - model_id, provider, pricing
  - max_context_len: architectural ceiling from upstream config.json (e.g.,
    Llama-2's max_position_embeddings=2048). Used by LLMConfig validator
    to reject `cluster.max_model_len` overruns before vLLM rejects them.
  - quirks: API-side behavior flags (e.g., GPT-5 only accepts temperature=1).

What does NOT live here (deployment choices, not model facts):
  - num_gpus, mem_gb, dtype, the actually-served max_model_len, chat_template,
    gpu_types_excluded — all in conf/llm/<model>.yaml.

Adding a new model: append one `LLMModel.<NAME> = ModelSpec(...)` row.
Adding a new per-model fact: add a field to `ModelSpec`, populate selected
rows. No new scattered dicts.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Provider(str, Enum):
    """LLM service provider — drives factory dispatch."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"
    NU_CLUSTER = "nu_cluster"


class ModelQuirk(str, Enum):
    """API-side behavior flags. A model carries a frozenset of these.

    Each quirk is observable in code via `model.has_quirk(...)`. Adding a
    new quirk is just: define the enum value, mark the relevant rows on
    LLMModel. No new sets-by-model scattered through constants.py.
    """
    # OpenAI newer models renamed `max_tokens` → `max_completion_tokens`
    USES_MAX_COMPLETION_TOKENS = "uses_max_completion_tokens"
    # OpenAI reasoning models reject any temperature != 1.0
    NO_CUSTOM_TEMPERATURE = "no_custom_temperature"


@dataclass(frozen=True)
class ModelSpec:
    """Static facts about a model. Frozen so each enum value is hashable."""
    model_id: str
    provider: Provider
    input_price: float = 0.0          # $/1M input tokens (0 for self-hosted)
    output_price: float = 0.0         # $/1M output tokens
    max_context_len: Optional[int] = None   # arch ceiling; None when unknown
    quirks: frozenset = field(default_factory=frozenset)
    # Chat template name → src/llm_utils/chat_templates/<name>.jinja, passed to
    # vLLM as --chat-template. None means "use the tokenizer's baked-in template"
    # (correct for modern chat-tuned checkpoints; their tokenizer.json ships one).
    # Set explicitly for: (a) classifiers / non-chat fine-tunes whose training
    # prompts are pre-formatted (HarmBench-Llama-2-13b-cls → "passthrough"),
    # (b) legacy chat models whose tokenizer doesn't ship a template.
    chat_template: Optional[str] = None


# ────────────────────────────────────────────────────────────────────
# Quirk presets (used heavily by GPT-5 / O-series rows below)
# ────────────────────────────────────────────────────────────────────
_GPT5_QUIRKS = frozenset({
    ModelQuirk.USES_MAX_COMPLETION_TOKENS,
    ModelQuirk.NO_CUSTOM_TEMPERATURE,
})
_GPT41_QUIRKS = frozenset({
    ModelQuirk.USES_MAX_COMPLETION_TOKENS,
})


class LLMModel(Enum):
    """Per-model static registry. Each value is a frozen ModelSpec."""

    # ──────── OpenAI ────────
    GPT_3_5_TURBO = ModelSpec("gpt-3.5-turbo",  Provider.OPENAI, 0.50,  1.50)
    GPT_4         = ModelSpec("gpt-4",          Provider.OPENAI, 30.00, 60.00)
    GPT_4_TURBO   = ModelSpec("gpt-4-turbo",    Provider.OPENAI, 10.00, 30.00)
    GPT_4O        = ModelSpec("gpt-4o",         Provider.OPENAI, 2.50,  10.00)
    GPT_4O_MINI   = ModelSpec("gpt-4o-mini",    Provider.OPENAI, 0.15,  0.60)

    # GPT-4.1 series — `max_completion_tokens` rename starts here
    GPT_4_1       = ModelSpec("gpt-4.1",        Provider.OPENAI, 2.00,  8.00,  quirks=_GPT41_QUIRKS)
    GPT_4_1_MINI  = ModelSpec("gpt-4.1-mini",   Provider.OPENAI, 0.40,  1.60,  quirks=_GPT41_QUIRKS)
    GPT_4_1_NANO  = ModelSpec("gpt-4.1-nano",   Provider.OPENAI, 0.10,  0.40,  quirks=_GPT41_QUIRKS)

    # GPT-5 series — also drops custom temperature
    GPT_5         = ModelSpec("gpt-5",          Provider.OPENAI, 2.50,  10.00, quirks=_GPT5_QUIRKS)
    GPT_5_MINI    = ModelSpec("gpt-5-mini",     Provider.OPENAI, 0.25,  2.00,  quirks=_GPT5_QUIRKS)
    GPT_5_NANO    = ModelSpec("gpt-5-nano",     Provider.OPENAI, 0.20,  1.25,  quirks=_GPT5_QUIRKS)
    GPT_5_PRO     = ModelSpec("gpt-5-pro",      Provider.OPENAI, 15.00, 120.00, quirks=_GPT5_QUIRKS)
    GPT_5_1       = ModelSpec("gpt-5.1",        Provider.OPENAI, 1.25,  10.00, quirks=_GPT5_QUIRKS)
    GPT_5_2       = ModelSpec("gpt-5.2",        Provider.OPENAI, 1.75,  14.00, quirks=_GPT5_QUIRKS)
    GPT_5_2_PRO   = ModelSpec("gpt-5.2-pro",    Provider.OPENAI, 21.00, 168.00, quirks=_GPT5_QUIRKS)
    GPT_5_4       = ModelSpec("gpt-5.4",        Provider.OPENAI, 2.50,  15.00, quirks=_GPT5_QUIRKS)
    GPT_5_4_MINI  = ModelSpec("gpt-5.4-mini",   Provider.OPENAI, 0.75,  4.50,  quirks=_GPT5_QUIRKS)
    GPT_5_4_NANO  = ModelSpec("gpt-5.4-nano",   Provider.OPENAI, 0.20,  1.25,  quirks=_GPT5_QUIRKS)
    GPT_5_4_PRO   = ModelSpec("gpt-5.4-pro",    Provider.OPENAI, 30.00, 180.00, quirks=_GPT5_QUIRKS)
    GPT_5_5       = ModelSpec("gpt-5.5",        Provider.OPENAI, 5.00,  30.00, quirks=_GPT5_QUIRKS)
    GPT_5_5_PRO   = ModelSpec("gpt-5.5-pro",    Provider.OPENAI, 30.00, 180.00, quirks=_GPT5_QUIRKS)

    # O-series reasoning models — same shape as GPT-5
    O1            = ModelSpec("o1",             Provider.OPENAI, 15.00, 60.00, quirks=_GPT5_QUIRKS)
    O3            = ModelSpec("o3",             Provider.OPENAI, 2.00,  8.00,  quirks=_GPT5_QUIRKS)
    O3_MINI       = ModelSpec("o3-mini",        Provider.OPENAI, 1.10,  4.40,  quirks=_GPT5_QUIRKS)
    O4_MINI       = ModelSpec("o4-mini",        Provider.OPENAI, 1.10,  4.40,  quirks=_GPT5_QUIRKS)

    # ──────── Anthropic ────────
    # Sonnet
    CLAUDE_SONNET_4   = ModelSpec("claude-sonnet-4-20250514",   Provider.ANTHROPIC, 3.00, 15.00)
    CLAUDE_SONNET_4_5 = ModelSpec("claude-sonnet-4-5-20250929", Provider.ANTHROPIC, 3.00, 15.00)
    CLAUDE_SONNET_4_6 = ModelSpec("claude-sonnet-4-6",          Provider.ANTHROPIC, 3.00, 15.00)
    # Opus
    CLAUDE_OPUS_4   = ModelSpec("claude-opus-4-20250514",   Provider.ANTHROPIC, 15.00, 75.00)
    CLAUDE_OPUS_4_1 = ModelSpec("claude-opus-4-1-20250805", Provider.ANTHROPIC, 15.00, 75.00)
    CLAUDE_OPUS_4_5 = ModelSpec("claude-opus-4-5-20251101", Provider.ANTHROPIC, 5.00,  25.00)
    CLAUDE_OPUS_4_6 = ModelSpec("claude-opus-4-6",          Provider.ANTHROPIC, 5.00,  25.00)
    CLAUDE_OPUS_4_7 = ModelSpec("claude-opus-4-7",          Provider.ANTHROPIC, 5.00,  25.00)
    # Haiku
    CLAUDE_HAIKU_4_5 = ModelSpec("claude-haiku-4-5-20251001", Provider.ANTHROPIC, 1.00, 5.00)

    # ──────── Google ────────
    GEMINI_2_0_FLASH               = ModelSpec("gemini-2.0-flash",                Provider.GOOGLE, 0.10,  0.40)
    GEMINI_2_0_FLASH_LITE          = ModelSpec("gemini-2.0-flash-lite",           Provider.GOOGLE, 0.075, 0.30)
    GEMINI_2_5_FLASH               = ModelSpec("gemini-2.5-flash",                Provider.GOOGLE, 0.30,  2.50)
    GEMINI_2_5_FLASH_LITE          = ModelSpec("gemini-2.5-flash-lite",           Provider.GOOGLE, 0.075, 0.30)
    GEMINI_2_5_PRO                 = ModelSpec("gemini-2.5-pro",                  Provider.GOOGLE, 1.25,  10.00)
    GEMINI_3_FLASH_PREVIEW         = ModelSpec("gemini-3-flash-preview",          Provider.GOOGLE, 0.50,  3.00)
    GEMINI_3_PRO_PREVIEW           = ModelSpec("gemini-3-pro-preview",            Provider.GOOGLE, 1.25,  10.00)
    GEMINI_3_1_PRO_PREVIEW         = ModelSpec("gemini-3.1-pro-preview",          Provider.GOOGLE, 2.00,  12.00)
    GEMINI_3_1_FLASH_LITE_PREVIEW  = ModelSpec("gemini-3.1-flash-lite-preview",   Provider.GOOGLE, 0.075, 0.30)

    # ──────── Local (HF transformers in-process) ────────
    LLAMA3       = ModelSpec("llama3",                                   Provider.LOCAL)
    LLAMA3_1     = ModelSpec("llama3.1",                                 Provider.LOCAL)
    LLAMA3_8B    = ModelSpec("meta-llama/Meta-Llama-3-8B-Instruct",      Provider.LOCAL)
    LLAMA3_2_1B  = ModelSpec("meta-llama/Llama-3.2-1B-Instruct",         Provider.LOCAL)
    LLAMA3_2_3B  = ModelSpec("meta-llama/Llama-3.2-3B-Instruct",         Provider.LOCAL)
    MISTRAL_7B   = ModelSpec("mistralai/Mistral-7B-Instruct-v0.2",       Provider.LOCAL)
    PHI_3_MINI   = ModelSpec("microsoft/Phi-3-mini-4k-instruct",         Provider.LOCAL)

    # ──────── NU Cluster (vLLM-served) — max_context_len populated ────────
    LLAMA3_1_8B_CLUSTER = ModelSpec(
        "meta-llama/Llama-3.1-8B-Instruct", Provider.NU_CLUSTER,
        max_context_len=131_072)               # Llama-3.1 long-context
    LLAMA3_8B_CLUSTER = ModelSpec(
        "meta-llama/Meta-Llama-3-8B-Instruct", Provider.NU_CLUSTER,
        max_context_len=8_192)                 # Llama-3 (8K)
    VICUNA_13B_CLUSTER = ModelSpec(
        "lmsys/vicuna-13b-v1.5", Provider.NU_CLUSTER,
        max_context_len=4_096)                 # Vicuna v1.5 (4K)
    PIXTRAL_12B  = ModelSpec("mistralai/Pixtral-12B-2409",      Provider.NU_CLUSTER)
    LLAVA_7B     = ModelSpec("llava-hf/llava-1.5-7b-hf",        Provider.NU_CLUSTER)
    QWEN2_5_VL_7B = ModelSpec("Qwen/Qwen2.5-VL-7B-Instruct",    Provider.NU_CLUSTER)

    # Judge models for canonical benchmark evaluators
    HARMBENCH_LLAMA_2_13B_CLS = ModelSpec(
        "cais/HarmBench-Llama-2-13b-cls", Provider.NU_CLUSTER,
        max_context_len=2_048,                 # Llama-2 architecture (HARD)
        # Fine-tuned classifier — training prompts are pre-wrapped in
        # Llama-2's [INST] <<SYS>>...[/INST] syntax verbatim. Llama-2's
        # tokenizer doesn't ship a chat template, so we emit content as-is.
        chat_template="passthrough")
    LLAMA_3_3_70B_INSTRUCT = ModelSpec(
        "meta-llama/Llama-3.3-70B-Instruct", Provider.NU_CLUSTER,
        max_context_len=131_072)               # Llama-3.3 long-context

    # ──────── Accessors ────────────────────────────────────────────────
    # Same API surface as before: model.model_id, model.provider, etc.
    # Just reading from the dataclass instead of a positional tuple.

    @property
    def model_id(self) -> str:
        return self.value.model_id

    @property
    def provider(self) -> Provider:
        return self.value.provider

    @property
    def input_price(self) -> float:
        return self.value.input_price

    @property
    def output_price(self) -> float:
        return self.value.output_price

    @property
    def max_context_len(self) -> Optional[int]:
        """Architectural max context (from upstream config.json), None if unknown.

        Used by `LLMConfig` validator to reject `cluster.max_model_len`
        values that would cause vLLM to refuse at server startup (e.g.,
        Llama-2's RoPE positional encoding is undefined beyond 2048).
        """
        return self.value.max_context_len

    @property
    def chat_template(self) -> Optional[str]:
        """Chat-template name → src/llm_utils/chat_templates/<name>.jinja.

        None means "use the tokenizer's baked-in chat template" (vLLM
        derives it automatically — correct for modern chat-tuned models).
        Set explicitly for classifiers and legacy models whose tokenizer
        doesn't ship a template. YAML can override per-deployment via
        `cluster.chat_template` but the source of truth is this field.
        """
        return self.value.chat_template

    def has_quirk(self, q: ModelQuirk) -> bool:
        """Whether this model has an API-side behavior quirk."""
        return q in self.value.quirks

    @classmethod
    def from_string(cls, model_str: str) -> "LLMModel":
        """Resolve a string (model_id or enum name) to LLMModel.

        Tries model_id first, then enum-name (case-insensitive, normalizing
        '-' and '.' to '_'). Raises ValueError with a sample of available
        models on no match.
        """
        # Try by model_id first
        for model in cls:
            if model.model_id == model_str:
                return model

        # Try by enum name (case insensitive, '-'/'.' → '_')
        model_str_upper = model_str.upper().replace("-", "_").replace(".", "_")
        for model in cls:
            if model.name == model_str_upper:
                return model

        available = [m.model_id for m in cls]
        raise ValueError(
            f"Unknown model: '{model_str}'. "
            f"Available: {available[:10]}... ({len(available)} total)")
