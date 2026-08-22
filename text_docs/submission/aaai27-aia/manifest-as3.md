# AS-3 — AAAI-27 AI Alignment special track — submission package manifest

Built 2026-08-22. This file is the package's identity: the upload step sends
exactly these files. **Any edit to a listed file invalidates this manifest** —
rebuild that artifact and re-hash.

## The upload set

| File | Channel | Size | SHA-256 |
|---|---|---|---|
| `paper.pdf` | Main submission PDF | 0.47 MB | `18f3fca12d1a180d7ac4b0ba397ce42acb69f4e6c71ed3bd294814dc609550cb` |
| `supplementary.pdf` | Supplementary Document | 0.60 MB | `3f0d6d29ea6ec50fbb8c12139a3e49134951c5b8d73dbe4fbe219b642a5fc963` |
| `supplementary_code_and_data.zip` | Code and Data Supplement | 6.62 MB | `1435d4c19b1088cd5a0b4aa64468c9fe8098196a5ed62b4d7bb850d4860f8906` |

Source tree: `paper/as-3/aaai_2027_ai_alignment/`. Repo HEAD at packaging:
`46fca14`. ⚠️ `paper/` is gitignored, so the repo hash does **not** cover the
paper source; the `.tex` revision history lives only in the `.pre-*` snapshots
beside `paper.tex`.

Rebuild everything with:

```
./paper/as-3/aaai_2027_ai_alignment/aaai_aia_latex/build.sh   # both PDFs + all checks
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
