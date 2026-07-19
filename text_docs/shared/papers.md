# Papers in this repo — alias index

This repository is a **shared harness for a line of work**, not a single paper. This file is the crisp
`alias ↔ paper ↔ namespace` map so any reader or session can orient in one glance.

**This is a projection, not the source of truth.** The canonical registry — evaluation, priority, venue and
review status, publication record, and future aims (including papers outside this repo, e.g. the QML side
track) — is the portfolio of record (psyche `self_model/portfolio.md`); live status/venue tracking is the
gitignored `TODO.md`. Keep review status, scores, and venue decisions **out of this committed file** (public
repo, public-grade discipline).

| Alias | Codename | Topic (one line) | Namespace | Key doc | Stage |
|---|---|---|---|---|---|
| **A** | MathEnc | *Exposing LLM Safety Gaps Through Mathematical Encoding* — text-side encoders (set theory, formal logic, code) recast harmful queries into out-of-distribution surface forms | — *(predates namespacing; encoders live in `src/prompt_transformations/text/`)* | `README.md` line-of-work; arXiv 2605.03441 | published |
| **B** | ImgAug | *Image Augmentation Strengthens VLM Defenses Against Encoded Jailbreak Attacks* — adding an image (even a content-unrelated decoy) shifts a defense's behavior via coverage alignment | `imgaug_defense` | `text_docs/imgaug_defense/paper_b_rebuttal_results.md` | under review |
| **C** | The Decode Gap | Black-box **recover→decode→guard** defense — deployed guards *inspect/reason about* content but never *decode* an obfuscated payload; `modality_complete` closes the decode gap | `autoattack_defense` | `text_docs/autoattack_defense/{proposal,experiments_plan,experiment_results}.md` | in progress |
| **D** | Variance Channels | *Best-of-N Jailbreaking Beyond Surface Noise* — Best-of-N over a strong structural/encoding attack (code_attack) decisively beats vanilla surface-noise BoN, defended and undefended; the strategy channel survives a canonicalize→guard defense. Venue: **AAAI-27 primary** (abstract 7/21 / paper 7/28) | `bestofn_attack` | `text_docs/bestofn_attack/proposal.md` | in progress |
| **E** | Blind Judges | Do safety **judges** share the defenses' *decode blind spot*? First per-judge × per-encoding × human-labeled miss/over-count calibration on encoded / image-rendered harm, + a decode-then-judge fix — the measurement mirror of Paper C | `judge_reliability` | `text_docs/judge_reliability/proposal.md` | founding (S3 → S4 scoop gate) |

**Namespacing convention.** Each paper owns a subdir keyed by its **Namespace** above under `text_docs/`,
`conf/experiment/`, and `outputs/`; `shared/` holds cross-paper material (venue facts, judge validation,
literature, this index). Aliases (A/B/C/D/E) are the stable shorthand; codenames are the paper-facing titles.
When a new paper starts, add its row here and create its namespace subdirs.

**Note — the `bestofn_defense` namespace is NOT a separate paper.** It holds Paper D's *supportive*
canonicalize→guard defense sub-part — pivoted 2026-07-17 from a standalone paper into a section of the
attack-primary Paper D (`bestofn_attack`). Any older doc calling `bestofn_defense` "Paper D" or "Paper E"
is stale drift; the live aliases are the table above.
