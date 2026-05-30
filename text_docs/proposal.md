# Research Proposal: Image Rendering as a Defense Destroyer for Text-Encoding Attacks on VLMs

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

No published method positions itself as a **defense destroyer** — a wrapper applied on top of an existing attack to defeat advanced black-box defenses uniformly. Prior work focuses on adaptive attacks against a specific defense or on stronger base attacks; the "wrapper that breaks arbitrary defenses for an arbitrary encoded attack" category is unexplored. We instantiate this category with Image Rendering (IR) and demonstrate that `ir_plain`-wrapped encoded attacks defeat three advanced defenses (SAGE, ECSO, SemanticSmooth) that successfully block the bare encoded attacks.

### Key Empirical Insight

- **ASR measurement validity (Chouldechova, NeurIPS 2025):** Bootstrap CIs required. Our 100-prompt evaluations with multiple encodings × models provide adequate statistical power.
- **JRS (2025):** Blank images alone shift representations +28pp toward jailbreaking on open-source models — image modality affects safety processing at the representation level.

---

## 1. Core Idea

**Image Rendering as a Defense Destroyer for Text-Encoding Attacks on VLMs (regrouped May 23):**

The project is reframed around a single centerpiece: IR is a **defense destroyer** — neither attack nor defense in isolation, but a wrapper that converts otherwise-blocked text-encoded attacks into successful ones against advanced black-box defenses. Two directions are archived as dead; D1 is rebuilt around the destroyer claim, with D2/D3/D4 as supporting or optional directions.

### Dead directions (archived)

- **DD1 (was D1) — Defense composition beats SAGE.** Premise: hybrid IR+SAGE_system_prompt or SAGE+IR reduces ASR below SAGE on weaker/older models. **Data refutes this in every (model, encoding) cell of P2.** SAGE text-mode is ≤ IR+SAGE_sys everywhere; composition never wins. Worst case for SAGE is Gemini 2.5 Flash Lite formal_logic where SAGE 28% vs IR+SAGE_sys 42% — SAGE still wins. Bury the composition-defense story.
- **DD2 (was D4) — SAGE wins everywhere, comprehensive empirical study floor.** By definition the contingency, not actively pursued. Demoted to fallback if D1–D3 collapse.

### Active directions (regrouped May 23 — D1 reframed as IR-based defense destroyer)

Conceptual shift: IR is **neither an attack nor a defense in isolation**. As an attack, text+IR ASR ≤ text-only ASR on undefended models — IR alone does not boost attack success. As a defense, IR beats SemanticSmooth but loses to SAGE — not a reliable defense either. The right framing is that IR is a **defense destroyer**: a wrapper applied on top of an existing text-encoded attack that converts otherwise-blocked attacks into successful ones against advanced black-box defenses. This is a new category of method — no prior published work proposes a defense destroyer — so the baseline is the pure (un-wrapped) attack under each defense rather than competing with prior destroyer methods. D2 (MM-SAGE defense) and the cost analysis (D3 over-refusal Pareto) become optional supporting directions; the old D1c adaptive text-mode attack track becomes a separate optional side bet, unrelated to the defense-destroyer spine.

---

**D1 — IR-based defense destroyer for text-encoding attacks (centerpiece contribution; first in category):**

The paper's central contribution is to establish a new category of attack-wrapping method — the *defense destroyer* — and demonstrate its effectiveness against three advanced black-box defenses (SAGE, ECSO, SemanticSmooth) chosen for cross-family coverage.

**Core claim:**
For each defense D ∈ {SAGE, ECSO, SemanticSmooth} and each encoded attack A:
- `ASR(A | no defense)` is moderate to high (encoded attacks work on undefended VLMs)
- `ASR(A | D)` is low (D successfully defends against the bare encoded attack)
- `ASR(IR(A) | D) ≫ ASR(A | D)` (wrapping the attack with IR destroys D's defense)
- `ASR(IR(A) | no defense) ≈ ASR(A | no defense)` (IR is neutral on undefended models — destroyer effect is *defense-specific*, not a generic ASR boost)

The gap `ASR(IR(A) | D) − ASR(A | D)` quantifies destroyer effectiveness against each defense.

**Why "first in category" is a legitimate framing, not a baseline gap:**
There is no published defense-destroyer method to beat — wrappers like IR have not previously been studied as defense bypasses. The baseline for each headline row is the pure encoded attack under the same defense, not a prior destroyer. The contribution is establishing the category and demonstrating its effectiveness, not exceeding a prior destroyer's gap.

**Headline evaluation grid:**
- {4 encodings} × {3 defenses: SAGE, ECSO, SemanticSmooth} × {pure attack, IR-wrapped attack} × {target VLMs}
- Primary metric per cell: ASR gap induced by IR wrapping under each defense
- Secondary: undefended `ASR(IR(A))` vs `ASR(A)` confirms IR is neutral without a defense (rules out the trivial "IR is just a stronger attack" interpretation)

**Mechanism per defense (paper narrative; not part of headline table):**
- *SAGE* (self-discrimination prompting on input text): the discrimination wrapper receives an image, not the encoded harmful string, so the discrimination step has no explicit text to flag. SAGE's text-level reasoning cannot perturb or analyze pixels-as-text.
- *ECSO* (caption-then-check): the captioning step recovers the *encoded* text from the image, then runs a text safety check. The safety check fails for the same reason the bare encoded attack defeats text-level safety alignment — the destroyer just routes the attack through a pipeline whose final check is the weak one.
- *SemanticSmooth* (paraphrase + majority vote): paraphrasing image input requires first reconstructing text (OCR-style), and the paraphrased outputs preserve the encoded structure — majority vote then still ratifies the encoded attack. Same root cause as ECSO, different defense mechanism.

**Supporting ablations (NOT main result):**
- *Trivial destroyer baselines*: plain screenshot of the attack (no encoding), attack rendered with no IR-style processing, random/blank companion image. Shows the destruction is specific to IR-rendered encoded text, not an artifact of any image input. Strengthens the mechanism claim but does not appear in the headline.
- *Cross-defense generality*: do all three defenses break by the same gap, or do some resist? Differential gap patterns illuminate which defense mechanisms are robust to which destroyer properties.

**Status:** SAGE branch has substantial data from Stage 10e Round 1 (see §4.7: Gemini 2.5 Flash Lite set_theory SAGE 3% → IR-wrapped 42%). ECSO and SemanticSmooth branches require running on the same encoding × model grid. The 3-defense × {pure, IR-wrapped} × multiple VLMs matrix is the gating experiment. Pipeline supports all three defenses already (`semantic_smooth` is in the defender factory; ECSO is the new addition).

---

**D2 — MM-SAGE: multimodal-native SAGE variant (defense-side method, NEW):**
Build a multimodal-native SAGE that closes the D1a (and D1b where applicable) gap on mid-tier models without breaking frontier performance. Candidate mechanisms in order of implementation cost: (i) *wrap-in-user-message* — move SAGE instructions from system prompt to user message alongside image (trivial code change); (ii) *OCR-then-wrap* — model OCRs the image, then applies SAGE-style discrimination to extracted text (1 week, 2 model calls per query); (iii) *joint multimodal safety reasoning* over (image, decoded text). Target: close the 11–29pp gap on Gemini-flash family while preserving 0–5pp on frontier. Required to lift the paper from analytical to method-contributing.

**D3 — Safety-utility tradeoff via OR-Bench benign (supporting Pareto):**
Run SAGE / IR / IR+SAGE_system_prompt / SemanticSmooth on OR-Bench benign + JBB benign across 2–3 models. Plot the (harmful ASR, benign refusal) Pareto frontier. SAGE's wrapper aggressively flags "implicit harm" and "nested innocent tasks" — exactly the language OR-Bench's deliberately ambiguous prompts trigger. If SAGE over-refuses → clean safety-helpfulness narrative. Cheapest decisive experiment; run first.

**D4 — IR-as-defense scaling within the GPT family (supporting empirical):**
Within GPT: nano +12pp (IR amplifies) → mini −5 to −19pp (IR defends) → 5.4 −22 to −32pp (IR dominant). Clean within-family scaling. Cross-provider story (Gemini, Claude) is mixed and reported only with qualification. Already supported by existing data; requires no new experiments — repositioned as a supporting section.

---

**Scaling property (confirmed for GPT family, supports D4):** GPT-5.4-nano +12pp → GPT-5.4-mini −5 to −19pp → GPT-5.4 −22 to −32pp. Image-safety alignment strengthens faster than text-safety within the GPT capability ladder. Provider-dependent — should not be generalized across providers without qualification.

### Execution order

By **what drives the main paper claim**, not what is cheapest. The gating experiment is the **destroyer matrix**: pure attack vs IR-wrapped attack across {SAGE, ECSO, SemanticSmooth} × {target VLMs}. D3 runs in parallel as supporting; D2 lifts the paper from analytical to method-contributing.

1. **Destroyer matrix — SAGE branch** on Qwen2.5-VL-7B + Pixtral-12B (cluster, free); more API models if access restored. SAGE branch is already partially supported by Stage 10e Round 1 data (§4.7).
2. **Destroyer matrix — ECSO branch** on the same VLMs. Requires implementing ECSO in the defender factory (captioning + safety check pipeline).
3. **Destroyer matrix — SemanticSmooth branch** on the same VLMs. Pipeline already supports `semantic_smooth` defender.
4. *(Concurrent)* **Trivial destroyer ablation** on a smaller grid: plain screenshot of attack, attack-as-image without IR-style rendering. Shows specificity of IR-rendered encoded text. **Supporting ablation, not headline.**
5. *(Concurrent)* **Mechanistic hidden-state analysis** on Qwen / Pixtral — confirm per-defense mechanism narrative.
6. **D3 over-refusal** runs in parallel — Claude API + benign benchmarks don't compete with cluster harmful jobs. Supporting only; doesn't gate the paper.
7. **D2 MM-SAGE wrap-in-user-message variant** — optional bonus; start only after destroyer matrix confirms SAGE branch generalizes.
8. **D4** — pure writing, no experiments.
9. **Adaptive text-mode attacks against SAGE** (old D1c) — speculative parallel sidecar, unrelated to destroyer spine. Do not bet the paper on it.

---

## 2. Research Questions

- **RQ1 (Defense Destroyer — main):** Does wrapping a text-encoded attack with Image Rendering (IR) defeat advanced black-box defenses (SAGE, ECSO, SemanticSmooth) that successfully block the bare encoded attack? *(D1)*
- **RQ2 (Destroyer Specificity):** Is the destroyer effect specific to the defense (i.e., `ASR(IR(A) | D) ≫ ASR(A | D)` while `ASR(IR(A) | no defense) ≈ ASR(A | no defense)`), rather than a generic ASR boost from any image input? *(D1, ablations)*
- **RQ3 (Cross-Defense Generality):** Does the destroyer effect generalize across three defense families — self-discrimination prompting (SAGE), caption-then-check (ECSO), and paraphrase + majority vote (SemanticSmooth)? *(D1)*
- **RQ4 (Mechanism):** Why does each defense fail under the destroyer — what about its pipeline lets IR-wrapped encoded text through? *(D1, mechanism analysis)*
- **RQ5 (Generality across encodings and models):** Does the destroyer effect hold across multiple text encodings (set theory, formal logic, classical Chinese, SemanticCamo) and target VLMs (frontier and mid-tier, open and closed)? *(D1)*
- **RQ6 (Defense Cost):** What is the benign over-refusal cost of each defense (SAGE / ECSO / SemanticSmooth) on OR-Bench / JBB benign? *(D3)*
- **RQ7 (IR scaling within GPT family — supporting):** When evaluated as a standalone defense on undefended models, does IR's effect scale with model capability within a single provider family? *(D4)*
- **RQ8 (Defense-side response — optional bonus):** Can a multimodal-native variant of SAGE (MM-SAGE) close the destroyer-induced gap on mid-tier VLMs without breaking frontier performance? *(D2)*
- **RQ9 (Adaptive text-mode attacks — speculative sidecar):** Can attacks tailored to SAGE's discriminative analysis module defeat SAGE in pure text mode? *(side bet, unrelated to destroyer spine)*

---

## 3. Methodology

### 3.1 Threat Model

**Attacker:** Possesses a text-encoded harmful prompt (math notation, classical language, formal logic, semantic camouflage) and a **defense destroyer** — a wrapper applied to that prompt before sending it to the VLM. The destroyer in this paper is Image Rendering (IR): the encoded text is rendered into an image and submitted as image-only input. The attack proceeds in two stages: (i) text encoding hides the harmful intent from text-level safety alignment; (ii) IR wrapping routes the encoded attack around the defense in deployment. The attacker assumes black-box API access to the target VLM and to any deployed defense.

**Defender:** Deploys a VLM with one of three advanced black-box defenses — SAGE (self-discrimination prompting), ECSO ("Eyes Closed, Safety On" — caption-then-check), or SemanticSmooth (paraphrase + majority vote). We do **not** claim these defenses were designed against IR-wrapped attacks; the contribution is to establish that a simple destroyer wrapper renders all three ineffective, exposing a category of vulnerability not previously studied.

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

### 3.3 Defenses Targeted by the Destroyer

We target three advanced black-box defenses, chosen for cross-family mechanism coverage. All three are training-free, deployable as VLM API wrappers, and effective against the bare encoded attack — making them meaningful targets for the destroyer to break.

| Defense | Venue | Mechanism family | Why it's a meaningful target |
|---------|-------|------------------|------------------------------|
| SAGE | ACL Findings 2025 | Self-discrimination prompting on input text | Strong on bare encoded attacks (0–3% ASR on frontier models); represents the discrimination-prompt family. |
| ECSO | (multimodal safety, 2024) | Caption-then-check: image → caption → text safety check | Designed specifically for the image-input setting; represents the caption-pipeline family. |
| SemanticSmooth | AACL-IJCNLP 2025 | LLM paraphrase + majority vote | Designed for input perturbation; represents the smoothing family. Effective on some encodings (classical_chinese), so a meaningful baseline. |

**Baseline framing:** The baseline for the destroyer's effectiveness is the *pure encoded attack under the same defense*. There is no published defense-destroyer method to compare against — IR-as-destroyer is a new category. The contribution is to establish this category and demonstrate its cross-defense effectiveness, not to exceed a prior destroyer.

**Why no prior defense-destroyer baselines exist:** Defense bypass in the literature has focused on (i) adaptive attacks tailored to a specific defense (e.g., GCG-against-SAGE-style work), or (ii) stronger base attacks. Neither is a "wrapper applied on top of an arbitrary attack to make it bypass arbitrary defenses." The destroyer category itself is the contribution.

**Supporting comparisons (ablations, not headline):**

| Variant | What it isolates |
|---------|------------------|
| Pure encoded attack under each defense | Baseline — what the defense blocks |
| `ir_plain`-wrapped encoded attack under each defense | **Headline** — destroyer effectiveness |
| Plain-text-screenshot (no encoding) under each defense | Trivial destroyer baseline — is destruction from any image input? |
| `ir_plain`-wrapped attack with no defense | Confirms destroyer is defense-specific, not a generic ASR boost |
| `ir_fc_typo`, `ir_figstep` renderer variants | Robustness of destroyer effect across rendering styles |

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

## 4. Results (as of May 19, 2026)

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

### 4.7 Defense Destroyer Evidence — SAGE Branch (anchor data)

Stage 10e Round 1 provides the first evidence that `ir_plain` wrapping defeats SAGE on mid-tier VLMs even though SAGE successfully blocks the bare encoded attack. This is the data anchor for the SAGE branch of D1 (defense destroyer).

| Model | Encoding | Pure attack (no defense) | Pure attack + SAGE | `ir_plain`-wrapped attack + SAGE | Destroyer gap |
|-------|----------|:------------------------:|:------------------:|:--------------------------------:|:------------:|
| Gemini 2.5 Flash Lite | set_theory | 45% | **3%** | **42%** | **+39pp** |
| Gemini 2.5 Flash Lite | formal_logic | 31% | **0%** | 14% | **+14pp** |
| GPT-5.4-nano | set_theory | 33% | **0%** | 9% | **+9pp** |
| GPT-5.4-nano | formal_logic | 12% | **0%** | 1% | +1pp |

Reading this as defense-destroyer evidence: SAGE successfully blocks the bare encoded attack (0–3% ASR), but `ir_plain` wrapping recovers most of the attack's effectiveness (back to within 3pp of the pure-attack-no-defense ASR for Gemini 2.5 Flash Lite set_theory). The destroyer effect is largest on mid-tier VLMs. Frontier models (GPT-5.4, Claude Sonnet 4.6) retain SAGE's protection under the destroyer (0–5pp gap), bounding the claim. If the pattern replicates on Qwen2.5-VL-7B, Pixtral-12B, and more API VLMs, the SAGE branch of the destroyer claim is established. ECSO and SemanticSmooth branches require independent runs on the same grid.

### 4.8 Companion-Image Ablation (supporting, not headline)

Text + image companion-image variants test whether the destroyer effect survives in a multimodal message composition where the encoded attack remains visible to the text defense. This is a *supporting ablation* — it bounds whether destruction is purely from optical delivery (image-only input) or also from multimodal context — not the main headline.

| Condition | Text content | Image content | What it isolates |
|-----------|--------------|---------------|------------------|
| Pure encoded attack + SAGE | Encoded harmful prompt | None | Baseline — text defense fully receives the attack |
| Text + blank image + SAGE | Same encoded harmful prompt | Blank/neutral image | Multimodal-context effect when defense still sees text |
| Text + unrelated image + SAGE | Same encoded harmful prompt | Benign unrelated image | Distraction-style multimodal context |
| Text + `ir_plain` duplicate + SAGE | Same encoded harmful prompt | Image-rendered duplicate of attack | Whether destroyer effect requires removing text |

If ASR remains low across these conditions, the destroyer's effect is specifically tied to image-only delivery (the text defense never seeing the encoded text). If ASR rises, the multimodal context itself contributes — a weaker but still useful secondary finding. Either way, this is supporting evidence for the headline destroyer claim, not a parallel result.

---

## 5. What Remains (updated May 19)

### 5.1 Critical Path (regrouped May 23, prioritized by what drives the main paper claim)

Ordering principle: **the destroyer matrix is the gating experiment** — pure attack vs `ir_plain`-wrapped attack across {SAGE, ECSO, SemanticSmooth} × {target VLMs}. D3 (over-refusal) is supporting on separate infrastructure. D2 (MM-SAGE) is optional bonus, starts only after destroyer matrix confirms.

| Order | Experiment | Direction | Purpose | Status |
|:-:|------------|-----------|---------|--------|
| **1 (gating)** | **Destroyer matrix — SAGE branch** on Qwen2.5-VL-7B + Pixtral-12B with `ir_plain` | D1 | Pure attack vs `ir_plain`-wrapped attack under SAGE. Extends Stage 10e Round 1 anchor data (§4.7) to free cluster VLMs. **If destroyer effect doesn't replicate, the main claim collapses.** | **NEXT** |
| **1 (gating)** | **Destroyer matrix — ECSO branch** on the same VLMs with `ir_plain` | D1 | Pure attack vs `ir_plain`-wrapped attack under ECSO. **Requires implementing ECSO in `src/defense/defender_factory.py`.** | Pipeline change required |
| **1 (gating)** | **Destroyer matrix — SemanticSmooth branch** on the same VLMs with `ir_plain` | D1 | Pure attack vs `ir_plain`-wrapped attack under SemanticSmooth. Pipeline already supports the `semantic_smooth` defender. | Concurrent cluster jobs |
| 1 (parallel) | **Trivial destroyer ablation**: plain-text screenshot, attack-as-image without IR style | D1 (ablation) | Sanity check that destruction is specific to `ir_plain`-rendered encoded text, not artifact of any image input. **Supporting only.** | Concurrent |
| 1 (parallel) | **Renderer ablation**: `ir_fc_typo`, `ir_figstep` under each defense | D1 (ablation) | Robustness of destroyer effect to rendering style. Pipeline already supports these renderers. | Concurrent |
| 1 (parallel) | **Mechanistic hidden-state analysis** on Qwen / Pixtral | D1 (mechanism) | Per-defense mechanism story: where in each defense pipeline does the destroyer slip through? | Concurrent cluster jobs |
| 1 (parallel, separate infra) | **Over-refusal: each defense × OR-Bench benign + JBB benign** | D3 | Pareto frontier for safety-utility tradeoff. **Supporting only; does not gate the paper.** Runs on Claude API + benign benchmarks. | Concurrent |
| 1 (parallel, separate infra) | **Destroyer matrix on more API models** (GPT-4o-mini + more Gemini variants) | D1 | Only runs if API access restored. Broadens VLM coverage. | If API restored |
| 2 (no new experiments) | **Capability correlation analysis** | D1 | Regress destroyer gap against MMMU / MMLU / MathVista | After enough datapoints exist |
| **3 (lifts paper, optional)** | **MM-SAGE wrap-in-user-message variant** | D2 | Defense-side response: can a multimodal-native SAGE close the destroyer gap on mid-tier without breaking frontier? | After destroyer matrix confirms |
| 3 (conditional) | **MM-SAGE OCR-then-wrap / joint multimodal variants** | D2 | Investment only if wrap-in-user-message closes >30% of destroyer gap | Conditional on cheapest variant |
| 4 (companion-image ablation) | **Text + image companion-image variants** under SAGE | D1 (ablation) | Whether destroyer effect requires removing text or also fires under multimodal-context. **Pipeline change required** for companion-image support. | After pipeline change |
| 5 (writing) | **D4** — GPT-family IR scaling | D4 | Pure writing on existing data; supporting section only | Anytime |
| 6 (sidecar) | **Adaptive text-mode attacks against SAGE** (old D1c) | side bet | Engineer wrapper-injection / DAM-targeting / multi-turn / GCG-against-SAGE | Speculative parallel research bet — do not gate paper on it |
| Deferred | Multi-image, OCR-defeating, engineered renderers | D1 extensions | Higher implementation cost; pursue only if plain + fc_typo + figstep destroyer variants show signal | Deferred |
| Skip | SAGE+IR composition completion | Archived (DD1) | Originally for composition-defense story; composition never beats SAGE. Reframed: SAGE+IR is now interpreted as a destroyer variant. | Skip |

### 5.2 Completed (May 9–19)

| Experiment | Result |
|------------|--------|
| IR+SAGE_system_prompt on frontier (GPT-5.4, Claude 4.6) | Does NOT beat SAGE (0-10% vs 0-3%) |
| Classical Chinese on frontier | GPT-5.4: −19pp. Claude: no effect (+2pp). |
| SemanticSmooth on classical_chinese | Works (−18 to −21pp) — unlike formal_logic |
| SAGE defense_transform | 3 encoding outputs ready for hybrid pipeline |
| Gemini 2.5 Pro (partial) | 2/4 done, others timeout |
| Stage 10e Round 1 | SAGE remains strong in text; IR+SAGE_system_prompt exposes optical-delivery gap on Gemini 2.5 Flash Lite |

### 5.3 After Core Experiments

| Experiment | Purpose | Effort |
|------------|---------|--------|
| Bootstrap CIs on all claims | Statistical rigor | Local computation |
| Full HarmBench (240) on frontier models | Robustness check for paper | Low cost re-run |
| Benign over-refusal on frontier models | Defense cost measurement | ~12 tasks |
| SemanticCamo (4th attack) | Generality | 1 round |
| Open-source VLMs (Qwen/Pixtral) | Test D3 modality flip and connect with practical VLM deployments | Cluster |

### 5.4 Blockers

- **OpenAI API**: Account warned, appeal failed. Cannot submit harmful prompts.
- **Google API**: Account warned. Gemini batch tasks may be blocked.
- **Claude API**: Still working.

---

## 6. Paper Positioning

### Core Contribution (regrouped May 23 — defense-destroyer framing)

The paper establishes **a new category of attack-wrapping method — the defense destroyer**: a wrapper applied on top of an existing text-encoded attack that converts otherwise-blocked attacks into successful ones against advanced black-box defenses. We instantiate this category with Image Rendering (IR) and demonstrate cross-defense effectiveness against SAGE, ECSO, and SemanticSmooth. There is no published defense-destroyer method to compete with; the baseline is the pure encoded attack under each defense. Paper framings, ordered by current scientific priority:

**Option A (target: full destroyer matrix + ablations + D3 — main paper):** *IR as a Defense Destroyer: Defeating Self-Discrimination, Caption-Then-Check, and Smoothing Defenses for VLMs*
- D1 main contribution: `ir_plain` wrapping defeats all three defenses (SAGE, ECSO, SemanticSmooth) across multiple encodings and target VLMs, even though IR alone is neutral on undefended models. Per-defense mechanism narrative explains *why* each defense breaks.
- Supporting ablations: trivial destroyer baselines (plain screenshot, attack-as-image) confirm specificity to IR-rendered encoded text; renderer variants (`ir_fc_typo`, `ir_figstep`) confirm robustness to rendering style; companion-image variants bound whether destruction is purely optical-delivery or also multimodal-context.
- D3 supporting: over-refusal cost of each defense on OR-Bench / JBB benign — quantifies what defenders give up for the protection IR-destroyer breaks.
- Main claim: VLM safety defenses, even when effective on the bare attack, can be uniformly broken by a simple input-side wrapper. This establishes "defense destroyer" as a category worth studying separately from attack strength.

**Option B (destroyer matrix + D3 only, no MM-SAGE):** *Same as Option A without the defense-side response.* Cleanest first-in-category result; ceiling is lower without a defense suggestion but stays coherent.

**Option C (Option A + D2 MM-SAGE bonus):** Add a defense-side response — a multimodal-native SAGE variant that closes the destroyer gap on mid-tier without breaking frontier. Concrete method contribution lifting the paper from analytical-only.

**Option D (D4 as support):** Reframe the GPT-family IR scaling result (`ir_plain` as standalone defense within GPT family) as a supporting section on when IR helps vs. hurts on undefended models. No new experiments needed.

**Option E (Adaptive text-mode attacks against SAGE — old D1c, speculative sidecar):** *Unrelated to the destroyer spine.* If text-mode attacks defeat SAGE on frontier, that's a separate paper or a strong appendix — do not bet the main line on it.

**Option F (DD2 floor — empirical study):** First systematic evaluation of encoding attacks × defenses × VLMs. Used only if destroyer matrix underperforms across all three defenses.

### Evidence Structure (updated)

| Claim | Evidence |
|-------|----------|
| Encoding attacks are a real threat on undefended VLMs | 24–39% ASR on GPT-5.4 with set_theory / formal_logic / classical_chinese |
| Each targeted defense is meaningful (blocks bare encoded attacks) | SAGE: 0–3% ASR on frontier; ECSO: pending; SemanticSmooth: helps on classical_chinese |
| **Destroyer defeats SAGE on mid-tier (anchor)** | Gemini 2.5 Flash Lite set_theory: pure-attack-no-defense 45% → pure-attack+SAGE 3% → `ir_plain`+SAGE 42% (+39pp destroyer gap) |
| Destroyer is defense-specific, not a generic ASR boost | `ir_plain`-wrapped attack ≈ pure attack on undefended models (no IR ASR boost without a defense) |
| Destroyer generalizes across defense families (pending) | Cross-family runs against ECSO and SemanticSmooth on the same encoding × model grid |
| Destroyer specificity to IR-rendered encoded text (ablation) | Trivial destroyer baselines (plain screenshot, attack-as-image) under each defense |
| IR-as-standalone-defense scales within GPT family (supporting) | nano fails (+12pp) → mini works (−5 to −19pp) → 5.4 dominant (−22 to −32pp) |

### Probability Assessment (regrouped May 23 — defense-destroyer framing)

| Direction | Experiment needed | Probability | If confirmed | Paper level |
|-----------|-------------------|:-----------:|-------------|:-----------:|
| **D1 SAGE branch: `ir_plain` destroyer defeats SAGE across multiple VLMs** | Extend Stage 10e Round 1 anchor to Qwen2.5-VL-7B, Pixtral-12B (cluster, free); more API models if restored | 70% | Anchor of the destroyer claim | **EMNLP Findings; main if cross-defense generalizes** |
| **D1 ECSO branch: `ir_plain` destroyer defeats ECSO on the same grid** | Implement ECSO in defender factory; run pure-vs-IR-wrapped across encodings × VLMs | 60% | Cross-family generality — caption-pipeline defense breaks the same way | **EMNLP main plausible** |
| **D1 SemanticSmooth branch: `ir_plain` destroyer defeats SemanticSmooth on the same grid** | Run pure-vs-IR-wrapped across encodings × VLMs (pipeline already supports) | 55% | Cross-family generality — smoothing defense breaks too | **EMNLP main plausible** |
| **D1 ablation: trivial destroyer baselines do NOT defeat the defenses (specificity)** | Plain-text screenshot, attack-as-image under each defense | 60% | Supporting evidence that destruction is specific to IR-rendered encoded text | **Strengthens main claim** |
| **D3: each defense has measurable over-refusal cost on OR-Bench / JBB benign** | Run defenses × benign benchmarks on 2–3 models | 55% | Pareto frontier; safety-utility tradeoff section | **EMNLP Findings / AIES support** |
| **D2 (optional bonus): MM-SAGE closes destroyer gap on mid-tier without breaking frontier** | Wrap-in-user-message variant first; OCR-then-wrap if signal | 30% | Defense-side method contribution lifting paper above pure empirical | **EMNLP main plausible** |
| **D4: IR-as-standalone-defense scales within GPT family** | (already confirmed) | — | Supporting section on when IR helps undefended models | (already in data) |
| **Adaptive text-mode attacks defeat SAGE on frontier (sidecar)** | Engineer wrapper-injection / DAM-targeting / multi-turn / GCG-against-SAGE | 20% | Major separate contribution | **NeurIPS / ICLR / USENIX Security if it works** |
| **DD2 floor: destroyer effect fails across all three defenses** | (contingency) | 15% | Reframe as empirical study of encoding attacks × defenses | **AIES / Workshop** |

Note: SAGE + ECSO + SemanticSmooth destroyer branches form the main paper line. Trivial-destroyer ablation is supporting evidence for specificity. D3 over-refusal is supporting only. D2 MM-SAGE is optional bonus. D4 is a no-experiment supporting section. Adaptive text-mode attacks are a separate research bet — do not bet the main paper on them. DD2 is the contingency if the destroyer effect doesn't generalize.

---

## 7. Timeline (updated May 19)

| Date | Milestone |
|------|-----------|
| May 1–6 ✅ | Data, encoding, imaging, JBB/HarmBench eval on 8 models, renderer exploration |
| May 6 ✅ | Frontier IR results (GPT-5.4, Claude Sonnet 4.6). Scaling law confirmed. |
| May 7 ✅ | SAGE/SemanticSmooth baselines — SAGE unexpectedly strong (0% ASR). Judge bug discovered. |
| May 8 ✅ | Judge bug fixed. Pivot to hybrid defense. Code refactored (defense_transform mode). |
| May 9 ✅ | IR+SAGE_system_prompt on frontier (does NOT beat SAGE), CC eval, SemanticSmooth CC, SAGE transform |
| May 13 ✅ | Pivot to testing older models. API accounts restricted (OpenAI, Google). |
| May 19 ✅ | Stage 10e Round 1: SAGE strong in text, but optical delivery weakens SAGE on Gemini 2.5 Flash Lite. Evaluator refusal safeguards added. |
| May 19–22 | Run D6 text+image smoke test, then replicate D5/D6 on more models/defenses if promising |
| May 20–25 | Paper writing |
| **May 25** | **ARR deadline (EMNLP or AIES)** |

Fallback: ARR June (~Jun 15) or EMNLP direct (Jun 2026).

---

## 8. Risks & Mitigation

| Risk | Likelihood | Mitigation |
|------|:-:|-----------|
| Destroyer effect on SAGE fails to replicate beyond Gemini 2.5 Flash Lite | Medium | Reframe as mid-tier-VLM-specific destroyer finding; bound the claim to non-frontier deployments. Cross-defense generality (ECSO, SemanticSmooth) still carries the paper if those branches hold. |
| Destroyer effect on ECSO or SemanticSmooth is weak / absent | Medium | Single-defense destroyer story (SAGE branch only) is still publishable, just narrower. Reframe as "cross-family destroyer behavior is defense-mechanism-dependent" — a result in itself. |
| Trivial destroyer baselines (plain screenshot, attack-as-image) ALSO defeat the defenses | Medium | Reduces the contribution to "any image-wrapped attack defeats these defenses" — still a finding but smaller. Reframe as "image-input modality is a weakness for text-side defenses" rather than IR-specific. |
| Companion-image ablation shows no signal | Low | Drop the ablation; destroyer claim doesn't depend on it. |
| D2 MM-SAGE doesn't close the gap, or breaks frontier performance | 65% (MM-SAGE is a real research bet) | Optional bonus only — paper still ships on destroyer matrix + ablations + D3 without it. Document attempt as negative result with mechanism discussion. |
| Reviewers say SAGE/ECSO/SemanticSmooth weren't designed against IR wrappers | Medium | Frame as a *new category of attack vector*, not a failure to meet stated authors' claims. The point is that these are the strongest published black-box defenses and they all break under a trivial wrapper. |
| Destroyer gap appears only on 1–2 mid-tier VLMs | Medium | Require replication on ≥3 VLMs before making it the main claim. Use mechanism analysis to lift result above anecdote. |
| D3 over-refusal cost turns out to be negligible | 45% | Drop the Pareto section; destroyer matrix carries the paper. |
| Adaptive text-mode sidecar finds nothing | 80% | Cost-bounded sidecar; doesn't affect main paper. |
| "Too simple" criticism (IR is just image input) | Medium | The contribution is establishing the *category*, demonstrating cross-defense generality, and providing per-defense mechanism. Simplicity of the wrapper is a *strength* — defenses should not break under trivial wrappers. |
| Reviewers say "no prior defense-destroyer baseline" | High | Lean into it: the category is new. Baseline is pure attack under each defense; the contribution is establishing the category, not exceeding prior destroyers. |
| API access restrictions block API-side experiments | MEDIUM | Cluster (Qwen2.5-VL-7B, Pixtral-12B) and Claude Sonnet 4.6 unblocked. New OpenAI/Google accounts being obtained for stretch coverage. |

---

## 9. Paper Structure (revised May 23 — defense-destroyer framing)

1. **Introduction:** Text-encoding attacks defeat undefended frontier VLMs (24–39% ASR on GPT-5.4). Advanced black-box defenses (SAGE, ECSO, SemanticSmooth) successfully block the bare encoded attack. We introduce the **defense destroyer**: a wrapper applied on top of an existing encoded attack that defeats all three defenses. We instantiate the category with Image Rendering (IR) and demonstrate that `ir_plain`-wrapped encoded attacks restore most of the attack's pre-defense effectiveness across defense families. The destroyer is defense-specific — IR alone is neutral on undefended models — and the effect is robust to renderer style.
2. **Background:** Text-encoding attacks (CC-BOS, MathPrompt, formal logic), VLM safety alignment, the three targeted defense families (self-discrimination prompting, caption-then-check, paraphrase + majority vote), modality safety asymmetry, prior work on attacks against specific defenses.
3. **Method:** Defense destroyer formulation — wrapper `W(·)` applied to encoded attack `A` to produce `W(A)`, evaluated against each defense `D` for the gap `ASR(W(A) | D) − ASR(A | D)`. Instantiation: `W = ir_plain` (and renderer variants `ir_fc_typo`, `ir_figstep`). Per-defense pipeline through which the destroyer slips.
4. **Experimental Setup:** Target VLMs (frontier + mid-tier, closed + open), 4 encodings, 3 defenses, HarmBench (100/240), pure-attack vs IR-wrapped-attack evaluation grid, evaluation protocol.
5. **Results:**
   - 5.1 Encoding attacks on undefended VLMs (baseline ASR)
   - 5.2 Each defense blocks the bare encoded attack (defenses are meaningful targets)
   - 5.3 **Destroyer matrix — SAGE branch** (anchor)
   - 5.4 **Destroyer matrix — ECSO branch** (cross-family)
   - 5.5 **Destroyer matrix — SemanticSmooth branch** (cross-family)
   - 5.6 Destroyer is defense-specific (`ir_plain` ≈ pure attack on undefended models)
   - 5.7 Specificity ablation: trivial destroyer baselines (plain screenshot, attack-as-image) do not defeat the defenses
   - 5.8 Renderer ablation (`ir_fc_typo`, `ir_figstep`) — destroyer survives style changes
   - 5.9 Companion-image ablation — bounds optical-delivery vs multimodal-context contribution
   - 5.10 Over-refusal cost of each defense (D3, supporting)
   - 5.11 IR-as-standalone-defense scaling within GPT family (D4, supporting)
6. **Analysis:** Per-defense mechanism — why each defense's pipeline lets `ir_plain`-wrapped encoded text through (SAGE: no text to discriminate; ECSO: caption recovers encoded text; SemanticSmooth: paraphrase preserves encoded structure). Deployment recommendations.
7. **Conclusion:** Defense destroyers are a new category of attack vector worth studying separately from attack strength. Black-box VLM safety defenses, even when strong on bare attacks, need to be evaluated against simple input-side wrappers before deployment.

---

## 10. Publication Strategy (updated May 19)

| Venue | Deadline | P(accept) | Fit |
|-------|----------|:---------:|-----|
| **EMNLP 2026 (via ARR)** | May 25 | ~30-35% (main+Findings) if D1 succeeds; lower if empirical only | Higher prestige; needs a clear method or strong regime-shift story |
| **AIES 2026** | May 25 (same cycle) | ~40-55% for empirical safety framing | Natural fit for safety findings; lower prestige |
| ARR June 2026 | ~Jun 15 | — | Backup if May too tight |
| USENIX Security 2027 | ~Feb 2027 | — | If reframed for security audience |

**Decision (regrouped May 23 — defense-destroyer framing):** EMNLP is the right target only if the destroyer matrix is strong enough: either (i) destroyer effect generalizes across all three defenses (SAGE + ECSO + SemanticSmooth) on ≥3 VLMs — main paper line, (ii) destroyer effect generalizes on SAGE branch only but with strong mechanism analysis + over-refusal cost + renderer/trivial-destroyer ablations — Findings-tier first-in-category result, or (iii) destroyer matrix + MM-SAGE bonus closes the gap. If destroyer effect fires only on Gemini 2.5 Flash Lite and one defense, AIES is the safer and more coherent venue. DD2 floor (destroyer effect doesn't generalize anywhere) is workshop / AIES only.

---

## 11. Future Work

Note: Hidden-state mechanism analysis and the trivial-destroyer / renderer / companion-image ablations have all been promoted into the main paper plan; they are no longer future work.

- **Beyond IR — other destroyer wrappers:** Are there other simple input-side wrappers that defeat these defenses? (Multi-image splitting, audio modality if VLMs support it, retrieval injection.)
- **Defense-side response beyond MM-SAGE:** Joint multimodal safety reasoning, image-conditioned discriminator training, destroyer-aware caption checks for ECSO.
- **Selective destroyer detection:** Can a defender detect that a wrapper has been applied? If yes, can they fall back to a stricter check? (Trades off with over-refusal.)
- **Longitudinal study:** Track destroyer effectiveness across future VLM and defense releases.
- **Adaptive text-mode attacks against SAGE** (old D1c sidecar): separate research bet if not pursued during main paper window.
