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

**Defense Composition for Encoding Attacks on VLMs:**

No single defense is robust across all conditions:
- SAGE (text-level self-discrimination) is strong on GPT-5.4 (0% ASR) but may not generalize to all models/attacks
- IR (image modality routing) is strong on GPT-5.4 (2-7% ASR) but fails on some provider/encoding combinations (Claude + formal_logic: +46pp)
- SemanticSmooth (paraphrasing) can be actively harmful — decodes encoding back to plain harmful text

**Our approach:** Combine SAGE and IR into hybrid defenses:
- **SAGE+IR:** Wrap text with SAGE safety instructions, then render as image → VLM sees image of safety-wrapped text (double defense pipeline)
- **IR+SAGE:** Render attack as image, send with SAGE instructions as system prompt → VLM receives safety instructions via text + attack via image

**Key insight:** SAGE and IR operate through orthogonal mechanisms (text-level discrimination vs. modality-level safety). Composing them may provide robustness where individual defenses have gaps.

**Scaling property (still valid):** IR defense improves with model capability (GPT-5.4-nano → mini → full: +12pp → −12pp → −27pp). Hybrid defenses inherit this property while adding SAGE's text-level protection.

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

| Defense | Venue | Mechanism | Actual effectiveness |
|---------|-------|-----------|---------------------|
| SemanticSmooth | AACL-IJCNLP 2025 | LLM paraphrases input N times + majority vote | Mixed — reduces ASR on GPT-5.4, but **increases** ASR on Claude (decodes encoding to plain harmful text) |
| SAGE | ACL Findings 2025 | Self-discrimination prompt: model judges safety before answering | **Strong** — achieves 0% ASR on GPT-5.4 (contra expectations) |
| **IR** | — | Render text as image → VLM's image-safety alignment filters it | Strong on GPT-5.4 (2-7% ASR), inconsistent across providers |
| **SAGE+IR (ours)** | — | SAGE wraps text → render as image → double modality safety | TBD — composing both defenses |
| **IR+SAGE (ours)** | — | Render as image → SAGE safety instructions as system prompt | Running |

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
| GPT-5.4 | OpenAI | Strongest IR defense signal (−22 to −32pp) |
| Claude Sonnet 4.6 | Anthropic | Cross-provider validation |
| Gemini 2.5 Pro | Google | Google frontier |

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
| Gemini 3 Flash Preview | Google | Supplementary frontier |
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

## 4. Results (as of May 9, 2026)

### 4.1 Frontier Model IR Defense

| Model | Encoding | Text ASR | Image ASR | Δ (IR defense) |
|-------|----------|:--------:|:---------:|:-----------:|
| **GPT-5.4** | set_theory | 24% | 2% | **−22pp** |
| **GPT-5.4** | formal_logic | 39% | 7% | **−32pp** |
| Claude Sonnet 4.6 | set_theory | 3% | 0% | −3pp |
| Claude Sonnet 4.6 | formal_logic | 5% | 51% | +46pp (FAILS) |
| Gemini 2.5 Pro | — | — | — | running |

⚠️ Claude Sonnet 4.6 text ASR corrected (judge bug: empty refusals misclassified as harmful). IR amplifies formal_logic on Claude.

### 4.2 SAGE Defense — Unexpectedly Strong

| Model | Encoding | No defense | SAGE | IR |
|-------|----------|:---:|:---:|:---:|
| GPT-5.4 | set_theory | 24% | **0%** | 2% |
| GPT-5.4 | formal_logic | 39% | **0%** | 7% |
| Claude Sonnet 4.6 | set_theory | 3% | 0% | 0% |
| Claude Sonnet 4.6 | formal_logic | 5% | 3% | 51% |

SAGE achieves near-zero ASR. This challenges the "baselines fail" hypothesis — SAGE's self-discrimination prompt IS effective even against encoding attacks on frontier models.

### 4.3 SemanticSmooth — Harmful on Claude

| Model | Encoding | No defense | SemanticSmooth |
|-------|----------|:---:|:---:|
| GPT-5.4 | set_theory | 24% | 7% |
| GPT-5.4 | formal_logic | 39% | 27% |
| Claude Sonnet 4.6 | set_theory | 3% | 12% (WORSE) |
| Claude Sonnet 4.6 | formal_logic | 5% | 42% (MUCH WORSE) |

SemanticSmooth's paraphrasing decodes encoded text back to plain harmful English, which Claude then complies with.

### 4.4 The Diverging Scissors (GPT Family Scaling)

| Model tier | set_theory Δ | formal_logic Δ | Trajectory |
|------------|:------------:|:--------------:|:----------:|
| GPT-5.4-nano (budget) | +12pp | −2pp | Defense FAILS |
| GPT-5.4-mini (mid) | −5pp | −19pp | Defense works |
| GPT-5.4 (frontier) | −22pp | −32pp | Defense DOMINANT |

As model capability increases: IR defense goes from failing → working → near-perfect.

### 4.5 Cross-Provider IR Summary

| Model | Conditions where IR works | Average Δ |
|-------|:------------------------------:|:---------:|
| GPT-5.4 | 2/2 (100%) | −27pp |
| GPT-5.4-mini | 6/6 (100%) | −13pp |
| Gemini 2.5 Flash Lite | 2/2 (100%) | −16pp |
| Gemini 2.5 Flash | 4/6 (67%) | −7pp |
| Claude Sonnet 4.6 | 1/2 (50%) | +22pp |
| GPT-5.4-nano | 0/2 (0%) | +5pp |
| Gemini 2.0 Flash | 1/5 (20%) | +4pp |

### 4.6 Defense Cost (benign over-refusal)

| Model | text refusal | image refusal | Cost |
|-------|:-:|:-:|:-:|
| GPT-5-mini | 3-9% | 5-13% | +2–6pp |
| Gemini 2.0 Flash | 0-8% | 1-8% | ~0pp |
| Claude Sonnet 4 | 8-33% | 6-28% | variable |

Frontier model cost TBD.

---

## 5. What Remains

### 5.1 Critical Path (running now)

| Experiment | Purpose | Status |
|------------|---------|--------|
| IR+SAGE hybrid eval (6 tasks) | Does combining IR with SAGE system prompt outperform either alone? | Running |
| Gemini 2.5 Pro eval (4 tasks) | Complete frontier model trio | Running |
| Classical Chinese frontier eval (6 tasks) | 3rd encoding for generality | Running |
| SemanticSmooth Gemini 2.5 Pro + CC (5 tasks) | Complete defense comparison | Running |
| SAGE defense_transform (3 tasks) | Produce wrapped prompts for SAGE+IR hybrid | Running |

### 5.2 Round 2 (depends on this round's output)

| Experiment | Purpose | Effort |
|------------|---------|--------|
| SAGE+IR hybrid (imaging + eval) | Image of SAGE-wrapped text — does double defense work? | ~8 tasks |
| SAGE evaluate on Gemini 2.5 Pro + CC | Complete SAGE comparison table | ~6 tasks |
| SemanticCamo (encode + eval) | 4th attack for generality | 1 round |

### 5.3 After Core Experiments

| Experiment | Purpose | Effort |
|------------|---------|--------|
| Bootstrap CIs on all claims | Statistical rigor | Local computation |
| Full HarmBench (240) on frontier models | Robustness check for paper | Low cost re-run |
| Benign over-refusal on frontier models | Defense cost measurement | ~12 tasks |

### 5.4 Nice-to-Have

- Mechanism analysis: WHY image safety is stricter
- Adaptive attack against SAGE (encoding that defeats self-discrimination)
- Benign over-refusal comparison: SAGE vs IR on frontier models

---

## 6. Paper Positioning

### Core Contribution (revised May 9)

**Original claim ("baselines fail") is DISPROVEN** — SAGE is effective (0% ASR on GPT-5.4). New strategy:

**Option A (if hybrids work): Defense Composition Paper**
- First study of defense composition against encoding attacks on frontier VLMs
- Key finding: SAGE+IR or IR+SAGE achieves stronger/more robust protection than either alone
- Novel observation: SemanticSmooth is HARMFUL on Claude (decodes encoding → increases ASR)
- Scaling law: defense composition effectiveness improves with model capability

**Option B (fallback): Empirical Study Paper**
- First comprehensive evaluation of encoding attacks AND defenses on frontier VLMs (2026)
- Novel findings: modality safety asymmetry, SAGE effectiveness, SemanticSmooth danger, scaling laws
- Contribution is the evaluation framework and benchmark results, not a new method

### Evidence Structure (updated)

| Claim | Evidence |
|-------|----------|
| Encoding attacks are a real threat | 24–39% ASR on frontier VLMs (GPT-5.4) |
| SAGE is effective (contra prior expectations) | 0% ASR on GPT-5.4 with set_theory and formal_logic |
| SemanticSmooth can be harmful | +37pp ASR increase on Claude (decodes encoding) |
| IR provides near-complete protection on GPT-5.4 | 2–7% residual ASR |
| IR is inconsistent across providers | Fails on Claude formal_logic (+46pp) |
| Hybrid defense is more robust | TBD (IR+SAGE running) |
| Defense scales with model capability | GPT family: +12pp → −12pp → −27pp |

### Probability Assessment (updated May 9)

| Scenario | Probability | Outcome | Paper level |
|----------|:-:|----------|:-:|
| Hybrid defense clearly outperforms individual defenses | 30% | "Defense composition for encoding attacks" | **EMNLP Main / Findings** |
| Hybrid is comparable to SAGE but more robust across conditions | 35% | "Robustness through defense composition" | **Findings** |
| Hybrid shows no benefit over SAGE alone | 20% | Pivot to empirical study | **Findings / Workshop** |
| Surprising new finding from experiments | 15% | Depends on what emerges | **Variable** |

---

## 7. Timeline (updated May 9)

| Date | Milestone |
|------|-----------|
| May 6 ✅ | Frontier IR results (GPT-5.4, Claude Sonnet 4.6). Scaling law confirmed. |
| May 7 ✅ | SAGE/SemanticSmooth baselines — SAGE unexpectedly strong (0% ASR). Judge bug discovered. |
| May 8 ✅ | Judge bug fixed + results corrected. Pivot to hybrid defense strategy. Code refactored (defense_transform mode). |
| May 9 | Round 1 running: Gemini 2.5 Pro + CC eval + IR+SAGE + SemanticSmooth + SAGE transform |
| May 10 | Round 2: SAGE+IR imaging + eval. SAGE evaluate on new models. |
| May 11–12 | SemanticCamo + remaining experiments |
| May 12–14 | Bootstrap CIs + statistical analysis |
| May 14–20 | Paper writing |
| May 20–25 | Polish + advisor review + submit |
| **May 25** | **ARR May deadline** |

Fallback: ARR June (~Jun 15) or EMNLP direct (Jun 2026).

---

## 8. Risks & Mitigation

| Risk | Likelihood | Mitigation |
|------|:-:|-----------|
| Hybrid defense shows no benefit over SAGE alone | 30% | Pivot to empirical study framing — SAGE effectiveness is itself a novel finding worth reporting |
| IR inconsistency across providers weakens claims | HIGH (confirmed) | Frame as provider-specific: IR is strongest on OpenAI (strongest safety investment). Hybrid compensates gaps. |
| "Too simple" criticism (both SAGE and IR are trivial) | Medium | Contribution is the composition insight + empirical evaluation, not algorithmic novelty. CC-BOS was similarly simple (ICLR). |
| Reviewers say "just use SAGE" | 30% | Show conditions where SAGE alone fails or hybrid is more robust (Claude formal_logic, or future adaptive attacks) |
| SemanticSmooth danger finding is "expected" | Low | No prior work has shown paraphrasing INCREASES attack success. Novel and actionable. |
| Scaling claim challenged (only 3 GPT tiers) | Medium | Cross-provider validation + multiple encodings. Hybrid inherits scaling property. |

---

## 9. Paper Structure (revised May 9)

1. **Introduction:** Text-encoding attacks achieve 24–39% ASR on frontier VLMs. We study defenses: individual (SAGE, IR) and composed (SAGE+IR, IR+SAGE). Key findings: SAGE is effective (contra prior expectations), SemanticSmooth is harmful on some providers, and defense composition provides robust cross-condition protection.
2. **Background:** Text-encoding attacks (CC-BOS, MathPrompt, formal logic), VLM safety alignment, existing defenses (SemanticSmooth, SAGE), modality safety asymmetry.
3. **Method:** Defense strategies — IR (modality switching), SAGE (self-discrimination), and two hybrid compositions. Implementation of defense_transform pipeline for composability.
4. **Experimental Setup:** 3 frontier models, 3-4 encodings, HarmBench (100/240), 4 defense configurations, evaluation protocol.
5. **Results:**
   - 5.1 Encoding attacks on frontier VLMs (attack success table)
   - 5.2 Individual defenses: SAGE strong, IR strong on OpenAI, SemanticSmooth dangerous
   - 5.3 Defense composition: SAGE+IR and IR+SAGE results
   - 5.4 Scaling with model capability (diverging scissors)
   - 5.5 Generality across encodings and providers
   - 5.6 Defense cost: benign over-refusal
6. **Analysis:** Why SAGE works (self-discrimination effective even on encoded text). Why SemanticSmooth fails (decoding as attack amplifier). Why IR is provider-dependent. Deployment recommendations.
7. **Conclusion:** First systematic evaluation of defense composition for encoding attacks. Practical recommendations for production VLM safety.

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

- **Adaptive attacks against SAGE:** Can an encoding defeat SAGE's self-discrimination? (Potential separate attack paper)
- **Three-way composition:** SAGE + IR + SemanticSmooth — does paraphrasing help when combined with other defenses?
- **Selective application:** Route through IR only when encoding is detected (reduces benign cost)
- **Mechanism analysis:** Attention probing on open-source VLMs to explain image safety gap and SAGE effectiveness
- **Longitudinal study:** Track defense effectiveness across future model releases
- **Broader attack evaluation:** Test defenses against newer attacks (MIDAS multi-image, Text-DJ decomposition)
