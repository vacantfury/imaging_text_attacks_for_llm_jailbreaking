# AS-4 — AAAI-27 AI Alignment special track — submission package manifest

> ✅ **SUBMITTED 2026-08-22 (owner press), AAAI-27 AI Alignment special track,
> OpenReview submission #205.** Filed inside the wall (22 Aug 2026 04:59 PDT /
> 11:59 UTC). The four artifacts below were re-hashed immediately before the
> press and all four matched this manifest, so what was uploaded is exactly what
> is recorded here.
>
> Filed complete: main-track withdrawal, the updated title/abstract, all four
> uploads including the reproducibility checklist. Nothing about this filing is
> outstanding.

Built 2026-08-22, after the main/supplementary split. This file is the package's
identity: the submit step uploads exactly these files, and **any edit to a listed
file invalidates this manifest** — rebuild that artifact, re-hash, then re-check.

*(`manifest-as2.md` is AS-2's package and `manifest.md` is AS-7's. Three different
papers. Do not cross-read them.)*

## The upload set

| File | Channel | Size | SHA-256 |
|---|---|---|---|
| `aaai_aia_latex/paper.pdf` | Main submission PDF | 324 KB | `30074bea0a30972a5fc285d0f7020dc6e58eb0dfbd943442e2e8d7d76c79e7fb` |
| `aaai_aia_latex/supplementary.pdf` | Supplementary Document | 456 KB | `7f865de5eb72407b7630657a3594dd835b7d6705d3d8be1adfc378e6b5d4140a` |
| `supplementary_code_and_data.zip` | Code and Data Supplement | 9.3 MB | `259d522ac78451e162004eceb581793f5c558c6a44ff099396a3fc25ae25aa70` |
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
| **Whether the AIA OpenReview form has a checklist slot** | the live AIA form | ✅ **VERIFIED 2026-08-22 at the AS-4 press — the slot EXISTS and the checklist was uploaded.** Settled for the venue; build and upload one for any AIA filing. Do not re-ask. ⚠️ This row should never have read UNVERIFIED: `manifest-as2.md` in this same directory already recorded the checklist as REQUIRED with a designated form field, quoted from the live AAAI-27 submission instructions, on this same day. Read the sibling manifests before flagging a venue fact as unknown. |
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
- Code artifact: 456 files, 103 strings scrubbed, `verify_tree` anonymization
  **PASSED**, 498 entries in the zip.
- Three **pre-existing** uncited floats in the appendix (`tab:main`,
  `tab:app-band`, `tab:app-ci`) were found by the new float sweep and fixed.
  Uncited floats raise no LaTeX warning, which is this repo's known silent-defect
  class.

## Cross-family review (the `paper-check` second opinion)

Run against **Gemini 3.1 Pro** via `llm_utils`, a third model family: I am Claude,
and the six prior cspaper rounds were GPT-family. The prompt gave it the **main
paper only** and asked one question the venue rule makes decisive: judge
self-containment as a reviewer who never opens the supplement. Four passes, ~$0.06
each. It found real defects that nothing else did, and the fixes are in:

1. **I had over-moved.** The temperature panel left while its prose still referred
   to "panels" and "columns" that were no longer there, so the paper's third claim
   had no table. **Table 2 is back in the main paper**; the budget-curve figure went
   to the supplement in its place. First pass: "broken references: several". Second
   pass onward: **"None found."**
2. **An orphaned headline number.** The abstract and introduction compared SAGE's
   $99.8\%$ per-draw block rate against "a classifier gate blocking $95.6\%$", and
   $95.6$ appeared *nowhere else in the paper or the working notes*. Traced to the
   Gemma round: SAGE blocks $99.8\%$ and loses **12** behaviors, the gate blocks
   $95.6\%$ and loses **10** — same target, same round, both rows now visible in
   Table 2. The claim is true and is now anchored where it is made.
3. **A stale pre-fix number and a round mix-up.** The borrowed-strength sequences
   spliced main-matrix values with the temperature panel and carried the 70B at its
   **pre-correction** $22$ where Table 2 reads $25$. Both values are real, from
   different rounds. The paragraph now reads one panel, and the paper states the
   convention once, in Setup: *every contrast is read inside one panel, against that
   panel's own control*. That single sentence retired three separate
   "contradictions" the reviewer had raised across passes — all of them the reader
   dividing one panel's number by another panel's baseline.
4. **A broken cross-reference** (`Sections 5 and 5`: two subsections that render
   identically under `secnumdepth 1`), **a labelling promise the tables did not
   keep** (Setup promises pre-correction cells are labelled "CodeAttack variant";
   the captions now say so), and **the wrapper variants were never defined** in the
   main text (\textsc{verdict-only} and \textsc{+verdict} are now named where used).

**Where it still objects, and why we are not acting on it.** Its final pass says the
paper "functions as an extended abstract for the supplementary material" because the
supporting experiments — the wrapper intervention, the paraphrase control, the
SemanticSmooth and gate re-runs — state their outcome in prose while their tables
sit in the supplement. That is the division the venue rule prescribes: those are
*check*-material for claims the paper already states with its numbers, and the
alternative is not fitting them in the main submission. The judgement to accept here
is deliberate and recorded, not an oversight.

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
