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
| `paper.pdf` | Main submission PDF — **SUBMITTED, frozen** | 306 KB | see the note below |
| `supplementary.pdf` | Supplementary Document (Technical Supplement field, 10 MB cap) | 478 KB | `0537e8a046785e1101b79e5325fca6ba027bd1938a34a156efbd2971ab913531` |
| `supplementary_code_and_data.zip` | Code and Data Supplement (50 MB cap) | 6.7 MB | `432293dcf8f8548fc022f6c9e7aa304de1af961f4a7e0f710aa5a736a9335005` |
| ~~`ReproducibilityChecklist.pdf`~~ | **NOT UPLOADED — owner ruling 2026-08-22: the Edit Supplementary Materials form carries no checklist field.** Built and kept for the record. | 76 KB | `f66dbb814bff272abda8087c2980b2c83f59cf44c683664ee6645971210f0d4b` |

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
