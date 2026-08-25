# AS-2 — AAAI-27 AI Alignment special track — submission package manifest

Built 2026-08-22, after the one-quantity re-spine and the final `paper-check` fix pass. This file is the package's
identity: `paper-check` FINAL's staleness key covers every file listed here, and
the submit step uploads exactly these four files. **Any edit to a listed file
invalidates this manifest** (note: `build.sh` embeds a build timestamp, so a
rebuild alone changes the two PDF hashes even with identical source; hash AFTER
the last build, never before) — repackage that artifact, then delta re-check.

*(`manifest.md` in this directory is AS-7's package, a different paper. Do not
cross-read the two.)*

## The upload set

| File | Channel | Size | SHA-256 |
|---|---|---|---|
| `paper.pdf` | Main submission PDF — **SUBMITTED 2026-08-22, FROZEN** | 0.35 MB | `eb4bc96624faab189349fa427c5cbdff7baa30acefafa88d950c685c861a3fe8` |
| `supplementary.pdf` | Supplementary Document | 0.45 MB | `82f38c7abc4aea8840ea1097ac4df8cd50a159ec9e9e3ca4d92a62b0fdcaa77b` |
| `supplementary_code_and_data.zip` | Code and Data Supplement | 36.11 MB | `1c4d9d06c2cda4a0cd7159b77167063806d623da23cb3d912b891e2f3eede2eb` |
| `ReproducibilityChecklist.pdf` | Reproducibility Checklist (separate field) | 0.08 MB | `4aaa6cd5ae5c2423233afba7bdc02d84df23ce8ae6d9b27dbf49dd266eef9a8d` |

Source tree: `paper/my_papers/as-2/aaai_2027_ai_alignment/`. Repo HEAD at packaging:
`7d53331`. ⚠️ `paper/` is gitignored, so the repo hash does **not** cover the
paper source. Its revision history is the `paper.tex.pre-*` backups beside it;
`paper.tex.pre-respine` is the last pre-re-spine state.

Rebuild everything with:

```
./paper/my_papers/as-2/aaai_2027_ai_alignment/aaai_aia_latex/build.sh    # both PDFs
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
| **Reproducibility checklist is REQUIRED, uploaded separately** | [AAAI-27 submission instructions](https://aaai.org/conference/aaai/aaai-27/submission-instructions/): *"Authors must complete the reproducibility checklist provided in the AAAI-27 Author Kit and submit it at the time of paper submission"*, *"uploaded separately from the main paper in the designated field of the submission form"* | 2026-08-22, live — ⚠️ **this was missing from the package until 2026-08-22**; built from the Author Kit template, all 24 applicable items answered, anonymity swept clean |
| Ethics statement, if included, must sit in the main content pages (not the supplementary) | same | 2026-08-22, live |
| No stated abstract length cap | same | 2026-08-22, live — not mentioned |
| **Supplementary file-size caps** | OpenReview submission form, AAAI-27 AIA Submission201 | 2026-08-22, read off the live form — **RESOLVED**: Technical Supplement **10 MB** (ours 0.45 MB), Code and Data Supplement **50 MB** (ours 36.11 MB). The earlier UNVERIFIED row is closed; no fallback projection needed. |

## What the re-spine changed

AS-2 was re-spined 2026-08-22 onto **one quantity**: the refusal shift caused by
an uninformative image attachment. Material measuring a *different* quantity —
which property of the visual input carries the magnitude — left for a separate
paper (AS-9, `text_docs/presence_carrier/proposal.md`); its tables are extracted
verbatim at `paper/my_papers/as-9/inherited_from_as2.tex`.

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


## Post-submission state (2026-08-22)

**The main paper was submitted and is frozen.** `paper.pdf` is immutable at
`eb4bc966…`; `paper.SUBMITTED.pdf`, `paper.tex.SUBMITTED` and `paper.aux.SUBMITTED`
are read-only copies beside it. The remaining OpenReview fields and the two
supplementary uploads stay editable until the wall, so refinement continues on
those alone.

### The frozen cross-reference contract

The submitted PDF renders **17 references into the Supplementary Document**
(section, table and figure numbers). Those numbers are baked into a file that can
no longer change, so the supplementary may be rewritten but **may not renumber**.
The contract is recorded in `aaai_aia_latex/FROZEN_XREFS.txt` and enforced by
`check_supp.py`, which fails the build if any of the 17 moves.

Practical consequence for any later edit: prose, captions and **section titles**
are free (the frozen paper prints bare numbers, never titles), but inserting or
removing a numbered section, table or figure ahead of a pinned one is forbidden.
Pinned: sections S4, S8, S17, S21, S22, S23, S24, S29 · tables S4, S8, S10, S11,
S12, S14, S15, S16 · figure S1.

`build.sh` rebuilds BOTH documents and would change the submitted PDF's bytes.
**Use `build_supp.sh` instead** — it never runs pdflatex on `paper.tex` and
restores `paper.aux` from the submitted copy before each run.

### What the supplementary refinement fixed

Damage left by the earlier condensation passes, all verified against the artifact
or the document before acting:

- **Six placeholder section headings** ("Elaboration, part four/three/five/six",
  "Elaboration, continued") retitled to describe their contents. One of them, S11,
  was **completely empty** and could not be deleted without shifting the frozen
  ethics appendix; it now holds the pairing-protocol material relocated from S13.
- **Four truncated headings** — `Conclu`, `Introdu`, `Experimental Setu` — repaired
  to house style, and a duplicated closing passage removed (S13 and S16 carried
  near-identical conclusions; S13's fuller version survives).
- **A dangling auto-generated pointer** (`\S\ref{…} continues.`) and its stub
  subsection removed; the real content was relocated into S15.
- **The supplementary referred to itself in the third person** four times
  ("Table X *of the Supplementary Document*", once doubled). All four tables are
  defined in this document; the phrase is gone.
- **Nine subsections opened mid-thought** with a referent that had left with the
  main paper ("That limit…", "Their shortcut…", "That invariance…"). Each now names
  its subject.
- **`llava-1.5-7b` was missing as the subject of its own result.** The passage
  reporting `37→76%` reads as though it describes `pixtral-12b`, whose cells are
  48/50/80/81/83. Checked against the release: 37→76 harmful and 10→2 benign are
  `llava_7b`, campaign `paper_b_sign_inversion` — the *second* inverting
  checkpoint. Data correct, subject restored.
- Spelling aligned to the frozen paper (`artifact`, `judgement`).

**A claim I introduced and then removed:** a lead-in sentence I wrote asserted the
effect acts through the image channel "on most of the checkpoints we test." The
data does not support that count. Replaced with what is shown.

`tex_stat_audit` flags line 233 as inconsistent. Re-verified by hand this session:
exact McNemar(10,1)=0.01172 and McNemar(1,9)=0.02148, both exactly as printed. The
tool pairs one sentence's p with the next sentence's counts. Not a defect.

Build state: 0 errors, 0 undefined refs, 0 undefined cites, 0 overfull boxes, 0
`??` in the rendered PDF, 17/17 frozen cross-references holding, anonymity clean
(the only name hits are the third-person citation of a published paper, correct
under double-blind) and no author in the PDF metadata.


## Second supplementary pass — checked AGAINST the submitted paper (2026-08-23)

The first pass repaired the document on its own terms. This pass checked it as the
**companion to the frozen paper**, which is now the fixed reference.

**Pointer-delivery audit (verified, 17/17).** Every one of the 17 references the
submitted PDF makes into this document was traced to its target and tested against
what the paper *promises* there. All 17 deliver. One apparent failure was my own
check being wrong, not the document: the paper's "three judges have now been
applied" is delivered by S29 (`gpt-5-mini` at collection, `gpt-5-nano` across all
88 cells, cross-family `gemini-2.5-pro` on the load-bearing ones, plus two human
anchors); my probe searched for a literal phrase the section never uses.

**Continuation audit (verified).** The document declares that each subsection
continues a paragraph of the main paper. Condensation cut paragraphs, so every
subsection was matched against the FINAL paper's headings: 32 of 34 match; the 2
exceptions are the repaired Conclusion and Setup fragments, which correspond to
paper *sections* rather than paragraphs. No subsection continues something that no
longer exists.

**A false claim in the opening, fixed.** The document asserted "Every table a
load-bearing claim of the main paper rests on is printed in the main paper itself."
That is not true: the paper cites **eight** tables defined here, including the three
backing `qwen3-vl-8b`, the checkpoint the paper says "carries the paper's scope
claim." The opening now states the defensible posture the paper's own source
comments record ("numbers stated in text") — the main paper states in its text every
quantity its argument turns on, and these tables are what a reader consults to check
them — and it now **names all eight with their numbers**, so a reviewer arriving
from the paper can navigate straight to the one cited.

⚠️ **Self-containment note for any future venue.** For `tab:strata` the paper states
the method (30 prompts × 10 categories) but *not* the result; it concedes "a sampling
defect in the measurement carrying our central cost claim" and points here for
whether the fix cured it. A reviewer reading only the main paper cannot tell. The
supplementary answers it completely (S6 prose + Table S12: all 30 per-category
contrasts positive, 26 surviving Benjamini--Hochberg, effect *larger* than the
unrepresentative slice). Unfixable now that the paper is frozen; state the result
inline if this work is ever re-filed.

**Duplication swept (4 near-duplicate passages → 1).**
- The **Limitations appendix contained two stacked write-ups**: three truncated
  subsections (`Scope.` / `Coverage.` / `Instrument.`, all opening mid-sentence)
  followed by the real elaboration, whose paragraphs fully subsume them. The frozen
  paper points a reviewer straight at this section, so they were landing on the
  broken copy first. Truncated trio deleted; the section now opens on its intro.
- The randomised-interleaving numbers were printed verbatim in two sections;
  S11 now points to S26, which carries the full comparison, seeds and caveats.
- The one remaining pair is a section summary and its detailed home — legitimate.

**Also:** a stale source comment claimed `tab:strata` had been "promoted to the main
paper" (it was not); corrected, and the section holding the cited tables gained a
label so the pointer is real. A `\tableofcontents` was tried and reverted: the
aaai2027 style suppresses ToC generation, so it rendered as an empty "Contents"
heading.

Build state: 0 errors, 0 undefined refs, 0 undefined cites, 0 overfull boxes, 0
`??`, 17/17 frozen cross-references holding, 17/17 pointers delivering, anonymity
clean, no author in PDF metadata. Frozen `paper.pdf` still `eb4bc966…`.


## Sample image and Reproducibility Checklist verified (2026-08-23)

**Figure S1 (the three request-independent images) — verified correct.** The panel
dimensions were checked against the source files, not against the caption's own
words: `mountain.png` 1024x141, `blank.png` 512x512, `rabit.jpeg` 1189x1418, all
three matching the caption exactly. The rendered figure was inspected: (a) the
caption image carrying its typed sentence, (b) the pure-white blank, (c) the
clip-art rabbit. The caption names the drawn subject deliberately, so a reader can
verify for themselves that the content is request-independent. No change needed.

**Reproducibility Checklist — official format confirmed, all 31 answered.** Built
on the AAAI-27 Author Kit template (`\checksubsection` / `\question` /
`\ifyespoints` macros, the `isChecklistMainFile` standalone-or-input conditional).
Final tally: 19 yes, 1 no (the theoretical-contributions gate), 10 NA, 1 partial.
Zero blanks, zero off-menu answers other than the gated NAs below. 2 pages,
anonymity clean, no Author in the PDF metadata.

Each answer was checked against the artifact rather than accepted as written:

- **Q20 (values tried per hyperparameter + selection criterion): `partial` -> `yes`.**
  Verified that AS-2 performed no hyperparameter search: its own config dir carries
  no temperature override (it inherits the greedy default) and the files whose names
  contain "sweep"/"grid" vary experimental *conditions* (image property, rung,
  checkpoint), not model hyperparameters. A repo-wide grep does turn up non-zero
  temperatures and real search machinery, but those belong to the sibling papers, so
  the claim was scoped to this paper's configs before being made. A
  **Parameter selection** paragraph was added to the reproducibility appendix stating
  that one value was tried per parameter, fixed a priori, with reproducibility rather
  than performance as the criterion. With that in place the question is fully
  answered.
- **Q26 (computing infrastructure): stays `partial`, deliberately.** The question
  demands GPU/CPU models, memory, OS *and* library versions. The software stack is
  fully specified (vLLM 0.25.0, PyTorch 2.11.0, CUDA 13.1, Transformers 5.13.1);
  the hardware is not, and the runs span more than one cluster, so no single GPU
  model could be asserted truthfully. Its option set offers no NA. `partial` is the
  correct answer and was left alone rather than inflated.
- **Q5-Q9 (`NA` against a `yes/partial/no` menu): correct, left as is.** These sit
  behind "Does this paper make theoretical contributions? *no*", so their option list
  assumes a reader who answered yes. Answering `no` would actively misstate (it would
  claim we failed to state assumptions). All three sibling checklists — including
  AS-4, already accepted by the portal — answer NA here.
- Q25 (seeds), Q28 (runs per result) and Q31 (final hyperparameters) confirmed
  against the reproducibility appendix, which states the decoding settings verbatim
  and is honest that no hosted provider honours a seed, so bit-for-bit reproducibility
  is not claimed anywhere.
- Q14/Q15/Q18 (novel datasets) stay NA: every prompt set is drawn from an existing
  public benchmark. The judgment rows and stimulus assets that *are* shipped are
  results and stimuli, covered by Q21-Q23, all yes and all present in the zip
  (`code/artifacts/` 284 entries, `code/data/`, `code/conf/`, `code/src/`).

⚠️ **Whether the checklist can still be changed is a portal question.** The board
records an owner ruling that the *edit* form exposes no checklist field (it was on
the initial submission form). The corrected file is ready either way; confirm the
field exists before assuming it can be re-uploaded.
