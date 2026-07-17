# Research Proposal — Variance Channels: Best-of-N Jailbreaking Beyond Surface Noise (`bestofn_attack`)

**Workflow stage:** S4 · Literature loop (as of 2026-07-17) — founded this session; the S4 **prior-art check is the make-or-break gate** (§4). S1 external idea-check (cspaper, owner hands) is pending as a parallel gate. Nothing runs without the owner's go.

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

**New code owed (S7):** a stochastic **paraphrase** transform (open served model, meaning-preserving) · the **variance-channel wrapper / orchestration** (the two knobs) · *optional* ReNeLLM-generator port (surviving-ops-only, seeded — the native-variance booster).

## 9. Publication strategy (candidates + criteria; deadlines from `text_docs/shared/conference_timeline.md`, last verified 2026-07-16 — LIVE re-check owed at S10)

Scope (prior-art + build + a models×defenses matrix) rules out **AAAI-27** (abstract 7/21 — too tight).

- **Primary candidates:** **IEEE SaTML 2027** (full paper **2026-09-29**; Fit 10 — dedicated secure/trustworthy-ML, the natural home) · **ICLR 2027** (abstract ~9/19, full ~9/24 — EXPECTED; Rep 9.5, safety/robustness fit).
- **Aggressive option:** ARR August cycle → EACL 2027 (full **2026-08-03**) *if* the matrix moves fast — likely too tight.
- **Early non-archival outlet (optional):** NeurIPS 2026 workshops (late Aug–early Sep) — EvoRobust (8/30, robustness eval) / VLM4RWD (8/31) — a workshop version while the conference version cooks.
- **Pick criterion:** default **SaTML** (perfect fit + comfortable 9/29 timeline) unless the result is strong enough to reach for ICLR. Venue pick **DEFERRED**; re-verify deadlines live at S10.

## 10. Next actions (gates)

- **S4 · Literature loop (owner preferred-strong) — the make-or-break.** Via `lit-review-loop`: stage candidate BibTeX in `paper/literature/my_base.bib` → owner verifies + downloads PDFs → read → write `text_docs/bestofn_attack/literature_review.md` (or extend the shared review). Pointed at the two §4 checks.
- **S1 · External idea-check (owner hands)** — distilled writeup → `cspaper.org/idea-check`; parallel gate. Fallback = internal adversarial check.
- Nothing runs without the owner's go.
