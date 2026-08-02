# Code Refinement Plan

> Scope: Fix structural bugs, improve code quality across src/.
> Excluded: Model call retry/rate-limit logic, SLURM/cluster changes (not vital).

---

## Phase 1 — Broken Imports & Exports (P1)

- [x] 1.1 `src/text_encoding/__init__.py`: Added `QuantumMechanicsLLMEncoder` import
- [x] 1.2 `src/text_encoding/encoder_config.py`: Replaced broken `llm_config` import with inline `LLMModelConfig` dataclass
- [x] 1.3 `src/evaluation/harmbench_evaluation/__init__.py`: Created
- [x] 1.4 `src/llm_utils/constants.py`: Added `GPT_4_NANO`, `GPT_5_2`, `GPT_5_2_PRO` to `MODELS_USING_MAX_COMPLETION_TOKENS`

## Phase 2 — Resource & Error Handling (P2)

- [x] 2.1 `src/experiment/task.py`: Fixed `json.load(open(...))` → `with open(...)`
- [x] 2.2 `src/experiment/task.py`: Narrowed `except`, added `exc_info=True`, `.copy()` before `.pop()`
- [x] 2.3 `src/llm_utils/llm_services/claude_service.py`: Added `_extract_text()` helper for safe response parsing
- [x] 2.4 `src/llm_utils/llm_services/google_service.py`: Fixed ImportError to say `pip install google-genai`

## Phase 3 — Code Duplication (P3)

- [x] 3.1 Created `src/llm_utils/media_utils.py` with shared `encode_image_to_b64()`, wired into both services
- [x] 3.2 `src/experiment/task.py`: Extracted `_load_and_slice_prompts()`, used in imaging+evaluate
- [x] 3.3 Removed redundant local import in `_load_prompts`
- [x] 3.4 Removed duplicate `from omegaconf import OmegaConf` in `cluster_server_manager.py`

## Phase 4 — Type Safety (P4)

- [x] 4.1 `src/experiment/config.py`: Consolidated `MISSING`/`OmegaConf`/`DictConfig` import, added `Optional` + `Any` to `load_conf`
- [x] 4.2 `src/experiment/experiment.py`: Renamed `TaskInfo.type` → `task_type`, added `Optional` and return types
- [x] 4.3 `src/experiment/task.py`: Added `list[Prompt]`, `dict[str, Any]` return annotations
- [x] 4.4 `src/utils/logger.py`: Added `str`, `int`, `-> logging.Logger` annotations
- [x] 4.5 `src/utils/experiment.py`: Added `Optional[str]` for `dataset`/`model` params

## Phase 5 — Architecture Cleanup (P5)

- [x] 5.1 `src/experiment/task.py`: Extracted `_build_conversations_for_stage()` and `_run_asr_judging()`
- [x] 5.2 `src/experiment/experiment.py`: Updated module docstring to reflect single-semaphore design
- [x] 5.3 `src/experiment/schemas.py`: Removed unused `EncodedPrompt`, `ImagePrompt`, `ModelResponse`
- [x] 5.4 `src/text_encoding/README.md`: Rewrote to match current encoder architecture

## Phase 6 — Minor Cleanup (P6)

- [x] 6.1 Removed unused `Optional` from `base_image_renderer.py`; removed `os`, `Optional` from `fc_flowchart_image_renderer.py`
- [x] 6.2 `src/utils/logger.py`: Renamed `DEFAULT_LOGGER_NAME` to `"llm_guardrail_security"`
- [x] 6.3 `src/experiment/config.py`: Documented `_strip_hydra` mutation is safe (fresh objects)

---

## Summary of Changes

Files modified: 16
Files created: 2 (`src/llm_utils/media_utils.py`, `src/evaluation/harmbench_evaluation/__init__.py`)

All phases complete. No linter errors introduced.
