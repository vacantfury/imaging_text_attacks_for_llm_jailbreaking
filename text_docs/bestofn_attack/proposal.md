# Research Proposal — Variance Channels: Best-of-N Jailbreaking Beyond Surface Noise (`bestofn_attack`)

**Workflow stage:** S9 — **R3-100 complete; blocked on a JUDGE-CONTAMINATION gate** (as of 2026-07-18). R3 scaled to 100 behaviors × 100 draws and uncovered that the free **wildguard judge false-positives 41–68% on the strategy channel** (`code_attack`/`artprompt` outputs echo the harmful task as a code literal without completing the behavior; wildguard flags the string, not the completion). **This RETRACTS the R1/R2 "strategy dominates" headline** — it was the same artifact at small N. Cleaned (obvious-FP-stripped) ASR(N) inverts the story: under the guard, surface survives best (0.72), strategy falls to ~0.37. **Next gate (owner-decision, FREE):** rejudge all 6 cells' saved responses with `cais/HarmBench-Llama-2-13b-cls` (behavior-completion judge, cluster, no re-query) before ANY channel claim; then `bon_asr` curve; gpt-5-mini reserved for the final headline. Full R3 table + mechanism: `experiment_results.md` §Round 3. — Prior autonomous-while-away context follows: Smoke validated all 3 channels end-to-end on the cluster (surface/paraphrase/strategy ✓); a smoke-caught orchestrator gap — cluster helper models inside transforms went unserved — was fixed (commit `7e8a50a`, offline-tested, delivered to cluster). **Round-1 pilot COMPLETE + spot-checked** (jobs 8446956 transforms, 8448016 evals; results in `experiment_results.md`). **Candidate finding (5-behavior pilot): the STRATEGY channel is the robust winner** — ASR(N=100) stays 1.00 even under canonicalize→guard, while paraphrase collapses 0.60→0.00 (the guard reads fluent harm) and surface drops 1.00→0.60. **Reframes the thesis:** paraphrase survives *pure* normalization but NOT a semantic guard; strategy survives both. **R2 DONE** (jobs 8449291/8450818, 10 behaviors, 3 channels × 3 defenses): **strategy channel dominates — ASR(N)=1.00 under no_defense AND canonicalize AND canonicalize→guard**; paraphrase collapses only under the semantic guard (0.70→0.10); surface partial (1.00→0.80). Guardless canonicalize barely defends (doesn't block). **Headline = the strategy variance channel is the most defense-robust.** **R3 (next):** the clean axis-1 test needs a BLOCKING normalization defense (SmoothLLM/perplexity — `semantic_smooth` free w/ cluster perturbation model); scale behaviors; full ASR-vs-N curve; gpt-5-mini rejudge (owner-gated). Full table: `experiment_results.md`. Earlier prepared-state (superseded): [S4+S1 cleared, S7 built, S6/S8 written]. S4+S1 cleared; S7 code built + offline-tested (§8); S6/S8 done — plan + FREE cheap-first pilot preset written (`text_docs/bestofn_attack/experiments_plan.md`, `conf/experiment/bestofn_attack/experiment.yaml`; qwen target + wildguard judge + vicuna helper, $0). **BLOCKER (verified):** the cluster checkout is an rsync target (no git) → the new code can't be delivered by git-pull; it needs the owner's **Cursor Sync-Rsync**. **Resume = experiments_plan.md §BLOCKER:** owner syncs local→remote + says "go" → session runs smoke → Stage 1 → fills timestamps → Stage 2 → reports job ids. API-judged headline run reserved (owner-gated). S4 literature loop done (synthesis in `literature_review.md` §13); **S1 external idea-check PASSED** — cspaper green-lit it ("bridges a critical gap... uniquely addresses the degradation of sampling budgets under canonicalization, overlooked by the other papers"; neither Plentiful nor LIAR was even retrieved as a scoop; review pasted into `idea_check.md`). The idea-check surfaced two papers the S4 search missed, now folded into §13: **I-FSJ** (`NEURIPS2024_39a3aa9d` — grey-box demo-search that already beats SmoothLLM/PPL; trims "first to beat normalization" → we claim the general black-box channel-depth *law*) and **Adversarial Déjà Vu** (`dabas2026adversarial` — skill-primitive defense overlapping our strategy channel). **Gate verdict = SURVIVES, NARROWED** (see §4 → S4 findings + review §13.6). **Open before build: owner ratifies the reframe + says go for S5.** Deferred: full-text reads of the must-distinguish set (LIAR / Plentiful / Say-It-Differently / AutoDAN-Reasoning; I-FSJ read done) at camera-ready. Nothing runs without the owner's go.

*Origin: pivoted 2026-07-17 from the defense-framed `bestofn_defense` (Paper D). Over that session the framing flipped from defense-primary to **attack-primary**; a new subfolder was the clean home. Running name is a WORKING title (refined at writing). Full design was co-developed with the owner in the 2026-07-17 session.*

---

## 1. Decision & posture (settled 2026-07-17 — do NOT relitigate)

- **Attack-PRIMARY paper.** The `canonicalize → guard` defense (carried over from `bestofn_defense`) folds in as the **SUPPORTIVE secondary contribution**, living in THIS subfolder.
- **Supersedes `bestofn_defense` as a standalone.** Shared `src/` code is reused as-is; `bestofn_defense` docs go legacy. (Portfolio card + repo TODO re-scoped to this paper.)
- **Home:** this repo, `bestofn_attack` namespace (existing repo — Paper-C precedent, shares pipeline/harness/data; no new repo).

## 2. The idea — variance channels

Best-of-N (Hughes et al., NeurIPS 2025) is a black-box **budget** attack: sample N stochastic variants of one request, succeed if *any* lands; ASR is power-law in N (`1-(1-p)^N → 1`).

**Key insight: Best-of-N's *variance channel* — where its N variants differ — determines both its raw power and its defense-evasion.** Vanilla BoN varies only the **surface** (word-scramble / random-caps / ASCII-noise), which any input-normalization defense (canonicalization, perplexity filter, paraphrase defense, SmoothLLM) neutralizes.

**Thesis: move the variance into deeper channels.** A spectrum of increasing channel depth:

| Channel | What varies per draw | vs normalization defenses | Diversity / effective-N |
|---|---|---|---|
| **surface** (= vanilla BoN) | scramble/caps/ASCII on the request | **dies** (normalization strips it) | low; free per draw |
| **input-paraphrase** | semantic reword of the request, fixed attack | **survives** | moderate (saturates in ~tens); LLM cost per draw |
| **strategy** | sample the attack family per draw | **survives** | **maximal** — different attacks fail independently (anti-correlated) |

**Core claim:** *channel depth sets effective-N and defense-survival* — surface < paraphrase < strategy, and the gap **widens against defenses**. Semantic/strategy Best-of-N matches/exceeds vanilla BoN on raw models and **dominates** it against input-normalization defenses, at a characterizable **work-factor**.

## 3. The wrapper (general, two uniform knobs)

A Best-of-N wrapper **parameterized by its variance channel**. Two *uniform* variance knobs over the whole attack factory:

- **which-paraphrase** — a stochastic, meaning-preserving paraphrase stage applied to the behavior *before* any attack (attack-agnostic).
- **which-attack** — sample the attack family per draw from the registered bank.

**Generality is structural:** every registered `PromptTransformation` is a drop-in member — no per-attack variance code. Sample-attack × input-paraphrase gives the strong lever (anti-correlated draws) with zero tailoring. ReNeLLM-style *native* within-family variance (random rewrite-op combinatorics) is an **optional per-family booster**, never required for membership.

- **Vary DURING, not AFTER.** Real variance = the attack re-drawn stochastically per row (the existing `expand_bon_dataset` fan-out already runs the encoder per row). Bolting surface noise onto an attack's *output* is rejected: it is trivial/correlated, corrupts structured encodings (base64/code/formula), and sits in the canonicalizable head (the defense erases it). See the 2026-07-17 design trail.
- **Extends across modality** — the attack slot also takes image renderers (paraphrase the behavior, then render).
- Legitimately a **budget** attack (not a fixed portfolio): the sampling space (≈bank-size × params × paraphrases) far exceeds any N run.

## 4. Novelty & prior-art — THE gate (S4)

**Novelty lane:** the **budget / effective-N lens applied to semantic/strategy perturbations, characterized against input-normalization defenses.** NOT "semantic jailbreak" (crowded), NOT "ensemble of attacks" (known).

**Must carve against:** PAIR / TAP (iterative *optimizers* with feedback — not budget attacks, not studied as budget-vs-normalization) · ReNeLLM (random rewrite ops — one native-variance instance, not the channel-depth framing) · rephrasing/persuasion attacks (PAP etc.) · portfolio / best-of-all (fixed max, not a budget power-law; the repo's `complementarity_gap`).

**Make-or-break checks (via `lit-review-loop`), either kills the paper:**
1. "Semantic / strategy Best-of-N vs input-normalization defenses — already published?"
2. "Best-of-N over an *attack distribution* — already published?"

If either exists → re-scope or kill. **Boundary:** adding feedback (reweight toward families that worked) turns this into an optimizer (PAIR/TAP class) = a different paper — keep the pure-sampling budget framing.

### S4 findings (2026-07-17 search pass — gate verdict: SURVIVES, NARROWED)

Three parallel searches (log: `outputs/lit_review/2026-07-17/`). Neither make-or-break check is pre-empted, but two close-prior-art papers **narrow and sharpen** the novelty — the framing must change.

- **Check #1 (semantic/strategy BoN vs normalization defenses) — OPEN.** No paper does all three halves (semantic/strategy channel + budget/power-law + measured-vs-normalization-defense). Closest: **Say It Differently** (2511.10519 — semantic-style variance +57pp, but no budget, no defense test) and **LIAR** (2412.05232 — self-labels a "best-of-N attack" and claims perplexity-evasion, but varies *output* continuations from a weak model, not input paraphrase/strategy, and only *asserts* evasion, never measures it vs a defense).
- **Check #2 (BoN over an attack distribution) — the operator itself is NOT novel.** **Plentiful Jailbreaks with String Compositions** (2411.01084) is already "an automated best-of-N attack that samples from a combinatorially large space of string compositions" — but **surface-only** (leetspeak/cipher/base64), no defense test. Combined with the base's §9.1 ruling that best-of-suite (fixed max over an ensemble = AutoAttack) is non-novel, **we can no longer claim "best-of-N over a distribution" as the contribution.**
- **The whole strategy/distribution space is OPTIMIZER-class** (h4rm3l bandit; AutoDAN-Turbo/-Reasoning learned library + scorer; Rainbow Teaming / RainbowPlus / Ferret QD; DAGR / AutoRISE / Babel feedback; "Average Jane" bandit) — none is a pure-sampling budget/power-law attack, and **not one tests against input-normalization/rendering defenses.** The defense-survival axis is empty ground.
- **Coined framing** ("variance channel" / "channel depth") returns zero on-point hits — unclaimed.

**Sharpened novelty lane (what to claim):** (1) moving BoN's variance into the **semantic-paraphrase / sampled-attack-family** channel — *deeper than* Plentiful's surface-string compositions; (2) the **channel-depth / effective-N characterization** (surface < paraphrase < strategy); (3) **measured defense-survival vs input-normalization defenses** — nobody has done this; SemanticSmooth's own Table 2 (semantic attacks leave 46%/54% ASR under SmoothLLM vs 20%/26% under SemanticSmooth) is published *supporting* evidence.

**DROP/soften:** "best-of-N over a distribution is novel." Frame the contribution as **channel-depth + defense-survival**, not the distribution-BoN operator.

**Must-read full text before commit:** LIAR (2412.05232), Plentiful (2411.01084), Say It Differently (2511.10519), AutoDAN-Reasoning (2510.05379); PAP (2401.06373) + h4rm3l (in base) for related work. Candidates staged (unverified) in `paper/literature/my_base.bib`.

## 5. Contributions (provisional)

1. The **variance-channel framing** of Best-of-N (surface / paraphrase / strategy) + the effective-N / work-factor characterization.
2. A **general, uniform** Best-of-N wrapper (two knobs) over an attack factory — any attack is a drop-in member.
3. **Empirical:** channel depth → effective-N and defense-survival across models × defenses; wrapped BoN defeats the input-normalization defenses that neutralize vanilla BoN.
4. *(Supportive)* the `canonicalize → guard` defense, and a **map** of where on the grid it holds (N-independence on the canonicalizable head) vs. fails (work-factor cost on the irreducible tail).

## 6. Threats to validity

- **Novelty collapse (§4) — the top risk;** gate S4 hard.
- **Against RAW models the win is weak** (vanilla BoN already saturates at large N) — the real teeth are **against defenses**; frame accordingly.
- **Cost honesty:** semantic/strategy variants cost LLM calls per draw (not BoN's near-free noise) → the work-factor must price *total attacker compute*, not just N.
- **Attribution:** strategy-sampling is a black-box ensemble → report *which families carry the load* (`complementarity_gap`) so it reads as insight, not mystery-max, and pre-empts "isn't this just a portfolio?".
- **Paraphraser refusal/cost:** the paraphrase stage is an aligned LLM that may refuse harmful rewording → use an open, cluster-served model.

## 7. Judge methodology (reuse the shared Round-J resolution)

Same as Papers B/C/D — do NOT re-run judge selection. **Headline:** `gpt-5-mini` (validated, API). **Robustness:** `WildGuard` rejudge on saved responses (free, served). **Pilot/intermediate:** `WildGuard` only. **HARD GATE (owner 2026-07-16):** any API model in an experiment needs a stated good reason + explicit owner ask before running; pilots/smokes/directional runs use FREE cluster models.

## 8. Reused machinery (shared `src/`, cross-paper) + new code owed

**Reuse as-is:** `non_llm_best_of_n` encoder (surface channel) · `canonicalize` / `canonicalize_guard` (the supportive defense) · `bon_asr` (ASR(N) + log-log slope = the effective-N meter, and the "is a channel meaningful?" certifier) · `complementarity_gap` analysis (which-families-carry-load) · the transformation factory (all encoders + ReNeLLM cloned at `other_repos/ReNeLLM`) · the defense factory (`sage` / `semantic_smooth` / `ecso` / … = normalization defenses to attack) · `expand_bon_dataset` (per-behavior fan-out).

**New code — S7 status (2026-07-17):**
- ✅ **BUILT** — stochastic **paraphrase** transform (`llm_paraphrase`; `src/prompt_transformations/text/encoders/llm_paraphrase_encoder.py` + `conf/text_encoding/paraphrase.yaml`; temperature-driven diversity, refusal→no-op fallback).
- ✅ **BUILT** — the **variance-channel wrapper** (`variance_channel_bon`; `src/prompt_transformations/text/variance_channel.py` + `conf/text_encoding/variance_channel.yaml`). One transform, `channel: surface|paraphrase|strategy`, two uniform knobs (which-paraphrase pre-step + which-attack bank sampling per row), sub-transform usage aggregated for the work-factor. Registered + aliased (`paraphrase`, `variance_channel`, `bon_wrapper`); **structurally tested offline (no model calls)** — registration, surface perturbation, per-row bank sampling, output ordering, seed reproducibility all pass.
- ⏳ *optional* ReNeLLM-generator port (surviving-ops-only, seeded — the native-variance booster); deferred, not required for the first matrix.

**Next (S6/S8, owner-gated):** experiment matrix design + **cost estimate** (models × normalization defenses × channels × N-budget) → owner approves before ANY run (cheap-first: free cluster judge/target for pilots; no API model without explicit OK).

## 9. Publication strategy (owner-directed 2026-07-17: AAAI-PRIMARY; deadlines from `text_docs/shared/conference_timeline.md`, last verified 2026-07-16 — LIVE re-check owed at S10)

**Target: AAAI-27 (main + AI Alignment track — Rep 9.0, Fit 9.0).** Abstract **2026-07-21** (register by **7/20** — a FREE, non-binding placeholder → costs nothing, preserves the option); full paper **2026-07-28**. The claim is committable now for an honest abstract (*"variance-channel best-of-N beats vanilla BoN against input-normalization defenses"*).

- **Sprint plan (11 days):** clear **S4 prior-art FAST** (make-or-break) → build (paraphrase transform + variance-channel wrapper) → aggressively-scoped models×defenses matrix → decide ~**7/26** (TODO item-1 ④) whether results back the claim → submit 7/28 or fall back.
- **Clean fallback (no loss — same work, later deadline):** **IEEE SaTML 2027** (full **2026-09-29**, Fit 10 — the natural home) · or **ICLR 2027** (~9/24 EXPECTED, Rep 9.5).
- **Optional early non-archival outlet:** NeurIPS 2026 workshops (late Aug) — EvoRobust (8/30) / VLM4RWD (8/31).
- **Honest caveat (once):** 11 days from an un-run prior-art check to a full experimental paper is a genuine sprint, and S4 could still kill it — but the free abstract + the SaTML fallback cap the downside (cheap-option play). Check the AAAI **AI Alignment track** CFP for a possibly-distinct deadline/rubric (TODO item-1 ②).

## 10. Next actions (gates)

- **S4 · Literature loop (owner preferred-strong) — the make-or-break.** Via `lit-review-loop`: stage candidate BibTeX in `paper/literature/my_base.bib` → owner verifies + downloads PDFs → read → write `text_docs/bestofn_attack/literature_review.md` (or extend the shared review). Pointed at the two §4 checks.
- **S1 · External idea-check (owner hands)** — distilled writeup → `cspaper.org/idea-check`; parallel gate. Fallback = internal adversarial check.
- Nothing runs without the owner's go.
