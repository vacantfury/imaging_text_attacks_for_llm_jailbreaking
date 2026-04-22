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


class Judgment(BaseModel):
    """ASR judgment for a single response (used by evaluation/)."""
    id: str
    model: str
    encoding: str
    prompt_stage: str
    judge_output: str     # "yes" | "no"
    judge_reasoning: Optional[str] = None
    is_jailbroken: bool


# Legacy schemas kept for backward compatibility
class EncodedPrompt(BaseModel):
    """Legacy: prompt after text encoding stage."""
    id: str
    encoding: str
    original: str
    encoded: str
    image_path: Optional[str] = None


class ImagePrompt(BaseModel):
    """Legacy: reference to a rendered image prompt."""
    id: str
    encoding: str
    image_path: str


class ModelResponse(BaseModel):
    """Legacy: raw response from target model."""
    id: str
    model: str
    encoding: str
    modality: str
    response: str
    timestamp: str
