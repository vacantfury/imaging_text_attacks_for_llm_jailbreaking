# AS-7 — AAAI-27 AI Alignment special track — submission package manifest

Built by the `package-submission` skill, 2026-08-21. This file is the package's
identity: `paper-check` FINAL's staleness key covers every file listed here, and
the submit step uploads exactly these files. **Any edit to a listed file
invalidates this manifest** — repackage that artifact, then delta re-check.

## The upload set

| File | Channel | Size | SHA-256 |
|---|---|---|---|
| `paper.pdf` | Main submission PDF | 0.47 MB | `82241cf6b9e0f1d39af7d0ec8cb70d2abf621e3c3ada2a9ad96dd139ac3f905c` |
| `supplementary.pdf` | Supplementary Document | 0.37 MB | `2a43281f7a359b4db7079f0023e0050b4f45088c15038190aa00559a8cb49d2e` |
| `supplementary_code_and_data.zip` | Code and Data Supplement | 1.68 MB | `237aa365bb7308713ff39173df7048fe9e8837163dc75e5be98064b56e1a9c2a` |

Source tree: `paper/as-7/aaai_2027_ai_alignment/`. Repo HEAD at packaging:
`ac8f9b0 (`paper/` is gitignored; this session's paper edits are not in it)`. ⚠️ `paper/` is gitignored, so the repo hash does **not** cover the
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

## Source-read audit of the narrative claims (2026-08-21, second pass)

The gated-mitigation read above found four numeric errors in ONE Introduction
sentence, none of which any guard covered. That is a defect *class*, not one
sentence, so every summary claim in the Abstract, Introduction, Discussion and
Conclusion was then read against its source table. Eight findings, all fixed:

| # | Finding | Severity |
|---|---|---|
| 1 | **The Experimental Setup section described a different paper.** It listed five API targets and three defenses. It omitted all three open-weight targets that carry the lead results (`qwen3-vl-8b-instruct`, `internvl3-8b`, `pixtral-12b`), all three guard classifiers, SemanticSmooth, the channel-routed panel, and both ORBench benign sets. Stale from before the read-access re-spine. | major |
| 2 | **Three central instruments were never cited.** WildGuard, Llama Guard and GuardReasoner-VL carry Tables 1-5 and appeared nowhere in the bibliography. SemanticSmooth and OR-Bench had entries in `paper.bib` that no `\cite` ever reached. | major |
| 3 | Conclusion scope claim "seven targets and two encodings"; the paper tests **eight** targets and **three** encodings. | real |
| 4 | `tab:bypass`-describing prose called the variant `ir_plain`, while the paragraph immediately below it insists the table is `ir_plain+text` and that the distinction "is not terminological". | real |
| 5 | Same sentence: "residual ASR $41$--$43\%$ on their worst cells". Both worst cells are $43$; the $41$ came from a non-worst cell. | real |
| 6 | `tab:channelasr` caption asserted block counts are "target-independent by construction" while its own table shows `guardreasoner-vl` at $99$ and $98$ on the two targets. It is a *generative* guard, so sampling, not the target, explains the one-prompt difference. Caption now says so. | real |
| 7 | One Introduction sentence spliced numbers from two different grids (`tab:benefit`, open-weight, and `tab:deployable`, API) without naming either, so a reviewer looking for $-63$ in the table supplying $-38/-24/-24$ would not find it. Both grids now named. | clarity |
| 8 | "every cell $p<10^{-10}$" appeared twice in prose, but the tables' own legend only marks $p<10^{-4}$. **The claim is true**: recomputed by exact McNemar from the stored per-prompt outcomes, the four cells are $2.8\times10^{-17}$, $7.5\times10^{-11}$, $3.5\times10^{-18}$, $1.8\times10^{-15}$. The exact bounds are now in the `tab:benefit` caption so the claim is checkable from the paper. | unsupported, now supported |

**What was checked and found correct** (recorded so a later session does not
redo it): every figure in the Abstract; the three-setting attribution itemize;
the channel block rates and their replication; the ARM-T/ARM-I attack-success
consequence on `pixtral-12b`; the discrimination table and its bootstrap
intervals; the router's four cells; the redundancy and stacking deltas; the
whole of `tab:benefit`, whose sixteen values and significance marks were
**recomputed from the per-prompt flags and match exactly**; the read-ladder
ranges; the within-defense stage isolation; the $74$--$100\%$ benign-refusal
bound; the SemanticSmooth $55$-to-$57$-point conclusion claim; and the gated
sentence repaired in the first pass.

**Two house sweeps, both clean on both documents**: no "pp" notation anywhere,
and the draft-history narration battery (the `paper_writing.md` handbook rule
seeded by this very paper) returns zero hits per fixed string.

## House dash-connector sweep (2026-08-21, third pass)

The owner's standing prose rule bans a dash line (em dash, `--`, `---`) used to
join two sentences or clauses, in papers as in every other text written for him
or on his behalf. Both documents are now clean: **192 sites in the main paper and
55 in the supplementary**, each read and rewritten individually as a period, a
comma, a colon, a semicolon, or a parenthetical, whichever the sentence wanted.
Twelve `\paragraph{Step N --- ...}` headings in the supplementary became
`Step N: ...`.

Not a blind substitution, and three classes were deliberately preserved:
`--` inside numeric ranges (`$41$--$43$`, an en dash, not a connector);
`---` as a "not applicable" cell marker in five results tables, where rewriting
it would have falsified a table; and dashes inside LaTeX comments, which reach
no reader. Two grammar slips were fixed in passing, "the $1$ points gap" and
"a $13$ points change", both now hyphenated singulars.

Verified after: both documents build 0/0/0/0, the full guard battery is green
(`as7_tables verify`, `as7_xdoc_numbers verify` plus its negative control,
`as7_may_cells` selftest), the "pp" and draft-history sweeps stay clean, and the
rendered PDF text was spot-read at the heaviest rewrite sites.

## Known risks

1. **The paper source has no version control.** `paper/` is gitignored, so
   `aaai_aia_latex/_backups/tex/` is the entire revision history of a 230 KB
   manuscript. A private engine repo or a local git repo under `paper/` would fix
   it. Not actioned: it is a structural decision for the owner.
2. **`build.sh` is load-bearing.** A bare `pdflatex paper.tex` on a clean tree
   produces 31 undefined references. Anyone rebuilding must use the script.
