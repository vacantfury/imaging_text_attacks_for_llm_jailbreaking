# AAAI-27 submission facts — venue reference for the Paper B / Paper C route decision

*Compiled 2026-07-13 from the official AAAI-27 pages (see Sources); **AAAI Phase-1 rejection date, the full ARR August 2026 (EACL 2027) cycle timeline, and the review-milestone withdrawal checkpoints added 2026-07-19 from the owner-provided official calendars.** Shared across papers (Paper B/C/D/E submission timeline = TODO item 1; Paper C = item 4; Paper D = item 7; Paper E = item 8). This is the reference the AAAI-vs-EACL routing + review-milestone withdrawal decisions turn on.*

## Conference
- **AAAI-27** = 41st AAAI Conference on Artificial Intelligence, **Montréal, Canada, Feb 16–23, 2027**.

## Deadlines (main technical track; all 11:59 PM UTC-12 / AoE)
| Milestone | Date |
|---|---|
| OpenReview opens — author registration | June 17, 2026 |
| OpenReview opens — paper submission | June 30, 2026 |
| Abstract (title + abstract) | **July 21, 2026** |
| Full paper | **July 28, 2026** |
| Supplementary material & code | July 31, 2026 |
| **Phase 1 rejection notification** ⚖️ | **Sept 24, 2026** |
| Author feedback window (reviews released + response) ⚖️ | Oct 19–25, 2026 |
| Final notification | Nov 30, 2026 |
| Camera-ready | Dec 14, 2026 |

The abstract deadline (7/21) is a **hard wall with no paper attached yet** — you must register title + abstract by 7/21 to be allowed to upload the paper on 7/28.

**AAAI-27 runs a two-phase review with an early cull:** the **Phase 1 rejection notice (Sept 24)** removes a batch of papers before the author feedback window — a paper either survives into Oct 19–25 (reviews out + author response) or is culled here. ⚖️ = a withdrawal / redirect decision point (see §Withdrawal / redirect decision points at review milestones).

## Format
- AAAI two-column camera-ready style (**AAAI-27 Author Kit**), high-resolution PDF, US Letter (8.5″×11″), Type 1 / TrueType fonts.
- **Page limit: 7 pages of main technical content, 9 pages max total** — pages 8–9 are for **references only** (reproducibility checklist allowed beyond that). This is tighter than an ACL/ARR long paper (8 pages content), so a Paper-B port would need trimming.
- **Double-blind**: submissions are anonymous; remove all author/affiliation info.

## Main-track review criteria (verbatim from the AAAI-27 main-track call, captured 2026-07-30)
- *"All submissions will be evaluated and scored for the **significance and novelty** of the contributions (research problems or questions addressed, methods, experiments, analyses), **theoretical and/or empirical soundness** of the claims, their **relevance to the AAAI community**, and **clarity of exposition."*** Plus responsible-research practices and *"steps to ensure **reproducibility** of research results."*
- Contribution types admitted: *"theoretical, methodological, algorithmic, empirical, integrative (connecting ideas and methods across disparate subfields of AI), or critical."*
- **Two-phase process detail:** Phase 1 = at least two human reviews **plus one AI-generated supplementary review** (non-decisional); papers surviving into Phase 2 get additional human reviews + the author response window. (Compare the AIA rubric in §AI Alignment special track — AIA's four criteria replace significance-to-the-AAAI-community with relevance-to-alignment, make "new perspective/analysis" first-class novelty, and add the engagement-with-alignment-literature criterion.)

## Policies that bear on the Paper B decision
- **Dual / concurrent submission — the load-bearing constraint:** *"AAAI-27 does not permit simultaneous submission of papers involving an overlapping set of authors that do not constitute distinct scientific contributions, whether submitted to AAAI-27 or another archival conference or journal."* → **A paper currently under ARR review must be WITHDRAWN from ARR before it can be submitted to AAAI-27.** (ARR is an archival review process.)
- **Author submission cap:** ≤10 AAAI-27 submissions per author, combined across the main track + AI Alignment + AI for Social Impact special tracks. Not binding for us (we'd submit ≤2).
- **No transfer between main track and special tracks** (stated for AAAI-25/26; assume it still holds — you pick the track at submission, no post-hoc move).

## Preprint / arXiv policy — when each paper may go on arXiv (verified 2026-07-13)
Governs TODO item 1 ⑦ (the arXiv-posting step). The two venues differ:
- **ARR (EMNLP/EACL route):** ACL removed the fixed anonymity period on **2024-02-15** — a non-anonymous preprint is allowed at any time, the OpenReview submission just stays anonymized. At submission you pick a **preprint-status** option; the **binding "no non-anonymous preprint"** choice grants ARR **award eligibility + priority on borderline acceptance decisions**, and commits you to *"not preprinting until the metareviews are released, under the penalty of desk rejection."* The cutoff is **meta-review, NOT acceptance** — so the optimal play is: *choose binding → post arXiv right after that cycle's meta-review.* The earned benefit survives (it rewards the clean anonymous review) and the preprint still precedes final acceptance. Meta-review dates: **May cycle = 7/30**; **August cycle ≈ October**. ⚠️ A paper's preprint-status choice is fixed at submission — **Paper B's May-cycle choice is already locked** (check OpenReview → the submission's preprint field to see what was selected).
- **AAAI-27:** preprints are permitted, but the two artifacts must stay **disconnected** — *"the AAAI-27 submission should not include citations or pointers to the non-anonymous material and the non-anonymous online material should not reference the fact that the work was submitted to AAAI-27; violations may lead to summary rejection."* So an AAAI-routed paper can go on arXiv **right after the 7/28 submission**, as long as the arXiv version doesn't name AAAI and the AAAI PDF doesn't cite the arXiv.
- **arXiv version always links the REAL public repo** (`github.com/…/imaging_text_attacks_for_llm_jailbreaking`), never the blind review mirror (`blind-submission1111/…`, which expires); the anonymized submission keeps the blind repo. The repo is already public under the author's name (project policy), so linking it on arXiv adds no de-anonymization beyond the named preprint itself.
- Sources: ARR anonymity policy (aclrollingreview.org/anonymity + the CFP preprint clause); AAAI-27 submission instructions.

## AI Alignment special track (relevant because both our papers fit it)
- **Exists at AAAI-27** (one of two special tracks, alongside AI for Social Impact). Special-track papers are **reviewed under a different rubric than the main track.**
- **Scope (AAAI-27):** scalable oversight, mechanistic interpretability, **empirical robustness evaluation, red-teaming**, human cognitive/psychological factors, safe-by-design engineering incl. formal safety cases; plus governance, human-centered evaluation, and pluralistic coordination.
  - Robustness/security is explicitly in scope: *"How do we create AI systems that work well in new or adversarial environments, including scenarios where a malicious actor is intentionally attempting to misuse the system?"* → **jailbreak attacks + defenses fit squarely.**
  - Evaluation is explicitly in scope: *"How can we evaluate the safety of models and the effectiveness of various alignment techniques?"*
  - *"Papers that release open datasets, reproducible code, or practical evaluation tools are especially encouraged."* → our released pipeline is a plus here.
- **Review rubric (4 criteria, differs from main track):**
  1. **Relevance to AI Alignment** — does it address a problem central to safe/secure AI?
  2. **Engagement with existing literature** (the alignment field).
  3. **Methodological or analysis novelty.**
  4. **Quality of evaluation.**
- **Mutually exclusive with the main track — CONFIRMED (per the prior-year AIA calls, pattern holds):** *"There will be no transfer of papers between the AAAI main track and the AI Alignment track; therefore, authors will need to decide to which track they want to submit their paper."* (AAAI-26 AIA call.) → you pick ONE track per paper at submission; there is **no post-hoc move** and **no dual-track hedge**. A paper is submitted via the regular AAAI procedure but the author selects the AIA special track. The per-author cap (≤10) is **shared** across main + AISI + AIA (not binding for us).
- **Archival — same AAAI proceedings:** AIA special-track papers appear in the AAAI proceedings (AAAI-26 AIA = *Proc. AAAI* Vol. 40 No. 44) → **equal prestige to the main track**, no rep loss from choosing AIA.
- **Track-specific timeline — RELEASED (captured 2026-07-29 from the live AIA page; supersedes the TBA status of the 07-20→07-28 checks).** All deadlines 11:59 PM UTC-12 / AoE:

| Milestone | Date |
|---|---|
| Abstract | **Aug 14, 2026** |
| Full paper | **Aug 21, 2026** |
| Supplementary material & code | Aug 24, 2026 |
| Author feedback window ⚖️ | Oct 27 – Nov 2, 2026 |
| Final notification | Nov 30, 2026 |
| Camera-ready | Dec 14, 2026 |

  - **Still pending on the page as of 2026-07-29:** the CFP text proper (*"The Call for Papers and the complete submission timeline will be announced shortly"*) — so the AIA-27 page limit, rubric confirmation, and submission instructions are NOT yet published — and the **separate AIA submission site is still NOT open**. Keep the watch until both land.
  - **No Phase-1 rejection milestone is listed for AIA** (the main track culls Sept 24) — the AIA timeline goes straight to the author feedback window (Oct 27–Nov 2, one week LATER than main's Oct 19–25). Whether AIA runs single-phase review is unconfirmed until the CFP text lands.
  - **The same-cycle withdrawal question is STILL unanswered:** nothing on the page says whether a paper WITHDRAWN from the AAAI-27 main track may be freshly submitted to AIA in the same cycle (main ↔ AIA remain mutually exclusive, no transfer). Track chairs: aaai27aialignment@aaai.org (general inquiries: workflowchairs@aaai.zendesk.com) — **ask the chairs BEFORE withdrawing anything**; withdrawal from the main track is irreversible per paper.
  - **Decision-clock consequences** (recorded in TODO item 1): the C/D withdraw-from-main-for-AIA decision lands ~2 days before the **8/14** AIA abstract wall (~8/12), gated on the chairs' answer + CFP text + site opening. **Paper B's real fork is EARLIER — the 8/2 EMNLP-commit wall:** committing B to EMNLP forecloses AIA (B would still be under EMNLP consideration at the 8/14 abstract / 8/21 paper deadlines → dual submission), so B's commit-vs-AIA call happens at 8/2 with the 7/30 meta-review in hand. Per the recorded ④ exception, B is review-complete after the meta-review → no ARR withdrawal needed for an AIA submission (re-verify that reading at decision time).

## Fit read (my assessment, not a decision)
- **Papers B, C and D are all robustness / red-teaming / safety-evaluation work** → strong fit for the AI Alignment track, arguably a *better* home than the main track: criterion 1 (relevance to alignment) rewards the framing, and the "open code/eval tools encouraged" note matches our released pipeline. The tighter page budget (7 vs 8) is the main format cost.
- **VERIFIED against the AAAI-26 AIA proceedings (2026-07-30; *Proc. AAAI* Vol. 40 No. 44, ~105 papers): the jailbreak/security literature IS this track's field literature.** ~13 accepted papers are exactly this genre, **including pure attack papers** — MetaCipher (cipher jailbreaks), STACK (attacks on safeguard pipelines), Multi-Faceted Attack (suffix optimization against defense-equipped VLMs, also our §4 limitations cite). Consequence: **no big alignment reframe is needed for an AIA submission** (an earlier session over-estimated this and the owner corrected it twice on 07-30 — "you understand AI alignment too narrowly"). The real cost is a **light criterion pass per paper, ~a day each**: add explicit criterion-1 sentences (the safe/secure-AI stakes) and a criterion-4 sentence (what the paper teaches about *evaluating safeguards*). Everything else in the 8/14→8/21 window goes to strengthening, not repositioning.
- **Per-paper criterion read (2026-07-30 session comparison, recommendation only):** **C** — decode-gap coverage ceiling is a safeguard-evaluation result, fits all four criteria directly. **D** — attack-primary, and red-teaming is named verbatim in the scope; c3 carries method *and* analysis novelty, and Round 7's defense-evaluation findings (SemanticSmooth is counterproductive under best-of-N; surface-noise BoN under-measures safeguard robustness) carry c4 as a safeguard-evaluation lesson. A first pass wrongly concluded "D stays main" by judging D's *current* form rather than its best-refined form — see the comparison-frame rule in memory (`feedback_compare_best_refined_form_for_track_calls`).
- **Unknown that no amount of reading fixes:** the AIA track's acceptance rate is not public for any year (`knowledge/aaai_ai_alignment_track_acceptance_rate.md`), so track choice cannot be optimized on odds — only on fit and on the timeline mechanics above.
- **The Paper B timing bind is the real issue, not fit:** sending Paper B to AAAI means **withdrawing from ARR first** (irreversible — no un-withdraw), and the **7/21 abstract wall lands BEFORE the 7/30 meta-reviews and the 8/2 EMNLP/AACL commit**. So an AAAI-B route forces the withdraw call on **raw scores + whatever discussion signal exists by ~7/20**, giving up the ARR meta-review information. Current standing decision (TODO item 1 timeline, owner leans NOT to withdraw) already reflects this; the decision is revisited at the **2026-07-19 checkpoint** (see the abstract-placeholder tactic below — the binding wall is actually 7/28, but still pre-meta-review). This doc is the fact base for that checkpoint.

## ARR May 2026 cycle timeline (Paper B's current process)
Paper B is under review in the ARR **May 2026** cycle (feeds EMNLP 2026 + AACL 2026). *(Discussion-close through meta-review-start updated 2026-07-13 from the ARR program-chairs timeline email — see the note below the table.)*
| Milestone | Date (AoE) |
|---|---|
| Submission | May 25, 2026 |
| Author-Reviewer discussion window | July 8 – **July 15** (extended +1 day from 7/14) |
| Reviewers finalize reviews | July 16 – 17 |
| **Authors submit Review Issue Reports** | **by July 17** |
| Meta-reviewing period begins | July 18, 2026 |
| Meta-reviews released | **July 30, 2026** |
| Commitment deadline (EMNLP & AACL, same) | **August 2, 2026** |
| Acceptance notification | August 20, 2026 |
| Camera-ready (EMNLP long & short) | **August 30, 2026** |
| EMNLP 2026 main conference | **October 24–29, 2026** (Workshops/Tutorials TBD) |

*(EMNLP camera-ready + main-conference dates owner-provided 2026-07-19 — the ARR-May cycle feeds EMNLP, so these are Paper B's post-acceptance dates.)*

**ARR timeline-email details (2026-07-13):**
- **Discussion extended one day to July 15 AoE.** When it closes, reviewers re-check the forum for author responses and are asked to update assessments if a listed major weakness was sufficiently addressed or rested on a misunderstanding that a clarification resolved. Authors may point reviewers to the [ARR review guidelines](https://aclrollingreview.org/reviewerguidelines) in discussion; a well-justified guideline issue should prompt a review update.
- **Review Issue Report — NEW author deliverable, due July 17 AoE.** A new kind of "official comment" on a review, filed in the OpenReview interface. Authors flag if a review seems seriously amiss. It (a) informs the AC's decision and (b) is analyzed program-wide for the quality distribution of peer reviews (feeding ARR process design). Details + screenshots: https://aclrollingreview.org/authors#step2.2. This is a companion lever to the discussion engagement — use it where a review genuinely departs from the guidelines, not routinely.
- **Revised review form.** Now includes an **excitement score** = a reviewer's personal preference, which *may not* be backed by the review text (so it can't be challenged for lack of textual support). By contrast, **soundness** and **reproducibility** assessments *must* be backed by the review text — these are the dimensions a Review Issue Report can legitimately contest. Formulations of soundness and overall assessment were also revised.

## ARR August 2026 cycle (EACL 2027) timeline
The review route for Papers **C / D / E**, and for **B** if it revise-and-resubmits (TODO item 1 ⑥). Dates from the official EACL-2027 / ARR August-cycle calendar (owner-provided 2026-07-19).
| Milestone | Date (AoE) |
|---|---|
| ARR submission (long & short) | **August 3, 2026** |
| Reviewer registration (all authors) | August 5, 2026 |
| Reviews released | ≈ before Sept 14 (author response opens 9/14) |
| Author response period ⚖️ | Sept 14–19, 2026 |
| Reviewer engagement & author-reviewer discussion ⚖️ | Sept 20–24, 2026 |
| **Meta-review released** ⚖️ | **October 8, 2026** |
| **EACL 2027 commitment deadline** | **October 11, 2026** |
| Acceptance notification (long & short) | November 12, 2026 |
| Camera-ready | November 26, 2026 |
| EACL 2027 main conference | **March 9–14, 2027** (Workshops/Tutorials TBD) |

⚖️ = withdrawal / redirect decision point (see next section).

## Withdrawal / redirect decision points at review milestones (owner 2026-07-19)
Standing rule: at **each review milestone — reviews released, rebuttal/discussion end, meta-review released — reassess the paper's acceptance trajectory and make an explicit stay-vs-exit call**, per venue. The exits differ:
- **ARR August cycle (C/D/E, or B-resubmit):** the clean exit is the commitment stage, NOT a hard withdrawal. (a) reviews out (~9/12) + author response 9/14–19 → read the initial scores; (b) discussion end 9/24 → did reviewers move; (c) **meta-review 10/8 = the decisive signal → the 10/11 commit call:** commit to EACL, OR don't-commit-and **revise-and-resubmit to the next ARR cycle** (no penalty, reviews carry forward — the preferred redirect), OR submit elsewhere. A hard ARR withdrawal (OpenReview trash-can) is irreversible and makes those reviews ineligible for ANY commitment — reserve it for leaving ARR entirely, never as the routine redirect.
- **AAAI-27:** no commit step — straight accept/reject with an early cull. (a) **Phase-1 rejection 9/24** — involuntary; if culled, the paper is free to redirect (a later ARR cycle / other venue / arXiv); if it survives, continue. (b) **Author feedback 10/19–25** (reviews out + response) — if the reviews clearly point to rejection, consider **withdrawing to redirect sooner** (you cannot submit the same paper elsewhere while it is under AAAI review) rather than waiting for the 11/30 final reject. (c) final notification 11/30 — decision, no choice left.
- **Cross-venue:** a paper lives in EITHER AAAI or the ARR-August cycle, never both (dual-submission) → these are within-venue trajectory calls, EXCEPT the ⑥(b) case where a genuinely-distinct spin-off paper runs its own separate ARR-August track.

## EMNLP vs AACL — the choice was LOCKED at submission (May), not deferrable to commitment
**Key finding (2026-07-13): the EMNLP-vs-AACL choice is single-select and was made at ARR submission in May — you CANNOT switch at commitment time.** Both venues carry the identical, symmetric gate:
- **EMNLP CFP (verbatim):** *"authors will need to explicitly declare which conference they intend to commit to at submission time. This choice will be binding for EMNLP 2026: i.e., ARR 2026 May submissions that do not select EMNLP 2026 during submission will not be able to commit to EMNLP 2026."*
- **AACL CFP (verbatim):** *"ARR 2026 May submissions that do not select AACL 2026 during submission will not be able to commit to AACL 2026."*
- The wording is *"which conference"* (**singular**) → exactly **one** venue was selected in May. The one you did NOT select, you **cannot** commit to now.

**Paper B selected EMNLP at submission (owner-confirmed 2026-07-13)** → it is **locked to EMNLP** on the ARR path and **cannot switch to AACL**. The commitment step (deadline **Aug 2, 2026**; AACL acceptance notification Sept 7 vs EMNLP Aug 20) is only where you *finalize* the EMNLP commit — not a second chance to pick the venue.

This whole question is **moot if Paper B is withdrawn for AAAI.**

## AAAI abstract-placeholder tactic (holds the AAAI option at ~zero cost)
- **Registering the AAAI abstract is a free, non-binding placeholder** — title + abstract + authors only, no obligation to submit the full paper. An abstract registration is **not** a paper "under review," so it does **not** trigger the dual-submission conflict. Paper B can stay in ARR meanwhile. **DO THE ABSTRACT SUBMISSIONS ON 7/20, not 7/21 (owner rule 2026-07-19): decide which papers get an abstract AND register them on 7/20 — a one-day buffer before the hard 7/21 wall, never slip to deadline day.**
- The dual-submission conflict triggers only when the **same full paper is under review at two archival venues at once** — i.e. when the AAAI full paper is submitted on **7/28**. So: make the *binding* AAAI-vs-ARR call by **7/28**; if going AAAI, **withdraw from ARR first, then submit the AAAI full paper**; if staying ARR, just let the AAAI abstract lapse.
- **Net:** the placeholder extends the AAAI decision runway from 7/21 to ~7/28 at no cost. **But 7/28 is still before the 7/30 ARR meta-reviews** — the tactic does *not* buy meta-review visibility. Choosing AAAI always means deciding pre-meta-review.
- Verify once (owner or session): confirm AAAI's submission instructions don't treat abstract registration *itself* as a binding "submission" under the dual-submission policy — standard practice is that it does not, but worth a glance.

## ARR withdrawal & resubmission mechanics (Paper B)
- **Withdrawal is immediate** (OpenReview → select submission → trash-can icon). Dual-submission restrictions lift at once, so a same-day *withdraw → submit to AAAI* is fine — no latency.
- **Withdrawal is permanent/irreversible:** *"any earlier reviewed versions also become ineligible for commitment"* — once you withdraw you can no longer commit those reviews to EMNLP. Only withdraw when the AAAI decision is locked; there is **no path back to EMNLP** after withdrawal.
- **The EACL-2027 route is NOT a withdrawal — it's revise-and-resubmit.** ARR: *"If you can see ways to markedly improve your paper… consider revising it and resubmitting to a subsequent ARR review cycle"* — a distinct process needing no withdrawal, with **no penalty**; the May reviews carry forward into the August cycle. (The 48-hour rule — withdrawing >48h after the submission deadline blocks *ARR resubmission* in the next cycle — therefore does **not** bite the EACL route, since that route is a resubmit, not a withdrawal.)
- **After the meta-review (7/30) the paper is free:** *"Your paper's review is considered complete as soon as you receive the meta-review, and you are free to commit it to a venue that accepts ARR reviews, submit it to some other venue, or resubmit it to ARR in the next cycle."* → once 7/30 passes, B can go to AAAI/EACL/EMNLP with no withdrawal needed. But the **AAAI full-paper deadline (7/28) precedes 7/30**, so for the AAAI route you'll normally still be pre-meta-review and must withdraw first — unless the meta-review is early (the reason step ④ checks on 7/26).

## Sources
- [AAAI-27 Main Technical Track Call](https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/)
- [AAAI-27 Submission Instructions](https://aaai.org/conference/aaai/aaai-27/submission-instructions/)
- [AAAI-27 conference home](https://aaai.org/conference/aaai/aaai-27/)
- AI Alignment track scope confirmed via AAAI-27 search results + prior-year calls ([AAAI-26 AI Alignment call](https://aaai.org/conference/aaai/aaai-26/aia-call/), [AAAI-25 AI Alignment call](https://aaai.org/conference/aaai/aaai-25/ai-alignment-call/)) — AAAI-27's own AI Alignment CFP page pending.
