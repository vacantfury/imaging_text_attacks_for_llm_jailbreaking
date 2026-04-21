"""
Pydantic schemas for inter-stage data contracts.

Both task.py (writer) and data_loader (reader) import from here —
single source of truth for data formats.

Write: model.model_dump_json() → JSONL line
Read: ModelClass.model_validate_json(line) → validated object
"""
from pydantic import BaseModel


class RawPrompt(BaseModel):
    """Source prompt from harmful/benign datasets."""
    id: str
    category: str
    source: str           # "advbench" | "harmbench" | "jailbreakbench"
    prompt: str


class EncodedPrompt(BaseModel):
    """Prompt after text encoding stage."""
    id: str
    encoding: str         # "plain" | "classical_chinese" | "math" | "formal_logic"
    original: str
    encoded: str


class ImagePrompt(BaseModel):
    """Reference to a rendered image prompt."""
    id: str
    encoding: str
    image_path: str       # relative path to PNG within output dir


class ModelResponse(BaseModel):
    """Raw response from target model."""
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
    modality: str
    gpt4o_judge: bool
    llamaguard_judge: bool
    asr: bool             # final ASR decision
