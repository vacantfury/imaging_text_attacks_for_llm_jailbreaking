# Evaluating Defenses Against Text-Encoding Attacks on VLMs

**Target:** EMNLP 2026 (ARR May cycle, deadline May 25) | AIES 2026 (same deadline)

**Status (May 16, 2026):** 196+ evaluation tasks completed across 10+ models. Four paper directions under investigation; running Stage 10e (SAGE on older models) as the primary decision point.

---

## Research Overview

Text-encoding attacks convert harmful prompts into semantically valid encodings (set theory, formal logic, classical Chinese) that bypass VLM safety filters, achieving 24–70% ASR on frontier models. We systematically evaluate black-box defenses — Image Rendering (IR), SAGE, SemanticSmooth, and hybrid compositions — across model capability tiers and providers.

**Key findings so far:**
- IR is a strong defense on GPT-5.4 (−22 to −32pp ASR) but amplifies attacks on weaker models (GPT-5.4-nano: +12pp, Gemini 2.0 Flash: +6pp, Claude Sonnet 4 set_theory: +13pp)
- SAGE achieves near-zero ASR (0–3%) on all tested frontier models — unexpectedly strong
- SemanticSmooth is encoding-dependent and unstable across providers
- IR+SAGE beats IR alone on Claude but does not beat SAGE alone on frontier models
- GPT-family scaling: IR defense monotonically improves from nano (fails) → mini (works) → full (dominant)

## Paper Directions

Four directions ordered by scientific priority:

| Direction | Hypothesis | Probability | Target venue |
|-----------|-----------|:-----------:|:---:|
| **D1: Hybrid beats SAGE on weaker models** | SAGE degrades on budget/older models; IR+SAGE fills the gap | 25% | EMNLP Main/Findings |
| **D2: Safety-utility tradeoff** | SAGE over-refuses benign; IR maintains lower benign refusal | 45% | EMNLP Findings/AIES |
| **D3: Modality flip / regime shift** | IR amplifies attacks on open-source/weak models, defends on frontier | 65% | EMNLP Findings/AIES |
| **D4: Empirical study** | Comprehensive evaluation of attacks × defenses × model tiers | 100% | AIES/Workshop |

## Research Questions

- **RQ1 (Defense Effectiveness):** When does IR reduce ASR of text-encoding attacks on VLMs?
- **RQ2 (Defense Cost):** What is the benign over-refusal cost of each defense?
- **RQ3 (Comparison):** How do IR, SAGE, SemanticSmooth, and hybrid compositions compare?
- **RQ4 (Generality):** Across models, encodings, renderers, and benchmarks?
- **RQ5 (Scaling):** Does defense effectiveness change with model capability — including open-source VLMs?

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

### Pipeline Modes

| Mode | Description |
|------|-------------|
| `text_encode` | Encode prompts with LLM-based encoders (set_theory, formal_logic, classical_chinese, etc.) |
| `imaging` | Render encoded text as images (plain, FC-Typography renderers) |
| `defense_transform` | Apply SAGE wrapping to encoded prompts (output: `prompts.jsonl` for downstream evaluate/imaging) |
| `evaluate` | Query target model + judge ASR / refusal rate |
| `defense` | Coupled defense+query (SemanticSmooth: paraphrase × N + majority vote) |

Tasks are defined in `conf/experiment/experiment.yaml` and run concurrently via async scheduling.

---

## Models

**API models:**

| Tier | Models |
|------|--------|
| Frontier | GPT-5.4, Claude Sonnet 4.6, Gemini 2.5 Pro |
| Mid | GPT-5.4-mini, Gemini 2.5 Flash |
| Budget | GPT-5.4-nano, Gemini 2.5 Flash Lite |
| Older | GPT-5-mini, Gemini 2.0 Flash, Claude Sonnet 4, GPT-4o-mini |

**Cluster (open-source, vLLM on NURC):**

| Model | HF ID | Status |
|-------|-------|--------|
| Pixtral-12B | `mistralai/Pixtral-12B-2409` | ✅ Downloaded |
| Qwen2.5-VL-7B | `Qwen/Qwen2.5-VL-7B-Instruct` | ✅ Downloaded (May 16) |

---

## Project Structure

```
conf/                    # All YAML configs (experiment, llm, imaging, evaluation)
src/
├── experiment/          # Orchestrator + task dispatcher
├── text_encoding/       # Encoding strategies (LLM-based: set_theory, formal_logic, cc, semantic_camo)
├── imaging/             # Image renderers (plain, fc_typography)
├── defense/             # Defenders: SAGE (transform-only), SemanticSmooth (coupled)
├── evaluation/          # ASR judges (HarmBench, JBB, JBB-refusal, OR-Bench)
├── llm_utils/           # LLM service layer (OpenAI, Claude, Google, vLLM cluster)
└── utils/               # Logger, MLflow tracker

data/                    # Datasets (JSONL): harmbench, jbb, jbb_benign, orbench x3
text_docs/               # Plans, results, findings (see Key Documents below)
outputs/                 # Experiment outputs (on cluster, not in repo)
fonts/                   # Unicode fonts for rendering (Noto CJK, Devanagari, not in repo)
scripts/                 # Dataset extraction, result correction utilities
paper/                   # Presentation slides generator
```

## LLM Services

Single API: `service.batch_chat(conversations, system_message, is_test)`.

| Provider | Strategy |
|----------|----------|
| OpenAI | `AsyncOpenAI` + `asyncio.gather` (concurrent) |
| Claude | Native Message Batches API (50% cheaper) |
| Google | Native Batch API inline (50% cheaper) |
| vLLM (cluster) | `AsyncOpenAI` pointed at vLLM HTTP endpoint; supports images via base64 `image_url` |

## Key Documents

| File | Purpose |
|------|---------|
| [`text_docs/experiments_plan.md`](text_docs/experiments_plan.md) | Full experiment plan: all stages, what's done, what's next, priority order |
| [`text_docs/experiment_results.md`](text_docs/experiment_results.md) | All evaluation results — ASR tables with experiment directory paths |
| [`text_docs/proposal.md`](text_docs/proposal.md) | Research proposal: methods, results summary, paper directions, probability estimates |
| [`text_docs/progress_report.md`](text_docs/progress_report.md) | Brief progress report: findings, analysis, current directions, blockers |
| [`text_docs/nurc_cluster_properties.md`](text_docs/nurc_cluster_properties.md) | NURC cluster SLURM config and constraints |
| [`scripts/frequent_commands.md`](scripts/frequent_commands.md) | Common commands for cluster, experiments, MLflow |

## Tracking

MLflow (local): `mlflow ui` at http://localhost:5000. Each task logs params, metrics, artifacts, and cost.
