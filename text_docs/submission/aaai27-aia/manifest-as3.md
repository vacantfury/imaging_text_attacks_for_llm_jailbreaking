# AS-3 — AAAI-27 AI Alignment special track — submission package manifest

Built 2026-08-22. This file is the package's identity: the upload step sends
exactly these files. **Any edit to a listed file invalidates this manifest** —
rebuild that artifact and re-hash.

⚠️ **A rebuild alone invalidates the two PDF hashes, with no edit at all.**
`pdflatex` embeds a build timestamp, so `./build.sh` produces a byte-different
PDF every run (verified 2026-08-22: the same source rebuilt to a different
digest). These hashes therefore identify one specific build, which is the one
sitting on disk now. If you rebuild before uploading, re-hash. The ZIP is
unaffected: `zip -X` strips extra attributes and the builder is deterministic
over an unchanged tree.

## The upload set

| File | Channel | Size | SHA-256 |
|---|---|---|---|
| `paper.pdf` | Main submission PDF | 0.33 MB | `07ae8a3279e57fa6f23a5352eaa2ab83ce48b098fbb468269b0f958383c3a499` |
| `supplementary.pdf` | Supplementary Document | 0.67 MB | `3b872e7b3037bc334ca65030873927b8a91d716b44adaaaaa7b5f4e3b532e8a2` |
| `supplementary_code_and_data.zip` | Code and Data Supplement | 6.63 MB | `c474abc5d83ee3d0e502ed131d46eebad6f60365a6fcc4068141bebf1eef01ae` |
| `ReproducibilityChecklist/ReproducibilityChecklist.pdf` | Reproducibility checklist | 78 KB | `8f61db3987f514eea00939b2b037e6d9bbe967d04bff3d011b85af9b175dbbd8` |

Source tree: `paper/my_papers/as-3/aaai_2027_ai_alignment/`. Repo HEAD at packaging:
`46fca14`. ⚠️ `paper/` is gitignored, so the repo hash does **not** cover the
paper source; the `.tex` revision history lives only in the `.pre-*` snapshots
beside `paper.tex`.

Rebuild everything with:

```
./paper/my_papers/as-3/aaai_2027_ai_alignment/aaai_aia_latex/build.sh   # both PDFs + all checks
python3 scripts/build_code_artifact.py --paper as3            # the code zip
```

## What changed at packaging (2026-08-22)

1. **The supplement's filename was `appendix.tex`.** Renamed to
   `supplementary.tex` / `supplementary.pdf`, matching AS-2/AS-4/AS-7 and the
   owner's correction that this material is supplementary material, not an
   appendix. The document title already said so; the filename did not, and the
   filename is what a chair sees on the upload.
2. **`build.sh` did not exist for AS-3.** Added, modelled on AS-4's (same
   by-name pointer scheme, no `xr`). It is now the only supported entry point.
3. **The code ZIP was hand-rolled** in a scratch directory with no anonymity
   verification. Replaced by the validated builder (`--paper as3`), which
   scrubs and then **greps the built tree** for every forbidden pattern. See the
   next section: it caught four real leaks the hand-rolled ZIP would have
   shipped.

## The `as3` builder profile, and how it differs from its siblings

**It ships no `data/` directory, deliberately.** AS-3's ethics statement says in
the submitted text that benchmark behaviors are not redistributed and that users
obtain them under the benchmarks' own licenses. Shipping
`data/harmbench_prompts.jsonl` the way the AS-4 profile does would make the
paper's own ethics claim false. The package therefore ships the derivation
script for the one dataset we construct (the category-balanced OR-Bench-Hard
draw) and the README names the four files to place. Do not "fix" this by adding
`data/` back.

Otherwise the profile is the house one: 506 files, 10 MB unpacked, all of
`src/`, the full `conf/experiment/autoattack_defense/` preset directory, and the
vendored `llm_utils`. Other papers' analysis modules are dropped rather than
scrubbed.

## What the anonymity verify caught

The verify pass runs over the **built output**, so it catches what no scrub rule
anticipated. On the first `as3` build it aborted on four leaks:

| Leak | Where | Disposition |
|---|---|---|
| `/Users/<name>/...` absolute repo root | `paper_c_cost_table.py`, `paper_c_view_vs_strictness.py` | **fixed in the repo**, not scrubbed: `REPO` is now derived from `__file__`. The hardcoded path was a real defect — the module could not run on any cluster either. |
| `/Users/<name>/.claude/skills/...` | `paper_c_figures.py` | **fixed in the repo**: now `os.environ.get("SCIVIS_SKILL", expanduser(...))`. The import was already guarded by a try/except with a style fallback. |
| cluster account name in a comment | `conf/clusters/xc.yaml` | scrub rule added |

Two further categories were then swept, neither of them author identity but
neither of them things an AAAI reviewer should be reading:

- **Prior-review provenance.** Preset headers cite the review round that
  motivated each experiment by naming the site it was reviewed on. The site name
  is rewritten to "earlier"; review numbers and dates are left intact.
- **Companion-submission aliases.** The repo names its papers twice over
  (`AS-N` and "Paper X"). A **sibling's** alias is rewritten to "a companion
  paper"; the package's **own** alias is left alone, because it is opaque and
  rewriting it broke the surrounding sentences.

⚠️ A first attempt at that sweep rewrote review numbers and every paper alias.
It passed the verify pass and produced "every this paper preset" and a docstring
whose date the regex had eaten. Machine-mangled prose is a worse artifact than
the internal label it replaced. The rules are deliberately narrow now, and the
narrowness is the point.

The sibling packages (AS-2, AS-4, AS-7) were built before these rules existed
and carry the prior-review and alias strings. Their built ZIPs are unaffected
unless rebuilt; rebuilding any of them now picks up the new scrubbing and
changes that package's hash.

## What `build.sh` checks, and two checks that were wrong before they were right

State at packaging: **PACKAGE CLEAN**. Main paper 0 errors, 0 undefined
references, 0 undefined citations, 0 overfull boxes; supplement the same but 5
overfull boxes (counted, not fatal).

- **Cross-document pointers: 25 distinct, 0 missing.** The two documents compile
  separately and the main paper cites supplement sections **by name**, so a
  renamed heading breaks a pointer silently. This check is the only thing that
  catches it.
  ⚠️ Both earlier versions of this check were wrong in opposite directions. A
  looser check matched the section name **anywhere in the file**, including in
  prose, and passed all 25 on evidence that never tested the claim. A stricter
  one required an exact heading match and failed 8 pointers that are correct as
  written, because the paper cites short forms on purpose ("Component Ablation"
  for "Component Ablation, Per Guard"). The check now resolves a pointer as a
  prefix broken at `,`, `:` or ` and `, and against a `\paragraph` title minus
  its trailing period.
- **Double-blind is checked on the PDFs, not the source.** `aaai2027.sty`'s
  `[submission]` option overrides the template's `\author` block, so the
  AAAI-template author text sitting in `paper.tex` is inert while a named author
  in the PDF would be fatal. A source-level check reports a leak that does not
  exist; the PDF check confirms both documents print "Anonymous submission".
- **Orphan floats fail for the main paper, warn for the supplement.** The
  supplement's layout is one-table-per-subsection, so the heading is the
  pointer. All 16 were checked by hand against the prose that discusses them.

## The reproducibility checklist carried three wrong answers

AS-3 had a checklist, but it sat in the retired main-track directory, dated
2026-07-29, and predated the five-guard panel, the balanced benign redraw and the
code-package decision. Copied into the AIA package and corrected:

- **"Does this paper make theoretical contributions?" was `yes`**, and with it
  "Proofs of all novel claims are included: `yes`". Both documents contain
  **zero** theorem, lemma, proposition or proof environments. Now `no`, with the
  seven theory sub-items `NA`.
- **"the method used for setting seeds is described" was `yes`.** We set no
  generation seed: determinism comes from greedy decoding, and SemanticSmooth's
  paraphrase step samples at $T{=}0.7$ per its reference implementation. The
  supplement says so. Now `partial`, which is what the disclosure supports.

The other 28 answers were re-read against the current paper and hold. The
data-appendix answer stays `partial` on purpose: the one dataset this work
constructs is regenerable exactly from a shipped deterministic script, and
shipping the derived file would redistribute the benchmark it draws from.

⚠️ Whether the AIA OpenReview form has a checklist slot is **unverified**, the
same open question AS-4's manifest records. The artifact is ready either way;
walk the form at submit time.

## Post-submission refinement of the supplement (2026-08-22)

**The main paper is SUBMITTED and frozen.** `paper.tex` was not edited in this pass;
after every rebuild the extracted text of `paper.pdf` was diffed against the
submitted text and came back byte-identical. Only the supplement, the code ZIP
and the form entries remain editable, which is what this pass touched.

The supplement had been written against the **pre-condensation** main paper, so
its cross-document pointers had gone stale in ways nothing would have caught at
review time except a reader following them:

| Stale pointer | Reality after the cut | Fix |
|---|---|---|
| "Table~1 of the main paper" ×13, meaning the results grid | condensation made the ladder Table 1 and the grid **Table 2** | repointed to Table~2 |
| "Algorithm~1 of the main paper, line~5" | the algorithm now lives **in the supplement**, and the reguard branch is **line 7**, not 5 | `\ref{alg:amplifier}`, line 7 |
| "Figure~2 of the main paper" | the main paper has **no figures at all** | `\ref{fig:frontier}` (this supplement) |
| "the safety--utility frontier figure in the main paper" | relocated into the supplement | `\ref{fig:frontier}` |
| "the main paper's evidence / leave-one-out / component-ablation table" | all three are supplement tables | `\ref{tab:evidence}`, `\ref{tab:loo}`, `\ref{tab:ablation}` |
| "since Table~1 lists only the mc and +rg columns" | the submitted Table 2 **does** report guard-alone over-refusal | claim corrected |
| ECSO's 26% floor cited to the main table | that table now reports the balanced draw (25.8) | cites the index-order draw the baselines used |

Also fixed: the opening sentence read "This technical this supplement supplements
the main paper", damage from the earlier appendix→supplement rename; the
relocated pipeline figure and algorithm had **no** introducing text, so the
relocated-material section now opens with a lead-in that references both; and all
**five overfull boxes** are gone (four tables wrapped to column width, one
unbreakable module path made breakable). Supplement now builds 0/0/0/0.

**Not done, deliberately:** the supplement carries ~321 dash-line connectors. The
sweep is the highest-risk edit left in the package, it is the surface reviewers
are least obliged to read, and a mechanical pass earlier in this session is what
produced the "this supplement supplements" damage above. Left for an explicit
decision rather than done blind.

**Builder path repair:** the 2026-08-22 restructure moved `paper/<name>/` to
`paper/my_papers/<name>/`, which silently broke the `paper_dir` of **all five**
profiles in `scripts/build_code_artifact.py`. They now resolve either layout via
`_paper_dir()`, so the next move does not break them again.

## Supplement restructured to stand on its own (2026-08-22, second pass)

`paper.tex` untouched; `paper.pdf` still hash-matches the recorded upload. Built
with the new **`build_supp.sh`**, which compiles the supplement ALONE — `build.sh`
would rebuild the submitted PDF for no reason.

**The frozen contract is now enforced, not remembered.** AS-3 does not use `xr`:
the submitted paper cites **14 supplement sections BY NAME**, so renaming a
heading breaks a pointer silently and cannot be fixed on the paper side.
`FROZEN_XREFS.txt` records those 14 names plus what the paper actually contains
(Tables 1-2, Eq. 1, and **no figures and no algorithm**); `check_supp.py` fails
the build on any violation, in both directions.

**Two defects the restructure surfaced:**

1. 🔴 **The bibliography printed on page 28 of 44**, with sixteen more pages of
   content after it, because `\bibliography` sat before the final section in the
   source. Moved to the end; References now print on the last pages.
2. The document carried **two parallel organisations** — a thematic one and a
   20-subsection dump titled *Material Relocated from the Main Text*, a name that
   only means anything to someone who saw the pre-condensation paper. Several of
   its entries duplicated the thematic sections, and one pointed from the
   supplement *at the supplement*.

**What was done:** the relocated section is dissolved. All 20 subsections moved
to the thematic section that owns their topic (setup, results, mechanism,
over-refusal, adaptive, reliability, related work); the pipeline figure and
algorithm became a real *The Pipeline, Diagrammed* subsection; three redundant
adjacent headings were folded into the section that owns the topic; and the
circular pointer now reads "given above".

⚠️ **Nothing was deleted.** The obvious-looking merge — dropping *The Attack
Suite, in Detail* as a duplicate of *The Attack Suite* — was checked first and
refused: the shorter copy carries **five citations and three numbers** the longer
one does not. It was moved and folded, not dropped.

State: 45 pages, 0 errors / 0 undefined refs / 0 undefined citations / 0 overfull,
anonymous, 14/14 frozen names resolving, no duplicate labels, no dangling refs.

## Packaging profile relied on

Same AAAI-27 AIA profile verified for the sibling packages 2026-08-21: the
technical supplement is a **separate PDF**, reviewers are **not obliged** to
consult it (so the main paper stands alone), **web links in supplementary are
prohibited** (so code ships as this ZIP and no anonymous-repo link appears in
either PDF), and double-blind binds the supplement too.

## Not done

- The main text carries ~150 em-dash connectors and the supplement more. Five of
  the worst-offending sentences were split; the rest are untouched pending the
  owner's word, since converting them wholesale changes the register of a
  submission-ready paper.
- Three InternVL3 guard cells of the identification factorial (wildguard,
  qwen3guard, thinkguard) were cancelled and never ran. The paper does not claim
  them.
