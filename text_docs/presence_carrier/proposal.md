# Research Proposal — Visual Budget: what carries the presence shift (`presence_carrier`)

**ID:** AS-9 · **Codename:** Visual Budget · **Namespace:** `presence_carrier`
**Founded:** 2026-08-22, by split from AS-2 (owner-ratified same day).
**Workflow stage:** S4 — evidence substantially collected, thesis stated, prior-art gate not run.
**Target venue:** ICLR 2027 — abstract ~2026-09-19, full ~2026-09-24 (both EXPECTED, re-verify
before planning). This is the least mature of the four papers in the line; CVPR 2027
(~2026-11-13, EXPECTED) is the natural slip and is a legitimate home, since the mechanism is a
claim about visual tokenisation.

---

## 1. The one quantity

**What physically produces the magnitude of the refusal shift that an uninformative image
attachment causes.**

AS-2 measures the shift and characterises its behaviour: who pays it, whether it corrects
under instruction, whether it needs an image at all, whether its sign is stable, whether it
tracks available harm. All five are properties of the *same* number, which is why they are
one paper. This paper asks a different question: not how the shift behaves, but what
generates it.

The claim, as far as the evidence currently reaches: **two substitutable axes, how much
visual input arrives and how uninterpretable it is, which saturate; and canvas size acts
*through* the visual-token budget rather than through resolution as such.**

## 2. Why this is a separate paper, not an AS-2 section

The split test applied at the 2026-08-22 sitting: *does this measure the paper's quantity, or
a different one?*

AS-2's quantity is the shift. A carrier taxonomy does not measure the shift, it explains it.
Keeping it inside AS-2 forced the draft to carry a positive mechanism claim alongside a
behavioural claim, and the two need different evidence and different amounts of hedging.

There is a second, sharper reason. The carrier story has a real internal history that needs
room to be told honestly: a matched-size caption contrast and a JPEG-quality contrast
recorded content as **inert**; a stronger manipulation on realistic images overturned that;
and the size axis then vanishes on a host whose canvas cannot buy visual tokens. Told at
length that is careful science. Compressed into a section between two other arguments it
reads as the paper contradicting itself.

Boundary with AS-2, to be held on both sides:
- **AS-2 keeps** the *negative* property claim: the response varies with properties carrying
  no information about the request (a black canvas costs more than a white one of identical
  size; refusal climbs with pixel count on an open checkpoint). That is leg one of AS-2's
  ratified four-leg spine and it must not be removed.
- **AS-9 takes** the *positive* claim: which axes, how they compose, how they saturate, and
  what they act through.
- **Shared control:** the token-matched text ladder is AS-2's control against an input-length
  explanation and stays there. AS-9 should extend it rather than re-report it, so the two
  papers do not rest a claim on one table.

## 3. What is already collected

Committed presets under `conf/experiment/image_presence_threshold/` (they stay where they
are; new AS-9 rounds write to `conf/experiment/presence_carrier/`):

| Evidence | Presets | Campaign field |
|---|---|---|
| Ten-arm property sweep, hosted | `image_property_ablation_stage{1,2}` | `paper_b_image_property_ablation` |
| Property sweep, open checkpoint | `property_ablation_ow_stage{1,2}` | `paper_b_property_ablation_ow` |
| Size x fill instance replication (12 arms) | `instance_replication_stage{1,2}` | `paper_b_instance_replication` |
| Content levels over independent instances | `instance_content_replication_stage{1,2}` | `paper_b_instance_content_replication` |
| Realistic images at a matched visual-token budget | `realistic_images_stage{1,2}` | `paper_b_realistic_images` |
| Second vendor, content axis at a host-verified matched budget (n=300) | `second_checkpoint_hosted_content` | `paper_b_second_checkpoint_hosted` |
| Second open checkpoint, built and pre-registered, **not yet run** | `second_checkpoint_gemma` | `paper_b_second_checkpoint_gemma` |
| Carrier exclusion sweeps | `mechanism_sweep`, `mechanism_sweep_cider`, `mechanism_sweep_newtargets` | `paper_b_mechanism_sweep*` |

**The tables are already extracted, verbatim, at `paper/as-9/inherited_from_as2.tex`**
(gitignored, like all paper sources): `tab:imgprops`, `tab:contentinstance`, `tab:instance`,
`tab:realistic`, `tab:secondcheckpoint`, `tab:locus`, `tab:owprops`. That file is not
compilable as it stands, since the captions still reference AS-2 labels and need rewriting.
The prose that accompanied them is recoverable from
`paper/as-2/aaai_2027_ai_alignment/aaai_aia_latex/paper.tex.pre-respine`.

**One table did NOT transfer, deliberately.** `tab:imgvsimg` stays in AS-2 and now carries
leg one of its spine: direct image-versus-image contrasts with an image attached in *both*
arms, so only the named property moves. At the re-spine it gained a row, the open
checkpoint's $1536^2$-vs-$256^2$ size contrast ($+16$pp, $18$ flips against $2$, $p=0.0004$,
95% CI $[+7.7,+24.9]$, computed with `src/analysis/paired_binary.py`). AS-9 may re-use those
cells but must not treat that table as its own.

**The gemma round is built, pre-registered and unbought (~$1.6).** Its preset header records
the architectural finding that motivated it: on that processor the blank ladder is
byte-identical across canvas sizes, so the size arm is a rig check rather than a contrast.
Read that header before deciding whether to buy it.

**One lead not yet a claim.** The within-family generational ladder shows the shift appearing
abruptly between two adjacent checkpoints rather than along a gradient. That table stays with
AS-2 as decoupling-under-control evidence, but the *step* reading belongs here and needs more
families before it is worth asserting: a release moves alignment, vision encoder and
pretraining corpus together, so a single family cannot isolate anything.

## 4. What is missing before this is a paper

In order:
1. More checkpoints on the carrier axes. Two vendors is a replication; it is not a
   characterisation.
2. An architecture-aware design. Continuous-budget models (qwen3-vl) and fixed-budget models
   (gemma-3, the Gemini family) are different instruments, and the size axis is only
   *askable* on the first. The paper should be organised by that distinction rather than
   fighting it.
3. Its own token-budget control, so it does not share AS-2's.
4. A mechanistic probe would lift this from characterisation to explanation. The guard-internals
   sibling repo (`model_internals_safety`) is the natural collaborator; that is a cross-repo
   read, not a dependency.
5. Prior-art gate through `lit-review-loop`, in solution vocabulary (visual token budget,
   resolution scaling, perceptual entropy, image complexity and refusal).

## 5. Do not relitigate

- **AS-2 keeps leg one.** Removing the negative property claim from AS-2 to feed this paper
  would break AS-2's ratified spine. Do not propose it.
- **No claim about a single carrier across the hosted tier.** The hosted size arms are flat or
  point at colour; the current draft already refuses this and so should the new paper.
- Public repo: no reviewer text, no personal data, no venue career-weighting in this file.
