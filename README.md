# Does Modality Matter? Encoding × Modality Interactions in LLM Jailbreaking

**Target venue:** EMNLP 2026 (ARR May cycle) | **Submission deadline:** May 25, 2026

## Motivation

LLM safety alignment — RLHF, refusal training, Llama Guard — is built entirely on **tokenized text**. But frontier models (GPT-4o, Gemini 2.5, Claude) now accept images. This creates an asymmetry: safety mechanisms trained on text may not generalize to the same content delivered visually.

Recent work shows safety is **brittle to input representation** along three independent axes:

- **Language:** Low-resource language attacks achieve 3–80× higher ASR than English (Deng et al., 2024; Yong et al., 2023)
- **Encoding:** Cipher (CipherChat), math (MathPrompt, 73.6% ASR), and Classical Chinese (CC-BOS, ~100% ASR) attacks bypass filters by transforming *how* content is represented
- **Modality:** Rendering text as images bypasses text-trained safety — FigStep showed 82.5% ASR on open-source LVLMs, Text-DJ showed 2–4× ASR boost with text-in-image on Qwen3-VL

These three axes have been studied **in isolation**. No work examines their **interactions** — whether combining encoding with modality change produces synergistic, additive, or antagonistic effects. In particular, the **double indirection** (OCR → decode) when rendering encoded text as an image has never been characterized.

Furthermore, all typographic attack studies test open-source models only. **GPT-4o, Gemini 2.5, and Claude remain completely untested** for typographic jailbreaks.

## Research Goal

Provide the first **clean, controlled study** of the encoding × modality interaction on frontier multimodal LLMs. Specifically:

- **RQ1 (Modality Gap):** Does image-rendering change ASR vs. plain text? Is it encoding-dependent?
- **RQ2 (Interaction):** Does the double indirection (OCR → decode) amplify or degrade attacks? Math notation (high OCR fidelity) may amplify; Classical Chinese (lower OCR fidelity) may degrade.
- **RQ3 (Architecture):** Do different model architectures show different modality gaps?

Every outcome is publishable: gap found (vulnerability), gap closed (positive safety finding), or encoding-dependent gap (nuanced interaction).

## Experimental Matrix

**3 encodings × 2 modalities × 4 models = 24 conditions**

| Encoding | Text | Image-of-Text | Δ (Modality Gap) |
|----------|:----:|:-------------:|:----------------:|
| **Plain English** | ASR_E,T | ASR_E,I | Δ₁ |
| **Classical Chinese (文言文)** | ASR_C,T | ASR_C,I | Δ₂ |
| **Math Encoding** | ASR_M,T | ASR_M,I | Δ₃ |

**Key hypothesis (double indirection):** Rendering encoded text as an image forces the model to OCR → decode — two obfuscation layers. Math notation (high OCR fidelity) may amplify the bypass; Classical Chinese (lower OCR fidelity) may degrade it.

## Target Models

| Model | Type |
|-------|------|
| GPT-4o | Frontier closed-source |
| Gemini 2.5 Pro | Frontier closed-source |
| Claude Sonnet 4 | Frontier closed-source |
| LLaVA-NeXT | Open-source (FigStep comparison) |

## Dataset

- **150 harmful prompts** stratified across categories (AdvBench, HarmBench, JailbreakBench)
- **50 benign prompts** for comprehension verification and false refusal measurement

## Evaluation

- **ASR:** GPT-4o judge (HarmBench protocol) + Llama Guard 3
- **Modality Gap (Δ):** ASR_image − ASR_text per encoding per model
- **Interaction Effect:** ANOVA across encodings — does Δ vary by encoding type?
- **Statistical rigor:** Bootstrap confidence intervals, permutation tests

## Project Structure

```
src/
├── llm_utils/         # LLM API layer (OpenAI, Claude, Google, Local)
├── text_encoding/     # Encoding strategies (Plain, Classical Chinese, Math)
├── imaging/           # Pillow text→image rendering
├── experiment/        # Experiment orchestration with mode-based dispatch
├── evaluation/        # ASR judging
├── data_loader/       # Dataset loading
└── utils/             # Logger, multiprocessing
```

### Task Modes

The experiment runs in three phases, each invoked as a separate mode:

```bash
# Phase 1: Encode prompts (run once per encoding, shared across models)
python -m src.experiment  mode=encode  encoding=classical_chinese

# Phase 2: Render as images (run once per encoding)
python -m src.experiment  mode=image   encoding=classical_chinese

# Phase 3: Query models and judge (per model × encoding × modality)
python -m src.experiment  mode=evaluate  model=gpt4o  encoding=classical_chinese  modality=image
```

## Timeline

| Week | Milestone |
|------|-----------|
| 1 | Encoding pipelines (Classical Chinese, Math) + image rendering |
| 2 | Text-modality experiments: 3 encodings × 4 models |
| 3 | Image-modality experiments: 3 encodings × 4 models |
| 4 | Comprehension controls + statistical analysis |
| 5 | Paper writing + figures |

## Key Prior Work

| Paper | What it shows | Gap we fill |
|-------|--------------|-------------|
| **FigStep** (AAAI 2025) | 82.5% ASR with typographic images on open-source LVLMs | No text baseline, no frontier models |
| **Text-DJ** (2026) | 2–4× ASR boost from image rendering on Qwen3-VL | Confounded with decomposition, one model family only |
| **JailBreakV-28K** (COLM 2024) | Text attacks (50.5% ASR) >> image attacks (30%) | Never tested text rendered *as* images |
| **CC-BOS** (ICLR 2026) | Near-100% ASR with Classical Chinese encoding | Text-only, never tested in image modality |
| **MathPrompt** (2024) | 73.6% ASR with math encoding | Text-only, never tested in image modality |

## Detailed Docs

- **Full proposal:** [`text_docs/proposal.md`](text_docs/proposal.md) — research questions, methodology, risks, publication strategy
- **Project structure:** [`text_docs/project_structure.md`](text_docs/project_structure.md) — codebase architecture, migration plan, task modes
- **Literature review:** [`paper/literature_review.md`](paper/literature_review.md) — comprehensive survey + integrated gap analysis

## Setup

```bash
# Install dependencies
poetry install

# Set API keys in src/llm_utils/.env
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GOOGLE_API_KEY=...
```

Requires Python ≥ 3.12.
