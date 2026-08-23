# AS-4 — editorial refinement pass (paper-check, `check` mode)

- **Run** 2026-08-22, on owner order "check main paper and refine". **Interrupted
  mid-pass** when he moved to the AS-2 form; this file is the parked state.
- **Source** `paper/my_papers/as-4/aaai_2027_ai_alignment/aaai_aia_latex/paper.tex`, sha256 prefix `e160328daa220697`. Any edit to that file stales the
  judged findings below; the verified ones name their own evidence and survive.
- **Venue** AAAI-27 AI Alignment. **Status: the main paper is ALREADY SUBMITTED**
  (#205). Nothing here is a submission blocker. It is refinement material for the
  arXiv version and the camera-ready.
- **Method** mechanical passes run locally; judged dimensions from one
  cross-family cold read (Gemini 3.1 Pro, full PDF text, six-dimension rubric).
  A second family (GPT-5) was attempted and returned nothing usable (its response
  hit a length filter) — that half of the cross-family pass is a NAMED DEBT, not
  a pass.

## Verified clean (mechanical, re-runnable)

| Check | Result |
|---|---|
| `build.sh` package check | errors 0, undefined refs 0, undefined cites 0, overfull 0 |
| orphan floats / dangling refs / duplicate labels | none, both documents |
| cross-document supplement pointers | 10 distinct, all resolving |
| `paper_d_claim_check` | 11/11 derived claims found verbatim **in the main paper** |
| debt marks (TODO/TBD/XXX/FIXME) | none |

Note on the claim guard: all 11 probes match `paper.tex` and none match
`supplementary.tex`. That is the right result. It means every claim the paper
derives from its own panels is stated in the self-contained document, which is
what the AAAI self-containment rule requires.

## Finding 1 — "points" names two different quantities (VERIFIED, real)

Table 2's panel headers read `(ctrl. drop 14%)`, `24%`, `12%`, `15%`. These are
**relative** drops, exactly as the caption defines Net, and they are arithmetically
correct:

| target | $T{=}1$ → $T{=}0$ | absolute | relative | header |
|---|---|---|---|---|
| Llama-3.1-8B | 96 → 83 | 13 | 13.54% → 14 | 14% ✓ |
| Gemma-2-9B | 97 → 74 | 23 | 23.71% → 24 | 24% ✓ |
| Qwen2.5-7B | 98 → 86 | 12 | 12.24% → 12 | 12% ✓ |
| Llama-3.3-70B | 95 → 81 | 14 | 14.74% → 15 | 15% ✓ |

**The defect is in the prose, not the table.** The body says the answer channel is
"already costing the control $12$--$24$ **points**". Those are relative
percentages, but everywhere else in the paper "points" means absolute
percentage-points ("costs SAGE $59$, $76$, $82$ and $29$ **points** more than
it costs the control"). One word, two units, inside the same argument, and the two
are being compared to each other. That is the comparison the whole section rests on.

**Why nothing caught it:** `paper_d_claim_check` verifies the NUMBER (12--24) and
the number is right. No guard checks the UNIT WORD attached to a number. That is a
genuine gap in the claim guard, worth a probe class of its own.

**Fix:** say "12--24% of its own coverage" (or restate both quantities in the same
unit). Do NOT change the table; it is correct.

## Finding 2 — Gemini's headline claim is REFUTED, recorded so it is not re-raised

Gemini reported as MUST-FIX: *"You are off by exactly 1 point on three of the four
targets... it destroys trust in the data."* It read the `%` headers as absolute
subtractions of the two printed cells. The caption says "relative collapse", the
headers carry `%`, and the recomputation above confirms all four. **No action.**
Kept here because a future reader will hit the same apparent mismatch.

## Findings 3+ — judged, from the cross-family read, NOT yet triaged

Carried verbatim in intent, not yet accepted or rejected by me:

1. **Numbers with no table in this document.** The undefended-baseline block and
   the gate-vs-transform inversion block are long runs of figures in running prose
   with no table. Under self-containment these are the paragraphs most exposed.
   The block rates 99.8% and 95.6% appear in the abstract and body but in no table.
2. **Title spine vs section order.** The title claim is *Depth, Not Breadth*, and
   its factorial (Table 3) is the LAST result. The middle of the paper is the
   variance-channel material. Gemini proposes reordering so the factorial follows
   the composition table. **This is a story decision, not a copy-edit** — it is the
   owner's call, and it is the main open question from this pass.
3. **Synonym drift.** "code encoding" / "CodeAttack" / "code arm" / "structural
   channel" name one thing; "character search" / "original BoN" / "character arm" /
   "surface noise" / "breadth" name another. Fix by defining two names in Setup and
   using them rigidly.
4. **"Actionable severity" is defined only inside Table 1's caption**, though it is
   a headline metric. Should be defined in prose before first use.
5. **Structural asymmetry in Results:** the composition result (the headline) sits
   in an unnamed block while the two secondary results get named subsections.
6. Wording polish, several sentences quoted in the source read.
7. Bibliography artifacts, e.g. an entry rendering as
   "ArXiv:2605.15598v1, 15 May 2026, arXiv:2605.15598."

## Resume

```
cd "/Users/haoyu/repos/aisafety/llm_guardrail_security"
uv run python -m src.analysis.paper_d_claim_check paper/my_papers/as-4/aaai_2027_ai_alignment/aaai_aia_latex/paper.tex
./paper/my_papers/as-4/aaai_2027_ai_alignment/aaai_aia_latex/build.sh
```

Next actions, in order: (1) apply Finding 1, it is unambiguous; (2) put Finding 3.2
(the reordering) to the owner as a story question; (3) triage Findings 3.1 and 3.3
to 3.7; (4) file the missing claim-guard probe class for unit words.

---

# Supplement refinement pass (same day, after the main paper was confirmed frozen)

The owner's framing: **the main paper is submitted and fixed; every other entry on
#205 is still editable, especially the supplementary document.** That changes what
these findings are worth. A finding about the main paper's prose is dead for this
submission. A finding of the form "a number in the main paper has no home a
reviewer can check" is very much alive, because the supplement is exactly where a
reviewer goes to check, and it can still be re-uploaded.

## What the main paper claims that a reviewer could not check

Tested mechanically: for each load-bearing value quoted in the main paper, does it
appear anywhere in the supplement? Most of Gemini's "orphaned numbers" complaint is
**refuted** — the undefended baselines, the QtFS medians, and the whole gate-versus-
transform inversion block all DO have supplement homes. Gemini could not see them
because it read only the main paper, by design.

Three had no home anywhere: `99.8`, `95.6`, and `+62.3`. Two of those are in the
abstract.

## The 99.8 / 95.6 finding (VERIFIED, and it was a real error)

The main paper says *"SAGE blocks $99.8\%$ of individual draws and still loses 12
behaviors at $N{=}100$ where a gate blocking $95.6\%$ loses 10"*, and the intro
cites `Table~\ref{tab:temperature}` as the home. **Table 2 contains no block rates
at all**; its columns are behaviors broken. So the pointer sent the reader to a
table that cannot confirm the number.

Recomputed from the two pinned cells, 10,000 judged draws each, Gemma-2-9B at $T{=}1$:

| cell | per-draw ASR | non-success (100−ASR) | canned block, exact match | behaviors |
|---|---|---|---|---|
| SAGE | 0.23% | **99.77%** | **0.00%** | 12 |
| gate (guard baseline) | 4.44% | **95.56%** | **92.54%** | 10 |

So both published figures are `100 − per-draw ASR`, not block rates:

1. **SAGE blocks nothing.** It is a transform defense with no canned refusal
   string; every refusal in its cell is the target's own generated text. Its block
   rate in the gate's sense is exactly 0.00%. Calling it a block rate is the
   transform-versus-gate conflation this repo's own CLAUDE.md architecture section
   exists to prevent, and the memory rule "report guard-blocked and target-refused
   separately" names the same trap.
2. **The gate's real block rate is 92.5%, not 95.6%.** The missing three points are
   draws the gate PASSED and the target then declined on its own.

**The argument survives; only the verb is wrong.** Both figures are the same
quantity measured the same way, so the contrast and its direction are sound: the
defense that stops more individual draws loses more behaviors to a repeat attacker.
What the figures cannot support is any claim about screening accuracy, since only
one of the two defenses screens.

**Why nothing caught it.** `paper_d_claim_check` held `GEMMA_BLOCK = {"sage": 99.8,
"guard": 95.6}` as a HARDCODED constant, so the guard "verified" the abstract by
comparing it against a number typed into the guard itself. Circular, and it traced
to no artifact.

## What was done about it, all in editable surfaces

1. **Supplement**: new subsection *"Per-draw stopping rates, and what they do and do
   not count"* plus `tab:blockrate`, in *The Temperature Panel* where the section
   already contrasts per-draw rates against union coverage. It gives 99.8 and 95.6 a
   home, defines them precisely as per-draw non-success, and prints the canned-block
   decomposition beside them. A reviewer who checks now lands on the precise reading
   instead of on a table that lacks the number.
2. **Claim guard**: `recompute_gemma_rates()` now derives both rates from the stored
   draws, cross-checks them against the declared constants, and fails if SAGE ever
   reports a nonzero canned block. Absent outputs report `not-run`, never a silent
   pass. New supplement probes assert the four table values verbatim; negative
   control confirmed (corrupting 95.56 is caught).
3. **`build.sh`**: it counted `Overfull \hbox` only. It now SIZES both hbox and
   vbox, and the verdict gates on anything over 5pt. This immediately exposed a
   34.62646pt vbox overfull on the supplement's first page that had been invisible.

## Open: the baselined vbox overfull

That 34.6pt vbox is **pre-existing** (identical with and without the new section)
and **content-invariant**: unchanged when the opening float is resized 0.92 to 0.55
textwidth, unchanged with the float moved to a float page, and `\raggedbottom` is
already set. It is therefore structural in the title block, not a defect in any
section's text. It is BASELINED in `build.sh` by its exact value, not ignored: a
vbox of any other size, or a second one, still fails. Five gating cases were tested
directly. Remove the baseline once the class-level cause is found.

## Still unaddressed

- `+62.3` (matched-budget gain on the code arm) still has no supplement home. Its
  partner `+3.0` does. Same fix shape as above; not yet done.
- The main paper's "12--24 points" unit collision stands, and cannot be fixed there.
  Worth a sentence in the supplement giving the correct unit, same tactic as the
  block-rate table.
- TL;DR on #205 was registered under the OLD spine ("Defenses that sample their
  safety verdict...") while the paper is now *Depth, Not Breadth*. That field is
  editable and currently mismatches the submitted paper.
