# Research Proposal: Encoding × Modality Interactions in Multimodal LLM Safety

## 0. Literature Review Summary (May 2026)

### Landscape

- **FigStep is dead on frontier models:** MIDAS (ICLR 2026) confirms 0.00% ASR on GPT-5-Chat, <4% on GPT-4o/Gemini-2.5-Pro. Safety patches completely neutralize simple typographic attacks.
- **Text-DJ (arXiv 2026) provides confounded modality gap evidence:** TiI ablation shows 2–4.5× ASR increase from images on Qwen3-VL and GPT-4.1-mini/Gemini-2.5-Flash. But always within their decomposition+distraction framework — never clean A/B.
- **MIDAS achieves 72–97% on frontier models** via multi-image puzzles (6 images, game-style templates). High bar for attack papers.
- **Adversarial Smuggling: GPT-5 content moderation 98.6% blind to visual text.** Yet GPT refuses to GENERATE harmful content from images — safety is generation-level, not perception-level.
- **Encoding-based attacks (CC-BOS, MathPrompt) work in text** but are unstudied in image modality.
- **Semantic codebook defenses fail on non-canonical attacks (AUC 0.60).** Encoded prompts would trivially evade.
- **ASR measurement validity (Chouldechova, NeurIPS 2025):** Small N requires bootstrap CIs. 100 prompts may not support fine-grained claims.
- **JRS: blank images alone shift representations +28pp toward jailbreaking** on open-source models.

### Our Position

Nobody has done a **clean, controlled** encoding × modality comparison on frontier models. Text-DJ is confounded. MIDAS uses complex multi-image puzzles. CC-BOS/MathPrompt are text-only. We fill the intersection: same content, same judge, only modality varies, with encoding as a controlled variable.

---

## 1. Introduction & Motivation

LLM safety alignment is built on **text-centric** mechanisms — RLHF, refusal training, and classifiers like Llama Guard all operate on tokenized text. With frontier multimodal LLMs (GPT-5-mini, Gemini 2.0 Flash, Claude Sonnet 4) now processing images, a critical question arises: does the **modality** of input affect safety behavior?

Two attack dimensions exist independently:
- **Modality attacks** (FigStep, Text-DJ): Render harmful text as images to bypass text-trained safety. FigStep achieved 82.5% on 2023 open-source models but is now 0% on frontier models. Text-DJ shows 2–4.5× amplification but is confounded.
- **Encoding attacks** (CC-BOS, MathPrompt): Transform harmful content into classical languages or math notation. 60–74% ASR in text modality.

**The gap:** Nobody has studied their interaction. Does encoding + imaging compound, cancel, or interact in unexpected ways? This is not just an academic question — if encoding makes image attacks non-brittle (surviving even OCR-based defenses), the threat model changes fundamentally.

**Updated framing based on preliminary results:** Our experiments reveal that the interaction is more nuanced than "amplification vs. cancellation." The modality effect is provider-dependent (GPT defends, Claude/Gemini amplify), renderer-dependent (FigStep causes massive benign over-refusal that encoding eliminates), and encoding-dependent (math encodings are modality-invariant, classical languages vary). This complexity is itself the finding — safety is not a unified mechanism but a patchwork of format-specific responses.

## 2. Research Questions

- **RQ1 (Modality Effect):** Does image-rendering change ASR compared to plain text, and how does this interact with encoding?
- **RQ2 (Safety Calibration):** Does image-rendering affect benign refusal rate (false positives), and does encoding modulate this?
- **RQ3 (Provider Divergence):** Do different providers exhibit systematically different modality effects, and why?
- **RQ4 (Renderer Effects):** How do different image rendering styles (plain, FigStep, FC-Typography) interact with encoding and model?

## 3. Methodology

### 3.1 Experimental Design

**Encoding × Modality × Renderer × Model** factorial design.

| Dimension | Levels |
|-----------|--------|
| Encoding | plain, set_theory, formal_logic, classical_chinese_literary, sanskrit_literary |
| Modality | text, image |
| Renderer | plain, figstep, fc_typography |
| Model | GPT-5-mini, Gemini 2.0 Flash, Claude Sonnet 4 |
| Prompt type | harmful (JBB 100, OR-Bench 100+), benign (JBB 100, OR-Bench 100+) |

### 3.2 Encoding Implementations

- **Plain English:** Direct prompts from benchmark. Baseline.
- **Set Theory:** Harmful semantics encoded as formal set-theoretic expressions. Via GPT-4.1-mini.
- **Formal Logic:** First-order logic with quantifiers and predicates. Via GPT-4.1-mini.
- **Classical Chinese (文言文, literary):** CC-BOS-inspired multidimensional literary strategy. Via GPT-4.1-mini.
- **Sanskrit (literary):** Adapted classical language encoding in Devanagari script. Via GPT-4.1-mini.

### 3.3 Image Rendering

| Renderer | What it tests |
|----------|---------------|
| **Plain** | Pure modality effect — clean text on white background |
| **FigStep** | Numbered-step formatting; tests whether patched attack format triggers safety |
| **FC-Typography** | Stylized fonts (Pacifico, Creepster, etc.); tests OCR-difficulty effect |

### 3.4 Datasets

- **JailbreakBench** (100 harmful + 100 benign): High-quality, curated. Currently primary.
- **OR-Bench** (harmful + benign_hard, first 100–1000 rows): Larger N for statistical power. Dedicated over-refusal benchmark.
- **Bootstrap CIs** on all ASR comparisons (per Chouldechova, 2025).

### 3.5 Target Models

| Model | Provider | Why |
|-------|----------|-----|
| GPT-5-mini | OpenAI | Latest efficient frontier; shows "imaging-as-defense" pattern |
| Gemini 2.0 Flash | Google | Fast, capable; shows "imaging-as-amplifier" pattern |
| Claude Sonnet 4 | Anthropic | Strongest safety alignment; shows "imaging-as-amplifier" + extreme FigStep over-refusal |

Generational comparison (Stage 9): GPT-4o-mini, Pixtral-12B on same images for temporal trend.

### 3.6 Evaluation

- **ASR judge:** GPT-5-nano (HarmBench protocol)
- **Refusal judge:** GPT-5-nano 3-class (direct_answer / direct_refusal / indirect_refusal, OR-Bench protocol)
- **Statistical testing:** Bootstrap 95% CIs; permutation tests for pairwise comparisons

## 4. Preliminary Results & Current Status

### What we have

- Text encoding on JBB harmful: ~55-67% ASR across models (encoding works, as expected)
- Plain image (no encoding): marginal effects, model-dependent
- FigStep + encoding on harmful: resurfaces some ASR on Claude/Gemini, not on GPT
- FigStep on benign: 75% refusal on Claude (massive over-refusal from renderer formatting)
- Encoding eliminates FigStep-induced over-refusal (75% → ~5%)
- FC-Typography generally stronger attack renderer than FigStep/Plain
- GPT-5-mini: imaging slightly reduces ASR (defensive)
- Claude/Gemini: imaging slightly amplifies ASR on some conditions

### What's missing

- OR-Bench at scale (in progress)
- Generational comparison (Stage 9, planned)
- FC-Typography benign completion (in progress)
- Statistical significance testing with CIs

## 5. Candidate Paper Directions

We list multiple directions. Final choice depends on which results are strongest after remaining experiments.

### Direction A: "Encoding Resurrects Dead Attacks"

**One-sentence pitch:** Text encoding transforms image-based attacks from patched (0% ASR) to effective (X%), proving safety patches are format-level, not semantic.

**Requirements for this to work:** X needs to be consistently >40% across multiple models. Currently strongest on Claude/Gemini with FC-Typography, but need more data.

**Paper structure:** Attack paper. Clear before/after metric. Simple method, surprising result.

### Direction B: "Dual-Axis Safety Calibration"

**One-sentence pitch:** Encoding simultaneously bypasses image safety (reducing false negatives on harmful) AND eliminates image over-refusal (reducing false positives on benign) — proving safety is format-matching.

**Requirements:** OR-Bench at scale must show statistically significant effects on BOTH axes. The "dual effect from one transformation" is the logic that makes it novel.

**Paper structure:** Measurement/diagnostic paper. Needs scale for credibility.

### Direction C: "Provider Safety Architecture Divergence"

**One-sentence pitch:** The same encoding+imaging attack has opposite effects across providers — GPT's safety defends against images while Claude/Gemini become more vulnerable — revealing fundamentally different safety architectures.

**Requirements:** Pattern must hold consistently across more models per provider and more conditions. Currently N=1 per provider.

**Paper structure:** Empirical analysis. Needs generational data to confirm.

### Direction D: "Generational Safety Evolution"

**One-sentence pitch:** Cross-modal safety calibration has changed (improved? worsened? shifted?) across model generations, measured using encoding as a controlled probe.

**Requirements:** Stage 9 results. At least 2 generations per provider showing a clear trend.

**Paper structure:** Temporal trend / longitudinal study.

## 6. Timeline (Revised May 2026)

| Date | Milestone |
|------|-----------|
| May 4–10 | Complete Stage 7e (FC-Typo benign) + Stage 8a (OR-Bench encoding) |
| May 10–14 | Stage 9 (generational comparison) + Stage 8b (OR-Bench imaging) |
| May 14–18 | Stage 8c (OR-Bench evaluation) + analyze all results |
| May 18–20 | **Decision point:** Choose paper direction based on strongest signal |
| May 20–25 | Paper writing |
| **May 25** | **ARR May cycle deadline** |

## 7. Risks & Mitigation

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| No direction shows dramatic results | Medium | Workshop paper (SoLaR, TrustNLP). Still publishable as empirical contribution. |
| Modality gap too small/noisy for claims | Medium-High | OR-Bench scale + bootstrap CIs. Report CIs honestly; small-but-real effects are valid findings. |
| "Just combining known methods" criticism | High | Emphasize controlled comparison methodology and unexpected interaction effects. Cite Chouldechova on why controlled comparison IS a contribution. |
| Text-DJ already tested frontier models | Real | Differentiate: our comparison is unconfounded (no decomposition/distraction framework). |
| MIDAS makes our ASR numbers look weak | Medium | Don't compete on raw ASR. Frame as diagnostic/evaluation, not pure attack. |

## 8. Key Decisions Still Open

1. **One paper or two?** If dual-axis effect is strong → one combined paper. If only one axis works → split or pick.
2. **Include defense experiments?** Literature already shows defenses fail (Text-DJ: 0% detection, Smuggling: 98.6% evasion). May not need our own if we cite these.
3. **Include generational comparison?** Only if results show a clear trend. Otherwise noise.
4. **How many OR-Bench prompts?** Start with 100, expand to 1000 if effects look real.
5. **Include FC-Flowchart?** Depends on whether it adds signal or just noise.

## 9. Publication Strategy

### 9.1 Primary Target: EMNLP 2026 (ARR May cycle, deadline ~May 25)

Regardless of which direction is strongest, we target EMNLP via ARR May. The empirical NLP safety track is the natural fit: encoding is linguistic, multimodal, and the safety community publishes here.

**What the paper will contain (minimum viable):**
- Controlled encoding × modality comparison on 3 frontier models
- At least one benchmark at scale (OR-Bench or JailbreakBench)
- Bootstrap CIs on all claims
- 3-class judge evaluation (not just binary ASR)
- Benign refusal as a control axis

### 9.2 Direction → Framing Map

| Direction | Title style | Contribution type | Venue fit |
|-----------|-------------|-------------------|-----------|
| A (Resurrection) | "Encoding Revives Patched Attacks..." | Attack paper | EMNLP / USENIX Security |
| B (Dual-Axis Calibration) | "One Transformation, Two Failures..." | Measurement paper | EMNLP / ACL |
| C (Provider Divergence) | "Same Attack, Opposite Effects..." | Empirical analysis | EMNLP / NeurIPS (safety) |
| D (Generational Evolution) | "How Cross-Modal Safety Changed..." | Longitudinal study | EMNLP / FAccT |

### 9.3 Outcome-Dependent Strategy

**If one direction is clearly strongest (>May 18):**
- Single focused paper, 8 pages, tight story
- Other findings go into appendix or future work

**If no single direction dominates:**
- Combined empirical paper: "Encoding × Modality Interactions in Frontier LLM Safety"
- Present findings as a systematic study with multiple insights
- Each direction becomes a subsection of results
- Less dramatic but more complete

**If nothing is publication-ready by May 25:**
- Skip ARR May → target ARR June (NAACL) or ARR August (ACL 2027)
- Use extra time to run more conditions and scale OR-Bench to 1000+
- Workshop fallback: SoLaR @ NeurIPS 2026, TrustNLP @ NAACL 2027

### 9.4 Two-Paper Potential

If the dual-axis story works (Direction B), a natural split exists:

| | Paper 1 (attack axis) | Paper 2 (over-refusal axis) |
|-|---|---|
| Focus | Encoding bypasses image safety on harmful prompts | Encoding eliminates image over-refusal on benign prompts |
| Benchmark | JBB/HarmBench harmful | OR-Bench benign_hard |
| Timeline | EMNLP 2026 (May ARR) | AAAI/ACL 2027 |
| Status | Data mostly collected | Needs OR-Bench scale |

Decision: One combined paper preferred (stronger as unified finding). Split only if combined is too dense for 8 pages.

### 9.5 Venue Priority

| Priority | Venue | Deadline | Fit |
|----------|-------|----------|-----|
| 1st | EMNLP 2026 (ARR May) | ~May 25, 2026 | Primary target |
| 2nd | ARR June → NAACL 2027 | ~Jun 15, 2026 | Fallback if May is rushed |
| 3rd | AAAI 2027 | ~Aug 2026 | AI safety track; broader scope |
| 4th | NeurIPS 2026 workshops | ~Sep 2026 | SoLaR, SafeGenAI |
| Reach | ICLR 2027 | ~Oct 2026 | If expanded with mechanistic analysis |

## 10. Future Work (Beyond First Paper)

- **Composable encodings:** Stacking encoding layers (Classical Chinese + math)
- **AI-generated rendering:** GPT Image 2 for naturalistic visual contexts
- **Multi-image attacks:** MIDAS-style comparison with our simpler single-image approach
- **Defense proposal:** If OCR-based defense shows promise, separate defense paper
- **Open-source model analysis:** Mechanistic probing (attention, representations) on LLaVA/InternVL
