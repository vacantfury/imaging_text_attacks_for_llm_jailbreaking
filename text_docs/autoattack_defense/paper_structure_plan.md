# Paper C — AAAI-27 structure plan: length budget + main-vs-appendix allocation

*Compiled 2026-07-21. Governs how the Paper-C draft (`paper/autoattack_defense/latex/paper.tex`) is
grown into a competitive AAAI-27 submission and what goes where. Source for AAAI facts:
`text_docs/shared/aaai27_venue_info.md` + the AAAI-27 AuthorKit (`paper/aaai_2027/AuthorKit27/`).*

## 1. AAAI-27 length requirements (the format facts)

- **7 pages of main technical content** — this is the hard budget. It includes **all sections, figures,
  tables, and any "content appendix"**. Everything that argues the paper counts against 7.
- **9 pages maximum total**; **pages 8–9 are for references ONLY** (no body text may spill there).
- **Reproducibility checklist** allowed beyond page 9. AAAI expects one — the AuthorKit ships
  `ReproducibilityChecklist.tex`; we fill it and `\input` it after the references.
- **No per-section length limits.** AAAI sets only the *total* 7-page budget; how we divide it across
  Intro/Method/Experiments is our discretion. (So "length of different sections" = an allocation choice,
  not a venue rule.)
- **US Letter, two-column AAAI style, anonymized** (double-blind). No page-layout hacks (`\vspace`
  tricks around floats, margin changes) — auto-reject risk. An "obviously squeezed" paper is rejected.

## 2. Where content can live — and the AAAI-specific catch (VERIFIED 2026-07-21)

**AAAI is NOT like NeurIPS/ICML/ICLR.** In those venues the appendix is part of the same camera-ready
PDF, unlimited length, and IS published. AAAI is stricter: **"appendix" and "supplementary material" are
different things, and the supplement is NOT published and NOT assembled back into the paper.** Verified
from the AAAI-27 CFP, the AAAI-27 Supplementary-Material page, and a real published example (FigStep,
AAAI-25, ojs.aaai.org/article/view/34568 — proceedings PDF is 9 pp / pp. 23951–23959, no supplement
hosted). Four possible homes:

1. **Main body** (numbered sections 1–N). The load-bearing narrative. **In the 7-page budget. Published.**
2. **Content appendix** (lettered A, B, … via `\appendix`, after the main body, before references).
   *Part of the paper PDF, IS published, but COUNTS toward the 7 pages.* Only used if we overflow — **we
   won't** (§4). Not a free overflow space.
3. **Supplementary Document** — a **SEPARATE PDF**, AAAI-27 deadline **July 31**. Review-time aid ONLY:
   *"reviewers will not be obliged to consult"* it, evaluation is on the main submission, it is **NOT in
   the proceedings and NOT merged into the camera-ready** (the main paper must be *self-contained*). Types:
   Supplementary Document (proofs/derivations/extended results), Media Archive (zip), Code+Data (zip).
   → weak: never put anything a claim *depends on* here. Good for reproducibility backing a reviewer may
   spot-check.
4. **arXiv extended version** — the real home of full appendices *for readers*. AAAI permits arXiv
   preprints (kept disconnected from the anon submission); our repo is public anyway. This is where the
   exhaustive tables/prompts live for anyone who cites us — NOT the AAAI supplement.

**Consequence (the correction to the earlier plan):** because tier 3 is unpublished and optionally-read,
the **main paper must stand alone** — this *reinforces* "expand the main body," and it means our overflow
has two real destinations by purpose: reproducibility a reviewer might check → **Supplementary Document
(July 31)**; full detail for readers → **arXiv extended version**.

## 3. The decision test — main body vs. supplementary

One question per item: **"Does a reviewer need this to BELIEVE the paper's claims?"**

- **Yes → main body.** Because the supplementary is not in proceedings and reviewers may skip it,
  **nothing a headline claim depends on may live only in the appendix.** The core evidence chain — the
  ensemble metric, the amplifier result, the reguard safety–utility ceiling, the second-model
  generalization — is all main-body.
- **No, it's exhaustive backing / re-implementation detail → supplementary.** Full per-cell tables,
  prompt templates, per-attack examples, extended-guard results, judge-validation transcripts.

Corollary tests:
- *Would a re-implementer need it but a believer not?* → supplementary (prompts, hyperparameters, seeds).
- *Is it a summarized claim's full backing?* → summary + representative rows in main, full table in supp.
- *Is it a robustness/ablation a skeptic would demand?* → main if it defends a headline claim, else supp.

## 4. The key finding: the draft is UNDER budget, not over

Current `paper.tex` compiles to **5 pages total** (~4 pages content + ~1 page references) at ~2,150 words,
3 figures, 1 table. **That leaves ~3 pages of content headroom.** A 4-page-content paper reads as
underdeveloped for an AAAI main-track submission. So the primary job is **EXPAND the main body**, and use
the supplementary for genuine overflow — the opposite of a trimming exercise.

## 5. Concrete allocation for Paper C

### Main body — expand to ~6.5–7 content pages
| Section | Now | Plan |
|---|---|---|
| Intro | solid (1 col) | keep; tighten only |
| Related Work | 4 paras | keep; maybe +1–2 sentences on adaptive-eval |
| Threat Model & Evaluation | short | **expand**: enumerate the 11-attack suite (one line each, both channels), define the ensemble metric formally, state datasets/judge |
| Method | short prose | **expand**: a compact algorithm/step box for recover→decode→(reguard); one worked example (encoded prompt → recovered/decoded payload → guard verdict) |
| Experiments | headline numbers only | **expand most**: add the **per-attack diagnostic table** (per-attack ASR × guard × {gb, mc, +rg} — the core evidence, currently only described); add **InternVL3 second-target** results (rejudge running now) as a generalization subsection; keep the 3 figures + reguard table |
| Discussion & Limitations | 1 para | **expand**: the two structural failure modes analyzed; deployment implication (the frontier is the practitioner takeaway); honest single-suite/two-model scope |
| Conclusion | fine | keep |

### Overflow homes — Supplementary Document (July 31, review-only) + arXiv extended (readers)
*Not published/merged — see §2. Reproducibility a reviewer may spot-check → Supplementary Document; the same content, fuller, also goes in the arXiv extended version for readers. Nothing load-bearing lives only here.*
- **Full result tables**: per-attack × per-guard × condition, both models, harmful + benign (the exhaustive backing for the main-body summary + diagnostic table).
- **All 11 attacks**: full description + one rendered/encoded example each.
- **Prompt templates**: recover, decode, reguard, and the gpt-5-mini judge rubrics verbatim.
- **Judge validation**: the WildGuard-as-judge failure analysis (why it over-flags; the 41–68% false-positive measurement) — main body keeps the one-footnote summary, supp holds the evidence.
- **Extended guards**: LlamaGuard-3 / ThinkGuard full numbers (main body foregrounds 3 guards in the table; supp carries all 5).
- **Compute / cost / reproducibility**: models served, cluster, judge call counts, seeds.
- **Reproducibility checklist** (`ReproducibilityChecklist.tex`), after references.

## 6. Order of work
1. (running) InternVL3 rejudge → fold second model into the diagnostic table + a generalization subsection.
2. Build the per-attack diagnostic table (main) from the validated per-attack numbers.
3. Expand Threat Model, Method, Discussion per §5.
4. Draft the supplementary document skeleton; move exhaustive tables/prompts there.
5. Fill the reproducibility checklist.
6. Final length pass: confirm ≤7 content pages, refs on 8–9.
