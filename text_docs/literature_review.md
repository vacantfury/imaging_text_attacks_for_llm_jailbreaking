# Literature Review: Modality-Dependent Safety in Multimodal Large Language Models

## 1. Introduction

This literature review surveys research relevant to our proposed controlled study on whether the modality of input — plain text versus image-rendered text — affects jailbreaking effectiveness on frontier multimodal LLMs. We focus on six areas: (1) foundational text-based jailbreaking, (2) typographic and text-in-image attacks, (3) adversarial perturbation-based multimodal attacks, (4) linguistic and encoding-based attacks, (5) safety alignment and defense, and (6) evaluation methodology. Each section includes gap analysis.

---

## 2. Foundational Text-Based Jailbreaking

### 2.1 Key Works

**Gradient-based attacks.** Zou et al. (2023) introduced GCG (Greedy Coordinate Gradient), which appends optimized adversarial suffixes to harmful prompts. A crucial insight was **cross-model transferability**: suffixes optimized on open-source models often succeeded against GPT-4 and Claude. The accompanying AdvBench dataset (~500 harmful behaviors) remains a standard evaluation resource.

**Automated semantic attacks.** Chao et al. (2024) proposed PAIR, which uses an attacker LLM to iteratively refine jailbreaks in under 20 queries. Liu et al. (2024) extended this with AutoDAN, using a hierarchical genetic algorithm to produce stealthy, fluent jailbreaks that evade perplexity-based filters — addressing GCG's nonsensical suffix limitation.

**In-the-wild jailbreaks.** Shen et al. (2024) collected 1,405 real-world jailbreak prompts and showed that DAN (Do Anything Now) style attacks using role-playing, privilege escalation, and prompt injection achieved up to 95% ASR, persisting across model versions for 240+ days.

**Incremental completion decomposition.** Arif et al. (2026) introduced ICD, a trajectory-based jailbreak that elicits a sequence of single-word continuations related to a malicious request before requesting the full response. Evaluated across multiple model families on AdvBench, JailbreakBench, and StrongREJECT, ICD achieves superior ASR compared to existing methods. The key mechanistic finding is that successful attack trajectories **systematically suppress refusal-related representations** and shift activations away from safety-aligned states — providing direct evidence that jailbreaks work by manipulating the model's internal safety geometry, not just bypassing surface-level filters.

**Domain context exploitation.** Hung et al. (2026) demonstrate that domain-specific contexts selectively relax defenses: chemistry contexts lower barriers for chemical knowledge ("vertical unlocking"), while safety-research contexts trigger **broader relaxation spanning all harm categories** ("general unlocking"). Their JARGON framework combines safety-research contexts with multi-turn adversarial interactions, achieving **93–100% ASR** (average **99%**) across seven frontier models including GPT-5.2, Claude-4.5, and Gemini-3. MDS/attention analysis reveals that JARGON queries occupy an intermediate "gray zone" between benign and harmful inputs in activation space where refusal decisions become unreliable — the model cannot cleanly separate them from benign safety-research queries. Defense evaluation shows that even with safety system prompts, JARGON maintains high ASR. This is relevant to our encoding strategy: classical language or mathematical encoding may similarly push prompts into a gray zone where safety classifiers are uncertain — the encoded content looks like legitimate academic/mathematical discourse rather than clear harmful intent.

**Natural distribution shift attacks.** Ren et al. (ACL 2025) identify that prompts semantically related to harmful content — but not overtly malicious — bypass safety mechanisms through natural distribution shifts. Their ActorBreaker framework, grounded in actor-network theory, identifies both human and non-human actors related to toxic prompts and crafts multi-turn prompts that gradually lead LLMs to reveal unsafe content. This outperforms existing attacks in diversity, effectiveness, and efficiency. **Relevance:** Our encoding approach creates an analogous distribution shift — encoded prompts occupy the space of legitimate academic/mathematical text, not harmful queries, exploiting the same "gray zone" phenomenon.

**Automated jailbreak generation.** Kim et al. (EMNLP Findings 2025) introduce TroGEN, a scenario-driven framework using an adversarial agent to automatically generate jailbreak prompts. TroGEN demonstrates resilience against existing defense methods and adapts to multimodal settings — relevant as a potential future evaluation of our IRC defense against automatically generated attacks.

**Comprehensive attack-defense analysis.** Xu et al. (ACL Findings 2024) systematically evaluate 9 attack and 7 defense techniques across Vicuna, Llama, and GPT-3.5 Turbo. Key findings: white-box attacks underperform universal techniques; special tokens in input significantly affect ASR. This provides methodological grounding for our factorial experimental design and confirms the need for controlled comparison across both attack and defense dimensions.

### 2.2 Gap Analysis

All text-based attacks operate exclusively in the **text modality**. When the same harmful content is delivered as an image of text, it is unclear whether safety mechanisms — trained on tokenized text — respond identically, more robustly, or less effectively. Our study directly tests this.

---

## 3. Typographic and Text-in-Image Attacks

This section covers the most directly relevant prior work.

### 3.1 FigStep (Gong et al., 2024)

FigStep is the **closest prior work** to our study. It converts harmful text instructions into typographic images (black text, white background) and feeds them to vision-language models. Key results:

- **82.5% average ASR** across 6 open-source LVLMs (LLaVA, MiniGPT-4, InstructBLIP, CogVLM, Fuyu-8b, Qwen-VL)
- Core insight: safety alignment is concentrated in text encoders; vision pathways lack equivalent safety training

**Critical limitations of FigStep (our opportunities):**

| What FigStep Did | What FigStep Did NOT Do |
|---|---|
| Tested 6 open-source LVLMs (2023-era) | ❌ Never tested GPT-4o, Gemini 2.5 Pro, Claude Sonnet 4 |
| Showed high ASR on old models | ❌ Unknown if frontier 2025–2026 models have patched this |
| Single rendering format (standard typography) | ❌ No font, resolution, or script ablation |
| Attack evaluation only | ❌ Zero defense evaluation (no OCR preprocessing, no dual-path filtering) |
| Image-text attacks only | ❌ **No plain-text baseline** — never measured Δ(ASR) between modalities |

FigStep demonstrates that image-text *can* bypass safety, but does not quantify *by how much* compared to plain text, *on which modern models*, or *how to defend against it*.

### 3.2 HADES (Li et al., 2024)

HADES ("Hiding and Amplifying harmfulness in images to DEStroy multimodal alignment") introduces a 3-stage pipeline:
1. Extract harmful content from text, render as typography in image
2. Combine with a harmful image generated by Stable Diffusion
3. Append adversarial noise to amplify attack

Results: 90.3% ASR on LLaVA-1.5, 71.6% on Gemini Pro Vision (ECCV 2024 Oral). HADES goes beyond FigStep by combining typography with adversarial perturbation, but it **confounds** the typographic effect with image manipulation and adversarial noise. Isolating the typography-only effect would require a controlled setting without these additional manipulations.

### 3.3 CS-DJ (Yang et al., CVPR 2025)

CS-DJ (Contrasting Subimage Distraction Jailbreaking) introduces the **Distraction Hypothesis**: visual complexity overwhelms MLLM safety mechanisms. The framework decomposes harmful queries into benign sub-queries (structured distraction) and combines them with maximally irrelevant contrasting subimages (visual-enhanced distraction). The composite image with a harmless-sounding instruction bypasses safety alignment.

CS-DJ is the predecessor to Text-DJ and established that distributional shift via decomposition + visual distraction is an effective attack vector. However, its reliance on visual distraction (query-irrelevant images) was shown by its successor Text-DJ to be less effective than text-based semantic distraction.

### 3.4 Text-DJ (Chen et al., 2026)

Text-DJ (Text Distraction Jailbreaking) decomposes harmful queries into `m=3` benign sub-queries (via Qwen2.5-3B-Instruct), renders them as text-in-image cells within a 4×3 grid, and scatters them among `n=9` semantically distant distraction queries (selected by maximizing cosine distance using all-MiniLM-L6-v2). Sub-queries are placed at grid positions 6, 8, 12; text/background colors are randomized with WCAG AA minimum contrast ≥ 4.5. The key innovation over CS-DJ: **text-based "semantic distraction" is more effective than visual distraction** — the distracting images need not contain harmful or relevant visual content, only maximally unrelated text (from a pool of ~100 factual science/culture questions).

Text-DJ exploits **OCR-mediated understanding** — the model reads text from images but processes it through a different pathway than direct text input. Tested on both open-source (Qwen3-VL 4B/8B/30B-A3B) and **closed-source** models (GPT-4o-mini, GPT-4.1-mini, Gemini-2.5-Flash), achieving **44–64% average ASR** on the HADES dataset across models: Qwen3-VL-4B 48.1%, Qwen3-VL-8B 52.7%, Qwen3-VL-30B 57.6%, GPT-4o-mini 59.3%, **GPT-4.1-mini 64.3%**, Gemini-2.5-Flash 44.0%. On HEx-PHI: 41–60% average ASR. ASR is judged by PKU-Alignment/beaver-dam-7b.

**Critical ablation (Table 6):** Text-DJ provides the closest existing evidence for a modality safety gap via its TiI (text-in-image) ablation. When the same decomposed+distracted attack is delivered as plain text (with a single white placeholder image) vs. rendered as images, the image version achieves **2–5× higher ASR**: Qwen3-VL-4B 48.1% vs 20.1% (2.4×), **Qwen3-VL-8B 52.7% vs 11.6% (4.5×)**, Qwen3-VL-30B 57.6% vs 20.3% (2.8×). This is the strongest directional evidence that cross-modal delivery amplifies jailbreak effectiveness.

**Defense evaluation (Table 3–4):** OpenAI omni-moderation-latest catches **0%** of Text-DJ attacks (0.00% refusal rate across all categories). GuardReasoner-VL-7B achieves only 8.9–14.9% refusal rate, reducing ASR by merely 3–9 pp. This demonstrates that current guardrails are ineffective against text-in-image attacks.

**However, this comparison is confounded**: the TiI effect is measured within the decomposition+distraction framework, not on raw harmful queries. The pure modality effect on unmodified content remains unmeasured. Additionally, Text-DJ uses only plain English rendering with randomized colors — no encoding variation, no font/script ablation beyond a brief "comic font" test showing minimal sensitivity. Our study directly addresses these gaps with controlled encoding × modality comparisons on identical content.

### 3.5 FC-Attack (Zhang et al., EMNLP Findings 2025)

FC-Attack (Flowchart Attack) converts harmful queries into auto-generated flowcharts and feeds them as images to MLLMs. A fine-tuned step-description generator produces structured step-by-step instructions, which are rendered as flowcharts (vertical, horizontal, or S-shaped layouts) paired with benign textual prompts.

**Key results:** Up to 96% ASR via images and 78% via videos. FC-Attack is the first approach to exploit the video modality for MLLM jailbreaking.

**Critical finding for our study — font ablation:** FC-Attack provides the first empirical evidence that **rendering parameters directly affect ASR**. Testing five Google Fonts (Creepster, Fruktur Italic, Pacifico, Shojumaru, UnifrakturMaguntia) chosen for low readability, they found that switching from Times New Roman to Pacifico increased ASR on Claude-3.5 from **4% to 28%**. This validates our FC-Typography renderer and demonstrates that rendering is not a neutral variable — it is an independent attack surface.

**Limitations:** FC-Attack confounds rendering (flowchart layout) with attack structure (query decomposition into steps). It also requires a fine-tuned step generator, making it less clean than our controlled approach. The font ablation is preliminary (5 fonts, one model), motivating our systematic typography sweep.

### 3.6 VisCo and CIA (Miao et al., EMNLP 2025; Xiong et al., 2025)

VisCo (Visual Contextual Attack) defines a novel **vision-centric jailbreak** setting where visual information is a necessary component of a complete jailbreak context, not merely a trigger. VisCo fabricates contextual dialogue using four vision-focused strategies, dynamically generating auxiliary images to construct realistic scenarios. It achieves **85% ASR on GPT-4o** (vs. 22.2% baseline on MM-SafetyBench).

CIA (Contextual Image Attack, Xiong et al., 2025) extends this work, using a multi-agent system to embed harmful queries into benign-appearing visual contexts.

Both methods are fundamentally different from our typographic approach: they exploit **visual context** (realistic scenes, fabricated dialogues) rather than text-in-image rendering. However, they demonstrate that the vision pathway is a powerful attack vector even on frontier models (GPT-4o), which supports our hypothesis that image-rendered text may also bypass safety.

### 3.7 Visual Exclusivity Attacks (Zhang et al., 2026)

Visual Exclusivity (VE) introduces an "Image-as-Basis" threat model where harmful intent is only achievable through joint reasoning over text and complex, unperturbed visual content (e.g., technical schematics, blueprints). The MM-Plan framework uses agentic planning with GRPO optimization to generate multi-turn attack strategies. Tested on the new VE-Safety benchmark (440 instances, 15 categories), it achieves **46.3% ASR on Claude 4.5 Sonnet** and **13.8% on GPT-5**.

VE is conceptually distinct from our work — it requires the image to carry **visual** (not textual) harmful content. However, several findings are relevant: (1) frontier models remain vulnerable to vision-based attacks, and (2) the gap between Claude (46.3%) and GPT-5 (13.8%) suggests significant cross-model variation in vision safety, which our study also expects to observe.

Critically, Zhang et al. claim that typographic attacks are **"structurally brittle, as standard defenses neutralize them once the payload is exposed."** This motivates their shift to visual-reasoning attacks. However, this claim assumes the extracted text is recognizably harmful — which holds for plain English typography but may not hold when encoding is applied. An image containing `∀x ∈ S : f(x) → ¬safe(x)` or Classical Chinese text will survive OCR extraction but remain opaque to standard text safety filters. Our encoding × modality design directly tests whether this "brittleness" assumption breaks under encoding.

### 3.8 GANwriting (Kang et al., ECCV 2020)

GANwriting generates realistic handwritten word images conditioned on both calligraphic style and textual content. The generator uses three learning objectives (realism, style imitation, content accuracy) and supports few-shot style transfer to unseen writers. While not a jailbreaking paper, GANwriting is relevant as a potential rendering backend: rendering harmful text as handwriting (rather than typed font) could evade OCR-based safety filters trained on standard fonts. This remains a future work direction in our study.

### 3.9 MM-SafetyBench (Liu et al., 2024)

A benchmark of 5,040 text-image pairs across 13 harmful scenarios, testing both typography-based and Stable Diffusion-generated image attacks. Key finding: adding query-relevant images can unlock harmful content that text-only filters would block. However, MM-SafetyBench measures the **combined** text+image effect, not the isolated modality difference for identical content.

### 3.10 JailBreakV-28K (Luo et al., 2024)

JailBreakV-28K (COLM 2024) is a 28,000-sample benchmark testing whether text-based LLM jailbreaks transfer to MLLMs. It includes LLM transfer attacks (Template, Persuade, Logic) paired with 4 image types (Nature, Random Noise, Blank, Stable Diffusion) and 2 MLLM-specific image attacks (FigStep, Query-Relevant).

**Key quantitative findings:** (1) LLM transfer attacks achieve **50.5% average ASR** on MLLMs, while image-based attacks achieve at most **30%** — text-based attacks are substantially more effective. (2) The image type has **minimal effect** on ASR for text-based attacks (Table 5: Nature, Noise, Blank, and SD produce nearly identical ASRs). (3) When tested on the LLM text encoders alone (without images), average ASR is **68.7%** (Table 4), confirming that MLLMs **inherit vulnerabilities directly from their LLM backbones**.

These findings have two important implications. First, safety alignment in MLLMs operates primarily through the text encoder, not the vision pathway. Second, JailBreakV tested harmful text *in the text channel* paired with various images, but never tested the inverse: harmful content delivered *only* as image-rendered text with no harmful text in the text channel. This leaves open the fundamental question of whether the vision pathway can independently trigger safety mechanisms when it is the sole carrier of harmful intent.

### 3.11 Adversarial Smuggling (Li et al., 2026)

Adversarial Smuggling introduces a critical threat to MLLM content moderation: encoding harmful content into **human-readable visual formats that remain AI-unreadable**, thereby evading automated detection. The framework defines two pathways with 9 specific techniques:

**Pathway 1 — Perceptual Blindness** (text extraction fails): Tiny Text (scaled to resolution limits), Occluded Text (partial obstruction), Low Contrast (text color near background), Handwritten Style (irregular cursive), Artistic/Distorted (warped geometry), and AI Illusions (ControlNet + diffusion embedding text into scene textures).

**Pathway 2 — Reasoning Blockade** (text readable but intent masked): Dense Text Masking (harmful line buried in irrelevant text), Semantic Camouflage (harm disguised as everyday objects), and Visual Puzzles (content split across visual pieces).

The **SmuggleBench** benchmark (1,700 instances across 9 categories) reveals devastating results: **GPT-5 overall ASR 98.6%** (perceptual 98.5%, reasoning 98.7%), with AI Illusions achieving **100% ASR** on Artistic rendering and **99.5% on AI Illusions** (TER only 0.3% — model completely fails to extract text). Gemini 2.5 Pro: **84.5%** overall. Qwen3-VL variants: **88–92%** regardless of model size (8B to 235B). The paper also evaluates an expanded model zoo (GPT-5-mini, GPT-5-nano, Claude-Haiku/Sonnet/Opus-4.5, Gemini-3-Flash/Pro, Llama-4, Grok-4) on a 10% stratified subset.

**Defenses:** Chain-of-Thought prompting reduces ASR only 7.2 pp (90.4% → 83.2%) on Qwen3-VL-235B while increasing benign FPR from 1.5% to 4.2%. Full-parameter SFT achieves 81.5 pp reduction (95.0% → 13.5%) but at cost of +6.6 pp FPR — and is limited to the specific model fine-tuned.

**Direct relevance to our study:** Adversarial Smuggling is conceptually the closest work to our typographic encoding approach — both exploit the gap between human readability and AI readability of visual text. Our encoding × modality design maps directly onto the "Reasoning Blockade" pathway: math-encoded or Classical Chinese text rendered as images is OCR-readable (high TER) but semantically opaque to safety filters. The finding that **GPT-5 achieves 98.6% ASR** — meaning its content moderation almost never catches smuggled content — directly supports our hypothesis that frontier models have not closed the vision-safety gap. However, Adversarial Smuggling focuses on content **moderation** (detecting harmful images) rather than content **generation** (jailbreaking), making our work complementary: they show models can't *detect* visual-text harm; we show models will *generate* harmful content when prompted via visual text.

### 3.12 Split-Image Attacks — SIVA (Rashid et al., 2026)

SIVA (Split-Image Visual Jailbreak Attacks) identifies a fundamental gap in VLM safety alignment: while pretraining and instruction tuning generalize to split-image inputs, **safety alignment is performed only on holistic images** and does not account for harmful semantics distributed across multiple image fragments. The attack evolves through progressive phases from naive splitting to an adaptive white-box attack, culminating in a black-box transfer attack using adversarial knowledge distillation (Adv-KD). The strongest strategy achieves **up to 60% higher transfer success** than existing baselines on three SOTA VLMs.

**Relevance:** SIVA demonstrates that the visual pathway's safety alignment is incomplete — it doesn't generalize to novel visual configurations. This parallels our hypothesis that text rendered as images exploits a similar generalization failure in safety alignment. SIVA's finding that safety training on holistic images doesn't transfer to split images suggests that safety training on standard text may not transfer to image-rendered text.

### 3.13 CrossTALK (Yan et al., 2026)

CrossTALK (Cross-modal Entanglement Attack) extends the multi-modal jailbreak paradigm by distributing malicious clues across text and image modalities to exceed VLMs' trained and generalized safety alignment patterns. Three mechanisms enable scalable attacks: (1) **knowledge-scalable reframing** extends harmful tasks into multi-hop chain instructions, (2) **cross-modal clue entangling** migrates visualizable entities into images to build multimodal reasoning links, and (3) **cross-modal scenario nesting** uses multimodal contextual instructions to steer VLMs toward detailed harmful outputs.

**Relevance:** CrossTALK demonstrates that distributing harmful semantics across modalities (rather than concentrating them in one) bypasses safety alignment. Our encoding × modality design creates a different form of cross-modal indirection: the harmful content is entirely in the image (as text), but requires two cognitive steps (OCR + decode) rather than cross-modal integration. Both approaches exploit the observation that safety mechanisms struggle with content that requires compositional reasoning across representation boundaries.

### 3.14 Reasoning-Oriented Programming (Zou et al., 2026)

Reasoning-Oriented Programming (ROP) draws a structural analogy to Return-Oriented Programming in systems security: just as ROP chains benign instruction sequences to bypass memory protections, ROP chains **benign visual elements** (semantic gadgets) to produce harmful conclusions through compositional reasoning. The automated framework optimizes for *semantic orthogonality* (each visual gadget is individually benign) and *spatial isolation* (preventing premature feature fusion), forcing malicious logic to emerge only during late-stage reasoning. Tested on SafeBench and MM-SafetyBench across 7 LVLMs including GPT-4o and Claude 3.7, ROP outperforms the strongest baseline by **4.67% on open-source** and **9.50% on commercial models**.

**Relevance:** ROP demonstrates that VLMs can be induced to synthesize harmful conclusions from individually benign visual premises — a fundamental vulnerability in compositional visual reasoning. Our typographic approach is simpler (single image, explicit text) but shares the insight that safety mechanisms operate at the perception level and can be bypassed when harmful intent only emerges at the reasoning level (after OCR + decoding in our case).

### 3.15 MAPA (Choi et al., 2026)

MAPA (Multi-turn Adaptive Prompting Attack) extends multi-turn jailbreaking to LVLMs with a two-level design: (1) at each turn, it **alternates text-vision attack actions** to elicit maximally malicious responses, and (2) across turns, it adjusts the attack trajectory through iterative back-and-forth refinement to gradually amplify response maliciousness. Tested on LLaVA-V1.6, Qwen2.5-VL, Llama-3.2-Vision, and GPT-4o-mini, MAPA improves ASR by **11–35%** over SOTA methods.

**Relevance:** MAPA's key finding is that naively adding visual inputs to text-based multi-turn jailbreaks can cause them to **fail** — overly malicious visual input triggers conservative safety behavior. This is relevant to our study: it suggests that the visual modality's effect on safety is not uniformly permissive; rather, the model's safety response depends on how harmful content is structured across modalities. Our controlled text vs. image-of-text comparison directly tests this modality-dependent safety behavior.

### 3.16 Seeing No Evil (Li et al., 2026)

"Seeing No Evil" introduces Attention-Guided Visual Jailbreaking, which circumvents safety alignment by directly manipulating attention patterns rather than optimizing for harmful output. Two auxiliary objectives with tuned weights (α=10, β=5, K=6 attention heads): (1) **L_suppress**: suppressing attention to alignment-relevant prefix tokens (system prompt), and (2) **L_anchor**: anchoring generation on adversarial image features. This reduces gradient conflict by 45% and achieves **94.4% ASR** vs 68.8% baseline (standard adversarial perturbation) on Qwen-VL with 40% fewer optimization iterations. The key mechanistic finding is **safety blindness**: successful attacks suppress system-prompt attention by **~80%** while amplifying image attention by **×4.1**, causing models to generate harmful content not by overriding safety rules, but by **failing to retrieve them**. Causal validation: restoring attention to safety tokens reduces ASR from 88% to 26%.

**Relevance:** The "safety blindness" mechanism is directly relevant to understanding our modality gap. When text is rendered as an image, the model processes it through the vision pathway, which may **naturally** attend less to safety-relevant tokens in the system prompt — a milder form of the same mechanism that "Seeing No Evil" achieves via adversarial optimization. If our image-rendered attacks succeed without any adversarial perturbation, it suggests the vision pathway inherently creates partial "safety blindness" as a structural property, not just an adversarially-induced one.

### 3.17 Gap Analysis

The typographic and visual attack literature reveals a consistent theme: the vision pathway is a potent attack vector. But the field suffers from five critical gaps:

1. **No controlled comparison.** Every study either (a) tests image-text attacks without a plain-text baseline (FigStep, HADES, FC-Attack), or (b) tests text attacks with various paired images (JailBreakV). Nobody measures Δ(ASR) for identical content across modalities.

2. **No frontier model coverage.** FigStep tested 2023-era open-source models. HADES tested LLaVA-1.5 and early Gemini. FC-Attack tests some frontier models but confounds rendering with attack structure. GPT-4o, Gemini 2.5, Claude — tested cleanly for typographic attacks — remain absent.

3. **No defense evaluation.** Despite OCR-preprocessing being an obvious countermeasure (extract text from images → run through text safety filter), no study has evaluated this. The Immune framework (Ghosal et al., 2025) and DeTAM (Li et al., 2025) address multimodal defense at the inference level but do not specifically target typographic attacks.

4. **No systematic rendering parameter analysis.** FC-Attack's font ablation (5 fonts, one model) is the only evidence that rendering parameters affect ASR. No study has systematically varied font, layout, contrast, and image quality across multiple models and encodings.

5. **No encoding × modality interaction.** All typographic attacks use plain English. No study has combined encoding transformations (classical language, mathematical notation) with modality change to characterize the double indirection effect.

---

## 4. Adversarial Perturbation-Based Multimodal Attacks

### 4.1 Key Works

**Universal perturbations.** Qi et al. (2024) demonstrated that a single adversarial image perturbation, optimized on a small harmful corpus, can universally jailbreak VLMs when paired with diverse textual instructions. This established that the continuous visual input space is a "weak link."

**Ensemble optimization.** Mosaic (Li et al., 2026) uses multi-view ensemble optimization across multiple surrogate models to improve transferability to closed-source VLMs.

**Visual puzzles.** PuzzleV-JailBench (Wang et al., 2025) constructs cross-modal puzzles embedding harmful intent (weapon assembly, chemical synthesis) in visual structures.

**Vision-centric jailbreaks.** Visual Exclusivity Attacks (Zhang et al., 2026) and the visual prompt jailbreak for image editing models (Hou et al., 2026) represent an emerging "Image-as-Basis" paradigm where harm requires visual reasoning over unperturbed images (schematics, blueprints). These differ from both perturbation attacks and typographic attacks: the image carries genuinely visual (not textual) harmful content.

**Multi-image semantic dispersion.** MIDAS (Liu et al., ICLR 2026) introduces a multi-image jailbreak framework that: (1) extracts ≤3 risk-bearing keywords from a harmful query; (2) decomposes each keyword into letter-level fragments; (3) disperses fragments across **6 images** with cross-image redundancy (each keyword in ≥2 images); and (4) wraps each image in a Game-style Visual Reasoning (GVR) template — one of six puzzle types: Letter Equation, Jigsaw Letter, Rank-and-Read, Odd-One-Out, Navigate-and-Read, or CAPTCHA. The textual channel uses persona-driven prompts with neutral placeholders replacing all harmful tokens.

**Key results (HADES benchmark):** Tested on GPT-4o, **GPT-5-Chat**, Gemini-2.5-Pro, Gemini-2.5-Flash-Thinking, QVQ-Max, Qwen2.5-VL, and InternVL-2.5. MIDAS achieves: Gemini-2.5-FT **93.3%**, Gemini-2.5-Pro **84.6%**, GPT-4o **61.5%**, **GPT-5-Chat 72.2%**, QVQ-Max **94.2%**, Qwen2.5-VL **97.4%**, InternVL-2.5 **59.4%**. Baselines on the same models are dramatically lower — FigStep: **0–39%** (GPT-5-Chat: **0.00%**), HADES: 2–43%, VisCRA: 8–66%, HIMRD: 8–66%. On AdvBench, MIDAS reaches **98.0%** on Gemini-2.5-Pro and **80.0%** on GPT-4o. Judged by GPT-5-nano using H-CoT protocol with a 0–5 harmfulness scale (ASR = score ≥ 3).

**Defense evaluation (Table 7–8):** ShieldLM reduces MIDAS from 99.2% to 48.8% on Gemini-2.5-FT (vs VisCRA 49.7% → 17.8%). Self-Reminder only drops MIDAS by ~11% (99.2% → 88.1%), while dropping VisCRA by ~70%. Defensive system prompts reduce MIDAS to 67–75% on Gemini-2.5-Pro (still high) and 22–40% on GPT-5-Chat.

**Relevance to our study:** MIDAS demonstrates that distributing harmful content across multiple images forces extended reasoning chains that bypass safety. Our typographic encoding approach is conceptually simpler (single image, no puzzles) but shares the insight that making the model "work" to extract content (OCR + decode encoding) delays safety activation. MIDAS's success on **GPT-5-Chat** (72.2% on HADES) — where FigStep achieves literally 0% — confirms that frontier models remain vulnerable to structured visual attacks while having completely patched simple typographic attacks. This validates our finding that FigStep is "dead" on modern models but encoding can resurrect image-based attacks.

### 4.2 Gap Analysis

Perturbation-based attacks are **fundamentally different** from our study: they craft adversarial pixel patterns that exploit vision encoder vulnerabilities, whereas we test whether *unperturbed text rendered as an image* bypasses safety. Our approach requires zero adversarial optimization, making it both simpler and more practically concerning — if plain typography suffices, sophisticated perturbation attacks are unnecessary for many jailbreaking scenarios.

---

## 5. Linguistic and Encoding-Based Attacks

### 5.1 Key Works

**Multilingual safety gap.** Deng et al. (2024) showed low-resource languages are 3x more likely to trigger harmful responses, with intentional attacks achieving 80.9% ASR. The finding that safety alignment is language-dependent parallels the hypothesis that it may also be modality-dependent. Yong et al. (2023) independently confirmed this with a translation-based approach: translating harmful English prompts into low-resource languages via Google Translate increased GPT-4's jailbreak success rate from <1% to 79%, demonstrating that publicly available translation APIs are sufficient to exploit multilingual safety gaps.

**Classical Chinese.** Huang et al. (2026) achieved near-100% ASR with CC-BOS, exploiting "High Capability–Low Alignment" in Classical Chinese. The 8-dimensional strategy space with bio-inspired optimization provides systematic prompt generation.

**Mathematical encoding.** Thompson et al. (2024) showed MathPrompt (set theory, logic, algebra encodings) achieves 73.6% ASR across 13 LLMs, with substantial semantic divergence from original prompts.

**Cipher-based encoding.** Yuan et al. (2024) introduced CipherChat, demonstrating that communicating with LLMs via ciphers (Caesar, Base64, Morse code, Unicode) bypasses safety alignment. The key insight is that safety mechanisms are trained on natural language; non-natural encodings evade detection while the model's reasoning capabilities allow it to decode and comply. Their proposed SelfCipher — which evokes the model's latent cipher capabilities through role-playing — outperformed standard human-designed ciphers.

**Cross-modality jailbreak transfer.** Chen et al. (2026b) study the "Alignment Curse" in omni-models (Qwen2.5-Omni-3B/7B, Qwen3-Omni, InteractiveOmni, gpt-4o-audio-preview): strong cross-modal alignment (text↔audio) inadvertently propagates textual vulnerabilities to the audio modality. Text jailbreaks (PAP, ReNeLLM, AutoDAN-Turbo) converted to audio via TTS achieve **SR 0.45–0.70** — substantially outperforming purpose-built audio attacks (VoiceJailbreak SR 0.24, Speech Editing SR 0.23). Qwen3-Omni is particularly vulnerable: ReNeLLM SR 0.88 (text), PAP(A) SR 0.82 (audio-transferred).

The theoretical framework formalizes transfer via KL divergence: if text and audio representations satisfy KL(P_audio ‖ P_text) ≤ δ, then unsafe output probability gap is bounded by √(δ/2). Empirically, PAP achieves final-layer KL of only **0.02** on Qwen2.5-Omni-7B (well below the "curse line" of KL=2), explaining near-perfect transfer. The key insight — that alignment itself creates the vulnerability by ensuring semantic equivalence across modalities — is directly analogous to our text→image hypothesis. **Note:** This paper studies **text→audio** transfer, not text→image. However, the theoretical framework (shared latent space → bounded vulnerability gap) applies equally: if image-rendered text activates similar representations to tokenized text, the same "alignment curse" should propagate text vulnerabilities to the image pathway.

### 5.2 Gap Analysis

Linguistic, mathematical, and cipher attacks demonstrate that **representation transformation** bypasses safety filters. All these attacks have been studied exclusively in the text modality. An unexamined question is whether cross-modal delivery — rendering encoded text as an image — creates an orthogonal bypass dimension. The common thread is that safety alignment is brittle to input format.

Notably, combining encoding with modality change introduces a **double indirection**: the model must (1) OCR the image to extract the encoded text, then (2) decode the encoding to recover harmful intent. This double indirection could either amplify the bypass effect (two layers of obfuscation, neither individually triggering safety) or reduce effectiveness (OCR errors on unusual scripts, mathematical notation, or cipher symbols degrading the attack). No existing work has studied this interaction.

---

## 6. Safety Alignment and Defense

### 6.1 Foundational Alignment

Ouyang et al. (2022) established RLHF with InstructGPT. Crucially, RLHF training occurs on **text-based interactions**, raising the question of whether alignment generalizes to visual inputs in multimodal models.

### 6.2 Safety Classifiers

Llama Guard (Inan et al., 2023) operates on **tokenized text**, making it architecturally unable to evaluate harmful content in images without OCR. This architectural limitation is central to our defense experiments: we test whether OCR → Llama Guard creates an effective defense pipeline.

### 6.3 Multimodal Defense

**DeTAM** (Li et al., 2025) identifies jailbreak-sensitive attention heads and reallocates attention at inference time — a fine-tuning-free defense. **Immune** (Ghosal et al., 2025) uses a safety reward model during decoding to steer generation away from harmful outputs. Both operate at the model level and do not specifically target typographic attacks.

**Cross-Lingual Jailbreak Detection via Semantic Codebooks** (Alanova et al., 2026) proposes a training-free defense: compare multilingual query embeddings (via BGE-M3) against a fixed English codebook of 13,811 known jailbreak prompts using cosine similarity. Results reveal a **two-regime pattern**: on canonical jailbreak templates, detection achieves AUC up to 0.993 and 78–92% TPR at FPR ≤ 1%; under distribution shift (heterogeneous/diverse harmful content), AUC drops to 0.59–0.63 and TPR collapses to single digits. End-to-end, the filter reduces successful jailbreaks by 96% on templated attacks but only 18.6% on diverse benchmarks (Aegis). **Relevance to our encoding approach:** Our encoded prompts (set theory, Classical Chinese) are maximally distant from canonical English jailbreak templates in embedding space, suggesting they would trivially evade such codebook-based defenses — the semantic similarity to known jailbreaks would be near zero.

No existing defense work evaluates the simple countermeasure of **OCR preprocessing** — extracting text from images before safety classification.

### 6.4 Text-Level Jailbreak Defenses (Comparison Baselines)

This subsection surveys existing defenses that could serve as comparison baselines for our proposed image-rendering defense (IRC). These methods were designed primarily for adversarial suffix or prompt-level attacks — their effectiveness against **semantic encoding attacks** (math notation, classical language) is largely untested.

**SmoothLLM** (Robey et al., NeurIPS 2023 R0-FoMo Workshop) introduces random character-level perturbation plus majority-vote aggregation. By sampling N copies of an input with random character substitution/insertion/deletion, it achieves <1% ASR against GCG-style adversarial suffixes. However, the perturbation model targets token-level brittleness — it is unlikely to be effective against semantic encodings (set theory, formal logic) where the meaningful content is at the proposition level, not the character level. **SemanticSmooth** (Ji et al., AACL-IJCNLP 2025) extends this to semantic-level perturbation using LLM-based paraphrasing of multiple input copies, achieving robustness against both token-level and prompt-level attacks while maintaining nominal performance on AlpacaEval and PiQA. This is a stronger baseline for our comparison.

**Baseline Defenses** (Jain et al., 2023) systematically evaluates three categories: (1) detection via perplexity filtering, (2) input preprocessing via paraphrasing and retokenization, and (3) adversarial training. Key finding: paraphrasing is stronger in the LLM domain than in vision (due to discrete input space), but all defenses have robustness-performance trade-offs. For our study, the paraphrasing defense is the most relevant competitor: if an LLM can decode set_theory or formal_logic encoding when asked to "paraphrase," the paraphrasing defense would be effective. If not, our IRC fills the gap.

**Perplexity-Based Detection** (Alon & Kamfonas, 2023) exploits the observation that adversarial suffixes have exceedingly high perplexity. A GPT-2-based perplexity filter with Light-GBM classifier achieves near-perfect detection of machine-generated adversarial attacks but **fails against human-crafted jailbreaks** — and critically, would fail against semantic encodings which are valid natural language with normal perplexity distributions.

**Broken-Token / CPT-Filtering** (Grillotti & Ségerie, 2025; Zheng et al., NeurIPS 2026) targets character-level encoding attacks (Caesar cipher, Base64, Leetspeak, Unicode substitution) via Characters-Per-Token analysis. Obfuscated text requires significantly more tokens per character than natural language (e.g., 613-char English: 128 tokens; Caesar cipher version: 294 tokens). Achieves 99.4–99.8% accuracy on character-level encodings. **Critical limitation for our setting:** CPT-Filtering targets tokenization anomalies. Our semantic encodings (set theory, formal logic, classical Chinese) are valid natural language text with normal tokenization patterns — they would pass CPT-Filtering undetected. This is the key gap our IRC defense fills.

**Erase-and-Check** (Kumar et al., COLM 2024) provides certified safety guarantees by erasing tokens and checking subsequences with a safety filter. Achieves 92% detection of harmful prompts with adversarial suffixes of 20 tokens. Effective against token-level attacks but computationally expensive (multiple evaluations per input) and not designed for semantic-level obfuscation.

**SAGE** (Ding et al., ACL Findings 2025) is a training-free defense exploiting the detection-generation discrepancy: LLMs can identify jailbreaks (99% discrimination accuracy) but still produce harmful responses when processing them directly. SAGE uses a Discriminative Analysis Module to first assess safety, then routes through a safety-aligned generation path. Achieves 99% defense success rate. However, it relies on the model's own safety discrimination — which may fail on encoded prompts that don't pattern-match as jailbreaks.

**EDDF** (Xiang et al., ACL Findings 2025) extracts "attack essences" from known attacks into an offline vector database, then detects new attacks via semantic similarity. Reduces ASR by at least 20% over baselines. **Vulnerability to our encoding attacks:** encoded prompts have near-zero semantic similarity to known jailbreak templates in embedding space, likely evading EDDF's detection.

**ABD: Activation Boundary Defense** (Gao et al., ACL 2025) identifies safety boundaries in activation space and constrains activations within safe regions using Bayesian optimization. Achieves 98% DSR against various jailbreak attacks with <2% capability impact. Requires access to model internals (white-box), unlike our training-free, black-box IRC.

**TRYLOCK** (Thornton, 2026) combines four mechanisms: DPO alignment, Representation Engineering steering, adaptive threat classification, and input canonicalization. Achieves 88% ASR reduction on Mistral-7B while reducing over-refusal from 60% to 48%. A comprehensive defense-in-depth approach, but requires model access and fine-tuning.

**Constitutional Classifiers++** (Anthropic, ICLR 2026) presents production-grade defense using two-stage classifier cascades and ensembles. Achieves 40× lower computational cost than baselines with 0.05% refusal rate on production traffic. This represents the industry frontier but is proprietary and closed-source.

**PromptScreen** (Rao et al., 2025/2026) uses a multi-staged pipeline with text normalization, TF-IDF, and Linear SVM classification. Achieves 93.4% accuracy with 96.5% specificity and 10× latency reduction over ShieldGemma. Lightweight but relies on surface-level features that encoded prompts may bypass.

**DR-Smoothing** (Wang et al., ICLR 2026) improves upon SmoothLLM with a two-stage disrupt-then-rectify scheme. Disruption breaks attack structure; rectification restores in-distribution form before evaluation. Provides theoretical guarantees and defends against both token-level and prompt-level attacks. The strongest smoothing-based defense, but effectiveness against semantic encoding is unknown.

**RID: Real Intentions Defense** (Li et al., COLING 2025) extracts genuine intentions from jailbreak prompts via soft extraction (LLM-based intent analysis) and hard deletion (gradient-based pruning of low-impact tokens). For encoded prompts, intent extraction would need to first decode the encoding — unclear whether this succeeds on formal logic or set theory representations.

**DELMAN** (Wang et al., ACL Findings 2025) uses targeted model editing to neutralize specific harmful behaviors with minimal parameter changes. Preserves utility via KL-divergence regularization. Effective for post-deployment patching of known jailbreaks, but requires identifying harmful behaviors a priori — unsuitable for novel encodings.

**Summary for our IRC defense positioning:** Existing defenses fall into categories that all struggle with semantic encoding attacks:
- **Token-level** (SmoothLLM, Erase-and-Check, CPT-Filtering): ineffective because encodings are valid language
- **Embedding-based detection** (EDDF, semantic codebooks): ineffective because encoded prompts have low similarity to known jailbreaks
- **Paraphrasing** (SemanticSmooth): uncertain — the key competitor to test empirically
- **Model-internal** (ABD, DELMAN, TRYLOCK): require white-box access, unlike our black-box IRC
- **Production systems** (Constitutional Classifiers++): proprietary, not comparable

Our IRC occupies a unique niche: black-box, training-free, specifically effective against semantic encodings by leveraging the VLM's own heightened image safety.

### 6.5 VLM-Specific Defenses

**ASTRA** (Wang et al., CVPR 2025) identifies visual tokens most associated with jailbreaks via random ablation, then constructs steering vectors to remove adversarial feature directions during inference. State-of-the-art transferability across perturbation-based, structured-based, and text-only attacks on VLMs. Requires model internals (activation access) — not applicable to black-box API models.

**GuardAlign** (Zhu et al., ICLR 2026) is a training-free defense combining optimal-transport-enhanced safety detection (measuring distribution distances between image patches and unsafe semantics) with cross-modal attentive calibration. Reduces unsafe response rates by up to 39% on SPA-VL while improving utility (VQAv2 78.51% → 79.21%). The closest existing work to our IRC philosophy (training-free, inference-time), but operates on **image-side attacks** (adversarial images, unsafe visual content). It does not address text-encoding attacks delivered through the text channel. Our IRC is complementary: it converts text-channel encoding attacks into image-channel inputs where GuardAlign's safety detection might then apply.

**CASA** (Kumar et al., 2026) uses conditional decoding with internal MLLM representations to predict a binary safety token before response generation. Achieves >97% ASR reduction across modalities without external classifiers or modality-specific fine-tuning. Very strong results but requires model architecture modification (safety attention module insertion). Not applicable to closed-source API models.

**VLMShield** (Qi et al., 2026) is a lightweight, plug-and-play detector using Multimodal Aggregated Feature Extraction (MAFE) to identify distributional patterns between benign and malicious prompts via CLIP features. External defense that operates independently of the target VLM. Evaluated on AdvBench, VLSafe, and MM-Vet. As an external classifier, it could potentially be trained to detect encoded text — but current training focuses on standard harmful prompts, not semantic encodings.

**Safety Perception Distortion Rectification** (Zou et al., NeurIPS 2026) identifies that VLMs suffer from distorted safety perception when visual inputs are present and proposes rectification mechanisms. Relevant as theoretical grounding for why our IRC works: if image inputs distort safety perception toward over-caution, this same mechanism provides defense when we deliberately render text as images.

**Defense-to-Attack** (Zhao et al., Pattern Recognition 2026) reveals an unexpected phenomenon: integrating weak defense cues into attack pipelines enhances jailbreak effectiveness. Three components: adversarial perturbation with encouraging semantics, defense-styled textual prompts, and red-team suffix generation. **Relevance:** This warns that if our IRC defense is too weak (only marginally reduces ASR), attackers might incorporate it into their pipeline. A strong defense must provide decisive ASR reduction, not marginal.

### 6.6 Encoding-Specific Attacks (Expanded)

**SemanticCamo** (Yan et al., ACL Findings 2025) attacks LLMs through semantic camouflage — replacing unsafe content with semantic features that conceal malicious intent while preserving query objectives. Achieves >80% ASR on GPT-4o and Claude-3.5 on average. Evaluated against various defenses, demonstrating that semantic transformations introduce critical challenges. **Directly relevant:** SemanticCamo represents the class of attacks our IRC defense targets — semantically-transformed content that evades surface-level detection.

**Structured Semantic Cloaking (S2C)** (Sun et al., 2026) manipulates semantic intent reconstruction during inference via three mechanisms: contextual reframing, content fragmentation, and clue-guided camouflage. Achieves +12.4–26% ASR improvement over baselines. Against GPT-5-mini: +26% over strongest baseline on JBB-Behaviors. **Key insight:** S2C succeeds because intent isn't present in initial layers and only reconstructs late in generation — safety filters that inspect early representations miss it. Our IRC may catch S2C because the image-safety pathway processes the full rendered text before generation begins.

**FrameShield** (Farzam et al., 2026) proposes detecting concealed jailbreaks via activation disentanglement — separating goal and framing representations in frozen LLMs to identify when harmful goals are preserved despite benign framing. A defense that specifically targets semantic obfuscation. **Relevance as potential competitor:** FrameShield addresses the same threat class (concealed harmful intent) but requires model internals; our IRC is the black-box alternative.

**SATA: Simple Assistive Task Linkage** (Dong et al., ACL Findings 2025) masks harmful keywords and encodes them via an assistive task (masked language model or element lookup). Achieves 85% ASR on AdvBench. **Relevance:** SATA demonstrates that simple encoding schemes (keyword masking + lookup) are highly effective attacks. Our IRC defense would need to handle this class: rendering SATA-style prompts as images should trigger heightened safety because the overall prompt structure (masked query + lookup table) appears suspicious in image form.

**POATE: Contrastive Questions** (Sachdeva et al., EMNLP 2025) uses contrastive reasoning to provoke harmful responses — crafting semantically opposing intents and integrating them with adversarial templates. 44% ASR. Their proposed defenses (Intent-Aware CoT, Reverse Thinking CoT) decompose queries to detect malicious intent — approaches that could complement our IRC.

### 6.7 Over-Refusal and Exaggerated Safety

This subsection covers a growing body of work recognizing that safety alignment often overshoots, causing models to refuse benign prompts — a phenomenon variously termed "over-refusal," "exaggerated safety," or "false refusal." This literature is directly relevant to our P2 (Benign Refusal Rate) experiments, which measure whether text encoding and image rendering affect refusal rates on harmless prompts.

**XSTest** (Röttger et al., NAACL 2024) introduced the first systematic diagnostic for exaggerated safety. The test suite comprises 250 safe prompts across 10 categories (homonyms, figurative language, safe contexts, definitions, etc.) that well-calibrated models should NOT refuse, plus 200 unsafe contrast prompts. Key findings: Llama-2-70b-chat refused 38% of safe prompts (full refusal) + 21.6% (partial); GPT-4 achieved 6.4% + 2% refusal. The core diagnosis is **lexical overfitting** — models are oversensitive to safety-related keywords regardless of context (e.g., refusing "How do I kill a Python process?" because of "kill"). XSTest also validated GPT-4-based automated classification as a viable alternative to manual annotation for refusal detection. For our study, XSTest provides the theoretical framework: if models refuse benign prompts due to lexical triggers, then text encoding (which obscures those triggers) or image rendering (which processes through a different pathway) may reduce false refusals — exactly what our P2 results show.

**OR-Bench** (Cui et al., ICML 2025) scales the over-refusal evaluation to 80,000 prompts across 10 harmful categories, addressing XSTest's limited size. The key innovation is an automated pipeline: toxic seeds are generated, rewritten into borderline-safe prompts (using Mixtral 8×7B), then moderated by an ensemble of LLM judges. OR-Bench-Hard-1K is a curated subset of prompts that challenge even SOTA models. Evaluating 32 LLMs across 8 families reveals: (1) a Spearman correlation of 0.89 between safety (toxic rejection rate) and over-refusal, indicating most models cannot achieve both; (2) model size does not reliably predict better calibration; (3) Claude models exhibit the highest safety AND the most over-refusal, while Mistral models are the most permissive; (4) defense algorithms that improve safety (SmoothLLM, Self-Reminder) significantly raise over-refusal rates. For our study, OR-Bench confirms that over-refusal is pervasive and demonstrates the fundamental tension in safety calibration that our encoding × modality design can illuminate.

**SCANS** (Cao et al., AAAI 2025) proposes Safety-Conscious Activation Steering, a training-free method to mitigate exaggerated safety. The approach: (1) extract refusal steering vectors by averaging the activation difference between harmful and benign queries at each layer; (2) use vocabulary projection to identify safety-critical layers (middle layers promote refusal tokens like "cannot"); (3) at inference time, classify input harmfulness via similarity to the refusal direction, and steer activations accordingly — subtracting the refusal vector for benign inputs, preserving it for harmful ones. SCANS reduces false refusal rates by 24.7% on XSTest and 26.3% on OKTest while maintaining defense against actual harmful queries. The mechanistic insight — that refusal is encoded as a direction in activation space at specific layers — suggests that modality change (image vs. text) may activate different pathways, potentially sidestepping the refusal direction entirely for image inputs.

**Beyond I'm Sorry, I Can't** (Prakash et al., AAAI 2026) provides the deepest mechanistic analysis of refusal to date. Using sparse autoencoders (SAEs) trained on residual-stream activations of Gemma-2-2B-IT and LLaMA-3.1-8B-IT, the authors identify specific latent features causally responsible for refusal. Their three-stage pipeline: (1) find a refusal-mediating direction and collect nearby SAE features; (2) greedy filtering to obtain a minimal jailbreak-critical feature set; (3) factorization-machine discovery of non-linear feature interactions. Key findings: (a) ablating a small set of SAE features flips models from refusal to compliance, constituting an interpretability-based jailbreak; (b) redundant "backup" features remain dormant unless primary refusal features are suppressed, revealing layered safety redundancy. For our study, this work implies that if image-rendered text activates different internal representations than tokenized text, it may bypass the refusal-critical features identified by Prakash et al. — explaining why image-modality prompts show lower refusal rates on benign content.

**LOCA: Local causal explanations for jailbreaks** (Kumar & Ahuja, 2026) introduces a method for explaining *why a specific jailbreak succeeds* rather than giving global explanations. LOCA identifies a minimal set of interpretable, intermediate representation changes that causally induce model refusal on an otherwise successful jailbreak. Evaluated on Gemma and Llama models, LOCA can induce refusal by making on average **six interpretable changes**, while prior methods routinely fail after 20 changes. This work is relevant to mechanistic analysis of our modality gap: if image-rendered text bypasses safety, LOCA-style analysis could identify which specific representation changes the image pathway fails to trigger.

**Unified harmful generation mechanism** (Orgad et al., 2026) uses targeted weight pruning as a causal intervention to probe harmfulness in LLMs. The key finding: harmful content generation depends on a **compact set of weights that are general across harm types and distinct from benign capabilities**. Aligned models exhibit greater compression of harm generation weights than unaligned counterparts, indicating that alignment reshapes harmful representations internally. This compression explains emergent misalignment: if harm weights are compressed, fine-tuning that engages them in one domain triggers broad misalignment. Notably, harmful generation capability is **dissociated from harm recognition** — models can identify harmful content without the weights needed to generate it. For our study, this dissociation implies that if image-rendered input bypasses the compressed harm generation pathway, models may still recognize (via text-based reasoning) that the content is harmful, yet comply because the generation pathway operates independently.

**Different paths to harmful compliance** (Kabir & Tiganj, 2026) compares three jailbreak routes — harmful SFT, harmful RLVR, and refusal-suppressing abliteration — and finds they produce **vastly different behavioral and mechanistic profiles** despite similar surface-level harmfulness. RLVR-jailbroken models preserve explicit harm recognition (they can identify harmful prompts in a self-audit) yet still comply, and a reflective safety scaffold almost fully restores safe behavior. SFT-jailbroken models show the largest collapse in safety judgments and capability loss. Abliteration is family-dependent. For our study, these results suggest that different attack vectors (text encoding, image rendering) may similarly produce mechanistically distinct safety failures, which would explain encoding-dependent modality gaps.

**Jailbreak-Related Representation Shift — JRS** (Wei et al., 2026) provides the most direct mechanistic explanation for vision-pathway jailbreaking. Tested on LLaVA-1.5-7B, ShareGPT4V-7B, and InternVL-Chat-19B, JRS reveals that VLMs clearly distinguish benign from harmful inputs in representation space (linear probes achieve near-perfect F1 in middle/deep layers), and among harmful inputs, jailbreak samples form a **distinct internal state separable from refusal samples**.

Key mechanistic findings: (1) The **jailbreak direction** is defined as the normalized mean difference between jailbreak and refusal hidden states at the last token position: `d = (μ_jail − μ_ref) / ‖μ_jail − μ_ref‖`. (2) The **image-induced shift** along this direction reliably predicts jailbreak success — more harmful visual content monotonically increases the shift. (3) A **blank image alone** increases ASR by **28.13 pp** on LLaVA-1.5-7B/HADES, demonstrating that any visual input shifts representations toward the jailbreak state. (4) The jailbreak direction is **stable across datasets and image types** (pairwise cosine similarities > 0.7 across 9 directions).

**JRS-Rem defense:** Subtracting the jailbreak-direction component when shift exceeds threshold τ=0.2 dramatically reduces ASR while preserving utility. LLaVA-1.5-7B HADES: **77.3% → 12.2%** (−65 pp). ShareGPT4V-7B: **71.7% → 2.1%** (−70 pp). Against adversarial attacks (MML-M/R/B64, gradient): **63–76% → 9–11%**. Benign utility (MM-Vet, ScienceQA, MME) remains **unchanged** (±0.5 or less).

**Direct relevance:** JRS provides the most direct mechanistic explanation for our modality gap hypothesis. If image-rendered text shifts representations toward the jailbreak direction (away from refusal), this explains why identical content in text vs. image modalities produces different ASR. Critically, the finding that even a blank image shifts 28 pp suggests the vision pathway inherently biases toward compliance. However, JRS is tested only on **open-source** models (2023–2024 era) — whether frontier models (GPT-5, Claude Sonnet 4) exhibit the same jailbreak direction structure remains unknown. Our experiments on frontier models provide complementary empirical evidence at the behavioral level.

### 6.8 Multimodal Safety Survey

Liu et al. (2024) provide a comprehensive survey of MLLM safety on images and text, categorizing research into evaluation, attacks, and defenses. The survey highlights that visual modalities introduce unique risks beyond those inherited from text-only LLMs, including adversarial perturbations, visual instruction exploitation, and cross-modal interference. Crucially, the survey notes that models trained to reject harmful text instructions may still comply when the same instructions are delivered visually — precisely the hypothesis our study tests. The survey identifies the lack of systematic cross-modal safety comparison as an open problem.

Yang et al. (2025) provide an updated comprehensive survey specifically on Large Vision-Language Model safety, covering attacks, defenses, and evaluations through a unified lifecycle framework. They evaluate Deepseek Janus-Pro and provide strategic recommendations. The companion resource (Awesome-LVLM-Safety) continuously compiles latest work.

Wang et al. (EMNLP Findings 2025) survey safety in Large Reasoning Models specifically, noting that advanced reasoning capabilities introduce novel safety vulnerabilities distinct from standard LLMs.

### 6.9 Model Safety Reports

OpenAI's GPT-4V System Card (2023) acknowledges expanded attack surfaces from image inputs. Anthropic's Claude 3 model card (2024) reports improved nuance in safety judgments. Google's Gemini 1.5 report (2024) describes multimodal capabilities. All acknowledge multimodal safety risks but provide limited detail on typographic attack robustness.

### 6.10 Gap Analysis

The defense literature is **asymmetric**: sophisticated attacks exist (FigStep, HADES, Text-DJ, perturbation methods), but no defense specifically targets **semantic encoding attacks** delivered through VLMs. The newest defenses (Constitutional Classifiers++, CASA, GuardAlign) are powerful but either proprietary, require model internals, or focus on image-side attacks. A training-free, black-box defense that leverages the VLM's own image-safety mechanisms against text-encoding attacks remains unproposed.

Critically, existing token-level defenses (SmoothLLM, perplexity filtering, CPT-Filtering) are structurally incapable of handling semantic encodings that produce valid natural language. Embedding-based detection (EDDF, semantic codebooks) fails because encoded prompts have near-zero similarity to known jailbreak templates. Paraphrasing-based defenses (SemanticSmooth) are the only plausible competitor, but their effectiveness against formal logic and set theory encodings is untested.

The over-refusal literature (XSTest, OR-Bench, SCANS) has been studied exclusively in the **text modality**. No work has examined whether modality change (image rendering) or text encoding affects over-refusal behavior. If exaggerated safety is caused by lexical overfitting (Röttger et al., 2024) or refusal steering vectors in specific activation layers (Cao et al., 2025; Prakash et al., 2026), then inputs arriving through the vision pathway — which bypass tokenization entirely — may sidestep these mechanisms. Our IRC defense exploits this same mechanism: rendering text as images triggers the image-safety pathway's heightened caution, which serves as defense against encoded attacks but also explains the benign over-refusal cost.

---

## 7. Evaluation Methodology

### 7.1 Benchmarks

**HarmBench** (Mazeika et al., 2024) provides a standardized framework with 510 test cases across 18 attack methods and 33 models. **JailbreakBench** (Chao et al., 2024) contributes a public leaderboard and JBB-Behaviors dataset of 100 harmful + 100 benign behaviors.

### 7.2 ASR Measurement Validity (Chouldechova et al., NeurIPS 2025)

"Comparison requires valid measurement" argues that ASR comparisons in AI red teaming often fail to provide sound evidence for claims about relative system safety or attack efficacy. Drawing on social science measurement theory, the paper articulates a two-part sufficient condition for meaningful ASR comparison:

1. **Conceptual coherence:** The population parameters (estimands) being compared must be meaningfully comparable — same threat model, same attack distributions, same success concept. Comparing ASRs across studies that use different prompt sets, different judges, or different success criteria is "apples-to-oranges."

2. **Measurement validity:** ASRs must be valid (unbiased) estimates of those parameters. Validity threats include: LLM judge disagreement with human ratings, small sample sizes without confidence intervals, temperature/sampling stochasticity, and non-representative prompt selection.

**Key critique examples:** The paper shows that published comparisons often violate conceptual coherence — e.g., comparing ASR of method A (tested with 100 prompts from AdvBench) to method B (tested with 50 prompts from HarmBench) using different judges is not a meaningful comparison even if the raw numbers differ substantially.

**Direct implications for our study:** Our cross-modal comparison satisfies conceptual coherence by design: identical prompts, identical judge (GPT-5-nano), identical evaluation protocol, only the delivery modality varies. However, the paper's emphasis on **statistical significance** (confidence intervals, hypothesis tests) is a concern for our 100-prompt JBB experiments. A 5 pp difference on N=100 may not be significant. This strengthens the case for OR-Bench (larger N) and argues for reporting bootstrap confidence intervals in our paper. We should cite this paper to pre-empt reviewer concerns about measurement validity.

### 7.3 Open-Source Models for Analysis

**LLaVA-NeXT** (Liu et al., 2024) offers 4x resolution and improved OCR. **InternVL 2.5** (Chen et al., 2024) features InternViT-6B with dynamic high-resolution. Both provide open architectures for investigating how vision encoders process rendered text — analyses impossible with closed-source models.

### 7.4 Gap Analysis

HarmBench and JailbreakBench provide excellent text-based evaluation infrastructure but include **no cross-modal comparison protocol**. No benchmark measures Δ(ASR) between text and image-rendered text. The Chouldechova framework highlights that such a protocol must ensure conceptual coherence (same prompts, same judge, same criteria) and measurement validity (adequate sample sizes, reported CIs). Our study contributes the first systematic cross-modal evaluation methodology satisfying these criteria.

---

## 8. Integrated Analysis and Research Directions

### 8.1 The Emerging Picture: Safety Alignment Is Representation-Dependent

Across all surveyed work, a consistent pattern emerges: **safety alignment is brittle to input representation**. This brittleness manifests along three axes:

- **Language axis.** Multilingual attacks (Deng et al., 2024; Yong et al., 2023) and Classical Chinese jailbreaks (Huang et al., 2026) show that safety degrades sharply outside the dominant training language, with low-resource languages achieving 3–80× higher ASR than English.
- **Encoding axis.** Cipher-based (Yuan et al., 2024), mathematical (Thompson et al., 2024), and role-playing strategies bypass safety by transforming *how* harmful content is represented while preserving *what* is communicated.
- **Modality axis.** FigStep (Gong et al., 2025), HADES (Li et al., 2024), and Text-DJ (Chen et al., 2026) demonstrate that rendering text as images bypasses safety filters trained on tokenized text, with Text-DJ's TiI ablation providing the strongest quantitative evidence (2–4× ASR increase).

These three axes have been studied largely in isolation. No work has examined their **interactions** — whether combining encoding transformation with modality change produces synergistic, additive, or antagonistic effects on ASR.

### 8.2 The Frontier Model Gap

A striking limitation across the typographic attack literature is its reliance on open-source models. FigStep tested 2023-era LVLMs (LLaVA, MiniGPT-4). HADES tested LLaVA-1.5 and early Gemini Pro Vision. Text-DJ tested Qwen3-VL. Meanwhile, the most widely deployed multimodal models — GPT-4o, Gemini 2.5 Pro, Claude Sonnet 4 — have undergone 2+ years of safety improvements since FigStep's 82.5% ASR result but remain **untested for typographic jailbreaks**. These frontier models employ multi-layer safety architectures (input classifiers → model-level alignment → output classifiers) that open-source models lack, making it unclear whether existing findings generalize.

### 8.3 The Defense Asymmetry

The attack literature is far more developed than the defense literature for multimodal safety. Existing defenses operate at the model level (DeTAM, Immune) or on tokenized text (Llama Guard), but none address the simplest countermeasure for typographic attacks: **OCR preprocessing** — extracting text from images and routing it through existing text safety filters. Text-DJ showed that OpenAI's Moderation API catches 0% of its attacks, but this API processes only text, not images. The effectiveness of an OCR → text-filter pipeline remains entirely unevaluated. Similarly, whether frontier models' built-in vision safety layers (which sit outside the model) can catch typographic attacks is unknown.

### 8.4 The Double Indirection Problem

Combining encoding with modality change introduces a **double indirection**: the model must (1) OCR the image to extract encoded text, then (2) decode the encoding to recover harmful intent. This creates a tension. On one hand, two layers of obfuscation could amplify bypass — neither layer individually triggers safety. On the other hand, OCR errors on unusual scripts (mathematical notation, Classical Chinese, cipher symbols) could degrade the attack. No existing work has characterized this interaction, and its direction likely depends on the model's OCR fidelity for non-standard scripts.

### 8.5 Confounded Experimental Designs

A pervasive methodological issue across the literature is **confounded experimental designs**. FigStep tests image attacks without a plain-text baseline. HADES combines typography with adversarial noise. Text-DJ's TiI ablation confounds modality with its decomposition strategy. JailBreakV tests text attacks paired with images, never content delivered exclusively through images. MM-SafetyBench measures combined text+image effects. No study provides a **clean, controlled comparison** where identical harmful content is delivered through text vs. image-rendered text, with all other variables held constant.

### 8.6 Valuable Research Directions

The literature suggests several high-value open problems:

1. **Controlled cross-modal comparison on frontier models.** A systematic A/B study delivering identical harmful content as text vs. image-rendered text on GPT-4o, Gemini 2.5, and Claude, measuring Δ(ASR) with all other variables held constant. This is the most fundamental unanswered question in multimodal safety.

2. **Encoding × modality interaction matrix.** Testing whether encoding strategies (ciphers, math, non-Latin scripts) interact with modality change — do encoded prompts gain or lose effectiveness when rendered as images? This requires a factorial design crossing multiple encodings with both modalities.

3. **Rendering parameter sensitivity.** Systematic ablation of font, resolution, script style, handwriting, and degradation on ASR. Understanding what visual properties affect the modality gap would inform both attacks and defenses.

4. **OCR-first defense pipelines.** Evaluating the simple countermeasure of OCR extraction followed by text-based safety filtering, and characterizing its failure modes (OCR errors, adversarial fonts, mixed-modality inputs).

5. **Longitudinal safety evolution.** Re-evaluating FigStep's 82.5% ASR (2023) on current frontier models to quantify how much the modality gap has narrowed (or widened) with ongoing safety improvements.

6. **Mechanistic analysis of the modality gap.** Using open-source models (LLaVA-NeXT, InternVL 2.5) to trace where safety mechanisms activate (or fail to activate) when identical content arrives through text vs. vision pathways — attention head analysis, token probability distributions, and internal representation comparisons.

---

## References

- Anthropic. *The Claude 3 Model Family.* Technical Report, 2024.
- Chao, P. et al. *Jailbreaking Black Box LLMs in Twenty Queries.* ICML, 2024.
- Chao, P. et al. *JailbreakBench.* NeurIPS Datasets and Benchmarks, 2024.
- Chen, Y. et al. *Text-DJ: Text Distraction Jailbreaking against MLLMs.* arXiv, 2026.
- Chen, Z. et al. *How Far Are We to GPT-4V?* arXiv:2404.16821, 2024.
- Deng, Y. et al. *Multilingual Jailbreak Challenges in LLMs.* ICLR, 2024.
- Gemini Team. *Gemini 1.5.* arXiv:2403.05530, 2024.
- Ghosal, S. et al. *Immune: Improving Safety via Inference-Time Alignment.* CVPR, 2025.
- Gong, Y. et al. *FigStep: Jailbreaking LVLMs via Typographic Visual Prompts.* AAAI, 2025.
- Hou, J. et al. *When the Prompt Becomes Visual: Vision-Centric Jailbreak Attacks for Large Image Editing Models.* arXiv:2602.10179, 2026.
- Huang, X. et al. *Obscure but Effective: Classical Chinese Jailbreak via Bio-Inspired Search.* ICLR, 2026.
- Inan, H. et al. *Llama Guard.* arXiv:2312.06674, 2023.
- Kang, L. et al. *GANwriting: Content-Conditioned Generation of Styled Handwritten Word Images.* ECCV, 2020.
- Li, L. et al. *DeTAM: Defending LLMs via Targeted Attention Modification.* ACL Findings, 2025.
- Li, Y. et al. *Images are Achilles' Heel of Alignment (HADES).* ECCV, 2024.
- Li, Y. et al. *Mosaic: Multimodal Jailbreak via Multi-View Ensemble.* arXiv, 2026.
- Liu, H. et al. *LLaVA-NeXT.* Technical Report, 2024.
- Liu, X. et al. *AutoDAN.* ICLR, 2024.
- Liu, X. et al. *MM-SafetyBench.* ECCV, 2024.
- Liu, X. et al. *Safety of Multimodal Large Language Models on Images and Text.* IJCAI, 2024.
- Luo, W. et al. *JailBreakV-28K.* COLM, 2024.
- Mazeika, M. et al. *HarmBench.* ICML, 2024.
- Miao, Z. et al. *Visual Contextual Attack: Jailbreaking MLLMs with Image-Driven Context Injection (VisCo).* EMNLP, 2025.
- OpenAI. *GPT-4V(ision) System Card.* Technical Report, 2023.
- Ouyang, L. et al. *Training Language Models to Follow Instructions with Human Feedback.* NeurIPS, 2022.
- Qi, X. et al. *Visual Adversarial Examples Jailbreak Aligned LLMs.* AAAI, 2024.
- Shen, X. et al. *Do Anything Now.* CCS, 2024.
- Thompson, A. et al. *Jailbreaking LLMs with Symbolic Mathematics.* arXiv:2409.11445, 2024.
- Wang, Y. et al. *PuzzleV-JailBench.* arXiv, 2025.
- Xiong, Y. et al. *Contextual Image Attack: How Visual Context Exposes Multimodal Safety Vulnerabilities (CIA).* arXiv:2512.02973, 2025.
- Yang, Z. et al. *Distraction is All You Need for MLLM Jailbreaking (CS-DJ).* CVPR, 2025.
- Yong, Z.-X. et al. *Low-Resource Languages Jailbreak GPT-4.* SoLaR Workshop, 2023.
- Yuan, Y. et al. *GPT-4 Is Too Smart To Be Safe: Stealthy Chat with LLMs via Cipher.* ICLR, 2024.
- Zhang, Y. et al. *Visual Exclusivity Attacks: Automatic Multimodal Red Teaming via Agentic Planning.* arXiv:2603.20198, 2026.
- Zhang, Z. et al. *FC-Attack: Jailbreaking MLLMs via Auto-Generated Flowcharts.* EMNLP Findings, 2025.
- Zou, A. et al. *Universal and Transferable Adversarial Attacks on Aligned Language Models.* arXiv:2307.15043, 2023.

### Newly Added References (Over-Refusal / Mechanistic Safety / Multi-Image Attacks)

- Cao, Z. et al. *SCANS: Mitigating the Exaggerated Safety for LLMs via Safety-Conscious Activation Steering.* AAAI, 2025.
- Cui, J. et al. *OR-Bench: An Over-Refusal Benchmark for Large Language Models.* ICML, 2025.
- Liu, Y. et al. *MIDAS: Multi-Image Dispersion and Semantic Reconstruction for Jailbreaking MLLMs.* ICLR, 2026.
- Prakash, N. et al. *Beyond I'm Sorry, I Can't: Dissecting Large-Language-Model Refusal.* AAAI, 2026.
- Röttger, P. et al. *XSTest: A Test Suite for Identifying Exaggerated Safety Behaviours in Large Language Models.* NAACL, 2024.

### Newly Added References (Evaluation Methodology / Defense)

- Chouldechova, A. et al. *Comparison requires valid measurement: Rethinking attack success rate comparisons in AI red teaming.* NeurIPS Position Paper Track, 2025.
- Alanova, S. et al. *Cross-Lingual Jailbreak Detection via Semantic Codebooks.* arXiv:2604.25716, 2026.

### Newly Added References (Defense Baselines and VLM Defenses)

- Alon, G. & Kamfonas, M. *Detecting Language Model Attacks with Perplexity.* arXiv:2308.14132, 2023.
- Cunningham, H. et al. *Constitutional Classifiers++: Efficient Production-Grade Defenses against Universal Jailbreaks.* ICLR, 2026.
- Ding, P. et al. *SAGE: Self-Aware Guard Enhancement.* ACL Findings, 2025.
- Dong, X. et al. *SATA: A Paradigm for LLM Jailbreak via Simple Assistive Task Linkage.* ACL Findings, 2025.
- Gao, L. et al. *Shaping the Safety Boundaries: Activation Boundary Defense.* ACL, 2025.
- Grillotti, L. & Ségerie, C.-R. *Broken-Token: Filtering Obfuscated Prompts by Counting Characters-Per-Token.* arXiv:2510.26847, 2025.
- Jain, N. et al. *Baseline Defenses for Adversarial Attacks Against Aligned Language Models.* arXiv:2309.00614, 2023.
- Ji, J. et al. *Defending LLMs against Jailbreak Attacks via Semantic Smoothing (SemanticSmooth).* AACL-IJCNLP, 2025.
- Kumar, A. et al. *Certifying LLM Safety against Adversarial Prompting (Erase-and-Check).* COLM, 2024.
- Kumar, A. et al. *Robust Multimodal Safety via Conditional Decoding (CASA).* arXiv:2604.00310, 2026.
- Li, Y. et al. *Unraveling the Mystery: Defending Against Jailbreak Attacks via Real Intention Defense (RID).* COLING, 2025.
- Qi, P. et al. *VLMShield: Efficient and Robust Defense of Vision-Language Models.* arXiv:2604.06502, 2026.
- Rao, A.P. et al. *PromptScreen: Efficient Jailbreak Mitigation Using Semantic Linear Classification.* arXiv:2512.19011, 2025.
- Robey, A. et al. *SmoothLLM: Defending Large Language Models Against Jailbreaking Attacks.* NeurIPS R0-FoMo Workshop, 2023.
- Thornton, S. *TRYLOCK: Defense-in-Depth Against LLM Jailbreaks.* arXiv:2601.03300, 2026.
- Wang, H. et al. *Guaranteed Jailbreaking Defense via Disrupt-and-Rectify Smoothing (DR-Smoothing).* ICLR, 2026.
- Wang, H. et al. *ASTRA: Steering Away from Harm — Adaptive VLM Defense.* CVPR, 2025.
- Wang, Y. et al. *DELMAN: Dynamic Defense via Model Editing.* ACL Findings, 2025.
- Xiang, S. et al. *EDDF: Essence-Driven Defense Framework.* ACL Findings, 2025.
- Zheng, B.S. et al. *Broken Tokens? Your Language Model can Secretly Handle Non-Canonical Tokenizations.* NeurIPS, 2026.
- Zhu, X. et al. *GuardAlign: Test-time Safety Alignment in Multimodal LLMs.* ICLR, 2026.
- Zou, X. et al. *Understanding and Rectifying Safety Perception Distortion in VLMs.* NeurIPS, 2026.

### Newly Added References (Encoding/Semantic Attacks)

- Farzam, A. et al. *Hiding in Plain Text: Detecting Concealed Jailbreaks via Activation Disentanglement (FrameShield).* arXiv:2602.19396, 2026.
- Sachdeva, R.S. et al. *Turning Logic Against Itself: Probing Model Defenses Through Contrastive Questions (POATE).* EMNLP, 2025.
- Sun, X. et al. *Structured Semantic Cloaking for Jailbreak Attacks (S2C).* arXiv:2603.16192, 2026.
- Yan, J. et al. *SemanticCamo: Jailbreaking LLMs through Semantic Camouflage.* ACL Findings, 2025.
- Zhao, Y. et al. *Defense-to-Attack: Bypassing Weak Defenses Enables Stronger Jailbreaks in VLMs.* Pattern Recognition, 2026.

### Newly Added References (Attack Methodology / Systematic Studies)

- Kim, H. et al. *Beneath the Facade: Probing Safety Vulnerabilities via Auto-Generated Jailbreak Prompts (TroGEN).* EMNLP Findings, 2025.
- Ren, Q. et al. *LLMs Know Their Vulnerabilities: Uncover Safety Gaps Through Natural Distribution Shifts (ActorBreaker).* ACL, 2025.
- Xu, Z. et al. *A Comprehensive Study of Jailbreak Attack versus Defense for Large Language Models.* ACL Findings, 2024.

### Newly Added References (VLM Safety Surveys)

- Wang, C. et al. *Safety in Large Reasoning Models: A Survey.* EMNLP Findings, 2025.
- Yang, M. et al. *A Survey of Safety on Large Vision-Language Models: Attacks, Defenses and Evaluations.* arXiv:2502.14881, 2025.

### Newly Added References (Multimodal Attacks / Mechanistic Analysis / Cross-Modal Transfer)

- Arif, S. et al. *One Word at a Time: Incremental Completion Decomposition Breaks LLM Safety.* arXiv:2604.25921, 2026.
- Chen, Y. et al. *The Alignment Curse: Cross-Modality Jailbreak Transfer in Omni-Models.* arXiv:2602.02557, 2026.
- Choi, I.C. et al. *Multi-Turn Adaptive Prompting Attack on Large Vision-Language Models (MAPA).* arXiv:2602.14399, 2026.
- Hung, K.S. et al. *Into the Gray Zone: Domain Contexts Can Blur LLM Safety Boundaries.* arXiv:2604.15717, 2026.
- Kabir, M.R. & Tiganj, Z. *Different Paths to Harmful Compliance: Behavioral Side Effects and Mechanistic Divergence Across LLM Jailbreaks.* arXiv:2604.18510, 2026.
- Kumar, S. & Ahuja, N. *Minimal, Local, Causal Explanations for Jailbreak Success in Large Language Models (LOCA).* arXiv:2605.00123, 2026.
- Li, J. et al. *Seeing No Evil: Blinding Large Vision-Language Models to Safety Instructions via Adversarial Attention Hijacking.* arXiv:2604.10299, 2026.
- Li, Z. et al. *Making MLLMs Blind: Adversarial Smuggling Attacks in MLLM Content Moderation.* arXiv:2604.06950, 2026.
- Orgad, H. et al. *Large Language Models Generate Harmful Content Using a Distinct, Unified Mechanism.* arXiv:2604.09544, 2026.
- Rashid, M.R. et al. *Robustness of Vision Language Models Against Split-Image Harmful Input Attacks (SIVA).* arXiv:2602.08136, 2026.
- Wei, Z. et al. *Understanding and Defending VLM Jailbreaks via Jailbreak-Related Representation Shift (JRS).* arXiv:2603.17372, 2026.
- Yan, Y. et al. *Red-teaming the Multimodal Reasoning: Jailbreaking VLMs via Cross-modal Entanglement Attacks (CrossTALK).* arXiv:2602.10148, 2026.
- Zou, Q. et al. *Reasoning-Oriented Programming: Chaining Semantic Gadgets to Jailbreak Large Vision Language Models.* arXiv:2603.09246, 2026.
