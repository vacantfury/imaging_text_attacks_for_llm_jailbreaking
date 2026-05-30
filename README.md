# Image Augmentation Amplifies and Bypasses VLM Jailbreak Defenses

Code accompanying the paper of the same title.

This repository implements and reproduces:
- The **encoded-jailbreak attack pipeline**: text-side encoders (code-completion, formal logic, set theory) that transform harmful queries into out-of-distribution surface forms.
- The **image-augmentation operator**: paired (text, image) inputs with two variants — **M2** (encoded text rendered as a typographic image) and **M4** (encoded text on the text channel paired with a content-unrelated decoy image).
- **Three black-box defenses**: a no-defense passthrough, SAGE (prompt-level safety guard), and ECSO (caption-mediated re-verification).
- **Paired safety / utility evaluation** on HarmBench (harmful) and JailbreakBench-benign (utility), reported on the safety–utility plane.

## Headline findings (from the paper)

- **Amplification (M4 + ECSO):** wrapping an encoded text attack with a content-unrelated decoy image *strengthens* the caption-mediated defense ECSO. On `gemini-2.0-flash`, ECSO's ASR reduction grows from 1pp (text-only) to 48pp (M4) on code-completion attacks; 5pp to 43pp on formal-logic attacks.
- **Bypass (M2 + SAGE-as-system):** when the encoded text is rendered *into* the image and SAGE is applied as a system message (text-channel only), the defense is bypassed. On `gemini-2.5-flash-lite`, SAGE's ASR drop collapses from 54→4% (text channel) to 54→33% (image channel) — a +29pp bypass. The failure mode concentrates on the Gemini family in our suite.
- **Unified mechanism:** defense effectiveness is governed by whether the defense's processing covers the modality where the encoded content lives.
- **Decoy ablation:** the M4 amplification persists when the image is a content-unrelated decoy, supporting a modality-level (not content-level) mechanism.
- **Deployment hazard:** SAGE on the Gemini family in the M4 regime achieves near-zero ASR at 76–100% benign-refusal cost — the trivial-reject failure mode.

---

## Installation

```bash
pip install -e .
```

Python ≥ 3.12. Dependencies in `pyproject.toml`.

API keys via `.env`:

```bash
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GOOGLE_API_KEY=...
```

Non-Latin-script encoders (e.g. classical Chinese) require Noto fonts; place under `fonts/` (gitignored).

---

## Reproducing the paper

### Quick smoke test (~$0.01)

```bash
python main.py test
```

Runs `conf/experiment/test.yaml` — a 4-task end-to-end pipeline check across two encoders and two models. Verifies the install + API keys are working.

### Full experiment

```bash
python main.py experiment
```

Reads `conf/experiment/experiment.yaml`. Each task is a `(mode, model, defense, source_chain, prompt_range)` cell. Tasks run concurrently with `asyncio` (`num_main_job_threads` knob).

The paper's main results come from two job batches:

1. **Stage 1 (prompt transforms)** — render encoded text + image variants once, cache to `outputs/prompt_transform/`. Decoy variants (mountain, blank, rabbit) for the §5.3 mechanism test are rendered here.
2. **Stage 2 (defense + evaluate)** — for each (model, defense, source) cell, apply the defense, query the target model, and judge the response. Outputs to `outputs/defense+evaluate/<benchmark>/<cell>/results.json`.

To rebuild the paper's tables from outputs:

```bash
python scripts/build_paper_tables.py            # all three (Table 1, App G, App H)
python scripts/build_paper_tables.py --table 1  # just Table 1
```

The script scans `outputs/defense+evaluate/` and emits LaTeX-ready rows.

### Cleaning failed runs

```bash
python scripts/cleanup_failed.py              # dry-run
python scripts/cleanup_failed.py --delete
python scripts/cleanup_failed.py --recent 1d --delete
```

Drops any output folder lacking `results.json` (i.e., started but didn't complete).

---

## Pipeline modes

| Mode | What it does |
|---|---|
| `prompt_transform` | Apply a chain of text encoders + image renderers. Output: a chain folder with per-step subdirectories, each containing `prompts.jsonl` + `results.json`. |
| `defense+evaluate` | Take a prompt-transform output, apply a defense (no_defense / SAGE / ECSO), query the target VLM, judge with the configured classifier. Coupled in one task to avoid intermediate-state proliferation. |
| `evaluate` | Query target + judge only (no defense). Used for baselines. |
| `defense_transform` | Apply a transform-only defense (e.g., SAGE as text rewrite) without querying the target. Produces an intermediate `prompts.jsonl` for downstream `evaluate`. |
| `imaging` | Standalone image rendering of prompts (used to pre-render large image batches). |

The IR variant grid (M0/M2/M4) is realized by composing different `prompt_transform` chains:

- **M0** (`text`): an encoder step only (e.g., `code_attack`); no image.
- **M2** (`ir_plain`): encoder step + `ir_plain` typographic renderer.
- **M4** (`ir_constant`): encoder step + `ir_constant` renderer with a fixed `image_path` (decoy).

`src/prompt_transformations/image/images/` holds the decoy images (`mountain.png`, `blank.png`, `rabit.jpeg`).

---

## Models

Five VLMs, three families, accessed via official APIs:

| Family | Models |
|---|---|
| Google | `gemini-2.0-flash`, `gemini-2.5-flash`, `gemini-2.5-flash-lite` |
| OpenAI | `gpt-4o-mini` |
| Anthropic | `claude-sonnet-4-6` |

Provider routing (one unified call shape `service.batch_chat(...)`):

| Provider | Strategy |
|---|---|
| OpenAI | `AsyncOpenAI` + `asyncio.gather` |
| Anthropic | Native Message Batches API |
| Google | Native Batch API (inline) |
| Local (vLLM) | `AsyncOpenAI` against a vLLM HTTP endpoint, supports base64 `image_url` |

Model registry + pricing: `src/llm_utils/llm_model.py`.

---

## Project structure

```
conf/
├── experiment/          # YAML task specs (experiment, test, ablations)
├── llm/                 # Model registry + per-provider config
├── prompt_transform/    # Encoder + renderer configs (set_theory, code_attack, ir_plain, ir_constant, ...)
├── defense/             # SAGE, ECSO config
└── evaluation/          # Judge configs (HarmBench, JBB-refusal)

src/
├── experiment/          # Orchestrator (concurrent task dispatch) + Pydantic schemas
├── prompt_transformations/
│   ├── text/encoders/   # LLM-based + rule-based text encoders
│   └── image/           # ir_plain (typographic) + ir_constant (decoy) renderers
├── defense/             # SAGE, ECSO, no_defense
├── evaluation/          # HarmBench classifier + JBB-refusal classifier
├── llm_utils/           # Provider services (OpenAI / Anthropic / Google / vLLM)
└── utils/               # Logger, MLflow tracker

scripts/
├── build_paper_tables.py    # Regenerate paper Table 1 / App G / App H from outputs/
├── cleanup_failed.py        # Drop incomplete output folders
└── run_experiment.sbatch    # SLURM submission script (optional)

paper/                       # LaTeX source + figures (camera-ready format)
data/                        # Datasets (gitignored; obtain from public sources)
outputs/                     # Experiment outputs (gitignored)
fonts/                       # Unicode fonts for rendering (gitignored)
mlruns/                      # MLflow tracking (gitignored)
```

---

## Output layout

Every task writes to its own directory:

```
outputs/<mode>/<benchmark>/<short_name>_<timestamp>_<rand>/
├── results.json         # config + headline metrics + upstream chain reference
├── prompts.jsonl        # per-prompt records (Prompt schema, src/experiment/schemas.py)
├── raw_results.jsonl    # per-prompt response + judge_output + judge_reasoning + judge_raw_response
└── images/              # rendered image artifacts (image-variant tasks only)
```

The full judge audit trail (per-prompt `judge_output`, `judge_reasoning`, `judge_raw_response`) is stored — any single judgment can be inspected directly.

The chain provenance is reconstructable from `results.json` → `upstream` → ... recursively.

---

## Tracking

Each task is logged as an MLflow run (params, metrics, artifacts). Local file store under `mlruns/`:

```bash
mlflow ui              # http://localhost:5000
```

Per-run cost (input/output tokens, USD) is recorded in `target_usage` inside each `results.json`.

---

## License

Code: MIT. Datasets: see the original HarmBench / JailbreakBench / OR-Bench / XSTest licenses for the prompts used as evaluation inputs.

---

## Notes on reproducibility

- **Pairing protocol:** all variants in a (model, defense, encoding) cell share a single canonical encoded text, encoded once. Repeated runs reuse it via `source_transform_subdir` references rather than re-encoding.
- **Empty-response handling:** the judge auto-classifies empty model responses as refusals (`judge_reasoning: "Empty response auto-classified as refusal"`). This correctly handles upstream API content-filtering on encodings the model's provider has decided to block at the API layer.
- **Variance:** the paper's headline cell uses 3 seeds; per-cell raw judge outputs are stored, so a third party can re-judge with a different classifier without re-querying the target model.
