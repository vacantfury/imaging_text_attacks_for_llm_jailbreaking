# AS-7 — AAAI-27 AI Alignment special track — submission package manifest

Built 2026-08-22, after the owner-ratified re-spine (lead with the SHARE) and the
main/supplementary split. This file is the package's identity: `paper-check`
FINAL's staleness key covers every file listed here, and the submit step uploads
exactly these four files. **Any edit to a listed file invalidates this manifest**
(note: the build embeds a timestamp, so a rebuild alone changes the PDF hashes
even with identical source; hash AFTER the last build, never before) —
repackage that artifact, then delta re-check.

*(`manifest-as2.md` and `manifest-as4.md` in this directory are different papers.
`manifest.md` is this paper's SUPERSEDED 2026-08-21 package, from before the
re-spine; it is kept for history and must not be used to submit.)*

## The upload set

| File | Channel | Size | SHA-256 |
|---|---|---|---|
| `paper.pdf` | Main submission PDF — **SUBMITTED, frozen** | 306 KB | `bc1250824ec1e77b0f876847401b844dc5aaea4851a57d6ab59baea54cc46fac` (bytes on disk; see the note below) |
| `supplementary.pdf` | Supplementary Document (Technical Supplement field, 10 MB cap) | 488 KB | `5d1061f80bbae343d50b45749de74c11cbe98b6d729f769f8d962582fa1c3ea6` |
| `supplementary_code_and_data.zip` | Code and Data Supplement (50 MB cap) | 6.7 MB | `e260aa6f3e092aec22d9f81df685fda67bb3f9291132f72c20faed745a518e33` |
| `ReproducibilityChecklist.pdf` | Reproducibility checklist — **re-verified and rebuilt 2026-08-24 on the owner's ask.** The instructions require it *"uploaded separately from the main paper in the designated field of the submission form"*, but the Edit Supplementary Materials form he screenshotted has no checklist field; it is ready if the field exists elsewhere on the submission page. | 76 KB | `691f980d514360d6a87064dccd828b173bc42c19dbb86bff5cc982601289543c` |

> ⚠️ **The main paper was SUBMITTED on 2026-08-22 and is frozen.** Two builds of it
> existed that day (before and after a prose-refinement pass), and which one was
> uploaded is not recorded here. It does not matter for the remaining uploads:
> the two builds are **structurally identical** — same section headings in the
> same order, same label set, so every section, table and appendix number the
> Supplementary Document points at resolves the same way under either. Only prose
> differs. Keep a copy of the uploaded PDF if you want a byte-exact record.
>
> **Everything else on the submission form is still editable and is what this
> manifest now tracks.**

Source tree: `paper/my_papers/as-7/aaai_2027_ai_alignment/`. Repo HEAD at packaging:
`948e9d6`. ⚠️ `paper/` is gitignored, so the repo hash does **not** cover the
paper source. Its revision history is the `paper.tex.pre-*` / `supplementary.tex.pre-*`
backups beside it: `.pre-respine` is the last pre-re-spine state, `.pre-condense`
the state before this session's main/supplementary split, and `.ok1`/`.ok2`/`.ok3`
are intermediate checkpoints.

Rebuild everything with:

```
./paper/my_papers/as-7/aaai_2027_ai_alignment/aaai_aia_latex/build.sh        # both PDFs
python scripts/build_code_artifact.py --paper as7                  # the code zip
cd paper/my_papers/as-7/aaai_2027_ai_alignment/ReproducibilityChecklist && \
  pdflatex -interaction=nonstopmode ReproducibilityChecklist.tex   # the checklist
```

## Packaging profile relied on

| Fact | Source | Verified |
|---|---|---|
| **7 pages of main content; pages 8–9 references only** — *"The main submission PDF can have up to 9 pages, with pages 8–9 reserved exclusively for references. That is, the main paper can have up to 7 pages of non-references content."* | [AAAI-27 submission instructions](https://aaai.org/conference/aaai/aaai-27/submission-instructions/) | 2026-08-22, live |
| **Ethics statement must sit in the 7 content pages** — *"Acknowledgements should be omitted from papers submitted for review, and any ethical statements or similar considerations, if included, must be included in the 7 content pages."* | same | 2026-08-22, live — ⚠️ AS-7's Ethics Statement was in the SUPPLEMENTARY until 2026-08-22; moved into the main content pages this session |
| **Reproducibility checklist is REQUIRED, uploaded separately** — *"Authors must complete the reproducibility checklist provided in the AAAI-27 Author Kit and submit it at the time of paper submission… must be uploaded separately from the main paper in the designated field."* | same | 2026-08-22, live — ⚠️ **missing from AS-7's package until 2026-08-22**; built this session from the Author Kit template, all applicable items answered against AS-7's own content |
| Channel names ("Supplementary Document", "Code and Data Supplement") | same | 2026-08-21, cached in science `venues/aaai27_venue_info.md` |
| **Main submission must be self-contained; reviewers are not obliged to consult supplementary** | [AIA call](https://aaai.org/conference/aaai/aaai-27/aia-call/) + main-track instructions | 2026-08-21, cached |
| AIA follows the regular technical-paper procedure, plus track selection | AIA call | 2026-08-21, cached |
| Supplementary size caps | the live OpenReview "Edit Supplementary Materials" form | **VERIFIED 2026-08-22**: Technical Supplement **10 MB**, Media Supplement **50 MB**, Code and Data Supplement **50 MB**. Ours: 0.49 MB and 7.01 MB. The same form states the repo-link ban in writing (*"linking to the paper sources/data in an external code/data repository is forbidden, including anonymized repositories like AnonymousGitHub and similar"*) and carries **no Reproducibility Checklist field**. |
| No repo link in the PDF | project policy (AAAI bans anonymous-repo links; code ships as the zip) | swept 2026-08-22: **0 hits** for `github`/`gitlab`/`anonymous.4open`/`zenodo`/`osf.io`/any URL in either document. The live instructions do not address repo links either way, so carrying none is the safe position under both readings. |

## What the split rule actually was

Not length. The binding rule is self-containment: **anything a reviewer needs in
order to ACCEPT a claim stays in the main paper; only material consulted to CHECK
an already-stated claim may move.** Every number a main-paper claim rests on is
printed in the main paper, in prose where its table moved.

**Main paper keeps 3 tables**: `tab:attribution` (the 0 / 41–45 / 99 headline),
`tab:channel` (the 100→0 / 81→0 channel collapse), `tab:readladder` (grant
inflation ordered by read position). These are the displays for contributions
(i), (ii) and (iii).

**Moved to the Supplementary Document** (App. "Main-paper detail moved out at
packaging", plus the pre-existing appendices): `tab:main` (full decoy grid),
`tab:discrim` (per-cell benign discrimination), `tab:deployable` (hosted-model
protocol grid), `tab:stage` (per-stage isolation), `fig:pareto` (both protocols
on shared axes), `tab:samewindow`, `tab:benefit`, `tab:stagewiring`, judge
robustness, the scope control, the multiplicity material, and the full-form
versions of five main-paper passages (evidentiary status, the measured null,
same-window re-collection, stage-isolation bounds, the black-box scope note,
the harness audit, extended positioning).

**Left the paper entirely, to AS-8**: the routed panel, stacking, coverage,
efficacy and the mitigations appendix. Preserved verbatim at
`paper/my_papers/as-8/inherited_from_as7.tex` — **not recoverable from git history**,
because `paper/` is gitignored and nothing under it has ever been tracked.

## Verification run on this package

| Check | Result |
|---|---|
| `build.sh` both documents | `errors=0 undef_ref=0 undef_cite=0 overfull=0` on main and supplementary |
| Page structure | main `paper.pdf` = 9 pages: **content ends on page 7**, References occupy pages 8–9 starting at the top of page 8 |
| Label-set integrity (the float-loss guard) | no label lost from either document across the whole condense pass |
| Citation-set integrity | no citation lost; the only citations that left (`chi2024llamaguard3vision`, `verma-etal-2025-multiguard`) went with the AS-8 material by design |
| Number drift guard (`as7_tables verify --supp`) | `verify OK` — every measured ASR and block rate in the pinned numbers file appears in `paper.tex`, with 10 values DEMOTED to the supplementary and **0 DRIFT** |
| Dash-connector rule | 0 em-dash clause connectors in either document (remaining `--` are compound words and numeric ranges) |
| Code-zip anonymity | builder's own verify PASSED (169 scrubs); independent sweep of all 622 files for handle/name/affiliation → 1 hit, `"Northeastern Somalia"` inside a HarmBench benchmark prompt, a false positive |
| PDF text anonymity | 0 hits in all three PDFs for name/handle/affiliation/acknowledgements |
| PDF metadata | `Creator: TeX`, `Producer: pdfTeX-1.40.27`; no Author/Title/Subject/Keywords fields |

## Two content defects found and fixed while packaging

Both were stale supplementary text left behind by the re-spine, and both would
have been visible to a reviewer:

1. **The supplementary asserted the paper's own §4.5 result did not exist.** A
   passage read *"What we have not isolated is stage attribution within the fired
   path… that requires stage ablations… which are new runs we have not executed;
   until then, stage-level attribution remains hypothesis."* Those runs exist and
   are §4.5 / `tab:stage`. Replaced with the actual finding.
2. **The Ethics Statement described a mechanism the paper no longer proposes**
   (the channel-routed panel, now AS-8) and sat in the wrong document. Rewritten
   for a measurement paper and moved into the main content pages, where the
   venue requires it.

Also corrected: the extended-limitations coverage note still cited the
detector-gated and adaptive-attack evaluations, both of which left for AS-8.

## Still open before the press

- **Read the OpenReview form** for supplementary format/size caps and any other
  required fields, and confirm the AIA track is selected.
- **`paper-check` FINAL** has not been run on this upload set.
- The submission itself is the owner's press. Nothing here submits anything.

## Supplementary Document refinement pass, 2026-08-22 (after the main paper was submitted)

The main paper being frozen, every fix below landed on the supplementary side.

| Defect | Fix |
|---|---|
| 🔴 **The Supplementary Document carried the OLD PRE-RE-SPINE TITLE** ("Who Controls What a Guardrail Reads? The Attacker Chooses the Channel, the Evaluator Chooses the Prompt"). A reviewer opening it saw a different paper name than the submission. The title is hardcoded in `supplementary.tex` and the re-spine only changed `paper.tex`'s `\title{}`. | Synced to the submitted title verbatim. |
| 🔴 **`\tableofcontents` printed a bare "Contents" heading with nothing under it.** `aaai2027.sty` line 92 does `\def\addcontentsline#1#2#3{}`, so a ToC can never populate under this style. Restoring the standard definition worked but overflowed `article`'s ToC number boxes with our `S16.1` numbering (14 overfull boxes), i.e. it required altering venue style machinery for a convenience. | Removed the dead ToC; replaced with a one-paragraph section guide that costs the style nothing. |
| 🔴 **`sec:res-rootcause` was defined in BOTH documents** (a block moved at the split carried the main paper's `\label` with it). Under `xr` a duplicated label makes a cross-document `\ref` silently resolve to the local copy. Harmless today (nothing in the supplementary referenced it) but latent. | Dropped the stray label. **`build.sh` now counts `dup_label` and fails on it** — it previously checked only errors/undef refs/undef cites/overfull. |
| **A whole subsection was duplicated** at 0.84 word-set similarity: the Discussion's guardrail-reconnaissance-and-stated-convention passage had been moved twice, into both `app:movedout` and `app:positioning`. | Deleted the `app:movedout` copy; left a one-line pointer so the frozen paper's dual citation still lands. |
| **An empty subsection** ("Harness audit (full form)", heading with no body) sat above a subsection that reused the frozen main paper's own §4.6 title. | Merged into one subsection, "The released-code audit, in full". |
| **`app:movedout` was titled "Main-paper detail moved out at packaging"** — our internal process, meaningless to a reviewer — and its subsections were all named "(full form)". It is the most-cited appendix (7 pointers from the frozen paper). | Retitled to "Supporting detail for the main paper's results"; all subsections given content titles. Label kept, since the frozen paper points at it. |
| **The provenance, campaign-variation, replicate and multiplicity material** that the frozen §4.8 explicitly sends readers to `app:scope` for was buried at `\paragraph` depth inside one 10.7k-character subsection. | Promoted "Campaign-level variation", "A designed replicate of the protocol grid" and "Multiplicity accounting" to subsections. |
| Two further subsections **cloned the frozen main paper's own section titles**. | Retitled so the two documents' headings are distinguishable. |

**Verified after the pass:** both documents `errors=0 undef_ref=0 undef_cite=0 overfull=0 dup_label=0` · no label or citation lost against the pre-pass supplementary · every one of the supplementary's 13 cross-references into the main paper resolves · drift guard `verify OK`, 10 demoted, 0 drift · 0 dash-connector hits · 0 identity hits and no Author/Title metadata in the supplementary PDF · stale-content sweep for AS-8 material, old-spine vocabulary and unrun-work claims returns 0 · **the replicate sentence added to the main paper during the refine pass is supported in App. S16** ("median absolute change across the twelve pairs is 3 points").

**Both uploads sit well inside the form's caps** (verified off the live OpenReview form): Technical Supplement 0.49 MB / 10 MB, Code and Data Supplement 7.01 MB / 50 MB.


## Second supplementary pass, 2026-08-24 — read against the SUBMITTED main PDF

The first pass read the supplementary against `supplementary.tex`. This one read
it against what the frozen `paper.pdf` actually **prints**, which is the only
thing a reviewer holds. Every appendix and float number the submitted PDF names
was extracted with `pdftotext -layout` and pinned; each fix below had to hold
them.

**The one broken pointer.** The submitted paper says the complete
5 model × 2 attack × 3 defense grid is *"in the supplementary material
(App. S15, Table S19)"*. Table S19 existed and carried the right number, but it
sat in **App. S18**, a section no pointer in the paper reaches at all. A reviewer
following that sentence landed in the wrong appendix.

| Defect | Fix |
|---|---|
| 🔴 **Table S19 (the complete amplification grid) was in App. S18, not the App. S15 the submitted paper names.** | Moved the grid and its significance paragraph into App. S15, placed after Table S18 so it still numbers **S19** — anywhere else renumbers a pointer already printed in the submitted PDF. App. S15's opening now leads with it. |
| 🔴 **App. S18 was an unreachable leftover bin** (significance testing, duplicating App. S7, plus the channel replication), reached by no pointer from the paper. | Now one topic: "Channel replication, and what the coverage gap costs". App. S14's channel subsection points into it, so a reader following the channel thread arrives. |
| **App. S16 was titled "Judge robustness, collection provenance, and multiplicity"**, leading with the one thing the paper does *not* send readers there for (§4.8 sends them for provenance, the replicate and multiplicity; judge questions go to App. S8). Its first subsection restated App. S8. | Retitled "Collection provenance, replication, and multiplicity"; the duplicate subsection deleted and its one new point (absolute ASR is judge-relative, do not compare across papers) folded into App. S8. |
| **The submitted paper promises "all four [placements], with examples, in App. S3"; App. S3 opened on a figure of three** and named the fourth only inside that figure's caption. | App. S3 now opens by naming and distinguishing all four, and the caption says which three the figure draws. |
| **Table S7 (complete outcome accounting) printed 16 read-position rows as 8 pairs with no column telling them apart** — a reader could not tell two encodings from the same cell twice. | Added a `Cell` column: `code` / `f.log`, superscript `r` for the replicate campaign, `--` for the encoder-free channel rows; three blocks separated by rules; caption explains it. Generated, not hand-typed: `src/analysis/as7_outcomes.py` now derives the label from each cell's upstream transform dir and sorts on it, so row order is no longer glob order. Every number is unchanged. |
| **Every table from S7 on was deferred past the end of the text** (tables on pages 16–20, text ending page 15), so a reader checking a number in App. S9 jumped eight pages. | `\clearpage` at each section boundary from App. S9 on flushes the float queue; every table now lands inside the section that introduces it. |
| **Six subsections in App. S14 and App. S17 were immediately followed by a `\paragraph` restating the subsection title.** | Redundant headers dropped, text kept. |
| **App. S14 and App. S17 opened with internal process notes** ("Material moved out ... at the 2026-08-22 re-spine"), dated, describing our workflow to a reviewer. | Rewritten in reader terms. |

**Verified after the pass:**

| Check | Result |
|---|---|
| Every appendix/table/figure number printed in the SUBMITTED `paper.pdf` | **27 pinned numbers, 0 drift** — checked against `supplementary.aux` after the rebuild |
| Submitted `paper.pdf` untouched | Backed up before the build, rendered text diffed identical after it, original bytes restored: `bc125082…` unchanged |
| `build.sh` both documents | `errors=0 undef_ref=0 undef_cite=0 overfull=0 dup_label=0` |
| Labels / citations lost | **0** (only the deliberately deleted duplicate subsection label `sec:res-judge`) |
| Unresolved `??` in the supplementary PDF | 0 |
| Number drift guard | `verify OK` — 10 demoted, **0 drift** (unchanged) |
| Anonymity | 0 identity hits beyond third-person citations of the authors' own published work, which is the required double-blind form; no Author/Title PDF metadata; code tree clean |
| Prose dash connectors | 0 (two hits are in LaTeX comments) |
| Stale-content sweep | 0 hits for re-spine language, AS-8 material, paper-letter references, unrun-work claims |
| Code zip | rebuilt after the `as7_outcomes.py` change: same 669 entries, staged copy compiles, anonymity clean |

**Caps** (verified off the live OpenReview form): Technical Supplement 0.49 MB / 10 MB · Code and Data Supplement 6.7 MB / 50 MB.

**One thing that cannot be fixed and is not worth a change of plan:** the
submitted paper's §4.5 contains a sentence beginning lower-case after a full stop
("... under both protocols alike. and defenses whose decision does not depend
..."). It is in the frozen PDF. Record it for the camera-ready or an arXiv
version; nothing about this submission turns on it.

**One last typo caught on the render, pre-existing:** Table S7's caption legend read
"guard *blk*ock (exact string match)" — `\\emph{blk}ock` sets "blk" against "ock",
which is not a word. Now "guard *blk* (a block, exact string match)".


## Sample images and reproducibility checklist, 2026-08-24

### The two sample-image figures

Both were checked by rendering them, not by reading their captions. Two defects,
both visible in the submitted-quality PDF:

| Defect | Fix |
|---|---|
| 🔴 **Fig. S2 panel (c) was labelled "rabbit — natural image".** It is a black-and-white clip-art line drawing, its own caption calls it "the line-drawing decoy class", and the paper's Limitations list **natural photographs among the classes NOT tested**. The figure contradicted the Limitations in the same document. | Relabelled "rabbit: line-drawing illustration", matching the caption and the Limitations. |
| 🔴 **Fig. S2 panel (a) printed literal backticks: ``` ``mountain'' ```.** LaTeX quote syntax was passed to a matplotlib title, which is not LaTeX and renders it verbatim. | Plain quotes. |
| **Both figure generators were broken** and had been since the `paper/` refactor: `Path(__file__).parents[3]` pointed at `as-7/`, so neither script could find its source images. A reviewer running them from the artifact got `FileNotFoundError`. | Each now looks beside itself first (the images ship in `figs/`) and walks up to the harness copy as a fallback, so the figures rebuild from the released package alone. |
| `make_variants.py`'s docstring still described the panels as `M0 / M2 / M4`, a naming the paper abandoned. | Rewritten to `text / ir_plain / decoy`. |
| Em-dash connectors in three figure labels (invisible to the `.tex` sweep, which does not read images). | Replaced with colons. |

Fig. S1 was correct and is unchanged apart from one label separator.

### The checklist, verified against the official template

The format is the AAAI-27 Author Kit's `ReproducibilityChecklist.tex`
(`science/writing/venue_kits/AuthorKit27/`), confirmed against the live
[AAAI-27 submission instructions](https://aaai.org/conference/aaai/aaai-27/submission-instructions/)
and the [checklist page](https://aaai.org/conference/aaai/aaai-27/reproducibility-checklist/)
on 2026-08-24.

- **All 31 questions present, in the official order, with the official answer
  options** — the `\question` lines are now byte-identical to the kit (one
  straight apostrophe had replaced the kit's curly one; the kit says not to
  modify any part of a `\question` command, so it was restored).
- All 31 answered, no `Type your response here` left, builds `errors=0
  overfull=0`, no identity string and no PDF Author/Title metadata.

Three answers were checked against the artifact rather than assumed, and **two
of them were not backed by anything** until this pass:

| Item | Answer | What backs it now |
|---|---|---|
| 4.7 seeds described sufficiently to replicate | `yes` | Was unbacked: the document never mentioned a seed. App. S10 now has a **Randomness and seeds** paragraph — sampling is removed rather than seeded (greedy everywhere), hosted-API nondeterminism is not seedable and is handled by the measured drift band plus the designed replicate, the one bootstrap uses a stated fixed seed, and every significance test is exact rather than sampled. |
| 4.8 computing infrastructure specified | `partial` | Was unbacked: the document said **nothing** about hardware, software or versions. App. S10 now has a **Computing infrastructure and software** paragraph. Kept at `partial`, honestly: GPU classes and library names with pinned ranges are given, exact per-node memory and OS are not. |
| 4.5 code released under a research-permitting license | `yes` | Was a bare promise: the artifact shipped no license. It now ships `LICENSE` (MIT for code, CC BY 4.0 for the judgment release, third-party benchmark terms untouched, copyright line withheld for blind review) on the AS-4 pattern, plus README sections 6 and 7. |

The remaining answers were re-checked and stand: no theoretical contributions
(2.x all `NA`), no novel dataset introduced (3.3/3.4 `NA`), pre-processing and
analysis code both shipped (4.3/4.4 `yes`, verified against the zip's
`src/prompt_transformations`, `src/defense`, `src/evaluation`, `src/experiment`,
`src/analysis`, `conf/experiment` and `data/`), and `partial` on 4.2 because no
hyper-parameter search was run or reported.

The artifact was rebuilt through `scripts/build_code_artifact.py --paper as7`
rather than by hand, so the anonymization scrub and its verifier ran over
everything: 623 files, 168 scrubs, **verify PASSED**. Hand-syncing would have
undone it — the staged copy of one figure script deliberately differs from the
repo copy where an internal paper letter was scrubbed out.

**Verified after this pass:** all 27 numbers the submitted `paper.pdf` prints
still hold, 0 drift · both documents build `0/0/0/0/0` · checklist builds
`errors=0 overfull=0` · 0 unresolved refs · 0 identity hits · 0 prose dash
connectors · submitted `paper.pdf` byte-identical at `bc125082…`.


## Authors — authoritative source (added 2026-08-23 after failure #398)

⚠️ **The author list of this submission is NOT in this repo.** Every AIA
`paper.tex` is `\author{Anonymous submission}` for double-blind, so the only
authoritative record is the author list entered on **OpenReview** for this
submission.

**Do NOT read the author list off `paper/my_papers/<as-N>/arxiv_latex/`.** That is
a different venue attempt and its `\author{}` block can be older and shorter than
the submitted one. A session did exactly that on 2026-08-23, concluded a real
co-author "is not an author", and nearly excluded a qualified AAAI reciprocal-reviewer
nominee during the submission window (failures ledger #398,
`agent.unverified_claim`). Known from the owner's correction: **Hanwen Liu is an
author on AS-2 and AS-3, and on others** — he does not appear in any local `.tex`.

Any question that turns on who authored a submission (reviewer nomination,
conflicts, the concurrent-submission attestation) is answered from OpenReview or by
asking the owner, never from a local tex file.
