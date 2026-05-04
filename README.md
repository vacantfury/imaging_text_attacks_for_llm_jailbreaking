# Safety Miscalibration Across Modalities

**Target:** EMNLP 2026 (ARR May cycle, deadline May 25)

**Core finding:** Image-modality safety adds cost (over-refusal of benign content, +22-62pp) without proportional protection — encoded harmful attacks still succeed at similar rates across text and image modalities. This reveals safety alignment relies on pattern matching rather than semantic understanding.

---

## Research Questions

- **RQ1 (Modality Gap):** Does rendering text as an image change ASR vs. plain text?
- **RQ2 (Over-refusal):** Do models over-refuse benign content more in image modality?
- **RQ3 (Interaction):** Does the encoding x modality interaction reveal miscalibration?

## Experimental Design

Text encoding strategies (plain, set theory, formal logic, classical Chinese, Sanskrit, etc.) combined with multiple imaging methods (plain rendering, FigStep, FC-Typography, FC-Flowchart), evaluated across frontier multimodal models (GPT-5-mini, Gemini 2.5 Flash, Claude Sonnet 4).

Datasets: JailbreakBench (harmful + benign), HarmBench, OR-Bench (over-refusal benchmark with 3-class evaluation).

---

## Key Documents

| File | Purpose |
|------|---------|
| [`text_docs/experiments_plan.md`](text_docs/experiments_plan.md) | What experiments to run, in what order, what's done, what's next |
| [`text_docs/experiment_results.md`](text_docs/experiment_results.md) | All evaluation results — ASR tables with experiment directory paths |
| [`text_docs/experiments_findings.md`](text_docs/experiments_findings.md) | Interpreted findings, story framing, strategic decisions |
| [`text_docs/proposal.md`](text_docs/proposal.md) | Original research proposal |
| [`text_docs/nurc_cluster_properties.md`](text_docs/nurc_cluster_properties.md) | NURC cluster SLURM config and constraints |

---

## How to Run

```bash
pip install -e .

# API keys in .env
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GOOGLE_API_KEY=...
```

```bash
python main.py experiment   # runs conf/experiment/experiment.yaml
python main.py test         # smoke test
```

### Pipeline

1. **`text_encode`** — Encode prompts (plain, set_theory, formal_logic, classical_chinese, etc.)
2. **`imaging`** — Render text as images (plain, FigStep, FC-Typography, FC-Flowchart)
3. **`evaluate`** — Query target model + judge for ASR / refusal classification

Tasks are defined in `conf/experiment/experiment.yaml` and run concurrently via async scheduling.

---

## Project Structure

```
conf/                    # All YAML configs (experiment, llm, imaging, evaluation)
src/
├── experiment/          # Orchestrator + task dispatcher
├── text_encoding/       # Encoding strategies (LLM-based + rule-based)
├── imaging/             # Image renderers
├── evaluation/          # ASR judges (HarmBench, JBB, JBB-refusal, OR-Bench)
├── llm_utils/           # LLM service layer (OpenAI, Claude, Google, vLLM)
└── utils/               # Logger, MLflow tracker

data/                    # Datasets (JSONL): harmbench, jbb, jbb_benign, orbench x3
text_docs/               # Plans, results, findings (see table above)
outputs/                 # Experiment outputs (on cluster, not in repo)
fonts/                   # Unicode fonts for rendering (not in repo)
scripts/                 # Dataset extraction, utilities
```

## LLM Services

Single API: `service.batch_chat(conversations, system_message, is_test)`.

| Provider | Strategy |
|----------|----------|
| OpenAI / vLLM | `AsyncOpenAI` + `asyncio.gather` (concurrent, instant) |
| Claude | Native Message Batches API (50% cheaper) |
| Google | Native Batch API inline (50% cheaper) |

## Tracking

MLflow (local): `mlflow ui` at http://localhost:5000. Each task logs params, metrics, artifacts.
