# Experiment Plan: Black-Box Defenses Against Text-Encoding Attacks

**Direction (updated May 16):** We study black-box defenses against text-encoding attacks on VLMs. The paper direction depends on experimental outcomes across four ordered branches:

- **Direction 1 (highest upside):** SAGE degrades on weaker/older models, and IR+SAGE or SAGE+IR beats SAGE there → defense-composition method paper.
- **Direction 2 (supporting):** SAGE over-refuses benign queries vs IR → safety-utility tradeoff story as a supporting section.
- **Direction 3 (strong fallback):** IR flips from attack amplifier on weaker/open-source models to defense on frontier → modality-regime empirical paper.
- **Direction 4 (floor):** SAGE wins everywhere → comprehensive empirical study only.

**Experiment order (scientific priority, API constraints assumed resolvable):**
1. Stage 10e — SAGE on older/budget models (tests Direction 1, the binary decision point)
2. Stage 10e hybrid — IR+SAGE + SAGE+IR on models where SAGE fails (only if Direction 1 shows gaps)
3. Stage 16 — Open-source VLM pilot: Qwen2.5-VL-7B + Pixtral-12B text vs image (confirms Direction 3, $0 cluster cost)
4. Stage 12 — SAGE benign refusal on OR-Bench (Direction 2 supporting evidence)

**Primary evidence:** GPT-5.4, Claude Sonnet 4.6, Gemini 3 Flash Preview / Gemini 2.5 Pro partial
**Scaling/mechanism evidence:** GPT-5.4-nano → GPT-5.4-mini → GPT-5.4 (IR improves within GPT family, with nano failing = amplification)
**Open-source VLMs:** Qwen2.5-VL-7B downloaded to cluster ✅. Pixtral-12B already available.

**Research questions:**
- RQ1: When does IR reduce ASR of encoding attacks on VLMs? (defense effectiveness)
- RQ2: What is the benign over-refusal cost of each defense?
- RQ3: How do IR, SAGE, SemanticSmooth, and hybrid defenses compare?
- RQ4: Generality across models, encodings, renderers?
- RQ5: Does defense effectiveness change with model capability — including open-source VLMs?

**Key remaining work:**
1. **Stage 10e:** SAGE on older/budget models (GPT-5.4-nano, Gemini 2.5 Flash Lite, GPT-5-mini, Claude Sonnet 4) — **Direction 1 decision point**
2. **Stage 10e hybrid:** IR+SAGE + SAGE+IR on models where SAGE shows gaps (conditional on Step 1)
3. **Stage 16:** Qwen2.5-VL-7B + Pixtral-12B pilot — text vs image on HarmBench 100 rows
4. **Stage 12:** SAGE benign refusal on OR-Bench (safety-utility tradeoff)
5. Bootstrap CIs + statistical analysis
6. SemanticCamo / full HarmBench only if the paper story is confirmed

---

## IMPORTANT: Dataset Row Limit

**Row limit applies ONLY to evaluation (querying target models + ASR judging).** All other stages use full datasets:

| Stage | Rows used |
|-------|-----------|
| `text_encode` (attack/encoding) | **ALL rows** |
| `imaging` (render text as image) | **ALL rows** |
| `defense_transform` (SAGE wrapping) | **ALL rows** |
| `evaluate` (query model + judge) | **First 100 rows** (`prompt_range: [0, 99]`) |
| `defense` (coupled defense+query, e.g., SemanticSmooth) | **First 100 rows** (`prompt_range: [0, 99]`) |

| Dataset | Total rows | Rows evaluated |
|---------|:----------:|:--------------:|
| JBB harmful | 100 | 100 (full) |
| JBB benign | 100 | 100 (full) |
| HarmBench | 240 | **100** |
| OR-Bench harmful | 655 | **100** |
| OR-Bench benign hard | 1319 | **100** |
| OR-Bench benign 1k | 1000 | **100** |

Rationale: Encoding/imaging/wrapping are cheap (local compute or 1 LLM call each). Evaluation is expensive (target model API calls + judge calls). Keeping full upstream data means we can later evaluate on larger slices without re-encoding.

---

## ⚠️ Known Batch API Issues

| Model | Issue | Resolution |
|-------|-------|------------|
| **Claude 4.5 Haiku** | Batch API never processes image requests — stuck at 3600s timeout | **Discarded** from all experiments |
| **Gemini 3 Pro Preview** | Batch API timeout after 3600s on ~60% of tasks | Avoid for new experiments |
| **Gemini 2.5 Pro** | Batch API also timed out on multiple HarmBench tasks | Use smaller batches only if Google access is restored |
| **OpenAI / Google API accounts** | Harmful benchmark submissions triggered trust & safety warnings | New accounts being obtained; resume once available |

Claude 4.5 Haiku and Gemini 3 Pro Preview should NOT be used as `target_model` in new experiment configs. Gemini 2.5 Pro is usable only if batch reliability and account access are resolved.

---

## Cluster Job Sizing (NURC gpu partition)

| Parameter | Value |
|-----------|-------|
| Max wall time | 8 hours (hard limit, job killed if exceeded) |
| Recommended `num_main_job_threads` | 6 |
| GPT-5-mini avg task time | ~70 min (reasoning model, slow) |
| Gemini/Claude avg task time | ~15-25 min |
| Mixed batch (like Stage 7): safe max | **40 tasks per job** |
| GPT-5-mini only: safe max | **25 tasks per job** |
| Gemini/Claude only: safe max | **60 tasks per job** |

**Strategy:** Split large batches by model speed. Run fast models (Gemini, Claude) together; run GPT-5-mini in a separate job or with fewer tasks.

---

## Core Experimental Matrix

| Encoding | Script/Notation | Text | Image-of-Text | Δ (Modality Gap) | Category |
|----------|----------------|------|---------------|------------------|----------|
| **Plain English** (baseline) | Latin | ASR_E,T | ASR_E,I | Δ₁ | Baseline |
| **Classical Chinese** (literary) | CJK | ASR_CC,T | ASR_CC,I | Δ₂ | Classical language |
| **Latin** (literary) | Latin | ASR_L,T | ASR_L,I | Δ₃ | Classical language |
| **Sanskrit** (literary) | Devanagari | ASR_S,T | ASR_S,I | Δ₄ | Classical language |
| **Set Theory** (math) | Symbolic | ASR_ST,T | ASR_ST,I | Δ₅ | Math encoding |
| **Formal Logic** (math) | Symbolic | ASR_FL,T | ASR_FL,I | Δ₆ | Math encoding |

**6 encodings × 2 modalities × 6 models = 72 conditions** (Plain English baseline comes free via `original` field).

**Target Models (tiered by safety alignment strength):**

| Tier | Model | Provider | Cost (input/output per M tokens) |
|------|-------|----------|----------------------------------|
| Tier 1 (older/weaker) | GPT-4o-mini | OpenAI | $0.15 / $0.60 |
| Tier 1 (older/weaker) | Claude Sonnet 4 | Anthropic | $3.00 / $15.00 |
| Tier 1 (older/weaker) | Gemini 2.0 Flash | Google | $0.10 / $0.40 |
| Tier 2 (newer/stronger) | GPT-5-mini | OpenAI | $0.25 / $2.00 |
| Tier 2 (newer/stronger) | GPT-5.4-mini | OpenAI | $0.75 / $4.50 |
| Tier 2 (newer/stronger) | Gemini 2.5 Flash | Google | $0.30 / $2.50 |
| Tier 3 (budget) | GPT-5.4-nano | OpenAI | $0.20 / $1.25 |
| Tier 3 (budget) | Gemini 2.5 Flash Lite | Google | $0.075 / $0.30 |
| Tier 4 (frontier) | GPT-5.4 | OpenAI | $2.50 / $15.00 |
| Tier 4 (frontier) | Claude Sonnet 4.6 | Anthropic | $3.00 / $15.00 |
| Tier 4 (frontier) | Gemini 3 Flash Preview | Google | $0.50 / $3.00 |
| Cluster | Pixtral-12B | vLLM (NURC) | $0 |

**Analytical decomposition:**
- Δ₂ vs. Δ₃ vs. Δ₄: isolates **script difficulty** (CJK vs. Latin vs. Devanagari)
- Δ₅ vs. Δ₆: tests whether mathematical bypass **generalizes across notations**
- Classical languages vs. math encodings: compares **natural language obscurity** vs. **symbolic formalization**
- Tier 1 vs. Tier 2: shows how encoding attacks **scale with model safety alignment**

---

## Cluster Properties (NURC)

| Constraint | Value | Impact |
|-----------|-------|--------|
| Max jobs submitted | 8 | Master + 7 workers |
| Max concurrent running | 4 | Effective parallelism |
| Max wall time (gpu) | 8 hours | Enough for vLLM serving |
| Available GPUs | V100-SXM2 (16GB), A100 (80GB), H200 | Pixtral-12B fits on 1× A100; Qwen2.5-VL-7B fits on 1× A100 |

**Open-source VLMs available on cluster:**
| Model | HF ID | Size | Status |
|-------|-------|------|--------|
| Pixtral-12B | `mistralai/Pixtral-12B-2409` | ~24GB | ✅ Downloaded |
| Qwen2.5-VL-7B | `Qwen/Qwen2.5-VL-7B-Instruct` | ~16GB | ✅ Downloaded (May 16) |

**Cluster relevance:** Pixtral-12B and Qwen2.5-VL-7B require the cluster (open-source, need GPU). All API models use standard API calls.

---

## Stage 1: Data Prep + Encoding + Imaging ✅ DONE

All data preparation, encoding, and imaging are complete with no issues.

| What | Detail | Output |
|------|--------|--------|
| HarmBench data | 240 harmful behaviors | `data/harmbench_prompts.jsonl` |
| JailbreakBench data | 100 harmful + 100 benign prompts | `data/jbb_prompts.jsonl`, `data/jbb_benign_prompts.jsonl` |
| OR-Bench benign 1k | 1000 easy benign (sampled from 80k) | `data/orbench_benign_1k_prompts.jsonl` |
| OR-Bench benign hard | 1319 hard benign prompts | `data/orbench_benign_hard_prompts.jsonl` |
| OR-Bench harmful | 655 toxic/harmful prompts | `data/orbench_harmful_prompts.jsonl` |
| Text encoding (5 encodings × 2 benchmarks + benign) | GPT-4.1-mini encoder | dirs in `outputs/text_encode/` |
| Imaging (5 encodings × 2 benchmarks + benign) | Plain renderer, [original, encoded] | dirs in `outputs/imaging/` |

**Encodings completed:**
- `classical_chinese_simplified_literary` (Classical Chinese)
- `latin_literary` (Latin)
- `sanskrit_literary` (Sanskrit)
- `set_theory` (Set Theory)
- `formal_logic` (Formal Logic)

Plain English baseline requires no separate encoding — uses `text_original` / `image_original` from any encoding run.

---

## Stage 2: JBB Text Eval — Tier 1 Canary ✅ DONE

Run JailbreakBench (100 prompts) first as a cheap validation pass.

| Model | prompt_stages | Tasks |
|-------|---------------|-------|
| GPT-4o-mini | [text_original] | 1 |
| Claude Sonnet 4 | [text_original] | 1 |
| Gemini 2.0 Flash | [text_original] | 1 |
| GPT-4o-mini | [text_encoded] | 5 (5 encodings × jailbreakbench) |
| Claude Sonnet 4 | [text_encoded] | 5 |
| Gemini 2.0 Flash | [text_encoded] | 5 |

**Total: 18 tasks** | Thread pool: 5 | Judge: GPT-5-nano (max_tokens: 16384)

**Actual cost:** ~$7.73 (est. $9)

**Results (ASR %):**

| Encoding | GPT-4o-mini | Gemini 2.0 Flash | Claude Sonnet 4 |
|----------|-------------|------------------|-----------------|
| Baseline (text_original) | 9 | 3 | 7 |
| Set Theory | 62 | 52 | 19 |
| Classical Chinese | 11 | 39 | 12 |
| Latin Literary | 5 | 12 | 16 |
| Sanskrit Literary | 17 | 34 | 13 |
| Formal Logic | 57 | 62 | 59 |

**Validation:** GPT-4o-mini & Gemini baselines match previous paper (10%/4%). Set Theory & Formal Logic within expected range. Claude Sonnet 4 more resistant than Claude 3.7 Sonnet (paper) for Set Theory but Formal Logic still effective.

---

## Stage 3: JBB Image Eval + Investigation ✅ DONE (partial — font bug found)

Image modality on same 3 Tier 1 models, JailbreakBench only. Core contribution — modality gap Δ. Also investigated raw responses (P3).

**Results (ASR %):**

| Encoding | GPT-4o-mini | Gemini 2.0 Flash | Claude Sonnet 4 |
|----------|-------------|------------------|-----------------|
| Baseline (image_original) | 4 | 1 | 1 |
| Set Theory | 55 | 58 | 32 |
| ~~Classical Chinese~~ | ~~0~~ | ~~0~~ | ~~0~~ |
| Latin Literary | 1 | 15 | 10 |
| ~~Sanskrit Literary~~ | ~~0~~ | ~~0~~ | ~~0~~ |
| Formal Logic | 58 | 67 | 47 |

**⚠️ Font rendering bug discovered:** Classical Chinese and Sanskrit rows were **invalidated and deleted**. `DejaVuSans.ttf` lacks CJK and Devanagari glyphs — characters rendered as tofu rectangles (□□□). All 3 models reported "I cannot read this image." The 0% ASR was an artifact of unreadable images.

**Investigation (P3):** Confirmed by reading `raw_results.jsonl` — responses were OCR failures, not safety refusals.

**Valid finding (3 encodings):** Math encodings (set_theory, formal_logic) survive as images. Latin literary is readable but low ASR. Baseline image_original shows slight ASR drop vs text.

---

## Stage 4: Font Fix + Benign Text Eval + JBB Re-eval ✅ DONE

Combined stage: (a) fix font bug, (b) run benign text evaluation, (c) re-evaluate fixed JBB images.

### 4a: Font Fix + Re-render JBB Images ✅

- Installed `Noto Sans CJK SC` and `Noto Sans Devanagari` in `fonts/`
- Updated `PlainImageRenderer` with script detection and font fallback chain
- Re-rendered 4 JBB imaging dirs (harmful + benign × classical_chinese + sanskrit)
- **Note:** Height cap (7680px, iterative font reduction) was added AFTER this re-render. JBB benign Sanskrit had 3 images >8000px → fixed in Stage 5b.

### 4b: Benign Text Eval (18 tasks) ✅

| Encoding | GPT-4o-mini | Gemini 2.0 Flash | Claude Sonnet 4 |
|----------|-------------|------------------|-----------------|
| Baseline (text_original) | 4 | 20 | 7 |
| Set Theory | 0 | 2 | 27 |
| Formal Logic | 0 | 0 | 8 |
| Classical Chinese | 11 | 8 | 33 |
| Latin Literary | 8 | 6 | 9 |
| Sanskrit Literary | 9 | 8 | 22 |

`judge_method: jbb_refusal` | **Key finding:** Claude over-refuses encoded benign (27-33%). GPT/Gemini math encodings reduce refusal below baseline.

### 4c: Re-evaluate JBB Image — Harmful cc+sk (6 tasks) ✅

Results in `experiment_results.md`. Completes the P1b table for all 5 encodings.

---

## Stage 5: Benign Image Completion + HarmBench Re-imaging ✅ DONE

### 5a: HarmBench re-imaging + Benign image eval (8 tasks) ✅

| Task | Mode | Result |
|------|------|--------|
| HarmBench re-imaging cc | imaging | ✅ 480 images (44s) |
| HarmBench re-imaging sk | imaging | ✅ 480 images (63s), 1 image height-capped |
| Benign image eval cc × 3 models | evaluate | ✅ GPT: 71%, Gemini: 7%, Claude: 13% |
| Benign image eval sk × 3 models | evaluate | ✅ (re-done in 5b after height fix) |

**Key finding:** GPT-4o-mini **cannot OCR non-Latin scripts** in images — 87-93% of responses are "I'm unable to decode or respond to the content of the image." This is a capability limitation, not safety. Gemini/Claude read them fine (6-13% refusal).

### 5b: Re-render + re-eval JBB benign Sanskrit (4 tasks) ✅

| Step | Task | Result |
|------|------|--------|
| 1 | Re-render `jailbreakbench_benign` Sanskrit with height cap | ✅ 200 images, max height capped |
| 2 | Re-eval Sanskrit benign × 3 models (`judge_method: jbb_refusal`) | ✅ GPT: 83%, Gemini: 8%, Claude: 6% |

**After Stage 5:** JBB fully complete (all 36 harmful + 36 benign evaluations). HarmBench images for cc + sk ready for Stage 6.

---

## Stage 6: GPT-5-mini Validation ✅ DONE

| Task | Prompt Stage | ASR (%) |
|------|-------------|---------|
| JBB harmful baseline | text_original | 3.0 |
| JBB harmful baseline | image_original | 3.0 |
| JBB harmful set_theory | text_encoded | 40.0 |
| JBB harmful set_theory | image_encoded | 25.0 |

**Key finding:** GPT-5-mini shows **-15pp modality gap** (image REDUCES ASR). Compare GPT-4o-mini: -7pp, Gemini: +6pp, Claude: +13pp. OpenAI models show imaging as implicit defense; Gemini/Claude show imaging as attack amplifier. This provider divergence is a critical observation.

**Technical fix applied:** GPT-5-mini (and all GPT-5 family) does not support `temperature` parameter. Added to `MODELS_WITHOUT_TEMPERATURE_SUPPORT`.

---

## Stage 7: Imaging Method Exploration + GPT-5-mini Full Coverage ⚠️ PARTIAL — bugs found, make-up needed

Two goals: (1) test whether FigStep/FC-Typography produce a larger modality gap, (2) complete GPT-5-mini coverage on all encodings to validate the imaging-as-defense pattern.

### 7a: Render JBB encoded text with alternative renderers ✅ DONE (images rendered but 2 bugs found)

| Renderer | Encodings | Dataset | Images | Status |
|----------|-----------|---------|--------|--------|
| FigStep (760×760, numbered steps) | set_theory, formal_logic, classical_chinese | JBB harmful + benign | 600 | ❌ INVALID — content truncation |
| FC-Typography (Pacifico font) | set_theory, formal_logic | JBB harmful + benign | 400 | ✅ Valid (Latin-script encodings) |
| FC-Typography (Pacifico font) | classical_chinese | JBB harmful + benign | 200 | ❌ INVALID — CJK font tofu |

**⚠️ Bug 1 — FigStep content truncation:** FigStep renders 80pt monospace at 15-char wrap on fixed 760×760 canvas. Only ~6 lines (~90 chars) are visible. Our encoded prompts are 2000+ chars. Models only see the system role prefix ("You are a math problem solver...") — all actual encoded content is invisible. ALL FigStep results are artifacts.

**⚠️ Bug 2 — FC-Typography CJK font:** Pacifico font has zero CJK glyphs. Classical Chinese text renders as tofu rectangles — same class of bug as Stage 3 DejaVuSans issue. Fix: FC-Typography renderer needs script-aware font selection (same approach as PlainImageRenderer fix).

Technical fix applied: renderer factory now filters kwargs via `inspect.signature`.

### 7b: Evaluate — renderer comparison ✅ PARTIAL (6 valid + 24 invalid → deleted)

**Valid results (FC-Typography, set_theory + formal_logic only):**

| Model | Renderer | Encoding | ASR (harmful) | Refusal (benign) |
|-------|----------|----------|:-------------:|:----------------:|
| GPT-5-mini | FC-Typography | set_theory | 43% | 9% |
| GPT-5-mini | FC-Typography | formal_logic | 57% | 3% |
| Gemini 2.0 Flash | FC-Typography | set_theory | 47% | 13% |
| Gemini 2.0 Flash | FC-Typography | formal_logic | 44% | 19% |
| Claude Sonnet 4 | FC-Typography | set_theory | 58% | 1% |
| Claude Sonnet 4 | FC-Typography | formal_logic | 62% | 9% |

**Deleted:** All 9 FigStep evals (harmful) + 9 FigStep evals (benign) + 3 FC-Typography CC evals (harmful) + 3 FC-Typography CC evals (benign) = 24 tasks.

### 7c: GPT-5-mini full encoding coverage — plain renderer ✅ DONE (1 benign Sanskrit killed)

| Encoding | text_encoded ASR | image_encoded ASR | Δ (img−txt) |
|----------|:----------------:|:-----------------:|:-----------:|
| set_theory | 40% | 25% | −15pp |
| formal_logic | 51% | 51% | 0pp |
| classical_chinese | 30% | 41% | +11pp |
| latin_literary | 18% | 21% | +3pp |
| sanskrit_literary | 36% | 24% | −12pp |

Benign refusal (image_encoded plain): set_theory 9%, formal_logic 6%, classical_chinese 9%, latin_literary 7%, sanskrit_literary **(killed — rerun needed)**.

### 7d: Make-up Round 1 — re-render + partial eval ✅ PARTIAL (29/37 eval completed, 8 killed by time limit)

**Code fixes applied:** FC-Typography (script-aware fonts, auto-wrap-width, auto-height canvas). FigStep also rewritten but **later invalidated** — see Stage 9a note.

**Round 1: Re-render ALL FigStep + FC-Typography images** ✅ DONE (12 imaging tasks) — ⚠️ FigStep images later invalidated (extreme aspect ratios for long/CJK text)

**Round 2: Evaluate (37 tasks submitted, 29 completed)**

Completed (29 tasks):
- FigStep harmful: 9/9 ✅
- FigStep benign: 9/9 ✅
- FC-Typography harmful: 9/9 ✅
- FC-Typography benign: 2/9 (Gemini set_theory + formal_logic only)

Killed by SLURM 8h time limit (6 tasks with empty output dirs, deleted):
- GPT-5-mini × FC-Typography benign: set_theory, formal_logic, classical_chinese
- Gemini 2.0 Flash × FC-Typography benign: classical_chinese
- Claude Sonnet 4 × FC-Typography benign: set_theory, formal_logic

Never started (2 tasks):
- Claude Sonnet 4 × FC-Typography benign: classical_chinese
- GPT-5-mini × benign Sanskrit plain (killed task rerun)

### 7e: Make-up Round 2 — remaining 8 eval tasks ✅ DONE (job mj_6574716, May 5)

| # | Model | Dataset | Source (FC-Typography) | Judge |
|---|-------|---------|------------------------|-------|
| 1 | GPT-5-mini | jailbreakbench_benign | set_theory_fc_typography | refusal |
| 2 | GPT-5-mini | jailbreakbench_benign | formal_logic_fc_typography | refusal |
| 3 | GPT-5-mini | jailbreakbench_benign | classical_chinese_fc_typography | refusal |
| 4 | Gemini 2.0 Flash | jailbreakbench_benign | classical_chinese_fc_typography | refusal |
| 5 | Claude Sonnet 4 | jailbreakbench_benign | set_theory_fc_typography | refusal |
| 6 | Claude Sonnet 4 | jailbreakbench_benign | formal_logic_fc_typography | refusal |
| 7 | Claude Sonnet 4 | jailbreakbench_benign | classical_chinese_fc_typography | refusal |
| 8 | GPT-5-mini | jailbreakbench_benign | sanskrit plain (killed task rerun) | refusal |

**All 8 tasks completed** in job mj_6574716 (May 5).

**Decision points (updated):**
1. Does FC-Typography produce Δ > +15pp on Gemini/Claude? → ✅ YES confirmed (Claude set_theory: +39pp, formal_logic: +3pp)
2. Does fixed FigStep with readable content produce meaningful ASR? → unknown, depends on fix
3. Does GPT-5-mini show negative Δ across ALL encodings? → ❌ NO, encoding-dependent (−15pp set_theory, +11pp classical_chinese)
4. Does GPT-5-mini handle non-Latin scripts? → ✅ YES (classical_chinese 41% ASR, but GPT-4o-mini cannot)

---

## Stage 8: OR-Bench Harmful (first 100 rows)

**Purpose (RQ1):** Additional harmful dataset beyond JBB/HarmBench. OR-Bench harmful (655 prompts) is diverse and challenging. First 100 rows as calibration.

### 8a: Encode OR-Bench (4 tasks, fast ~10 min each) ✅ DONE (job mj_6574716, May 5)

| Dataset | Rows | Encodings | Source file |
|---------|------|-----------|-------------|
| orbench_harmful | 100 (first 100) | set_theory, formal_logic | `data/orbench_harmful_prompts.jsonl` |
| orbench_benign_hard | 100 (first 100) | set_theory, formal_logic | `data/orbench_benign_hard_prompts.jsonl` |

**4 text_encode tasks** — completed in job mj_6574716. (benign_hard encoding done, eval deferred to Stage 12.)

### 8b: Image OR-Bench harmful (2 tasks) ✅ DONE (job mj_6578843, May 6)

| # | Type | Dataset | Detail | Tasks |
|---|------|---------|--------|:-----:|
| 1–2 | imaging | orbench_harmful | set_theory, formal_logic × plain | 2 |

Output dirs:
- `outputs/imaging/orbench_harmful/set_theory_plain_20260506_030606_87130643`
- `outputs/imaging/orbench_harmful/formal_logic_plain_20260506_030606_81884761`

### 8c: Evaluate OR-Bench harmful

**Text eval (6 tasks) ✅ DONE (job mj_6578843, May 6):**

| Model | Encoding | text_original ASR | text_encoded ASR |
|-------|----------|:-:|:-:|
| GPT-5-mini | set_theory | 6% | 86% |
| GPT-5-mini | formal_logic | 6% | 86% |
| Gemini 2.0 Flash | set_theory | 4% | 97% |
| Gemini 2.0 Flash | formal_logic | 3% | 92% |
| Claude Sonnet 4 | set_theory | 20% | 67% |
| Claude Sonnet 4 | formal_logic | 18% | 93% |

**Image eval (6 tasks) — NEXT JOB:**

| Model | Dataset | Stages | Judge | Tasks |
|-------|---------|--------|-------|:-----:|
| GPT-5-mini | harmful × 2 enc × plain | [image_original, image_encoded] | harmbench | 2 |
| Gemini 2.0 Flash | harmful × 2 enc × plain | [image_original, image_encoded] | harmbench | 2 |
| Claude Sonnet 4 | harmful × 2 enc × plain | [image_original, image_encoded] | harmbench | 2 |

**6 image eval tasks** — depends on 8b output dirs (done ✅).

**What this gives us (RQ1):** With 86–97% text ASR, even a modest image reduction (e.g. −20pp) would be a dramatic defense demonstration.

---

## Stage 9: IR Defense on Newer Models (GPT-5.4-mini + Gemini 2.5 Flash) ✅ DONE

**Purpose (RQ1, RQ4, RQ5):** Confirm IR defense on newer-generation models. Preliminary data shows GPT-5.4-mini averages −13pp ASR reduction across all conditions — the strongest defense signal we have.

**Key comparison:** `text_encoded ASR` vs `image_encoded ASR`. If image_encoded < text_encoded → IR defense works.

### 9a: Evaluate GPT-5.4-mini + Gemini 2.5 Flash — HARMFUL

**Datasets:** JBB harmful (100) + HarmBench harmful (first 100).

#### 9a Batch 1 — ✅ DONE (job mj_6574716, May 5)

| Type | Tasks | Status |
|------|:-----:|--------|
| Text eval (2 models × 2 datasets × 3 enc) | 12 | ✅ all completed |
| JBB image eval (2 models × 3 enc × plain + fc_typo) | 12 | ✅ all completed |
| HarmBench plain image eval (2 models × 3 enc) | 6 | ✅ all completed |
| **Imaging: JBB + HarmBench fc_flowchart (6 tasks)** | 6 | ❌ **FAILED — graphviz timeout bug** |

**Failure detail:** `graphviz` on cluster lacks `timeout` in `pipe()`. Code fix deployed (thread-based timeout via `ThreadPoolExecutor`).

#### 9a Batch 2 — ✅ DONE (job mj_6578843, May 6)

| Type | Tasks | Status |
|------|:-----:|--------|
| HarmBench fc_typography eval (2 models × 3 enc) | 6 | ✅ all completed |

**FigStep + FC-Flowchart deferred to Stage 13** (dynamic adaptation needed).

*Benign evaluation on newer models deferred to Stage 12 (RQ2 lower priority).*

#### 9b: Budget/Newer Model Exploration — HarmBench (100 rows) ✅ PARTIAL (job mj_6579252)

**Purpose (RQ4, RQ5):** Extend generality claim across model tiers.

| Model | Provider | Cost (in/out $/M) | Dataset | Encodings | Modalities | Tasks | Status |
|-------|----------|-------------------|---------|-----------|------------|:-----:|--------|
| GPT-5.4-nano | OpenAI | $0.20 / $1.25 | HarmBench (100) | set_theory, formal_logic | text + image | 4 | ✅ Done |
| Gemini 2.5 Flash Lite | Google | $0.075 / $0.30 | HarmBench (100) | set_theory, formal_logic | text + image | 4 | ✅ Done |
| ~~Claude 4.5 Haiku~~ | ~~Anthropic~~ | — | — | — | — | — | ❌ Discarded (batch API timeout) |

**8 eval tasks completed.** Claude Haiku discarded — batch API never processed image requests (stuck 3600s).

**Results:** GPT-5.4-nano defense FAILS (+12pp on set_theory). Gemini 2.5 Flash Lite defense STRONG (−22pp on set_theory).

#### 9c: Frontier Model Exploration — HarmBench (100 rows) ✅ DONE (job mj_6580412)

**Purpose (RQ5):** Test whether stronger models with more safety investment show stronger IR defense effect.

| Model | Provider | Cost (in/out $/M) | Dataset | Encodings | Modalities | Tasks | Status |
|-------|----------|-------------------|---------|-----------|------------|:-----:|--------|
| GPT-5.4 | OpenAI | $2.50 / $15.00 | HarmBench (100) | set_theory, formal_logic | text + image | 4 | ✅ Done |
| Claude Sonnet 4.6 | Anthropic | $3.00 / $15.00 | HarmBench (100) | set_theory, formal_logic | text + image | 4 | ✅ Done |
| Gemini 3 Flash Preview | Google | $0.50 / $3.00 | HarmBench (100) | set_theory, formal_logic | text + image | 4 | ✅ Done |

**12 eval tasks completed.** Estimated cost: ~$15-20.

**Results:** GPT-5.4 shows **strongest IR defense in entire experiment** (−22pp, −32pp). Claude Sonnet 4.6 consistent (−5pp, −13pp). Gemini 3 Flash Preview mixed (+4pp, −6pp).

**CONFIRMED:** IR defense scales with model capability within GPT family (nano → mini → full: +12pp → −12pp → −27pp avg).

#### 9d: Gemini 2.5 Pro — HarmBench (100 rows) ⚠️ PARTIAL (2/4 done, others timeout)

**Purpose:** Complete the Gemini scaling test. Gemini 3 Flash showed mixed results; Gemini 2.5 Pro has stronger safety alignment. (Gemini 3 Pro Preview was discarded due to batch API timeouts.)

| Model | Provider | Cost (in/out $/M) | Dataset | Encodings | Modalities | Tasks |
|-------|----------|-------------------|---------|-----------|------------|:-----:|
| Gemini 2.5 Pro | Google | $1.25 / $10.00 | HarmBench (100) | set_theory, formal_logic | text + image | 4 |

**4 eval tasks.** Can run alongside next stage tasks.

#### 9e: Classical Chinese on HarmBench — encode + image + frontier eval ✅ DONE (GPT-5.4 + Claude done, Gemini failed)

**Purpose:** Add classical_chinese encoding to HarmBench so all 3 encodings are available for frontier model comparison and defense baselines.

| Step | Task type | Details | Tasks |
|------|-----------|---------|:-----:|
| Encode | text_encode | HarmBench (all rows), classical_chinese, GPT-4.1-mini | 1 |
| Image | imaging | Render classical_chinese plain images (all rows) | 1 |
| Eval text | evaluate | GPT-5.4, Claude Sonnet 4.6, Gemini 2.5 Pro × text (100 rows) | 3 |
| Eval image | evaluate | GPT-5.4, Claude Sonnet 4.6, Gemini 2.5 Pro × image (100 rows) | 3 |

**8 tasks total.** Encode + image are cheap (GPT-4.1-mini + local, full dataset). Eval ~$3 (100 rows).

---

## Stage 10: Defense Baselines — SAGE + SemanticSmooth

**Purpose (RQ3):** Run existing black-box defense baselines on the same encoded prompts to compare transfer behavior across defenses. Current results show SAGE is strongest on frontier models, while IR and SemanticSmooth are provider/encoding-dependent.

**Implementation:** `src/defense/` — SAGE (prompt-wrapping, transform-only) and SemanticSmooth (SUMMARIZE variant, N=5 copies + majority vote, coupled).

**Architecture (refactored May 8):**
- SAGE uses the new `defense_transform` mode — produces `prompts.jsonl` with SAGE-wrapped text. No model query. Downstream `evaluate` or `imaging` consumes this output.
- SemanticSmooth remains in `defense` mode (coupled: paraphrase + query + vote in one step).

### 10a: Quick Validation — Does SemanticSmooth decode our encodings? ✅ DONE

Before committing compute: test whether paraphrasing decodes the encoding.
- Give GPT-4.1-mini: "Paraphrase the following: [set_theory encoded prompt]"
- If output remains encoded → SemanticSmooth fails as defense → IR clearly wins
- If output decodes to plain harmful English → SemanticSmooth is a real competitor

**1 manual test** — determines how much to invest in SemanticSmooth runs.

### 10b: SAGE baseline (transform + evaluate) ✅ DONE (frontier: 0-3% ASR — too strong)

SAGE is now a two-step pipeline:
1. `defense_transform` — wraps all prompts with SAGE template (fast, no API calls to target)
2. `evaluate` — queries target model with SAGE-wrapped text, runs ASR judge

| Step | Mode | Model | Dataset | Encodings | Tasks |
|------|------|-------|---------|-----------|:-----:|
| Transform | defense_transform | — | HarmBench | set_theory, formal_logic, classical_chinese | 3 |
| Evaluate | evaluate | GPT-5.4 | HarmBench (100) | set_theory, formal_logic, classical_chinese | 3 |
| Evaluate | evaluate | Claude Sonnet 4.6 | HarmBench (100) | set_theory, formal_logic, classical_chinese | 3 |
| Evaluate | evaluate | Gemini 2.5 Pro | HarmBench (100) | set_theory, formal_logic, classical_chinese | 3 |

**3 transform + 9 evaluate = 12 tasks.** Transform tasks use all rows; evaluate uses first 100.

### 10c: SemanticSmooth baseline (high compute — N=5 calls per prompt) ⚠️ PARTIAL (CC works, Claude formal_logic harmful)

| Model | Dataset | Encodings | Tasks |
|-------|---------|-----------|:-----:|
| GPT-5.4 | HarmBench (100) | set_theory, formal_logic, classical_chinese | 3 |
| Claude Sonnet 4.6 | HarmBench (100) | set_theory, formal_logic, classical_chinese | 3 |
| Gemini 2.5 Pro | HarmBench (100) | set_theory, formal_logic, classical_chinese | 3 |

**9 defense tasks** — each generates 5 summarized copies, queries target 5 times, majority vote.

**Cost:** ~5× higher than normal eval per task (N=5 queries × 100 prompts = 500 target queries per task). Estimate ~$30 for this stage.

**Expected outcome:** Paraphrasing may fail to decode math notation / classical Chinese → SemanticSmooth's majority vote sees 5 harmful responses → defense fails.

### 10d: Hybrid Defenses — SAGE+IR and IR+SAGE ⚠️ PARTIAL (IR+SAGE on frontier done: 6-10%, does NOT beat SAGE; SAGE+IR pending)

**Purpose:** Investigate whether combining SAGE and IR yields a stronger defense than either alone.

**Two hybrid strategies:**

| Hybrid | Pipeline | Rationale |
|--------|----------|-----------|
| **SAGE+IR** | text_encode → defense_transform(SAGE) → imaging → evaluate(image) | SAGE wraps text first, then IR renders the wrapped text as image. Model sees image of SAGE instructions + attack. |
| **IR+SAGE** | text_encode → imaging → evaluate(image + SAGE system message) | IR renders attack as image first, then SAGE instruction is sent as text alongside the image. Model sees SAGE text + attack image. |

**SAGE+IR pipeline:**
1. `defense_transform` — SAGE wraps encoded prompts (reuse from 10b)
2. `imaging` — render SAGE-wrapped text as images
3. `evaluate` — send images to target model, judge ASR

**IR+SAGE pipeline:**
1. `imaging` — render encoded prompts as images (reuse existing imaging output)
2. `evaluate` — send image with SAGE template as `system_message`, judge ASR

| Hybrid | Model | Encodings | New tasks needed |
|--------|-------|-----------|:----------------:|
| SAGE+IR | GPT-5.4 | set_theory, formal_logic | 2 eval (imaging reuse transform output) |
| SAGE+IR | Claude Sonnet 4.6 | set_theory, formal_logic | 2 eval |
| SAGE+IR | Gemini 2.5 Pro | set_theory, formal_logic | 2 eval |
| IR+SAGE | GPT-5.4 | set_theory, formal_logic | 2 eval |
| IR+SAGE | Claude Sonnet 4.6 | set_theory, formal_logic | 2 eval |
| IR+SAGE | Gemini 2.5 Pro | set_theory, formal_logic | 2 eval |

**~2 imaging + 12 evaluate = ~14 tasks** (plus transform tasks from 10b).

**Stage 10 total: 1 manual test + 12 SAGE + 9 SemanticSmooth + 14 hybrid = ~36 tasks** | Cost: ~$50

*Benign false-positive test for baselines deferred to Stage 12c.*

### 10e: Defense Scaling — SAGE vs Hybrids on Older/Weaker Models (CRITICAL) 🔜 NEXT

**Purpose:** Test whether SAGE degrades on older/budget models that cannot self-diagnose encoded attacks. If SAGE fails but IR+SAGE or SAGE+IR succeeds, the paper has a method contribution: defense composition improves robustness where a single defense breaks.

**Hypothesis:** SAGE requires strong reasoning to self-diagnose. Weaker models may see `∀x ∈ S, P(x)` and think "math," not "harmful." SAGE self-check may pass and the model may comply. IR is also imperfect on weak models, so the key question is whether IR+SAGE or SAGE+IR is more robust than either defense alone.

**Models (chosen for high vulnerability + varying IR effectiveness):**

| Model | Provider | text_encoded ASR | IR effect | Why this model |
|-------|----------|:---:|:---:|---|
| GPT-5.4-nano | OpenAI | 26-39% | IR FAILS (+12pp set_theory) | Best case: SAGE fails + IR fails → only hybrid works |
| GPT-5-mini | OpenAI | 40-51% (JBB) | IR works for set_theory (−15pp) | Moderate: SAGE might partially work |
| Claude Sonnet 4 | Anthropic | 19-59% (JBB) | IR FAILS on set_theory (+13pp JBB) | Claude API accessible; older Claude |
| Gemini 2.5 Flash Lite | Google | 57-59% | IR works (−22pp set_theory) | Highest vulnerability; cheap |

**Existing data we already have (No Defense + IR only):**
- GPT-5.4-nano: HarmBench text + image baselines (DONE)
- Gemini 2.5 Flash Lite: HarmBench text + image baselines (DONE)
- GPT-5-mini: JBB baselines only (need HarmBench text + image)
- Claude Sonnet 4: JBB baselines only (need HarmBench text + image)

**5 defense conditions to compare:**

| # | Defense | Pipeline | What it tests |
|---|---------|----------|---------------|
| 1 | No Defense | text_encoded → target model | Baseline vulnerability |
| 2 | SAGE | defense_transform → target model (text) | Does self-diagnosis work on weaker models? |
| 3 | IR only | imaging → target model (image) | Does modality switching help? |
| 4 | IR+SAGE | imaging → target model (image + SAGE system_msg) | Image safety + text-level safety check |
| 5 | SAGE+IR | defense_transform → imaging → target model (image of SAGE-wrapped text) | Render safety instructions as image too |

**Execution rounds (sequential dependency: imaging must complete before SAGE+IR evaluate):**

**Round 1a — SAGE+IR imaging (instant, local rendering):**
Run imaging on defense_transform output to create SAGE+IR image directories.

| Mode | Source | Encodings | Tasks |
|------|--------|-----------|:-----:|
| imaging | `outputs/defense_transform/harmbench/sage_set_theory_*` | set_theory | 1 |
| imaging | `outputs/defense_transform/harmbench/sage_formal_logic_*` | formal_logic | 1 |

**Round 1b — All evaluate tasks (single job, after imaging dirs exist):**

| Step | Mode | Models | Encodings | Tasks |
|------|------|--------|-----------|:-----:|
| SAGE evaluate | evaluate | GPT-5.4-nano, Gemini 2.5 Flash Lite | set_theory, formal_logic | 4 |
| IR+SAGE evaluate | evaluate | GPT-5.4-nano, Gemini 2.5 Flash Lite | set_theory, formal_logic | 4 |
| SAGE+IR evaluate | evaluate | GPT-5.4-nano, Gemini 2.5 Flash Lite | set_theory, formal_logic | 4 |

**Priority: 2 imaging + 12 evaluate = 14 tasks** (HarmBench models with existing baselines)

**Round 2 — GPT-5-mini + Claude Sonnet 4 (need HarmBench baselines first):**

| Step | Mode | Models | Encodings | Tasks |
|------|------|--------|-----------|:-----:|
| Baseline text | evaluate | GPT-5-mini, Claude Sonnet 4 | set_theory, formal_logic | 4 |
| Baseline image (IR) | evaluate | GPT-5-mini, Claude Sonnet 4 | set_theory, formal_logic | 4 |
| SAGE evaluate | evaluate | GPT-5-mini, Claude Sonnet 4 | set_theory, formal_logic | 4 |
| IR+SAGE evaluate | evaluate | GPT-5-mini, Claude Sonnet 4 | set_theory, formal_logic | 4 |
| SAGE+IR evaluate | evaluate | GPT-5-mini, Claude Sonnet 4 | set_theory, formal_logic | 4 |

**Round 2: 20 evaluate tasks**

**Total: 2 imaging + 32 evaluate = 34 tasks** | Estimated cost: ~$25

**Dream result (makes the paper):**

| Model | No Defense | SAGE | IR | IR+SAGE | SAGE+IR |
|-------|:---:|:---:|:---:|:---:|:---:|
| GPT-5.4 (frontier) | 24-39% | **0%** | 2-7% | 0-2% | TBD |
| GPT-5.4-nano (budget) | 26-39% | ~25-35%? | 38% (FAILS) | **~10-15%?** | **~10-15%?** |
| GPT-5-mini (older) | 40-51% | ~20-35%? | 25-51% | **~10-20%?** | **~10-20%?** |

Story if successful: "SAGE is excellent on frontier models, but degrades on weaker models. IR alone is also unreliable. Hybrid composition provides a more reliable black-box defense across model tiers."

---

## Stage 11: SemanticCamo Attack Baseline

**Purpose:** Validate our SemanticCamo encoder implementation as an additional attack baseline. Demonstrates generality — IR defends against diverse encoding attacks, including multi-step LLM-based ones.

### 11a: Encode HarmBench with SemanticCamo (1 task)

| Dataset | Encoder | LLM | Task |
|---------|---------|-----|:----:|
| HarmBench (all rows) | llm_semantic_camo | GPT-4.1-mini | 1 |

### 11b: Image SemanticCamo (1 task)

Render SemanticCamo output as plain image (all rows).

### 11c: Evaluate SemanticCamo (text + image) on frontier models

| Model | Dataset | Stages | Tasks |
|-------|---------|--------|:-----:|
| GPT-5.4 | HarmBench (100) | [text_encoded, image_encoded] | 2 |
| Claude Sonnet 4.6 | HarmBench (100) | [text_encoded, image_encoded] | 2 |
| Gemini 2.5 Pro | HarmBench (100) | [text_encoded, image_encoded] | 2 |

**6 eval tasks** — shows IR defense reduces ASR even for SemanticCamo on frontier models.

**Stage 11 total: 8 tasks** | Cost: ~$8

---

## Stage 12: Safety-Utility Tradeoff on OR-Bench (HIGH PRIORITY)

**Purpose:** If SAGE is too strong on harmful inputs, the paper may still have a strong story through the safety-utility tradeoff. A defense should reduce harmful ASR **and** avoid refusing benign encoded requests. OR-Bench is the best benchmark for this because it contains both harmful prompts and benign hard prompts from the same benchmark family, enabling a consistent harmful/benign comparison.

**Core metric:** Plot each defense as a point:
- x-axis: harmful ASR on OR-Bench harmful (lower is better)
- y-axis: benign refusal on OR-Bench benign_hard (lower is better)

This produces a Pareto frontier:
- If SAGE has lowest harmful ASR but high benign refusal, IR may still be useful as a lower-refusal defense.
- If IR+SAGE or SAGE+IR improves harmful ASR without increasing benign refusal too much, composition has a tradeoff story.
- If SAGE dominates both harmful ASR and benign refusal, then the paper becomes primarily a SAGE validation / empirical study.

### 12a: Complete OR-Bench benign_hard IR baseline

Existing OR-Bench harmful text+image eval is done for GPT-5-mini, Gemini 2.0 Flash, and Claude Sonnet 4. OR-Bench benign_hard encoding already exists from Stage 8a; benign_hard image rendering/eval should be completed for the same models and encodings.

| Model | Dataset | Encodings | Stages | Judge | Tasks |
|-------|---------|-----------|--------|-------|:-----:|
| GPT-5-mini | OR-Bench benign_hard | set_theory, formal_logic | text_encoded + image_encoded | `orbench` | 4 |
| Gemini 2.0 Flash | OR-Bench benign_hard | set_theory, formal_logic | text_encoded + image_encoded | `orbench` | 4 |
| Claude Sonnet 4 | OR-Bench benign_hard | set_theory, formal_logic | text_encoded + image_encoded | `orbench` | 4 |

**Plus:** 2 imaging tasks if benign_hard images do not already exist.

### 12b: Defense tradeoff comparison on OR-Bench

Run the same defense conditions on OR-Bench harmful and OR-Bench benign_hard. Start with the model/encoding pairs that already show high harmful ASR, because they provide the most headroom.

| Defense | Harmful input | Benign input | Why |
|---------|---------------|--------------|-----|
| No defense | text_encoded | text_encoded | Baseline harmful ASR + benign refusal |
| IR | image_encoded | image_encoded | Modality safety tradeoff |
| SAGE | defense_transform text | defense_transform text | Strong harmful defense; may over-refuse benign |
| IR+SAGE | image_encoded + SAGE system message | image_encoded + SAGE system message | Dual-channel defense tradeoff |
| SAGE+IR | image of SAGE-wrapped text | image of SAGE-wrapped text | Full composition tradeoff |

**Suggested first slice:** OR-Bench, set_theory + formal_logic, GPT-5-mini and Claude Sonnet 4. Add Gemini only if Google access is restored.

### 12c: Interpretation Rules

| Result | Paper implication |
|--------|-------------------|
| Hybrid beats SAGE on harmful ASR | Defense composition method paper |
| SAGE wins harmful but over-refuses benign | Safety-utility tradeoff paper; IR/hybrid may be Pareto-useful |
| SAGE wins harmful and benign | Empirical study / SAGE validation; weaker EMNLP story, stronger AIES story |
| SemanticSmooth has unstable benign/harmful tradeoff | Support for "defenses do not transfer cleanly" story |

**Stage 12 priority:** Run after or alongside Stage 10e. It is no longer secondary; it is the main fallback if hybrids do not beat SAGE on harmful ASR alone.

---

## Stage 13: Dynamic Rendering Adaptation — FigStep + FC-Flowchart (SUPPLEMENTARY)

**Purpose (RQ4 — renderer generality):** Show IR defense works across different visual formats. Currently deferred due to rendering bugs with long text.

**Problem:** FigStep and FC-Flowchart use fixed parameters for short prompts (79–140 chars). Encoded text (500–2500 chars) produces extreme aspect ratios.

**Implementation needed:**
- Scale canvas width / wrap_width by text length to maintain aspect ratio ≤ 3:1
- FigStep: wider canvas for CJK (target 25 chars/line), font floor at 50pt
- FC-Flowchart: adaptive wrap_width (scale with `sqrt(text_length)`), reduce DPI for long text

**After implementation:** Re-render + re-evaluate on JBB harmful + HarmBench.

**Estimated: ~15 imaging + ~48 eval = ~63 tasks** | Cost: ~$20

**Priority:** Adds breadth but not required for core story (plain + fc_typography already cover renderer variation).

---

## Stage 14: Statistical Analysis + Comparison (can start once Stages 9–11 done)

**Purpose:** Produce final numbers with proper statistical rigor.

| Analysis | Method | Answers |
|----------|--------|---------|
| IR defense effect sizes on frontier models (with bootstrap 95% CIs) | Bootstrap 10K resamples | RQ1 |
| Benign over-refusal comparison | Paired permutation test | RQ2 |
| IR vs SAGE vs SemanticSmooth (pairwise on frontier models) | Permutation test on ASR | RQ3 |
| Cross-model / cross-encoding interaction | Two-way ANOVA or CI overlap | RQ4 |
| Diverging scissors (GPT-5.4-nano → mini → full) | CI trend plot + regression | RQ5 |

**Output:** Tables + figures for paper.

---

## Stage 15: Writing

**Core narrative: Capability-Dependent Defense Transfer**
- Text-encoding attacks remain effective across model tiers.
- IR gets stronger within the GPT family, but is not reliable across all providers.
- SAGE is unexpectedly strong on frontier models; the key open question is whether it degrades on weaker models.
- SemanticSmooth is unstable across encodings and providers.

**Paper structure:**
1. Introduction: Text-encoding attacks achieve high ASR on modern VLMs. We systematically evaluate black-box defenses and show defense behavior is capability-, modality-, and provider-dependent.
2. Background: Text-encoding attacks (CC-BOS, MathPrompt), VLM safety, existing black-box defenses.
3. Method: IR, SAGE, SemanticSmooth, and hybrid compositions (IR+SAGE, SAGE+IR).
4. Experimental Setup: model capability tiers, 3-4 encodings, HarmBench/JBB/OR-Bench, defense comparison.
5. Results:
   - 5.1 IR is strong on GPT-5.4 but provider-dependent
   - 5.2 SAGE is unexpectedly strong on frontier models
   - 5.3 SemanticSmooth is unstable across encodings/providers
   - 5.4 GPT-family scaling: IR improves with capability
   - 5.5 Hybrid defense results and remaining SAGE weakness test
   - 5.6 Safety-utility tradeoff: harmful ASR vs benign refusal on OR-Bench
6. Analysis: Why defense transfer differs by modality, provider, and model capability. Failure cases and deployment recommendations.
7. Conclusion: Systematic evidence that black-box defense effectiveness cannot be assumed to transfer across model tiers or modalities.

---

## Stage 16: Open-Source VLM Pilot — Qwen2.5-VL-7B + Pixtral-12B 🔜 NEXT (after Stage 10e)

**Purpose (Direction 3):** Test whether IR flips from attack amplifier to defense as model capability increases. Open-source VLMs with no special safety alignment are expected to show amplification (IR increases ASR), matching the pattern seen on weaker API models (GPT-5.4-nano +12pp, Gemini 2.0 Flash +5-7pp, Claude Sonnet 4 set_theory +13pp).

**Models:**
| Model | HF ID | Provider | Expected behavior |
|-------|-------|----------|-------------------|
| Qwen2.5-VL-7B-Instruct | `Qwen/Qwen2.5-VL-7B-Instruct` | NURC cluster | IR amplifies attacks (hypothesis) |
| Pixtral-12B | `mistralai/Pixtral-12B-2409` | NURC cluster | IR amplifies attacks (hypothesis) |

**Tasks (pilot — 8 evaluate tasks):**

| Mode | Model | Encodings | Prompt stages | Dataset | Judge | Tasks |
|------|-------|-----------|---------------|---------|-------|:-----:|
| evaluate | Qwen2.5-VL-7B | set_theory, formal_logic | [text_original, text_encoded, image_original, image_encoded] | HarmBench (100) | harmbench | 4 |
| evaluate | Pixtral-12B | set_theory, formal_logic | [text_original, text_encoded, image_original, image_encoded] | HarmBench (100) | harmbench | 4 |

**Cost:** $0 (cluster only)
**Dependency:** Existing HarmBench imaging outputs (already done). No new encoding/imaging needed.

**Decision point:**
- If both models show IR amplification (+Δ) → Direction 3 story confirmed across API and open-source
- If models show IR defense (−Δ) → modality-flip story weakens; rely on API tier comparison only

---

## Priority (updated May 16)

1. **Stage 10e** — SAGE on older/budget models (CRITICAL — Direction 1 decision point)
2. **Stage 10e hybrid** — IR+SAGE + SAGE+IR on models where SAGE shows gaps (conditional on Stage 10e results)
3. **Stage 16** — Open-source VLM pilot: Qwen2.5-VL-7B + Pixtral-12B ($0 cluster, Direction 3 confirmation)
4. **Stage 12** — SAGE benign refusal on OR-Bench (Direction 2 supporting evidence)
5. Stage 14 — statistical analysis + comparison tables
6. Stage 11 — SemanticCamo (4th attack for generality; only after main story is stable)
7. Full HarmBench 240 — robustness check (only after story confirmed)
8. Stage 13 — dynamic rendering (supplementary, only if time)

**API status:**
- **OpenAI API**: Account warned, appeal failed. New account being obtained.
- **Google API**: Account warned. New account being obtained.
- **Claude API**: Still working.

Fallback deadlines: ARR June (~Jun 15) or EMNLP direct (Jun 2026).

---

## Compute Budget

### Actual spend to date (from `results.json` usage tracking, 170 tasks)

| Category | Tasks | Cost |
|----------|:-----:|-----:|
| Evaluate (target: "unknown" — older runs) | 66 | $36.55 |
| Evaluate (target: GPT-5-mini) | 28 | $24.39 |
| Evaluate (target: Claude Sonnet 4) | 14 | $23.31 |
| Evaluate (target: Gemini 2.0 Flash) | 13 | $1.41 |
| Evaluate (target: GPT-4o-mini) | 2 | $0.91 |
| Text encoding (GPT-4.1-mini) | 19 | $2.32 |
| Imaging (local rendering) | 28 | $0.00 |
| **Total spent** | **170** | **$88.90** |

### Estimated remaining spend

| Stage | Priority | Tasks | Est. cost |
|-------|----------|:-----:|----------:|
| 10e: SAGE + hybrids on HarmBench budget models | CRITICAL | ~14 | ~$5 |
| 12: OR-Bench safety-utility tradeoff | CRITICAL fallback | ~14-30 | ~$10-20 |
| 10d: SAGE+IR on frontier | HIGH | ~6 | ~$5 |
| 14: Statistical analysis | HIGH | — | $0 |
| 11: SemanticCamo attack baseline | CONDITIONAL | 6 | ~$5 |
| Full HarmBench 240 robustness | CONDITIONAL | TBD | TBD |
| 13: Dynamic rendering (supplementary) | LOW | ~63 | ~$20 |
| **Estimated decision-critical remaining** | | **~34-50** | **~$20-30** |

---

## Configuration Notes

- Encoder LLM: `gpt-4.1-mini` (all encodings)
- Judge model: `gpt-5-nano` (max_tokens: 16384) for all evaluation methods
- **Judge method by dataset/purpose:**

| Dataset | Purpose | `judge_method` | Output | Metric |
|---------|---------|----------------|--------|--------|
| JBB harmful | Attack ASR | `harmbench` | safe/unsafe | ASR % |
| HarmBench harmful | Attack ASR | `harmbench` | safe/unsafe | ASR % |
| OR-Bench harmful | Attack ASR | `harmbench` | safe/unsafe | ASR % |
| JBB benign | Over-refusal | `jbb_refusal` | refused/answered | Refusal % |
| OR-Bench benign_hard | Over-refusal | `orbench` | direct_answer/direct_refusal/indirect_refusal | Refusal % (direct+indirect) |
- `text_original` / `image_original` evaluated only once per model × benchmark (not per encoding)
- Image renderers (active): `plain` (baseline), `fc_typography` (Pacifico for Latin, Noto for CJK/Devanagari, auto-width + auto-height)
- Image renderers (deferred — need dynamic adaptation): `figstep`, `fc_flowchart` — fixed params produce unreadable images for long encoded text
- Font: script-aware selection (Noto Sans CJK + Devanagari) with max height cap (7680px) — shared via `src/imaging/font_utils.py` across ALL renderers
- FC-Flowchart: Graphviz font set to Noto Sans CJK / Devanagari for non-Latin text; thread-based timeout (30s) for rendering
- Directory collision fix: random suffix appended to output dir names
- Tier 1 target models: GPT-5-mini (replaces GPT-4o-mini), Gemini 2.0 Flash, Claude Sonnet 4
- Tier 2 (generational comparison): GPT-5.4-mini (2026), Gemini 2.5 Flash (2026)
- Tier 3 (budget): GPT-5.4-nano, Gemini 2.5 Flash Lite — HarmBench only
- Tier 4 (frontier — **primary results**): GPT-5.4, Claude Sonnet 4.6, Gemini 2.5 Pro — HarmBench only
- Tier 4 (supplementary): Gemini 3 Flash Preview — HarmBench only (Gemini 3 Pro Preview discarded due to batch API timeouts)
- Legacy reference: GPT-4o-mini (2024) — already has full JBB data for generational comparison
- Benign prompts: 100 from JailbreakBench + first 100 from OR-Bench benign hard
- OR-Bench datasets downloaded via `scripts/extract_datasets.py` from HuggingFace `bench-llm/or-bench`
- Defense baselines: SAGE (`src/defense/defenders/sage_defender.py`) — transform-only, run via `defense_transform` mode then `evaluate`. SemanticSmooth SUMMARIZE N=5 (`src/defense/defenders/semantic_smooth_defender.py`) — coupled, run via `defense` mode.
- Hybrid defenses: SAGE+IR (defense_transform → imaging → evaluate), IR+SAGE (imaging → evaluate with SAGE system_message).
- Attack baseline: SemanticCamo (`src/text_encoding/encoders/llm_semantic_camo_encoder.py`) — multi-step LLM camouflage attack.
- GPT-5 family models do NOT support temperature parameter (fixed in MODELS_WITHOUT_TEMPERATURE_SUPPORT).
- Image renderer factory filters kwargs to renderer-accepted params only (inspect.signature fix).
