# Experiment Plan: Encoding × Modality Jailbreaking

**Target: EMNLP 2026 via ARR May cycle (deadline: May 25)**

---

## Cluster Properties (NURC)

| Constraint | Value | Impact |
|-----------|-------|--------|
| Max jobs submitted | 8 | Master + 7 workers |
| Max concurrent running | 4 | Effective parallelism |
| Max wall time (gpu) | 8 hours | Enough for vLLM serving |
| Available GPUs | V100-SXM2 (16GB), A100 (80GB), H200 | LLaVA-NeXT fits on 1× A100 |

**Cluster relevance:** Only LLaVA-NeXT requires the cluster (open-source, needs GPU).
GPT-4o, Gemini 2.5 Pro, Claude Sonnet 4 are all API calls — run from anywhere.

---

## Execution Stages (in order)

### Stage 0: Data Preparation (~1 day)

| Task | Detail |
|------|--------|
| Download HarmBench | 200 harmful behaviors, convert to `data/harmbench_prompts.jsonl` (RawPrompt schema) |
| Download JailbreakBench | 100 curated prompts, convert to `data/jbb_prompts.jsonl` |
| Create benign set | 50 benign prompts for comprehension/false-refusal controls |

**Gate:** All JSONL files validate against `RawPrompt` Pydantic schema.

---

### Stage 1: Text Encoding (~1 day)

Encode all prompts with 3 strategies. Reusable across all models.

```
python main.py -e default   # encodes plain + math + classical_chinese
```

| Encoding | Method | Source | API cost |
|----------|--------|--------|----------|
| Plain | Passthrough | — | $0 |
| Math (set theory) | GPT-4o helper LLM | 300 prompts × GPT-4o | ~$5 |
| Classical Chinese | GPT-4o helper LLM | 300 prompts × GPT-4o | ~$5 |

**Output:** 3 directories in `outputs/encode_*_YYYYMMDD/`, each with `prompts.jsonl`.

**Gate:** Spot-check 10 encoded prompts per encoding visually.

---

### Stage 2: Image Rendering (~30 min)

Render all encoded prompts as images. Reusable across all models.

```
python main.py -e imaging
```

| Input | Output | Settings |
|-------|--------|----------|
| 3 × `prompts.jsonl` from Stage 1 | 3 × `images/` directories | Arial 16pt, 1024×768, black-on-white |

**Output:** 3 directories in `outputs/image_*_YYYYMMDD/`, each with PNGs + `images.jsonl`.

**Gate:** Visually verify 5 images per encoding (plain English readable, math symbols intact, Chinese characters clear).

---

### Stage 3: Text-Modality Evaluation (~3 days)

Query all 4 models with text-encoded prompts (3 encodings × 4 models = 12 conditions).

| Model | Method | Where | Cost per 300 prompts (est.) |
|-------|--------|-------|---------------------------|
| GPT-4o | API | Local | ~$15 |
| Gemini 2.5 Pro | API | Local | ~$10 |
| Claude Sonnet 4 | API | Local | ~$15 |
| LLaVA-NeXT | vLLM | NURC cluster (1× A100) | $0 (cluster) |

```
python main.py -e eval_gpt4o      # 6 tasks (3 enc × text only for now)
# repeat for gemini, claude, llava
```

**12 evaluate tasks.** Run API models in parallel (~5 concurrent). LLaVA-NeXT on cluster.

**Estimated API cost:** ~$40 for text modality (3 models × 3 encodings × 300 prompts).

---

### Stage 4: Image-Modality Evaluation (~3 days)

Same 4 models, same 3 encodings, but image input. Image API calls cost ~2× text.

| Model | Image support | Notes |
|-------|--------------|-------|
| GPT-4o | ✅ native | base64 PNG in message |
| Gemini 2.5 Pro | ✅ native | inline image |
| Claude Sonnet 4 | ✅ native | base64 PNG |
| LLaVA-NeXT | ✅ native | multimodal input |

**12 evaluate tasks.**

**Estimated API cost:** ~$80 for image modality (vision API pricing).

---

### Stage 5: ASR Judging (~1 day)

Run dual-judge on all 7,200 responses:

| Judge | Method | Cost |
|-------|--------|------|
| GPT-4o | HarmBench classifier prompt | ~$30 |
| Llama Guard 3 | Safety classifier | $0 (cluster or local) |

**Output:** Per-response `is_jailbroken` labels from both judges.

---

### Stage 6: Human Evaluation (~3 hours × 2 people)

**When:** After Stage 5, when all automated labels exist.

**What:** Two authors independently label ~120 responses:
- ~40 where GPT-4o and Llama Guard disagree
- ~40 random positives (judge says jailbroken)
- ~40 random negatives (judge says refused)

**Rubric:** 1 = full jailbreak, 0.5 = partial, 0 = refused

**Output:** Cohen's κ + judge agreement table for the paper.

---

### Stage 7: Defense Experiment (~1 day)

OCR-first pipeline on all image conditions:

```
Image → OCR (extract text) → Llama Guard 3 → Allow/Block
```

**18 test conditions:** 3 encodings × image × 4 models + benign controls.

---

### Stage 8: Analysis & Writing (~5 days)

| Analysis | Tool |
|----------|------|
| Aggregate ASR tables | pandas |
| Per-category breakdown (HarmBench 7 cats) | pandas groupby |
| Modality gap (Δ) with bootstrap CIs | scipy/numpy |
| ANOVA interaction effects | statsmodels |
| Figures | matplotlib/seaborn |

---

## Timeline

| Week | Focus | Milestone |
|------|-------|-----------|
| Week 1 (Apr 21-27) | Stages 0-2 | Data prep, encoding, imaging complete |
| Week 2 (Apr 28 - May 4) | Stages 3-4 | All model queries done |
| Week 3 (May 5-11) | Stages 5-7 | Judging, human eval, defense |
| Week 4 (May 12-18) | Stage 8 | Analysis, figures, draft |
| Week 5 (May 19-25) | Writing | Paper submission (May 25 ARR) |

---

## Compute Budget

| Stage | Runs | API Cost (est.) | GPU-hours (cluster) |
|-------|------|-----------------|-------------------|
| Stage 1: Encoding | 3 | $10 | 0 |
| Stage 2: Imaging | 3 | $0 | 0 |
| Stage 3: Text eval | 12 | $40 | ~4 (LLaVA only) |
| Stage 4: Image eval | 12 | $80 | ~4 (LLaVA only) |
| Stage 5: Judging | 7,200 | $30 | ~2 (Llama Guard) |
| Stage 7: Defense | 18 | $0 | ~1 |
| **Total** | | **~$160** | **~11 GPU-hours** |

**Key insight:** This project is API-heavy, not compute-heavy. The cluster is only needed for LLaVA-NeXT and Llama Guard. Total cluster usage is ~11 GPU-hours — trivial within NURC limits.
