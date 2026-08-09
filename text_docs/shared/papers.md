# Papers in this repo — alias index

This repository is a **shared harness for a line of work**, not a single paper. This file is the crisp
`ID ↔ alias ↔ paper ↔ namespace` map so any reader or session can orient in one glance. Series IDs follow
the paper-ID standard (owner-ratified 2026-08-03; registry of record = the science repo `portfolio.md`):
`<BIG><SMALL>-<n>`, earned at commitment; dead papers carry no series ID (a rare post-submission death
leaves its number as a tombstone, never reused); the legacy letters remain valid aliases.

**This is a projection, not the source of truth.** The canonical registry — evaluation, priority, venue and
review status, publication record, and future aims (including papers outside this repo, e.g. the QML side
track) — is the portfolio of record (the science repo `portfolio.md`); live status/venue tracking is the
gitignored `TODO.md`. Keep review status, scores, and venue decisions **out of this committed file** (public
repo, public-grade discipline).

| ID | Alias | Codename | Topic (one line) | Namespace | Key doc | Stage |
|---|---|---|---|---|---|---|
| **AS-1** | **A** | MathEnc | *Exposing LLM Safety Gaps Through Mathematical Encoding* — text-side encoders (set theory, formal logic, code) recast harmful queries into out-of-distribution surface forms | — *(predates namespacing; encoders live in `src/prompt_transformations/text/`)* | `README.md` line-of-work; arXiv 2605.03441 | published |
| **AS-2** | **B** | Presence Tax | *The Uncontrolled Variable: Vision–Language Model Refusal Responds to Image Presence in Ways Risk Cannot Explain* — safety-aligned VLMs key their refusal threshold on whether an image is attached, holding the request fixed. ⚠️ **Spine REFRAMED 2026-08-09 (cspaper review 3, con 3):** the paper no longer claims attachment is uninformative — a black-box study cannot establish that, and attachment plausibly does correlate with risk in real traffic. It claims the RESPONSE does not behave like a risk policy, on four legs: it varies with canvas colour (+22pp black vs white, same size) and pixel count, its sign inverts across checkpoints, it survives an explicit instruction to disregard the image, and it fires on a bare asserted attachment with nothing attached. Legs 1/3/4 are measured on frontier hosted models and leg 2 on open weak ones, so neither tier can be dismissed as the other's failure. The cost lands on sensitivity-adjacent benign traffic (all ten OR-Bench categories, 26 of 30 per-category contrasts surviving BH) and is decoupled from any safety benefit. ⚠️ **Codename ≠ title since 2026-08-08:** the codename stays `Presence Tax` (registered here and in the science portfolio); the TITLE dropped the tax metaphor because the exchange rate was withdrawn as unreproducible and the sign inverts on `pixtral-12b`. Do not 'fix' either to match the other. | `image_presence_threshold` | *(working docs local-only)* | under review |
| **AS-3** | **C** | The Decode Gap | Black-box **recover→decode→guard** defense — deployed guards *inspect/reason about* content but never *decode* an obfuscated payload; `modality_complete` closes the decode gap | `autoattack_defense` | `text_docs/autoattack_defense/{proposal,experiments_plan}.md` | in progress |
| **AS-4** | **D** | Variance Channels | *Best-of-N Jailbreaking Beyond Surface Noise* — Best-of-N over a strong structural/encoding attack (code_attack) decisively beats vanilla surface-noise BoN, defended and undefended; the strategy channel survives a canonicalize→guard defense | `bestofn_attack` | `text_docs/bestofn_attack/proposal.md` | in progress |
| **AS-7** | — *(born ID-first)* | Read Access | *Read Access: Channel Coverage and Oracle Inflation in Black-Box Multimodal Guardrails* (title settled 2026-08-08 — this row previously carried a divergent working title, "What the Defense Can Read: Channel Scope and Evaluation Protocol…"; **`paper.tex` is the authority and this row follows it**) — what an input defense can read decides what it catches (text-only guards miss a payload that merely moved to the image channel), and what the evaluation lets it read decides how safe it scores (oracle protocol inflates measured benefit) | `defense_read_access` | *(working docs local-only)* | in progress |
| — *(dead, no ID)* | ~~**E**~~ | Smuggled Actions | **→ SPUN OUT 2026-07-19 to its own repo `llm_agent_security`** — agent-side security (encoded indirect injection on LLM agents) is a separate line with a different runtime (tool-loop / action-scoring, not this repo's VLM eval pipeline). Work continues there; this repo keeps the model-side papers A–D. | — | sibling repo `llm_agent_security` | moved out |

**Note — AS-2 SPLIT into AS-2 + AS-7 on 2026-08-08, and the old `imgaug_defense` namespace was renamed.** Paper B was one paper claiming "one mechanism, three surfaces." Its own data refutes that: `internvl3-8b` and `pixtral-12b` show −43 / −37pp of ECSO decoy amplification while their benign threshold does not move at all (+7pp n.s., −2pp n.s.), so the model-level effect and the defense-level effect are causally INDEPENDENT — they shared a description, not a mechanism. AS-2 keeps the model-side work (renamed `ImgAug` → **Presence Tax**, namespace `imgaug_defense` → **`image_presence_threshold`**); AS-7 takes the defense-and-evaluation work (**`defense_read_access`**). Each paper carries an explicit scope boundary plus a control ruling out the other's mechanism, which is what carries the distinctness bar for concurrent submission (AAAI's rule is cross-venue: *"…whether submitted to AAAI-27 or another archival conference or journal"*, so track choice does not soften it).

⚠️ **Pre-split outputs all live under `outputs/image_presence_threshold/`, for BOTH papers.** The output tree was renamed wholesale rather than split, because splitting it would have broken the `upstream_ref.source_dir` provenance chains that let a result reconstruct what produced it. AS-7's historical runs are identified by their **`campaign`** field (e.g. `paper_b_guard_channel`, `paper_b_channel_coverage`, `paper_b_deployable_*`), never by directory. New AS-7 runs write to `outputs/defense_read_access/`. All 229 chains were verified resolving after the rename.

**Paper-source dirs are keyed by series ID, not namespace (renamed 2026-08-08, owner order).** Each live paper's LaTeX/source lives at `paper/as-2` · `paper/as-3` · `paper/as-4` · `paper/as-7` (formerly `paper/<namespace>`). The Namespace column above still governs `text_docs/` and `outputs/` only. Non-paper dirs under `paper/` (`literature`, and the historical `coverguard` / `bestofn_defense` / `aaai_2027` tombstone) keep their names.

**Boundary with AS-6** (guard internals, repo `model_internals_safety`): AS-6 probes guard ACTIVATIONS to separate "never decoded" from "decoded but never blocked"; AS-7 is black-box throughout and claims no mechanism inside the guard. AS-7's channel result (a text guard never *receives* an image payload) sits upstream of both of AS-6's links and supplies it a hypothesis, which AS-6 re-measures in its own harness per its own scope note.

**What is tracked.** Only `proposal.md`, `experiments_plan.md`, and structural planning docs are committed. Working
result logs — `experiment_results.md`, `experiment_matrix.md`, `experiments_findings.md`, `progress_report.md`,
and per-paper working notes — are **gitignored on purpose**: analyzed results belong in the papers, not in untracked
working notes on a public repo. Do not cite them as a "key doc" here; a reader cloning the repo will not have them.

**Namespacing convention.** Each paper owns a subdir keyed by its **Namespace** above under `text_docs/`,
`conf/experiment/`, and `outputs/`; `shared/` holds cross-paper material (venue facts, judge validation,
literature, this index). Series IDs are the primary identifiers; the letters (A/B/C/D/E) remain valid
aliases and the historical shorthand; codenames are the paper-facing titles. When a new paper starts, it is
born ID-first — add its row here and create its namespace subdirs. Note: the letter E was reassigned
2026-08-02 to the model-internals first paper (**AS-5**, repo `model_internals_safety`); a pre-08-02
"Paper E" in this repo's docs means Smuggled Actions (dead 2026-08-02 — dead papers carry no series ID).

**Note — the `bestofn_defense` namespace is NOT a separate paper.** It holds Paper D's *supportive*
canonicalize→guard defense sub-part — pivoted 2026-07-17 from a standalone paper into a section of the
attack-primary Paper D (`bestofn_attack`). Any older doc calling `bestofn_defense` "Paper D" or "Paper E"
is stale drift; the live aliases are the table above.

**Note — `judge_reliability` ("Blind Judges") is NOT a standalone paper (PARKED 2026-07-19).** It was
investigated as Paper E, but two independent scoop-checks returned Medium/High overlap (the neighborhood is
crowded from two directions — judge-calibration = StrongREJECT/SORRY-Bench; capability-gap = the
scalable-oversight scaling laws), so it was **not pursued standalone** and the **E alias moved to
`agent_injection`**. Its measured judge-validation (Round-J human-κ, WildGuard FP, gpt-5-nano inflation) stays
in Papers C/D where it already lives. Disposition record: `text_docs/judge_reliability/proposal.md §11`. Any
doc calling `judge_reliability` "Paper E" is now stale drift.
