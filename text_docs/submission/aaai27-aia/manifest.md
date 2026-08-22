# AS-7 — AAAI-27 AI Alignment special track — submission package manifest

Built by the `package-submission` skill, 2026-08-21. This file is the package's
identity: `paper-check` FINAL's staleness key covers every file listed here, and
the submit step uploads exactly these files. **Any edit to a listed file
invalidates this manifest** — repackage that artifact, then delta re-check.

## The upload set

| File | Channel | Size | SHA-256 |
|---|---|---|---|
| `paper.pdf` | Main submission PDF | 0.47 MB | `01c426d245f62c76a37deeed60cd38bc0f471924c5fec4cf75fea02cd523ba8e` |
| `supplementary.pdf` | Supplementary Document | 0.37 MB | `3bde751916cc07be7ab40b89e8bde575daa949308bd59aa306774da499648afc` |
| `supplementary_code_and_data.zip` | Code and Data Supplement | 1.68 MB | `237aa365bb7308713ff39173df7048fe9e8837163dc75e5be98064b56e1a9c2a` |

Source tree: `paper/as-7/aaai_2027_ai_alignment/`. Repo HEAD at packaging:
`7a3ed1d27657b08f4a6dfdf50df632636eaf8447`. ⚠️ `paper/` is gitignored, so the repo hash does **not** cover the
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
- 🔴 **The detector-gated mitigation (`sec:res-gated` / `App. S6`) was read
  end to end against its source table on 2026-08-21, and the finding was not the
  placement.** The placement is already handled: the main paper carries an
  explicit paragraph, "Two mitigations we measured, and why they sit in the
  supplementary material", which justifies it on thesis grounds (these are
  efficacy questions, and the paper answers attribution) and discloses that these
  are the only two tables scored by the collection-era judge. What the read found
  instead was that **the Introduction's one-sentence summary of that table was
  wrong in four ways at once**, and that the main paper was asserting an efficacy
  recommendation its own scope paragraph says it does not make. Both fixed:

  | Introduction said | Source says | Fix |
  |---|---|---|
  | "returns benign cost to the **undefended** baseline" | the comparator is the **text** baseline (the text arm still runs the defense) | corrected |
  | "$0$ points inflation" | gated benign is 9/10, 4/5, 11/11 vs text, so $0$ to $1$ point | corrected |
  | "against $20$--$79$ **points** for unconditional attachment" | 20-79 is a benign refusal **rate**; the inflation is **+9 to +67 points** | corrected |
  | "detector recall ... $9$--$16\\%$" | **12-16%**, in both the source prose and its caption; the stray 9 appears to bleed from the neighbouring "+9 to +67" | corrected |

  The two overclaims were softened rather than deleted, so the paper keeps its
  closing move ("the open problem this work exposes is detection of encoded
  inputs, not decoy design") without asserting an efficacy result it elsewhere
  declines to make: "the mitigation we can actually recommend" became "a
  deployable variant we measured", and "buys safety in proportion to detector
  recall" became "recovers the safety gain only where the detector fires".

  **Guard added:** `src/analysis/as7_xdoc_numbers.py` catches the one member of
  that group that is mechanically checkable, a numeric range printed as a rate in
  one document and as a delta in the other. Its negative control re-injects the
  real defect and requires the guard to fail. It deliberately does NOT claim to
  cover the other three, where the numbers were present in the source and only
  their meaning was wrong; those are caught by reading the source table against
  the claim, which is a duty and not a script. A guard implying otherwise would
  be the "reads green over ground it never covered" defect this repo has already
  hit three times.

## Known risks

1. **The paper source has no version control.** `paper/` is gitignored, so
   `aaai_aia_latex/_backups/tex/` is the entire revision history of a 230 KB
   manuscript. A private engine repo or a local git repo under `paper/` would fix
   it. Not actioned: it is a structural decision for the owner.
2. **`build.sh` is load-bearing.** A bare `pdflatex paper.tex` on a clean tree
   produces 31 undefined references. Anyone rebuilding must use the script.
