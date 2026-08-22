# AS-2 — AAAI-27 AI Alignment special track — submission package manifest

Built 2026-08-22, after the one-quantity re-spine. This file is the package's
identity: `paper-check` FINAL's staleness key covers every file listed here, and
the submit step uploads exactly these files. **Any edit to a listed file
invalidates this manifest** — repackage that artifact, then delta re-check.

*(`manifest.md` in this directory is AS-7's package, a different paper. Do not
cross-read the two.)*

## The upload set

| File | Channel | Size | SHA-256 |
|---|---|---|---|
| `paper.pdf` | Main submission PDF | 0.45 MB | `e56399637005aab30ee144b24ff8a82519ff1ba7a6cd3792fb4ceaad1d1219a6` |
| `supplementary.pdf` | Supplementary Document | 0.32 MB | `142ebb54634dce3409da66006d3b8e411e8defce106895977149a44509718303` |
| `supplementary_code_and_data.zip` | Code and Data Supplement | 34 MB | `b0f8109d1acd7f0e190f3f5c098c37dacd2217e7903e847ca2724cd46bd8d1cf` |

Source tree: `paper/as-2/aaai_2027_ai_alignment/`. Repo HEAD at packaging:
`6e6bec3`. ⚠️ `paper/` is gitignored, so the repo hash does **not** cover the
paper source. Its revision history is the `paper.tex.pre-*` backups beside it;
`paper.tex.pre-respine` is the last pre-re-spine state.

Rebuild everything with:

```
./paper/as-2/aaai_2027_ai_alignment/aaai_aia_latex/build.sh    # both PDFs
python -m src.analysis.as2_judgments_release                   # the judgment release
python scripts/build_code_artifact.py --paper as2              # the code zip
```

## Packaging profile relied on

| Fact | Source | Verified |
|---|---|---|
| Channel names ("Code and Data Supplement", "Supplementary Document") | [AAAI-27 submission instructions](https://aaai.org/conference/aaai/aaai-27/submission-instructions/) | 2026-08-22, live |
| Materials must be provided at submission time; "will be released after acceptance" is not evidence of reproducibility | same | 2026-08-22, live |
| Appendix has no in-PDF home; it goes to the Supplementary Document | [AIA call](https://aaai.org/conference/aaai/aaai-27/aia-call/) + main-track instructions | 2026-08-21, cached in science `venues/aaai27_venue_info.md` |
| Main submission must be self-contained; reviewers are not obliged to consult supplementary | same | 2026-08-21, cached |
| No repo link in the PDF (AAAI bans anonymous-repo links; code ships as the zip) | project policy + venue record | swept 2026-08-22: 0 hits |
| **Supplementary file-size cap** | not stated on the instructions page | ⚠️ **UNVERIFIED** — no published limit found 2026-08-22. 34 MB is within normal portal limits but is not confirmed against a stated cap. If the portal refuses it, the fallback is the lean projection (`{id, asr, refusal}`, ~1.3 MB) plus a one-sentence narrowing of the artifact statement. |

## What the re-spine changed

AS-2 was re-spined 2026-08-22 onto **one quantity**: the refusal shift caused by
an uninformative image attachment. Material measuring a *different* quantity —
which property of the visual input carries the magnitude — left for a separate
paper (AS-9, `text_docs/presence_carrier/proposal.md`); its tables are extracted
verbatim at `paper/as-9/inherited_from_as2.tex`.

- Body floats **23 → 10**; Introduction paragraphs **15 → 8**; abstract **3
  paragraphs / ~50 numbers → 1 paragraph / 3 numbers** (handbook rule).
- Results is now three subsections: the shift and who pays it · what it is not ·
  the price and its decoupling.
- Six tables moved to the Supplementary Document as material that *defends* the
  claim without carrying it (stratified cost, the asserted-attachment ladder, the
  model-selection scan, within-family replication, break-even, delimitation),
  plus the judge-robustness section.
- `tab:imgvsimg` stayed and now carries leg one, gaining the open-checkpoint size
  row (+16pp, 18/2, p=0.0004, 95% CI [+7.7,+24.9]).
- Two defects found and fixed while cutting: the Conclusion still asserted the
  carrier claim the paper no longer makes, and put the pixtral inversion at 35
  points where the body says 33 and states the lower value is carried throughout.

## State at packaging

| Check | Main | Supplementary |
|---|---|---|
| errors / undefined refs / undefined cites | 0 / 0 / 0 | 0 / 0 / 0 |
| overfull boxes | 2 | 0 |
| `??` in rendered PDF | 0 | 0 |
| `tex_stat_audit` | CONSISTENT (19 rows) | CONSISTENT (7 rows) |

- Draft-history sweep: **0 hits** across all 16 fixed strings, both documents.
- Anonymity: `\author{Anonymous submission}`, empty affiliations, `[submission]`
  option; **0** web or repository pointers in either document.
- Code artifact: 604 files, 95 strings scrubbed, `verify_tree` anonymization
  **PASSED**; 258 judgment cells, each verified to reproduce its own recorded
  metric before release.

## claim-integrity

`pending` — this repo has no claim-guard suite yet (the port task is filed; the
reference implementation is `model_internals_safety` `scripts/claim_sets.py` +
`tests/test_paper_claim_integrity.py`). The statistical audit above is the
partial substitute: it recomputes every stated Δ and p-value from its own
discordant counts, but it cannot check a unit, a comparator, or which grid a
number came from. **S12 refuses on a `pending` row**, so this must be resolved
(guard ported, or a recorded manual recompute claim by claim) before submit.

## Known residue, not blocking the package

- 240 dash-line sentence connectors (house rule). New prose written at the
  re-spine is clean; the existing sweep is unrun and is a mechanical edit with
  real risk, since some are legitimate table placeholders. Owner's call.
- Spelling drift: artefact/artifact, judgement/judgment, standardised/standardized.
- Bold carries two meanings across tables (emphasis vs significance).
