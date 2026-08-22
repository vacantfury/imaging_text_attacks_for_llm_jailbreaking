# paper-check — FINAL — AS-2 "The Uncontrolled Variable"

| | |
|---|---|
| Mode | `final` (research-workflow S10b) |
| Paper | AS-2, AAAI-27 **AI Alignment special track** |
| Source | `paper/as-2/aaai_2027_ai_alignment/aaai_aia_latex/` (gitignored) |
| Repo HEAD | `7d53331` |
| Upload-set hashes | `paper.pdf` `73f7f352…` · `supplementary.pdf` `7eb89d73…` · `supplementary_code_and_data.zip` `1c4d9d06…` (full values in `text_docs/submission/aaai27-aia/manifest-as2.md`) |
| Venue source | [AAAI-27 submission instructions](https://aaai.org/conference/aaai/aaai-27/submission-instructions/) + [AIA call](https://aaai.org/conference/aaai/aaai-27/aia-call/), checked 2026-08-22 |
| **Verdict at first pass** | **`blocked`** — all six dimension reads and the cross-family read returned `blocked` |
| **Verdict after the fix pass** | **`pass` on the six rubric dimensions** — every blocking finding closed and re-verified |
| **Submission readiness** | **not yet** — the venue-compliance battery below found a required upload missing (built 2026-08-22) and two placement items still open |

The verdict is keyed to the upload-set hashes in the manifest. Any edit to a
listed file stales it (verification decay); re-check the dimensions the diff
touches and reissue.

## How the check ran

Six fresh-context subagents, one per rubric dimension, reading the compiled PDFs
and the `.tex` source cold, plus one independent cross-family read of the PDF.
None of the readers shared the context that wrote the prose. All edits were held
until every reader returned, so their findings stayed keyed to the files they
read.

Findings below are labelled **verified** (a mechanical scan, a recompute from the
artifact, or a readback of rendered output) or **judged** (editorial judgment).

---

## Blocking findings, and what closed them

### 1. Evidence the paper cites and does not contain — verified

Two campaigns of collected data backed claims that appeared in no table in either
document and shipped in no artifact. Both existed on disk the whole time.

| Gap | Data | Closure |
|---|---|---|
| Hosted models' harmful side: 18→0, 11→5, 6→1, 14→13. Half the central price claim, and the whole input to the break-even table. | campaign `paper_b_symmetry_test` | Recovered, paired statistics computed, printed as `tab:hostedharm`; campaign added to the release |
| Open checkpoint's ladder + matched harmful rung, backing the 2% plain-harmful figure quoted in abstract, intro, results and conclusion | campaign `paper_b_exchange_rate_ow` | Added to the release; `tab:owladder` now has released cells behind it |

Release went **258 → 282 cells**, every one verified to reproduce its own
recorded metric. The provenance table (`tab:provenance`) is now **generated from
that index**, so its "provenance of every result" claim is true by construction:
18 rows summing to 282.

### 2. Three headline numbers wrong — verified

- **Introduction: `+33 points` for the asserted-attachment effect "with nothing
  attached".** The placebo ladder — the only grid with no image attached in any
  arm — runs 14 → 24 → 40 → 39, so the attachment clause is worth **+16**. The
  +33 belongs to a cell where a canvas *is* attached. The paper's own claims table
  already stated +16, so two load-bearing statements disagreed by 17 points.
  Corrected to +16.
- **Abstract: `≤2 points` without qualifier.** The Results carry "on three of four
  hosted models"; Table 1 has `gemini-2.5-flash-lite` neutral at 1→14, marked
  significant. Qualifier restored, and spelled out as the first use of the unit.
- **Pixtral inversion at `35 points`, three sites.** The table reads 48→81 and the
  claims table says +33; the cross-family rescore independently reads +30.0.
  Corrected to 33.

### 3. Evidence sitting where a reviewer may not read it — judged

`tab:placebo` carried **six** main-paper references and `tab:strata` a starred
load-bearing claim row, while both lived in the Supplementary Document, which
AAAI tells reviewers they are not obliged to consult. Both promoted into the main
paper.

The ten-arm property sweep was cited four times and existed in **neither**
document, having left with AS-9 in the re-spine. It and its two
instance-replication tables returned as `app:imgprops`, which also repairs
families **F2** and **F6** of the multiplicity accounting, whose tables had
departed with it.

The evidentiary-tag legend governing every table in the main paper was stranded
inside a supplementary caption; moved into the main paper, together with the
first sentence anywhere telling the reader a Supplementary Document exists.

### 4. Rendering defects a reviewer sees — verified by readback

| Defect | Measurement | Fix |
|---|---|---|
| Two tables overprinting the neighbouring column | 39.95pt and 38.86pt, ~17% of a 239.4pt column | `table*` promotion; `\scriptsize` + tight `\tabcolsep` |
| Significance asterisks overprinting the next column | rendered `1 → 14∗∗∗11 → 34∗∗∗` | 13 `\rlap` wrappers removed |
| Claims table an inline `center` block, able to separate from its caption | — | made a real `table*` float |
| Figure 1 labels illegible | 8pt in a 7.2in figure scaled to a 3.31in column = **3.7pt** | `figure*` at `\textwidth` → **7.8pt** |

`build.sh` reported `overfull=2` on every build this session and the count was
read as benign. It now **sizes** each box, prints the offenders with line numbers,
and **fails the build above 5pt**. This is the enforcement-lane fix: a count is
not a check.

### 5. House-rule violations — verified

- **Percentage-point abbreviation, 176 uses.** Handbook `paper_writing.md` forbids
  it in paper text: in scholarly context that abbreviation means *pages*.
  Converted to "percentage points" at first use and "points" thereafter, with
  attributive forms hyphenated. Zero remain.
- **Dash sentence connectors, 205.** Standing owner order 2026-08-19 names papers
  explicitly. Converted to commas, colons, parentheses or sentence splits. Zero
  prose connectors remain; the 13 surviving `---` are table cells meaning "not
  applicable", which are not connectors. The mechanical pass left 11 defects
  (double colons, nested parentheses); all were found by a follow-up scan and
  repaired by hand.
- **Manuscript revision history, two passages.** Handbook: a submission never
  narrates its own draft history, and under double-blind it is an anonymity
  hazard. Converted to statements about the data, keeping every number.

### 6. Consistency and citation defects — verified

Open-weight checkpoint count stated as six, seven and eight in four places; the
true count is **seven**. A `±7`-point bound contradicted by a printed
`[-2.7,+9.3]` interval. A "ten OR-Bench categories" enumeration listing nine.
"Four kinds" followed by five. False "unmarked contrasts n.s." claims over two
columns that were never tested. An unqualified "pre-registered" against a
multiplicity section stating nothing was registered anywhere. An unbalanced
parenthesis. An orphan table. `keep_text` used as undefined internal jargon.

Citations: the closest prior work carried year 2026 against a booktitle naming the
**thirty-ninth** NeurIPS (2025). Two attack instruments in `tab:headroom` were used
with no citation at all; both now cited, one of them a published paper by an author
of this submission, cited in third person for double-blind. That entry was also
swapped from its arXiv preprint to its version of record (PMLR v318).

The paired-difference interval method (**Newcombe**) was never declared; the
statistics section named only Wilson, which is an interval on a different
quantity. Both now declared and distinguished.

---

## Batteries

| Battery | Result |
|---|---|
| Build, both documents | errors 0 · undefined refs 0 · undefined citations 0 · overfull >5pt **0** |
| Placeholders (`TODO`/`TBD`/`XXX`/`FIXME`/`??`) | 0 |
| Float integrity | 24 floats · orphans **0** · dangling refs **0** · duplicate labels **0** |
| `tex_stat_audit` | **CONSISTENT** both documents: every Δ matches its discordant counts and rate pair, every *p* matches an exact two-sided McNemar |
| Draft-history sweep (17 fixed strings) | **0 hits** |
| House rules | `pp` 0 · prose dash connectors 0 · parenthesis balance 0 |
| Anonymity | `\author{Anonymous submission}`, empty affiliations, `[submission]`, **0** web or repository pointers |
| Code artifact | 629 files, 95 strings scrubbed, `verify_tree` **PASSED**, 282 cells each reproducing its recorded metric |
| claim-integrity | `pass (manual recompute) · host: local` — see the manifest |

**One `tex_stat_audit` flag was investigated and dismissed**: it paired one
sentence's *p* with the next sentence's counts. Both values were recomputed by
hand and are correct — McNemar(10,1) = 0.0117 and McNemar(1,9) = 0.0215, exactly
as printed.

## Venue-compliance battery — run 2026-08-22 against the live instructions

Source: [AAAI-27 submission instructions](https://aaai.org/conference/aaai/aaai-27/submission-instructions/),
fetched 2026-08-22, plus the [AIA call](https://aaai.org/conference/aaai/aaai-27/aia-call/).

| Check | Result |
|---|---|
| Template provenance | `aaai2027.sty` `[2027/05/04 AAAI 2027 Submission format]`, byte-identical to the sibling package's copy; `[submission]` option set; no margin/font tampering |
| Anonymity formatting | `\author{Anonymous submission}`, empty affiliations, 0 web or repository pointers, no PDF Author metadata |
| Packaging placement | Main PDF · Supplementary Document · Code and Data Supplement, matching the venue's own channel names |
| No repo link in the PDF | 0 hits (AAAI bans anonymous-repo links) |
| **Reproducibility checklist** | 🔴 **REQUIRED and was MISSING.** *"Authors must complete the reproducibility checklist provided in the AAAI-27 Author Kit and submit it at the time of paper submission"*, *"uploaded separately from the main paper in the designated field of the submission form"*. Built 2026-08-22, 24 applicable items answered, anonymity clean, now the fourth file in the manifest |
| Ethics statement placement | 🔴 **Currently past the content boundary.** *"any ethical statements or similar considerations, if included, must be included in the 7 content pages"*. Filed to the task file |
| Abstract length cap | None stated |
| Supplementary size/format cap | None stated — the named debt below stands as *unverified*, not violated |
| Main-content requirement | Outstanding; the remaining work is the author's own and is tracked in the task file, not here |

## Named debts



- **Supplementary file-size cap unverified.** No published limit found on the
  AAAI-27 instructions page. 36.1 MB is within normal portal limits but is not
  confirmed against a stated cap. Fallback if the portal refuses it is recorded
  in the manifest.
- **No claim-guard suite in this repo.** The claim-integrity battery ran its
  sanctioned manual-recompute fallback. The port task is filed.

## Not submitted

Nothing has been uploaded. The final press is the owner's.
