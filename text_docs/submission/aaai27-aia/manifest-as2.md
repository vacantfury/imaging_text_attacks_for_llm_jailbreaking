# AS-2 — AAAI-27 AI Alignment special track — submission package manifest

Built 2026-08-22, after the one-quantity re-spine and the final `paper-check` fix pass. This file is the package's
identity: `paper-check` FINAL's staleness key covers every file listed here, and
the submit step uploads exactly these files. **Any edit to a listed file
invalidates this manifest** (note: `build.sh` embeds a build timestamp, so a
rebuild alone changes the two PDF hashes even with identical source; hash AFTER
the last build, never before) — repackage that artifact, then delta re-check.

*(`manifest.md` in this directory is AS-7's package, a different paper. Do not
cross-read the two.)*

## The upload set

| File | Channel | Size | SHA-256 |
|---|---|---|---|
| `paper.pdf` | Main submission PDF | 0.5 MB | `73f7f35256a0778897538345b6256f7ed73b0a78646150fae223bf9aaed77551` |
| `supplementary.pdf` | Supplementary Document | 0.3 MB | `7eb89d7321c77cf039b87c287939946dd0a25440bc284013aec0d4b6692470c2` |
| `supplementary_code_and_data.zip` | Code and Data Supplement | 36.1 MB | `1c4d9d06c2cda4a0cd7159b77167063806d623da23cb3d912b891e2f3eede2eb` |

Source tree: `paper/as-2/aaai_2027_ai_alignment/`. Repo HEAD at packaging:
`7d53331`. ⚠️ `paper/` is gitignored, so the repo hash does **not** cover the
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
| overfull boxes | 0 | 0 |
| `??` in rendered PDF | 0 | 0 |
| `tex_stat_audit` | CONSISTENT (23 rows) | CONSISTENT (7 rows) |

- Draft-history sweep: **0 hits** across all 16 fixed strings, both documents.
- Anonymity: `\author{Anonymous submission}`, empty affiliations, `[submission]`
  option; **0** web or repository pointers in either document.
- Code artifact: 629 files, 95 strings scrubbed, `verify_tree` anonymization
  **PASSED**; 282 judgment cells, each verified to reproduce its own recorded
  metric before release.

## What the final `paper-check` fix pass changed (2026-08-22)

Six fresh-context dimension reads plus a cross-family second opinion all returned
`blocked`. Every finding below was verified against the artifact or the document
before being acted on; the pass is recorded in
`text_docs/checks/2026-08-22-paper-check-final.md`.

**Two evidence gaps, both pre-existing, both closed with data that already
existed on disk but shipped nowhere.**

- The **hosted models' harmful side** (18→0, 11→5, 6→1, 14→13) is half the
  paper's central price claim and the whole input to the break-even table. It was
  printed in no table in either document and was absent from the judgments
  release. Recovered from campaign `paper_b_symmetry_test`, given paired
  statistics, and printed as `tab:hostedharm`.
- The **open checkpoint's own ladder plus matched harmful rung** (campaign
  `paper_b_exchange_rate_ow`) backs the 2% plain-harmful figure quoted in the
  abstract, introduction, results and conclusion. Also absent from the release.

Both campaigns are now in `CAMPAIGNS`; the release went 258 → 282 cells and the
provenance table is generated from that index, so its completeness claim is now
true by construction (18 rows summing to 282).

**Three headline numbers were wrong.**

- The Introduction attributed **+33 points** to the asserted-attachment effect
  measured with nothing attached. The placebo ladder gives **+16**; +33 belongs to
  a cell where a canvas *is* attached. The paper's own claims table already said
  +16, so the two disagreed by 17 points on a load-bearing claim.
- The abstract's `≤2 points` dropped the "on three of four hosted models"
  qualifier the Results carry, and Table 1 has a starred +13-point neutral cell.
- The pixtral inversion read **35 points** at three sites against the table's
  48→81 and the claims table's +33.

**Evidence returned to the main paper.** `tab:placebo` had six main-paper
references and `tab:strata` a starred claim row while both sat in the
supplementary; both are now printed in the main paper. The ten-arm property sweep
was cited four times and existed in *neither* document (it had left with AS-9);
it and its two instance-replication tables are back in the supplementary as
`app:imgprops`.

**Rendering.** Two tables were overprinting the neighbouring column's text by
~17% of a column width; significance asterisks were overprinting the next column
via `\rlap`; the claims table was an inline `center` block that could separate
from its caption; Figure 1's labels were rendering at **3.7pt** (a 7.2in figure
scaled to a 3.31in column). All four fixed. `build.sh` now **sizes** overfull
boxes and fails above 5pt, because a count alone was what let this hide.

**House rules.** The percentage-point abbreviation was used 176 times against the
handbook rule; converted. Dash sentence connectors, 205 of them, converted per the
standing order; the only `---` left are 13 table cells meaning "not applicable".
Two passages narrating this manuscript's own revision history were converted to
statements about the data.

**Also fixed:** open-checkpoint count (7, was stated as six and as eight); the
±7-point bound contradicted by a printed [-2.7,+9.3] interval; a ten-category
enumeration listing nine; "four kinds" followed by five; false "unmarked contrasts
n.s." claims in two captions; an unqualified "pre-registered"; an unbalanced
parenthesis; an orphan table; `keep_text` used as undefined jargon; the closest
prior work cited with the wrong year; two attack instruments used with no
citation, one of them a published paper by an author of this one, now cited in
third person; and the paired-difference interval method (Newcombe) never declared
alongside Wilson.

## claim-integrity

`pass (manual recompute) · host: local` — this repo has no claim-guard suite yet,
so the battery ran its sanctioned fallback: every sentence that COUNTS over our
own runs or NAMES the source of a number was recomputed from its artifact,
claim by claim.

**Verified against the released artifact.** The `qwen3-vl-8b` borderline shift
recomputes to **+32** and **+28** from the tier-scan and generational-ladder
cells in `artifacts/judgments/`, matching the paper. All 282 released cells
reproduce the metric their own `results.json` recorded; the emitter refuses
otherwise. Cell and withholding counts (282 / 46) read directly from `index.json`.

**Verified against the paper's own validated builder.**
`src/analysis/paper_b_multiplicity.py` reproduces "36 of 69 tests survive a
global Bonferroni" and the declared-null families.

**Four stale-set defects found and fixed** — a counted claim ranging over a set
the re-spine had shrunk, which is the failure the sibling repo's handoff
describes:

1. Discussion claimed the effect holds "across ten image variants". The paper no
   longer shows ten. Rewritten to what it shows.
2. Results counted "all ten arms on that model are null" over a table that left.
   Rewritten to drop the count, keeping both stated values.
3. `tab:claims` gave the hosted range as "+23 to +57pp", splicing a per-CATEGORY
   cell into a per-MODEL range. Pinned to +23 to +54pp, one grid.
4. Method described "ten arms varying resolution, aspect ratio, colour, encoding
   and content". Rewritten to the contrasts actually reported.

The surviving "+57pp" at paper.tex:155 is legitimate: it is a per-category cell,
correctly attributed to one category on one model.

**Not verified, and not claimed as such.** An ad-hoc scan written the same hour
mis-assigned text-versus-image arms on one campaign (arm identity is in the
config, never the path), so no count was reported from it. The remaining counted
claims — "three of the six open-weight models", "four of the five", "three of
four hosted models" — rest on the paper's tables rather than on an independent
recompute. Porting a real claim guard is the fix and is filed.

## Known residue, not blocking the package

- 240 dash-line sentence connectors (house rule). New prose written at the
  re-spine is clean; the existing sweep is unrun and is a mechanical edit with
  real risk, since some are legitimate table placeholders. Owner's call.
- Spelling drift: artefact/artifact, judgement/judgment, standardised/standardized.
- Bold carries two meanings across tables (emphasis vs significance).
- `src/analysis/paper_b_multiplicity.py` ships in the code artifact with source
  labels naming `tab:imgprops`/`tab:owprops`/`tab:instance`, tables that left the
  paper at the re-spine. Display strings only, no effect on its arithmetic; left
  unedited rather than touching a validated instrument late.
