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
