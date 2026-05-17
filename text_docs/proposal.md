# Research Proposal: Evaluating and Composing Defenses Against Text-Encoding Attacks on VLMs

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

No systematic evaluation exists for **semantic-encoding attacks** (math notation, classical language, formal logic) against modern VLM defenses. Existing defenses target token-level perturbations (GCG, AutoDAN) or known image-attack patterns (FigStep). We study whether black-box defenses transfer to this threat class, including image rendering, self-discrimination prompting, paraphrasing, and hybrid compositions.

### Key Empirical Insight

- **ASR measurement validity (Chouldechova, NeurIPS 2025):** Bootstrap CIs required. Our 100-prompt evaluations with multiple encodings × models provide adequate statistical power.
- **JRS (2025):** Blank images alone shift representations +28pp toward jailbreaking on open-source models — image modality affects safety processing at the representation level.

---

## 1. Core Idea

**Defense Evaluation and Composition for Encoding Attacks on VLMs (updated May 16):**

The paper's final direction depends on experimental outcomes. Four directions are under investigation, ordered by scientific priority:

**Direction 1 — Defense composition (highest upside):** SAGE (text-level self-discrimination) is strong on frontier models (0-3% ASR) but may degrade on weaker/older models that cannot self-diagnose encoded attacks. If SAGE fails on 2+ weaker models and hybrid composition (IR+SAGE, SAGE+IR) fills the gap → defense-composition method paper.

**Direction 2 — Safety-utility tradeoff (supporting):** SAGE may over-refuse benign encoded inputs while IR (math encodings, 3-13% benign refusal observed) does not. If confirmed → IR offers a better deployment tradeoff even where SAGE wins on harmful ASR.

**Direction 3 — Modality flip (strong fallback):** IR transitions from attack amplifier on weaker/open-source models to defense on frontier models. This is already visible in existing data (GPT-5.4-nano: +12pp, Gemini 2.0 Flash: +6pp, Claude Sonnet 4 set_theory: +13pp vs. GPT-5.4: −22 to −32pp). If Qwen2.5-VL-7B and Pixtral-12B also show amplification → the regime-shift story holds across API tiers and open-source VLMs.

**Direction 4 — Empirical study (floor):** If SAGE works everywhere and no flip story holds → comprehensive benchmark evaluation paper.

**Scaling property (confirmed for GPT family):** GPT-5.4-nano +12pp → GPT-5.4-mini −5 to −19pp → GPT-5.4 −22 to −32pp. Image-safety alignment strengthens faster than text-safety within the GPT capability ladder. This is provider-dependent and should not be generalized across providers without qualification.

---

## 2. Research Questions

- **RQ1 (Defense Effectiveness):** When does IR reduce ASR of text-encoding attacks on VLMs?
- **RQ2 (Defense Cost):** What is the benign over-refusal increase from image rendering?
- **RQ3 (Comparison):** How do black-box defenses (IR, SAGE, SemanticSmooth) transfer to encoding attacks?
- **RQ4 (Generality):** Is the defense effective across models, encodings, and renderers?
- **RQ5 (Scaling):** Does defense effectiveness change with model capability?

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

The defense tests whether the VLM's image-safety alignment is stricter than its text-safety alignment. On some frontier models this routing sharply reduces ASR; on other providers or weaker models, the effect is smaller or can reverse.

Properties:
- Training-free: no fine-tuning or additional models
- Encoding-agnostic implementation: does not require a detector for a specific encoding
- Black-box: works with API-only VLM access
- No additional model call: same target model, different input modality
- Capability-dependent: strongest when the target model has mature image-safety alignment

### 3.3 Comparison Defenses

| Defense | Venue | Mechanism | Actual effectiveness |
|---------|-------|-----------|---------------------|
| SemanticSmooth | AACL-IJCNLP 2025 | LLM paraphrases input N times + majority vote | Mixed — reduces ASR on GPT-5.4 and classical_chinese, but is weak or slightly harmful on some Claude conditions |
| SAGE | ACL Findings 2025 | Self-discrimination prompt: model judges safety before answering | **Strong** — achieves 0-3% ASR on frontier models (contra expectations) |
| **IR** | — | Render text as image → VLM's image-safety alignment filters it | Strong on GPT-5.4 (2-13% ASR), inconsistent across providers and model tiers |
| **SAGE+IR (ours)** | — | SAGE wraps text → render as image → double modality safety | Pending — tests whether safety instructions still work through image modality |
| **IR+SAGE (ours)** | — | Render as image → SAGE safety instructions as system prompt | Improves IR on Claude, but does not beat SAGE on frontier models |

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

## 4. Results (as of May 13, 2026)

### 4.1 Frontier Model IR Defense

| Model | Encoding | Text ASR | Image ASR | Δ (IR defense) |
|-------|----------|:--------:|:---------:|:-----------:|
| **GPT-5.4** | set_theory | 24% | 2% | **−22pp** |
| **GPT-5.4** | formal_logic | 39% | 7% | **−32pp** |
| **GPT-5.4** | classical_chinese | 32% | 13% | **−19pp** |
| Claude Sonnet 4.6 | set_theory | 8% | 16% | +8pp (FAILS) |
| Claude Sonnet 4.6 | formal_logic | 51% | 44% | −7pp |
| Claude Sonnet 4.6 | classical_chinese | 24% | 26% | +2pp |
| Gemini 3 Flash Preview | set_theory | 51% | 55% | +4pp |
| Gemini 3 Flash Preview | formal_logic | 70% | 64% | −6pp |

⚠️ Claude Sonnet 4.6 text ASR was corrected after the empty-response judge bug fix. After correction, IR is strongest on GPT-5.4, mixed on Claude, and mixed on Gemini.

### 4.2 SAGE Defense — Unexpectedly Strong

| Model | Encoding | No defense | SAGE | IR |
|-------|----------|:---:|:---:|:---:|
| GPT-5.4 | set_theory | 24% | **0%** | 2% |
| GPT-5.4 | formal_logic | 39% | **0%** | 7% |
| Claude Sonnet 4.6 | set_theory | 8% | **0%** | 16% |
| Claude Sonnet 4.6 | formal_logic | 51% | **3%** | 44% |
| Gemini 3 Pro Preview | set_theory | — | **0%** | — |
| Gemini 3 Pro Preview | formal_logic | — | **3%** | — |

SAGE achieves near-zero ASR on frontier models. This challenges the "baselines fail" hypothesis — SAGE's self-discrimination prompt is effective even against encoding attacks when the target model is sufficiently capable.

### 4.3 SemanticSmooth — Encoding-Dependent and Unstable

| Model | Encoding | No defense | SemanticSmooth |
|-------|----------|:---:|:---:|
| GPT-5.4 | set_theory | 24% | 7% |
| GPT-5.4 | formal_logic | 39% | 27% |
| GPT-5.4 | classical_chinese | 32% | 11% |
| Claude Sonnet 4.6 | set_theory | 8% | 12% (WORSE) |
| Claude Sonnet 4.6 | formal_logic | 51% | 42% |
| Claude Sonnet 4.6 | classical_chinese | 24% | 6% |

SemanticSmooth is not uniformly safe or unsafe. It helps on classical_chinese and GPT-5.4, but can be weak or slightly harmful on some Claude conditions. The main finding is instability across encodings and providers, not universal failure.

### 4.4 The Diverging Scissors (GPT Family Scaling)

| Model tier | set_theory Δ | formal_logic Δ | Trajectory |
|------------|:------------:|:--------------:|:----------:|
| GPT-5.4-nano (budget) | +12pp | −2pp | Defense FAILS |
| GPT-5.4-mini (mid) | −5pp | −19pp | Defense works |
| GPT-5.4 (frontier) | −22pp | −32pp | Defense DOMINANT |

Within the GPT family, IR defense goes from failing → working → near-perfect. This is the clearest scaling result, but it should not be generalized across all providers without qualification.

### 4.5 Cross-Provider IR Summary

| Model | Conditions where IR works | Average Δ |
|-------|:------------------------------:|:---------:|
| GPT-5.4 | 3/3 (100%) | −24pp |
| GPT-5.4-mini | 6/6 (100%) | −13pp |
| Gemini 2.5 Flash Lite | 2/2 (100%) | −16pp |
| Gemini 2.5 Flash | 4/6 (67%) | −7pp |
| Claude Sonnet 4.6 | 1/3 (33%) | +1pp |
| GPT-5.4-nano | 0/2 (0%) | +5pp |
| Gemini 2.0 Flash | 1/5 (20%) | +4pp |

### 4.6 Defense Cost (benign over-refusal)

| Model | text refusal | image refusal | Cost |
|-------|:-:|:-:|:-:|
| GPT-5-mini | 3-9% | 5-13% | +2–6pp |
| Gemini 2.0 Flash | 0-8% | 1-8% | ~0pp |
| Claude Sonnet 4 | 8-33% | 6-28% | variable |

Frontier model benign cost remains incomplete and should be measured before making deployment claims.

---

## 5. What Remains (updated May 13)

### 5.1 Critical Path

| Experiment | Purpose | Status |
|------------|---------|--------|
| **Stage 10e: SAGE on older models** | Does SAGE fail on weaker models? Key to paper story. | NEXT |
| Stage 10e: IR+SAGE + SAGE+IR on older models | Does hybrid beat both on weaker models? | After SAGE results |
| Stage 10d: SAGE+IR on frontier | Complete hybrid comparison on frontier models | Pending (imaging done) |

### 5.2 Completed (May 9–13)

| Experiment | Result |
|------------|--------|
| IR+SAGE on frontier (GPT-5.4, Claude 4.6) | Does NOT beat SAGE (0-10% vs 0-3%) |
| Classical Chinese on frontier | GPT-5.4: −19pp. Claude: no effect (+2pp). |
| SemanticSmooth on classical_chinese | Works (−18 to −21pp) — unlike formal_logic |
| SAGE defense_transform | 3 encoding outputs ready for hybrid pipeline |
| Gemini 2.5 Pro (partial) | 2/4 done, others timeout |

### 5.3 After Core Experiments

| Experiment | Purpose | Effort |
|------------|---------|--------|
| Bootstrap CIs on all claims | Statistical rigor | Local computation |
| Full HarmBench (240) on frontier models | Robustness check for paper | Low cost re-run |
| Benign over-refusal on frontier models | Defense cost measurement | ~12 tasks |
| SemanticCamo (4th attack) | Generality | 1 round |

### 5.4 Blockers

- **OpenAI API**: Account warned, appeal failed. Cannot submit harmful prompts.
- **Google API**: Account warned. Gemini batch tasks may be blocked.
- **Claude API**: Still working.

---

## 6. Paper Positioning

### Core Contribution (revised May 16)

**Original claim ("baselines fail") is DISPROVEN** — SAGE is effective (0% ASR on GPT-5.4). Four possible paper framings, ordered by priority:

**Option A (if D1 succeeds): Defense Composition Paper**
- Hybrid defense (IR+SAGE or SAGE+IR) beats SAGE on weaker models where SAGE degrades
- SAGE reliability is capability-dependent; composition provides cross-tier robustness
- Scaling law: IR and SAGE both strengthen with model capability within GPT family

**Option B (if D3 confirmed): Modality Regime-Shift Paper**
- IR transitions from attack amplifier (open-source/weaker models) to defense (frontier models)
- Explains contradictions between FigStep-era image attacks and modern IR defense results
- Practical warning: applying IR as a defense on open-source VLMs increases attack surface

**Option C (D2 as support):** In either A or B, add a safety-utility tradeoff section showing SAGE's benign over-refusal cost vs. IR's lower cost on benign inputs.

**Option D (floor): Empirical Study Paper**
- First systematic evaluation of encoding attacks × 10+ models × 3 defenses × 3 benchmarks
- Novel findings: modality safety asymmetry, SAGE effectiveness, SemanticSmooth instability, GPT-family scaling law

### Evidence Structure (updated)

| Claim | Evidence |
|-------|----------|
| Encoding attacks are a real threat | 24–39% ASR on frontier VLMs (GPT-5.4) |
| SAGE is effective (contra prior expectations) | 0% ASR on GPT-5.4 with set_theory and formal_logic |
| SemanticSmooth is unstable | Helps on classical_chinese, weak/slightly harmful on some Claude set_theory conditions |
| IR provides strong protection on GPT-5.4 | 2–13% residual ASR across three encodings |
| IR is inconsistent across providers | Fails or weakens on Claude set_theory/classical_chinese and Gemini set_theory |
| IR+SAGE improves IR on Claude | Claude formal_logic: 44% → 10%, but still worse than SAGE |
| Defense scales with model capability | GPT family: nano fails, mini works, full is strongest |

### Probability Assessment (updated May 16)

| Direction | Experiment needed | Probability | If confirmed | Paper level |
|-----------|-------------------|:-----------:|-------------|:-----------:|
| **D1: Hybrid beats SAGE on weaker models** | Stage 10e SAGE + hybrid | 25% | Method contribution: defense composition | **EMNLP Main / Findings** |
| **D2: IR wins on benign tradeoff** | Stage 12 SAGE benign refusal | 45% | Supporting story (safety-utility) | **Findings / AIES** |
| **D3: Modality flip confirmed on open-source** | Stage 16 Qwen + Pixtral | 65% | Empirical finding: regime-shift story | **EMNLP Findings / AIES** |
| **D4: SAGE wins everywhere, no flip** | (already partially confirmed) | 35% | Empirical study only | **AIES / Workshop** |

Note: D1 and D3 are not mutually exclusive — D1 can serve as the method contribution while D3 provides the scientific framing. D2 is best as a supporting section within D1 or D3.

---

## 7. Timeline (updated May 13)

| Date | Milestone |
|------|-----------|
| May 1–6 ✅ | Data, encoding, imaging, JBB/HarmBench eval on 8 models, renderer exploration |
| May 6 ✅ | Frontier IR results (GPT-5.4, Claude Sonnet 4.6). Scaling law confirmed. |
| May 7 ✅ | SAGE/SemanticSmooth baselines — SAGE unexpectedly strong (0% ASR). Judge bug discovered. |
| May 8 ✅ | Judge bug fixed. Pivot to hybrid defense. Code refactored (defense_transform mode). |
| May 9 ✅ | IR+SAGE on frontier (does NOT beat SAGE), CC eval, SemanticSmooth CC, SAGE transform |
| May 13 | Pivot to testing older models. API accounts restricted (OpenAI, Google). |
| May 14–16 | **Stage 10e: SAGE + hybrids on older models** (resolve API access first) |
| May 16–20 | Complete experiments + statistical analysis |
| May 20–25 | Paper writing |
| **May 25** | **ARR deadline (EMNLP or AIES)** |

Fallback: ARR June (~Jun 15) or EMNLP direct (Jun 2026).

---

## 8. Risks & Mitigation

| Risk | Likelihood | Mitigation |
|------|:-:|-----------|
| Hybrid defense shows no benefit over SAGE anywhere (D1 fails) | 75% | Pivot to D3 modality-flip story or D4 empirical study |
| Open-source VLMs also show IR defense, not amplification (D3 weakens) | 35% | IR provider-dependency story still holds across API tiers alone |
| "Too simple" criticism | Medium | CC-BOS (ICLR 2026) was similarly simple; empirical novelty is sufficient for Findings |
| Reviewers say "just use SAGE" | HIGH if D1 fails | D3 reframes: the question is not "which defense wins" but "when does each defense fail" |
| SemanticSmooth finding is too mixed | Medium | Present as instability, not danger; instability is the finding |
| Scaling claim challenged (mostly GPT-family) | Medium | State as GPT-family result; cross-provider heterogeneity is a separate finding |
| API access restrictions block Stage 10e | MEDIUM | New accounts being obtained; Stage 16 (cluster) and Claude Sonnet 4 unblocked now |

---

## 9. Paper Structure (revised May 9)

1. **Introduction:** Text-encoding attacks achieve 24–39% ASR on GPT-5.4 and up to 51–70% on some Claude/Gemini frontier conditions. We study defenses: individual (SAGE, IR) and composed (SAGE+IR, IR+SAGE). Key findings: SAGE is effective on frontier models, IR is strong but provider-dependent, SemanticSmooth is unstable, and defense behavior changes with model capability.
2. **Background:** Text-encoding attacks (CC-BOS, MathPrompt, formal logic), VLM safety alignment, existing defenses (SemanticSmooth, SAGE), modality safety asymmetry.
3. **Method:** Defense strategies — IR (modality switching), SAGE (self-discrimination), and two hybrid compositions. Implementation of defense_transform pipeline for composability.
4. **Experimental Setup:** 3 frontier models, 3-4 encodings, HarmBench (100/240), 4 defense configurations, evaluation protocol.
5. **Results:**
   - 5.1 Encoding attacks on frontier VLMs (attack success table)
   - 5.2 Individual defenses: SAGE strong, IR strong on OpenAI, SemanticSmooth dangerous
   - 5.3 Defense composition: IR+SAGE improves IR but does not beat SAGE on frontier models; SAGE+IR pending
   - 5.4 Scaling with model capability (diverging scissors)
   - 5.5 Generality across encodings and providers
   - 5.6 Defense cost: benign over-refusal
6. **Analysis:** Why SAGE works (self-discrimination effective even on encoded text). Why SemanticSmooth is unstable across encodings/providers. Why IR is provider-dependent. Deployment recommendations.
7. **Conclusion:** First systematic evaluation of black-box defenses against encoding attacks. Practical recommendations for production VLM safety.

---

## 10. Publication Strategy (updated May 13)

| Venue | Deadline | P(accept) | Fit |
|-------|----------|:---------:|-----|
| **EMNLP 2026 (via ARR)** | May 25 | ~30-35% (main+Findings) | Higher prestige; needs stronger method story |
| **AIES 2026** | May 25 (same cycle) | ~40-55% | Natural fit for safety findings; lower prestige |
| ARR June 2026 | ~Jun 15 | — | Backup if May too tight |
| USENIX Security 2027 | ~Feb 2027 | — | If reframed for security audience |

**Decision:** EMNLP gives a higher-upside NLP venue, but needs a stronger method story. AIES is safer and naturally fits the empirical safety framing. If Stage 10e hybrid results are strong → EMNLP. If SAGE wins everywhere → AIES is safer and more coherent.

---

## 11. Future Work

- **Adaptive attacks against SAGE:** Can an encoding defeat SAGE's self-discrimination? (Potential separate attack paper)
- **Three-way composition:** SAGE + IR + SemanticSmooth — does paraphrasing help when combined with other defenses?
- **Selective application:** Route through IR only when encoding is detected (reduces benign cost)
- **Mechanism analysis:** Attention probing on open-source VLMs to explain image safety gap and SAGE effectiveness
- **Longitudinal study:** Track defense effectiveness across future model releases
- **Broader attack evaluation:** Test defenses against newer attacks (MIDAS multi-image, Text-DJ decomposition)
