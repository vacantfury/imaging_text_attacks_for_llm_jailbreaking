# Experiment Plan: Encoding × Modality Jailbreaking

**Paper 1 target: EMNLP 2026 via ARR May cycle (deadline: May 25)**
**Paper 1 story:** Safety miscalibration across modalities — image safety adds cost (over-refusal) without proportional protection (encoded attacks pass through).
**Key insight:** Benign over-refusal (22-62pp increase) is the PRIMARY finding; harmful ASR parity across modalities is SUPPORTING evidence.

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
| Tier 1 (weaker) | GPT-4o-mini | OpenAI | $0.15 / $0.60 |
| Tier 1 (weaker) | Claude Sonnet 4 | Anthropic | $3.00 / $15.00 |
| Tier 1 (weaker) | Gemini 2.0 Flash | Google | $0.10 / $0.40 |
| Tier 2 (stronger) | GPT-4o | OpenAI | $2.50 / $10.00 |
| Tier 2 (stronger) | Gemini 2.5 Pro | Google | $1.25 / $10.00 |
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
| Available GPUs | V100-SXM2 (16GB), A100 (80GB), H200 | Pixtral-12B fits on 1× A100 |

**Cluster relevance:** Only Pixtral-12B requires the cluster (open-source, needs GPU). All other models are API calls.

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

`judge_method: refusal` | **Key finding:** Claude over-refuses encoded benign (27-33%). GPT/Gemini math encodings reduce refusal below baseline.

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
| 2 | Re-eval Sanskrit benign × 3 models (`judge_method: refusal`) | ✅ GPT: 83%, Gemini: 8%, Claude: 6% |

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

**Code fixes applied:** FigStep (auto-height canvas, script-aware fonts), FC-Typography (script-aware fonts, auto-wrap-width, auto-height canvas). All existing FigStep + FC-Typography results deleted.

**Round 1: Re-render ALL FigStep + FC-Typography images** ✅ DONE (12 imaging tasks)

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

### 7e: Make-up Round 2 — remaining 8 eval tasks ⬜ TODO

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

**8 eval tasks** — ~2h estimated, easily fits in one job.

**Decision points (updated):**
1. Does FC-Typography produce Δ > +15pp on Gemini/Claude? → ✅ YES confirmed (Claude set_theory: +39pp, formal_logic: +3pp)
2. Does fixed FigStep with readable content produce meaningful ASR? → unknown, depends on fix
3. Does GPT-5-mini show negative Δ across ALL encodings? → ❌ NO, encoding-dependent (−15pp set_theory, +11pp classical_chinese)
4. Does GPT-5-mini handle non-Latin scripts? → ✅ YES (classical_chinese 41% ASR, but GPT-4o-mini cannot)

---

## Stage 8: OR-Bench Calibration (first 100 rows) — PRIMARY EVIDENCE for paper

**Purpose:** JBB benign (100 borderline prompts) is weak evidence for over-refusal claims. OR-Bench is the gold-standard over-refusal benchmark (ICLR 2025, dedicated 3-class judge, human-verified benign labels). Reviewers cannot dismiss OR-Bench results.

### 8a: Encode OR-Bench (4 tasks, fast ~10 min each)

| Dataset | Rows | Encodings | Source file |
|---------|------|-----------|-------------|
| orbench_harmful | 100 (first 100) | set_theory, formal_logic | `data/orbench_harmful_prompts.jsonl` |
| orbench_benign_hard | 100 (first 100) | set_theory, formal_logic | `data/orbench_benign_hard_prompts.jsonl` |

**4 text_encode tasks** — can run in parallel with Stage 7e.

### 8b: Image OR-Bench (8 tasks, fast ~1 min each)

| Dataset | Encodings | Renderers | Tasks |
|---------|-----------|-----------|:-----:|
| orbench_harmful | set_theory, formal_logic | plain, figstep | 4 |
| orbench_benign_hard | set_theory, formal_logic | plain, figstep | 4 |

**8 imaging tasks** — depends on 8a output dirs.

### 8c: Evaluate OR-Bench (24 tasks)

| Model | Dataset | Stages | Judge | Tasks |
|-------|---------|--------|-------|:-----:|
| GPT-5-mini | harmful × 2 enc × 2 renderers | [image_original, image_encoded] | harmbench | 4 |
| Gemini 2.0 Flash | harmful × 2 enc × 2 renderers | [image_original, image_encoded] | harmbench | 4 |
| Claude Sonnet 4 | harmful × 2 enc × 2 renderers | [image_original, image_encoded] | harmbench | 4 |
| GPT-5-mini | benign_hard × 2 enc × 2 renderers | [image_original, image_encoded] | refusal | 4 |
| Gemini 2.0 Flash | benign_hard × 2 enc × 2 renderers | [image_original, image_encoded] | refusal | 4 |
| Claude Sonnet 4 | benign_hard × 2 enc × 2 renderers | [image_original, image_encoded] | refusal | 4 |

**24 eval tasks** — depends on 8b output dirs.

**Note:** text_original + text_encoded evaluation also needed (12 tasks), but these can use source_file directly without imaging. Include in eval batch.

**Total Stage 8: 4 encode + 8 imaging + 36 eval = 48 tasks** | Cost: ~$20

**What this gives us:** Dual-axis (ASR + refusal) measurement on OR-Bench with FigStep vs plain × 2 encodings × 3 models. If the "FigStep + encoding = high ASR + low refusal" pattern replicates on OR-Bench, that IS the paper.

---

## Stage 9: Generational Safety Calibration — HIGH PRIORITY (fast, uses existing images)

Test whether the imaging-as-defense pattern strengthens with newer model generations. Uses EXISTING JBB images — no encoding or imaging needed. Pure evaluation tasks.

### Hypothesis

| Model | Generation | Expected Modality Gap (image - text ASR) |
|-------|-----------|------------------------------------------|
| GPT-4o-mini | 2024 | -7pp (observed) |
| GPT-5-mini | 2025 | -15pp (observed, set_theory only) |
| GPT-5.4-mini | 2026 | -??pp (predict larger negative) |
| Gemini 2.0 Flash | 2025 | +6pp (observed) |
| Gemini 2.5 Flash | 2026 | +??pp or shift negative? |

### 9a: Evaluate GPT-5.4-mini + Gemini 2.5 Flash on existing JBB images

All source images already exist in `outputs/imaging/`. No pipeline needed — just evaluation tasks.

| Model | Encodings | Renderers | Stages | Tasks |
|-------|-----------|-----------|--------|:-----:|
| GPT-5.4-mini | set_theory, formal_logic, classical_chinese | plain, figstep | [image_original, image_encoded] harmful | 6 |
| Gemini 2.5 Flash | set_theory, formal_logic, classical_chinese | plain, figstep | [image_original, image_encoded] harmful | 6 |
| GPT-5.4-mini | set_theory, formal_logic, classical_chinese | plain, figstep | [image_original, image_encoded] benign (refusal) | 6 |
| Gemini 2.5 Flash | set_theory, formal_logic, classical_chinese | plain, figstep | [image_original, image_encoded] benign (refusal) | 6 |

**24 eval tasks** — can run immediately after Stage 7e/8a. ~4-6h estimated.

### 9b: Scale OR-Bench (if generational trend confirmed)

- Full orbench_benign_hard (1319) + orbench_harmful (655) with best models/renderers
- Unified 3-class judge for clean TPR/FPR calibration plot

**Total: ~24 tasks** | Cost: ~$30-50

**Decision point:** If GPT-5.4-mini shows even larger negative Δ → strong generational story. If Gemini 2.5 Flash shifts from positive to negative → convergence story (all providers improving). If neither → provider-specific only.

**Why this is fast:** All JBB images (plain + FigStep + FC-Typography) already rendered. Just evaluating with new models on existing directories. No sequential pipeline dependency.

---

## Stage 10: Optional/Supplementary

- HarmBench full eval (240 harmful prompts, per-category breakdown) — if needed for reviewer concerns about benchmark diversity
- Pixtral-12B open-source comparison (cluster) — frontier vs open-source divergence

---

## Stage 11: Analysis + Writing

| Analysis | Tool |
|----------|------|
| Unified refusal rate table (1-ASR vs benign refusal) | pandas |
| Safety calibration ROC plot (TPR vs FPR per condition) | matplotlib |
| Renderer comparison (plain vs FigStep vs Typography) | pandas |
| Modality gap Δ by renderer × encoding × model | seaborn heatmap |
| Bootstrap CIs on key differences | scipy/numpy |
| Figures (grouped bar, calibration curve) | matplotlib/seaborn |

---

## Timeline (updated May 3, for May 25 deadline)

| Date | Stage | Milestone |
|------|-------|-----------|
| May 1–2 ✅ | Stages 1–4 | Data, encoding, JBB text+image, font fix, benign text, JBB re-eval |
| May 2–3 ✅ | Stage 5 (12 tasks) | Benign image cc+sk + HarmBench re-imaging + Sanskrit height fix |
| May 3 ✅ | Stage 6 (4 tasks) | GPT-5-mini validation — imaging-as-defense discovered (-15pp) |
| May 3–4 | Stage 7 (52 tasks, 36 deleted + 1 killed) | Renderer exploration + GPT-5-mini full. FigStep truncation + FC-Typo bugs found. Renderers rewritten. |
| May 4 | Stage 7d make-up R1 (12 img + 37 eval, 29 completed) | Re-render done. 29/37 eval completed, 8 killed by time limit. |
| May 4–5 | Stage 7e + 8a (12 tasks) | FC-Typo benign + Sanskrit rerun + OR-Bench encoding (parallel) |
| May 5 | Stage 9a + 8b (24 eval + 8 img) | Generational eval on existing images (fast!) + OR-Bench imaging |
| May 5–6 | Stage 8c (36 tasks) | OR-Bench full evaluation |
| May 6–7 | Stage 9b / 10 | Scale OR-Bench or HarmBench/Pixtral (depends on results) |
| May 8–12 | Stage 11 | Analysis, figures, tables |
| May 12–18 | — | Writing |
| May 19–22 | — | Internal review, rewrite, polish |
| May 23–25 | — | Final formatting, submit ARR |

**Paper core — CANNOT cut:**
- Stage 9 (generational calibration) — fast (uses existing images), potentially strongest finding (temporal trend). Run FIRST.
- Stage 8 (OR-Bench calibration) — PRIMARY evidence for over-refusal claim. Required for reviewers.

**Strengthens Paper (in priority order):**
- Stage 10 (HarmBench / Pixtral) — benchmark diversity + open-source comparison

---

## Compute Budget

| Stage | Tasks | API Cost (est.) | GPU-hours |
|-------|-------|-----------------|-----------|
| 1: Encoding + Imaging ✅ | 20 | $5 | 0 |
| 2: JBB text eval ✅ | 18 | $8 (actual) | 0 |
| 3: JBB image eval ✅ | 18 | $12 (actual) | 0 |
| 4: Font fix + benign text + JBB re-eval ✅ | 28 | $7 (actual) | 0 |
| 5: Benign image completion + HB re-imaging ✅ | 12 | $4 (actual) | 0 |
| 6: GPT-5-mini validation ✅ | 4 | $3 (actual) | 0 |
| 7: Renderer exploration + GPT-5-mini full | 52 (16 valid, 36 deleted) | $12 (actual, valid only) | 0 |
| 7d: Make-up (full re-render + re-eval) | 49 | $20 | 0 |
| 8: OR-Bench calibration (100 rows) | 30 | $15 | 0 |
| 9: Generational calibration | 40 | $50 | 0 |
| 10: Optional (HarmBench / Pixtral) | 36 | $66 | ~8 |
| 11: Analysis + writing | — | $0 | 0 |
| **Total** | **~258** | **~$195** | **~8 GPU-hours** |

---

## Configuration Notes

- Encoder LLM: `gpt-4.1-mini` (all encodings)
- ASR Judge: `gpt-5-nano` with `max_tokens: 16384` (HarmBench/JBB classifier)
- Refusal Judge: `gpt-5-nano` via `judge_method: refusal` (JBB RefusalEvaluator)
- OR-Bench Judge: `gpt-5-nano` via `judge_method: orbench` (3-class: direct_answer / direct_refusal / indirect_refusal, adapted from Cui et al., 2024)
- `text_original` / `image_original` evaluated only once per model × benchmark (not per encoding)
- Image renderers: `plain` (baseline), `figstep` (auto-height, script-aware), `fc_typography` (Pacifico for Latin, Noto for CJK/Devanagari, auto-width + auto-height)
- Font: script-aware selection (Noto Sans CJK + Devanagari) with max height cap (7680px) — shared via `src/imaging/font_utils.py` across ALL renderers
- FC-Flowchart: Graphviz font set to Noto Sans CJK / Devanagari for non-Latin text
- Directory collision fix: random suffix appended to output dir names
- Tier 1 target models: GPT-5-mini (replaces GPT-4o-mini), Gemini 2.0 Flash, Claude Sonnet 4
- Tier 2 (generational comparison): GPT-5.4-mini (2026), Gemini 2.5 Flash (2026)
- Legacy reference: GPT-4o-mini (2024) — already has full JBB data for generational comparison
- Benign prompts: 100 from JailbreakBench + first 100 from OR-Bench benign hard
- OR-Bench datasets downloaded via `scripts/extract_datasets.py` from HuggingFace `bench-llm/or-bench`
- Defense: logically implied (if imaging increases ASR, OCR→text filter reverses it). No implementation needed.
- GPT-5 family models do NOT support temperature parameter (fixed in MODELS_WITHOUT_TEMPERATURE_SUPPORT).
- Image renderer factory filters kwargs to renderer-accepted params only (inspect.signature fix).
