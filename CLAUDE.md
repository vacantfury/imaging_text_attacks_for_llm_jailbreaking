# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Visibility: public *(deliberately public from the start — owner policy 2026-07-09: science projects are public from birth, and the repo doubles as résumé/portfolio evidence. Consequence: public-grade discipline is MANDATORY — never commit personal data, ARR/reviewer text (`text_docs/reviews/` is gitignored), task files, secrets, or 1Password references.)*

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

`src/experiment/task.py::run_task` dispatches by `task.mode` (a discriminated Pydantic union — `PromptTransformTask` / `DefenseEvaluateTask` / `AnalyzeTask` in `schemas.py`):

- `prompt_transform` — runs a chain of `PromptTransformation` steps (text encoders + image renderers, in order); writes one subfolder per step under `outputs/prompt_transform/...`, each with a cumulative `results.json`. Input is a raw dataset JSONL (`source_file`) or a prior step (`source_transform_subdir`, for chaining and for sharing one encoding across ablations).
- `defense+evaluate` — defense + target-model query + judging, **fused into one mode** (there is no separate transform-only vs. coupled split anymore). Consumes a `prompt_transform` subfolder and writes to `outputs/defense+evaluate/<benchmark>/<target>_<defense>_<chain>_<ts>_<rand>/`.
- `analyze` — pure post-processing, no model/judge I/O; fans **in** from many `defense+evaluate` dirs (e.g. portfolio / best-of-all ASR, `complementarity_gap`) via `src/analysis`.

Each `results.json` carries an `upstream_ref: {source_dir, results_sha256}` pointer (drift-detecting hash; a legacy `upstream` dict is read for back-compat only), so the chain reconstructs full provenance. Where applicable a step also writes `prompts.jsonl` / `raw_results.jsonl` / `images/`.

### Orchestration

`src/experiment/experiment.py::Experiment` reads tasks from a single YAML preset and runs them concurrently. Two independent knobs:
- `num_main_job_threads` — `asyncio.Semaphore` controlling in-process task concurrency.
- `num_cluster_jobs` — SLURM job budget (orchestrator + vLLM servers), hard-capped at `MAX_SUBMIT_JOBS_PER_USER = 8`.

When any task targets a `Provider.NU_CLUSTER` model, `ClusterModelServerManager` submits vLLM servers as separate SLURM jobs, waits for one endpoint per model, and registers them with `LLMServiceFactory` so cluster-bound tasks auto-resolve endpoints. Servers are torn down in a `finally` block.

### 3-layer config merge

`src/experiment/config.py::load_conf` is used everywhere (text encoders under `conf/text_encoding/`, renderers under `conf/imaging/`, defenses, LLM defaults, evaluation):

```
conf/<subdir>/default.yaml  →  conf/<subdir>/<override_name>.yaml  →  task_overrides (from preset)
```

`load_conf` returns a merged plain dict via `_deep_merge` (a hand-rolled `OmegaConf.merge` replacement — OmegaConf is no longer a dependency). Validation is plain Pydantic at the call site: `llm/` merges into `ModelConfig`/`ClusterConfig`/`LLMConfig`, `evaluation/` into `JudgeLLMConfig`/`EvaluationConfig` (all in `schemas.py`) — adding a YAML field means adding it to the corresponding Pydantic model. The `conf/text_encoding/` and `conf/imaging/` dirs still exist even though the *code* factory is unified — `_resolve_step_config` picks the subdir by whether a step is image-producing.

### Factories

Each subsystem follows the same pattern — a `@register_*` class-decorator populates a name→class registry; a factory resolves a string (with alias fallback) to a concrete class:
- `src/prompt_transformations/transformation_factory.py` (`@register_transformation`) — **one unified registry** for both text encoders and image renderers (the old `text_encoding` + `imaging` factories were merged; `text/` vs `image/` is now just directory organization). Resolution order: direct `type_name` → `TRANSFORMATION_ALIASES` → classical-language auto-resolve. Text `type_name`s: `non_llm_baseline`, `non_llm_artprompt`, `non_llm_homoglyph`, `non_llm_addition_equation_split_reassemble`, `non_llm_conditional_probability`, `non_llm_symbol_injection`, `llm_set_theory`, `llm_formal_logic`, `llm_quantum_mechanics`, `llm_classical_language`, `llm_semantic_camo`, `deep_inception`, `ecso_evade`, `code_attack`. Image `type_name`s: `ir_plain`, `ir_fc_typo`, `ir_figstep`, `ir_fc_flowchart`, `ir_blank`, `ir_constant`, `cross_modal_split`. Common aliases: `plain`→`non_llm_baseline` (the *text* baseline — for the plain image renderer use `ir_plain` literally), `set_theory`, `formal_logic`, `quantum`, `semantic_camo`, …; `homoglyph`/`artprompt` have no alias (use `non_llm_homoglyph`/`non_llm_artprompt`).
- `src/defense/defender_factory.py` (`@register_defense`) — `no_defense`, `sage`, `semantic_smooth`, `ecso`, `modality_complete`, `joint_verify`, `amia_ia`. Every `Defense` implements one interface, `query(prompts, target_service, is_multimodal, source_dir, system_message)`, and OWNS the target-model interaction (wrap input, query once, or query→inspect→re-query). There is no `is_transform_only` flag — the old transform-only/coupled split is gone (`defense+evaluate` is the only mode a defense runs under).
- `src/evaluation/evaluator_factory.py` — `EvaluatorFactory.create_from_benchmark(benchmark)` is the preferred entry (`harmbench`→HarmBench; `jailbreakbench`→dual JBB harm+refusal judges; `jailbreakbench_benign`→refusal only; `orbench*`→ORBench); explicit `create(method=...)` accepts `harmbench`/`jailbreakbench`/`jbb`/`refusal`/`jbb_refusal`/`orbench`. `REFUSAL_RATE_EVALUATORS` tells `task.py` whether a run reports `refusal_rate` vs `attack_success_rate`.
- `src/llm_utils/llm_service_factory.py` — routes by `LLMModel.provider`:
  - `Provider.OPENAI` → `AsyncOpenAI` + `asyncio.gather`
  - `Provider.ANTHROPIC` → native Message Batches API (50% cheaper)
  - `Provider.GOOGLE` → native Batch API inline (50% cheaper)
  - `Provider.LOCAL` → `LocalLMService` (locally served models, e.g. Ollama)
  - `Provider.NU_CLUSTER` → `AsyncOpenAI` pointed at the vLLM endpoint registered by `ClusterModelServerManager` (supports image inputs as base64 `image_url`)

Unified call shape across providers: `service.batch_chat(conversations, system_message, is_test)`, where `conversations` is `[(conv_id, [(text, image_or_None), ...]), ...]` → `[(conv_id, response_text), ...]`. Model registry + pricing lives in `src/llm_utils/llm_model.py::LLMModel`; resolve a string with `LLMModel.from_string(...)`.

### Pydantic schemas

`src/experiment/schemas.py` is the contract between stages — carrier models `RawPrompt`, `Prompt`, `EvaluationRow`, `Judgment`, and the per-mode result models: `PromptTransformStepResult` / `PromptTransformResult` (`mode="prompt_transform"`), `DefenseEvaluateResult` (`mode="defense+evaluate"`; carries `defense`, `target_model`, `asr`, `refusal_rate`, `metrics`, `primary_metric`, `eval_stats`, usage), `AnalyzeGroupResult` / `AnalyzeResult` (`mode="analyze"`). Task configs are the discriminated union `TaskConfig` = `PromptTransformTask` | `DefenseEvaluateTask` | `AnalyzeTask`, bundled by `ExperimentPreset`. Each result carries `upstream_ref` (source_dir + results hash) so the chain reconstructs full provenance. Provenance/atomic-write helpers live in `src/utils/provenance.py` (`get_git_sha`, `judge_config_hash`, `provenance_fields`, `write_json_atomic`).

### Tracking

Every task is an MLflow run (`src/utils/mlflow_tracker.py`). The run_id is written back into the task's `results.json`, and `results.json` / `prompts.jsonl` / `raw_results.jsonl` are logged as artifacts. MLflow data lives in `mlruns/` (gitignored).

### Fonts / image rendering

`fonts/` is gitignored; rendering CJK/Devanagari (classical Chinese, Sanskrit) requires the Noto fonts present locally, else glyphs render as tofu boxes. Image-producing transforms live under `src/prompt_transformations/image/renderers/`.

## Conventions

- `prompt_range: [start, end]` is **inclusive on both ends**, 0-indexed, applied to the prompt list after loading.
- Benchmark is auto-inferred from path components (`harmbench`, `jailbreakbench`, `orbench_*`) via `_infer_benchmark`; override with `benchmark:` in the task.
- Cluster outputs are not in the repo — outputs live under `outputs/` (gitignored) and large dataset files under `data/original_datasets/` / `data/processed_datasets/` are also gitignored.
- Commit-message style is short snake-case phrases (e.g. `add_qwen_model`, `new_big_refactor`); follow that, not Conventional Commits.
- Python ≥ 3.12. Long-running model selection assumes the current model registry in `llm_model.py` — note that Claude Sonnet 4 / 4.5 are deprecated or sunsetting (see `TODO.md`).
- Always check and estimate experiment cost when designing experiments — API spend is a first-class design constraint (standing rule; moved here from the old TODO 2026-07-09 because rules that never complete are not tasks).
- **Cluster over local for experiments (standing rule, owner 2026-07-11).** The NURC cluster is the default execution surface; do NOT run experiments locally unless genuinely urgent (the cluster is down AND a result is time-critical). Local `python main.py <preset>` is for the ~$0.01 `test` smoke check only — real rounds go through the cluster (`sbatch scripts/run_experiment.sbatch` / the `run-experiment` skill). Local runs don't scale and burn the laptop.
