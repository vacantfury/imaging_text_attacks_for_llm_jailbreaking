# Research Proposal — Coverage-Complete Defense (working title)

**Working title:** *Coverage-Complete Defense: A Single Black-Box Guard for the Union of Encoded and Multimodal Jailbreaks on VLMs*

**One-line thesis:** Existing black-box VLM jailbreak defenses are *specialists* — each inspects one input/output surface — so no single deployed defense covers the union of known encoded and multimodal attacks; we build the minimal **coverage-complete** guard that does, and quantify the utility cost of completeness.

**Scope note (read first).** This proposal describes **only the current project**: the coverage-gap measurement (motivation) and the coverage-complete unified defense (the contribution). Everything beyond it — new compound attacks, cross-modal splitting, mechanism, and the deeper theory — is deliberately deferred to **§11 Future Work**, not because it lacks value but because it is a separate contribution that builds on this one. Keep the body of this document to what this paper ships.

---

## 0. Relationship to prior work (read this first)

This project is the third in a line and reuses the same evaluation harness throughout.

- **MathEnc** — *"Exposing LLM Safety Gaps Through Mathematical Encoding"* (published). Recasts harmful queries into mathematical / logical encodings (set theory, first-order logic, code) that bypass text-side alignment. Supplies the **encoders** this project uses as attack surfaces.
- **ImgAug** — *"Image Augmentation Strengthens VLM Defenses Against Encoded Jailbreak Attacks"* (under review). Found that adding an image — even a content-unrelated decoy — *changes* a defense's behavior: ECSO's `has_image` branch re-checks; intrinsic image-side safety catches image-resident content. Crucially, ImgAug also documented the **failure cost**: SAGE+decoy on Gemini collapses to 76–100% benign refusal (trivial-reject). Supplies the **image transforms** (`ir_plain`, decoy) and the **decoy-lever baseline** this project stress-tests.

**What this project adds.** ImgAug's finding, restated, is that a defense helps exactly when its coverage *happens* to line up with where the harmful content lives. We make that observation systematic and constructive: we **measure** that no single existing defense covers the union of known attacks, **build** the minimal defense that does, and **characterize the cost** of that completeness. This is a *defense* contribution; it cites MathEnc (encoders) and ImgAug (image transforms, decoy lever, and the over-refusal hazard) and is not substantially similar to either.

---

## 1. Core idea

A black-box VLM safety defense inspects content on some subset of surfaces: input-text, input-image, output, or the joint (text+image) interpretation. Call the set of surfaces a defense actually checks its **coverage**. Known attacks differ in *where they place the harmful content*: text-side encodings live on input-text; rendered attacks (`ir_plain`) live on input-image; output-framing lives on the output.

The governing observation: **a defense reduces a given attack's success only when its coverage includes the surface that attack uses.** ImgAug's "image helps" result is one instance — coverage and content happened to align. But each deployed defense is a *specialist*: SAGE covers input-text; ECSO covers a caption of the image, gated on `has_image`; ETA scores the image (CLIP) and the output (reward); MLLM-Protector checks the output. So against a *suite* of attacks that place harm on different surfaces, **for any single defense some attack routes harm to an uncovered surface.** No single specialist covers the union.

The minimal fix follows directly: a **coverage-complete** guard that, regardless of `has_image`, unconditionally recovers content from *every* input channel (reads the text **and** OCR/captions the image) and runs **one** unified safety check over the union. It removes both the single-channel blind spot and the `has_image` gate (the artifact behind ImgAug's decoy lever). The interesting question is not whether it raises safety — by construction it covers more — but **what completeness costs in utility**, and whether that cost is lower than the specialist defenses and ImgAug's decoy lever.

---

## 2. Research questions

- **RQ1 — Coverage gap (motivation).** Characterize each baseline defense by the surface it covers and each attack by where it places harm. Across the attack suite × the specialist defenses, does *any single defense* cover the union, or does every defense leave at least one attack that routes harm to an uncovered surface?
- **RQ2 — The coverage-complete guard.** Does a single guard that recovers and checks content on *all* input channels close the gap — reducing attack success across the *whole* suite below every single specialist's worst case?
- **RQ3 — The cost of completeness.** What benign-refusal cost does completeness incur, on JailbreakBench-benign? On the safety–utility plane, does the guard **dominate** ImgAug's decoy lever (≤ refusal at ≤ attack success) and the specialist defenses? Where it does *not* dominate (e.g. vs. output-side MLLM-Protector), what does that say about input-coverage vs. output-checking as complementary axes?
- **RQ4 — Held-out generalization.** If the guard is configured/tuned on a subset of attacks, does it still cover the *held-out* attacks? (Coverage is structural, so it should — this is the test that separates a real coverage property from a benchmark-overfit defense.)

RQ1 is the motivating measurement; **RQ2–RQ4 are the contribution.** RQ4 is the linchpin that makes RQ2 a coverage claim rather than a bake-off.

---

## 3. Threat model

Black-box API/endpoint access to the target VLM and to any deployed black-box defense — no weights, no activations. The attacker draws from a **fixed, public suite of known attacks** (the MathEnc encoders × ImgAug image transforms): for each harmful prompt the attacker may use any single attack in the suite, and counts a success if the chosen attack defeats the deployed defense (the *portfolio* / best-of-suite threat model). The defender deploys exactly one of {no-defense, SAGE, ECSO, ETA, MLLM-Protector, ImgAug decoy lever, **coverage-complete guard (ours)**}. We do **not** claim the specialist defenses were designed against the full suite; the point is that single-surface coverage is, in deployment, an insufficient surface, and the coverage-complete guard is the minimal black-box fix.

---

## 4. Method

### 4.1 The attack suite (all existing — no new attack work)

The portfolio is the existing, public attack surface, reused unchanged:

| Surface | Attacks |
|---|---|
| input-text | `set_theory`, `formal_logic`, `code_attack` (MathEnc encoders) |
| input-image | `ir_plain` (encoded attack rendered into the image, fixed-font paginated) |
| input-text + benign image | `decoy` / `constant_image` (ImgAug lever, as an *attack* surface and as a *baseline defense* lever) |

No new attacks are constructed in this project. Compound/sequential attacks are **Future Work (§11)**.

### 4.2 The defense (the new work)

- **Coverage-complete guard** (`modality_complete`, already built). A black-box wrapper that, regardless of `has_image`, (i) recovers content from *every* channel (reads the text **and** OCRs/captions the image), (ii) runs a single unified safety check over the recovered union, (iii) gates the response. Built from primitives already in the repo (ECSO's captioning + SAGE's discrimination). Removes the `has_image` gate and the single-channel blind spot.

### 4.3 Baselines

`no_defense`, `SAGE` (input-text), `ECSO` (image caption, gated), the **ImgAug decoy lever**, and two recent SOTA defenses for "you only beat weak defenses" pre-emption: **ETA** (black-box adaptation: CLIP image pre-eval + ArmoRM output post-eval + safe-regeneration) and **MLLM-Protector** (output-side harm detector + detoxifier; the *output-axis orthogonality control*). The SOTA baselines are **breadth, not core** — included if their checkpoints/GPU cost is affordable (see plan §3); the paper stands on SAGE/ECSO/decoy.

### 4.4 The coverage map (reporting frame)

Results are framed as a **coverage map**, not a sweep — "defense effectiveness is governed by which surfaces its safety check covers":

| Defense | input-text | input-image | output | joint |
|---|:--:|:--:|:--:|:--:|
| SAGE | ✓ | — | — | — |
| ECSO | — | ✓ (caption, gated) | — | — |
| ETA | — | ✓ (CLIP) | ✓ (reward) | — |
| MLLM-Protector | — | — | ✓ | — |
| **coverage-complete (ours)** | ✓ | ✓ (OCR) | — | — |

Each attack is labelled by where it places harm; each cell tests whether that surface is covered. The headline is RQ2/RQ3: the coverage-complete guard covers the union, and its safety–utility frontier vs. the specialists and the decoy lever.

### 4.5 Metrics

- **Attack success (ASR):** fraction of HarmBench-harmful (100 prompts) judged harmful (HarmBench classifier, `gpt-5-nano`). Lower = safer. Empty responses auto-classified as refusals (handles upstream API filtering).
- **Benign refusal:** fraction of JailbreakBench-benign (100 prompts) judged a refusal. Lower = more useful.
- **Portfolio ASR (per defense):** fraction of prompts on which *at least one* suite attack defeats the defense — the deployment-relevant worst case that RQ1 turns on.
- **Safety–utility plane:** every (model, defense) as an (ASR, benign-refusal) point; the headline is whether the coverage-complete guard dominates the decoy lever and specialists.
- **Statistics:** bootstrap 95% CIs on per-cell rates; paired permutation tests on per-prompt verdicts (guard-vs-decoy, guard-vs-specialist).

---

## 5. Experimental setup

| Axis | Choice |
|---|---|
| **Target VLMs (primary)** | open-weight, NU-cluster / vLLM: `qwen2_5_vl_7b` (workhorse), `pixtral_12b`, `llama3_2_11b_vision`, `internvl3_8b`. Iterate on Qwen + InternVL3 (7–8B), complete on the rest. |
| **Encoders** | `set_theory`, `formal_logic`, `code_attack` |
| **Image transforms** | `ir_plain` (fixed-font paginated), `decoy` (`constant_image`) |
| **Defenses** | no_defense, SAGE, ECSO, decoy-lever, **coverage-complete (new)**; *(breadth)* ETA, MLLM-Protector |
| **Benchmarks** | HarmBench-harmful (rows 0–99) = ASR; JailbreakBench-benign (0–99) = utility |
| **Judges** | HarmBench classifier + JBB-refusal classifier, `gpt-5-nano` backbone (parity with ImgAug) |
| **Decoding** | deterministic (temp 0, top_p 1, seed 42) |

**Code to build:** essentially none — the coverage-complete guard (`modality_complete`) is already built and smoke-verified. This project is primarily **run + analyze**: render the existing attack suite once (Stage 1), then run the defense matrix (Stage 2). API models (gemini-2.x-flash / gpt-4o-mini / claude-sonnet-4-6) are an optional late breadth layer.

---

## 6. Falsifiable predictions

| # | Prediction | Refutation would mean |
|---|---|---|
| P1 | For each single specialist defense, ∃ a suite attack that defeats it (no single defense covers the union) | Some single defense already covers everything — collapses the motivation; pivot headline to the cost characterization |
| P2 | The coverage-complete guard reduces ASR across the *whole* suite below every specialist's worst case | Completeness is insufficient — points to a deeper cause (output-only or joint-only harm), i.e. Future Work |
| P3 | The guard's safety–utility frontier dominates ImgAug's decoy lever (≤ refusal at ≤ ASR) | The decoy lever is utility-competitive — weakens the deployment story |
| P4 | The guard generalizes to **held-out** attacks it was not tuned on | Coverage is benchmark-specific, not structural — the contribution is overfit, not a coverage property |

A clean paper needs P2–P4. P4 is what makes this a coverage result rather than a bake-off; P1 is the motivating measurement (and is robust regardless of numbers — it is a characterization, not a gamble).

---

## 7. Why this is the right project to ship first

- **Near-zero null-result risk.** A defense *designed* to cover the union beats each single specialist by construction; the only unknown is the utility cost — and that cost is itself a reportable result whatever its value. There is no "the experiment comes back empty and kills the paper" failure mode.
- **Almost no new code.** The guard is built; the attacks exist; the baselines are wired. The work is running and analysis.
- **Reliable accept pattern.** Constructive defense + safety–utility frontier + beats baselines on a unified benchmark is a well-worn path. Evaluating all baselines on a broader suite than each was individually designed for is *standard* for a defense paper — which neutralizes the "out-of-scope attack" critique that would sink the same comparison framed as an attack claim.
- **It does not foreclose the rest.** The compound attack and the deeper science (§11) build naturally on top, and the eventual stronger defense gains a *characterized* threat space to claim honest generalization against.

The two cheap moves that turn this from a bake-off into a real paper — **held-out attacks** (RQ4/P4) and the **Pareto frontier** (RQ3/P3) — are free: they are just how the runs are sliced and reported.

---

## 8. Reporting framework (every outcome is a finding)

Pre-registered interpretations so no single cell can sink the paper:

| Result | Interpretation |
|---|---|
| no single specialist covers the union (P1) | "deployed black-box defenses are specialists; coverage is the governing variable" — the motivating thesis |
| coverage-complete guard covers the union (P2) | "the minimal coverage-complete defense closes the single-surface blind spot" — the contribution |
| guard dominates the decoy lever (P3) | "completeness is cheaper than ImgAug's lever; the `has_image` gate is an avoidable artifact" |
| guard does *not* dominate MLLM-Protector | "input-coverage and output-checking are complementary axes; robust safety needs both" (strengthens, not weakens) |
| guard generalizes to held-out attacks (P4) | "coverage is structural, not benchmark-specific" — the anti-overfit result |

---

## 9. Ethics

Consistent with MathEnc / ImgAug. All experiments use standardized public harmful-prompt benchmarks (HarmBench, JailbreakBench); the encoders and image-composition primitives are from published prior work, so this project introduces **no new attack capability** — it constructs no new attacks at all. The contribution is **defense-oriented**: characterizing an insufficiency in deployed black-box defenses and providing the minimal coverage-complete fix, with its over-refusal cost reported openly so deployers do not over-rely on it.

---

## 10. Publication targets (venue-agnostic)

One venue-agnostic body of work; the venue is chosen after results are in. As a constructive defense with a clean safety–utility characterization, natural homes are security/trustworthy-ML and *ACL venues: **SaTML**, **AAAI (AI-Alignment / Safety track)**, **EACL / ARR (main or Findings)**. The same paper cannot be under review at two venues at once. Low variance on acceptance is the point of choosing this project first.

---

## 11. Future Work

Everything below is deferred — a separate contribution that builds on the coverage-complete guard, **not** part of this paper.

### 11.1 Compound (single-input) attacks
A *new* attack that layers several techniques **sequentially into one input** (e.g. `set_theory`-encode → render to image → output-framing), as opposed to the portfolio's parallel single-method queries.
- **Synergy / superadditivity:** does layering beat the bare model *more* than its components predict in isolation? A positive result is a genuine attack-mechanism finding (techniques hit independent blind spots at once, or one sets up the next).
- **Single-input evasion (scope-proof):** because the compound is *one* input the defense must process as a whole, defeating a defense with it has no "out-of-scope attack" excuse — unlike the portfolio framing. This is the clean version of "attack beats defense."

### 11.2 Cross-modal splitting and joint verification
Distribute harmful content across text and image so each channel — and any *per-channel* check, even a coverage-complete one — sees only benign content, while the model reassembles the harmful request. If clean splits exist, **per-channel completeness is structurally insufficient**, motivating **joint multimodal verification** (the `joint_verify` defender, already built) — a single safety judgment over the joint (text, image) input. If clean splits *do not* exist, that is itself a positive finding: harmful intent has an irreducible single-channel core.

### 11.3 Extending the guard to the compound and split attacks
The unified defense paper: one guard robust to the portfolio **and** the compound attack **and** (where possible) splitting, evaluated with **held-out** generalization and the full safety–utility frontier. Stronger as a follow-on precisely because *this* project will have characterized the threat space it must defend.

### 11.4 Mechanism (white-box)
On open-weight targets (HF-loaded Qwen2.5-VL / InternVL3, not vLLM): why is vision-side alignment weaker than text-side? Where/whether does the model reassemble split content (hidden-state / attention probes)? The explanatory layer beneath the coverage map.

### 11.5 The deeper theory
- **Context-contaminated safety verdicts.** ImgAug (benign image *helps*) and interference (benign content *hurts* a defense's handling of a co-present attack) are two signs of one property: these defenses do not judge each piece of content on its own merits — their verdict is contaminated by incidental context. Characterize this directly.
- **The alignment manifold.** MathEnc moves a request into alignment-sparse regions via *encoding*; this line moves it via *modality*. A unified view: alignment is non-uniform over the input representation manifold, and encoding and modality-placement are coordinates on it; a defense "covers" only where it drags the request back toward alignment-dense regions. Turns the coverage map from a taxonomy into a *predictive* theory.
- **Compositional robustness.** Whether defenses robust to attacks individually are robust to their composition — the general principle of which splitting is the limiting case.

### 11.6 Breadth
API-model generalization (gemini-2.x-flash / gpt-4o-mini / claude-sonnet-4-6) once the open-weight results are locked; broader benchmark and alignment-tier spread.
