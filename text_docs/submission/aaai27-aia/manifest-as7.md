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
| `paper.pdf` | Main submission PDF | 324 KB | `b18616d08fd803804a0abdabba3a34ce6259609482c6740a72fc9de0f4ebf20f` |
| `supplementary.pdf` | Supplementary Document | 516 KB | `6fd1f24ad1822b44db14ace8eaaadd598c594f8c8865a9d1fa1a3a321969e38b` |
| `supplementary_code_and_data.zip` | Code and Data Supplement | 6.7 MB | `432293dcf8f8548fc022f6c9e7aa304de1af961f4a7e0f710aa5a736a9335005` |
| `ReproducibilityChecklist.pdf` | Reproducibility Checklist (separate designated field) | 80 KB | `f66dbb814bff272abda8087c2980b2c83f59cf44c683664ee6645971210f0d4b` |

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
| Supplementary format / size caps | — | **UNVERIFIED**: the 2026-08-22 live read of the submission instructions does not state them. Read them off the OpenReview form before uploading. |
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
