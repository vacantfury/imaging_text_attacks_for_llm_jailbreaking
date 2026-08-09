# AS-2 · cspaper review 3 — re-analyses (no new data collection)

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

**Status:** the ten-category round (`topic_stratified_stage1/2`, campaign
`paper_b_topic_stratified`, AICR jobs 327863 + 327869) is in flight to replace this
two-category read. Regardless of its outcome, **the five domain-naming sites must be
corrected to measured categories** — there is no result that rescues the current prose.

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

## Residue

- The ten-category round must land before §1 is written into the paper.
- Item 4 above (OCR vs visual structure) needs a prose audit of the paper's
  content-axis language — **concept sweep, not a phrasing sweep**.
- Human validation on the primary cells (con 8 / Q2) is deliberately untouched: the
  standing order puts human eval last.
