# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Visibility: public *(deliberately public from the start — owner policy 2026-07-09: science projects are public from birth, and the repo doubles as résumé/portfolio evidence. Consequence: public-grade discipline is MANDATORY — never commit personal data, ARR/reviewer text (`text_docs/reviews/` is gitignored), task files, secrets, or 1Password references.)*

## Project

Research codebase for "Evaluating Defenses Against Text-Encoding Attacks on VLMs" (EMNLP/AIES 2026 target). The pipeline encodes harmful prompts into alternative representations (set theory, formal logic, classical Chinese, etc.), optionally renders them as images, applies black-box defenses (Image Rendering, SAGE, SemanticSmooth, hybrids), queries a target VLM, and ASR-judges the response.

See `README.md` for the research narrative and `text_docs/autoattack_defense/experiments_plan.md` / `text_docs/autoattack_defense/experiment_results.md` for the current experimental state — this is an active research repo whose direction shifts week to week, so consult those before assuming what's important.

## Common commands

```bash
pip install -e .                          # install (uses pyproject.toml)
python main.py test                       # smoke test (~$0.01)
python main.py autoattack_defense/experiment                 # main run — reads conf/experiment/autoattack_defense/experiment.yaml
python main.py <preset>                   # any conf/experiment/<preset>.yaml

# Cluster (NURC)
sbatch scripts/run_experiment.sbatch autoattack_defense/experiment       # keeps old logs by default (owner 2026-07-16)
sbatch scripts/run_experiment.sbatch autoattack_defense/experiment --clean-logs   # opt in to purging old logs
sbatch scripts/run_experiment.sbatch test

# Cluster (AICR) — same, via the AICR profile wrapper
sbatch scripts/run_experiment_aicr.sbatch autoattack_defense/experiment

# Multi-cluster: split ONE preset across AICR+NURC, AICR-first (dry-run by default)
python dispatch.py autoattack_defense/experiment            # plan + ssh commands, submits nothing
python dispatch.py autoattack_defense/experiment --submit   # place + sbatch each sub-preset over ssh (sync code first)

# Cleanup half-finished experiment dirs (outputs/ that lack results.json)
python scripts/cleanup_failed.py                      # dry-run
python scripts/cleanup_failed.py --delete
python scripts/cleanup_failed.py --recent 1h --delete

# Tracking
mlflow ui                                 # http://localhost:5000
```

There is no test framework — `python main.py test` runs the 4-task smoke preset end-to-end. API keys are read as plain environment variables (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `HUGGINGFACE_TOKEN`, `DEEPSEEK_API_KEY`, `ZAI_API_KEY`, `XAI_API_KEY`, `MOONSHOT_API_KEY`; see `.env.example`). Locally, prefer `./run <preset>` — a gitignored bootstrap that injects the keys from the maintainer's secret manager, so no plaintext `.env` is needed. Plain `python main.py <preset>` still works if the vars are exported or a gitignored `.env` is present at the repo root.

## Architecture

### Conceptual pipeline & component roles (READ THIS before touching defenses)

End-to-end flow for ONE prompt, in order — the amplifier and the defense are TWO SEPARATE things; conflating them is the recurring confusion this section exists to prevent:

1. **Attack** (`prompt_transform` mode) — the original input (harmful, or benign for the over-refusal axis) is encoded into an **attack-processed prompt**: a text encoding (set theory, cipher, formal logic, classical Chinese, code) and/or an image render (FigStep, flowchart, typography, …).
2. **Defense** (`defense+evaluate` mode) — acts on the attack-processed prompt, and decomposes into two separable pieces:
   - **Amplifier** = **recover + decode**, a module placed **before** the defense (before-vs-after is a design choice). *Recover*: the target VLM transcribes the image to text. *Decode*: the target VLM restates the encoding in plain English. It **transforms** the prompt into decoded plaintext so the defense can see the hidden payload — it is **not** a defense on its own.
   - **Defense** = the safety mechanism that then acts on the (decoded) prompt. TWO KINDS:
     - **Transform defense** (**SAGE**): rewrites the text into a safety-check prompt the target answers → produces a "defense-processed prompt".
     - **Gate defense** (**WildGuard**, **LlamaGuard-3**, **Qwen3Guard**, …): a *classifier* that outputs harmful/not-harmful, then **blocks** (returns a canned refusal) or **passes the ORIGINAL prompt** to the target. A gate does **not** transform the prompt.
3. **Target response** — the target VLM (`qwen2_5_vl_7b`, …) produces the answer (or the defense already returned a refusal). Note: the target model ALSO performs the amplifier's recover/decode calls, and — for a SAGE transform defense — the self-check itself.
4. **Judge** (measurement, **external** to the defense) — **gpt-5-mini** scores the output: harm via the HarmBench rubric (→ ASR) and refusal via the OR-Bench 3-class rubric (→ over-refusal). The judge is NEVER the target model and NEVER a defense classifier. WildGuard-*as-judge* is a robustness-panel lens only — see `judge_model_issue/JUDGE_MODEL_REPORT.md` §7/§7b.

Code mapping: **`guard_baseline`** = a defense ALONE (no amplifier). **`modality_complete`** = amplifier + defense (`guard_model=None` → the SAGE *transform* defense; `guard_model=<classifier>` → a *gate* defense). The amplifier's contribution is measured as `modality_complete` vs `guard_baseline` **holding the defense fixed**; the over-refusal is a property of the chosen **defense** (a gate classifier's own calibration), not of the amplifier. **Headline metric = AutoAttack-style ENSEMBLE (best-of-N) ASR:** this repo attacks with a *suite* of ~10 elementary encoders/renderers, so a behavior counts as jailbroken under a condition if **any** attack in the suite breaks it (OR-reduction over per-prompt `asr` → `src/analysis/portfolio.py`); the headline compares that ensemble ASR across `no_defense` → `guard_baseline` → `modality_complete`. **Per-attack ASR (and its 11-attack mean) is a DIAGNOSTIC view only** — different attacks break different inputs, so the mean-per-attack understates the attacker's real (union) power and inflates how strong the defense looks.

Role glossary (one line each): **target** = the VLM under attack (also runs recover/decode, and the SAGE self-check) · **amplifier** = recover+decode transform, sits before the defense · **defense** = SAGE (transform) *or* a classifier such as WildGuard/LlamaGuard-3 (gate) that blocks/passes · **judge** = gpt-5-mini, the external scorer.

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

When any task targets a `Provider.NU_CLUSTER` model, `ClusterModelServerManager` submits vLLM servers as separate SLURM jobs, waits for one endpoint per model, and registers them with `LLMServiceFactory` so cluster-bound tasks auto-resolve endpoints. Servers are torn down in a `finally` block. A single orchestrator run is **single-cluster**: every SLURM call (`sbatch`/`squeue`/`scontrol`) is a local subprocess, so "which cluster" is just where the orchestrator process runs plus the `CLUSTER_PROFILE` env var (NURC default, or `aicr` → overlay `conf/llm/cluster_aicr.yaml`).

### Multi-cluster dispatch (`dispatch.py` / `src/experiment/multi_cluster.py`)

Because the code is synced to both clusters and each orchestrator only talks to its own local SLURM, using AICR **and** NURC together is a thin pre-submit split, not runtime SSH federation. `dispatch.py <preset>` splits one preset's task matrix across an ordered cluster pool (`conf/cluster_pool.yaml`, gitignored; template `conf/cluster_pool.example.yaml`), writes one sub-preset per cluster under the *same* paper subdir (`<paper>/_mc_<base>_<cluster>.yaml`, so output namespacing is preserved), and submits each via `ssh <cluster> sbatch <wrapper> <sub-preset>`. **Zero edits to the orchestrator runtime** — each cluster runs the existing single-cluster path natively.

- **Split key** = the full set of *cluster-served* models each task needs (target ∪ judge ∪ guard), computed by reusing `_required_cluster_models_for_task`. API judges (e.g. `gpt-5-nano`) aren't servers so they drop out → the split is target-only when the judge is API, target+judge when it's served. A cell is atomic: it runs on one cluster that serves all its models; a pipeline is never split.
- **Placement** = greedy, pool-ordered (AICR first): pack tasks onto the first cluster whose remaining server `budget` fits them, overflow the rest to the next. Small matrix → all on AICR, NURC idle (AICR preferred); big matrix → spills to NURC (both used, not failover). A model shared across a split is served once per cluster (accepted duplication); a `pins:` map forces a model onto a named cluster to keep e.g. a big judge single.
- **DRY-RUN by default** — prints the plan + exact ssh commands and writes sub-presets locally, submits nothing. `--submit` actually places + `sbatch`es (sync the code to both clusters first). Never self-initiate a run.

### 3-layer config merge

`src/experiment/config.py::load_conf` is used everywhere (text encoders under `conf/text_encoding/`, renderers under `conf/imaging/`, defenses, LLM defaults, evaluation):

```
conf/<subdir>/default.yaml  →  conf/<subdir>/<override_name>.yaml  →  task_overrides (from preset)
```

`load_conf` returns a merged plain dict via `_deep_merge` (a hand-rolled `OmegaConf.merge` replacement — OmegaConf is no longer a dependency). Validation is plain Pydantic at the call site: `llm/` merges into `ModelConfig`/`ClusterConfig`/`LLMConfig`, `evaluation/` into `JudgeLLMConfig`/`EvaluationConfig` (all in `schemas.py`) — adding a YAML field means adding it to the corresponding Pydantic model. The `conf/text_encoding/` and `conf/imaging/` dirs still exist even though the *code* factory is unified — `_resolve_step_config` picks the subdir by whether a step is image-producing.

### Factories

Each subsystem follows the same pattern — a `@register_*` class-decorator populates a name→class registry; a factory resolves a string (with alias fallback) to a concrete class:
- `src/prompt_transformations/transformation_factory.py` (`@register_transformation`) — **one unified registry** for both text encoders and image renderers (the old `text_encoding` + `imaging` factories were merged; `text/` vs `image/` is now just directory organization). Resolution order: direct `type_name` → `TRANSFORMATION_ALIASES` → classical-language auto-resolve. Text `type_name`s: `non_llm_baseline`, `non_llm_artprompt`, `non_llm_homoglyph`, `non_llm_cipher`, `non_llm_addition_equation_split_reassemble`, `non_llm_conditional_probability`, `non_llm_symbol_injection`, `llm_set_theory`, `llm_formal_logic`, `llm_quantum_mechanics`, `llm_classical_language`, `llm_semantic_camo`, `deep_inception`, `ecso_evade`, `code_attack`. Image `type_name`s: `ir_plain`, `ir_fc_typo`, `ir_figstep`, `ir_fc_flowchart`, `ir_blank`, `ir_constant`, `cross_modal_split`, and the established-multimodal-attack ensemble added 2026-07-16: `ir_low_contrast` + `ir_occluded` (Adversarial Smuggling perceptual-blindness renders; no LLM), `ir_mm_typo` (MM-SafetyBench TYPO: aux-LLM key-phrase extraction → typography, needs `model`), `ir_distraction_grid` (Text-DJ/CS-DJ distraction: aux-LLM decompose → numbered grid, needs `model`). Common aliases: `plain`→`non_llm_baseline` (the *text* baseline — for the plain image renderer use `ir_plain` literally), `set_theory`, `formal_logic`, `quantum`, `semantic_camo`, `cipher`→`non_llm_cipher` (param `cipher: base64|caesar`, default `base64`), `low_contrast`, `occluded`, `mm_typo`, `distraction`, …; `homoglyph`/`artprompt` have no alias (use `non_llm_homoglyph`/`non_llm_artprompt`). *(Semantic-Camouflage-in-image = the chain `llm_semantic_camo` → `ir_plain`, no new transform. Reference Attack held pending a guard pilot.)*
- `src/defense/defender_factory.py` (`@register_defense`) — `no_defense`, `sage`, `semantic_smooth`, `ecso`, `modality_complete`, `joint_verify`, `amia_ia`. Every `Defense` implements one interface, `query(prompts, target_service, is_multimodal, source_dir, system_message)`, and OWNS the target-model interaction (wrap input, query once, or query→inspect→re-query). There is no `is_transform_only` flag — the old transform-only/coupled split is gone (`defense+evaluate` is the only mode a defense runs under).
- `src/evaluation/evaluator_factory.py` — `EvaluatorFactory.create_from_benchmark(benchmark)` is the preferred entry (`harmbench`→HarmBench; `jailbreakbench`→dual JBB harm+refusal judges; `jailbreakbench_benign`→refusal only; `orbench*`→ORBench); explicit `create(method=...)` accepts `harmbench`/`jailbreakbench`/`jbb`/`refusal`/`jbb_refusal`/`orbench`. `REFUSAL_RATE_EVALUATORS` tells `task.py` whether a run reports `refusal_rate` vs `attack_success_rate`.
- `llm_utils` (BASE PACKAGE, pinned git dep `llm_utils @ git+https://github.com/vacantfury/llm_utils.git@v2.3.0` — vendored `src/llm_utils/` removed 2026-07-23; per-model YAML defaults wired via `LLMServiceFactory.set_config_loader` in `src/__init__.py`). `LLMServiceFactory` routes by `LLMModel.provider`:
  - `Provider.OPENAI` → `AsyncOpenAI` + `asyncio.gather`
  - `Provider.ANTHROPIC` → native Message Batches API (50% cheaper)
  - `Provider.GOOGLE` → native Batch API inline (50% cheaper)
  - `Provider.LOCAL` → `LocalLMService` (locally served models, e.g. Ollama)
  - `Provider.NU_CLUSTER` → `AsyncOpenAI` pointed at the vLLM endpoint registered by `ClusterModelServerManager` (supports image inputs as base64 `image_url`)
  - `Provider.BEDROCK` → `BedrockService` (boto3 `bedrock-runtime.converse`, sync in `asyncio.to_thread`; image inputs supported). AWS Bedrock = a US-hosted managed API fronting Claude/Kimi/DeepSeek/GLM/Qwen/Nova/…; creds via the standard AWS chain (`AWS_PROFILE`, no bearer key). Used on the **xc cluster** (an AWS box, API-first) — runbook + how-to-run: gitignored `cluster_files/xc_cluster_properties.md`. Model ids: Claude is INFERENCE_PROFILE-only (`us.`-prefixed), qwen/deepseek/nova use the bare on-demand id. Registry rows `BEDROCK_*` in `llm_model.py`; smoke preset `conf/experiment/bedrock_smoke.yaml`.

Unified call shape across providers: `service.batch_chat(conversations, system_message, is_test)`, where `conversations` is `[(conv_id, [(text, image_or_None), ...]), ...]` → `[(conv_id, response_text), ...]`. Model registry + pricing lives in the `llm_utils` package (`llm_utils.llm_model::LLMModel`); resolve a string with `LLMModel.from_string(...)`.

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
- **Conference deadlines: consult `text_docs/shared/conference_timeline.md` for ANY publication-planning work** (owner 2026-07-16). It is the shared, paper-agnostic, time-ordered list of submission deadlines (abstract/full only) plus per-venue Rep/Fit/Bar/Archival columns; update it there when a CFP lands or a date shifts — never fork per-paper deadline lists. **This copy is the CANONICAL one for all of the owner's research repos** (2026-07-20): sibling repos (`llm_agent_security`) hold a pointer stub to it, never a copy — cross-repo updates land HERE. The Fit column is scored per research repo; when a sibling repo reaches venue planning, add a second per-repo Fit column here rather than forking the file.
- **Cluster over local for experiments (standing rule, owner 2026-07-11; extended to API experiments 2026-07-13).** The NURC cluster is the default execution surface; do NOT run experiments locally unless genuinely urgent (the cluster is down AND a result is time-critical). Local `python main.py <preset>` is for the ~$0.01 `test` smoke check only — real rounds go through the cluster (`sbatch scripts/run_experiment.sbatch` / the `run-experiment` skill). Local runs don't scale and burn the laptop. **This includes API-based experiments** — judge/eval sweeps like `judge_model_issue/rejudge_candidates.py` — prefer the cluster for those too (owner 2026-07-13), once it can reach the API keys via the service account (TODO #1); a local API run ties up the laptop (lid must stay open to keep it alive).
