# AS-7 — AAAI-27 AI Alignment special track — submission package manifest

Built by the `package-submission` skill, 2026-08-21. This file is the package's
identity: `paper-check` FINAL's staleness key covers every file listed here, and
the submit step uploads exactly these files. **Any edit to a listed file
invalidates this manifest** — repackage that artifact, then delta re-check.

## The upload set

| File | Channel | Size | SHA-256 |
|---|---|---|---|
| `paper.pdf` | Main submission PDF | 0.47 MB | `7bb78385660dbd297e2603ab9abd48b558767a6fb5d7409553d21791194cc1ba` |
| `supplementary.pdf` | Supplementary Document | 0.37 MB | `6fa57e34ecf3f18c80cc6da4f4c801e74f77f2c391d41ffd702c8569726fa3f2` |
| `supplementary_code_and_data.zip` | Code and Data Supplement | 1.68 MB | `540d763f1306f675ceccf32c14e952b4ca57a03fdf3e829e8655ad94612cb54e` |

Source tree: `paper/as-7/aaai_2027_ai_alignment/`. Repo HEAD at packaging:
`abce55784683fb87144b502fa0df62f0cfb0fca2`. ⚠️ `paper/` is gitignored, so the repo hash does **not** cover the
paper source. The `.tex` revision history lives only in
`aaai_aia_latex/_backups/tex/` (see the note in the risks section).

Rebuild everything with:

```
./paper/as-7/aaai_2027_ai_alignment/aaai_aia_latex/build.sh   # both PDFs
python scripts/build_code_artifact.py --paper as7             # the code zip
```

## Packaging profile relied on (all verified 2026-08-21, live)

| Fact | Source | Verbatim |
|---|---|---|
| Channel names | [AAAI-27 submission instructions](https://aaai.org/conference/aaai/aaai-27/submission-instructions/) | "Code and Data Supplement" and "Supplementary Document" |
| Appendix has no in-PDF home | [AIA call](https://aaai.org/conference/aaai/aaai-27/aia-call/) | "Submissions are limited to 7 pages of main content, with a maximum total length of 9 pages. Any pages beyond page 7 are reserved exclusively for references." |
| What may go to supplementary | submission instructions | "Additional technical material such as proofs, assumptions, and algorithm pseudocode, may be included in the Supplementary Document." |
| 🔴 The binding constraint | submission instructions / AIA call | "The main submission may reference the supplementary material, but it should be self-contained"; "reviewers are not obliged to consult the supplementary material"; AIA: "reviewers are not required to review this material." |
| AIA inherits main-track mechanics | AIA call | "Submissions to this special track will follow the regular AAAI technical paper submission procedure but the authors need to select the AI Alignment (AIA) special track." |
| No repo link in the PDF | project policy + venue record | AAAI bans anonymous-repo links; code ships as the zip. Source swept: the submission PDF carries no repository pointer. |

Cached copy of this profile: science `venues/aaai27_venue_info.md` §Packaging
profile (updated in the same act, with the previously-UNVERIFIED fields now
verified).

## What the split did

The appendix was cut out of the main PDF into a self-contained Supplementary
Document. Both documents cross-reference each other through the `xr` package, so
a pointer prints a real number (`App. S3`, `Fig. S1`) rather than a blind "see
the supplementary material". Supplementary sections, figures and tables all carry
an **S** prefix so that a reader holding both PDFs is never ambiguous about which
document a number belongs to.

Because the two documents reference each other, **build order matters** and
`build.sh` is the only supported entry point; it alternates passes until both
`.aux` files settle and then reports errors, undefined references, undefined
citations and overfull boxes parsed from captured STDOUT.

State at packaging: both documents build with **0 errors, 0 undefined
references, 0 undefined citations, 0 overfull boxes**. All four analysis drift
guards pass against the main paper alone, which is the check that no guarded
number silently moved out of the submission.

## Self-containment audit (the binding constraint above)

26 sentences in the main paper point into the supplementary. Each was read
individually against the rule "a reviewer must be able to ACCEPT every claim from
the main paper alone; the supplementary may only carry what they would consult to
CHECK a claim already stated and supported."

- **Satisfied (23).** Prompt templates, worked case studies, the decoy-diversity
  ablation, the full five-way outcome accounting, Wilson intervals, the
  reproducibility manifest, ECSO execution-path accounting. In every case the
  main paper states the claim with its numbers and the supplementary carries the
  detail. Judge robustness in particular is safe: `sec:res-judge` remains a
  main-body Results subsection carrying the substance, and `App. S9` is only its
  backing grid.
- **Satisfied, scoping only (2).** `sec:res-adaptive` is referenced from
  Limitations, where the paper narrows its own claims. Nothing is asserted on it.
- 🔴 **ONE GENUINE GAP — the detector-gated mitigation (`sec:res-gated` /
  `App. S6`).** The Introduction asserts it as a bound on reading the paper's
  numbers, and the Discussion closes on it ("the open problem this work exposes is
  detection of encoded inputs, not decoy design"). Both state the figures inline,
  so the claim is *stated* in the main paper, but its only evidence table now sits
  where a reviewer is not obliged to look, and it carries the paper's closing
  argument. **Recommended resolution: soften the main body's reliance rather than
  promote the table.** `tab:gated` is scored by `gpt-5-nano` while the rest of the
  paper is `gpt-5-mini` (TODO item 43, disclosed in the manifest section as an
  honest exclusion), so promoting a table that is explicitly not comparable to
  `tab:main` into the main body would trade one defect for a worse one. This is a
  drafting decision and is left open for the owner.

## Known risks

1. **The paper source has no version control.** `paper/` is gitignored, so
   `aaai_aia_latex/_backups/tex/` is the entire revision history of a 230 KB
   manuscript. A private engine repo or a local git repo under `paper/` would fix
   it. Not actioned: it is a structural decision for the owner.
2. **`build.sh` is load-bearing.** A bare `pdflatex paper.tex` on a clean tree
   produces 31 undefined references. Anyone rebuilding must use the script.
