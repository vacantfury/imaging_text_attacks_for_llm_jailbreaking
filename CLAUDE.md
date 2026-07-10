# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Visibility: private *(matches the oikos map entry `imaging_text_attacks`; revisit if code is open-sourced at publication)*

## Project

Research codebase for "Evaluating Defenses Against Text-Encoding Attacks on VLMs" (EMNLP/AIES 2026 target). The pipeline encodes harmful prompts into alternative representations (set theory, formal logic, classical Chinese, etc.), optionally renders them as images, applies black-box defenses (Image Rendering, SAGE, SemanticSmooth, hybrids), queries a target VLM, and ASR-judges the response.

See `README.md` for the research narrative and `text_docs/experiments_plan.md` / `text_docs/experiment_results.md` for the current experimental state — this is an active research repo whose direction shifts week to week, so consult those before assuming what's important.

## Common commands

```bash
pip install -e .                          # install (uses pyproject.toml)
python main.py test                       # smoke test (~$0.01)
python main.py experiment                 # main run — reads conf/experiment/experiment.yaml
python main.py <preset>                   # any conf/experiment/<preset>.yaml

# Cluster (NURC)
sbatch scripts/run_experiment.sbatch experiment       # auto-cleans old logs
sbatch scripts/run_experiment.sbatch test --keep

# Cleanup half-finished experiment dirs (outputs/ that lack results.json)
python scripts/cleanup_failed.py                      # dry-run
python scripts/cleanup_failed.py --delete
python scripts/cleanup_failed.py --recent 1h --delete

# Tracking
mlflow ui                                 # http://localhost:5000
```

There is no test framework — `python main.py test` runs the 4-task smoke preset end-to-end. API keys come from `.env` (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`).

## Architecture

### Pipeline modes (single dispatcher)

`src/experiment/task.py::run_task` dispatches by `mode`:

```
text_encode → [defense_transform] → [imaging] → evaluate
                                  └→ evaluate (text-only)
                  defense    (coupled defense + query + judge; e.g. SemanticSmooth)
```

Every mode writes to its own `outputs/<mode>/<benchmark>/<shortname>_<timestamp>_<rand>/` directory containing `results.json` (config + metrics + `upstream` link to source dir) and, where applicable, `prompts.jsonl` / `raw_results.jsonl` / `images/`. Downstream stages consume the previous stage's directory via `source_dir`. The 2×2 prompt grid (text/image × original/encoded) flows through `Prompt` records in `prompts.jsonl`; `evaluate` selects which combinations to query via `prompt_stages: [text_original|text_encoded|image_original|image_encoded]`.

### Orchestration

`src/experiment/experiment.py::Experiment` reads tasks from a single YAML preset and runs them concurrently. Two independent knobs:
- `num_main_job_threads` — `asyncio.Semaphore` controlling in-process task concurrency.
- `num_cluster_jobs` — SLURM job budget (orchestrator + vLLM servers), hard-capped at `MAX_SUBMIT_JOBS_PER_USER = 8`.

When any task targets a `Provider.NU_CLUSTER` model, `ClusterModelServerManager` submits vLLM servers as separate SLURM jobs, waits for one endpoint per model, and registers them with `LLMServiceFactory` so cluster-bound tasks auto-resolve endpoints. Servers are torn down in a `finally` block.

### 3-layer config merge

`src/experiment/config.py::load_conf` is used everywhere (text encoders, renderers, defenses, LLM defaults, evaluation):

```
conf/<subdir>/default.yaml  →  conf/<subdir>/<override_name>.yaml  →  task_overrides (from preset)
```

For `llm/` and `evaluation/` the merge is type-checked via OmegaConf structured schemas (`ModelConfig`, `ClusterConfig`, `JudgeLLMConfig`, `EvaluationConf`) — adding a YAML field requires adding it to the corresponding dataclass.

### Factories

Each subsystem follows the same pattern — enum/string → factory → concrete class:
- `src/text_encoding/encoder_factory.py` (`create_encoder` + `resolve_encoding_name`) — LLM-based (`llm_set_theory`, `llm_formal_logic`, `llm_classical_language`, `llm_quantum_mechanics`, `llm_semantic_camo`) and rule-based (`non_llm_baseline`, `non_llm_addition_equation_split_reassemble`, `non_llm_conditional_probability`, `non_llm_symbol_injection`).
- `src/imaging/image_renderer_factory.py` — `plain`, `fc_typography`, `fc_flowchart`, `figstep`.
- `src/defense/defender_factory.py` — `sage` (transform-only, valid for `defense_transform` mode) vs `semantic_smooth` (coupled, requires `defense` mode + a `perturbation_model`). The `is_transform_only` flag on the defender gates which mode accepts it.
- `src/evaluation/evaluator_factory.py` — judge methods `harmbench`, `jailbreakbench`, `refusal`, `orbench`. `judge_method` determines whether `evaluate` reports `attack_success_rate` or `refusal_rate`.
- `src/llm_utils/llm_service_factory.py` — routes by `LLMModel.provider`:
  - `Provider.OPENAI` → `AsyncOpenAI` + `asyncio.gather`
  - `Provider.ANTHROPIC` → native Message Batches API (50% cheaper)
  - `Provider.GOOGLE` → native Batch API inline (50% cheaper)
  - `Provider.NU_CLUSTER` → `AsyncOpenAI` pointed at the vLLM endpoint registered by `ClusterModelServerManager` (supports image inputs as base64 `image_url`)

Unified call shape across providers: `service.batch_chat(conversations, system_message, is_test)`, where `conversations` is `[(conv_id, [(text, image_or_None), ...]), ...]`. Model registry + pricing lives in `src/llm_utils/llm_model.py::LLMModel`; resolve a string with `LLMModel.from_string(...)`.

### Pydantic schemas

`src/experiment/schemas.py` is the contract between stages — `RawPrompt`, `Prompt`, `EvaluationRow`, and the per-mode result models (`TextEncodeResult`, `ImagingResult`, `EvaluateResult`, `DefenseTransformResult`, `DefenseResult`). Each result embeds `upstream` (the previous stage's `results.json`), so a single `results.json` chain reconstructs the full provenance of any data point.

### Tracking

Every task is an MLflow run (`src/utils/mlflow_tracker.py`). The run_id is written back into the task's `results.json`, and `results.json` / `prompts.jsonl` / `raw_results.jsonl` are logged as artifacts. MLflow data lives in `mlruns/` (gitignored).

### Image quality gate

`_verify_image_quality` in `task.py` samples rendered PNGs and fails the imaging stage if non-white pixel ratio drops below `fail_threshold` (default 1%) — catches missing-glyph/tofu bugs from absent CJK fonts. `fonts/` is gitignored; rendering CJK/Devanagari requires the Noto fonts to be present locally.

## Conventions

- `prompt_range: [start, end]` is **inclusive on both ends**, 0-indexed, applied to the prompt list after loading.
- Benchmark is auto-inferred from path components (`harmbench`, `jailbreakbench`, `orbench_*`) via `_infer_benchmark`; override with `benchmark:` in the task.
- Cluster outputs are not in the repo — outputs live under `outputs/` (gitignored) and large dataset files under `data/original_datasets/` / `data/processed_datasets/` are also gitignored.
- Commit-message style is short snake-case phrases (e.g. `add_qwen_model`, `new_big_refactor`); follow that, not Conventional Commits.
- Python ≥ 3.12. Long-running model selection assumes the current model registry in `llm_model.py` — note that Claude Sonnet 4 / 4.5 are deprecated or sunsetting (see `TODO.md`).
- Always check and estimate experiment cost when designing experiments — API spend is a first-class design constraint (standing rule; moved here from the old TODO 2026-07-09 because rules that never complete are not tasks).
