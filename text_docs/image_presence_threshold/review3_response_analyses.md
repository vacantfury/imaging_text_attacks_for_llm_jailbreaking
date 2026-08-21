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

---

## Con 5 — the within-family harmful ladder (xc job 283, 2026-08-09)

**The ask.** Review 3: the collapse/decoupling claim "is primarily an across-model
descriptive pattern, not a controlled trend analysis. Model family, alignment
procedure, benchmark response style, base refusal rate, and judge behavior all vary
simultaneously. A stronger version would evaluate multiple checkpoints within one
family and alignment trajectory."

**What we ran.** One preset, two cells, filling the single missing rung so the
generational ladder has BOTH sides on all three checkpoints. Family, size class,
serving stack (xc, matching the two sibling rungs deliberately), judge
(`gpt-5-mini` + `harmbench` rubric, both pinned) and the upstream renders
(byte-identical, no new stage 1) all held fixed; only the checkpoint moves.

| rung | benign text→blank | Δ | harmful text→blank | Δ | 95% CI |
|---|---|---|---|---|---|
| qwen2-vl-7b (oldest) | 72 → 80 | +8.0 (p=0.057) | 2 → 2 | +0.0 | [−4.5, +4.5] |
| qwen2.5-vl-7b | 37 → 38 | +1.0 (p=1.0) | 4 → 7 | +3.0 | [−2.7, +9.3] |
| qwen3-vl-8b (newest) | 54 → 82 | **+28.0** (p=2.5e−07) | 2 → 1 | −1.0 | [−6.1, +3.7] |

Integrity: `fallback_parse_count: 0` and `total_evaluated: 100` on both new cells;
100/100 ids pair in every rung; campaigns pinned explicitly (a `paper_b_guard_channel`
no-defense text cell at 3.0% exists for qwen3-vl and would have been picked by
latest-wins — it is a different campaign and was excluded).

**Finding 1 — the decoupling survives the control.** At every rung the harmful effect
is a bounded null (all three equivalent to zero within ±10pp, the oldest within ±5pp)
while the benign cost runs +8, +1, +28pp. At the newest rung: +28pp benign against a
harmful effect confined to [−6.1, +3.7]pp. This is the controlled form of the paper's
central claim and it is now what the paper rests on.

**Finding 2 — a CORRECTION to the pre-registered read-out.** The preset recorded, in
advance, that a flat harmful line would mean the "harmful side collapses as models
improve" reading "is NOT supported within a family". **That inference would have been
wrong**, for the reason the repo's own standing rule names: a floored denominator fakes
a null. Plain-text ASR is 2, 4, 2% — the harmful side is already at the floor at the
*oldest* rung, so there is no headroom for a downward trend to be visible. The ladder
is uninformative about the collapse trend in *either* direction; it does not refute it.
Writing up the pre-registered branch verbatim would have manufactured a retraction out
of a power limit.

It does establish a smaller real thing: qwen3-vl's 2% is not a recency effect within
its own family — its two-generation-older sibling is also at 2%.

**Integrated as:** `tab:generational` widened to both sides + caption rewritten; a new
two-paragraph passage in §res-threshold stating what the ladder does and does not
support; intro asymmetry claim upgraded to lead with the control; contribution (i)
restated; Limitations given the explicit headroom bound; reproducibility row dated
08-08/09. Multiplicity: added to `NULL_FAMILIES` (bounds, not non-rejections, so no
correction applies), `--audit` 0 mismatches. Build 18pp, 0 errors, 0 undefined.

---

## Lit round — the "missing references" objection (2026-08-09)

**The ask.** Review 3 listed six references it said the related work should engage.

**Phase 0 found the objection was partly already met.** Two of the six were already in the
master bib. One is instructive: the review cited Chakraborty by its arXiv title
*"Cross-Modal Safety Alignment: Is textual unlearning all you need?"*, but it is filed under
the published EMNLP title *"Can Textual Unlearning Solve Cross-Modality Safety Alignment?"* —
a title-string grep would have missed it and staged a duplicate. Matching on eprint id caught it.

**Four were genuinely missing.** All venues verified against authoritative indexes rather than
assumed, and **three are published papers, not preprints**:

| ref | venue (verified) | note |
|---|---|---|
| `geng2025vscbench` VSCBench | Findings of ACL 2025 | ACL Anthology |
| `zhang2025spavl` SPA-VL | **CVPR 2025**, pp. 19867–19878 | CVF open access; review's year right for the venue, arXiv is 2024 |
| `weng2025adversaryawaredpo` ADPO | Findings of EMNLP 2025 | ACL Anthology |
| `gulati2026narrowfinetuning` | **Lifelong Agent Workshop @ ICLR 2026** | workshop, non-archival — confirmed verbatim from the arXiv Comments field |

The last one was staged conservatively as an unconfirmed preprint; reading the source revealed
an ICLR template with `\iclrfinalcopy` active, and the arXiv Comments field resolved it to a
**workshop** paper. That matters for weighting: it is context, not prior art.

**The one that needed a scoop check: VSCBench.** It is the closest published framing to AS-2's
two-sided accounting — it introduces *safety calibration*, scoring over- and undersafety as two
directions of one axis over 3,600 image–text pairs across 11 VLMs. Checked its dataset
construction directly: its image-centric subset pairs **visually similar images differing in
content**, with an image present in every condition. AS-2 varies **presence** with content
fixed. Orthogonal axes, no scoop — and the distinction is now stated explicitly in the paper,
because it is the cleanest answer to "isn't this just oversafety benchmarking, already done?"

**Integrated as:** review §6.1.1 (new — SPA-VL / ADPO / Gulati, the "where does the policy come
from" cluster) and §6.7 (VSCBench, with the prior-art verdict); CANDIDATE markers dropped on all
four; entries copied into the paper's self-contained `paper.bib` with working notes stripped;
cited in the paper at the taxonomy categories (iii) and (iv), the relation-to-(iv) passage, and
the generational-step discussion. Build 18pp, 0 errors, 0 undefined, all four resolve in the PDF.
Science repo `b63fd1a`.

---

## Con 1 and con 10 — the two writing items (2026-08-09)

**Con 1 — why the serving-route control sits on a small-effect checkpoint.** The reviewer
is right that the ±10pp route bound is not comfortably below `gemma-3-12b-it`'s own +7–9pp
presence effect. The obvious stronger design — route-test a LARGE-effect checkpoint such as
`qwen3-vl-8b` (+28pp) — was not run, and the reason is a real availability constraint, now
verified rather than asserted: the test needs a checkpoint that is simultaneously (a)
vision-capable, (b) offered by a managed commercial host, and (c) small enough to self-serve
on our GPUs. Per the account's live model sweep (devices repo
`knowledge/clusters/xc_bedrock_model_status.md`, 2026-08-07), the vision-capable open-weight
families on the host are gemma-3, llama-4, pixtral-large and qwen3-vl — and only gemma-3
satisfies (c). **`qwen3-vl` is offered only at 235B**, which we cannot self-serve. The
checkpoint we would most want to route-test is unavailable in the one configuration that
would test it. Written into Limitations as a named gap with that reason.

**Con 10 — the claim table.** Added `tab:claims`, immediately before Limitations: every
claim sorted into *measured* (direct paired contrast with intervals), *control-supported*
(rests on a control with a stated bound), and *hypothesis* (consistent with the data, not
established by it). Tier 3 is deliberately non-empty and carries the three readings a reader
might otherwise take from the prose — post-training as the specific cause (releases change
vision encoder and corpus too), the denominator shrinking with recency (across-model only;
our family is floored throughout), and attachment carrying no risk information in real
traffic (explicitly not claimed). Made non-floating so it cannot drift away from Limitations
under later edits, and referenced from the opening of that section.

**Build after both:** 19pp, 0 errors, 0 undefined refs, 0 overfull boxes. All seven review-3
items verified present in the compiled PDF (con 1, 2, 4, 5, 9, 10 + the lit round).

---

## ⚠️ Integrity find — a headline number whose cell had gone unreachable (2026-08-09)

**How it surfaced.** Scoping the cross-family judge round required enumerating the primary
cells. The pixtral sign-inversion pair would not resolve: the text arm was there at 48%,
the blank arm was not.

**What was wrong.** A sweep for `asr is None AND refusal_rate is None` across the whole
output tree found **four cells that collected 100 target responses each and were never
judged** — every row's verdict null, `eval_stats` null. All four from campaign
`paper_b_threshold_shift_openweight` (2026-08-07): one judging pass failed while the
expensive half, the generations, survived intact.

One of them was the **blank arm of the pixtral sign inversion**, which the paper asserted as
`48 → 83% (+35pp, p=3.1e-08)` — one of the four legs of the reframed spine ("its *direction*
is not shared"). No judged pixtral `ir_blank` harmbench cell existed on any of the four
output roots or on AICR, NURC or xc. Checked all before concluding.

The number was never fabricated: `experiment_matrix.md` recorded it with its p-value and
verbatim spot-check quotes from both arms. It was measured on a real cell that a later
re-run superseded — **the "latest-wins cell selection is unsafe" trap, where the newest cell
for a condition is the broken one.** The failure is silent by construction: nothing errors,
the dir just carries no metric.

**Recovery.** Rejudge of the stored responses with the paper's own judge (AICR job 328544,
gpt-5-mini + harmbench rubric, no target queried, ~$0.20). `fallback_parse_count` 0, 100/100
evaluated on every cell.

| cell | recovered | paper asserted |
|---|---|---|
| **pixtral-12b, blank arm (harmful)** | **81.0%** | 83% |
| internvl3-8b, text arm (harmful) | **5.0%** | 5 ✅ exact match |
| internvl3-8b, text arm (JBB benign) | 0.0% refusal | — |

**The claim holds.** Paired against the judged text arm: **48 → 81, +33pp, discordant 37/4,
p=1.03e-07, 95% CI [+21.8, +43.0]pp.** Thirty-seven prompts flip toward harm against four
away. The evidence that this *reproduces* the original judging rather than replacing it is
internvl3's text arm returning **5.0%, matching the recorded 5 exactly**; the 2-point pixtral
gap is the judge nondeterminism band.

**Propagated:** paper.tex at six sites (abstract, intro, reframed spine, results,
`tab:ow_threshold` body + caption, claim table) — 83→81, +35→+33pp, p 3.1e-08→1.0e-07;
`experiment_matrix.md` row corrected with a provenance block; multiplicity registry F-entry
upgraded from a `p_bound` placeholder to exact discordants (37/4), `--audit` 0 mismatches.
Build 19pp, 0 errors, 0 undefined, 0 overfull.

**Left open (does NOT back any paper number):** the 4th unjudged cell,
`qwen2_5_vl_7b … jailbreakbench_benign ir_blank` (campaign
`paper_b_threshold_shift_openweight`). It exists locally but not on AICR, which is why job
328544's 4th task failed. The paper's qwen2.5-vl rung-3 figures come from
`paper_b_generational_ladder` (37→38, judged) and `tab:tierscan` (7/7, judged), so this cell
is a redundant duplicate from another campaign. Recorded here so it is not rediscovered as a
mystery.

**Standing lesson for this repo:** run the null-verdict sweep before trusting any cell
enumeration — a failed judging pass leaves a well-formed directory with no metric, and
latest-wins selection walks straight into it.

---

## ⚠️ CORRECTION to the section above — the number was never unbacked (2026-08-09)

**The integrity find above overstated its case, and the record must say so.** The claim was
that AS-2's published `pixtral-12b 48 → 83%` had *no reachable backing cell on any root or
cluster*. That is **false**. A live cell held it all along:

```
outputs/image_presence_threshold/rejudge/harmbench/
    pixtral_12b_no_defense_gpt-5-mini_20260807_065442_3288533
    status=success · asr=83.0 · 0 null rows
    upstream_ref -> pixtral_12b_no_defense_non_llm_baseline_ir_blank_20260807_043819_60229939
```

Paired against the same text arm it reproduces the published digits **exactly**:
`+35.0pp, discordant 39/4, p=3.108e-08` — the paper's original numbers to three significant
figures. It is present **locally and on AICR**.

**Why the sweep missed it.** The sweep enumerated `defense+evaluate/` roots. But a cell whose
*first* judging failed can only ever have a `rejudge/` home — that is precisely where its
number must live. Worse, rejudge output dirs **drop the transform chain from their name**
(`pixtral_12b_no_defense_gpt-5-mini_<ts>`, no `ir_blank`), so a path-keyed search for the
blank arm cannot match them. The correct search is a glob over
`outputs/*/rejudge/*/*/results.json` matching on **`upstream_ref.source_dir`**, never on the
output dir's own name.

**What this means for the paper.** Both values are valid `gpt-5-mini` passes over *identical*
stored responses; they differ on **2 of 100 rows**, a ±2pp judge-nondeterminism band:

| pass | ASR | delta | discordant | p |
|---|---|---|---|---|
| 08-07 rejudge | 83.0 | +35.0pp | 39/4 | 3.108e-08 |
| 08-09 recovery rejudge | 81.0 | +33.0pp | 37/4 | 1.026e-07 |

**The paper KEEPS 81 / +33pp / 1.03e-07** — the conservative value, already propagated
consistently across six sites and the multiplicity registry (`--audit` 0 mismatches).
Reverting would re-propagate everything to land on a *larger* effect, which is strictly worse
practice. The spread is now reported in §Judge robustness as the instrument's own noise floor,
which is more useful than either number alone.

**The real standing lesson** (replaces the last line of the section above): before reporting a
published number as unbacked — a claim that costs trust in the whole table — re-run the search
**keyed on upstream provenance across every mode**, not just the mode that "should" hold it.
The null-verdict sweep itself remains correct and worth running.

---

## Con 6 / Q3 — CROSS-FAMILY JUDGE PANEL, COMPLETE (AICR job 328581, 2026-08-09)

Closes the machine half of "no multi-judge validation is reported for the headline cells".
`gemini-2.5-pro` re-scored the three results the reviewer named, over stored responses
(2200 rows, no target queried, no GPU). Wall 2:50 — that is 8-way concurrency, not a dead
judge: 10/10 tasks `status=success`, **0 null rows**, fallback parses 0–1 per 300.

### Result: every effect survives a different-family, stricter judge

| cell | n/arm | gpt-5-mini | gemini-2.5-pro | discordant | p (pro) |
|---|---|---|---|---|---|
| claude-sonnet-4-6, benign stratified | 300 | 9.3 → 61.7 (**+52.3**) | 16.7 → 73.7 (**+57.0**) | 172/1 | 2.9e-50 |
| gpt-4o-mini, benign stratified | 300 | 19.0 → 55.3 (**+36.3**) | 24.7 → 58.7 (**+34.0**) | 108/6 | 2.7e-25 |
| gemini-2.5-flash-lite, benign stratified | 300 | 24.0 → 58.7 (**+34.7**) | 26.3 → 61.0 (**+34.7**) | 111/7 | 3.4e-25 |
| qwen3-vl-8b, harmful | 100 | 2 → 1 (null) | 5 → 3 (**−2.0**) | 1/3 | 0.625 |
| pixtral-12b, harmful (inversion) | 100 | 48 → 81 (**+33**) | 50 → 80 (**+30.0**) | 37/7 | 5.3e-06 |

**The paired design does exactly what it is supposed to.** The cross-family judge sits at a
different *absolute* level — it calls 2–12pp more refusal on every benign cell, in **both**
arms — and the *contrast* lands within a few points everywhere. Absolute leniency cancels;
that was always the quantity at issue.

### Agreement (the statistic the reviewer asked for)

Pooled raw verdict agreement **94.4%** over all 2200 rows. *(Initially computed as 94.3% over 2100 — the pixtral blank arm had no comparable gpt-5-mini verdicts until the recovery rejudge was identified; recomputed complete.)* Per cell:

| cell | raw | kappa |
|---|---|---|
| benign, six cells | 86.7–97.7% | 0.65–0.94 |
| pixtral text arm | 94.0% | 0.880 |
| qwen3-vl-8b, both arms | 97.0 / 98.0% | 0.559 / 0.492 |

The low kappas are the **floored** qwen cells — the familiar instability of kappa at a 1–5%
base rate, where 97–98% raw agreement coexists with a weak chance-corrected score. Not a
disagreement signal.

### Read-out, against what was pre-registered in the preset

The pre-registered branch that fired is the **best** one: *"benign effects survive at similar
magnitude → the headline is judge-robust across families; report both judges side by side and
the objection is closed on the machine side."* Recorded honestly: the claude cell came back
**larger** (+57.0 vs +52.3), not smaller, so this is not a case of an effect surviving in
weakened form.

The qwen3-vl-8b null also behaved as the preset warned: the stricter judge moved it to 5% —
still **floored**, so it remains uninformative rather than becoming evidence. The pre-registered
instruction "check headroom before reading any null as a finding" applies and was applied.

### Two caveats, both written into the paper rather than left to a reader

1. **Family overlap on one row.** `gemini-2.5-flash-lite` is one of the *targets* being scored
   by `gemini-2.5-pro`. Reported per-model, never pooled, so it can be discounted. Empirically
   moot: it is the one contrast that does not move at all (+34.7pp under both judges).
2. **Same-judge noise floor.** `gpt-5-mini` re-run over identical stored pixtral responses
   flips 2/100 verdicts (±2pp). Reported; the lower value is carried throughout.

### Written into the paper

§Judge robustness gains two paragraphs (the panel + the two caveats) and hands off to the human
anchor with "a different-family judge still cannot exclude a blind spot shared by all
rubric-following language models". The Limitations line that read *"we have not run a
multi-judge panel on these cells"* is now stale and was rewritten to state three judges and
name what genuinely remains untested. **No multiplicity-registry change**: a robustness
re-scoring is the same hypothesis on a different instrument, not a new test — consistent with
how the existing `gpt-5-nano` pass is treated.

Build after integration: **19pp, 0 errors, 0 undefined refs, 1 overfull box of 1.34pt**
(0.5mm, invisible; `tab:factorial`). Two genuinely-visible pre-existing overflows found and
fixed in passing — `tab:families` (15.3pt) and `tab:modelids` (38.4pt), both appendix tables,
set to `\scriptsize`. Note for future layout work: **`aaai2027.sty` clamps `\footnotesize` to
`\small`**, so `\small → \footnotesize` changes a table's width by exactly nothing;
`\scriptsize` is the first step down that actually does anything.

---

## Con 6 / Q3 — HUMAN HALF: SHEETS BUILT AND VERIFIED, AWAITING THE OWNER'S LABELS (2026-08-09)

The independent-judge half closed above. This is the *"targeted manually annotated audit"*
half, over exactly the three claims Q3 names. **Everything is prepared to the last
keystroke; only the labelling itself is owner-side.**

**Tooling (committed, `ee5e529`):**
- `src/analysis/paper_b_human_eval.py` — builds the blind sheets
- `src/analysis/paper_b_human_eval_score.py` — scores the returned labels

**Artifacts** (in gitignored `judge_model_issue/`, because they hold harmful text):
`as2_roundA_{benign,harmful}_label_sheet_BLANK.csv`, the two `_key.csv` files, and
`as2_roundA_INSTRUCTIONS.md`.

### Design, and why each choice is the one it is

**Blind by construction — stronger than Paper C could manage.** Our manipulation is whether
a *blank canvas* is attached, so the request text is byte-identical between arms. The sheet
carries only request + response; there is no channel through which the arm could leak.
Paper C had to strip `defense` and `attack_family` columns; here there is nothing to strip.
⚠️ The one residual leak is **stated, not hidden**: a contrast pair puts the same request in
the sheet twice, so a repeat is noticeable. That reveals *pair membership*, never *arm
assignment* — and arm assignment is the only thing that must be blind, since the label is
per response. Rows are shuffled so pair members scatter.

**Two sheets, not one**, because the benign cells take the refusal rubric and the harmful
cells the HarmBench rubric; one file would ask the annotator to hold two decision rules at
once. Both rubrics are reproduced verbatim from the evaluators, so human and judge measure
the same thing.

**Two strata, never pooled** (the scorer enforces the separation, since pooling them is the
easy way to manufacture a flattering number):

| stratum | benign | harmful | what it is for |
|---|---|---|---|
| **A — contrast** (judge-discordant pairs, round-robin across models) | 30 (15 pairs of 384) | 20 (10 pairs of 44) | is the judge's *discordance* real? Deliberately not representative; **never** used for prevalence |
| **B — calibration** (uniform, **balanced across arms**) | 60 (30/30) | 40 (20/20) | agreement, prevalence, differential bias |

The arm balance in B is load-bearing: the component that does **not** cancel in a paired
contrast is (judge−human gap in the blank arm) − (the same gap in the text arm), and
estimating it needs both arms equally.

**Cells pinned by path** to the exact dirs the published numbers came from — never
latest-wins. `pixtral-12b`'s blank arm is drawn from the recovery rejudge the paper cites,
since its `defense+evaluate` cell has null verdicts.

### Verified before handing over (not asserted)

Sheets carry **zero** leak columns · 0 empty requests/responses · sample_id joins key 1:1 ·
all 25 contrast pairs complete with both arms · **0** concordant pairs leaked into the
contrast stratum · calibration exactly balanced 30/30 and 20/20. The scorer was smoke-tested
end-to-end on synthetic labels at 12% disagreement and **the synthetic files were deleted**
so they cannot be mistaken for real ones.

### Load and the one honest caveat

**150 responses** (90 refusal at ~2.1k chars mean, 60 harm at ~1.3k). Agreement and per-arm
kappa use all 150, so the effective n per arm is 45 (benign) / 30 (harmful) — comparable to
the paper's existing anchor at n≈50 per arm, but on **these** cells rather than a
neighbouring manipulation, which is the reviewer's actual point.

⚠️ **The differential-bias CI comes from stratum B alone (n=30/arm benign, 20/arm harmful)
and will be WIDE** — the smoke test showed roughly ±25–30pp at the harmful n. That must be
reported as a bound, not rounded into "the bias cancels" (the paper already declines to make
that move for the existing anchor and must decline again here). If a tighter interval is
wanted, `--calib-refusal 100 --calib-harm 60` raises it to n=50/arm at a cost of ~60 more
responses.

### What the scorer emits

Cohen's kappa overall and **per arm** (a judge confused by attachment would agree *worse* in
the blank arm) · prevalence per arm · differential bias with a 10k within-arm bootstrap CI ·
the population shift on stratum B, flagged **unpaired** since B samples arms independently
and is therefore *not* like-for-like with the paper's paired delta · and discordance
validity: of the pairs the judge scored as changed, how often the human agrees there was a
change and in the same direction — unbiased *conditional on judge discordance*, which is the
conditional the objection actually doubts.

---

## AS-2 residue, current as of 2026-08-09 (supersedes the earlier "Residue" section)

Everything in that earlier list is now closed — con 1, con 5, con 10 and the lit round each
have their own section above. What remains:

1. **Human labels** — the sheets above, owner's hands. The last open review-3 item.
2. **Page trim** — untouched by policy: it is the last step and the owner's call.

**⚠️ Stale TODO labels, NOT fixed here.** TODO items titled *"ORACLE-LEAK RERUN — Paper B
(AS-2), the ONE paper materially affected"* and *"PAPER B MECHANISM-SWEEP EXTENSION"* both
predate the **2026-08-08 AS-2/AS-7 split** and are AS-7's work, not AS-2's — "Oracle
Inflation" is literally in AS-7's title. Verified against the current sources: **neither the
AIA version nor the arXiv v2 mentions ECSO, SemanticSmooth or CIDER even once**, and both
state "no defense in the loop" five times. Left unedited deliberately: `TODO.md` was modified
five minutes earlier by a concurrent session — almost certainly the dedicated AS-7 session
that owns those items — and racing another session's edits in a shared working tree is worse
than a stale label. Flagged to the owner instead.

---

## ⚠️ CORRECTION — we ALREADY have human labels on BOTH rubrics (owner challenge, 2026-08-09)

The section above built a 150-response human round and called it "the last open review-3
item". **The owner pushed back — "previously we have human labels!" — and he is right.**
Two completed blind rounds already exist, both owner-labelled, and the second was never
cited in AS-2:

| round | task | n | agreement | channel split | targets |
|---|---|---|---|---|---|
| **Round R** (2026-07-28) | refusal | 100 | **κ=0.794** binary (0.847 dedup, 3-class 0.438) | stratified text × image | qwen2.5-vl-7b, internvl3-8b |
| **Round J** | harm (HarmBench) | 100 | **κ=0.680** | 56 text / 44 image | internvl3-8b 32, qwen2.5-vl-7b 32, **pixtral-12b 32**, gemini-2.5-flash 4 |

Records: Round R in `text_docs/autoattack_defense/experiment_results.md` §"Refusal-judge
human calibration (Round R)"; labels in `judge_model_issue/round_j_human_labels_final.csv`.

**The free win, applied.** AS-2 cited Round R and **not** Round J — verified by grep, the
paper contained no harm-side human anchor at all. So the harm axis looked unvalidated by
humans when it is validated at n=100, *including 32 rows on `pixtral-12b`* — the very model
carrying the sign inversion §res-judge is asked to defend. A paragraph now states it, and
the Limitations line reads "the two human anchors, one per rubric, 100 blind labels each".
Build clean, 20pp (was 19; float reflow).

**What the genuine remaining gap actually is** — much narrower than the section above
implied. Both rounds come from the defense-pipeline studies: self-served targets, defenses
in the loop, and an image channel carrying a *payload* rather than a blank canvas. So they
calibrate both rubrics, and they cover the text-vs-image contrast, but not on AS-2's three
API targets and not with a blank canvas. That is a scope note the paper already makes
honestly for the refusal anchor.

**Recommendation recorded: do NOT run the 150-row round.** Cost is ~3–4 hours of the
owner's labelling — the scarcest resource in the ordering — to narrow a gap the paper
already discloses, on top of two n=100 anchors plus a cross-family judge panel on the exact
cells. If any top-up is wanted later, ~40 rows weighted to the blank-canvas harmful cells
buys most of what 150 would; the builder takes `--contrast-harm/--calib-harm` flags. The
sheets stay on disk unlabelled, costing nothing.

**Process lesson (the real one):** the review item said "human validation", and I went
straight to *building* the artifact without first asking whether the repo already satisfied
it. The coverage check belonged before the build — the same Phase-0 discipline the
`lit-review-loop` skill enforces for literature applies to our own prior rounds.

**DROPPED BY OWNER DECISION 2026-08-09 ("yes, drop").** The 150-row round will not be run.
The unlabelled sheets, keys and instructions were deleted from `judge_model_issue/` so no
later session mistakes them for pending work; the builder is seeded (`--seed 20260809`,
deterministic) and regenerates them byte-identically if a top-up is ever wanted. Tooling
(`paper_b_human_eval.py`, `paper_b_human_eval_score.py`) stays committed. **Con 6 / Q3 is
answered as it stands:** a cross-family judge (`gemini-2.5-pro`) on the exact cells, plus
both rubrics humanly anchored at n=100 each (Round R refusal κ=0.794, Round J harm κ=0.680
including 32 `pixtral-12b` rows) — with the scope limit stated in the paper rather than
papered over.

---

## Self-check of today's judge-section edits — two errors found and fixed (2026-08-09)

A consistency pass over what THIS session wrote into §res-judge, run while the owner was
at the cspaper gate. Two defects, both introduced today, both in text a reviewer reads:

1. **🔴 WRONG RANGE.** The new paragraph claimed the cross-family judge "calls **5 to 7pp**
   more refusal on every benign cell". Recomputed from the six cells, the true spread is
   **+2.3 to +12.0pp** (claude text +7.3 / blank +12.0; gpt-4o-mini +5.7 / +3.3; flash-lite
   +2.3 / +2.3). The rhetorical point survives untouched — the shift is positive on all six
   cells, so the judge is uniformly more liberal about calling refusal while the paired
   contrast still lands within a few points — but the number was invented from a glance at
   two cells rather than computed. Fixed to `2 to 12`pp in the paper and this file.

2. **Incomplete denominator.** Agreement was reported as "94.3% across all 2,100 rows".
   2,200 rows were rescored; the pixtral blank arm was excluded because its comparator
   `gpt-5-mini` verdicts had not yet been located (they were in the recovery rejudge, per the
   `rejudge/`-tree correction above). Recomputed complete: **94.4% over 2,200**. Fixed.

**Verified correct, no change needed:** every paired contrast (+57.0/+34.0/+34.7 with
172/1, 108/6, 111/7; pixtral +30.0, CI [+17.9,+40.9], 37/7, p=5.3e-06; qwen 5→3, p=0.63) ·
the kappa ranges (floored qwen 0.49/0.56; benign 0.65–0.94) · and the judge-selection
figures, checked against `JUDGE_MODEL_REPORT.md` rather than recalled: gpt-5-mini HarmBench
**50%** flagged at **κ=0.680**, gemini-2.5-pro **33%** at **κ=0.438**.

**Also checked and deliberately NOT changed:** `tab:claims` says the benign effect spans
"+23 to +57pp, hosted", and +57 is the caption-image arm of the property sweep, not a
blank-canvas contrast (whose top is +52.3). That looked like an inflated range — but the
phrasing is used identically at four sites and is consistent with the paper's own thesis
that presence raises refusal *and* properties set the price. Not an error; recorded so it is
not "fixed" by a later session.

**Updated for today's evidence:** the `tab:claims` row "The judge does not manufacture the
effect" cited only the refusal anchor; it now reads "survives a cross-family judge; both
rubrics human-anchored, κ=0.79/0.68; differential +3.8pp". Build clean: 0 errors,
0 undefined, 1 overfull box of 1.34pt, 20pp.

**Lesson:** the cross-family panel's *computed* outputs were pasted into the paper correctly,
but two summary statements written from memory around them were not. Summary sentences need
the same recompute-and-check as the headline digits — they are what a reviewer actually reads.

---

# cspaper review 4 — handling (2026-08-10)

Review 4 (`paper/as-2/aaai_2027_main/reviews.md`, gitignored) rated 4/reject. Its **first
and heaviest con**, and the one it says drove the rating, was that the attachment x mention
table is internally inconsistent: that `12/2` discordant pairs cannot give `+30`pp or
`p=6.9e-8`, and `20/8` cannot give `+20`pp or `p=1.9e-6`.

## The charge is false, and the paper's arithmetic is exact

The table reports `32/2` and `20/0`, not `12/2` and `20/8`. Recomputed:

| contrast | b/c | (b-c)/100 | paper's Delta | exact McNemar | paper's p |
|---|---|---|---|---|---|
| mention, no image | 12/4 | +8pp | +8 | 0.07681 | 0.077 |
| attachment, no mention | 32/2 | +30pp | +30 | 6.938e-08 | 6.9e-8 |
| attachment, mention held | 20/0 | +20pp | +20 | 1.907e-06 | 1.9e-6 |

Every digit matches. Nothing was changed to make it match.

## Why the reviewer misread it — this is our defect, not theirs

`pdftotext -layout` on the submitted PDF shows the two-column layout placing the
generations table beside the factorial table, so a linearized read interleaves them:

```
qwen2.5-vl-7b  37  38  +1  1.000 ...   ∆ (mention)             +8 (12/4, p = 0.077)
qwen3-vl-8b    54  82  +28 <10−4 ...   attachment, no mention  +30 (32/2, p = 6.9×10−8)
```

`12/2` is `12` from the row above joined to `2` from the right-hand row; the `8` in `20/8`
comes from the neighbouring `+8` or the `10−8` exponent. The counts were also crammed into
an `\emph{(b/c, p=...)}` parenthetical with one digit bolded inside an italic run. Given how
reviewers now read PDFs, a table whose numbers cannot survive linearization is a defect
regardless of who is holding it.

**Fixes applied:** the contrast block now has real headed columns
(`contrast | Delta | gained | lost | p`) as a separate tabular; each row is atomic under
linearization, and the caption states that Delta is `(b-c)/100` and p an exact McNemar on
those two columns, so both are recomputable from the table. Re-extraction confirms the rows
now come out self-contained.

## `src/analysis/tex_stat_audit.py` — mechanised, not asserted

"We checked and it's fine" is worth nothing asserted. The auditor recomputes every paired
result straight from the .tex: Delta vs (b-c)/n, Delta vs the rate pair, and p vs an exact
two-sided McNemar on (b,c) alone. AS-2 AIA: **28 results parsed, all consistent.** Swept
across every paper build in the repo (AS-2/3/4/7) — no real inconsistency anywhere.

Coverage is printed loudly (`checked p: 27/28, UNCHECKED lines [...]`) because a silent skip
reads as a pass — see `project_empty_check_output_is_not_a_passing_check`. The two residual
unchecked items at the pixtral/llava paragraph were verified by hand: `39/0` -> +39pp and
3.638e-12 vs a stated 3.6e-12; `1/9` -> -8pp, no p stated there and fully checked where it
recurs.

Four tool bugs were found and fixed while building it, each of which had produced a *false*
finding: a non-brace-aware macro stripper that silently skipped `\mathbf{<10^{-4}}` p-cells;
p-value columns read as rates; Python's round-half-to-even calling a correct `0.125 -> 0.13`
a mismatch; and `68 / 29` rate pairs read as discordant counts (these papers write counts
tight, `32/0`, and rate pairs spaced — that spacing is the only separator).

## Other review-4 items fixed this round

1. **A real defect the review did not catch** (found while checking its claim). The claims
   table asserted "Attachment alone moves refusal with no image attached (+33pp)" citing
   `tab:factorial`. Self-contradictory wording, a number from a different experiment (+33pp
   is the gemini-2.5-flash canvas+instruction cell), and the wrong table. The intended claim
   is the placebo ladder's: an *asserted* attachment moves refusal with no image attached,
   +16pp over a matched system message (`tab:placebo`). Fixed. Plausibly primed the
   reviewer's distrust of `tab:factorial` — a claims row pointing there for a +33 that does
   not appear in it.
2. **Terminology (con 8).** "content-free" -> "request-independent" (11 sites). The old term
   was self-contradictory where the paper wrote "the only content-free image we test that
   carries readable text". The figure's own panel labels said "rabbit — natural image" and
   "text-pseudo-image" while the caption said "clip-art line drawing"; `figs/make_decoys.py`
   labels corrected and the figure regenerated. That script's repo-root path was also broken
   by the paper/as-N/ re-keying and now walks up instead of counting parents.
3. **Carrier claim softened (all four reviews name this — the strongest signal in the file).**
   Five sites: abstract, intro, contribution (ii), results, conclusion, claims table. Now
   "the shortcut needs no serving layer to appear; what hosted stacks add stays open" —
   we show a stack is not *necessary*, never that the hosted stacks contribute nothing.
4. **Pre-registration status (con 6 / Q4).** New paragraph in the multiplicity appendix
   stating plainly that nothing was pre-registered, that `qwen3-vl-8b` was *selected* out of
   a five-model scan so all its follow-ups are follow-up on a selected model, and that what
   protects them is re-collection (+32/+28/+29pp across three independent jobs) rather than
   the scan.

Build after all edits: **0 errors, 0 undefined refs, 0 overfull boxes, 20pp** (the restructure
removed the last overfull box), from captured pdflatex stdout.

## Open, needing the owner's decision — not started

- **Human labels on the actual manipulation (review 3 con 8 AND review 4 con 7, both Q3).**
  Both reviewers independently name the same gap: the two human anchors (Round R refusal
  k=0.79, Round J harm k=0.68) come from a *neighbouring* study where the image carried a
  payload, not from the blank-canvas cells. This is the round built and then dropped on
  2026-08-09. The builder is retained and regenerates byte-identically (seed 20260809).
- **Multiple image instances per property level (all four reviews).** The only remaining
  objection that needs new collection.
- **Broader harmful evaluation** beyond OR-Bench's harmful split (con 5).

---

## ⚠️ The carrier-claim softening was INCOMPLETE — five residue sites found and fixed (2026-08-21)

The review-4 round softened the carrier claim at five sites (abstract localisation
paragraph, intro, contribution (ii), the same-weights results caveat, conclusion,
claims table, limitations) and recorded it as done. **A verification sweep for the
strong phrasings found five more sites the pass had missed**, and their placement is
the worst possible: the paper now asserted the softened claim in the places a careful
reader checks and the strong claim in the places everyone reads.

| site | what it still said |
|---|---|
| abstract, **last sentence** | "an uncontrolled variable inherited with the weights" — flat, no hedge |
| conclusion, **last sentence** | same phrase, one paragraph after the caveat that contradicts it |
| §results "Taken together" | "it is **not** the hosting layer ... but the aligned checkpoint itself" |
| §discussion, third observation | "the serving-time layer is **not what carries** the effect" |
| §related work, `zou2026understanding` | the sign split "separated by the serving stack" |

The last one was not merely unsoftened, it was **contradicted by our own data**:
`pixtral-12b` (loosens) and `qwen3-vl-8b` (tightens) are both open checkpoints served
by us under one arrangement, so the sign split cannot run along the hosted/open line.

**What replaced them.** The licensed claim is narrower and is now stated uniformly: the
hosting layer is inert *on the one checkpoint we can test both ways*; among the **seven**
checkpoints we serve ourselves the serving arrangement is fixed by construction, and the
behaviour still ranges from $+32$pp to a sign reversal — so the checkpoint alone is
sufficient to produce it. What the hosted stacks contribute to their own $+23$–$57$pp
shifts is **not identified by this design**, and every site now says so.

**Lesson for any future claim-softening pass.** Softening is a *sweep*, not a set of
edits: grep the strong phrasings themselves (`hosting layer`, `serving layer`,
`checkpoint itself`, `inherited with the weights`, `carried by the checkpoint`) and
confirm zero survivors, rather than editing the sites the reviewer happened to cite.
The four reviews all named this claim; a fifth round would have re-raised it from the
abstract alone.

**Build after the fix:** 0 errors, 0 undefined refs, 0 overfull boxes, 20pp, from
captured pdflatex stdout. `tex_stat_audit.py` re-run: CONSISTENT, 27/28 p-values and
26/28 deltas checked (line 482 is the known CI-prose row).
