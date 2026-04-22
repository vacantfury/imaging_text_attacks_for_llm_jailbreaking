"""
Pydantic schemas for inter-stage data contracts.

Pipeline stages:
  text_encode → imaging → evaluate

Write: model.model_dump_json() → JSONL line
Read: ModelClass.model_validate_json(line) → validated object
"""
from typing import Optional
from pydantic import BaseModel


class RawPrompt(BaseModel):
    """Source prompt from harmful/benign datasets."""
    id: str
    category: str
    source: str           # "advbench" | "harmbench" | "jailbreakbench"
    prompt: str


class EncodedPrompt(BaseModel):
    """Prompt after text encoding stage.
    
    The imaging stage copies this and adds image_path.
    """
    id: str
    encoding: str         # "plain" | "math" | "formal_logic" | ...
    original: str         # original harmful prompt (always preserved)
    encoded: str          # text-encoded version
    image_path: Optional[str] = None  # relative path to PNG, added by imaging stage


class EvaluationResult(BaseModel):
    """One evaluation row: one prompt × one prompt_stage × one model."""
    id: str
    model: str
    encoding: str
    prompt_stage: str     # "original" | "text_encoded" | "imaging"
    prompt_sent: str      # what was actually sent to the model (text or image instruction)
    response: str         # model response
    original_prompt: str  # original harmful prompt (for ASR judging)
    timestamp: str


# Legacy schemas kept for backward compatibility
class ImagePrompt(BaseModel):
    """Reference to a rendered image prompt (legacy)."""
    id: str
    encoding: str
    image_path: str


class ModelResponse(BaseModel):
    """Raw response from target model (legacy)."""
    id: str
    model: str
    encoding: str
    modality: str         # "text" | "image"
    response: str
    timestamp: str


class Judgment(BaseModel):
    """ASR judgment for a single response."""
    id: str
    model: str
    encoding: str
    prompt_stage: str
    gpt4o_judge: Optional[bool] = None
    llamaguard_judge: Optional[bool] = None
    asr: Optional[bool] = None
