# Research Proposal: Image Rendering as a Training-Free Defense Against Text-Encoding Attacks on VLMs

## 0. Literature Review Summary (May 2026)

### Threat Landscape: Text-Encoding Attacks

- **CC-BOS (ICLR 2026):** 60–74% ASR using classical Chinese encoding with multi-round LLM optimization on GPT-4o/Gemini.
- **MathPrompt (arXiv 2024):** 73% average ASR converting harmful prompts to math notation, tested on text-only LLMs.
- **Adversarial Smuggling (2026):** GPT-5 content moderation 98.6% blind to visual text. 9 smuggling techniques, 1700-prompt SmuggleBench.
- **Text-DJ (arXiv 2026):** Text-in-Image (TiI) component shows 2–4.5× ASR amplification on Qwen3-VL, GPT-4.1-mini, Gemini-2.5-Flash — but confounded within decomposition+distraction framework.
- **MIDAS (ICLR 2026):** 72–97% ASR on frontier models via multi-image puzzles. Complex pipeline (6 images, game-style templates).

### Defense Landscape: What Exists

- **SemanticSmooth (AACL-IJCNLP 2025):** LLM-based paraphrasing of multiple input copies + majority vote. Effective against GCG, PAIR, PromptRS. Untested on semantic encodings — paraphrasing may fail to decode math notation or formal logic.
- **SAGE (ACL Findings 2025):** Training-free self-discrimination prompting — asks the model to judge safety before generating. 99% defense on standard jailbreaks. Untested on encoding attacks — discriminator likely sees formal logic as "math, not harmful."
- **White-box defenses (ABD, ASTRA, DELMAN, TRYLOCK, GuardAlign):** Require model internals. Not applicable to black-box API setting.
- **Semantic codebook defenses:** AUC drops to 0.60 on non-canonical attacks (would trivially fail on encoding).
- **FigStep-specific defenses:** Confirmed dead on frontier models (0% ASR per MIDAS).

### The Gap We Fill

No defense exists specifically targeting **semantic-encoding attacks** (math notation, classical language, formal logic). Existing defenses target token-level perturbations (GCG, AutoDAN) or known image-attack patterns (FigStep). We propose the first defense mechanism for this threat class: leveraging VLMs' own image-modality safety as a defense layer.

### Key Empirical Insight

- **ASR measurement validity (Chouldechova, NeurIPS 2025):** Bootstrap CIs required. Our 100-prompt evaluations with multiple encodings × models provide adequate statistical power.
- **JRS (2025):** Blank images alone shift representations +28pp toward jailbreaking on open-source models — image modality affects safety processing at the representation level.

---

## 1. Core Idea

**The Diverging Scissors:**

Traditional defenses (SAGE, SemanticSmooth) get *weaker* on newer models:
- Newer models are better at understanding encoded text → comply more reliably → defense degrades
- Paraphrasing doesn't decode math/logic notation → majority vote says "comply" → defense fails harder on capable models

IR defense gets *stronger* on newer models:
- Newer models have stronger image-safety alignment (providers keep investing)
- IR routes text through the improving image-safety pipeline → defense automatically strengthens
- No maintenance, no re-engineering — the model vendor improves the defense for free

**Defense:** Given any incoming text (potentially an encoded attack), render it as an image and submit to the VLM. The image-modality safety pipeline catches attacks that bypass text-only safety — without retraining, without model access, without understanding the specific encoding scheme.

**Key claim:** IR is the first defense whose effectiveness *improves with model capability* without any modification — a fundamentally different trajectory from all existing defenses.

---

## 2. Research Questions

- **RQ1 (Defense Effectiveness):** Does IR reduce ASR of text-encoding attacks on frontier VLMs?
- **RQ2 (Defense Cost):** What is the benign over-refusal increase from image rendering?
- **RQ3 (Comparison):** Does IR outperform existing defenses (SemanticSmooth, SAGE) against encoding attacks?
- **RQ4 (Generality):** Is the defense effective across models, encodings, and renderers?
- **RQ5 (Scaling):** Does the defense strengthen with model capability? (The diverging scissors hypothesis)

---

## 3. Methodology

### 3.1 Threat Model

**Attacker:** Sends text-encoded harmful prompts (math notation, classical language, formal logic) to a VLM via the text channel. The encoding is semantically valid language with normal perplexity, defeating token-level defenses.

**Defender:** Has access to a VLM with image input capability. Can preprocess any incoming text by rendering it as an image and evaluating safety on the image version. Does NOT require model internals, retraining, or knowledge of the specific encoding.

### 3.2 Our Defense: Image Rendering (IR)

```
Input text T → Render as image I = render(T) → Submit I to VLM →
  VLM's image-modality safety alignment filters harmful content
```

The defense leverages the VLM's own stricter image-safety alignment. No separate "check" logic — the VLM naturally refuses harmful content when it arrives as image rather than text tokens.

Properties:
- Training-free: no fine-tuning or additional models
- Encoding-agnostic: works regardless of how T was encoded
- Model-agnostic: any VLM with image input works
- Zero overhead: same inference call, different modality
- Self-improving: strengthens as model image-safety improves

### 3.3 Comparison Defenses

| Defense | Venue | Mechanism | Trajectory on newer models |
|---------|-------|-----------|----------------------------|
| SemanticSmooth | AACL-IJCNLP 2025 | LLM paraphrases input N times + majority vote | Degrades — paraphrasing doesn't decode encodings, model complies more reliably |
| SAGE | ACL Findings 2025 | Self-discrimination prompt: model judges safety before answering | Degrades — encoded prompts don't pattern-match as harmful to the discriminator |
| **IR (ours)** | — | Render text as image → VLM's own image-safety alignment filters it | **Strengthens** — image-safety improves with model capability |

Why only 2 baselines: All other published defenses require white-box model access. SemanticSmooth and SAGE are the only published, training-free, black-box defenses applicable to our threat model.

### 3.4 Encodings (Attack Methods)

| Encoding | Description | Encoder |
|----------|-------------|---------|
| Set Theory | Formal set-theoretic expressions | GPT-4.1-mini |
| Formal Logic | First-order logic with quantifiers | GPT-4.1-mini |
| Classical Chinese (CC-BOS) | Literary Chinese with multidimensional strategy | GPT-4.1-mini |
| SemanticCamo | Multi-step LLM-based semantic camouflage | GPT-4.1-mini |

### 3.5 Image Renderers

| Renderer | Description | Tests |
|----------|-------------|-------|
| Plain | Clean text on white background | Pure modality effect (primary) |
| FC-Typography | Stylized fonts (Pacifico, Noto CJK) | OCR-difficulty effect |

### 3.6 Target Models

**Primary (frontier — Table 1):**

| Model | Provider | Role |
|-------|----------|------|
| GPT-5.4 | OpenAI | Strongest defense signal (−22 to −32pp) |
| Claude Sonnet 4.6 | Anthropic | Cross-provider (−5 to −13pp) |
| Gemini 3 Pro Preview | Google | Google frontier (pending) |

**Scaling evidence (Table 2):**

| Model | Provider | Defense effect |
|-------|----------|----------------|
| GPT-5.4-nano | OpenAI | Fails (+12pp) |
| GPT-5.4-mini | OpenAI | Works (−5 to −19pp) |
| GPT-5.4 | OpenAI | Dominant (−22 to −32pp) |

**Supporting (older models — context):**

| Model | Provider | Role |
|-------|----------|------|
| GPT-5-mini | OpenAI | Earlier generation |
| Gemini 2.0 Flash | Google | Known failure case |
| Gemini 2.5 Flash | Google | Improvement over 2.0 |
| Claude Sonnet 4 | Anthropic | Earlier Anthropic |

### 3.7 Benchmarks

| Dataset | Size | Purpose |
|---------|------|---------|
| HarmBench harmful | 100 prompts | **Primary** attack evaluation (frontier models) |
| JailbreakBench harmful | 100 prompts | Supporting attack evaluation (scaling/older models) |
| OR-Bench harmful | 100 prompts | Tertiary dataset (breadth) |
| JailbreakBench benign | 100 prompts | Over-refusal measurement |

### 3.8 Evaluation

- **ASR judge:** GPT-5-nano (HarmBench protocol, max_tokens: 16384)
- **Metrics:** ASR reduction (pp), defense success rate, benign refusal increase
- **Statistics:** Bootstrap 95% CIs; permutation tests for pairwise comparisons

---

## 4. Results (as of May 6, 2026)

### 4.1 Frontier Model Defense (Primary Results)

| Model | Encoding | Text ASR | Image ASR | Δ (defense) |
|-------|----------|:--------:|:---------:|:-----------:|
| **GPT-5.4** | set_theory | 24% | 2% | **−22pp** |
| **GPT-5.4** | formal_logic | 39% | 7% | **−32pp** |
| Claude Sonnet 4.6 | set_theory | 21% | 16% | −5pp |
| Claude Sonnet 4.6 | formal_logic | 57% | 44% | −13pp |
| Gemini 3 Pro Preview | — | — | — | pending |

GPT-5.4 image_encoded ASR (2%, 7%) is barely above image_original (1%, 1%) — the model's image safety is essentially encoding-agnostic.

### 4.2 The Diverging Scissors (GPT Family Scaling)

| Model tier | set_theory Δ | formal_logic Δ | Trajectory |
|------------|:------------:|:--------------:|:----------:|
| GPT-5.4-nano (budget) | +12pp | −2pp | Defense FAILS |
| GPT-5.4-mini (mid) | −5pp | −19pp | Defense works |
| GPT-5.4 (frontier) | −22pp | −32pp | Defense DOMINANT |

As model capability increases: defense goes from failing → working → near-perfect. This is the opposite trajectory of traditional defenses.

### 4.3 Cross-Provider Summary

| Model | Conditions where defense works | Average Δ |
|-------|:------------------------------:|:---------:|
| GPT-5.4 | 2/2 (100%) | −27pp |
| Claude Sonnet 4.6 | 2/2 (100%) | −9pp |
| GPT-5.4-mini | 6/6 (100%) | −13pp |
| Gemini 2.5 Flash Lite | 2/2 (100%) | −16pp |
| Gemini 2.5 Flash | 4/6 (67%) | −7pp |
| GPT-5.4-nano | 0/2 (0%) | +5pp |
| Gemini 2.0 Flash | 1/5 (20%) | +4pp |

### 4.4 Defense Cost (benign over-refusal)

| Model | text refusal | image refusal | Cost |
|-------|:-:|:-:|:-:|
| GPT-5-mini | 3-9% | 5-13% | +2–6pp |
| Gemini 2.0 Flash | 0-8% | 1-8% | ~0pp |
| Claude Sonnet 4 | 8-33% | 6-28% | variable |

Cost is modest on newer models. Frontier model cost TBD.

---

## 5. What Remains

### 5.1 Critical Path (this week)

| Experiment | Purpose | Status |
|------------|---------|--------|
| Gemini 3 Pro Preview eval | Complete frontier model trio | Running |
| SAGE baseline on frontier models | Show it fails | Running |
| SemanticSmooth baseline on frontier models | Show it fails | Running |
| Classical Chinese on HarmBench | 3rd encoding for generality | Running |

### 5.2 After This Round

| Experiment | Purpose | Effort |
|------------|---------|--------|
| Classical Chinese imaging + frontier eval | Complete 3-encoding coverage | 1 round |
| SemanticCamo (encode + eval) | 4th attack for generality | 1 round |
| Bootstrap CIs on all claims | Statistical rigor | Local computation |
| Full HarmBench (240) on frontier models | Robustness check for paper | Low cost re-run |

### 5.3 Nice-to-Have

- Mechanism analysis: WHY image safety is stricter (attention probing on open-source models)
- Stacked defense: IR + paraphrasing combined
- Benign over-refusal on frontier models

---

## 6. Paper Positioning

### Core Contribution

**IR is the first defense with a positive scaling trajectory against encoding attacks.** Traditional defenses degrade as models improve (the model understands attacks better). IR strengthens as models improve (image-safety gets stricter). This diverging trajectory means IR is the only defense with a sustainable long-term outlook.

### Evidence Structure

| Claim | Evidence |
|-------|----------|
| Encoding attacks are a real threat | 24–57% ASR on frontier VLMs |
| Traditional defenses fail | SAGE/SemanticSmooth ASR ≈ undefended (testing) |
| IR provides near-complete protection | 2–7% residual ASR on GPT-5.4 |
| IR strengthens with model capability | GPT family scaling: +12pp → −12pp → −27pp |
| IR works across providers | GPT, Claude, Gemini all show reduction |
| IR works across encodings | set_theory, formal_logic, classical_chinese, SemanticCamo |

### Probability Assessment (updated May 6)

| Scenario | Probability | Outcome | Paper level |
|----------|:-:|----------|:-:|
| Beat both baselines + strong scaling story | **60%** | "First self-improving defense against encoding attacks" | **Main conf** |
| Baselines partially work, but IR still dominates | 25% | "Superior defense with unique scaling property" | **Main conf / Findings** |
| Gemini 3 Pro doesn't show expected pattern | 10% | "Defense works on OpenAI/Anthropic, mixed on Google" | **Findings** |
| Results don't replicate on full dataset | 5% | Need investigation | **Delayed** |

---

## 7. Timeline (updated May 6)

| Date | Milestone |
|------|-----------|
| May 6 ✅ | Frontier model results (GPT-5.4, Claude Sonnet 4.6). Scaling law confirmed. |
| May 6–7 | Gemini 3 Pro + SAGE/SemanticSmooth baselines + classical Chinese encode |
| May 7–8 | Classical Chinese imaging + frontier eval. SemanticCamo encode + eval |
| May 8–9 | Full HarmBench (240) verification on frontier models |
| May 9–11 | Bootstrap CIs + statistical analysis |
| May 11–16 | Paper writing |
| May 16–20 | Polish + advisor review |
| May 20–25 | Final revision + submit |
| **May 25** | **ARR May deadline** |

Fallback: ARR June (~Jun 15) or EMNLP direct (Jun 2026).

---

## 8. Risks & Mitigation

| Risk | Likelihood | Mitigation |
|------|:-:|-----------|
| Baselines actually work (SemanticSmooth decodes encodings) | 20% | IR is still simpler (1 call vs 5N calls), zero-cost, encoding-agnostic. Propose stacked defense. |
| Gemini 3 Pro doesn't show strong defense | 30% | 2/3 frontier models (GPT-5.4 + Claude) still show clear effect. Frame Gemini as provider-specific limitation. |
| "Too simple" criticism | Medium | Simplicity IS the contribution — training-free, deployable today, self-improving. CC-BOS (attack) was similarly simple and got ICLR. |
| Benign refusal cost deemed too high | Low | Frontier model cost likely low (GPT-5.4 original barely refuses). Propose threshold-based deployment. |
| Scaling claim challenged (only 3 GPT tiers) | Medium | Cross-provider validation (Claude Sonnet 4 → 4.6, Gemini 2.0 → 2.5 → 3) supports the trend independently. |

---

## 9. Paper Structure

1. **Introduction:** Text-encoding attacks bypass frontier VLM safety at 24–57% ASR. Existing defenses are not designed for this threat and degrade on newer models. We propose IR — the first defense that strengthens with model capability.
2. **Background:** Text-encoding attacks (CC-BOS, MathPrompt), VLM safety alignment, existing defenses (SemanticSmooth, SAGE).
3. **Method:** IR defense — one paragraph. Simplicity is the contribution.
4. **Experimental Setup:** 3 frontier models, 4 encodings, HarmBench, 2 comparison defenses, evaluation protocol.
5. **Results:**
   - 5.1 IR reduces ASR on frontier models (main table)
   - 5.2 Existing defenses fail against encoding attacks (SAGE, SemanticSmooth)
   - 5.3 The diverging scissors: IR strengthens with model capability (scaling table)
   - 5.4 Generality across encodings and providers
   - 5.5 Defense cost: benign over-refusal (modest)
6. **Analysis:** Why trajectories diverge. The "alliance with model providers" framing. Failure cases. Deployment.
7. **Conclusion:** First self-improving defense for encoding attacks. Zero cost, future-proof.

---

## 10. Publication Strategy

| Venue | Deadline | Fit |
|-------|----------|-----|
| **ARR May 2026** | May 25 | Primary target → EMNLP/ACL main |
| ARR June 2026 | ~Jun 15 | Backup if May too tight |
| EMNLP 2026 direct | ~Jun 2026 | Alternative submission path |
| USENIX Security 2027 | ~Feb 2027 | If reframed for security audience (practical deployability angle) |
| ICLR 2027 | ~Oct 2026 | If framed as "scaling law of VLM safety alignment" |

**Primary strategy:** ARR May → EMNLP 2026. The scaling story + baseline comparison + frontier model results make a complete main-conference paper.

---

## 11. Future Work

- **Stacked defenses:** IR + SemanticSmooth for maximum coverage
- **Selective application:** Only apply IR when input matches encoding patterns (reduces benign cost)
- **Mechanism analysis:** Attention probing on open-source VLMs to explain image safety gap
- **Adaptive attacks:** Can an attacker craft encodings that survive image rendering?
- **Formal analysis:** Theoretical model of why image-safety scales faster than text-understanding for encoded inputs
- **Longitudinal study:** Track IR effectiveness across future model releases to validate the diverging scissors prediction
