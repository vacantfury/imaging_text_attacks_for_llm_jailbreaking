# Roadmap — current paper & future work (Coverage-Complete Defense line)

> **⚙️ Infra note — deprecated API models (recorded 2026-06-15).** OpenAI is deprecating these GPT-5 snapshots: `GPT-5-2025-08-07`, `GPT-5-mini-2025-08-07`, `GPT-5-nano-2025-08-07`, `GPT-5-pro-2025-10-06`. They back the `gpt-5` / `gpt-5-mini` / `gpt-5-nano` / `gpt-5-pro` entries in `src/llm_utils/llm_model.py`. **Impact:** `gpt-5-nano` is the current Paper-C **judge** (`experiments_plan.md` §1) and an API target — any future project (and any re-judge of frozen data) must migrate to a non-deprecated model. Pick the replacement from the *then-live* registry; do not hard-code these snapshot IDs in new presets. Re-check this list before starting any new project — it will go stale.

This is the planning catalog split out of `proposal.md` (it was the proposal's §11), reorganized **current-paper-first**:

- **§1 — the current shipping paper's own near-term extensions** (not standalone projects): things still attached to the coverage-complete defense paper.
- **§2–§6 — separate future projects**, each a standalone contribution that builds on the coverage-complete guard, **one project per section, in rough priority / readiness order**: §2 the direct follow-on defense paper · §3 the explanatory mechanism/theory layer · §4 a gated orthogonal project (budget/resampling) · §5 a separate, further-out line (agents) · §6 a low-priority exploratory direction (volume/dilution).
- **§7 — a research-identity frame, not a project**: the unifying thesis the whole arc is a special case of, seeding its extensions (§7.2 multi-agent / distributed harm; §7.3 harm × truth / fabrication-based harm — deferred pending a literature search).
- **§8 — a second low-priority exploratory coordinate**: low-resource-language encoding as a third alignment-sparse axis on the §3.3 manifold — mostly-scooped as a standalone attack, ownable only in its compounding with modality.

Within each section, subsections are its component points.

---

## 1. Current paper — near-term extensions (not standalone projects)

Extensions of the *current* coverage paper rather than new projects; listed here so they are not lost.

### 1.1 Breadth — API-model & benchmark generalization

API-model generalization (gemini-2.x-flash / gpt-4o-mini / claude-sonnet-4-6) once the open-weight results are locked; broader benchmark and alignment-tier spread. This extends the *current* coverage paper rather than spawning a new project.

### 1.2 Severity-weighted evaluation — a discussion / limitations hook (NOT a metric change)

*Carded 2026-07-04 from Anthropic's **Cyber Jailbreak Severity (CJS)** framework (co-developed with Glasswing; "More details on Fable 5's cyber safeguards and our jailbreak framework," 2026-07-02).* CJS scores a jailbreak on four axes — uplift (0–4), uplift breadth (0–2), weaponization ease (0–2), discoverability (0–2) — summed to CJS-0…CJS-4.

- **Do NOT adopt it as machinery.** It is an early-draft, non-peer-reviewed, Anthropic-specific governance rubric; its axes are **cyber-specific** and don't map onto our multi-category benchmarks (HarmBench / JBB span chem, harassment, misinfo) without inventing a general severity rubric — the months-long benchmark-building trap §7.3 / §7.4 tells us to refuse. Our contribution is **coverage** (measured by ASR / refusal), a different axis from severity.
- **Use it as a citation-level discussion hook.** CJS is a timely, industry-blessed instance of a real critique our eval is exposed to: **binary ASR is severity-blind** — a judge scores `harmful=1` whether the model emits a high-uplift artifact or a CJS-0 already-public fragment. Acknowledge in the discussion that coverage is **orthogonal and complementary** to severity (coverage says *which* cells are unguarded; severity says *which unguarded cells matter*), and cite CJS as the emerging vocabulary.
- **Two CJS design choices are governance-side echoes of frames we already own** (clean citations, not new work): (i) *"uplift is relative to the tools available at evaluation time"* (its Log4Shell example: CJS-4 pre-disclosure → CJS-0 once scanners catch it) is exactly the **§4.2 security-work-factor** logic — cost-increase vs. the current adaptive baseline, not raw ASR; (ii) *"CJS can be revised up, never down — including when combined with other open findings"* is **compositional severity**, the §7.1 compositional-harm thesis stated in policy language.
- **Optional light analysis (discussion, not a project):** a **severity-weighted ASR** re-scoring existing successes with a severity judge, to show whether a defense's residual failures are trivial or dangerous. Keep it a discussion-section analysis — a *general* severity rubric is benchmark-building and out of scope.

---

## 2. Unified defense against compound & split attacks — the direct follow-on paper

The next defense paper: one guard robust to the portfolio **and** new compound attacks **and** (where possible) cross-modal splitting, evaluated with held-out generalization and the full safety–utility frontier. Stronger as a follow-on precisely because *this* project will have characterized the threat space it must defend. §2.1 and §2.2 are the attacks it must introduce; §2.3 is the defense.

### 2.1 Compound (single-input) attacks

A *new* attack that layers several techniques **sequentially into one input** (e.g. `set_theory`-encode → render to image → output-framing), as opposed to the portfolio's parallel single-method queries.

- **Synergy / superadditivity:** does layering beat the bare model *more* than its components predict in isolation? A positive result is a genuine attack-mechanism finding (techniques hit independent blind spots at once, or one sets up the next).
- **Single-input evasion (scope-proof):** because the compound is *one* input the defense must process as a whole, defeating a defense with it has no "out-of-scope attack" excuse — unlike the portfolio framing. This is the clean version of "attack beats defense."

### 2.2 Cross-modal splitting and joint verification

Distribute harmful content across text and image so each channel — and any *per-channel* check, even a coverage-complete one — sees only benign content, while the model reassembles the harmful request. If clean splits exist, **per-channel completeness is structurally insufficient**, motivating **joint multimodal verification** (the `joint_verify` defender, already built) — a single safety judgment over the joint (text, image) input. If clean splits *do not* exist, that is itself a positive finding: harmful intent has an irreducible single-channel core.

### 2.3 The unified guard (extending coverage to compound + split)

One guard robust to the portfolio, the compound attack, and (where possible) splitting, evaluated with **held-out** generalization and the full safety–utility frontier — the contribution that ties §2.1–§2.2 to the coverage-complete guard.

---

## 3. Mechanism & theory — the explanatory layer beneath the coverage map

Why the coverage map holds, not just that it does. The white-box mechanism (§3.1) is the empirical layer; §3.2–§3.4 are the conceptual theory that turns the coverage map from a taxonomy into a predictive account.

### 3.1 White-box mechanism

On open-weight targets (HF-loaded Qwen2.5-VL / InternVL3, not vLLM): why is vision-side alignment weaker than text-side? Where/whether does the model reassemble split content (hidden-state / attention probes)? The explanatory layer beneath the coverage map.

- **Role/harmfulness probes — a concrete method (carded 2026-07-11).** Method inspiration from an informal post on the mechanism of prompt injection (Ye & C., ~Jun 2026; *a blog/forum post, not a citable source — do NOT cite it. It claims a backing ICML paper; if this direction is ever built, verify and cite the formal version instead*). Their instrument: train a **linear probe on mid-layer activations** to read a token's internal role ("how much does the model think this is its own reasoning / a user command"), and show role is perceived from **writing style, not the true role tag** — the same surface-proxy-vs-true-object failure this whole line studies (their "attack-memorization = brittle vs role-perception = robust" mirrors our "inspect-only vs decode-then-judge"). Adapted here: train **harmfulness / decode probes** on the open-weight targets and ask — when an encoded harmful prompt is fed, does the model *internally represent* the harm, or does the encoding stop the harmful concept from forming at all? This turns the decode gap from a black-box behavioral fact into a mechanistic account of **where** safety breaks (harm not represented vs. represented-but-refusal-not-triggered), and would also give a mechanistic backing to the "judges share the decode blind spot" thread of the judge-methodology idea. **Pivot cost (be honest):** a real methodology shift — the current line is entirely black-box (API judges, ASR); this is white-box interp on HF-loaded weights. Feasible (the targets are already open-weight) but a different toolset, and standalone-project (Paper-D) scale — explicitly *not* a Paper-C add-on, and gated on not letting it pull the AAAI timeline.

### 3.2 Context-contaminated safety verdicts

ImgAug (benign image *helps*) and interference (benign content *hurts* a defense's handling of a co-present attack) are two signs of one property: these defenses do not judge each piece of content on its own merits — their verdict is contaminated by incidental context. Characterize this directly.

### 3.3 The alignment manifold

MathEnc moves a request into alignment-sparse regions via *encoding*; this line moves it via *modality*. A unified view: alignment is non-uniform over the input representation manifold, and encoding, modality-placement, **and natural-language choice (high- vs. low-resource, §8)** are coordinates on it; a defense "covers" only where it drags the request back toward alignment-dense regions. Turns the coverage map from a taxonomy into a *predictive* theory.

### 3.4 Compositional robustness

Whether defenses robust to attacks individually are robust to their composition — the general principle of which splitting is the limiting case.

---

## 4. Budget/resampling robustness against best-of-N — gated, orthogonal axis

The coverage map governs *where* harm is placed; it says nothing about *how many times* the attacker tries. A **best-of-N** adversary — resample N augmented variants of a single attack, succeed if any one lands (Hughes et al., NeurIPS 2025) — defeats defenses on a wholly different axis: a deterministic per-input guard can only lower the per-try slip probability *p*, leaving the structure `1 − (1−p)^N → 1` intact, so at sufficient budget it wins **regardless of coverage**. This is *not* defendable by the coverage-complete guard and is explicitly out of scope for the coverage paper — it is the **budget/resampling axis**, a manifestation of the (decade-unsolved) black-box adversarial-robustness problem. A separate, gated contribution.

### 4.1 Mechanism — the canonicalization carve

Variance reduction / **canonicalization**, *not* a SmoothLLM/SemanticSmooth re-run. The contribution is a *carve*: characterize which of best-of-N's augmentation axes are **canonicalizable** (collapse deterministically to one decision, killing the attack on that class at near-zero cost) versus an **irreducible** semantic/multimodal tail.

### 4.2 Objective — the security work-factor framing

*Not* ASR-reduction (wrong y-axis — ASR → 1 at large N), but the **security work-factor**: at fixed utility (≤ ~2% benign-refusal) and a target ASR, the **attack-cost increase**, reported as a *scaling-curve transformation* — constant shift (modest) vs. slope/exponent change (valuable) vs. full collapse on canonicalizable axes (strong) — decomposed by augmentation class, and measured against an **adaptive** attacker (else the number is inflated; EOT / Tramèr et al.).

### 4.3 Risk profile & gating

High-variance / bimodal — strong upside (first credible defense to a prominent, currently-undefended attack, with a super-constant work-factor increase) vs. a weak floor (constant-factor only → adaptive evasion → a negative result that is hard to place), plus **scoop risk** (best-of-N is a hot target). But the variance is **front-loaded and cheaply gated**: one experiment — does the defense change the power-law's *constant* or its *slope*? — resolves most of it before any real commitment. A **gated future option**, eval-only on the open-VLM cluster; run the gate first, commit only if the cost-increase scales super-constant. Full defense is *not* a goal (it would require solving black-box adversarial robustness).

---

## 5. Agent-side line — from models to agents (a separate line, not a follow-on)

The two subsections below leave the model-only setting entirely; they are a *separate line*, not a follow-on to the coverage guard. This whole project studies *where harmful content is placed* (encoding, modality) against a *model* whose only output is text and whose only adversary is the prompt author. Agents shift both axes at once: the adversary becomes a **third party** who controls data the agent *ingests* (a tool output, a retrieved document, an on-screen image — *indirect* injection), and the harm becomes an **action the agent takes**, not text it emits. This is a distinct contribution rather than an increment — it adds a new input surface (the untrusted tool/data channel) and a new harm axis (action completion) to the coverage frame — and it inherits this line's assets: the MathEnc encoders and the ImgAug image transforms become the **payloads**, now delivered through the agent's data channel instead of the user prompt. **Scope discipline (the lesson of this very line):** target the *minimal agent pattern* — untrusted-data → context → action — instantiated on a standard harness (AgentDojo / InjecAgent) and swept across backbones, **not** a bespoke complete agent whose idiosyncratic structure would make the result coupled and un-general. Generality comes from the multi-scaffold × multi-backbone sweep, exactly as the model results here generalize across VLMs.

### 5.1 Encoded indirect injection (attack-first)

Does an encoded payload survive **injection-specific** defenses — spotlighting, delimiter-isolation, prompt-shield / classifier guards — that are tuned on *natural-language* injections? These defenses have no pure-model analog, so defeating them is a genuinely new result, not a re-run of text-side jailbreaking.

- **Success = action completion**, not a harmful-text verdict: the agent actually executed the injected instruction / called the sensitive tool. This is the agent-native metric.
- **Attack-first, by design.** A payload is portable — a data blob dropped into any harness — whereas a defense must hook the agent's internals; the attack stays eval-only and decoupled, the defense (§5.2) is the coupled, later half.
- **Falsifiable:** encoded payloads raise injected-action success over plain-language payloads against deployed injection defenses, across ≥3 scaffolds × backbones. Refutation (encoding gives no lift once an injection guard is present) is itself a finding — injection defenses, unlike alignment, would be encoding-robust.

### 5.2 Multimodal injection, action-level coverage, and a flagship demonstration

- **Multimodal injection.** Computer-use / screenshot agents read *images*; the ImgAug `ir_plain` / decoy transforms become **image-borne** indirect injection into a VLM agent — a direct lift of this line's modality-placement work into the action-harm setting.
- **Action-level coverage (the defense half).** The coverage map gains the untrusted tool/data channel as a new *surface* and the action as a new *harm type*; the natural agent analog of the coverage-complete guard recovers and checks content on the data channel **before** it can reach an action. But agent defenses (information-flow control, dual-LLM quarantine) couple to agent structure — so this is the harder, more engineering-heavy, later contribution.
- **Flagship demonstration (a deliberately deferred *choice*).** The general result lands on a standard harness; impact comes from one striking demo on a *deployed, recognizable* agent with high-stakes actions — an email/calendar assistant (data exfiltration, sending on the user's behalf) or a coding agent with repo/CI access (supply-chain-flavored). The target is chosen for recognizability and stakes **at execution time** — explicitly *not* a niche tool. Any released-system demonstration follows responsible disclosure.

---

## 6. Volume / context-dilution attacks — long-context safety degradation (LOW PRIORITY)

*Hypothesis:* flooding the context with large, *irrelevant* content (e.g. a long novel) before the harmful request degrades the model's safety behavior — a *dilution* effect distinct from in-context harmful demonstrations.

### 6.1 Status

**Low priority — exploratory, not recommended as a project for this line.** Reasons: (1) the headline ("long context erodes safety, scales with length") is already owned by **many-shot jailbreaking** (Anil et al., 2024); the open part is a narrow mechanistic niche. (2) Crowded, compute-heavy area dominated by the labs that own the long-context models — a structural disadvantage for solo / free-cluster work. (3) **Orthogonal to the encoding/coverage arc** — no shared harness or identity; it does not compound.

### 6.2 Premise caveat

"Dilute system-prompt attention" assumes safety is system-prompt-gated; modern safety is largely *in-weights* (RLHF), so pure irrelevant dilution may not erode it. If any effect exists, the likely cause is general long-context **OOD/overload** degradation of learned behaviors, *not* specifically system-prompt attention dilution — so the stated mechanism is probably the wrong causal story.

### 6.3 The only version worth a cheap look — a disentanglement pilot

A mechanistic *disentanglement*: does volume-*without*-demonstration erode safety, controlling for context length, separately from in-context harmful examples? Run as a **context-length sweep** (e.g. 1k → 100k) with a **dilution-vs-demonstration control** (irrelevant filler vs. matched-length harmful demos). A clean negative ("long-context safety decay is demonstration-driven, not dilution-driven") is also a finding. A *lower* emergence scale would be more valuable (realistic threat) but is *less* likely (the many-shot effect is a power law in length, so smaller context → weaker effect).

### 6.4 Gating

(a) Prior-art check first (many-shot + any "long-context / context-overflow jailbreak"); (b) if not scooped, a ~1-day length-sweep-plus-control pilot; (c) decide from the curve. Keep boxed as a **pilot, never a project**, and only after the coverage arc ships. Minor connecting note: an *extract-and-judge* guard (like the coverage-complete guard) is structurally **more** robust to dilution than relying on intrinsic model safety — a small point in favor of guard-style defenses, not a reason to pursue the attack.

---

## 7. Research-identity frame — compositional harm (the umbrella, not a project)

A positioning layer, not a shippable line: how to *narrate* this whole arc and *seed* its largest extension. Distinct from §3.4 (the **technical** compositional-robustness question) and §5 (the agent **project**) — this is the **identity** that subsumes both. Recorded so the framing isn't lost when attention returns to Paper C. Triggered by a "should I broaden from narrow jailbreaking toward a wider notion of harm — deception, multi-agent adversary?" discussion (Jun 2026); the answer is *yes, but as an extension of the thesis already owned, not a pivot.*

### 7.1 The unifying thesis

The arc was never really about "jailbreaking." Its through-line: **safety guards that inspect one unit — one representation (encoding), one modality (text/image), one message, one agent — are structurally incomplete when harm is *composed across units*; the fix is coverage / joint verification at the level harm actually lives.** A→B→C are special cases on three coordinates of one principle (representation = MathEnc; modality-presence = ImgAug; modality-placement/splitting = the coverage paper). Reframing the arc this way converts a pile of jailbreak papers into one ownable claim — *per-unit safety is structurally insufficient against compositional harm* — which is a stronger identity than either pole: "I do jailbreaking" (narrow, saturated) or "I do AI harm" (diffuse, crowded). **NIW read:** a sustained, unifying contribution in a defensible niche beats both — niche *ownership*, not breadth, is what the sustained-contribution narrative rewards.

### 7.2 The next coordinate — multi-agent / distributed harm

Multi-agent adversary is the **cross-agent analog of the coverage paper's cross-modal splitting** (§2.2): harm distributed across agents, each agent's individual contribution benign, the *joint* behavior harmful — deception / collusion / steering as the mechanism, **joint / system-level verification** as the defense (the multi-agent analog of the `joint_verify` defender). This is the natural Paper-E shape and the broadest reach of the thesis. It is also the most **career-adjacent** coordinate — multi-agent orchestration is the M365-Copilot day job (starts 2026-07-20) — so it is naturally timed for the Microsoft era, when compute/context may be richer. Overlaps §5 (agent-side line) but generalizes it: §5 is single-agent indirect injection; §7.2 is the *multi-agent* composition where no single agent is individually compromised.

### 7.3 Another coordinate — harm × truth (fabrication-based harm)

A sibling coordinate to §7.2, surfaced 2026-06-15. **Decision deferred pending a dedicated literature search** (LLM misinformation / persuasion, honesty / truthfulness alignment, automated fact-checking defenses, and any existing fabrication-harm benchmarks) — carded here at full fidelity, *not* started.

- **The construct (the load-bearing definition):** *harm causally contingent on a falsehood* — counterfactually, if the fabricated claim were true there would be no harm (or it would be legitimate). The harm exists **because** the content is false and believed. This test separates the target from **pure fabrication** (false but dual-use — fiction / satire / synthetic data → weak harm claim) and from **pure harm** (harmful regardless of truth → already covered by harmlessness alignment).
- **Why it's the coverage thesis on a new pair of units (harm-type × truth-value):** alignment trains **harmlessness** (is the *topic* dangerous?) well and **honesty** (is it true?) weakly/barely. Fabrication-based harm lives in the intersection *neither single-axis guard covers* — topically benign (a testimonial, a citation, a news item) so the harmlessness guard passes it, and no honesty guard to catch the falsehood. Per-axis safety is incomplete against cross-axis harm — exactly §7.1, with **truth-value as a newly-exposed safety surface**.
- **Attack side:** maximize harm-contingent-on-falsehood while **minimizing overt-harm signal** (stay topically benign) → slip the harmlessness guard; the honesty guard is ~absent. Natural encoding tie-in (does obfuscated fake evidence slip even more — and past an agent's checks? links §5 / §7.2).
- **Defense side:** a guard that detects the **coupling** — content presented as factual, checkably false / unsupported, **and** harm-bearing if believed. Factuality-check-alone over-refuses fiction; harm-check-alone misses it; the **conjunction** is the contribution — same shape as `joint_verify` / `modality_complete` (§2.2).
- **Artifact:** a **benchmark is the natural first artifact** — no existing dataset isolates the intersection, building it *is* pinning down the construct, and it has a high NIW / adoption ceiling. But a *good* one is **months and annotation-heavy**, and its quality hinges on the factuality-labeling problem below.
- **Load-bearing risk → scope discipline:** the defense (and the benchmark labels) lean on **factuality verification**, an open / unreliable problem. **Scope to the verifiable tail** — fabricated citations, checkable medical / statistical claims, impersonation of real entities — for clean ground truth. Let it sprawl to open-ended "is this true" and the ceiling becomes automated fact-checking and the result goes mushy.
- **Gate (do NOT build the benchmark first):** a **~50-item, one-domain pilot** (matched fabrication-harm vs overt-harm controls) tests the two empirical claims — is harm×fabrication ASR ≫ overt-harm ASR, and does a joint harm×factuality verifier beat each single-axis guard? Strong **and** construct-survives-contact → the pilot seeds the benchmark and earns the months; mushy → months saved. The benchmark is gated on the pilot.
- **Caution:** the "covers many papers / could be a whole program" appeal is a **scope-explosion flag**, not a green light — the shippable unit is *one* paper, not a vein that could host many. Parked behind Paper C.

### 7.4 Disciplines (so the breadth is a strength, not a scatter)

- **Keep the through-line sharp.** Every new axis must read as "the same principle, new surface" (compositional / coverage). The failure mode is drifting into a generic "AI-safety" researcher with disconnected topics — refuse it; an axis that doesn't reduce to the coverage thesis doesn't belong on this arc.
- **Sequence, don't pivot.** Use the frame to *narrate* the shipping arc and *seed* §7.2 — not to start new work now. This is exactly the broad, no-deadline direction the under-shipping-without-a-deadline pattern eats; the arc ships first (Paper C is the only hard deadline).
- **Enter via the compositional angle, not the demo lane.** The viral "LLM lies in a toy game" genre (e.g. the **Kradle Deception Eval**, Jun 2026 — a non-peer-reviewed company eval) is resourced by labs and distrusted by reviewers. The ownable entry is *rigorous compositional harm* — per-agent-benign / joint-harmful, plus a joint-verification defense — reusing the harness identity, **not** another propensity-for-deception leaderboard.
- **Cost honesty.** A multi-agent harness is a materially bigger, more compute-heavy build than the current eval-only VLM setup — the main argument for deferring §7.2 to the resourced Microsoft era rather than spending the free-cluster / pre-MSFT window on it.

### 7.5 A candidate formal language for the through-line — category theory (a *language*, not a project)

Carded 2026-06-19. The §7.1 thesis is *about composition* — attacks/encoders/modalities/defenses/judges as transformations that compose, harm that lives in the *joint* of units no single guard inspects. Category theory (the mathematics of composable relationships) is the natural candidate language for narrating that, and it plays to a genuine comparative advantage (physics-trained instinct for the universal structure behind disparate phenomena). Recorded so the option isn't lost — explicitly **not** a contribution, **not** a theory paper, **not** a new coordinate alongside §7.2/§7.3.

- **What it is.** A *descriptive* language for the existing arc, not new science: the pipeline (Prompt → Encoding → Attack → Defense → Judge → Evaluation) as morphism composition; an attack family as a class of morphisms that *preserve semantic intent while changing representation*; a coverage-complete guard as something that must cover the *joint object*, not just its per-channel projections.
- **The one place it could earn paper-facing space.** The splitting result (§2.2 / §3.4) is a real statement of **non-compositionality**: the meaning of a multimodal input is *not* the product/sum of its per-channel meanings, which is exactly why per-channel guards (SAGE/ECSO) compose to a guard that still misses joint-only harm. That insight is worth *one plain-language sentence* in Paper C's intuition — and needs **zero** categorical apparatus to say. The apparatus earns space only if it ever expresses something that sentence can't.
- **The deletion test (binding, from the source note).** Introduce a categorical concept only if it yields at least one of: a cleaner taxonomy, a more unified explanation, simpler notation, a new experimental perspective, or an insight otherwise hard to state — *and* it provides intuitive value immediately. **If removing the categorical language leaves the paper essentially unchanged, cut it.** Empirical ML/NLP reviewers mostly don't know category theory: low prior bias (opportunity) but zero reward for decoration and a sharp penalty for perceived unnecessary complexity. "Perceived rigor" is *not* a reason to include it.
- **Why not a standalone project.** A "category theory for compositional AI safety" position/theory paper is the lowest-shippability, highest-taste-variance genre, would compete for the same pre-MSFT window, and the source note itself disclaims wanting it. Use it as a private structuring lens (sharpen the `modality_complete` definition, the joint-object construction, the G0 split) and as *narration* for the §7.1 identity — it rides on the shipping arc, it does not stand beside it. Same discipline as §7.4: a language that doesn't reduce to the coverage thesis doesn't belong on the arc.

---

## 8. Low-resource-language encoding — a third alignment-sparse coordinate (LOW PRIORITY / scooped standalone)

*Carded 2026-07-04 from the 2026-07 anecdotal Fable-5 / Sonnet-5 jailbreak reports (Pliny the Liberator; Vitto Rivabella).* Those reports claimed that once the homoglyph vector (already an encoder here — `add_homoglyph_encoder`) and the long-context-**dilution** vector (already §6) were hardened, the *persistently* weakest surface was obscure low-resource languages (Santali, Amharic). The reporters correctly frame this as **systemic, not a model-specific backdoor**: safety-alignment corpora are overwhelmingly English / high-resource, so guardrails are structurally thin in low-resource languages.

### 8.1 Why it's on-thesis

Low-resource language is another **coordinate on the alignment manifold (§3.3)** — a natural sibling to representation-encoding (MathEnc) and modality-placement (ImgAug). It slots into the existing encoder factory as one more `llm_*` axis (a `llm_low_resource_language` encoder, sibling to `llm_classical_language`), so it costs almost nothing to add and reuses the whole harness.

### 8.2 The honest scoping (why this is §8, not §2)

- **Standalone attack = scooped / saturated.** "Translate the harmful request into a low-resource language" is Yong et al., *Low-Resource Languages Jailbreak GPT-4* (Brown, 2023) and a large follow-up literature (incl. Stellenbosch-group work — the article's "斯坦陵布什大学" reference). Not publishable alone, and no free-cluster advantage over the labs.
- **The ownable version = compounding / coverage, not the bare axis.** The novel-and-cheap question is whether *stacking* two alignment-sparse axes is **super-additive**: render low-resource-language-encoded text into an image (`ir_plain`) and run the language × modality 2×2. Does ASR exceed what either axis predicts alone (a concrete instance of §2.1 compound single-input attack, and a test of the §3.3 manifold's compositional geometry)? And does the **coverage-complete guard's language coverage degrade when the text arrives through the image channel** rather than as native text — i.e. is the guard's multilingual safety modality-robust?

### 8.3 Gate & caveats

- **Cheap gate:** add 1–2 low-resource-language encoders, run the language × modality 2×2 on the existing open-VLM cluster; commit only if the compound lift is super-additive **and** it survives the coverage guard. Otherwise it stays a one-line "language is a manifold coordinate too" note in Paper C's discussion and nothing more.
- **Severity caveat (from the source).** The reports themselves conceded the extracted payloads were low-severity ("边角料" — fragmentary chem / mild vuln fragments, misinformation), not core-dangerous capability. Treat the tweets as *motivation*, not evidence; the real-world harm ceiling of the low-resource-language surface is unquantified.
- **Prior-art discipline:** before any run, a literature pass on multilingual jailbreak + multilingual *defense* (the axis is old; the multimodal-compounding twist is the only defensible delta).
