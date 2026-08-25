# AS-4 — AAAI-27 AI Alignment special track — submission package manifest

> 📁 **Paths moved 2026-08-22 (the `paper/` three-folder refactor).** Every path in
> this file now reads `paper/my_papers/as-4/...`; the source tree is otherwise
> untouched. ⚠️ `aaai_aia_latex/paper.pdf` and `supplementary.pdf` were REBUILT
> after the move, so their local bytes no longer match the SHA-256s in the table
> below. **The uploaded files are unchanged** — nothing was re-submitted. The
> rebuild changed only the file path pdflatex embeds; `paper.tex` has not been
> edited since before the press (mtime 2026-08-22 04:24, press ~04:5x). Treat the
> hashes below as the identity of what was UPLOADED, not of what is on disk.

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

Source tree: `paper/my_papers/as-4/aaai_2027_ai_alignment/`. Repo HEAD at packaging:
`141f66b`. ⚠️ `paper/` is gitignored, so the repo hash does **not** cover the
paper source. Its revision history is the `*.pre-*` backups beside it;
`paper.tex.pre-aia-split` and `supplementary.tex.pre-aia-split` are the last
pre-split states.

Rebuild everything with:

```
./paper/my_papers/as-4/aaai_2027_ai_alignment/aaai_aia_latex/build.sh   # both PDFs + package checks
uv run python -m src.analysis.as4_judgments_release emit      # the judgment layer
uv run python -m src.analysis.as4_judgments_release verify    # + legacy crosscheck
uv run python scripts/build_code_artifact.py --paper as4      # the code zip
```

⚠️ Use `--paper as4`. The older `--paper paperd` profile is the **legacy
main-track** package and still points at the pre-2026-08-08 path
`paper/my_papers/as-4/_legacy_aaai_main_track/`. It is kept so that package stays
rebuildable; it is not the AIA one.

## Packaging profile relied on

| Fact | Source | Verified |
|---|---|---|
| Channel names ("Supplementary Document", "Code and Data Supplement") | AAAI-27 submission instructions | 2026-08-21, cached in science `venues/aaai27_venue_info.md` |
| Appendix has no in-PDF home; it goes to the Supplementary Document | AIA call + main-track instructions | 2026-08-21, cached |
| Main submission must be self-contained; reviewers are not obliged to consult supplementary | same | 2026-08-21, cached |
| Reproducibility checklist is allowed beyond the main PDF | AAAI-27 Format section | 2026-08-21, cached |
| No repo link in the PDF (AAAI bans anonymous-repo links; code ships as the zip) | project policy + venue record | swept 2026-08-22: 0 URLs in either document |
| **Whether the AIA OpenReview form has a checklist slot** | the live AIA form | ✅ **VERIFIED — but the two forms differ, and an earlier note here conflated them.** The MAIN SUBMISSION form has a checklist field (used at the press). The **Edit Supplementary Materials** form does NOT: read directly off the captured form image 2026-08-23, its fields are TL;DR, Primary Topic, Secondary Topics, Country of Institutions, Technical Supplement, Media Supplement, Code and Data Supplement, Serve As Reviewer, Any Qualified Reviewer, and three policy checkboxes. So the checklist cannot be re-uploaded through the supplementary form. Settled for the venue; build and upload one for any AIA filing. Do not re-ask. ⚠️ This row should never have read UNVERIFIED: `manifest-as2.md` in this same directory already recorded the checklist as REQUIRED with a designated form field, quoted from the live AAAI-27 submission instructions, on this same day. Read the sibling manifests before flagging a venue fact as unknown. |
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

## Post-submission refinement, 2026-08-22 (supplement + code only)

The main paper is SUBMITTED and FROZEN. Everything below concerns entries on #205
that are still editable before the supplementary wall.

**Re-upload these two. Leave the main paper alone.**

| File | Channel | Size | SHA-256 (16) | Action |
|---|---|---|---|---|
| `aaai_aia_latex/supplementary.pdf` | Technical Supplement | 418 KB | `970105234f055308` | **RE-UPLOAD** |
| `supplementary_code_and_data.zip` | Code and Data Supplement | 9.3 MB | `dcc1b0e28560f26f` | **RE-UPLOAD** |
| `aaai_aia_latex/paper.pdf` | Main submission | 299 KB | `59ecbf3b09c77bf0` | do NOT re-upload; frozen, content unchanged since the press, bytes differ only from rebuilds |
| `ReproducibilityChecklist.pdf` | checklist | 76 KB | `2736ba210a8d0f1b` | unchanged |

Both re-uploads fit their caps (Technical Supplement 10 MB; Code and Data 50 MB),
read off the live form. Code artifact rebuild: 456 files, 138 identifying strings
scrubbed, **anonymization verify PASSED**.

**What changed in the supplement.** A new subsection and table, `tab:blockrate`, in
*The Temperature Panel*. The main paper says SAGE "blocks" 99.8% of draws against a
gate "blocking" 95.6%, and cites Table 2, which contains no block rates. Recomputed
from the two pinned cells (10,000 draws each): both figures are per-draw
NON-SUCCESS, `100 - ASR`. SAGE's actual canned-block rate is 0.00%, because a
transform defense has no block string and every refusal in its cell is the target's
own; the gate's actual block rate is 92.54%, not 95.6%. The comparison the main
paper draws is still sound, since both are the same quantity measured the same way,
and the ordering is unaffected. Only the verb is wrong, and the supplement now
carries the precise definition and the decomposition where a reviewer will look.

**What changed in the code.** `paper_d_claim_check` previously hardcoded
`GEMMA_BLOCK = {"sage": 99.8, "guard": 95.6}`, so it verified the abstract against a
constant typed into itself. It now recomputes both rates from the stored draws,
fails on a mismatch or on SAGE ever reporting a nonzero canned block, and reports
`not-run` where the outputs are absent rather than passing silently.

**Also.** `build.sh` counted `Overfull \hbox` only; it now sizes hbox and vbox and
gates on anything over 5pt. That exposed a 34.62646pt vbox overfull on the
supplement's first page, pre-existing and content-invariant, now baselined by exact
value so any different or additional overfull still fails.

⚠️ Still open on #205, not done: the TL;DR field was registered under the paper's
OLD spine and no longer matches the submitted title; `+62.3` still has no supplement
home; and Serve As Reviewer carries the same desk-reject exposure the form states.

## Supplement pass 2 — 2026-08-23 (main paper still frozen and untouched)

**Re-upload the supplement. `supplementary.pdf` = `298938894a3692b6`, 429 KB.**
The code zip is unchanged (`dcc1b0e28560f26f`); no `src/` file changed in this pass.
`paper.pdf` was never rebuilt: `59ecbf3b09c77bf0` before and after.

### New protection: the frozen cross-reference contract

`build.sh` rebuilds BOTH documents, which regenerates the submitted `paper.pdf` for
no reason. Three files now prevent that and the silent-rename hazard:

- `FROZEN_XREFS.txt` — the 12 supplement section names the submitted paper cites
  BY NAME. The two documents compile separately, so renaming one of these breaks a
  pointer in a PDF we can no longer fix, with no warning from LaTeX anywhere.
- `check_supp.py` — verifies all 12 resolve, catches duplicate section titles, and
  pins `paper.tex` by CONTENT HASH (`e160328daa220697`) rather than mtime, so a
  copy or an rsync does not raise a false alarm and a real edit cannot slip through.
  Both breach kinds were negative-control tested.
- `build_supp.sh` — builds the supplement ONLY, refuses to run on a broken
  contract, and fails if `paper.pdf`'s hash changes.

⚠️ These three live under `paper/`, which is gitignored, so they are the ONLY copy.

### What the pass found and fixed

**Coverage.** Every value quoted in the main paper's prose was tested for a home in
the supplement. Before: 4 of 120 had none. After: **0 of 120**. Added, all derived
from values the frozen paper already prints, none a new measurement:

- `tab:amplification` — the eight donation ratios (4.2/3.2/6.8/1.9 against
  1.8/-0.2/0.7/0.1). These had NO home; the apparent matches for 3.2 and 1.9 were
  coincidental hits on unrelated ASR values in the results matrix. Each is a
  defense's Net divided by that target's own control drop, and all eight reproduce
  from the main paper's temperature table.
- Budget Curves now states the matched-budget split explicitly: 4.7 to 67.0 is
  +62.3 on the code arm against +3.0 on the character arm.
- Uncertainty now carries the encoding-correction evidence: 67 pre-correction
  against 61 (`r11_codefix`) and 59 (`r17`) post-correction, and notes the
  correction moves the number DOWNWARD, so the reported effect is if anything
  conservative.

**A promise the supplement was not keeping.** The frozen paper says *"Full per-cell
configurations, templates and prompts are in the supplement (Attack and Defense
Configurations)"*. The supplement's own caption dropped the "in the supplement"
half and deferred entirely to the code, and contained ZERO prompt text. Reviewers
are not obliged to open a code archive any more than a supplement. New
`Templates, verbatim` subsection now prints the CodeAttack scaffold (including the
one-token `appendleft` difference that identifies pre-correction cells), the
published SAGE wrapper, and both wrapper variants.

**A table missing a row it was captioned for.** `tab:wrapper` printed three targets
while its own caption said "12 cells", which is four targets times three columns.
The main paper claims `8/8` cells at `+2` to `+64` behaviors; the six printed cells
give only +14 to +64. The Llama-3.3-70B cells exist. No validated builder pins this
table, and its `published` cells range 0 to 45 across campaigns, so the baseline was
resolved by consistency instead: `published=26` is the ONLY value that makes the
frozen paper's own stated range reproduce exactly (+2 to +64); the campaign-matched
alternative 21 gives +7 to +64 and does not. Row added as 26 / 28 / 52.

### Open, deliberately not done

- The full results matrix does not carry per-draw rates or QtFS for the factorial
  cells. Those cells are in the main paper's own table and in the released
  judgments, so this is detail rather than a coverage gap, and adding unvalidated
  rows to a submission document is the larger risk.
- `tab:wrapper` still has no validated builder. It is the one paper table resolved
  by consistency rather than by a pinned campaign. Worth a builder before any
  future venue.
- Page-1 vbox overfull, now 18.6pt, baselined in `build_supp.sh`. An earlier note
  calling it content-invariant was FALSIFIED and is corrected in both build scripts.

## Reproducibility checklist audit — 2026-08-23

Built from AAAI's own template (`AuthorKit27/ReproducibilityChecklist.tex`), verified
structurally identical: same 4 sections, same 31 questions, same macros. Compiles
clean, 2 pages, and a rendered-PDF sweep finds 0 identifying strings.

All 31 answers were audited against the actual paper rather than accepted as
written. Twenty-nine were already correct. **Two were overclaims, and both were
fixed on the editable side rather than by downgrading the answer:**

- **Q13** ("a motivation is given for why the experiments are conducted on the
  selected datasets") answered *yes*, but the paper only NAMED HarmBench, it never
  said why. The supplement's Reproducibility section now gives three reasons
  specific to a best-of-N study: completion-style behaviors a judge can rule on,
  the rubric our judge applies unmodified, and a scale that lets every cell afford
  100 draws under a fixed budget.
- **Q15** ("novel datasets will be made publicly available ... with a license that
  allows free usage for research purposes") answered *yes*, but there was NO
  license anywhere: not in the paper, not in the supplement, not in the zip. The
  single "licen" hit in the supplement was a false positive ("a methodological
  observation, not a license"). The artifact now ships a `LICENSE` (MIT for code,
  CC BY 4.0 for the judgment release, benchmark content explicitly NOT relicensed),
  the supplement states it, and the copyright line is anonymous for review.
  `build_code_artifact.py` copies `LICENSE` when a profile stages one and skips it
  otherwise, so the other papers' profiles are unaffected.

Answers deliberately left as `partial` because `partial` is the honest answer:
Q20 (hyperparameter ranges tried), Q25 (seed method), Q26 (infrastructure — vLLM,
precision and single-card are stated; GPU model, memory, OS and library versions
are not). Q4 `no` (no theoretical contributions) with Q5–Q11 `NA` is consistent.
Q14 `yes` rests on the per-draw judgment release being the paper's novel dataset,
which does ship in the Code and Data Supplement.

## Upload set as of 2026-08-23

| File | SHA-256 (16) | Size | Action |
|---|---|---|---|
| `aaai_aia_latex/paper.pdf` | `59ecbf3b09c77bf0` | 299 KB | FROZEN, never re-upload |
| `aaai_aia_latex/supplementary.pdf` | `1b39340edd7ddcf6` | 430 KB | **re-upload** |
| `supplementary_code_and_data.zip` | `d9e6567a12d5ab8d` | 9.3 MB | **re-upload** (now carries LICENSE) |
| `ReproducibilityChecklist.pdf` | `f902fee9d9ebf411` | 76 KB | no slot on the supplementary form |
