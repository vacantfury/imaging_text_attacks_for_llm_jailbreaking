# AAAI-27 submission facts — venue reference for the Paper B / Paper C route decision

*Compiled 2026-07-13 from the official AAAI-27 pages (see Sources). Shared across papers (Paper B route decision = TODO item 5; Paper C = TODO item 6). This is the reference the "withdraw Paper B from ARR → submit to AAAI?" question turns on.*

## Conference
- **AAAI-27** = 41st AAAI Conference on Artificial Intelligence, **Montréal, Canada, Feb 16–23, 2027**.

## Deadlines (main technical track; all 11:59 PM UTC-12 / AoE)
| Milestone | Date |
|---|---|
| Abstract (title + abstract) | **July 21, 2026** |
| Full paper | **July 28, 2026** |
| Supplementary material & code | July 31, 2026 |
| Author response / rebuttal window | Oct 19–25, 2026 |
| Final notification | Nov 30, 2026 |
| Camera-ready | Dec 14, 2026 |

The abstract deadline (7/21) is a **hard wall with no paper attached yet** — you must register title + abstract by 7/21 to be allowed to upload the paper on 7/28.

## Format
- AAAI two-column camera-ready style (**AAAI-27 Author Kit**), high-resolution PDF, US Letter (8.5″×11″), Type 1 / TrueType fonts.
- **Page limit: 7 pages of main technical content, 9 pages max total** — pages 8–9 are for **references only** (reproducibility checklist allowed beyond that). This is tighter than an ACL/ARR long paper (8 pages content), so a Paper-B port would need trimming.
- **Double-blind**: submissions are anonymous; remove all author/affiliation info.

## Policies that bear on the Paper B decision
- **Dual / concurrent submission — the load-bearing constraint:** *"AAAI-27 does not permit simultaneous submission of papers involving an overlapping set of authors that do not constitute distinct scientific contributions, whether submitted to AAAI-27 or another archival conference or journal."* → **A paper currently under ARR review must be WITHDRAWN from ARR before it can be submitted to AAAI-27.** (ARR is an archival review process.)
- **Author submission cap:** ≤10 AAAI-27 submissions per author, combined across the main track + AI Alignment + AI for Social Impact special tracks. Not binding for us (we'd submit ≤2).
- **No transfer between main track and special tracks** (stated for AAAI-25/26; assume it still holds — you pick the track at submission, no post-hoc move).

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
- **Track-specific deadline — TO VERIFY:** the dedicated AAAI-27 AI Alignment CFP page is not yet posted/discoverable (as of 2026-07-13). In AAAI-26 the AI Alignment track shared the main-track dates; in AAAI-25 it ran a few days later than main. **Working assumption: same as main (abstract 7/21, paper 7/28); confirm on the AI Alignment CFP page once it goes up.**

## Fit read (my assessment, not a decision)
- **Both Paper B and Paper C are robustness / red-teaming / safety-evaluation work** → strong fit for the AI Alignment track, arguably a *better* home than the main track: criterion 1 (relevance to alignment) rewards the framing, and the "open code/eval tools encouraged" note matches our released pipeline. The tighter page budget (7 vs 8) is the main format cost.
- **The Paper B timing bind is the real issue, not fit:** sending Paper B to AAAI means **withdrawing from ARR first** (irreversible — no un-withdraw), and the **7/21 abstract wall lands BEFORE the 7/30 meta-reviews and the 8/2 EMNLP/AACL commit**. So an AAAI-B route forces the withdraw call on **raw scores + whatever discussion signal exists by ~7/20**, giving up the ARR meta-review information. Current standing decision (TODO item 5, owner leans NOT to withdraw) already reflects this; this doc is the fact base if the lean is revisited before 7/21.

## Sources
- [AAAI-27 Main Technical Track Call](https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/)
- [AAAI-27 Submission Instructions](https://aaai.org/conference/aaai/aaai-27/submission-instructions/)
- [AAAI-27 conference home](https://aaai.org/conference/aaai/aaai-27/)
- AI Alignment track scope confirmed via AAAI-27 search results + prior-year calls ([AAAI-26 AI Alignment call](https://aaai.org/conference/aaai/aaai-26/aia-call/), [AAAI-25 AI Alignment call](https://aaai.org/conference/aaai/aaai-25/ai-alignment-call/)) — AAAI-27's own AI Alignment CFP page pending.
