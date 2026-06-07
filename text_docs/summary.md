# Project Summary — Coverage-Complete Defense for VLM Jailbreaks

*Prepared for Shanu · working draft, June 2026*

## In one sentence

Current black-box defenses for vision-language models (VLMs) are **specialists** — each one inspects a single input or output surface — so no single deployed defense covers the full set of known encoded and image-based jailbreaks; this project builds the minimal **coverage-complete** defense that checks every input channel, and measures what that completeness costs in usefulness.

## Background

The starting point is our Canadian AI encoding-attack work (the one you presented): recasting a harmful request into a **mathematical or logical encoding** — set theory, formal logic, code — slips it past text-based safety checks, because the request looks benign on the surface.

The bridge to this project is a follow-up of mine, currently under review, that you may be less familiar with, so here it is in two sentences. It asked what happens when you add an **image** to such an attack on a vision-language model, and found something counter-intuitive: adding an image — even a completely unrelated "decoy" image — often *strengthens* the defense rather than weakening it. The reason turned out to be mechanical: **a defense only blocks an attack when its safety check happens to inspect the surface where the harmful content actually sits**, and adding the image accidentally caused the defense to look in the right place.

This project takes that mechanical insight and turns it into a systematic, constructive result.

## The question

If a defense helps only when its coverage matches where the harm lives, then each existing defense has a blind spot:

- **SAGE** checks the input text, but not the image.
- **ECSO** checks a caption of the image, but only when an image is present.
- **ETA / MLLM-Protector** check the image score or the output, but not the input text.

So for any single deployed defense, there exists a known attack in our suite that places the harmful content on the surface that defense never inspects. **The research question is whether a single, minimal defense can cover the union of these surfaces — and at what cost to legitimate use.**

## The approach

1. **Coverage map (motivation).** Characterize each defense by the surface it inspects and each attack by where it places the harmful content, then show empirically that no single existing defense covers the whole attack suite. This uses only published attacks and defenses — no new attack is constructed.

2. **The coverage-complete guard (the contribution).** A black-box wrapper that, regardless of whether an image is present, recovers the content of *every* input channel (reads the text and OCRs the image) and runs **one** unified safety check over their union. It is built entirely from primitives that already exist in the pipeline, and it removes the single-channel blind spot that the specialist defenses share.

3. **The cost of completeness.** Completeness is easy to achieve by refusing more often; the real contribution is the **safety–utility trade-off**. We measure benign-refusal rates on a benign benchmark and ask whether the guard dominates the existing defenses — equal or better safety at a lower over-refusal cost. (The image-augmentation paper documented a severe version of this failure mode: one defense reached near-zero attack success only by refusing 76–100% of benign prompts.)

4. **Held-out generalization.** To show the guard reflects a genuine coverage property rather than benchmark overfitting, we tune it on a subset of attacks and test it on attacks it never saw.

## Why this framing

The result is low-risk and defensible: a defense designed to cover the union beats each specialist by construction, so the only open variable is the utility cost — which is itself the finding, whatever its value. Evaluating all defenses on a common, broader attack suite is standard practice for a defense paper, which avoids the "you attacked a defense outside its intended scope" objection. The two design choices that make it more than a benchmark exercise — held-out generalization and the full trade-off curve — cost nothing beyond how the runs are reported.

## Status

The full evaluation harness, the coverage-complete defender, and all baselines (including the SOTA defenses ETA and MLLM-Protector) are implemented and smoke-tested. Targets are four open-weight VLMs on the NU cluster (Qwen2.5-VL-7B, InternVL3-8B, Pixtral-12B, Llama-3.2-11B-Vision), with the frontier API models as an optional breadth layer. The immediate step is confirming OCR fidelity of the rendered attacks on the serving models, then running the coverage-gap measurement and the guard's safety–utility evaluation. I will bring preliminary numbers to a group meeting once the first matrix is in.

## Directions beyond this paper

Three natural follow-ups, deliberately kept out of the current paper so it stays focused:

- **Compound attacks** that layer several techniques into a single input — testing whether the techniques *synergize* against the model, and whether a single composed input defeats defenses that each handle its parts.
- **Cross-modal splitting**, where the harmful content exists only in the *joint* interpretation of text and image — which, if it works, shows that per-channel checking is structurally insufficient and motivates joint multimodal verification.
- **Mechanism**, using white-box access to the open-weight models to ask *why* image-side alignment is weaker and where the model reassembles split content.
