# Research Proposal — Blind Judges: Safety Evaluators Inherit the Decode Blind Spot (`judge_reliability`)

**Workflow stage:** S4 · literature/scoop gate **PASSED at MEDIUM overlap** (delta confirmed 2026-07-19; §4) — as of 2026-07-19. Next: **S5 main story** (lock the delta) + **S1 external idea-check** (owner hands; package = `idea_check.md`); the *standalone-focused-paper vs fold-into-Paper-C* direction is an OPEN owner decision (§4). Paper E is **NOT on the July AAAI crunch** (Papers C/D); it targets a later cycle (§9).

*Codename: **Blind Judges** (Paper E, alias E). Full working title (refined at writing): "Blind Judges: Safety Evaluators Inherit the Decode Blind Spot on Encoded and Image-Rendered Jailbreaks." Origin: `text_docs/shared/future_work.md §9` + TODO item 8 + the cross-paper judge-model open problem (`project_paper_c_judge_model_open_problem`, `project_wildguard_invalid_as_asr_judge`). Seed evidence already in hand across Papers C and D.*

---

## 1. Decision & posture (settled 2026-07-18 — do NOT relitigate)

- **Paper E = an EVALUATION-METHODOLOGY paper**: measure — and fix — how much automated safety **judges** mis-score harm when the harmful content is **encoded** (cipher / base64 / set-theory / formal-logic / code / classical-Chinese) or **image-rendered**. It is **not** a new defense and **not** a new attack — it studies the *measurement instrument*.
- **Home: THIS repo, `judge_reliability` namespace** (existing-repo paper, Paper-C precedent). It reuses the whole harness — the encoder suite, the judge/guard registry, the human-κ pipeline, the `verify_results_doc` integrity tooling. No new attack or defense work is owed.
- **The one-line identity — the measurement mirror of Paper C.** C ("The Decode Gap") showed **defenses** inspect/reason about content but never *decode* an obfuscated payload. E shows the **judges** — the instruments everyone measures encoded-attack ASR with — share the *same* decode blind spot. C fixes the defense with recover→decode→guard; E fixes the measurement with **decode-then-judge**.
- **Relationship to C and D (no relitigation):** E does not re-open C's defense claims or D's attack claims. It takes the *judge* as its object of study. D supplied the sharpest in-hand evidence (WildGuard 41–68% false-positive rate on the strategy/code channel; `project_wildguard_invalid_as_asr_judge`), and C supplied the tri-judge Round-J human-anchored study. Both become E's pilot data.
- **Posture on scoop (honest, load-bearing):** the *mechanism* (LLM judges are fragile) is known; **the specific measured object — a per-judge × per-encoding × human-labeled miss/over-count calibration, framed as the judges inheriting the defenses' decode blind spot — is the unclaimed sliver.** §4 is the make-or-break gate; the paper does not commit until it clears.

## 2. The idea (core claim)

**Claim.** Automated safety judges — fine-tuned classifiers, reasoning guards, LLM-judges, multilingual guards — **systematically misjudge harm when it is encoded or image-rendered**, in *both* directions, because they score **surface form, not decoded behavior**. Consequently, encoded-attack ASR and defense-success numbers across the subfield are systematically miscalibrated: the evaluator is blind exactly where the evaluated system is.

**One mechanism, two error directions (both already observed in-repo):**
- **Under-count (false "safe").** The harm is genuinely present but encoded, so a judge that never decodes the payload scores the response safe → inflates apparent defense success / deflates attack ASR. (The §9 headline gap; qualitative notes in h4rm3l / CodeChameleon / cipher-vs-guardrails.)
- **Over-count (false "harmful").** The judge anchors on *surface* malicious cues — a malicious-looking encoded string, the harmful task echoed as a **code literal/comment** with no steps completed, an ASCII-art word-ID — and fires without the behavior being completed → inflates attack ASR. (Directly measured: WildGuard **41–68%** FP on the strategy/code channel, `bestofn_attack` R3; gpt-5-nano **2–3×** absolute-ASR inflation vs stronger judges, `project_paper_c_judge_model_open_problem`; "Confusion is the Final Barrier" anchoring-on-tone.)

**The fix — decode-then-judge.** Prepend a recover/decode step (transcribe the image, restate the encoding in plaintext), then apply the HarmBench-style *behavior-completion* rubric to the decoded content. This is the measurement-side twin of Paper C's recover→decode→guard, and it should shrink *both* error directions. The paper also yields a practical **which-judge + decode-first recommendation** for anyone evaluating encoded/rendered jailbreaks.

## 3. The measurement design (judges × encodings × human ground truth)

The core artifact is a calibration table, **N judges × M encodings**, against a **human-labeled** anchor, reporting per-cell **miss rate (under-count)** and **over-count**, then the same table **with a decode-then-judge step** to show the recovery.

- **Judge axis (N).** Fine-tuned classifiers (HarmBench-cls, LlamaGuard-3, WildGuard, MD-Judge) · reasoning guards (GuardReasoner / ThinkGuard) · LLM-judges (gpt-5-mini — the validated headline; gpt-5-nano — retained as the inflation exemplar; a capable open model with a rubric) · multilingual guards (Qwen3Guard / PolyGuard / ShieldLM). Registry already in `src/llm_utils` + the guard rows.
- **Encoding axis (M).** The repo's own encoders — set-theory / formal-logic / code / classical-Chinese / cipher / homoglyph — plus base64 and **image-rendered** (`ir_plain`), spanning the surface↔semantic range.
- **Ground truth.** The **100-item human-anchored blind sheet** already built for Round J (70 stratified + 30 inter-judge-disagreement; `human_label/`, owner labeling in progress) is the pilot anchor; the full study extends the human-labeled set across the encoding axis.
- **Metric.** Per (judge, encoding): miss rate and over-count vs human labels, κ agreement, and the **decode-then-judge delta**. Headline = the systematic *pattern* of which judges fail on which encodings, and that decode recovers it.

## 4. Novelty & prior-art — THE gate (S4, UNRUN — make-or-break)

**This is the paper's make-or-break gate, and it has not been run.** The *plain* framing ("LLM judges are unreliable / consensus of many judges") is **taken** — StrongREJECT (NeurIPS'24) owns the better-autograder framing, and there is a live 2026 judge-reliability literature. The paper survives only if its delta is the encoded-harm-specific, decode-blind-spot angle.

- **Adjacent prior art to differentiate:** StrongREJECT (better autograder, plain jailbreaks) · Know Thy Judge (arXiv 2503.04474 — judges fragile to surface/style) · Confusion is the Final Barrier (arXiv 2508.16347, EMNLP'25 — anchoring on malicious *tone* → false positives) · A Coin Flip for Safety (arXiv 2603.06594 — judges degrade under distribution shift) · Schwinn et al. (**partial scoop** — BoN best↔worst flips under judge correction) · qualitative notes only in h4rm3l / CodeChameleon / cipher-vs-guardrails.
- **Our delta (the unclaimed sliver):** nobody has run the **systematic per-judge × per-encoding × human-labeled** miss/over-count measurement, and nobody frames it as **judges sharing the defenses' decode blind spot** with a **decode-then-judge** remedy. That framing is uniquely ours because it is the evaluation coordinate of this repo's compositional-coverage identity (`future_work.md §7.1`).
- **Gate procedure:** run `scoop-check` on the specific claim (dual-channel: signature terms + adjacent-subfield aliases), then the `lit-review-loop` (stage BibTeX → owner verify + download → read → write `text_docs/judge_reliability/literature_review.md` or extend the shared review). **Advance only if the delta survives.** If StrongREJECT-plus-a-2026-paper already covers the encoded-harm calibration, kill or narrow to the decode-then-judge-fix contribution.

### S4 scoop-check verdict — 2026-07-18 (Level 2, High Overlap — the broad claim is at risk)

Ran `scoop-check` (3 search angles, ~47 queries) + the in-bib §7.5 analysis. **Verdict: Level 2 — High Overlap (leaning Medium).** No single paper does the full 4-axis combination, but the territory is heavily occupied **piecemeal**, and one contribution (the decode-then-judge remedy) is **not a novel mechanism**:
- Judge calibration on **surface** encodings with a human anchor is done: **StrongREJECT** (Base64/ROT-13/disemvoweling/low-resource, human-validated, text-only), **On Calibration of Guard Models** (ICLR'25, 9 guards incl. cipher/ASCII), **SORRY-Bench** (ASCII/Caesar/Morse/Atbash + κ).
- The **over-count** mechanism (VENOM, tone-not-content) and the **image under-count** (FigStep, HarmBench-cls) are separately documented.
- **decode-then-judge on the eval side existed by 2023** — CipherChat (decrypt→judge), Yong et al. (back-translate→judge), Reading-Between-the-Pixels (OCR→judge). So the remedy is generality-not-principle, exactly as Paper C positions its defense-side recover→decode.

**Delta that survives (narrow):** (a) extend judge calibration to **semantic** encodings (set-theory/formal-logic/code/classical-Chinese) **+ image-rendered** — the alignment-sparse encodings no judge has been calibrated on (FigStep/MM-SafetyBench eval protocols confirmed to NOT decode-before-judging); (b) the **decode-blind-spot-shared-with-defenses** frame; (c) decode-then-judge **generalized + measured** across many judges.

**Gate outcome = LOOP-BACK / reconsider scope (NOT clean advance).** Do not lead with the broad "first judge-reliability-on-encoded-harm" headline (reads as StrongREJECT/On-Calibration on more encodings). Owner-decision among: **(i)** narrow hard to the semantic+image+decode-blind-spot delta → workshop (NeurIPS JUDGe); **(ii)** FOLD into Paper C as its first-of-kind judge-validation methodology section (Round J already sets this up); **(iii)** reconsider the Paper E direction (e.g. the §2 unified-defense or §7.2 multi-agent runners-up). **Confirm-gate:** download+verify `liu2025calibration` / `jeon2026encoders` / `zaghouani2026chisafe` — if any reports a per-encoding JUDGE calibration on semantic/image encodings, this is **Level 1 (fully scooped)** → fold into C. Staged CANDIDATE entries in `paper/literature/my_base.bib`; full log `outputs/scoop_check/2026-07-18/scoop_check_log.md`.

### S4 confirm-gate RESOLVED — 2026-07-19 (verdict upgraded to Medium; delta confirmed)

Owner verified+downloaded the candidates; I read the 3 confirm-gate papers in full (+ HPAA). **None does a per-encoding JUDGE calibration on semantic/image encodings → NOT Level 1; verdict UPGRADES to Level 3 (Medium Overlap), delta confirmed.** Reads recorded in `text_docs/shared/literature_review.md §7.7`:
- **On Calibration of Guard Models** (ICLR'25) — *confidence*-calibration (ECE) of 9 text guards under GCG/AutoDAN suffixes, broken down by response-model **not encoding**; no semantic/image, no decode-then-judge. Different axis.
- **Do Encoders Suffice?** (ICANN'26) — judge comparison broken down by **conversational technique** (single-turn/decomposition/escalation/context-manip), not encoding. Orthogonal.
- **ChiSafe-PAS** (LREC'26) — dataset paper; **proposes** per-obfuscation-accuracy but **defers the eval to future work**; surface-Chinese only (no 文言文 / cipher / semantic / image). Closest on the idea, doesn't execute it — its deferral is our opening.
- **HPAA** (USENIX Sec'26) — attack on content-moderation of social posts via typography; not an LLM-response judge, not image-render. Motivation cite.

**Ceiling = StrongREJECT** (§7.5): human-validated judge on SURFACE encodings only (Base64/ROT-13/disemvoweling/low-resource, text-only). **Clean delta:** extend judge calibration to SEMANTIC (set-theory/formal-logic/code/classical-Chinese) + IMAGE-rendered, unify under the decode-blind-spot frame, measure decode-then-judge across judges.

**Gate outcome = delta confirmed (Medium overlap), but as a FOCUSED contribution its MAIN-CONFERENCE ceiling is the open question** — and workshops are fallback-only, not a target (owner rule 2026-07-19), so "focused → workshop" is NOT an acceptable landing. Low-regret path: run the measurement richly so it serves Paper C's Round J regardless; **current lean = fold the judge-validation into Paper C and give the Paper E slot to a stronger main-conference direction** (see the direction re-evaluation, 2026-07-19). Owner decision open.

### S4 scoop-check #2 — the "capability-gap spine" — 2026-07-19 (Level 2, High Overlap on the INSIGHT)

Scoop-checked the sharpened claim: *judge–target decode-capability gap governs ASR measurement bias; grows as targets strengthen; decode-then-judge corrects only when decoder ≥ target; plaintext control.* The adjacent-subfield search (scalable oversight / weak-to-strong) found the hazard.

- **The "grows as the target gets stronger" hook is NOT novel — it is the general result of the scalable-oversight scaling-laws literature:** **Engels et al., "Scaling Laws For Scalable Oversight"** (NeurIPS'25 Spotlight, 2504.18530) models oversight success vs the capability gap and shows it *declines when overseeing stronger systems*; **Dorner et al.** (ICLR'25, 2410.13341) give the formal "a judge no more accurate than the model can't beat twice the data" bound; **Kenton et al.** (NeurIPS'24, 2407.04622) own the phrase "weak LLM judges strong LLM." All GENERAL-domain (games / ML-eval), not safety/encoded.
- **Safety-domain analogues** (closer domain, different mechanism): **Jailbreak Paradox** (Rao, 2406.12702) proves a weaker model can't detect whether a stronger one is jailbroken (plaintext, theoretical); **JADES** (Chu, 2508.20848) notes obfuscation-specific judge misfires + a decompositional fix; **ACE/LACE/CipherBench** (Handa, 2402.10601) makes decode-capability the explicit variable but on the *target*, no judge.

**Verdict: Level 2 (High Overlap) on the mechanism/insight** — the exciting "capability-gap predicts eval error, worse as models scale" framing is pre-owned (scalable oversight). **Delta that survives (Medium):** the *safety-encoded-decode* instantiation — the gap is a concrete **decode** gap on encoded/image payloads (not generic reasoning-complexity), with a **decode-then-judge correction bounded by decoder capability**, a **plaintext control**, and the **overturned published-ASR teeth**. Honest positioning: *"encoded-attack ASR measurement is a scalable-oversight problem"* — cite Engels/Dorner/Kenton as grounding, claim the safety-encoded instantiation + correction + control + overturned results as the contribution.

**Pattern flag:** this is the SECOND judge-reliability angle to return Medium overlap (narrow calibration = StrongREJECT/SORRY-Bench; capability-gap = scalable oversight). The neighborhood is crowded from two directions. Staged CANDIDATEs: engels2025scalingoversight, dorner2024limitseval, kenton2024scalableoversight, rao2024jailbreakparadox, handa2024ciphercompetency, chu2025jades — owner verify+download, then a deep-read confirms High-vs-Medium.

## 5. Contributions (provisional)

1. **The first systematic calibration** of automated safety-judge reliability on encoded / image-rendered harm — per-judge × per-encoding miss rate and over-count, against a human anchor.
2. **The unifying account** — judges score surface, not decoded behavior — that explains *both* the false-negatives (encoded harm missed) and the false-positives (surface cues over-flagged) with one mechanism.
3. **Decode-then-judge**, a cheap remedy that measurably shrinks both error directions, plus a practical **which-judge / decode-first** recommendation for the field.
4. **A validity correction with teeth:** a quantified statement of how much published encoded-attack ASR is distorted by the judge, not the defense — evidence in hand from Papers C and D.

## 6. Threats to validity

- **Scoop (§4)** — the dominant risk; gated before any commitment.
- **Human-anchor scale** — 100 items is a pilot; the per-encoding cells thin out. The full study needs the human-labeled set widened across encodings (owner-hands labeling is the bottleneck).
- **"Judge vs guard" conflation** — WildGuard/LlamaGuard are *input/response guards* with their own taxonomy, not HarmBench behavior-completion judges; a miss/over-count must be scored against a *fixed* rubric (HarmBench completion) so the finding is "wrong tool for the rubric," not an unfair comparison. (Exactly the `project_wildguard_invalid_as_asr_judge` lesson.)
- **Circularity of the fix** — decode-then-judge uses a model to decode; if the decoder is itself a target-class model, note the dependency and bound it (the same recover-step honesty as C).

## 7. Human-anchor & judge methodology (reuse Round-J)

Reuse the **shared Round-J** resolution rather than re-deriving it: the 100-item human blind sheet + `human_label/compute_kappa.py` (κ vs each judge, sliced representative / disagreement), the validated **gpt-5-mini** headline judge (κ=0.68 vs human), and the retained **gpt-5-nano** inflation exemplar. Full report: `judge_model_issue/JUDGE_MODEL_REPORT.md`; sanitized artifact `text_docs/shared/judge_validation_sample.md`. Paper E *is* Round J run richly across the encoding axis — the design was deliberately built so it could spin out (owner flag 2026-07-12).

## 8. Reused machinery + new code owed

- **Reused (no new build):** the encoder factory (`src/prompt_transformations/text/`), the image renderer (`ir_plain`), the judge/guard registry (`src/llm_utils` + guard rows), the human-κ pipeline (`human_label/`), the rejudge mode (`RejudgeTask`) for decoupled re-scoring of saved responses, and `scripts/verify_results_doc.py` for numeric-fidelity.
- **New (small):** a per-(judge, encoding) **miss/over-count analysis** in `src/analysis/` (against human labels, mirroring `bon_asr.py`'s standalone-CLI shape), and a **decode-then-judge** evaluation path (recover/decode → fixed completion rubric) reusing the existing decode step. No new attack, no new defense, no new target work.

## 9. Publication strategy (candidate — LIVE deadline re-check owed at S10)

Deadlines from `text_docs/shared/conference_timeline.md` (paper-agnostic, keep it as the single source). Paper E is off the July crunch, so it targets a later cycle:
- **Target = a MAIN conference (if pursued standalone):** an ARR cycle → EACL / ACL 2027, AAAI, or a safety venue (IEEE SaTML / S&P). A top-venue submission is the target; the pick stays deferred until the story/results firm up (EMNLP-vs-AACL precedent — settling criteria at S5/S10). **Workshops (e.g. NeurIPS JUDGe) are FALLBACK ONLY, never the target** (owner rule 2026-07-19; memory `feedback_papers_target_main_conferences`).
- **⚠️ Direction note:** the S4 confirm-gate (§4, Medium overlap = a *focused* contribution) plus the main-conference-only bar mean the *standalone* case is weak; the current lean is to **FOLD the judge-validation into Paper C's Round J** and reallocate the Paper E slot to a stronger main-conference direction. Open owner decision — see §4.
- **Fit:** AI-safety *evaluation* is a distinct, active axis from the defense/attack contributions; the paper reuses built infra, so its cost is a measurement sweep (mostly free cluster judges + a bounded gpt-5-mini pass), not a new system.

## 10. Next actions (gates)

- **S4 · Literature / scoop loop — the make-or-break (do FIRST).** `scoop-check` on the decode-blind-judge claim → `lit-review-loop` (stage → owner verify+download → read → write the review). Advance only if the delta survives.
- **S1 · External idea-check (owner hands).** The package is `idea_check.md` → cspaper.org/idea-check; bring back verdict + critiques. Fallback = internal adversarial check (fresh-context `scientific-critical-thinking` + `peer-review` pass), marked `idea-check: internal-only (debt)`.
- **S5/S6 (after the gates):** settle the main story + the measurement matrix design with a cost estimate; owner ratifies before any run. Nothing runs without the owner's go.
