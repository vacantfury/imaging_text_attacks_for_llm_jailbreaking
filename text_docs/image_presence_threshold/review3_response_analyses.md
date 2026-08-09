# AS-2 · cspaper review 3 — re-analyses

## 🔴 BLOCKER: the Anthropic API organization is DISABLED (found 2026-08-09)

Both `claude-sonnet-4-6` cells of AICR job 327869 failed in ~3 seconds with

    400 invalid_request_error — "This organization has been disabled."
    request_id req_011CdrfZgR1cyVNjPNMzBCS6 / req_011Cdrfa8GGswfegZqJuDBJm

**Verified directly, not inferred from the job log:** the key was fetched through the
job's exact injection path (`source ~/.secrets` → `op run --env-file=scripts/op_refs`)
on AICR, is present and well-formed (`sk-ant-api03...`), and a minimal
`/v1/messages` call to `claude-sonnet-4-5` returns the same 400. So this is **not** a
missing key, a preset error, a model-id error, or a cluster problem — it is the
Anthropic account itself.

**Consequence:** every Claude target and Claude judge in this repo is down until the
account is re-enabled in the Anthropic Console. That includes AS-2's largest-effect
target (`claude-sonnet-4-6`, +51pp) and any Claude arm in the sibling papers.

**Fix requires the owner** (billing/account state behind an auth wall). Bedrock is not
a substitute here: it serves Claude Sonnet 5 / Opus 4.8 / Haiku 4.5, not
`claude-sonnet-4-6`, so a Bedrock arm would be a different checkpoint and would not
replicate the published row.

---

## The rest (no new data collection)

Round 3 rated **4 (reject)**, as did rounds 1 and 2. The rating paragraph names four
blockers: serving-stack localization, the "form not content" framing, narrow benchmark
slices, and judge validation. This file records what the FREE re-analyses established
against the first, third and fourth-adjacent items. Everything below is computed from
per-prompt rows already on disk — no target or judge calls were made.

Statistics throughout: `src/analysis/paired_binary.py`, Newcombe (1998) method 10
intervals, exact McNemar p-values.

---

## 0. A method error found and fixed before any of it was used

The first implementation of the interval used the **exact conditional** construction —
condition on the discordant count `m = b + c`, put a Clopper–Pearson interval on
`pi = b/m`, map to `delta = (m/n)(2*pi - 1)`. It is exact conditionally and agrees with
the exact McNemar test by construction, which is why it looked right.

It is wrong as an interval for `delta`: conditioning caps the interval at `± m/n`, and
when a real effect exists `m` is itself the quantity carrying the signal, so the cap
falls below the true value about half the time. **Measured coverage 0.558** at n=100,
true delta=0.05, against a 0.95 nominal.

Three candidates were then coverage-tested against the paired multinomial, 2000 trials
per cell, and the reported method chosen on the measured worst case:

| case | delta | Wald | Newcombe | bootstrap |
|---|---|---|---|---|
| null, high concordance | +0.000 | 0.959 | 0.984 | 0.959 |
| moderate effect | +0.050 | 0.919 | 0.956 | 0.949 |
| large effect | +0.100 | 0.945 | 0.944 | 0.954 |
| small n, null | +0.000 | 0.993 | 0.993 | 0.993 |
| **Table-10 regime** | +0.005 | 0.994 | 0.998 | **0.611** |
| big effect, one-sided | +0.320 | 0.939 | 0.943 | 0.948 |

**Newcombe is what we report** (worst case 0.943). Note the percentile bootstrap —
the intuitive choice — **collapses to 0.611 in exactly the few-discordant regime that
Table 10 lives in**, because most resamples draw zero discordants. Reaching for it
would have been worst precisely where the paper needs it.

---

## 1. Con 4 / Q4 — the benign slice. THE REVIEWER IS RIGHT, AND IT IS WORSE THAN STATED

`prompt_range: [0, 99]` over `data/orbench_benign_hard_prompts.jsonl`. **That file is
grouped by category**, so the 100 prompts carrying the paper's headline benign cost are:

    deception   72
    harassment  28

Two of OR-Bench's ten categories. The paper meanwhile states at **five sites**
(abstract L32, intro L54, setup L129, conclusion L516, ethics L539) that the cost falls
on *"medical, legal, security, harm-reduction"* traffic. **None of those four is in the
sample**; OR-Bench does not carry medical or legal as categories at all.

This is a factual over-claim in the most-read parts of the paper, and it is the same
failure mode as the ratio residue and the post-training over-claim: a phrase repeated
across the paper that no pass ever swept as a *concept*.

### What the two available strata do show (reassuring)

Aggregates reproduce the published numbers exactly (+51 / +34 / +23), which validates
the extraction path. Both categories move on all three models:

| model | stratum | n | text → blank | delta | 95% CI | disc | p |
|---|---|---|---|---|---|---|---|
| claude-sonnet-4-6 | deception | 72 | 12.5 → 65.3 | +52.8 | [+39.2, +63.3] | 39/1 | 7.5e-11 |
| | harassment | 28 | 10.7 → 57.1 | +46.4 | [+25.9, +62.2] | 13/0 | 2.4e-04 |
| | ALL | 100 | 12.0 → 63.0 | +51.0 | [+39.9, +60.1] | 52/1 | 1.2e-14 |
| gpt-4o-mini | deception | 72 | 15.3 → 52.8 | +37.5 | [+25.7, +47.9] | 27/0 | 1.5e-08 |
| | harassment | 28 | 3.6 → 28.6 | +25.0 | [+8.8, +42.8] | 7/0 | 0.0156 |
| | ALL | 100 | 12.0 → 46.0 | +34.0 | [+24.5, +43.0] | 34/0 | 1.2e-10 |
| gemini-2.5-flash-lite | deception | 72 | 11.1 → 29.2 | +18.1 | [+8.4, +28.2] | 14/1 | 9.8e-04 |
| | harassment | 28 | 10.7 → 46.4 | +35.7 | [+17.0, +52.2] | 10/0 | 0.00195 |
| | ALL | 100 | 11.0 → 34.0 | +23.0 | [+14.3, +31.8] | 24/1 | 1.6e-06 |
| gemini-2.5-flash | deception | 72 | 13.9 → 8.3 | −5.6 | [−15.0, +3.4] | 3/7 | 0.344 |
| | harassment | 28 | 21.4 → 25.0 | +3.6 | [−12.4, +19.6] | 3/2 | 1.000 |
| | ALL | 100 | 16.0 → 13.0 | −3.0 | [−10.9, +4.8] | 6/9 | 0.607 |

So the effect is **not** one topic's artifact — it holds in both strata on all three
affected models, and the null model is null in both. Worth noting: flash-lite
**reverses the topic ordering** (harassment > deception) relative to the other two, so
which topic pays most is model-specific.

### The ten-category round — COMPLETE, 6 of 6 cells (2026-08-09)

`topic_stratified_stage1/2`, campaign `paper_b_topic_stratified`. AICR jobs 327863
(renders, exit 0) + 327869 (4 cells, exit 1 — the claude cells died on the Anthropic
blocker above) + 328313 (the two claude cells, exit 0, after the key was rerouted to
the NEU account).

30 prompts × 10 categories, one collection window per model, arms paired per prompt id.
Delta in pp; **bold** = survives BH across all 30 per-category tests.

| category | claude-sonnet-4-6 | gpt-4o-mini | gemini-2.5-flash-lite |
|---|---|---|---|
| deception | 6.7 → 86.7 (**+80.0**) | 20.0 → 63.3 (**+43.3**) | 20.0 → 33.3 (+13.3 n.s.) |
| harassment | 13.3 → 66.7 (**+53.3**) | 10.0 → 33.3 (**+23.3**) | 20.0 → 46.7 (**+26.7**) |
| harmful | 6.7 → 53.3 (**+46.7**) | 23.3 → 76.7 (**+53.3**) | 33.3 → 53.3 (+20.0 n.s.) |
| hate | 10.0 → 66.7 (**+56.7**) | 0.0 → 33.3 (**+33.3**) | 10.0 → 63.3 (**+53.3**) |
| illegal | 6.7 → 60.0 (**+53.3**) | 40.0 → 73.3 (**+33.3**) | 23.3 → 66.7 (**+43.3**) |
| privacy | 3.3 → 53.3 (**+50.0**) | 20.0 → 63.3 (**+43.3**) | 10.0 → 50.0 (**+40.0**) |
| self-harm | 13.3 → 76.7 (**+63.3**) | 13.3 → 40.0 (**+26.7**) | 33.3 → 70.0 (**+36.7**) |
| sexual | 3.3 → 43.3 (**+40.0**) | 0.0 → 26.7 (**+26.7**) | 20.0 → 76.7 (**+56.7**) |
| unethical | 10.0 → 30.0 (+20.0 n.s.) | 16.7 → 60.0 (**+43.3**) | 20.0 → 40.0 (+20.0 n.s.) |
| violence | 20.0 → 80.0 (**+60.0**) | 46.7 → 83.3 (**+36.7**) | 50.0 → 86.7 (**+36.7**) |
| **ALL** | **9.3 → 61.7 (+52.3)** | **19.0 → 55.3 (+36.3)** | **24.0 → 58.7 (+34.7)** |

Aggregates: claude 158/1 discordant, p=4.4e-46; gpt-4o-mini 109/0, p=3.1e-33;
flash-lite 110/6, p=7.6e-26. **BH across all 30 per-category tests: 26 survive**
(the four that do not: claude `unethical` p=0.0703; flash-lite `deception` p=0.219,
`harmful` p=0.0703, `unethical` p=0.0703).

Four things follow.

1. **The effect is broad, not a two-topic artifact.** All **thirty** contrasts are
   POSITIVE and 26 survive correction. Whatever these models key on, it is not
   specific to deception and harassment — it appears in hate, sexual, self-harm,
   violence, illegal, privacy, everything.
2. **The published slice UNDERSTATED the cost on two of three models.** flash-lite's
   borderline-rung number is +23pp on the original slice and **+34.7pp** stratified;
   gpt-4o-mini +34 → +36.3; claude +51 → +52.3 (unchanged within noise). Correcting
   the sampling defect **strengthens** the paper's cost claim rather than deflating
   it — which is the outcome the pre-registered read-out called the second case.
3. **Which topic pays most is model-specific**, and sharply so. claude is worst on
   `deception` (+80pp, 6.7 → 86.7); gpt-4o-mini on `harmful` (+53); flash-lite on
   `sexual` (+57). No shared ordering — consistent with the topic reversal already
   seen in the two-category read, and with the paper's existing finding that the
   carrying axis is a property of the checkpoint.
4. **⚠️ The stage-2 validity gate did NOT pass cleanly, and this is recorded rather
   than quietly dropped.** The preset predicted claude's no-image baseline would land
   near the other stratified baselines (19.0%, 24.0%) and **above** its 12% on the
   original slice. It came in at **9.3%** — below both. Reading per the gate's own
   instruction: claude's baseline over-refusal is *lower* on the broad category mix
   than on the deception/harassment slice, so the strata do differ in base
   sensitivity for claude. The delta is unaffected (paired, within one window) and
   the aggregate is consistent with the published +51, so nothing here is
   invalidated — but the per-category deltas are the quantity to read, not the
   baseline.

**The prose fix is unchanged by the good news:** the paper must name the categories it
actually measured. "medical, legal, security, harm-reduction" are not OR-Bench
categories and were never in any sample.

**One infrastructure fact to carry into the writeup:** the two claude cells were served
through a *different Anthropic account* than every earlier claude number in the paper
(same model id, same provider, same endpoint — an account is not a serving route, so no
confound is expected). Recorded because the paper's own Table 10 is a study of exactly
this class of assumption.

---

## 2. Con 2 / Q1 — the serving-route "equivalence". BOTH SIDES ARE PARTLY WRONG

Data: campaign `paper_b_serving_stack` on **xc**, 8 cells, `gemma-3-12b-it` through a
managed route (Bedrock) vs our own vLLM. Arms mapped by **full source dir**, not step
name — two arms share the step name `ir_blank` and would otherwise be merged.

Positive delta = the managed route refuses more.

| arm | managed | self-hosted | delta | 95% CI | disc | p | ±5pp | ±10pp |
|---|---|---|---|---|---|---|---|---|
| text | 6% | 5% | +1.0 | [−2.5, +5.1] | 1/0 | 1.00 | no | **yes** |
| blank 1024 | 13% | 12% | +1.0 | [−2.2, +4.5] | 1/0 | 1.00 | **yes** | **yes** |
| blank wide | 13% | 12% | +1.0 | [−2.2, +4.5] | 1/0 | 1.00 | **yes** | **yes** |
| caption | 6% | 9% | −3.0 | [−8.0, +1.0] | 0/3 | 0.25 | no | **yes** |

**The paper is wrong** to call this an "equivalence result" on the strength of
p ≥ 0.25. Two of four arms do not establish equivalence at ±5pp.

**The reviewer is also wrong** that the data cannot bound the route contribution. They
can: `delta` is bounded by `m/n` whatever the p-value says, so 1 discordant pair of 100
bounds that arm within a few points. All four arms are **equivalent at ±10pp**, and the
two blank arms at ±5pp.

**Correct statement for the paper:** the route difference is bounded within ±10pp on
all four arms and within ±5pp on both blank arms; the data do not resolve it more
finely. That is a genuine equivalence result and it is much stronger than the prose it
replaces — but it is **not** "nothing measurable".

**The honest cost, which con 1 correctly presses:** a route effect of up to ~8–10pp
cannot be excluded, and `gemma-3-12b-it`'s own presence effect is only +7 to +9pp. So
on the one checkpoint where the route control was run, the bound is **not** comfortably
below the effect it exists to rule out. It does constrain the hosted models' +23 to
+51pp effects — those are far outside a 10pp route bound — but the carrier claim must
be scoped to that, not stated generally.

**Q1's preferred fix is infrastructure-blocked.** A same-checkpoint dual-route
comparison on a large-effect model is not runnable with what is registered:
`qwen3-vl-8b` (our large-effect open model) exists on Bedrock only as the 235B;
pixtral likewise only as Large; `llama-3.2-11b-vision` is on Bedrock but cannot be
self-hosted at all (vLLM removed mllama). Narrowing the claim is the available move,
and Limitations should say why rather than leave it looking unattempted.

---

## 3. Con 7 / Q3 — property claims tested against each other, not just against text

Data: campaign `paper_b_image_property_ablation` on **AICR**, `gemini-2.5-flash-lite`,
11 arms, **exactly one cell per arm** (no rerun ambiguity — checked, not assumed). All
arms come from ONE collection window, which is what makes them mutually comparable; the
reference 1024 white blank is *not* in this campaign, so contrasts against it would
cross windows and are excluded rather than quietly included.

Benjamini–Hochberg across the family (this is the paper's F2, which uses FDR).

| contrast | rates | delta | 95% CI | disc | p | BH |
|---|---|---|---|---|---|---|
| **caption vs size-matched blank** | 68% vs 38% | **+30.0** | [+20.2, +38.7] | 31/1 | 1.5e-08 | **sig** |
| grey vs white (same window) | 47% vs 34% | +13.0 | [+5.3, +20.4] | 15/2 | 0.00235 | **sig** |
| black vs grey | 56% vs 47% | +9.0 | [+2.2, +15.6] | 11/2 | 0.0225 | n.s. |
| 256² vs 512² | 43% vs 34% | +9.0 | [+1.6, +16.2] | 12/3 | 0.0352 | n.s. |
| 256² vs 1536² | 43% vs 35% | +8.0 | [+0.3, +15.5] | 12/4 | 0.0768 | n.s. |
| line drawing vs caption | 64% vs 68% | −4.0 | [−11.2, +3.3] | 5/9 | 0.424 | n.s. |
| JPEG q40 vs q90 | 67% vs 68% | −1.0 | [−6.9, +4.9] | 4/5 | 1.000 | n.s. |
| wide vs tall | 38% vs 39% | −1.0 | [−3.1, +1.1] | 0/1 | 1.000 | n.s. |

Readings:

1. **The reviewer's headline ask survives strongly.** Caption vs a *size-matched* blank
   is +30pp at p=1.5e-08 — image content adds cost far above mere presence, and it is
   not a size artifact.
2. **Colour is real but the specific black-vs-white claim is not carried.** Grey vs
   white survives BH; black vs grey does not. The paper should claim the axis, not the
   pairwise extreme.
3. **Resolution is n.s. on flash-lite.** Consistent with the paper: the resolution axis
   is carried by `qwen3-vl-8b` (replicated across three fills), and the paper already
   says the carrying axis is model-specific. This is confirmation, not a problem.
4. **⚠️ A line drawing costs the same as a caption (−4pp, n.s.).** So the added cost is
   **not** OCR-ability — it is visual structure. Any prose implying the caption's
   readable text is what drives the extra cost is unsupported by our own data and
   should be checked and corrected.

---

---

## 4. INTEGRATED INTO THE PAPER (2026-08-09) — 17pp, 0 errors, 0 undefined refs

Applied in three passes, each with unique-match assertions and a concept-level residue
sweep (never a phrasing sweep — that is what caused three prior misses).

**Pass A, corrections (12 edits).**
- Domain over-claim removed at **six** sites, not the five first counted — the
  Discussion also carried an illustrative "a benign user asking a medical question".
  All now name measured OR-Bench categories.
- Equivalence over-claim rewritten at four sites (abstract, Results, §serving-route,
  table caption): "contributes nothing measurable" → a bounded interval with a
  declared margin, plus the honest note that the ±10pp bound is *not* comfortably
  below gemma's own +7–9pp effect, and that what it does exclude is a route artifact
  behind the hosted models' +23 to +57pp.
- The two quoted property differences now carry direct paired tests.
- Seed contradiction resolved: the harness sets `seed=42` where accepted, but no
  hosted provider honours one, so the field is inert and no bit-for-bit claim is made.

**Pass B, the stratified round.** New `tab:strata` + a paragraph that states the
sampling defect in the paper's own voice rather than quietly reporting the better
number — the same posture the draft already takes on the withdrawn
`gemini-2.5-flash` universal claim, which review 3 named as a credibility pro. The
failed validity gate (claude baseline 9.3%) is written into the caption.

**Pass C, multiplicity.** New families in `paper_b_multiplicity.py`:
- **F8** — 30 stratified per-category tests, BH. The three aggregates are deliberately
  *not* separate entries: they are F1's claim on a better sample, and at p = 4.4e-46 /
  3.1e-33 / 7.6e-26 they clear any correction here by tens of orders of magnitude.
- **F9** — the two direct between-arm property contrasts, Holm, both confirmatory.
- The serving-route entry in `NULL_FAMILIES` restated from "non-rejection" to
  "bounded interval", since correcting a set of intervals is not meaningful.

Totals moved **37 → 69 corrected tests, 7 → 9 families**; global Bonferroni threshold
α/69 = 7.3e-04, **36 of 69 survive**, primary claims survive, `--audit` 0 mismatches.
Appendix counts updated to match.

---

## Two corrections to this file's own earlier entries

1. **§3's "black vs white" was mislabelled.** The first pass compared `bBlack` against
   `bGrey` and against `b512` while describing the latter as "colour, size differs",
   and concluded the paper's colour claim needed narrowing. Wrong: `tab:imgprops`
   shows **all three colour arms are 512²**, so the paper's comparison was
   size-matched all along. The correct direct test is **black vs white +22.0pp, 22/0,
   p=4.8e-07** — which confirms the printed "+22pp" exactly. The claim does not need
   narrowing.
2. **The "cost is visual structure, not OCR" finding is WITHDRAWN.** It rested on
   line-drawing (64%) vs caption (68%), −4pp n.s. But the line drawing is 1189×1418
   and the caption is 1024×141 — an 11× pixel difference — so that contrast does not
   isolate OCR-ability from size and cannot support the conclusion. Nothing was
   written into the paper on its strength. (The paper already handles this correctly
   at §res-threshold for `qwen3-vl-8b`, where the matched-size content contrast is
   reported as an underpowered lead, p=0.15.) Isolating OCR from visual structure
   would need an arm we do not have: a 1024×141 non-text drawing.

---

---

## 5. THE REFRAME: uninformativeness → incoherence (owner-approved 2026-08-09)

Con 3 was the one blocker no experiment could resolve, because the paper was trying to
prove a negative it had no access to. The old spine claimed the models key on a feature
"carrying no information about what is being asked". A black-box study of shipped
models cannot establish that — users plausibly *do* attach images more often in
sensitive settings, so conditioning on attachment could be rational inference. The
constant canvas proves only that it carries no **per-prompt** information within an
arm, which is true by construction and therefore proves less than the title claimed.

**The new spine asks an answerable question instead:** not *is attachment
informative?* but *does the response to attachment behave like a risk policy?* Four
measurements already in the paper say no:

| leg | evidence | measured on |
|---|---|---|
| conditions on non-risk variables | black vs white, same size: **+22.0pp**, 22/0, p=4.8e-07; size axis p=0.0004 | **frontier hosted** + open |
| direction not shared | +35pp / +39pp ASR on pixtral, llava, while tightening on four hosted | **open weak** |
| does not update on evidence | "placeholder, disregard it" removes only 6–12pp of 23–54pp | hosted |
| does not require an image | asserted attachment alone: +33pp, modality word −1pp n.s. | hosted |

The tier split is load-bearing: legs 1/3/4 are measured on the frontier hosted models
and leg 2 on open weak ones, so the escape "the well-aligned models have the rational
prior and the broken ones are just broken" is closed **from both ends**.

The claim becomes strictly weaker and the evidence strictly stronger — the trade a
reviewer who twice named over-claiming as the blocker is asking for. Four findings
that read as scattered ablations become one argument with four legs.

**Edits applied (10, two passes).** Title's vulnerable clause replaced —
*"…Key Refusal on Request Form, Not Content"* → *"…Vision–Language Model Refusal
Responds to Image Presence in Ways Risk Cannot Explain"* (the main title
"The Uncontrolled Variable" survives; it already meant "not a designed policy").
Intro spine rewritten; the concession written into *What we do not claim* where a
reviewer looks for it; contributions (iii) and (iv) re-headed; abstract opening and
close; Discussion; §5 synthesis; Conclusion close.

**Concept sweep, not a phrasing sweep.** Six further sites carried the retired spine.
Four were fixed; **two were correctly qualified already** and deliberately left alone —
`\paragraph{The attached image carries no per-prompt information.}` and the
design-justification at §res-threshold both say *per-prompt*, which is exactly the
defensible form. The verbatim system-message prompts in the appendix are untouched:
they are the strings actually sent, and editing them would falsify the record.

Rebuilt: **18pp, 0 errors, 0 undefined refs.**

---

## Residue

- **Con 1 / Q1 (carrier scope)** — the localization claim is now bounded rather than
  absolute, but the reviewer's preferred fix (dual-route on a large-effect checkpoint)
  stays infrastructure-blocked. Limitations should say why it was not attempted.
- **Con 5 (decoupling as across-model description)** — untouched. The reframe does not
  address it: the "as models improve, the harmful side collapses" trend is still five
  heterogeneous points narrated as a direction, not a controlled analysis.
- **Con 10 (forceful prose / claim table)** — the reviewer asked for an explicit table
  separating what is directly measured, what is supported by controls, and what remains
  hypothesis. The reframe makes that easier to write, and it is not written yet.
- **Six missing references** — via `lit-review-loop`, Phase 0 coverage check by eprint
  id first.
- **Human validation on the primary cells (con 8 / Q2)** — deliberately last, per the
  standing review-handling order.
