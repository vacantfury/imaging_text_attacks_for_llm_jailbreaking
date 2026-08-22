# Research Proposal — Variance Channels: Best-of-N Jailbreaking Beyond Surface Noise (`bestofn_attack`)

**Workflow stage:** S12 — **THESIS RESTORED TO ATTACK-PRIMARY (2026-08-22, owner-ordered).** The draft had inverted its own ratified priority and this is recorded so no session re-drifts. HOW IT HAPPENED: the term "variance channel" changed owner. In this proposal it is a property of the ATTACKER (where the N draws differ: surface / paraphrase / strategy). In the 2026-08-10 draft it had become a property of the DEFENSE (SAGE resampling its own verdict), introduced as "a THIRD variance channel, and it is the defender's own choice" — counting the defender's as an extension of the attacker's three. From there the defense material, which §1 designates SUPPORTIVE SECONDARY, occupied contribution bullets 1-4, the attack fell to bullet 5 described as "the attack that makes the measurement possible", and the title became "Don't Ask the Model You're Defending". WHY IT MATTERED: all four GPT-5.6-Terra cspaper reviews (4/4/4/4, against GLM's 6/8/7/7) fire at the defense-mechanism claims, because the mechanism had become the paper and could not carry the scrutiny. Worse, the title asserted what the data refutes — LLM Self Defense screens with the model it is defending and behaves like the fixed-verdict defenses. RESTORED: title "Depth, Not Breadth: Best-of-$N$ Jailbreaking Beyond Surface Noise" (the R4 ratified language); abstract and contributions attack-first, leading with the structural-channel result ($67$/$22$/$15$ vs $\le 4.7$ / $\le 3.0$, and the same budget worth $+3.0$ on surface vs $+62.3$ on structural); the borrowed-strength, temperature and fusion material demoted to bullets explicitly marked "(supporting)"; the causal-isolation claim removed from the abstract, where it had survived the body's narrowing. The FUSION finding (2026-08-22) belongs here as supporting evidence for defense-survival, which is half of §2's ratified core claim, and is NOT a new thesis. BODY SWEPT SAME SESSION (2026-08-22): the restoration had touched title/abstract/contributions only, and the body still named the temperature panel "the panel this paper's central claim rests on" and attributed the paper's claim to the sampled verdict. Three claim anchors rewritten, a "Superadditive in what?" roadmap added at the head of Results routing the reader to the factorial, the factorial promoted to its own subsection "Depth, Not Breadth" (sec:factorial), and the Conclusion closed on the dissociation (depth breaks a transform defense, breadth breaks a gate). NO section reordering: the factorial genuinely depends on the paraphrase arm defined just before it, and a 700-line move near a wall is the wrong risk. Build clean, 0 undefined refs, 0 undefined citations, 0 '??' in the rendered PDF. INTRO RESTRUCTURED SAME SESSION: the body sweep exposed that the Introduction was still the pre-restoration defense-first narrative while the abstract had already been restored, so the two told different stories in the first column. The attack paragraph was moved ahead of all defense material and reheaded "Depth, not breadth" (it had been "The attack that makes the channel visible" — the demotion the restoration existed to undo); "Isolating the channel. The claim is causal, so we test it causally" became "Where the surviving draws come from (supporting)" with the causal assertion dropped to match the abstract; the "we identify a third [variance channel]" announcement was softened to supporting; and "Not all variance pays" now names the depth-versus-breadth dissociation. Contributions needed no change (already attack-first with bullets 3-4 marked supporting). Verified: build clean, 0 undefined, 0 '??', drift-term sweep 0 hits against a control pattern matching 78, and both validated builders (paper_d_temperature_ci, paper_d_severity_ci) still reproduce all 18 Table 3 cells and all 4 actionable counts exactly. R21 verdict-isolation (xc 307/308/309) was CANCELLED unfinished by owner order — it could not complete before the wall and the restored thesis does not rest on it. REVIEW 7 con 3 TRACED (2026-08-22): the Gemma 15-vs-8 inconsistency the reviewer called unresolved is real and now explained — tab:wrapper reproduces exactly from outputs/_quarantine/code_attack_appendleft_20260805/ (pre-correction, appendleft bug) while tab:compose is post-correction. Caption now states this; whether a quarantined table should ship at all is filed as TODO item 0, unresolved. — Prior S9 context follows. S9 — **R3 verified + R4 baselines resolved → STORY REFRAME** (as of 2026-07-19). R4 attack-paper baselines (gpt-5-mini): the attack clears every bar (beat N=1: 0.63→0.92; beat vanilla BoN/Hughes: 0.92 vs 0.74 no_def, 0.58 vs 0.54 guard; beat raw-prompt floor: 0.92 vs 0.19). BUT the "attack-diversity / bank" mechanism is REFUTED — **code_attack ALONE (0.92/0.58) ≈ the diverse bank (0.96/0.61)**, diversity adds only +0.03–0.04, and code_attack is far more query-efficient (63% vs 27% per-draw). **Reframe: hero = BoN over a single strong STRUCTURAL attack (code_attack) = "beyond surface noise"; depth-not-breadth; query-efficiency as secondary angle.** Details: `experiment_results.md` §Round 4. — Prior R3 context: R3-100 VERIFIED via gpt-5-mini rejudge (2026-07-18). R3 scaled to 100 behaviors × 100 draws. The free wildguard judge false-positived 41–68% on the strategy channel (`artprompt` + pure-echo `code_attack`), so all 60k saved responses were rejudged with the decided main judge `gpt-5-mini` (HB rubric, decoupled, ~$47). **Verified headline: the strategy channel is the most defense-robust** — ASR(N=100) under canon→guard = **0.61** (per-draw 6.3%) vs surface 0.54 (4.3%) and paraphrase 0.22 (2.0%); the variance-channel thesis HOLDS (BoN keeps amplifying strategy through the guard, 0.06→0.61 across N, but is capped for paraphrase 0.02→0.22). Two judge errors corrected en route (wildguard inflation AND my own heuristic over-correction). Full table + ASR-vs-N curve: `experiment_results.md` §Round 3 VERIFIED. **Next:** seed-variance + 2nd target model; small human-label audit (~50 strategy draws); the clean axis-1 pure-normalization (SmoothLLM) test still outstanding. Full R3 table + mechanism: `experiment_results.md` §Round 3. — Prior autonomous-while-away context follows: Smoke validated all 3 channels end-to-end on the cluster (surface/paraphrase/strategy ✓); a smoke-caught orchestrator gap — cluster helper models inside transforms went unserved — was fixed (commit `7e8a50a`, offline-tested, delivered to cluster). **Round-1 pilot COMPLETE + spot-checked** (jobs 8446956 transforms, 8448016 evals; results in `experiment_results.md`). **Candidate finding (5-behavior pilot): the STRATEGY channel is the robust winner** — ASR(N=100) stays 1.00 even under canonicalize→guard, while paraphrase collapses 0.60→0.00 (the guard reads fluent harm) and surface drops 1.00→0.60. **Reframes the thesis:** paraphrase survives *pure* normalization but NOT a semantic guard; strategy survives both. **R2 DONE** (jobs 8449291/8450818, 10 behaviors, 3 channels × 3 defenses): **strategy channel dominates — ASR(N)=1.00 under no_defense AND canonicalize AND canonicalize→guard**; paraphrase collapses only under the semantic guard (0.70→0.10); surface partial (1.00→0.80). Guardless canonicalize barely defends (doesn't block). **Headline = the strategy variance channel is the most defense-robust.** **R3 (next):** the clean axis-1 test needs a BLOCKING normalization defense (SmoothLLM/perplexity — `semantic_smooth` free w/ cluster perturbation model); scale behaviors; full ASR-vs-N curve; gpt-5-mini rejudge (owner-gated). Full table: `experiment_results.md`. Earlier prepared-state (superseded): [S4+S1 cleared, S7 built, S6/S8 written]. S4+S1 cleared; S7 code built + offline-tested (§8); S6/S8 done — plan + FREE cheap-first pilot preset written (`text_docs/bestofn_attack/experiments_plan.md`, `conf/experiment/bestofn_attack/experiment.yaml`; qwen target + wildguard judge + vicuna helper, $0). **BLOCKER (verified):** the cluster checkout is an rsync target (no git) → the new code can't be delivered by git-pull; it needs the owner's **Cursor Sync-Rsync**. **Resume = experiments_plan.md §BLOCKER:** owner syncs local→remote + says "go" → session runs smoke → Stage 1 → fills timestamps → Stage 2 → reports job ids. API-judged headline run reserved (owner-gated). S4 literature loop done (synthesis in `literature_review.md` §13); **S1 external idea-check PASSED** — cspaper green-lit it ("bridges a critical gap... uniquely addresses the degradation of sampling budgets under canonicalization, overlooked by the other papers"; neither Plentiful nor LIAR was even retrieved as a scoop; review pasted into `idea_check.md`). The idea-check surfaced two papers the S4 search missed, now folded into §13: **I-FSJ** (`NEURIPS2024_39a3aa9d` — grey-box demo-search that already beats SmoothLLM/PPL; trims "first to beat normalization" → we claim the general black-box channel-depth *law*) and **Adversarial Déjà Vu** (`dabas2026adversarial` — skill-primitive defense overlapping our strategy channel). **Gate verdict = SURVIVES, NARROWED** (see §4 → S4 findings + review §13.6). **Open before build: owner ratifies the reframe + says go for S5.** Deferred: full-text reads of the must-distinguish set (LIAR / Plentiful / Say-It-Differently / AutoDAN-Reasoning; I-FSJ read done) at camera-ready. Nothing runs without the owner's go.

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
