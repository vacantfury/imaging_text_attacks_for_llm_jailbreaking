# Does Modality Matter? Encoding × Modality Interactions in LLM Jailbreaking

**Target venue:** EMNLP 2026 (ARR May cycle) | **Submission deadline:** May 25, 2026

## Overview

LLM safety alignment is trained on tokenized text, but frontier models now accept images. This creates an untested gap: the same harmful content, rendered as an image, may bypass text-trained safety filters. We provide the first controlled study of the **encoding × modality interaction** on frontier multimodal LLMs (GPT-4o, Gemini 2.5 Pro, Claude Sonnet 4, LLaVA-NeXT).

## Experimental Design

### Research Questions

- **RQ1 (Modality Gap):** Does rendering text as an image change ASR vs. plain text?
- **RQ2 (Interaction):** Does double indirection (OCR → decode) amplify or degrade encoded attacks?
- **RQ3 (Architecture):** Do different model architectures show different modality gaps?

### 3 × 2 Matrix (24 conditions)

| Encoding | Text | Image-of-Text | Δ (Modality Gap) |
|----------|:----:|:-------------:|:----------------:|
| **Plain English** | ASR_E,T | ASR_E,I | Δ₁ |
| **Classical Chinese (文言文)** | ASR_C,T | ASR_C,I | Δ₂ |
| **Math Encoding** | ASR_M,T | ASR_M,I | Δ₃ |

### Datasets

| File | Source | Count |
|------|--------|-------|
| `data/harmbench_prompts.jsonl` | HarmBench (standard + contextual) | 240 |
| `data/jbb_prompts.jsonl` | JailbreakBench | 100 |
| `data/benign_prompts.jsonl` | JBB benign (controls) | 100 |

All in unified `RawPrompt` schema: `{id, category, source, prompt}`.

### Evaluation

- **ASR:** GPT-4o judge (HarmBench protocol) + Llama Guard 3
- **Modality Gap (Δ):** ASR_image − ASR_text per encoding per model
- **Statistical rigor:** Bootstrap CIs, permutation tests, ANOVA for interaction effects

---

## How to Run Experiments

### Setup

```bash
pip install -r requirements.txt   # or: poetry install

# Set API keys
export OPENAI_API_KEY=...
export ANTHROPIC_API_KEY=...
export GOOGLE_API_KEY=...
```

### Core Command

All experiments are driven by YAML presets — one command, no CLI flags:

```bash
python main.py test         # smoke test: 1 task per mode
python main.py experiment   # full experiment matrix
```

Presets live in `conf/experiment/`. Available:

| Preset | Description |
|--------|-------------|
| `test` | Smoke test: 1 task per mode (text_encode → imaging → evaluate) |
| `default` | Full experiment matrix |

### Three-Phase Pipeline

Each experiment runs through three sequential modes:

#### Phase 1: Text Encoding

Encode raw prompts with a strategy (plain, math, classical_chinese, etc.):

```yaml
# In conf/experiment/<preset>.yaml
tasks:
  - mode: text_encode
    encoding: plain                       # or: math, classical_chinese, symbol_injection, ...
    source_file: data/harmbench_prompts.jsonl
```

Output: `outputs/<benchmark>/text_encode_<encoding>_<timestamp>/prompts.jsonl`

#### Phase 2: Imaging

Render encoded prompts as PNG images:

```yaml
  - mode: imaging
    source_dir: outputs/harmbench/text_encode_plain_20260421_135559
```

Output: `outputs/<benchmark>/imaging_<encoding>_<timestamp>/` (240 PNGs + `images.jsonl`)

#### Phase 3: Evaluate

Query target model + ASR judging:

```yaml
  - mode: evaluate
    model: gpt-4o
    encoding: plain
    modality: text     # or: image
    source_dir: outputs/harmbench/text_encode_plain_20260421_135559
```

Output: `outputs/<benchmark>/eval_<model>_<encoding>_<modality>_<timestamp>/results.jsonl`

### Available Encodings

| Name | Type | EncoderType |
|------|------|-------------|
| `plain` | Passthrough | `non_llm_baseline` |
| `math` / `set_theory` | LLM-based | `llm_set_theory` |
| `formal_logic` | LLM-based | `llm_formal_logic` |
| `quantum` | LLM-based | `llm_quantum_mechanics` |
| `addition_equation` | Rule-based | `non_llm_addition_equation_split_reassemble` |
| `conditional_probability` | Rule-based | `non_llm_conditional_probability` |
| `symbol_injection` | Rule-based | `non_llm_symbol_injection` |

### Execution Architecture

The orchestrator (`src/experiment/experiment.py`) uses **async multi-queue scheduling**:

- **Local queue** (text_encode, imaging): Sequential execution
- **API queue** (GPT-4o, Gemini, Claude): Concurrent with semaphore
- **Cluster queue** (LLaVA-NeXT, Llama Guard): SLURM sbatch with job limit (max 4)

Tasks auto-classify to queues. All three queues run concurrently via `asyncio.gather`.

### Experiment Tracking

All runs are tracked in MLflow (local, no server):

```bash
mlflow ui   # → http://localhost:5000
```

Each task logs: params (config), metrics (ASR, count), artifacts (results files), tags (mode, encoding, model, modality).

### Output Structure

```
outputs/
  harmbench/
    text_encode_plain_20260421/
    text_encode_math_20260421/
    imaging_plain_20260421/
    eval_gpt-4o_plain_text_20260421/
  jailbreakbench/
    text_encode_plain_20260421/
    ...
```

---

## Project Structure

```
src/
├── text_encoding/     # Encoding strategies (13 encoders)
│   ├── base_encoder.py
│   ├── encoder_factory.py
│   ├── encoder_type.py
│   └── encoders/      # Concrete implementations
├── imaging/           # Pillow text→image rendering
├── experiment/        # Async multi-queue orchestrator
│   ├── experiment.py  # PTP-style task scheduler
│   └── task.py        # Mode dispatcher (text_encode, imaging, evaluate)
├── evaluation/        # ASR judging (HarmBench + JBB protocols)
├── data_loader/       # RawPrompt/EncodedPrompt/ImagePrompt schemas
├── llm_utils/         # LLM API layer (OpenAI, Claude, Google, vLLM)
└── utils/             # Logger, MLflow tracker
conf/experiment/       # YAML experiment presets
data/                  # Extracted datasets (JSONL)
scripts/               # Dataset extraction, analysis
```

## Detailed Docs

- [`text_docs/proposal.md`](text_docs/proposal.md) — full research proposal
- [`text_docs/experiments_plan.md`](text_docs/experiments_plan.md) — experiment plan and cluster setup
- [`text_docs/project_structure.md`](text_docs/project_structure.md) — codebase architecture
