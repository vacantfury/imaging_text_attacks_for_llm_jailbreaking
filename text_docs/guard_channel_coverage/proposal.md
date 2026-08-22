# Research Proposal — Channel Coverage: covering both channels of a guardrail (`guard_channel_coverage`)

**ID:** AS-8 · **Codename:** Channel Coverage · **Namespace:** `guard_channel_coverage`
**Founded:** 2026-08-22, by split from AS-7 (owner-ratified same day).
**Workflow stage:** S5 — evidence largely collected, thesis written, not yet drafted.
**Target venue:** IEEE SaTML 2027 — full paper **2026-09-29** (confirmed, no separate abstract).

---

## 1. The one quantity

**How much of a guardrail's required coverage a given deployment configuration actually
buys, and what it costs on benign traffic.**

AS-7 measures that a text-only guard's image-channel decision is a *constant*, and stops
there deliberately: it is an attribution paper and says so. It separates attribution from
efficacy and declines to answer efficacy. This paper is the efficacy answer.

The claim: **coverage and calibration live in different classifiers, so neither
substitution nor stacking is the right response, and the routed panel that is the right
response inherits a benign cost nobody prices.**

## 2. Why this is a separate paper, not an AS-7 section

The split test applied at the 2026-08-22 sitting: *does this measure the paper's quantity,
or a different one?*

AS-7's quantity is the guardrail's **share** of the refusals credited to it. Every result
that moves that share belongs to AS-7. A routed panel does not move it. It is a *fix*, and
its evaluation asks a different question: does this configuration work, and what does it
cost. AS-7's own scope note already draws this line ("this is an attribution claim and not
an efficacy claim, and the distinction is load-bearing"), then the draft answers the
efficacy question anyway across several sections. Those sections are this paper.

Boundary with AS-7, to be held on both sides:
- **AS-7 keeps** the channel measurement itself (the constant decision, harmful and benign),
  because that is what drives the share to zero.
- **AS-8 takes** everything that responds to it: the panel, stacking, redundancy coverage,
  the calibration pricing across guard families, the detector-gated deployment, the adaptive
  attacks, and the safety-utility ranking.
- Two AS-7 tables serve both roles and need an explicit call at AS-7's re-spine: the benign
  carrier grid and the discrimination grid. Default: AS-7 keeps the *minimal* form that shows
  the decision is constant; AS-8 takes the cross-guard calibration comparison.

## 3. What is already collected

Committed presets under `conf/experiment/defense_read_access/` (they stay where they are;
new AS-8 rounds write to `conf/experiment/guard_channel_coverage/`):

| Evidence | Presets | Campaign field |
|---|---|---|
| Channel-routed panel, end to end | `guard_router_panel_internvl3`, `guard_router_panel_pixtral` | `as7_guard_router`, `as7_guard_router_benign` |
| Benign calibration across guard families | `benign_carriers_stage1`, `stage1b_plain`, `stage2_{wildguard,llamaguard3,guardreasoner_vl}` | `as7_benign_carriers` |
| Benign channel arms | `benign_channel_stage1`, `benign_channel_{wildguard,llamaguard3,guardreasoner_vl}` | `as7_benign_channel` |
| Channel ASR, 3 guards x 2 targets | `channel_asr_{internvl3,pixtral}_{wildguard,llamaguard3,grvl}` | `as7_channel_asr` |
| Adaptive attacks against the re-check | `adaptive_image_{control,encoded}_stage{1,2}` | `as7_adaptive_image_control`, `as7_adaptive_image_encoded` |
| Stacking, redundancy | `stacked_defense` (in `image_presence_threshold/`) | `paper_b_stacked_defense`, `paper_b_channel_coverage` |

Results in the current AS-7 draft that transfer (source of record is that paper's git
history; sections and labels named so they can be recovered after the re-spine):
`sec:res-benign` (router half), `sec:res-coverage` / `sec:res-redundancy`,
`sec:res-stacked`, `sec:res-tradeoff`, tables `tab:router`, `tab:routershare`,
`tab:benigncarrier`, `tab:stacked`, plus the mitigations appendix (detector-gated
deployment; the detector recall figures are the binding constraint and belong here).

The panel already carries **pre-registered predictions including one written to fail, which
did**: it keeps the text guard's benign calibration and closes the image hole, but inherits
rather than repairs the multimodal guard's benign-image over-blocking. That refuted
prediction is an asset and should lead rather than be buried.

## 4. What is missing before this is a paper

In order:
1. A second target family beyond `internvl3` / `pixtral`, so the panel result is not a
   two-checkpoint claim.
2. More than one benign set. The calibration claim currently rests on one adversarially-hard
   benign population, and calibration is exactly the axis where population choice bites.
3. A third guard class in the routed panel, so "route by modality" is shown to be a rule
   rather than a two-guard pairing.
4. The over-blocking repair, or a measured argument that it cannot be repaired by routing
   alone. The paper is stronger if it names the residual it does not fix.
5. Prior-art gate through `lit-review-loop`, phrased in solution vocabulary (guard
   ensembling, modality routing, cascade classifiers), not only problem vocabulary.

## 5. Venue reasoning

SaTML 2027 is the right audience: a guardrail deployment-design paper reads as core
trustworthy-ML rather than as a general ML contribution, and SaTML is a main conference with
a single confirmed deadline and no separate abstract. ICLR 2027 is the alternative if the
work generalises faster than expected, but its bar for an applied defense-configuration
paper is set by novelty rather than by deployment relevance, which is this paper's strength.

## 6. Do not relitigate

- The **efficacy / attribution split** is AS-7's ratified boundary. This paper exists because
  of it; it does not reopen it.
- **No model-level refusal claims.** Whether the target's own threshold moves with attachment
  is AS-2's and AS-9's territory. Carry AS-7's scope control forward.
- Public repo: no reviewer text, no personal data, no venue career-weighting in this file.
