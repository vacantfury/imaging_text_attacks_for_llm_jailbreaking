# Paper B (AS-2) — restructure draft: title + abstract

Spine settled 2026-08-06: **safety decisions in multimodal pipelines are keyed on
channel and presence, not on content.** One mechanism, three surfaces — the
defense's control flow, the defense's coverage, and the model's own decision
boundary.

Target: AAAI-27 AI Alignment track. Abstract wall 2026-08-14, **target 8/12**.
Paper wall 2026-08-21, **target 8/19**.

---

## Title

**Recommended:**

> Presence, Not Content: Multimodal Guardrails Key on Channel Rather Than Harm

**Alternative** (more conservative, keeps the mechanism in the subtitle):

> Channel-Keyed Safety: How Image Presence Governs Black-Box VLM Defenses

Rejected: anything with "appear to work" / "illusion" — ECSO's 63pp drop is real,
and an over-strong title invites a reviewer to score the paper against a claim we
are not making.

---

## Abstract (draft 1)

Black-box input defenses are the safety layer most hosted vision--language model
(VLM) deployments actually rely on. We show that their safety decisions are
governed by *which channel an input uses and whether an image is present*, rather
than by what the input contains, and we demonstrate this on three independent
surfaces of the same pipeline.

**First, defense control flow.** A caption-mediated defense (ECSO) branches on
image presence: against a text-only encoded jailbreak it is inert by
construction, returning byte-identical responses to the undefended model on all
100 prompts, while the same defense with a content-free blank canvas attached
drops attack success rate (ASR) by up to 63pp. The attacker, not the defender,
decides whether the defense runs at all.

**Second, defense coverage.** A text-transform defense (SAGE) sanitizes the text
channel; attaching an image that renders the payload the text already carries ---
supplying no new information --- restores 26 to 36pp of attack success on two of
four models.

**Third, the model itself.** With no defense in the loop, attaching a blank
canvas to a benign request inflates refusal in proportion to topical sensitivity:
+23 to +51pp on borderline-benign prompts (three of four models), against
$\leq$2pp on genuinely neutral ones (three of four; +13pp on the fourth). This is
a threshold shift, not blanket caution. The same intervention on a *matched*
harmful set lowers ASR by 5 to 18pp. Pricing one against the other, image
presence buys one prevented harmful completion for every 2.8 to 6.8 benign
refusals it creates.

Together these show that apparent multimodal safety gains are modality-conditional
control flow and a spurious-feature threshold shift rather than improved
detection. [OPEN-WEIGHT SENTENCE --- pending AICR 298792.] We evaluate the one
deployable mitigation, gating image attachment on an encoded-input detector: it
recovers the safety gain and removes the benign cost where detector recall is
high ($\sim$100% on code-completion attacks) and collapses where it is not
(12--16% on formal-logic encodings), making detector recall --- not the image ---
the binding constraint. We report this as a characterization of how deployed
defense pipelines decide, not as a defense.

---

## The one parameterized claim

Filled when AICR 298792 lands. Two drafted forms, chosen by the result, NOT by
which reads better:

* **replicates** — "The threshold shift reproduces on three open-weight VLMs
  served with no moderation layer, so it is a property of the models rather than
  of vendor-side filtering."
* **does not replicate** — "The shift does not reproduce on three open-weight
  VLMs served without a moderation layer, localizing it to the commercial serving
  stack; we therefore scope the claim to hosted deployments."

If it splits by axis (benign reproduces, harmful does not), say so directly — that
strengthens the exchange-rate framing rather than weakening it, since it is cost
with no purchase at all.

---

## What the restructure does to the existing paper

Numbers do not change. The verdict does.

| Existing section | Fate |
|---|---|
| §res-pareto, §res-amplification (ECSO+decoy, 63pp) | **Keep, reframe** as surface ① — the defense fires on presence, which is why a blank canvas triggers it |
| §res-redundancy / `tab:bypass` (SAGE +26/+36pp) | **Promote** from ablation to surface ② — currently buried under "Limited additional benefit of SAGE" |
| §res-safety-utility (benign inflation) | **Absorb** into surface ③, replaced by the ladder + symmetry data, which explain it instead of noting it |
| §res-controls (decoy diversity, open-weight, non-symbolic) | Keep as-is; the open-weight run extends it to surface ③ |
| §res-gated (detector gating) | **Keep as the constructive counterweight** — critique, the one fix that partly works, why recall bounds it |
| §res-adaptive, §judge robustness | Keep |
| NEW | Sensitivity ladder + symmetry test + exchange rate (surface ③) |
| NEW | Stacked ECSO+SAGE (AICR 298793) — does covering both channels close the gap |

## Open risks, carried honestly

1. **Harmful-side headroom is small.** Biggest drop is claude 18→0; the rest are
   5–6pp. Frontier models already refuse plain harmful text. State it; do not let
   a reviewer find it.
2. **The exchange rate needs no loss function; "total errors" does.** Report the
   ratio. Do NOT report "1.8–2.6× more total errors" as a headline — it weights a
   benign refusal equal to a harmful completion, which is indefensible.
3. **gemini-2.5-flash is null on both axes.** 3 of 4, never 4 of 4.
4. **ECSO-inert-on-text is faithful to ECSO as published** (caption-then-recheck
   has nothing to caption), so this is a scope property of the method, not an
   implementation bug of ours. Say that explicitly — otherwise it reads as a
   strawman.
5. **Zou et al. (`zou2026understanding`, NeurIPS) is the foil, and it is a GAP,
   not a contradiction.** They use the same blank-image control and argue the
   shift originates in the visual modality itself, but measure only the harmful
   axis and never the benign one. Their harmful-axis direction (toward
   compliance, open-weight) is opposite to ours. Do not claim they contradict us
   on benign refusal — an earlier draft of this record did, wrongly.

---

## Introduction (draft 1)

**¶1 — the deployed safety layer.** Encoded jailbreaks bypass text-side safety
filters by moving harmful intent into out-of-distribution surface forms: symbolic
mathematics, formal logic, code templates, classical languages, semantic
camouflage. The defenses that hosted vision--language model (VLM) deployments
actually run against them are black-box input defenses --- they wrap, rewrite, or
re-inspect the input without touching the weights. Their evaluations report what
they are *for*: attack success rate falls when the defense is on. That number is
read as evidence the defense detects harm.

**¶2 — the claim.** We show it is frequently evidence of something else. Across
five frontier VLMs, three open-weight VLMs, three defenses, and three encoded
attack families, the safety behavior of these pipelines is governed by *which
channel an input arrives on and whether an image is present* --- not by what the
input contains. We demonstrate this on three independent surfaces of the same
pipeline, each of which we can manipulate without changing the harmful content at
all.

**¶3 — surface ①: the defense's control flow.** ECSO, a caption-mediated defense,
branches on image presence. Against a text-only encoded jailbreak it is inert *by
construction*: with no image to caption it returns byte-identical responses to the
undefended model on all 100 prompts. Attach a blank canvas --- an image that
cannot be OCR'd, cannot relate to the request, and carries no information --- and
the same defense drops ASR by up to 63pp. The attacker, not the defender, decides
whether the defense runs. [CONDITIONAL, pending the 4-cell same-encoding test:
and when the image *does* carry the payload, ECSO's protection disappears again
(52$\to$54\%, n.s.) --- a defense triggered by a blank image but not a harmful
one.]

**¶4 — surface ②: the defense's coverage.** SAGE rewrites the text channel.
Attaching an image that renders the payload the text *already carries* ---
supplying no new information to the model --- restores 36pp of attack success on
\texttt{gpt-4o-mini} ($p=2.9\times10^{-11}$, replicated across two independent
collection windows). The obvious remedy is to deploy both defenses, since their
blind spots point in opposite directions. We test it: stacking cuts the
redundant-image arm from 44\% to 24\%, and the gap versus the text arm remains
$+16$pp ($p=0.0004$). Defense-in-depth across modalities helps and does not
suffice.

**¶5 — surface ③: the model itself.** With no defense in the loop, attaching a
blank canvas to a benign request inflates refusal in proportion to topical
sensitivity: $+23$ to $+51$pp on borderline-benign prompts, against $\leq2$pp on
genuinely neutral ones --- a threshold shift, not blanket caution, and one whose
cost lands precisely on medical, legal, security, and harm-reduction traffic. The
same intervention on a *matched* harmful set lowers ASR by 5 to 18pp. Pricing one
against the other, image presence buys one prevented harmful completion for every
2.8 to 6.8 benign refusals it creates.

**¶6 — why this is an alignment question, not an implementation detail.** A safety
layer keyed on a content-free feature is a shortcut, and shortcuts fail in the two
ways shortcuts always fail: they are trivially steerable by anyone who knows the
key, and they mis-generalize to inputs the key does not track. Both failures are
visible here in the same system --- an attacker selects the channel and selects
which defense engages; a benign user asking a medical question pays a refusal for
attaching an image. Because these are the defenses hosted deployments actually
rely on, how much safety they deliver, to whom, and at whose expense is an
empirical alignment question.

**¶7 — what we are not claiming.** We do not claim these defenses never work: the
63pp drop is real, and the detector-gated pipeline we evaluate recovers it
without the benign cost wherever the detector fires. We claim that the mechanism
delivering it is modality-conditional control flow and a spurious-feature
threshold shift rather than improved detection of harm --- which determines how
far it generalizes and how easily it is evaded.

### Contributions

(i) **Three demonstrations that safety here keys on channel and presence, not
content**, each holding harmful content fixed and varying only delivery: a
defense inert on one channel and fully triggered by a blank image on the other; a
defense defeated by an image carrying information the text already supplied; and
a model whose refusal threshold moves tens of points on a blank canvas.
(ii) **The first two-sided price for image presence** --- a sensitivity ladder
isolating who pays the benign cost, a matched-harmful counterpart measuring what
it buys, and the exchange rate between them.
(iii) **A test of the natural remedy**: stacking a text-coverage and an
image-coverage defense narrows the gap without closing it.
(iv) **A live detector-gated deployment** identifying detector recall --- not the
image --- as the binding constraint.

### Positioning note (for related work, not the intro)

Zou et al. (`zou2026understanding`, NeurIPS) use the *same* blank-image control
and argue the shift originates in the visual modality itself rather than image
content --- so our design choice is theirs. Two differences to state precisely and
NOT overclaim: their harmful-axis direction is toward compliance on open-weight
models, opposite to ours; and they never measure the benign axis, so ours is an
**unmeasured gap in the closest prior work, not a contradiction of it**.
