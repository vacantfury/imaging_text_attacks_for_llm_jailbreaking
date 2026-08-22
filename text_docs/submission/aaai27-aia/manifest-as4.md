# AS-4 — AAAI-27 AI Alignment special track — submission package manifest

Built 2026-08-22, after the main/supplementary split. This file is the package's
identity: the submit step uploads exactly these files, and **any edit to a listed
file invalidates this manifest** — rebuild that artifact, re-hash, then re-check.

*(`manifest-as2.md` is AS-2's package and `manifest.md` is AS-7's. Three different
papers. Do not cross-read them.)*

## The upload set

| File | Channel | Size | SHA-256 |
|---|---|---|---|
| `aaai_aia_latex/paper.pdf` | Main submission PDF | 324 KB | `49858e7e0a9b968949087522b948ec2b5313ccbd2777f39ed2f5ffac6e947386` |
| `aaai_aia_latex/supplementary.pdf` | Supplementary Document | 456 KB | `76ad79ce4a5fb8dcba6a1cf34ab81ede089f4fe85ceb743a4f55e38c9ff0b9b9` |
| `supplementary_code_and_data.zip` | Code and Data Supplement | 9.3 MB | `ba3cf4238288e19a7435dd126292e6f19c3c988e5b816c52aa8bb064532613d4` |
| `ReproducibilityChecklist/ReproducibilityChecklist.pdf` | Reproducibility checklist | 132 KB | `2736ba210a8d0f1b656193685d94b7238f34d172bf1a998f4a84597021d86c91` |

Source tree: `paper/as-4/aaai_2027_ai_alignment/`. Repo HEAD at packaging:
`141f66b`. ⚠️ `paper/` is gitignored, so the repo hash does **not** cover the
paper source. Its revision history is the `*.pre-*` backups beside it;
`paper.tex.pre-aia-split` and `supplementary.tex.pre-aia-split` are the last
pre-split states.

Rebuild everything with:

```
./paper/as-4/aaai_2027_ai_alignment/aaai_aia_latex/build.sh   # both PDFs + package checks
uv run python -m src.analysis.as4_judgments_release emit      # the judgment layer
uv run python -m src.analysis.as4_judgments_release verify    # + legacy crosscheck
uv run python scripts/build_code_artifact.py --paper as4      # the code zip
```

⚠️ Use `--paper as4`. The older `--paper paperd` profile is the **legacy
main-track** package and still points at the pre-2026-08-08 path
`paper/bestofn_attack/aaai_2027_main/`. It is kept so that package stays
rebuildable; it is not the AIA one.

## Packaging profile relied on

| Fact | Source | Verified |
|---|---|---|
| Channel names ("Supplementary Document", "Code and Data Supplement") | AAAI-27 submission instructions | 2026-08-21, cached in science `venues/aaai27_venue_info.md` |
| Appendix has no in-PDF home; it goes to the Supplementary Document | AIA call + main-track instructions | 2026-08-21, cached |
| Main submission must be self-contained; reviewers are not obliged to consult supplementary | same | 2026-08-21, cached |
| Reproducibility checklist is allowed beyond the main PDF | AAAI-27 Format section | 2026-08-21, cached |
| No repo link in the PDF (AAAI bans anonymous-repo links; code ships as the zip) | project policy + venue record | swept 2026-08-22: 0 URLs in either document |
| **Whether the AIA OpenReview form has a checklist slot** | not established | ⚠️ **UNVERIFIED.** The checklist is built and ready either way; AS-2's package does not carry one. Walk the form at submit time and upload it if there is a slot. |
| **Supplementary file-size cap** | not stated on the instructions page | ⚠️ **UNVERIFIED**, same as AS-2's manifest records. 9.3 MB is small enough that this is unlikely to bind. |

## What the split changed

`paper.tex` became the main submission alone; `appendix.tex` was renamed
`supplementary.tex`. **The rule that decided what moved was the AAAI
self-containment clause, not length** — anything a reviewer needs to *accept* a
claim stayed, and only material consulted to *check* an already-stated claim
moved, so every number a claim rests on is still printed in the main paper, in
prose where its table moved.

- Stayed: the composition table and the factorial table, one evidence table per
  primary claim.
- Moved, each into a supplement section the main paper names: the budget curves,
  the temperature panel, the wrapper intervention, the self-check family, the
  gate panel with the inversion figure, and the configuration table.
- `tab:paraphrase` was dropped rather than moved: the supplement's *Probe Count*
  already carried a superset of it.

⚠️ **Pointer hazard.** The two documents compile **separately** and the main paper
cites supplement sections **by name, never by `\ref`**. Renaming a `\section` in
`supplementary.tex` breaks a pointer with no warning anywhere. `build.sh` checks
all of them (10 distinct, all resolving) along with orphan floats, dangling refs,
duplicate labels and overfull boxes.

## Two defects found while packaging, both fixed

1. **The cell census was wrong and self-contradicting.** The main paper said
   "92 cells and 670,000 judged generations" while the supplement said 67 cells
   and the same 670,000; 92 × 10,000 ≠ 670,000, and `tab:config`'s own seed split
   (43 + 24) reads 67. A previous session had flagged the 92 in `paper.tex`'s
   header as an unverified reconstruction. Neither total survives inspection —
   the panels **overlap**, so summing them double-counts. Both totals are gone.
   The main paper now states only what is uniform and checkable (every reported
   cell is 100 behaviors × 100 draws), the supplement gives per-panel counts and
   says explicitly why it prints no grand total, and the released judgment index
   is the authoritative per-cell record.
2. **The artifact statement over-claimed.** The supplement promised per-draw
   judgments "for all 67 cells"; the release directory held 31. AS-4 had no
   emitter in the repo at all — the release was written by something that no
   longer exists. Fixed by writing one (below) and by stating the layer's
   coverage precisely instead of in the round.

## The judgment layer

`src/analysis/as4_judgments_release.py` (new; AS-2 and AS-7 have had one for
months). Cell selection is never ad hoc: it comes from the paper's own validated
builders. Two labelled layers, different guarantees, both in the index:

- `builder_pinned/` — **66 cells, 660,000 draws**, each verified at release time
  to reproduce the metric its own `results.json` recorded. Refuses to write on a
  mismatch. The two `status=partial_judge` factorial cells have no stored metric
  (a missing summary block, not missing judgments) and are checked against the
  coverage `paper_d_factorial_ci` publishes and gates on.
- `p2_matrix/` — **31 cells, 310,000 draws** from the original cluster-side round.
  Their source directories no longer exist locally *or on any cluster* (checked
  2026-08-22: explorer holds 2, xc holds 0), so these files are the only surviving
  per-draw record and are kept. They are checked against the values the paper
  publishes: **9 of 9 reproduce exactly**, including the three headline cells.

The layers overlap on the main matrix. **Not in this layer:** the
wrapper-intervention panel, whose per-cell records ship with the code but whose
per-draw verdicts no validated module pins. The supplement says so rather than
implying full coverage.

⚠️ Packaging hazard hit and fixed en route: an unscoped file move swept 66
verified cells into the legacy directory and mislabelled them as unverifiable.
`_stage_legacy` is now pattern-scoped and idempotent.

## claim-integrity

`pass · host: local`. This repo had no claim guard, which the
model_internals_safety handoff of 2026-08-21 named as an open exposure. Written
this session: `src/analysis/paper_d_claim_check.py`, which recomputes every claim
the paper *derives* from its own published panels and then requires the result to
appear verbatim in the source. **All 7 derived claims pass**: the ordering margins
(34/81/74/27), the sampled- and fixed-verdict donation ratios
(4.2/3.2/6.8/1.9 against 1.8/−0.2/0.7/0.1), the ratio range (1.9 to 6.8), the
control-drop range (12–24), the matched-budget split (+3.0 vs +62.3), the
superadditivity multiples (9× / 12× / 75×) and the "inert on three of four
targets" count.

Independently, all three pre-existing validated builders reproduce their published
values: `paper_d_factorial_ci` (14 cells + 4 paired CIs), `paper_d_severity_ci`
(4 actionable counts), `paper_d_temperature_ci` ("all 18 published cells
reproduced exactly").

## State at packaging

| Check | Main | Supplementary |
|---|---|---|
| errors / undefined refs / undefined cites | 0 / 0 / 0 | 0 / 0 / 0 |
| overfull hboxes | 0 | 0 |
| orphan floats / dangling refs / duplicate labels | none | none |

- Main-paper structure: content ends within the main-content allowance, with the
  pages beyond it carrying references only.
- Anonymity, checked on the RENDERED PDFs rather than the source: `[submission]`
  option, `\author{Anonymous Submission}` (main) / `Anonymous submission`
  (supplementary), **0** web or repository pointers, **0** occurrences of any
  author/institution/account string, and no self-referential phrasing
  ("our previous work", "our companion paper"). The 13 "Zhang" hits a naive grep
  returns are all third-party citation authors. The owner's own published attack
  is not cited in this paper at all, so the third-person-citation hazard does not
  arise here.
- Code artifact: 455 files, 103 strings scrubbed, `verify_tree` anonymization
  **PASSED**, 498 entries in the zip.
- Three **pre-existing** uncited floats in the appendix (`tab:main`,
  `tab:app-band`, `tab:app-ci`) were found by the new float sweep and fixed.
  Uncited floats raise no LaTeX warning, which is this repo's known silent-defect
  class.

## Known residue, not blocking the package

- `tex_stat_audit` parses **0 rows** on this paper — it targets AS-2's
  paired-McNemar reporting format, which AS-4 does not use. That is a no-op, and
  it must not be reported as a pass.
- 53 dash-line sentence connectors (house rule), down from 156 pre-split as a side
  effect of the rewrite. The sweep is unrun here exactly as in AS-2's package:
  it is a mechanical edit with real risk, since some are legitimate parenthetical
  pairs. Owner's call.
- The wrapper-intervention per-draw layer is unreleased (above). Closing it needs
  a validated pin for those cells, which is a filed dev task, not a packaging step.
- The pre-fix encoding deviation is disclosed in the paper's Setup and remains an
  owner-ratified declared deviation (2026-08-10), not a defect.

## Not submitted

Nothing here has been uploaded. The submission press is the owner's.
