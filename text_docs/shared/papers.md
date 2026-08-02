# Papers in this repo — alias index

This repository is a **shared harness for a line of work**, not a single paper. This file is the crisp
`alias ↔ paper ↔ namespace` map so any reader or session can orient in one glance.

**This is a projection, not the source of truth.** The canonical registry — evaluation, priority, venue and
review status, publication record, and future aims (including papers outside this repo, e.g. the QML side
track) — is the portfolio of record (the science repo `portfolio.md`); live status/venue tracking is the
gitignored `TODO.md`. Keep review status, scores, and venue decisions **out of this committed file** (public
repo, public-grade discipline).

| Alias | Codename | Topic (one line) | Namespace | Key doc | Stage |
|---|---|---|---|---|---|
| **A** | MathEnc | *Exposing LLM Safety Gaps Through Mathematical Encoding* — text-side encoders (set theory, formal logic, code) recast harmful queries into out-of-distribution surface forms | — *(predates namespacing; encoders live in `src/prompt_transformations/text/`)* | `README.md` line-of-work; arXiv 2605.03441 | published |
| **B** | ImgAug | *Image Augmentation Strengthens VLM Defenses Against Encoded Jailbreak Attacks* — adding an image (even a content-unrelated decoy) shifts a defense's behavior via coverage alignment | `imgaug_defense` | *(working docs local-only)* | under review |
| **C** | The Decode Gap | Black-box **recover→decode→guard** defense — deployed guards *inspect/reason about* content but never *decode* an obfuscated payload; `modality_complete` closes the decode gap | `autoattack_defense` | `text_docs/autoattack_defense/{proposal,experiments_plan}.md` | in progress |
| **D** | Variance Channels | *Best-of-N Jailbreaking Beyond Surface Noise* — Best-of-N over a strong structural/encoding attack (code_attack) decisively beats vanilla surface-noise BoN, defended and undefended; the strategy channel survives a canonicalize→guard defense | `bestofn_attack` | `text_docs/bestofn_attack/proposal.md` | in progress |
| ~~**E**~~ | Smuggled Actions | **→ SPUN OUT 2026-07-19 to its own repo `llm_agent_security`** — agent-side security (encoded indirect injection on LLM agents) is a separate line with a different runtime (tool-loop / action-scoring, not this repo's VLM eval pipeline). Work continues there; this repo keeps the model-side papers A–D. | — | sibling repo `llm_agent_security` | moved out |

**What is tracked.** Only `proposal.md`, `experiments_plan.md`, and structural planning docs are committed. Working
result logs — `experiment_results.md`, `experiment_matrix.md`, `experiments_findings.md`, `progress_report.md`,
and per-paper working notes — are **gitignored on purpose**: analyzed results belong in the papers, not in untracked
working notes on a public repo. Do not cite them as a "key doc" here; a reader cloning the repo will not have them.

**Namespacing convention.** Each paper owns a subdir keyed by its **Namespace** above under `text_docs/`,
`conf/experiment/`, and `outputs/`; `shared/` holds cross-paper material (venue facts, judge validation,
literature, this index). Aliases (A/B/C/D/E) are the stable shorthand; codenames are the paper-facing titles.
When a new paper starts, add its row here and create its namespace subdirs.

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
