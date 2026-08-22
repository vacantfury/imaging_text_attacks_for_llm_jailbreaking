# AS-7 re-spine handoff — lead with the share

**Owner-ratified 2026-08-22.** This supersedes the "read access" spine settled 2026-08-21.
Written from an AS-2 session that did the cross-paper analysis; AS-7 executes it.

**This also RELEASES the hold.** The AS-7 board carried "main/supplementary split is ON
HOLD, the AS-2 session is working the same packaging problem and its opinion comes first."
That opinion is this document. The split is unblocked, but do the re-spine FIRST: splitting
the current body would package a paper that is about to lose several sections.

---

## The decision

Both AS-2 and AS-7 had accumulated material that measures a **different quantity** from the
one their thesis is about. That is what made both drafts unfocused. The test now applied to
every inclusion, in both papers:

> **Does this measure the paper's quantity, or a different one?**
> Same quantity in a supporting role → supplementary. Different quantity → the next paper.

**AS-7 is NOT halved.** An earlier proposal to split it into a channel paper and a grant
paper was considered and rejected. Both the attacker's channel choice and the evaluator's
read choice move **one** number, so they are one paper.

## AS-7's quantity

**The guardrail's own share of the refusals credited to it.**

That is already contribution (i) of the current draft, and the draft already states the
headline:

> **0% / 41–45% / 99%** — three settings that a results table would describe identically.
> Same defense, same targets, same corpus, same judge.

That row is the paper. The attacker's channel choice drives the share to 0. The evaluator's
read choice drives it to 99. Everything else in the draft is either a way of moving that
number, a control on it, or a different paper.

The draft already re-reads its own sections this way: the decoy grid is "the paper's thesis
inside a single defense," and the decoy case is "the sharpest case in the paper" when stated
as attribution. Those sentences were right; the spine had just moved off them.

## Why the spine moves, precisely

"Read access" is a taxonomy of **causes** (deployer / attacker / evaluator), layered on top of
a contribution that was already there. Note this is **neither of the two earlier titles**:

- The first title led with the **instrument** (how the share is computed) — that was the
  reason it was retired, and it was a fair reason.
- The second leads with the **causes**.
- The fix is to lead with the **number**.

So the retitle is not a return to the old spine. Do not restore the old title.

## What the body keeps — five sections

1. **The instrument and the headline.** The decomposition is exact, free and disjoint (guard
   blocks by exact match on the canned string, model refusals by judge, never a prefix or
   similarity heuristic). Then `tab:attribution`, the 0 / 41–45 / 99 table. This section is
   the paper in one table and should read that way.
2. **The attacker drives it to zero.** The channel measurement, harmful and benign
   (`tab:channel`, `tab:channelasr`, and the minimal form of the discrimination grid showing
   the decision is a *constant*, not merely wrong).
3. **The evaluator drives it to 99.** The grant (`tab:deployable`), ordered by read position
   (`tab:readladder`), and isolated inside one defense (`tab:stage`) — including that the
   isolation **refuted our own registered prediction** (the read conditioning the generated
   answer carries it, not the read making the decision). A refuted pre-registration is
   credibility; keep it visible.
4. **The root cause is in released code, not in evaluator judgment.** The reference
   implementation builds all three stages from one prompt field and cannot represent the
   attacker-sent / benchmark-behaviour distinction, plus the audit of four further released
   harnesses and the benchmark itself — including one benchmark shipping both strings as
   adjacent keys, and one harness immune to the grant precisely because it reads the target's
   output rather than a prompt. This is the section that makes the grant a field-level fact
   rather than a straw man. It is currently underweighted relative to how strong it is.
5. **The sharpest single case, and one bound.** The decoy grid read as attribution
   (`tab:main`, compact), plus the bound that a defense can buy its safety by refusing benign
   traffic (the trivial-reject corner at 74–100% benign refusal). The bound stays because
   without it no number in the paper is readable.

To supplementary: `tab:samewindow`, `tab:benefit`, `tab:stagewiring`, judge robustness, the
scope control, the multiplicity material.

## What leaves for AS-8

**AS-8 — Channel Coverage** was founded 2026-08-22 and is registered in
`text_docs/shared/papers.md` and in the science `portfolio.md`. Its proposal, with a full
inheritance manifest, is `text_docs/guard_channel_coverage/proposal.md`. Target venue IEEE
SaTML 2027, full paper 2026-09-29.

It takes everything that **responds** to the finding rather than measuring it:
`sec:res-benign` (router half), `sec:res-coverage` / `sec:res-redundancy`, `sec:res-stacked`,
`sec:res-tradeoff`, tables `tab:router`, `tab:routershare`, `tab:benigncarrier`,
`tab:stacked`, and the mitigations appendix (detector-gated deployment, adaptive attacks).

This is the paper's own boundary being enforced, not a new one. AS-7 already says the
attribution/efficacy distinction is "load-bearing" and that it does not answer efficacy. It
then answers it. AS-8 is that answer.

**Do not delete this material.** It must remain recoverable from git history, and the AS-8
proposal cites it by section and label so it can be found after the re-spine.

## Two calls that are yours to make in the re-spine

1. **The benign carrier grid and the discrimination grid serve both papers.** Default: AS-7
   keeps the *minimal* form that shows the guard's decision is a constant across benign and
   harmful (that is what makes it blindness rather than inaccuracy, and it is load-bearing for
   the share); AS-8 takes the cross-guard calibration comparison. Deviate if the re-spine
   shows the minimal form cannot carry section 2.
2. **How much of the decoy grid survives.** It is the sharpest case but it is also the
   largest table, and its ECSO cells are granted-protocol with a caveat attached. A compact
   form read purely as attribution is probably right.

## Do not

- **Do not halve the paper.** Considered and rejected; both halves move one number.
- **Do not reopen the attribution / efficacy split.** It is ratified and it is why AS-8 exists.
- **Do not make model-level refusal claims.** That is AS-2's and AS-9's territory. Keep the
  existing scope note and the control showing the effects run at full strength on two
  checkpoints whose own threshold does not move — that control is also what carries
  concurrent-submission distinctness against AS-2, so it is not optional.
- **Do not restore the previous title.** See "Why the spine moves" above.
- Public repo: no reviewer text, no personal data, no venue career-weighting in committed files.
