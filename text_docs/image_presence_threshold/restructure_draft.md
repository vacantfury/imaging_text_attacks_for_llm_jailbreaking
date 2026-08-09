# Paper B (AS-2) — post-split spine

**Status: spine REWRITTEN into `paper.tex` on 2026-08-08.** The title, abstract,
introduction and contribution list in the LaTeX source are now the truth; this
file records *what was decided and why*, so the body pass does not re-derive it.

⚠️ **The pre-split content of this file is dead.** It planned a spine —
*"one mechanism, three surfaces"* — that AS-2's own data refuted. Do not restore
it from git; it is preserved only in history.

---

## 1. The settled claim

> Safety-aligned VLMs condition their refusal threshold on whether an image is
> attached — a property of the interface, not of the request. The behaviour is a
> property of **particular aligned checkpoints**, arrives as a discrete change
> at one release (NOT attributed to post-training — see 2.3), scales with the
> amount of uninterpretable visual input, is not neutralised by instructing the
> model to ignore the image (with one checkpoint where the instruction is itself
> the cue — see 2.4), and is paid whether or not there is any harm to prevent.

**Every measurement in this paper is defense-free.** That is the paper's scope
boundary and its control against AS-7 in one sentence: no result here can be
attributed to a guardrail's design, coverage, or evaluation protocol, because
there is no guardrail. State it in the paper (it is in the Scope paragraph now),
not just here — the two papers are concurrent anonymous submissions and neither
may cite the other.

---

## 2. Forks that are now CLOSED

### 2.1 Ratio vs decoupling as the headline quantity → **DECOUPLING**

Settled 2026-08-08 during the spine rewrite; **the ratio was then DROPPED
OUTRIGHT later the same day (owner ruling)** — the first settlement kept it as
"the hosted-model instantiation", the second removed it. The *decoupling* is the
claim and the only claim; the paper now reports the two sides side by side and
never divides them.

**What triggered the second ruling.** The paper quoted `10k paired bootstrap`
confidence intervals, and **no code in this repo produces them.** All six files
in `src/analysis/` that bootstrap (`paper_c_bootstrap_table.py`,
`paper_c_stats.py`, `bon_asr.py`, `paper_c_review19.py`,
`paper_c_evidence_table.py`, `paper_d_figures.py`) belong to Papers C and D;
none touches `image_presence_threshold`, and no file anywhere is named for an
exchange rate. So `[1.9, 4.8]`, `[1.8, 12.5]` and `[3.2, 29.0]` were
unreproducible as published. The fork was: implement it with a stated estimand
and a zero-denominator rule, or drop the quantity. Dropped — the decoupling does
not need a ratio, and a statistic that dissolves exactly where the trend is
strongest is the wrong instrument for that trend.

**What replaced it** (§Results, `The two sides do not move together`): the raw
two-sided comparison on the borderline rung — cost `+51/+34/+23`pp against
benefit `18/5/6` points prevented, for claude / gpt-4o-mini / flash-lite —
plus the explicit statement of why no ratio is computed. The prevalence caveat
and the no-summed-error-count rule were preserved verbatim from the old text.
⚠️ **Do not reintroduce the ratio without writing the code first.**

**RESIDUE FOUND AND REMOVED 2026-08-08** (post-edit consistency audit). The drop
pass rewrote the **Results** section but missed the **abstract** and the
**conclusion**, both of which still quoted the ratio — the abstract including
*"every lower bound at or above 1.8"*, which is one of the very bootstrap
confidence bounds that had no producing code and caused the drop. So the paper
simultaneously said four times in the body *"we deliberately do not compute a
ratio"* and quoted one in its two most-read places, with an unreproducible
statistic surviving in the abstract.

Re-verified before fixing: `grep -rilE "exchange_rate|refusals_per|per_prevented"
src/` returns nothing, and every bootstrapping file under `src/analysis/` belongs
to Paper C or D. Five sites swept in one pass — abstract, intro *"What we do not
claim"* (`the rate should be known` → `the cost should be known`), Discussion vs
`zou2026understanding` (`at what rate` → `set against what it prevents`), and two
in the Conclusion. All replaced with the raw two-sided comparison
(+51/+34/+23pp against 18/5/6 points prevented), which now reads identically in
abstract, intro, results and conclusion. Backup: `paper.tex.pre-ratio-residue`.

🔁 **ROOT CAUSE, third instance this week:** an edit pass that targets *predicted
phrasings* only touches what it predicted. The localization pass missed 2 of 9
sites the same way, and two orphan floats slipped through for the same reason.
**Standing rule for any claim-retraction pass: after editing, grep the CONCEPT
(numbers, synonyms, implied nouns like "rate"/"per") and read every hit — never
trust the edit list as the coverage check.**

**Why the ratio cannot carry the paper:**

* Only `claude-sonnet-4-6`'s rate is well determined (2.8, CI [1.9, 4.8]). The
  others are [1.8, 12.5] and [3.2, 29.0] — consistent with almost anything.
* It is **undefined** on `gemini-2.5-flash` (already excluded) and on
  `qwen3-vl-8b` (2% plain-harmful ASR). Both exclusions happen for the same
  reason: no harmful headroom.
* That reason is not going away. The harmful denominators across our set run
  18 → 14 → 11 → 6 → 2%. **A quantity that becomes undefined precisely as models
  improve cannot be the headline of a paper about deployed models.**

**What the decoupling says instead:** the benign cost does not depend on there
being anything to buy. `qwen3-vl-8b` yields a harmful completion on 2% of plain
harmful requests and still pays a +29pp benign tax.

⚠️ **INTEGRITY GUARD — do not write "the cue buys nothing."** The qwen3-vl
harmful arm is an **underpowered null**, not a demonstrated zero (1 vs 2
discordant pairs). The defensible claim is the *asymmetry across the set*: the
denominator collapses as models improve while the benign cost does not track it
down. The paper states this limitation explicitly in the decoupling paragraph.

### 2.2 Title → **CHANGED 2026-08-08 (owner ruling); the earlier KEPT decision is superseded**

`The Uncontrolled Variable: Safety-Aligned Vision--Language Models Key Refusal on
Request Form, Not Content`

The first settlement kept `The Presence Tax: …Condition Refusal on Image
Attachment Rather Than Harm` on the grounds that the split changed what the paper
*demonstrates*, not what the title *claims*. Three later results falsified that:

1. **"Rather Than Harm" contradicted our own ladder.** Inflation is ≤2pp on
   neutral prompts and +23–51pp on borderline ones, so refusal *is* strongly
   harm-sensitive and the cue shifts a threshold INSIDE that system. The paper
   calls this "a threshold shift, not blanket caution" — the title denied a
   result the paper states on page one.
2. **"Image Attachment" became too narrow** once the placebo ladder found the
   same shape in the TEXT channel (§2.4): asserted attachment with nothing
   attached, +16pp, with the word "image" worth −1pp.
3. **"Tax" over-committed to a priced-cost reading the paper retreated from** —
   the exchange rate was dropped as unreproducible (§2.1), and the sign inverts
   on `pixtral-12b`, where the "tax" pays the attacker 35pp.

The decisive evidence was internal: the body already read *"it is the
uncontrolled variable of our title"* (Results, property-ablation paragraph) while
the title said `Presence Tax`. The prose's sense of the thesis had moved and the
title had not followed; that sentence is now true as written.

⚠️ **The CODENAME stays `Presence Tax`** in `text_docs/shared/papers.md` and the
science `portfolio.md` — codename and title are deliberately allowed to differ.
Do not "fix" either to match the other. (EMNLP/arXiv titles are already-submitted
artifacts and stay untouched.) Backup: `paper.tex.pre-retitle`.


### 2.3 What the generational ladder may claim → **RELEASE, NOT POST-TRAINING**

Settled 2026-08-08 after both cspaper reviewers led with this (R1 con 2, R2 con 1
— the single most-agreed criticism across the two rounds).

**The over-claim.** Seven sites said the effect was "introduced by a specific
round of post-training rather than by the architecture family or by scale". The
ladder compares three SHIPPED checkpoints (`qwen2-vl-7b` → `qwen2.5-vl-7b` →
`qwen3-vl-8b`). Consecutive releases differ in vision encoder, tokenisation and
pretraining corpus **as well as** alignment, so a black-box comparison of three
released models cannot attribute the step to post-training specifically.

**What now stands, and it is still load-bearing:**
* the serving stack is ruled out (same-weights control, at that effect size);
* VLMs-as-such are ruled out (three moderation-free nulls);
* the carrier is **something a downloader receives with the weights**;
* the arrival is a **step, not a gradient** — an observation about releases,
  stated as such.

**What is now explicitly disclaimed:** which *component* of the checkpoint
carries it, post-training included. ⚠️ Do not reintroduce "post-training" as a
cause anywhere. The claim is "the released checkpoint". Backup:
`paper.tex.pre-localization`.

### 2.4 What the `gemini-2.5-flash` +33pp cell means → **ASSERTED ATTACHMENT, NOT AN IMAGE EFFECT**

Settled 2026-08-08. The cell had stood as "the round's most consequential single
observation and also its least understood" since the first round.

**The confound, found in our own design.** The 2x2 (xc 256) read a +21pp "mention"
effect on flash and looked like a dissociation against `qwen3-vl`'s
attachment-driven result. It was not identified: arms A/B carried NO system
message while C/D carried the mention, and `system_message: None` is forwarded as
no system prompt at all (`src/defense/no_defense.py`). So `C - A` confounded the
image mention with the mere existence of a system prompt.

**The placebo ladder (xc 257) decomposed it**, four arms, NO image attached in any:

| rung | added ingredient | refusal | delta |
|---|---|---|---|
| A | *(no system message)* | 14% | — |
| P2 | a bare instruction | 24% | **+10pp** (p=.013) |
| P1 | + "any **file** attached … ignore it" | 40% | **+16pp** (p=.0015) |
| C | *file* → *image* | 39% | **−1pp** (12/13, p=1.0, n.s.) |

**The word "image" is worth nothing** (bounded to <=11pp at 25 discordant pairs).
The effect is being told an attachment exists and should be ignored — while
nothing is attached. Modality-general, and carried by TEXT.

**Consequences, all landed in the paper:**
* the +33pp cell is NOT a presence effect and must never be reported as one;
* "it cannot be instructed away" is scoped to the checkpoints where it was
  measured — on flash the instruction IS the cause;
* the headline is unaffected: the other models were measured with NO system
  message anywhere, and `qwen3-vl`'s +20pp (20/0) holds the system message
  byte-identical on both sides;
* it corroborates the form-not-content frame from a second channel — a request
  property carrying no per-prompt information moves the threshold.

⚠️ **The retracted reading ("flash is mention-driven / a two-cue dissociation")
must not be cited.** `experiment_matrix.md` marks that section superseded.

---

## 2.5 Introduction structure → **THESIS-FORWARD (owner ruling 2026-08-08)**

The intro was eleven paragraphs in RESULTS ORDER, with "why this is an alignment
question" at paragraph 10 of 11 and a contribution list naming four
*measurements*. A reader stopping on page 2 learned that a blank image changes
refusal rates and nothing about why that is alignment rather than trivia.

**Why this was a substantive problem, not a stylistic one.** The paper's own
Discussion states that `zou2026understanding` "use the same blank-image control
we do" — so the MEASUREMENT is not novel in kind. What is ours is the frame plus
the two-sided consequence structure. An intro reading *"we measured a blank-image
effect"* invites "incremental" from any reviewer who knows that work; an intro
reading *"safety acquired a form-keyed shortcut, and here are both ways shortcuts
fail"* makes the same evidence a contribution. Framing is load-bearing for
novelty here.

**The thesis was already written**, at the old paragraph 10: *"Shortcuts fail the
two ways shortcuts always fail: they are steerable by anyone who knows the key,
and they mis-generalise to everything the key does not track. Both failures are
visible here in one manipulation."* The pass PROMOTED it and invented nothing —
same situation as the title (§2.2): the prose knew the thesis, the structure did
not lead with it.

**What changed:** a new `The claim.` paragraph at position 2 (shortcut; two
failure modes; we measure both), a new `Why it goes unmeasured.` paragraph, the
old ¶10 trimmed to consequences + the black-box hedge, and all four contributions
re-headed as CLAIMS rather than measurements. Results, tables and paragraph order
untouched. Backup: `paper.tex.pre-thesis`.

⚠️ **Two guards, both deliberate — do not "strengthen" either:**
1. **The steerable side rests largely on ONE model** (`pixtral`). The opener says
   "we establish it narrowly" and states it qualitatively, so the intro inherits
   the Results section's scoping instead of inflating it. More models before any
   stronger wording.
2. **"no evaluation of its harm judgement will surface it" was retired** — a
   universal negative that invites *"MM-SafetyBench attaches images, wouldn't it
   catch this?"*. Replaced by the precise version: benchmarks vary what the image
   CONTAINS, never whether one is attached with content held fixed, so the shift
   is MISATTRIBUTED to content. Grounded in the 2026-08-08 lit pass — SAVeS runs
   no presence control, HoliSafe's five-way grid has no no-image cell, DUAL-Bench
   perturbs hazard-bearing images.

⚠️ Reviewers did NOT ask for this. R1/R2 were entirely evidentiary (localization,
instance idiosyncrasy, judge, multiplicity, reproducibility — all five closed).
This was a positioning judgment, so do not cite it as a review response.

---

## 3. What the spine now leads with

Ordered as the introduction runs:

1. **The finding** — blank canvas, defense-free, zero per-prompt information.
2. **Threshold shift, not blanket caution** — the ladder; who pays.
3. **Presence sufficient, properties set the price** — 10-arm ablation; on the
   open checkpoint the carrying axis is *size* (p=0.0004), colour and JPEG inert.
4. **Instruction does not neutralise it** — ~3/4 survives on three models;
   `gemini-2.5-flash` inverts +33pp, and the placebo ladder shows that cell is
   an asserted-attachment effect, not an image effect (2.4).
5. **Where the effect lives** *(the new backbone)* — serving stack ruled out
   (same-weights control) → VLMs-as-such ruled out (three nulls) → **particular
   aligned checkpoints**, exhibited on open `qwen3-vl-8b` at +32/+28/+29pp.
   The tier label fails to predict it (four of five models, same label,
   +32 → +0pp).
6. **A step, not a gradient** — qwen2-vl +8 n.s. / qwen2.5-vl +1 / qwen3-vl +28.
   A discrete change at one RELEASE; post-training is not isolated (2.3).
7. **Cost vs benefit, and their decoupling** — §2.1 above.
8. **The sign is not fixed** — pixtral 48→83%.
9. Alignment framing · Scope · What we do not claim · Contributions.

---

## 4. What the body pass still owes the spine

The introduction now promises results the body does not yet contain or
contradicts. In rough dependency order:

1. **Remove the AS-7 sections.** `sec:res-pareto`, `sec:res-amplification`,
   `sec:res-safety-utility`, `sec:res-decoy`, `sec:res-redundancy`,
   `sec:res-stacked`, `sec:res-deployable`, `sec:res-gated`, `sec:res-adaptive`
   — plus their tables, appendices and case studies.
2. **Rewrite `sec:res-threshold`'s open-weight paragraphs.** They currently
   assert the benign cost "does not reproduce" on open-weight models and
   conclude it is "a property of an aligned, moderated serving stack." That is
   false as written — see `experiment_matrix.md`, tier scan (xc 215).
3. **New tables** for: the tier scan, the qwen3-vl property ablation, the
   generational ladder, the qwen3-vl cost/benefit ladder (no ratio — 2.1).
4. **Rewrite `sec:method`.** It still describes an encoded-attack threat model
   with a defender — AS-7's framing. AS-2's manipulation is attachment alone.
5. **Limitations** — the open-weight boundary sentence needs replacing for the
   same reason as (2).
6. **Related work** — `zou2026understanding` is the closest prior work and the
   positioning still holds; re-check it once the body settles.

---

## 5. Files

* Truth: `paper/image_presence_threshold/aaai_2027_ai_alignment/aaai_aia_latex/paper.tex`
* Pre-spine-rewrite backup: `paper.tex.presplit-backup` in the same directory
  (⚠️ `paper/` is **gitignored** — there is no git history for the draft, so that
  file is the only rollback point).
* Measured numbers + integrity notes: `experiment_matrix.md` in this directory.
