# Future Work — Coverage-Complete Defense line

This catalogs deferred directions split out of `proposal.md` (it was the proposal's §11). Everything here is a **separate contribution that builds on the coverage-complete guard — not part of the shipping paper.** Each top-level section is one project or line; subsections are its component points. Rough ordering: §1 is the direct follow-on, §2 the explanatory layer, §3 a gated orthogonal project, §4 a separate (further-out) line, §5 a low-priority exploratory direction, §6 a near-term extension of the current paper (not a standalone project).

---

## 1. Unified defense against compound & split attacks — the direct follow-on paper

The next defense paper: one guard robust to the portfolio **and** new compound attacks **and** (where possible) cross-modal splitting, evaluated with held-out generalization and the full safety–utility frontier. Stronger as a follow-on precisely because *this* project will have characterized the threat space it must defend. §1.1 and §1.2 are the attacks it must introduce; §1.3 is the defense.

### 1.1 Compound (single-input) attacks

A *new* attack that layers several techniques **sequentially into one input** (e.g. `set_theory`-encode → render to image → output-framing), as opposed to the portfolio's parallel single-method queries.

- **Synergy / superadditivity:** does layering beat the bare model *more* than its components predict in isolation? A positive result is a genuine attack-mechanism finding (techniques hit independent blind spots at once, or one sets up the next).
- **Single-input evasion (scope-proof):** because the compound is *one* input the defense must process as a whole, defeating a defense with it has no "out-of-scope attack" excuse — unlike the portfolio framing. This is the clean version of "attack beats defense."

### 1.2 Cross-modal splitting and joint verification

Distribute harmful content across text and image so each channel — and any *per-channel* check, even a coverage-complete one — sees only benign content, while the model reassembles the harmful request. If clean splits exist, **per-channel completeness is structurally insufficient**, motivating **joint multimodal verification** (the `joint_verify` defender, already built) — a single safety judgment over the joint (text, image) input. If clean splits *do not* exist, that is itself a positive finding: harmful intent has an irreducible single-channel core.

### 1.3 The unified guard (extending coverage to compound + split)

One guard robust to the portfolio, the compound attack, and (where possible) splitting, evaluated with **held-out** generalization and the full safety–utility frontier — the contribution that ties §1.1–§1.2 to the coverage-complete guard.

---

## 2. Mechanism & theory — the explanatory layer beneath the coverage map

Why the coverage map holds, not just that it does. The white-box mechanism (§2.1) is the empirical layer; §2.2–§2.4 are the conceptual theory that turns the coverage map from a taxonomy into a predictive account.

### 2.1 White-box mechanism

On open-weight targets (HF-loaded Qwen2.5-VL / InternVL3, not vLLM): why is vision-side alignment weaker than text-side? Where/whether does the model reassemble split content (hidden-state / attention probes)? The explanatory layer beneath the coverage map.

### 2.2 Context-contaminated safety verdicts

ImgAug (benign image *helps*) and interference (benign content *hurts* a defense's handling of a co-present attack) are two signs of one property: these defenses do not judge each piece of content on its own merits — their verdict is contaminated by incidental context. Characterize this directly.

### 2.3 The alignment manifold

MathEnc moves a request into alignment-sparse regions via *encoding*; this line moves it via *modality*. A unified view: alignment is non-uniform over the input representation manifold, and encoding and modality-placement are coordinates on it; a defense "covers" only where it drags the request back toward alignment-dense regions. Turns the coverage map from a taxonomy into a *predictive* theory.

### 2.4 Compositional robustness

Whether defenses robust to attacks individually are robust to their composition — the general principle of which splitting is the limiting case.

---

## 3. Budget/resampling robustness against best-of-N — gated, orthogonal axis

The coverage map governs *where* harm is placed; it says nothing about *how many times* the attacker tries. A **best-of-N** adversary — resample N augmented variants of a single attack, succeed if any one lands (Hughes et al., NeurIPS 2025) — defeats defenses on a wholly different axis: a deterministic per-input guard can only lower the per-try slip probability *p*, leaving the structure `1 − (1−p)^N → 1` intact, so at sufficient budget it wins **regardless of coverage**. This is *not* defendable by the coverage-complete guard and is explicitly out of scope for the coverage paper — it is the **budget/resampling axis**, a manifestation of the (decade-unsolved) black-box adversarial-robustness problem. A separate, gated contribution.

### 3.1 Mechanism — the canonicalization carve

Variance reduction / **canonicalization**, *not* a SmoothLLM/SemanticSmooth re-run. The contribution is a *carve*: characterize which of best-of-N's augmentation axes are **canonicalizable** (collapse deterministically to one decision, killing the attack on that class at near-zero cost) versus an **irreducible** semantic/multimodal tail.

### 3.2 Objective — the security work-factor framing

*Not* ASR-reduction (wrong y-axis — ASR → 1 at large N), but the **security work-factor**: at fixed utility (≤ ~2% benign-refusal) and a target ASR, the **attack-cost increase**, reported as a *scaling-curve transformation* — constant shift (modest) vs. slope/exponent change (valuable) vs. full collapse on canonicalizable axes (strong) — decomposed by augmentation class, and measured against an **adaptive** attacker (else the number is inflated; EOT / Tramèr et al.).

### 3.3 Risk profile & gating

High-variance / bimodal — strong upside (first credible defense to a prominent, currently-undefended attack, with a super-constant work-factor increase) vs. a weak floor (constant-factor only → adaptive evasion → a negative result that is hard to place), plus **scoop risk** (best-of-N is a hot target). But the variance is **front-loaded and cheaply gated**: one experiment — does the defense change the power-law's *constant* or its *slope*? — resolves most of it before any real commitment. A **gated future option**, eval-only on the open-VLM cluster; run the gate first, commit only if the cost-increase scales super-constant. Full defense is *not* a goal (it would require solving black-box adversarial robustness).

---

## 4. Agent-side line — from models to agents (a separate line, not a follow-on)

The two subsections below leave the model-only setting entirely; they are a *separate line*, not a follow-on to the coverage guard. This whole project studies *where harmful content is placed* (encoding, modality) against a *model* whose only output is text and whose only adversary is the prompt author. Agents shift both axes at once: the adversary becomes a **third party** who controls data the agent *ingests* (a tool output, a retrieved document, an on-screen image — *indirect* injection), and the harm becomes an **action the agent takes**, not text it emits. This is a distinct contribution rather than an increment — it adds a new input surface (the untrusted tool/data channel) and a new harm axis (action completion) to the coverage frame — and it inherits this line's assets: the MathEnc encoders and the ImgAug image transforms become the **payloads**, now delivered through the agent's data channel instead of the user prompt. **Scope discipline (the lesson of this very line):** target the *minimal agent pattern* — untrusted-data → context → action — instantiated on a standard harness (AgentDojo / InjecAgent) and swept across backbones, **not** a bespoke complete agent whose idiosyncratic structure would make the result coupled and un-general. Generality comes from the multi-scaffold × multi-backbone sweep, exactly as the model results here generalize across VLMs.

### 4.1 Encoded indirect injection (attack-first)

Does an encoded payload survive **injection-specific** defenses — spotlighting, delimiter-isolation, prompt-shield / classifier guards — that are tuned on *natural-language* injections? These defenses have no pure-model analog, so defeating them is a genuinely new result, not a re-run of text-side jailbreaking.

- **Success = action completion**, not a harmful-text verdict: the agent actually executed the injected instruction / called the sensitive tool. This is the agent-native metric.
- **Attack-first, by design.** A payload is portable — a data blob dropped into any harness — whereas a defense must hook the agent's internals; the attack stays eval-only and decoupled, the defense (§4.2) is the coupled, later half.
- **Falsifiable:** encoded payloads raise injected-action success over plain-language payloads against deployed injection defenses, across ≥3 scaffolds × backbones. Refutation (encoding gives no lift once an injection guard is present) is itself a finding — injection defenses, unlike alignment, would be encoding-robust.

### 4.2 Multimodal injection, action-level coverage, and a flagship demonstration

- **Multimodal injection.** Computer-use / screenshot agents read *images*; the ImgAug `ir_plain` / decoy transforms become **image-borne** indirect injection into a VLM agent — a direct lift of this line's modality-placement work into the action-harm setting.
- **Action-level coverage (the defense half).** The coverage map gains the untrusted tool/data channel as a new *surface* and the action as a new *harm type*; the natural agent analog of the coverage-complete guard recovers and checks content on the data channel **before** it can reach an action. But agent defenses (information-flow control, dual-LLM quarantine) couple to agent structure — so this is the harder, more engineering-heavy, later contribution.
- **Flagship demonstration (a deliberately deferred *choice*).** The general result lands on a standard harness; impact comes from one striking demo on a *deployed, recognizable* agent with high-stakes actions — an email/calendar assistant (data exfiltration, sending on the user's behalf) or a coding agent with repo/CI access (supply-chain-flavored). The target is chosen for recognizability and stakes **at execution time** — explicitly *not* a niche tool. Any released-system demonstration follows responsible disclosure.

---

## 5. Volume / context-dilution attacks — long-context safety degradation (LOW PRIORITY)

*Hypothesis:* flooding the context with large, *irrelevant* content (e.g. a long novel) before the harmful request degrades the model's safety behavior — a *dilution* effect distinct from in-context harmful demonstrations.

### 5.1 Status

**Low priority — exploratory, not recommended as a project for this line.** Reasons: (1) the headline ("long context erodes safety, scales with length") is already owned by **many-shot jailbreaking** (Anil et al., 2024); the open part is a narrow mechanistic niche. (2) Crowded, compute-heavy area dominated by the labs that own the long-context models — a structural disadvantage for solo / free-cluster work. (3) **Orthogonal to the encoding/coverage arc** — no shared harness or identity; it does not compound.

### 5.2 Premise caveat

"Dilute system-prompt attention" assumes safety is system-prompt-gated; modern safety is largely *in-weights* (RLHF), so pure irrelevant dilution may not erode it. If any effect exists, the likely cause is general long-context **OOD/overload** degradation of learned behaviors, *not* specifically system-prompt attention dilution — so the stated mechanism is probably the wrong causal story.

### 5.3 The only version worth a cheap look — a disentanglement pilot

A mechanistic *disentanglement*: does volume-*without*-demonstration erode safety, controlling for context length, separately from in-context harmful examples? Run as a **context-length sweep** (e.g. 1k → 100k) with a **dilution-vs-demonstration control** (irrelevant filler vs. matched-length harmful demos). A clean negative ("long-context safety decay is demonstration-driven, not dilution-driven") is also a finding. A *lower* emergence scale would be more valuable (realistic threat) but is *less* likely (the many-shot effect is a power law in length, so smaller context → weaker effect).

### 5.4 Gating

(a) Prior-art check first (many-shot + any "long-context / context-overflow jailbreak"); (b) if not scooped, a ~1-day length-sweep-plus-control pilot; (c) decide from the curve. Keep boxed as a **pilot, never a project**, and only after the coverage arc ships. Minor connecting note: an *extract-and-judge* guard (like the coverage-complete guard) is structurally **more** robust to dilution than relying on intrinsic model safety — a small point in favor of guard-style defenses, not a reason to pursue the attack.

---

## 6. Near-term extension of the current paper (not a standalone project)

### 6.1 Breadth — API-model & benchmark generalization

API-model generalization (gemini-2.x-flash / gpt-4o-mini / claude-sonnet-4-6) once the open-weight results are locked; broader benchmark and alignment-tier spread. This extends the *current* coverage paper rather than spawning a new project; listed here only so it is not lost.
