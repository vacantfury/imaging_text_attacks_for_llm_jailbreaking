"""
Pydantic schemas for inter-stage data contracts.

Pipeline: text_encode → imaging → evaluate

2×2 condition grid:
              Text modality    Image modality
  Original    text_original    image_original
  Encoded     text_encoded     image_encoded
"""
from typing import Optional
from pydantic import BaseModel


class RawPrompt(BaseModel):
    """Source prompt from harmful/benign datasets."""
    id: str
    category: str
    source: str           # "advbench" | "harmbench" | "jailbreakbench"
    prompt: str


class Prompt(BaseModel):
    """Unified prompt record used across text_encode and imaging stages.
    
    text_encode creates rows with {id, encoding, original, encoded}.
    imaging copies and adds image_original / image_encoded paths.
    """
    id: str
    encoding: str
    original: str         # original harmful prompt (always preserved)
    encoded: str          # text-encoded version
    image_original: Optional[str] = None   # path to image of original text
    image_encoded: Optional[str] = None    # path to image of encoded text


class EvaluationRow(BaseModel):
    """One row in raw_results.jsonl (long format).
    
    One row per (prompt × prompt_stage).
    """
    id: str
    prompt_stage: str     # text_original | text_encoded | image_original | image_encoded
    response: str         # model response
    asr: Optional[bool] = None  # ASR judgment (null if judging not yet run)
    judge_output: Optional[str] = None
    judge_reasoning: Optional[str] = None
    judge_raw_response: Optional[str] = None


class Judgment(BaseModel):
    """ASR judgment for a single response (used by evaluation/)."""
    id: str
    model: str
    encoding: str
    prompt_stage: str
    judge_output: str     # "yes" | "no"
    judge_reasoning: Optional[str] = None
    is_jailbroken: bool


# ====================================================================
# Task result models — fully resolved config + metrics for results.json
# ====================================================================


class TextEncodeResult(BaseModel):
    """Complete record of a text_encode task run."""
    mode: str = "text_encode"
    encoding: str
    encoder_type: str
    encoder_config: dict
    benchmark: str
    source_file: str
    prompt_range: Optional[list[int]] = None
    count: int
    elapsed_seconds: float
    output_dir: str
    usage: Optional[dict] = None


class ImagingResult(BaseModel):
    """Complete record of an imaging task run."""
    mode: str = "imaging"
    encoding: str
    renderer_type: str
    renderer_config: dict
    render: list[str]
    source_dir: str
    prompt_range: Optional[list[int]] = None
    count: int
    image_count: int
    elapsed_seconds: float
    output_dir: str
    upstream: Optional[dict] = None


class TargetModelConfig(BaseModel):
    """Resolved LLM inference parameters for the target model."""
    max_tokens: int
    temperature: float
    top_p: float
    top_k: int
    frequency_penalty: float
    presence_penalty: float
    stop_sequences: list[str]
    seed: int
    n_completions: int
    stream: bool


class EvaluateResult(BaseModel):
    """Complete record of an evaluate task run — written to results.json.

    Contains all resolved parameters (from task YAML, evaluation defaults,
    and LLM defaults) so the result is fully self-contained and reproducible.
    """
    mode: str = "evaluate"
    target_model: str
    target_model_config: TargetModelConfig
    encoding: str
    benchmark: str
    prompt_stages: list[str]
    prompt_range: Optional[list[int]] = None
    source_dir: str
    system_message: Optional[str] = None
    image_instruction: str
    judge_method: str
    count: int
    count_per_stage: dict[str, int]
    asr: Optional[dict[str, float]] = None
    refusal_rate: Optional[dict[str, float]] = None
    usage: dict
    elapsed_seconds: float
    output_dir: str
    upstream: Optional[dict] = None


class DefenseTransformResult(BaseModel):
    """Result of a transform-only defense (e.g., SAGE wrapping).

    Output: prompts.jsonl in the same format as text_encode, where
    'encoded' contains the defense-wrapped text. Can be piped into
    imaging or evaluate stages directly.
    """
    mode: str = "defense_transform"
    defense_method: str
    defense_config: Optional[dict] = None
    encoding: str
    benchmark: str
    prompt_range: Optional[list[int]] = None
    source_dir: str
    count: int
    elapsed_seconds: float
    output_dir: str
    upstream: Optional[dict] = None


class DefenseResult(BaseModel):
    """Complete record of a defense task run — written to results.json."""
    mode: str = "defense"
    defense_method: str
    defense_config: Optional[dict] = None
    target_model: str
    encoding: str
    benchmark: str
    prompt_range: Optional[list[int]] = None
    source_dir: str
    system_message: Optional[str] = None
    judge_method: str
    count: int
    asr: Optional[float] = None
    refusal_rate: Optional[float] = None
    usage: Optional[dict] = None
    defense_usage: Optional[dict] = None
    elapsed_seconds: float
    output_dir: str
    upstream: Optional[dict] = None
