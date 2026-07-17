# The Decode Gap — Black-Box Recover-and-Decode Defense for Encoded & Image-Rendered VLM Jailbreaks

Research codebase for evaluating black-box defenses against encoded and image-rendered jailbreak attacks on Vision-Language Models, and for building a black-box **recover→decode→guard** defense that closes the **decode gap** — the step deployed guards lack: they *inspect or reason about* content but never *decode* an obfuscated payload.

This repo is the shared harness for a line of work:

- **MathEnc** — *Exposing LLM Safety Gaps Through Mathematical Encoding* (published): text-side encoders (set theory, formal logic, code) that recast harmful queries into out-of-distribution surface forms.
- **ImgAug** — *Image Augmentation Strengthens VLM Defenses Against Encoded Jailbreak Attacks* (under review): adding an image — even a content-unrelated decoy — changes a defense's behavior, because the defense's coverage happens to line up (or not) with where the encoded content lives.
- **Current project** — *The Decode Gap* (in progress): deployed black-box defenses — including the new multimodal / reasoning guards — *inspect or reason about* content but never **decode** an obfuscated payload, so semantically-encoded harm (in text or rendered into an image) routes past them; we build the minimal black-box **recover→decode→guard** defense that closes this gap and quantify its over-refusal cost. Covering every input surface is the method; the decode step is the contribution. See `text_docs/proposal.md` and `text_docs/experiments_plan.md`.

> This is an active research repo whose direction shifts; `text_docs/proposal.md`, `text_docs/experiments_plan.md`, and `text_docs/experiment_results.md` are the source of truth for what is currently in scope. Attack-side extensions (compound attacks, cross-modal splitting, mechanism) are **Future Work** (proposal §11).

---

## The pipeline

```
text_encode → [defense_transform] → [imaging] → evaluate
                                  └→ evaluate (text-only)
                  defense    (coupled defense + query + judge)
```

A harmful prompt is encoded (set theory / formal logic / code), optionally rendered into an image (`ir_plain`, fixed-font paginated) or paired with a decoy image, wrapped by a black-box defense, sent to a target VLM, and ASR-judged. Each stage writes `outputs/<mode>/<benchmark>/<cell>/results.json` with an `upstream_ref` chain so any data point's full provenance is reconstructable.

### Defenses

| Defense | Surface covered | Notes |
|---|---|---|
| `no_defense` | — | passthrough baseline |
| `sage` | input-text | prompt-level safety guard |
| `ecso` | input-image (caption, gated on `has_image`) | caption-mediated re-verification |
| `decoy` lever | input-text (+ benign image triggers re-check) | the ImgAug deployment lever, here a baseline |
| **`modality_complete`** | **input-text + input-image (OCR)** | **the contribution** — recover **and decode** every channel, one unified safety check over the union |
| guard-model baselines | input-text · input-image | comparison guards, served checkpoints (LlamaGuard-3 / -Vision, GuardReasoner-VL, OmniGuard, WildGuard) — **in progress**, see experiments plan |
| `joint_verify` | joint (text+image) | built; **Future Work** |

---

## Installation

```bash
pip install -e .
```

Python ≥ 3.12. Dependencies in `pyproject.toml`.

API keys (for judge + API targets) are read as plain environment variables (see
`.env.example`). Supply them however you prefer: export them in your shell, drop a
gitignored `.env` at the repo root, or feed them from your own secret manager. The
variables:

```bash
OPENAI_API_KEY=...        # judge + OpenAI targets/encoders
ANTHROPIC_API_KEY=...     # Anthropic targets (Message Batches API)
GOOGLE_API_KEY=...        # Gemini targets (Batch API)
HUGGINGFACE_TOKEN=...     # gated HF model downloads (cluster vLLM serving)
DEEPSEEK_API_KEY=...      # DeepSeek (OpenAI-compatible; judge/eval)
ZAI_API_KEY=...           # Z.AI / GLM (OpenAI-compatible; judge/eval)
XAI_API_KEY=...           # xAI / Grok (OpenAI-compatible)
MOONSHOT_API_KEY=...      # Moonshot / Kimi (OpenAI-compatible; judge/eval/target)
OLLAMA_BASE_URL=...       # optional; only for local Ollama-served models
```

The real `.env` is gitignored — never commit key values.

Non-Latin-script encoders and image rendering require Noto fonts under `fonts/` (gitignored).

---

## Running

```bash
python main.py test           # 4-task smoke test end-to-end (~$0.01); verifies install + keys
python main.py experiment     # main run — reads conf/experiment/experiment.yaml
```

**Active-preset convention:** the run target is hard-coded to `experiment`. For each round, **overwrite `conf/experiment/experiment.yaml`** with that round's tasks rather than creating per-round preset files. Prior rounds live in git history.

### Cluster (NU / SLURM)

Open-weight targets are served as separate vLLM SLURM jobs by the orchestrator:

```bash
sbatch scripts/run_experiment.sbatch experiment      # auto-serves vLLM targets, auto-cleans old logs
sbatch scripts/run_experiment.sbatch test --keep
```

### OCR fidelity probe (gate before image-channel runs)

```bash
sbatch temporary_scripts/ocr_probe.sbatch qwen2_5_vl_7b internvl3_8b pixtral_12b
```

Serves each VLM serially and transcribes sampled `ir_plain` images against the upstream encoded text — confirms the model can actually read the rendered attack before image-side cells are meaningful.

---

## Models

**Primary (open-weight, NU cluster / vLLM):**

| Model | Notes |
|---|---|
| `qwen2_5_vl_7b` | workhorse |
| `internvl3_8b` | `trust_remote_code: true` |
| `pixtral_12b` | marginal OCR on the longest encodings |
| `llama3_2_11b_vision` | serving blocked by a vLLM/Mllama incompatibility — text-restrict or version-pin |

**Breadth (API, optional late layer):** `gemini-2.x-flash`, `gpt-4o-mini`, `claude-sonnet-4-6`.

Provider routing behind one unified call shape `service.batch_chat(...)`:

| Provider | Strategy |
|---|---|
| OpenAI | `AsyncOpenAI` + `asyncio.gather` |
| Anthropic | native Message Batches API |
| Google | native Batch API (inline) |
| NU cluster (vLLM) | `AsyncOpenAI` against the vLLM endpoint registered by the server manager; base64 `image_url` for image input |

Model registry + pricing: `src/llm_utils/llm_model.py`.

---

## Project structure

```
conf/
├── experiment/          # YAML task specs (experiment is the run target)
├── llm/                 # model registry + per-provider config
├── text_encoding/       # encoder configs (set_theory, formal_logic, code_attack, ...)
├── imaging/             # renderer configs (ir_plain, figstep, ...)
├── defense/             # sage, ecso, modality_complete, amia_ia, semantic_smooth, ...
└── evaluation/          # judge configs (harmbench, jailbreakbench, orbench, refusal)

src/
├── experiment/          # orchestrator (concurrent dispatch, cluster server manager) + Pydantic schemas
├── text_encoding/       # LLM-based + rule-based encoders
├── imaging/             # image renderers (ir_plain fixed-font paginated, ...)
├── defense/             # all defenders incl. modality_complete (contribution) + joint_verify (future)
├── prompt_transformations/  # attack transforms (ecso_evade, cross_modal_split — future-work)
├── evaluation/          # HarmBench + JBB-refusal + OR-Bench judges
├── llm_utils/           # provider services + model registry
└── utils/               # logger, MLflow tracker

scripts/run_experiment.sbatch   # SLURM submission (canonical cluster runner)
text_docs/              # proposal, experiments plan, results, findings, summary (source of truth)
data/                   # prompt benchmarks (HarmBench, JBB, OR-Bench)
outputs/                # experiment outputs (gitignored)
fonts/ · mlruns/        # fonts + MLflow tracking (gitignored)
```

---

## Output layout

```
outputs/<mode>/<benchmark>/<short_name>_<timestamp>_<rand>/
├── results.json         # config + metrics + primary_metric + git_sha + upstream_ref
├── prompts.jsonl        # per-prompt Prompt records (src/experiment/schemas.py)
├── raw_results.jsonl    # per-prompt response + judge_output + judge_reasoning + judge_raw_response
└── images/              # rendered image artifacts (image-variant tasks only)
```

The full judge audit trail is stored per prompt, so any judgment can be inspected — or re-judged with a different classifier — without re-querying the target.

---

## Tracking

Each task is an MLflow run (params, metrics, artifacts), local file store under `mlruns/`:

```bash
mlflow ui              # http://localhost:5000
```

Per-run target token/USD usage is recorded in `results.json`.

---

## Reproducibility notes

- **Pairing:** all variants in a (model, defense, encoding) cell share one canonical encoded text, encoded once and reused via `source_transform_subdir` references rather than re-encoding.
- **Empty-response handling:** the judge auto-classifies empty responses as refusals — correctly handling upstream API content-filtering on encodings a provider blocks at the API layer.
- **Schema versioning:** every `results.json` carries `schema_version`/`git_sha`/`git_dirty`; table builders filter on `schema_version` to exclude stray legacy dirs.
- **Renderer change:** image-side data use the **fixed-font paginated** renderer; older single-image (shrink-to-fit) renders are demarcated in `experiment_results.md` and are **not** directly comparable.

---

## License

Code: MIT. Datasets: see the original HarmBench / JailbreakBench / OR-Bench licenses for the evaluation prompts.
