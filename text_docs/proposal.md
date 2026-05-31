# Research Proposal — Paper C (AAAI-27)

**Working title:** *Adversarial Modality Placement: The Image-Presence Safety Effect in VLMs Is Not Robust, and the Minimal Defense That Is*

**Target:** AAAI-27 main technical track. Abstract **July 21, 2026** (mandatory, locks title/claim); full paper **July 28**; supplementary + code July 31. Plan backward from July 21.

**Hard calendar:** ~3.3 weeks full-time from now → **June 22** (author starts a demanding job), then ~4 weeks evenings/weekends only. **All data collection must finish ~June 20.** Scope is therefore an evaluation / lightweight-method study on existing open or public-API models — no model training, no heavy infrastructure.

---

## 0. Relationship to Paper B (read this first)

This project builds directly on the author's submitted paper **B** — *"Image Augmentation Strengthens VLM Defenses Against Encoded Jailbreak Attacks"* (under ARR review). It reuses B's entire evaluation harness (multi-provider batch querying; SAGE / ECSO / no-defense wrappers; HarmBench + JailbreakBench judges; the safety–utility plane). It is developed in this repo, on `main`, on top of the tagged baseline `paper-b-arr-submission`.

**What B established (the seed):**
- Adding an *unrelated* image (a "decoy") alongside an encoded text attack **lowers** attack success rate (ASR) on 5 frontier VLMs, via two pathways: (i) caption-mediated defenses (ECSO) branch on `has_image`, so even a content-free decoy fires a safety re-check; (ii) on image-resident content (`ir_plain`), the model's *intrinsic* image-side safety reduces ASR with no explicit defense.
- A controlled decoy ablation supports an image-**presence** (not image-**content**) account (blank canvas ≈ mountain decoy).
- The safety gain has a benign-refusal cost: **SAGE + decoy on the Gemini family collapses to 76–100% benign refusal** (trivial-reject). B concludes **ECSO + decoy is the only configuration combining substantial ASR reduction with modest utility cost**, and proposes a deployment lever: *pair encoded inputs with a default decoy image.*
- B's method section already names **"modality coverage"** as the explanation, and B explicitly does **not** evaluate an adaptive attacker (stated limitation).

**What C adds (clearly distinct contribution):**
1. An **adaptive attacker that controls modality placement**, defeating SAGE/ECSO by construction — including refuting the robustness of B's "decoy strengthens the defense" / "ECSO + decoy is Pareto-optimal" claim.
2. A **modality-complete guard**: the minimal black-box defense that removes the single-modality blind spot, with a quantified safety–utility cost.
3. *(Stretch)* a **cross-modal splitting** attack that defeats *per-channel* defenses (even modality-complete ones), bounding what per-channel verification can achieve and motivating joint multimodal verification.

C **cites** B (the empirical seed and the defense it stress-tests). It is a different contribution (adaptive attack + defense + principle), so it is not "substantially similar" to B under ARR/AAAI dual-submission rules. C does **not** depend on B being accepted.

---

## 1. Core idea

A black-box VLM safety defense inspects content in some subset of the input modalities. Call a defense **modality-complete** if its safety check covers every modality that can carry harmful content, and **single-modality** otherwise. B's observation — that adding an image often *helps* — is, restated, that the defense's coverage *happened* to line up with where the content lived (ECSO's `has_image` re-check re-injected the text; intrinsic image-safety caught image-resident content). 

**The governing claim of C:** that alignment is *incidental and adversarially controllable.* An attacker who chooses where the harmful content lives can route it into whatever modality the deployed defense does not cover, defeating the defense **and** erasing B's image-presence safety gain. The minimal fix is to make the defense modality-complete by construction. The residual frontier is content that is harmful only in the *joint* multimodal interpretation — which no per-channel check, complete or not, can catch.

This is a principle that is (a) seeded but never weaponized by B, (b) falsifiable per (defense, placement) cell, and (c) closes on a concrete, deployable defense.

---

## 2. Research questions

**Floor (the AAAI submission core — committed):**
- **RQ-A (refute B's robustness).** Does an adaptive attacker defeat B's strongest configuration — **ECSO + decoy** — recovering ASR on the cells where B reports it near-eliminated? (e.g., gemini-2.0-flash, where B reports `code_attack` 79→32 and `formal_logic` 67→27 under decoy+ECSO.)
- **RQ-B (general modality placement).** Across B's 5 models × 3 encoders, does relocating harmful content into the uncovered modality defeat each single-modality defense (content-in-image vs. SAGE-system; ECSO re-check evasion)?
- **RQ-C (the minimal defense + its cost).** Does a **modality-complete guard** (unconditionally recover and check content from *all* channels, removing the `has_image` gate and the single-channel blind spot) restore protection against RQ-A/RQ-B attacks — and at what benign-refusal cost on JailbreakBench-benign, relative to B's decoy lever (which hits 76–100% refusal on Gemini)?

**Stretch (only if week-2 data is ahead of schedule):**
- **RQ-D (cross-modal splitting).** Can harmful content be **split** across text and image so each channel is individually benign (passing per-channel and caption checks) while the model reassembles the harmful request in its answer? Does this defeat even the modality-complete *per-channel* guard, and is **joint multimodal verification** required to catch it — at what additional cost?

---

## 3. Threat model

Black-box API access to the target VLM and to any deployed black-box defense (no weights, no activations) — identical to B, so the comparison is apples-to-apples. The attacker additionally **controls the modality placement** of the (already public) encoded payload: which channel (text, image, or both) carries it, and how it is rendered/composed. The defender deploys one of {no-defense, SAGE-system, ECSO, decoy-lever (B), **modality-complete guard (ours)**}. We do **not** claim the targeted defenses were designed against modality-placement attacks; the contribution is to show that single-modality coverage is an adversarially controllable surface, and to give the minimal coverage-complete defense.

---

## 4. Method

### 4.1 Attack families (what's new on the attack side)

1. **Modality relocation.** Move the harmful payload into the modality the defense does not cover.
   - vs. **SAGE-system** (text-only coverage): deliver via image. B's `ir_plain` already lowers ASR via *intrinsic* image-safety, so the adaptive component is a renderer/composition that stays model-readable while evading intrinsic image-safety (e.g., low-salience or layout-obfuscated rendering, content framed as transcription). Predict: relocation defeats SAGE-system where naive `ir_plain` did not.
   - vs. **ECSO**: see (2).
2. **Re-check evasion (ECSO-specific).** ECSO returns the initial response directly unless its self-judge (TELL) flags it, then re-asks safety-first (CAP→SAFE). Two levers: (a) make the *initial* response pass TELL (obfuscated/encoded output the self-judge reads as benign); (b) make the SAFE re-ask still comply. Either defeats **ECSO + decoy**, refuting B's Pareto-optimal claim (RQ-A).
3. **Cross-modal splitting (stretch, RQ-D).** Distribute the instruction so neither channel — nor any per-channel caption/check — sees a complete harmful request, but the model reassembles it. Defeats per-channel verification by construction.

### 4.2 Defense (what's new on the defense side)

- **Modality-complete guard.** A black-box wrapper that, regardless of `has_image`, (i) recovers content from *every* channel (caption/OCR the image **and** read the text), (ii) runs a unified safety check over the recovered union, (iii) gates the response on it. Built from primitives already in the repo (ECSO's captioning + SAGE's discrimination). Removes the `has_image` gate (the artifact behind B's decoy lever) and the single-channel blind spot. Expected to resist families 1–2; expected **not** to resist family 3 (splitting), which is the point of RQ-D.
- *(Stretch)* **Joint multimodal verification** — a single safety judgment over the *joint* (text, image) input rather than per-channel — as the candidate fix for splitting; characterize feasibility and cost.

### 4.3 Metrics

- **ASR**: fraction of HarmBench-harmful (100 prompts) judged harmful (HarmBench classifier, `gpt-5-nano`). Lower = safer. Empty responses auto-classified as refusals (handles upstream API filtering), per B.
- **Benign refusal**: fraction of JailbreakBench-benign (100 prompts) judged a refusal. Lower = more useful.
- **Safety–utility plane**: every (model, defense, attack) cell as an (ASR, benign-refusal) point. The headline is whether the modality-complete guard dominates B's decoy lever (lower refusal at equal/​lower ASR).
- **Statistics**: bootstrap 95% CIs on per-cell rates; paired permutation tests on per-prompt verdicts for attack-vs-baseline and guard-vs-decoy comparisons.

---

## 5. Experimental setup (almost entirely inherited from B)

| Axis | Choice | New work? |
|---|---|---|
| **Target VLMs** | gemini-2.0-flash, gemini-2.5-flash, gemini-2.5-flash-lite, gpt-4o-mini, claude-sonnet-4-6 (B's five). Iterate on the cheap Gemini-flash subset; full set for the final matrix. | reuse |
| **Encoders** | `code_attack`, `set_theory`, `formal_logic` (B's three) | reuse |
| **Defenses** | no-defense, SAGE-system, ECSO, decoy-lever (B baseline), **modality-complete guard (new)** | 1 new defender |
| **Attacks** | modality-relocation, ECSO re-check evasion, *(stretch)* cross-modal splitting | new transforms |
| **Benchmarks** | HarmBench-harmful (100), JailbreakBench-benign (100) | reuse |
| **Judges** | HarmBench classifier + JBB-refusal classifier, `gpt-5-nano` backbone | reuse |
| **Decoding** | deterministic (temp 0, seed 42), per B | reuse |

**Code to build (small, bounded):**
1. `modality_complete` defender in the defense factory (compose existing caption + discrimination primitives; ~few days).
2. Adaptive-placement attack transforms: dual-channel composition (payload in one channel + controlled content in the other); ECSO-evasion output-obfuscation variant. *(Stretch: cross-modal splitting transform.)*
3. No harness, provider, or judge changes expected.

---

## 6. Falsifiable predictions (per the principle)

| # | Prediction | Refutation would mean |
|---|---|---|
| P1 | Modality relocation recovers ASR under SAGE-system on cells where B's `ir_plain` lowered it | Intrinsic image-safety is robust, not incidental — narrows the claim |
| P2 | ECSO re-check evasion recovers ASR under **ECSO + decoy** (refutes B's Pareto-optimal config) | B's decoy lever is adaptively robust — strengthens B, weakens C's premise |
| P3 | Modality-complete guard restores protection vs. P1/P2 attacks | Coverage-completeness is insufficient — points to a deeper cause |
| P4 | Modality-complete guard costs *less* benign refusal than B's decoy lever at equal ASR | The decoy lever is utility-competitive — weakens C's deployment story |
| P5 *(stretch)* | Cross-modal splitting defeats the per-channel modality-complete guard | Per-channel checks suffice — no need for joint verification |

A clean paper needs P1–P4 to mostly hold; P2 is the linchpin (it is what makes C a refutation of B's robustness rather than a footnote).

---

## 7. Timeline (backward from July 21; data frozen ~June 20)

| Window | Mode | Work |
|---|---|---|
| **Now → ~Jun 6** | full-time | Build `modality_complete` defender + dual-channel/ECSO-evasion attack transforms. Smoke-test on the cheap Gemini-flash subset. Pilot RQ-A (refute ECSO+decoy) on 1–2 cells — **this is the gating result**; if P2 fails here, re-scope immediately. |
| **~Jun 6 → ~Jun 20** | full-time | Run the full floor matrix: RQ-A/B (attacks vs SAGE/ECSO/decoy across 5 models × 3 encoders) + RQ-C (modality-complete guard, safety + benign-refusal). Bootstrap CIs. *If clearly ahead by ~Jun 14: build + pilot RQ-D splitting.* **Freeze data ~Jun 20.** |
| **Jun 22 → ~Jul 14** | part-time (job started) | Write. Figures (safety–utility plane, per-cell ASR-recovery bars). Statistics. Lock the claim. |
| **~Jul 14 → Jul 21** | part-time | Polish, internal review, reviewer-proofing. **Submit abstract Jul 21**, paper Jul 28, code Jul 31. |

Gating checkpoint: **the RQ-A pilot (refuting ECSO+decoy) by ~Jun 6.** It is the cheapest decisive test of the whole thesis.

---

## 8. Risks & mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| P2 fails — ECSO+decoy is adaptively robust | Low–Med | Pivot the headline to SAGE-system relocation (P1) + the modality-complete guard; the principle + defense still stand. Detect early via the Jun 6 pilot. |
| Adaptive attack is "just a stronger encoded attack," not modality-specific | Med | Anchor every attack to a *no-defense* control: a true modality-placement effect must show the gain is defense-specific (attack ≈ baseline ASR with no defense, large gap with defense). Mirror B's own specificity logic. |
| "You just combined SAGE + ECSO" criticism of the guard | Med | Frame the contribution as the *principle + adaptive validation*, with the guard as its minimal instantiation; report the splitting result (even as a negative/limitation) to show per-channel completeness is necessary but not sufficient. |
| Reviewers: defenses weren't designed against placement attacks | Med | Same stance as B: these are the strongest deployed black-box defenses; the point is that single-modality coverage is an exploitable surface, disclosed responsibly with a fix. |
| Self-overlap with B (under ARR) | Low | Distinct contribution (adaptive attack + defense + principle); cite B; keep B's decoy lever as the *object of study*, not a re-derivation. |
| Stretch (RQ-D) doesn't finish in the box | Expected | RQ-D is explicitly optional; the floor (RQ-A/B/C) is a complete paper. Present splitting as motivated future work if unfinished. |
| Upstream API content filtering (esp. Claude `code_attack`) saturates cells | Known (from B) | Exclude saturated cells from the adaptive analysis, as B did; lean on the Gemini-flash family + gpt-4o-mini where B has clean signal. |

---

## 9. Paper structure

1. **Introduction.** Black-box VLM defenses' effectiveness against encoded attacks tracks *whether their safety check covers the modality where the content lives* (B's seed). We show this alignment is incidental and adversarially controllable: an attacker who places content in the uncovered modality defeats SAGE/ECSO — and erases the image-presence safety gain B reports, including refuting B's Pareto-optimal ECSO+decoy configuration. We give the minimal modality-complete guard that restores protection at lower utility cost, and show cross-modal splitting bounds what per-channel verification can achieve.
2. **Background.** Encoded attacks; VLM modality-safety asymmetry; the three black-box defense families; B's image-presence finding and its decoy lever (the object we stress-test).
3. **The modality-coverage principle & threat model.** Single-modality vs. modality-complete coverage; adversarial placement.
4. **Attacks.** Modality relocation; ECSO re-check evasion; (stretch) cross-modal splitting. No-defense controls for specificity.
5. **The modality-complete guard.** Construction from caption + discrimination primitives; (stretch) joint verification.
6. **Experiments.** Setup (B's models/encoders/benchmarks/judges). RQ-A refutation; RQ-B general placement; RQ-C guard + safety–utility plane; (stretch) RQ-D splitting.
7. **Analysis.** Per-defense mechanism; why coverage-completeness is necessary; the per-channel-vs-joint boundary.
8. **Conclusion / deployment guidance.** Evaluate black-box VLM defenses for modality coverage before deployment; image-presence "safety" must not be relied upon.

---

## 10. Ethics

Consistent with B's stance: all experiments use standardized public harmful-prompt benchmarks (HarmBench, JailbreakBench); the encoders and the image-composition primitive are from published prior work, so we introduce no fundamentally new attack capability. The contribution is **defense-oriented** — characterizing an adversarially controllable weakness in deployed black-box defenses and providing the minimal coverage-complete fix. Appendix examples use informational-harm prompts. We release no adversarial assets beyond what is already public, and report the over-refusal and robustness limitations of the proposed guard so deployers do not over-rely on it.

---

## 11. Publication strategy

One **venue-agnostic** body of work: the same experiments and claims serve every target; only the template and framing emphasis change. The venue is chosen **after results are in**, not now. The same paper cannot be under review at two venues at once.

### Table 1 — Primary options

The dominant variable is **which paper you end up with**, and that's known early — at **gate G0 (~Jun 6)**, the cross-modal-splitting feasibility test (experiments plan §3):
- **Strong track** — splitting works → a genuinely novel result (per-channel verification is *structurally* insufficient; joint reasoning required).
- **Modest track** — splitting fails → the floor only (modality placement + the modality-complete guard + over-refusal audit): solid, but "expected attack + expected defense."

P(accept) is therefore given **per track** (rough; each assumes clean execution of that track). **Value /100** = worth of an acceptance for prestige + record/NIW (job excluded): AAAI is top-tier broad AI (CORE A\*), EACL a tier below ACL/EMNLP, Findings a recognized lower tier.

| # | Option | Deadline | P · strong | P · modest | Value | Fit |
|---|---|---|:--:|:--:|:--:|---|
| 1 | AAAI-27 — **Main Technical** | Jul 28 | ~20–25% | ~10–15% | 95 | Strong |
| 2 | AAAI-27 — **AI Alignment** track | Jul 28 | **~30–35%** | ~12–18% | 92 | **Best** — solicits *"robustness evaluation, red-teaming"* |
| 3 | EACL 2027 — **main** (ARR Aug) | Aug 3 | ~30% | ~22% | 80 | Strong |
| 4 | EACL 2027 — **Findings** (ARR Aug) | Aug 3 | →**~55%** any-accept | →**~45%** any-accept | 65 | Good |

Rows 1–2 are **mutually exclusive** (one AAAI track per paper); rows 3–4 are **one ARR submission** with two accept tiers. AAAI special-track rates aren't published yet — confirm when the CFPs post.

**Reading it:**
- **AAAI Alignment dominates AAAI Main** in both tracks (≈equal value, better fit *and* odds). Alignment *is* the AAAI option; Main only if a reviewer-pool reason ever favors it.
- **Strong track → a real choice:** AAAI Alignment (value 92, ~30–35%, binary) vs. EACL (value 80/65, ~55% land). EACL banks more *expected* publication; AAAI banks more *prestige per hit* — and prestige is nonlinear for a thin record, so AAAI is worth the binary risk **if the result is clean**.
- **Modest track → EACL, not close:** AAAI Alignment drops to ~15% (an "expected" result is below the AAAI bar), EACL ~45% with a rebuttal. Findings exists precisely to land a solid-but-unsurprising paper.

**Decision flow (gate-driven, not a single July call):**
1. **~Jun 6 (G0).** Splitting works? → **yes:** build toward **AAAI AI Alignment**. → **no:** build toward **EACL** (and keep **SaTML**, Sep 24, in view — the modest/robustness paper is dead-center for "secure & trustworthy ML").
2. **~Jul 20 (final QA).** Is the chosen-track paper actually clean (RQ-A/B/C solid · guard clean · safety–utility crisp)? If a *strong*-track paper came in messy/borderline, **drop AAAI → EACL** before committing.
3. **Submit** AAAI Jul 28 *or* EACL Aug 3 accordingly (mutually exclusive for the same paper).

### Table 2 — Known-good fallbacks (the rest)

| Venue | Deadline | Value /100 | Fit | Note |
|---|---|:--:|---|---|
| SaTML 2027 | Sep 24 | 78 | **Best topical** | "secure & trustworthy ML" — dead-center; for the **modest/robustness** paper a genuine alternative to EACL, not just a fallback |
| ARR Oct cycle | Oct 12 | 75 (+Findings) | Strong | the **only true sequential net** — opens *after* an AAAI Phase-1 reject (Sept 24); commits to a 2027 \*ACL venue (TBD) |
| WSDM 2027 | Aug 14 | 73 | Moderate | weak fit (web/data-mining); needs a "trustworthy ML for deployed assistants" reframe; low priority |

**Timing reality:** AAAI's first decision (Sept 24) lands *after* every other deadline except ARR Oct 12 — so there is no "submit to AAAI, see the result, then fall back to EACL/WSDM/SaTML." Those are alternatives chosen *instead of* AAAI, up front. The only genuine after-an-AAAI-reject option is **ARR Oct 12**.

**Context / constraints:** no June/July ARR cycle (the ACL calendar jumps May 25 → Aug 3); EMNLP/AACL 2026 are closed (May 25 cycle — Paper B's); COLM and IEEE ICDM out of scope (timing / fit). Keeping options open is only free if the scope stays fixed — the §7 **June 20 data-freeze** governs; do not let an open venue list become a reason to let the claim drift.
