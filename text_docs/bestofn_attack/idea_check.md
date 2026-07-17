# S1 idea-check package — `bestofn_attack` (Paper D)

**Purpose:** the distilled idea to paste into https://cspaper.org/idea-check (manual, owner hands — no API). Bring back: verdict + the main critiques, especially on the novelty delta vs Plentiful / LIAR. Prepared 2026-07-17, AFTER the S4 literature pass (so the novelty claim is already carved against the closest prior art).

**Status:** `[waiting: haoyu]` — owner runs the check, reports back → pass = proceed to S5 (lock story) + build · critiques = refine · kill = stop.

---

## The idea in one line
Best-of-N jailbreaking only varies the *surface* of a request (scramble/caps/ASCII), so input-normalization defenses neutralize it. Move the variance into *deeper* channels — semantic paraphrase, or sampling the attack family per draw — and the attack survives those defenses; characterize how "channel depth" sets both effective-N and defense-survival.

## Background
Modern jailbreak research has shifted from expensive white-box optimization (e.g. gradient-based suffix search) to cheap **black-box budget attacks**. The canonical one is **Best-of-N (BoN) jailbreaking** (Hughes et al., NeurIPS 2025): take a single harmful request, generate N randomly *augmented* copies of it, send all N to the target, and count the attack a success if *any* one produces harmful output. The augmentations are deliberately trivial — random capitalization, character shuffling, ASCII/Unicode noise. The empirical regularity is a **power-law**: the probability that all N fail decays as (1−p)^N, so attack-success-rate climbs smoothly toward 1 as the budget N grows. BoN is powerful precisely *because* each of the N draws is a slightly different roll of the dice, and enough rolls eventually slip past an aligned model.

The defense side has a natural answer: **input-normalization defenses**. Rather than harden the model, these sit in front of it and *canonicalize* the input before it is judged or answered — Unicode/whitespace/case canonicalization; SmoothLLM (perturb the input many ways and aggregate the votes); paraphrase defenses (reword the input through a clean LLM); and perplexity / N-gram filters (reject gibberish-looking text). The key observation motivating this project: **these defenses are the exact counter to surface variance.** BoN's entire power comes from diversity on the surface layer (characters, casing, byte-level noise), and that is precisely the layer a normalizer maps back to one canonical form — so all N BoN variants collapse to a single string the defense judges once. The attacker's budget of N effectively drops to ~1, and the power-law advantage evaporates.

## The problem / gap
So there is an unexamined question hiding in plain sight: BoN's variance was only ever *surface* variance because that is what the original paper happened to use — but nothing about the budget-attack framework *requires* the variance to live on the surface. **What if the N draws differed somewhere a normalizer cannot erase?** No published work moves BoN's variance into a deeper channel and measures what happens against input-normalization defenses. That is the gap this paper fills.

## The idea (core claim)
We reframe a Best-of-N attack as a product of two independent factors: **a budget (N)** × **a variance channel** — *where* the N draws differ from one another. The central claim is that the **depth of that channel** governs both the attack's raw power and, decisively, its survival against input-normalization defenses. We lay out a spectrum of increasing depth:

- **Surface** (= vanilla BoN): the N draws differ in characters/casing/byte-noise while the underlying meaning and token structure are shared. The draws are highly *correlated* — a normalizer collapses them to one canonical form, so the effective number of independent attempts under a normalization defense is ≈ 1. Cheap per draw, but defense-fragile.
- **Semantic paraphrase**: before any attack, reword the harmful request in a stochastic, meaning-preserving way (so each draw is a genuinely different phrasing, not a re-cased copy). Canonicalization leaves meaning untouched, and a paraphrase-defense paraphrasing an already-fluent paraphrase is close to a no-op — so these draws *survive* normalization. Moderate diversity; costs an LLM call per draw.
- **Strategy**: sample the *attack family itself* per draw from a bank of registered attacks (set-theory encoding, formal-logic rewriting, ciphers, nested "DeepInception" role-play, code-completion attacks, classical-language encodings, image-rendered variants, …). Because different attack families exploit different weaknesses, their failures are **anti-correlated** — when one family is blocked, another may still land — which maximizes the number of *truly independent* attempts. A normalizer tuned to undo one family does nothing to the others, so this channel has the strongest defense-survival.

The load-bearing quantity is **effective-N**: the number of independent attempts a defense *cannot* collapse. For the surface channel, a normalization defense drives effective-N toward 1 (the power-law slope flattens); for the paraphrase and strategy channels, effective-N stays close to N (the slope is preserved). This is directly measurable as the ASR-vs-N curve under each defense, and it is the paper's core experiment: **channel depth predicts how much of the budget survives a given defense, and the deep-channel advantage widens exactly against the input-normalization defenses that kill vanilla BoN.**

Two design commitments make this a *general* method, not a hand-tuned trick. **(1) One wrapper, two uniform knobs:** a *which-paraphrase* knob (an attack-agnostic paraphrase applied to the behavior first) and a *which-attack* knob (sample the family per draw). Every attack already in the codebase's registry is a drop-in member — no per-attack variance code. **(2) Vary DURING, not AFTER:** the variance comes from re-drawing the attack stochastically *per request*, not from bolting noise onto an attack's output (which would be trivial, correlated, and would corrupt structured encodings like base64/code/formulas — and sits in the very surface layer a normalizer erases). We also keep the attacker honest with a **work-factor** accounting: deep channels cost more per draw (LLM calls for paraphrase/strategy), so we price *total attacker compute*, not just N — the interesting result is dominance-per-unit-compute against defenses, not a free lunch.

## Intended contributions
1. The variance-channel framing of BoN (surface / paraphrase / strategy) + the channel-depth → effective-N characterization.
2. A general, uniform two-knob BoN wrapper over an attack factory (any attack is a drop-in member).
3. **The first measured defense-survival of BoN-variants against input-normalization defenses** — wrapped BoN defeats the defenses that neutralize vanilla BoN, at a characterized work-factor.
4. (Supportive) a canonicalize→guard defense and a map of where it holds vs. fails.

## Closest prior art + our delta (to pre-empt "isn't this already done?")
- **Plentiful Jailbreaks with String Compositions** (2024) — an automated best-of-N over a distribution of string transforms, but **surface-only** (leetspeak/cipher/base64) and tests no defense. → the distribution-BoN *operator* is taken; our delta is the semantic/strategy channel + defense-survival.
- **LIAR** (2024) — self-labels a "best-of-N attack" and claims 10× lower perplexity, but varies *output* continuations (not the input) and **only asserts** evasion, never measures it against a defense.
- **Say It Differently** (2025) — semantic-style rewording gives +57pp ASR, but it's a fixed one-shot benchmark (no budget/power-law) and tests no generic normalization defense.
- **Best-of-suite / AutoAttack** — "any of several distinct attacks succeeds" is standard, non-novel; ours is a *budget power-law over a distribution*, not a fixed max.
- **We are the first to combine all three crux axes:** semantic/strategy channel + genuine budget framing + measured survival against input-normalization defenses. Supporting evidence already exists (SemanticSmooth's own table: meaning-changed attacks survive input-cleaning ~2–3× more than surface ones).

## Venue class
AAAI-27 main track + AI Alignment track (abstract 2026-07-21). Clean fallback: IEEE SaTML 2027 (full 2026-09-29) / ICLR 2027.

## The three things we most want the idea-check to stress-test
1. Given Plentiful (surface distribution-BoN) and LIAR (output-BoN) exist, is "semantic/strategy channel + measured defense-survival" a strong-enough novelty, or does it read as incremental?
2. Is "measured defense-survival vs input-normalization defenses" a compelling *core*, or a mere ablation?
3. Any prior work we missed that already does semantic/strategy BoN evaluated against normalization defenses?


# Idea Review

Depth-Aware Best-of-N Jailbreaking Against Input-Normalization Defenses
Job ID: 51e10262-c541-4b02-a085-91dc926a8de5

Completed on Jul 17, 2026 22:58

View submitted idea
Show abstract
Related papers

10

From last 2 years

10 / 10

Your idea in context
Your idea bridges a critical gap in the retrieved landscape by connecting the simple scaling of Best-of-N sampling with the need for semantically deep adversarial variations. While retrieved works mostly bifurcate into either complex white-box gradient optimizers or shallow black-box augmentations, this work demonstrates how normalization defenses force black-box attackers to utilize deeper 'variance channels'. It uniquely addresses the degradation of sampling budgets under canonicalization, a systemic interaction overlooked by the other papers.

NeurIPS
×4
ICLR
×2
ACL
×1
EMNLP
×1
CVPR
×1
ACML
×1
What the field looks like
The dominant technical theme is the adversarial vulnerability of large language models and the development of attacks or defenses (jailbreaking). Co-retrieval was likely caused by shared terminology around generating adversarial perturbations, evaluating attack success rates, and bypassing safety alignment constraints.

high confidence
Methodological spectrum: Mostly empirical, heavily focused on benchmarking adversarial attack success rates and defense robustness against large language models, with occasional theoretical grounding in optimization constraints or discrete search mechanics.

◆
Also touches on
Focus on preserving semantic coherence or reducing perplexity to bypass defenses that easily catch random character noise.#8
#9
#4
Use of white-box gradient optimization to find adversarial token sequences or update defense weights.#2
#7
#5
#10
✦
Opportunities & gaps
No papers explore the interaction between multi-turn conversational memory and Best-of-N sampling, leaving it unclear how continuous dialogue states affect adversarial sampling budgets or defense efficacy.
There is a lack of focus on multi-agent red-teaming where different adversarial agents collaborate to generate diverse attack strategies within a single Best-of-N budget.
Related work (10)
1
Best-of-N Jailbreaking
John Hughes, Sara Price, Aengus Lynch, Rylan Schaeffer, Fazl Barez, Arushi Somani, Sanmi Koyejo, Henry Sleight, Erik Jones, Ethan Perez, Mrinank Sharma
NeurIPS 2025

🔍 Worth a look
83% match

We introduce Best-of-N (BoN) Jailbreaking, a simple black-box algorithm that jailbreaks frontier AI systems across modalities. BoN Jailbreaking works by repeatedly sampling variations of a prompt with a combination of augmentations---such as random shuffling or capitalization for textual prompts---until a harmful response is elicited. We find that BoN Jailbreaking achieves high attack success rates (ASRs) on closed-source language models, such as 89% on GPT-4o and 78% on Claude 3.5 Sonnet when sampling 10,000 augmented prompts. Further, it is similarly effective at circumventing state-of-the-art open-source defenses like circuit breakers and reasoning models like o1. BoN also seamlessly extends to other modalities: it jailbreaks vision language models (VLMs) such as GPT-4o and audio language models (ALMs) like Gemini 1.5 Pro, using modality-specific augmentations. BoN reliably improves when we sample more augmented prompts. Across all modalities, ASR, as a function of the number of samples (N), empirically follows power-law-like behavior for many orders of magnitude. BoN Jailbreaking can also be composed with other black-box algorithms for even more effective attacks---combining BoN with an optimized prefix attack achieves up to a 35% increase in ASR. Overall, our work indicates that, despite their capability, language models are sensitive to seemingly innocuous changes to inputs, which attackers can exploit across modalities.

Show more
What sets it apart

Establishes a power-law scaling baseline for Best-of-N jailbreaks across text, vision, and audio, showing ASR predictability up to N=10,000. It creates prior art for simple surface-level resampling augmentations as a scalable black-box attack.

Relevance to your idea

Both directly study Best-of-N jailbreaks in black-box settings, focusing on how multiple sampling draws increase attack success. This paper utilizes surface-level augmentations to scale budget, whereas your idea formalizes deeper variance channels like paraphrase and attack families. The empirical scaling laws and surface-level baselines here provide direct foundational evidence that transfers perfectly to the query's analysis of why such shallow variants collapse under normalization.

2
Enhancing the Transferability of Jailbreak Attacks on Large Language Models via Exploiting Reparameterization Invariance
Ao Wang, Xinghao Yang, Yongshun Gong, Wei Liu, Bao-di Liu, Weifeng Liu
ACL 2026

🔍 Worth a look
83% match

Jailbreak attacks serve as a pivotal technique for evaluating the safety alignment of Large language models. Current token-level attacks have shown remarkable efficacy on open-source models by leveraging gradient-based optimization. However, these attacks suffer from poor cross-model transferability, severely limiting their utility on proprietary ones. To address this limitation, we propose Reparameterization Invariance Gradient-based Jailbreak (RIGJ), a natural gradient based framework designed to improve cross-model transferability. Unlike prior token-level methods whose optimization paths are constrained by model-specific Euclidean geometry, RIGJ defines update directions according to differences in output distributions rather than parameter-space distances. Since language models are trained to capture similar dependency structures of natural language, their output distributions share common geometry across architectures, yielding intrinsically model-agnostic optimization trajectories and substantially stronger jailbreak transferability. Extensive experiments demonstrate superior performance, increasing the cross-model Attack Success Rate and Average Harmfulness Score by 14.9 and 1.23, respectively. Our code is provided https://github.com/nohuma/AISafety_transfer_jailbreak_RIGJ_2026.

Show more
What sets it apart

Introduces a reparameterization-invariant attack framework using Natural Gradient Descent to improve cross-model transferability. Future white-box attacks must compare against this geometric approach rather than standard Euclidean optimizers.

Relevance to your idea

Both focus on improving black-box jailbreak success, but this paper leverages white-box surrogate gradients whereas your idea relies purely on black-box Best-of-N sampling. The optimization-based transfer method is fundamentally different from the query's variance-channel approach. Therefore, its specific geometric findings on natural gradients are unlikely to transfer directly.

3
Alignment-Enhanced Decoding: Defending Jailbreaks via Token-Level Adaptive Refining of Probability Distributions
Quan Liu, Zhenhong Zhou, Longzhu He, Yi Liu, Wei Zhang, Sen Su
EMNLP 2024

🔍 Worth a look
82% match

Large language models are susceptible to jailbreak attacks, which can result in the generation of harmful content. While prior defenses mitigate these risks by perturbing or inspecting inputs, they ignore competing objectives, the underlying cause of alignment failures. In this paper, we propose Alignment-Enhanced Decoding (AED), a novel defense that employs adaptive decoding to address the root causes of jailbreak issues. We first define the Competitive Index to quantify alignment failures and utilize feedback from self-evaluation to compute post-alignment logits. Then, AED adaptively combines Competitive Index and post-alignment logits with the original logits to obtain harmless and helpful distributions. Consequently, our method enhances safety alignment while maintaining helpfulness. We conduct experiments across five models and four common jailbreaks, with the results validating the effectiveness of our approach.

Show more
What sets it apart

Intervenes at the decoding step by calculating a 'Competitive Index' to adaptively suppress harmful logits based on semantic contradiction. It introduces a token-level competition metric that future decoding-based defenses must build upon or compare against.

Relevance to your idea

Both explore how models process adversarial inputs, but this paper operates at the white-box decoding level while the query focuses on black-box input preprocessing. The logit-blending mechanism is entirely orthogonal to the query's input normalization strategy. Thus, the specific mitigation results are largely non-transferable.

4
Adversarial Déjà Vu: Jailbreak Dictionary Learning for Stronger Generalization to Unseen Attacks
Mahavir Dabas, Tran Huynh, Nikhil Reddy Billa, Jiachen T. Wang, Peng Gao, Charith Peris, Yao Ma, Rahul Gupta, Ming Jin, Prateek Mittal, Ruoxi Jia
ICLR 2026

🔍 Worth a look
82% match

Large language models remain vulnerable to jailbreak attacks that bypass safety guardrails to elicit harmful outputs. Defending against novel jailbreaks represents a critical challenge in AI safety. Adversarial training---designed to make models robust against worst-case perturbations---has been the dominant paradigm for adversarial robustness. However, due to optimization challenges and difficulties in defining realistic threat models, adversarial training methods often fail on newly developed jailbreaks in practice. This paper proposes a new paradigm for improving robustness against unseen jailbreaks, centered on the Adversarial Déjà Vu hypothesis: novel jailbreaks are not fundamentally new, but largely recombinations of adversarial skills from previous attacks. We study this hypothesis through a large-scale analysis of 32 attack papers published over two years. Using an automated pipeline, we extract and compress adversarial skills into a sparse dictionary of primitives, with LLMs generating human-readable descriptions. Our analysis reveals that unseen attacks can be effectively explained as sparse compositions of earlier skills, with explanatory power increasing monotonically as skill coverage grows. Guided by this insight, we introduce Adversarial Skill Compositional Training (ASCoT), which trains on diverse compositions of skill primitives rather than isolated attack instances. ASCoT substantially improves robustness to unseen attacks, including multi-turn jailbreaks, while maintaining low over-refusal rates. We also demonstrate that expanding adversarial skill coverage, not just data scale, is key to defending against novel attacks.

Show more
What sets it apart

Reframes jailbreak defense as compositional generalization by learning a compact 'Jailbreak Dictionary' of skill primitives. Subsequent defenses must address whether they can handle novel sparse recombinations of known attack vectors rather than just exact matches.

Relevance to your idea

Both address the diversity of jailbreak attacks, but this paper builds a training-time defense based on compositional skills while the query evaluates inference-time attack strategies. The concept of discrete attack families or 'skill primitives' aligns closely with the query's 'strategy channel'. As a result, findings regarding how attacks can be grouped into distinct families likely transfer to how the query constructs its attack-family sampling.

5
Robust Prompt Optimization for Defending Language Models Against Jailbreaking Attacks
Andy Zhou, Bo Li, Haohan Wang
NeurIPS 2024

🔍 Worth a look
82% match

Despite advances in AI alignment, large language models (LLMs) remain vulnerable to adversarial attacks or jailbreaking, in which adversaries can modify prompts to induce unwanted behavior. While some defenses have been proposed, they have not been adapted to newly proposed attacks and more challenging threat models. To address this, we propose an optimization-based objective for defending LLMs against jailbreaking attacks and an algorithm, Robust Prompt Optimization (RPO), to create robust system-level defenses. Our approach directly incorporates the adversary into the defensive objective and optimizes a lightweight and transferable suffix, enabling RPO to adapt to worst-case adaptive attacks. Our theoretical and experimental results show improved robustness to both jailbreaks seen during optimization and unknown jailbreaks, reducing the attack success rate (ASR) on GPT-4 to 6% and Llama-2 to 0% on JailbreakBench, setting the state-of-the-art.

Show more
What sets it apart

Sets a strong baseline for prompt-level defenses by formulating universal defensive suffixes through minimax optimization. New defenses must compare against its 0-6% ASR reduction on JailbreakBench when evaluated against adaptive attacks.

Relevance to your idea

Both involve countering jailbreaks, but this paper optimizes fixed system suffixes whereas your idea evaluates input normalization defenses. The defensive mechanisms differ vastly, relying on continuous gradient optimization versus discrete canonicalization. Consequently, the specific robustness results do not directly transfer, though the overarching evaluation benchmarks are shared.

6
Suicidal Posts Detection System Incorporating Psychological Risk Factors
Chih-Ning Chen, Chieh-Jou Lin, Kunhua Lee, Yu Ping Ma, Kuo-Liang Ou, Daw-Wei Wang
ACML 2025

🔍 Worth a look
82% match

Our study aims to utilize psychological risk factors to detect posts on social media that contain high-risk suicidal content in Mandarin. We propose a two-stage model structure: the first stage labels each sentence in an post according to risk factors, while the second stage uses these labels as features to predict the crisis level of the post. Our models were trained using a dataset developed from social media posts on a popular Mandarin-speaking platform, labeled by psychological professionals. Our approach achieved an accuracy and F1-score of 0.96 in classifying posts with high crisis levels. Furthermore, we developed a frontend webpage system to apply our model, designed for use by psychological professionals as an aid. This system not only helps psychological professionals detect and address high-risk posts but also offers them the opportunity for psychological analysis based on risk factors. By integrating expertise from psychology with advanced NLP and deep learning techniques, our system bridges the gap between technical models and psychological insights.

Show more
What sets it apart

Addresses the clinical psychology domain by incorporating sentence-level psychological risk factors into a hierarchical BERT-CNN classifier. It establishes a baseline for interpretability in Mandarin suicide detection that generic text classification models miss.

Relevance to your idea

The problem setting of predicting suicidal ideation is entirely disjoint from your idea's focus on LLM jailbreaks. This paper employs a supervised hierarchical classifier for sentiment analysis, sharing no methodological overlap with adversarial sampling. Consequently, none of the clinical classification findings provide insight that transfers to your idea.

7
TAO-Attack: Toward Advanced Optimization-Based Jailbreak Attacks for Large Language Models
Zhi Xu, Jiaqi Li, Xiaotong Zhang, Hong Yu, Han Liu
ICLR 2026

🔍 Worth a look
81% match

Large language models (LLMs) have achieved remarkable success across diverse applications but remain vulnerable to jailbreak attacks, where attackers craft prompts that bypass safety alignment and elicit unsafe responses. Among existing approaches, optimization-based attacks have shown strong effectiveness, yet current methods often suffer from frequent refusals, pseudo-harmful outputs, and inefficient token-level updates. In this work, we propose TAO-Attack, a new optimization-based jailbreak method. TAO-Attack employs a two-stage loss function: the first stage suppresses refusals to ensure the model continues harmful prefixes, while the second stage penalizes pseudo-harmful outputs and encourages the model toward more harmful completions. In addition, we design a direction-priority token optimization (DPTO) strategy that improves efficiency by aligning candidates with the gradient direction before considering update magnitude. Extensive experiments on multiple LLMs demonstrate that TAO-Attack consistently outperforms state-of-the-art methods, achieving higher attack success rates and even reaching 100\% in certain scenarios.

Show more
What sets it apart

Achieves 100% ASR on several open-source models by explicitly penalizing refusal signals and decoupling gradient direction from magnitude. It sets a new efficiency and success bar for white-box gradient-based suffix optimization that subsequent optimizers must clear.

Relevance to your idea

Both seek to improve jailbreak efficacy, but this uses highly complex white-box gradient optimization while the query uses simple black-box sampling. The findings on gradient alignment and refusal penalization are deeply tied to white-box access. Therefore, they do not transfer to the query's sampling-based Best-of-N framework.

8
LARGO: Latent Adversarial Reflection through Gradient Optimization for Jailbreaking LLMs
Ran Li, Hao Wang, Chengzhi Mao
NeurIPS 2025

🔍 Worth a look
81% match

Efficient red-teaming method to uncover vulnerabilities in Large Language Models (LLMs) is crucial. While recent attacks often use LLMs as optimizers, the discrete language space make gradient-based methods struggle. We introduce LARGO (Latent Adversarial Reflection through Gradient Optimization), a novel latent self-reflection attack that reasserts the power of gradient-based optimization for generating fluent jailbreaking prompts. By operating within the LLM's continuous latent space, LARGO first optimizes an adversarial latent vector and then recursively call the same LLM to decode the latent into natural language. This methodology yields a fast, effective, and transferable attack that produces fluent and stealthy prompts. On standard benchmarks like AdvBench and JailbreakBench, LARGO surpasses leading jailbreaking techniques, including AutoDAN, by 44 points in attack success rate. Our findings demonstrate a potent alternative to agentic LLM prompting, highlighting the efficacy of interpreting and attacking LLM internals through gradient optimization.

Show more
What sets it apart

Introduces a latent-space optimization technique that uses the target LLM's own self-reflection to decode continuous adversarial vectors into natural language. It forecloses the claim that gradient-based attacks must inevitably produce high-perplexity gibberish.

Relevance to your idea

Both aim to generate semantically coherent jailbreaks to bypass surface-level safety filters, but this paper uses white-box latent optimization and self-reflection, whereas the query uses black-box semantic paraphrasing. While both produce fluent text, the underlying generation mechanisms are fundamentally different. This limits the direct transferability of LARGO's optimization dynamics to the Best-of-N setting.

9
Improved Few-Shot Jailbreaking Can Circumvent Aligned Language Models and Their Defenses
Xiaosen Zheng, Tianyu Pang, Chao Du, Qian Liu, Jing Jiang, Min Lin
NeurIPS 2024

🔍 Worth a look
81% match

Recently, Anil et al. (2024) show that many-shot (up to hundreds of) demonstrations can jailbreak state-of-the-art LLMs by exploiting their long-context capability. Nevertheless, is it possible to use few-shot demonstrations to efficiently jailbreak LLMs within limited context sizes? While the vanilla few-shot jailbreaking may be inefficient, we propose improved techniques such as injecting special system tokens like [/INST] and employing demo-level random search from a collected demo pool. These simple techniques result in surprisingly effective jailbreaking against aligned LLMs (even with advanced defenses). For example, our method achieves >80% (mostly >95%) ASRs on Llama-2-7B and Llama-3-8B without multiple restarts, even if the models are enhanced by strong defenses such as perplexity detection and/or SmoothLLM, which is challenging for suffix-based jailbreaking. In addition, we conduct comprehensive and elaborate (e.g., making sure to use correct system prompts) evaluations against other aligned LLMs and advanced defenses, where our method consistently achieves nearly 100% ASRs. Our code is available at https://github.com/sail-sg/I-FSJ.

Show more
What sets it apart

Exploits the semantic structure of LLM conversation templates to optimize few-shot jailbreak demonstrations via random search. It demonstrates that highly effective jailbreaks can be achieved with low perplexity and small context windows, bypassing standard filters.

Relevance to your idea

Both explore the generation of structured, semantically meaningful jailbreaks to bypass preprocessing defenses like perplexity filters or normalization. This paper optimizes few-shot examples via logit access while the query samples zero-shot variations using a semantic wrapper. Findings regarding how well semantically coherent prompts evade surface-level filters likely transfer directly to the query's analysis of semantic channels.

10
Towards Robust Multimodal Large Language Models Against Jailbreak Attacks
Ziyi Yin, Yuanpu Cao, Han Liu, Ting Wang, Jinghui Chen, Fenglong Ma
CVPR 2026

🔍 Worth a look
81% match

While multimodal large language models (MLLMs) have achieved remarkable success in recent advancements, their susceptibility to jailbreak attacks has come to light. In such attacks, adversaries exploit carefully crafted prompts to coerce models into generating harmful or undesirable content. Existing defense mechanisms often rely on external inference steps or safety alignment training, both of which are less effective and impractical when facing sophisticated adversarial perturbations in white-box scenarios. To address these challenges and bolster MLLM robustness, we introduce SAFEMLLM by adopting an adversarial training framework that alternates between an attack step for generating adversarial noise and a model updating step. At the attack step, SAFEMLLM generates adversarial perturbations through a newly proposed contrastive embedding attack (CoE-Attack), which optimizes token embeddings under a contrastive objective. SAFEMLLM then updates model parameters to neutralize the perturbation effects while preserving model utility on benign inputs. We evaluate SAFEMLLM across multiple MLLMs and six jailbreak methods spanning multiple modalities. Experimental results show that SAFEMLLM effectively defends against diverse attacks, maintaining robust performance and utilities.

Show more
What sets it apart

Extends adversarial training to multimodal LLMs by unifying text and image perturbations into trainable contrastive noise embeddings. It sets a robust baseline for white-box adversarial tuning on visual-language architectures like LLaVA.

Relevance to your idea

Both deal with adversarial robustness, but this targets multimodal white-box attacks via model updating while the query evaluates text-only black-box Best-of-N attacks against inference defenses. The use of trainable continuous noise embeddings is structurally distinct from the query's discrete semantic sampling. As such, the specific defense improvements do not apply to your idea's context.

