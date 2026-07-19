# S1 idea-check package — `judge_reliability` (Paper E · "Blind Judges")

*Ready-to-paste distillation for cspaper.org/idea-check (S1, owner hands). Bring back: the verdict + the main critiques, especially on the novelty/scoop axis (§ "three things"). Fallback if cspaper is skipped: the internal adversarial pass in `# Idea Review` below, marked `idea-check: internal-only (debt)`.*

## The idea in one line

Automated safety **judges** share the **decode blind spot** of the defenses they measure: when harm is encoded or image-rendered, they mis-score it in *both* directions — so the field's encoded-attack ASR numbers are systematically miscalibrated — and a **decode-then-judge** step recovers the true verdict.

## Background

Safety research measures jailbreak attacks and defenses with automated judges (fine-tuned classifiers like HarmBench-cls / LlamaGuard / WildGuard, reasoning guards, and LLM-judges). A parallel line (this repo's Papers A–C) shows *defenses* fail on **encoded / image-rendered** harm because they inspect surface form without decoding the payload — and Paper C fixes it with recover→decode→guard. The judges used to *evaluate* all of this have never been calibrated on the same encoded inputs.

## The problem / gap

No published work systematically, quantitatively measures how much automated safety judges **under-count** harm when it is encoded (cipher / base64 / set-theory / formal-logic / code / classical-Chinese) or **image-rendered**, nor how much they **over-count** by anchoring on encoded surface cues. The literature has only adjacent pieces — judges fragile to style, anchoring on malicious tone, degrading under distribution shift — never the per-judge × per-encoding × human-labeled calibration, and never the framing that the judges inherit the *defenses'* decode gap.

## The idea (core claim)

Judges score **surface form, not decoded behavior**, so on encoded/rendered harm they fail two ways with one mechanism:
- **Under-count** — genuine harm is encoded, the judge never decodes it, scores it "safe" → inflates defense success.
- **Over-count** — the judge fires on a malicious-looking encoded string or a harmful task echoed as a non-executing code literal → inflates attack ASR.

The remedy is the measurement-side mirror of Paper C: **decode-then-judge** — recover/decode to plaintext behavior, then apply a fixed behavior-completion rubric. It should shrink both error directions and yields a practical which-judge / decode-first recommendation.

**This is not hypothetical — the seed evidence is in hand:** WildGuard 41–68% false positives on the strategy/code channel (Paper D R3); gpt-5-nano 2–3× absolute-ASR inflation vs stronger judges (Paper C); a validated tri-judge Round-J human-anchored study (gpt-5-mini κ=0.68 vs 100 human labels).

## Intended contributions

1. First **systematic per-judge × per-encoding × human-labeled** calibration of safety-judge reliability on encoded/rendered harm (miss rate + over-count).
2. A **single unifying mechanism** (surface-not-decoded) that explains both false-negatives and false-positives.
3. **Decode-then-judge** as a cheap, measured remedy + a which-judge recommendation.
4. A **validity correction**: how much published encoded-attack ASR is the judge's error, not the defense's.

## Closest prior art + our delta (to pre-empt "isn't this already done?")

- **StrongREJECT** (NeurIPS'24) — better autograder for *plain* jailbreaks; does not touch encoded/rendered harm or the per-encoding calibration.
- **Know Thy Judge** (2503.04474) / **Confusion is the Final Barrier** (2508.16347) — judges fragile to style / anchor on tone; qualitative and *not* about encoding-specific decode failure.
- **A Coin Flip for Safety** (2603.06594) — judges degrade under distribution shift; not encoding-indexed.
- **Schwinn et al.** — BoN best↔worst flips under judge correction (**partial scoop** of the "judges change conclusions" point).
- **Our delta:** the *encoding-indexed, human-anchored* miss/over-count table **plus** the decode-blind-spot framing (judges inherit the defenses' gap) **plus** the decode-then-judge fix. That specific object is unclaimed.

## Venue class

AI-safety **evaluation methodology** — target a MAIN conference (ARR → EACL/ACL 2027, AAAI, or SaTML/S&P). Workshops are fallback-only, never the target (owner rule 2026-07-19). Off the July crunch.

## The three things we most want the idea-check to stress-test

1. **Scoop / novelty (the make-or-break).** Is the per-judge × per-encoding × human-labeled calibration genuinely unclaimed once you include the 2026 judge-reliability wave and any multilingual/obfuscation-judge work? Where is the closest existing table?
2. **Is the framing a real contribution or a re-label?** Does "judges inherit the defenses' decode blind spot + decode-then-judge fix" carry weight beyond "LLM judges are unreliable," or will reviewers read it as StrongREJECT-on-encodings?
3. **Is the finding actionable enough to matter?** Given that gpt-5-mini already largely corrects the inflation, is "use a strong judge + decode first" a strong enough recommendation, or does the paper need the mechanism/mirror to be the load-bearing contribution?

---

# Idea Review

*(Internal adversarial pass — the S1 fallback if cspaper is skipped. Run a FRESH-context critique before trusting this; the author-context tends to rubber-stamp. Replace with the cspaper verdict when it returns.)*

**Strongest case FOR.** The measured seed evidence is unusually strong for an idea-stage paper — the miss/over-count phenomenon is already documented across two of this repo's papers, so the core result is de-risked before a single new run. The infra cost is a measurement sweep on mostly-free judges, and the framing (evaluation coordinate of the compositional-coverage identity) gives it a clean, ownable through-line rather than a generic "judges are unreliable" pitch.

**Strongest case AGAINST (the risks to clear).**
- **Novelty is the whole ballgame and it is thin at the surface.** If a 2026 paper already reports an encoding-indexed judge miss-rate, the delta collapses to the decode-then-judge fix alone — publishable, but a workshop-tier contribution, not a main-venue one. → The S4 scoop-check is not optional; it gates everything.
- **The "over-count vs under-count" story risks being two half-papers.** The under-count (StrongREJECT-adjacent) and the over-count (WildGuard-FP) are unified only by the surface-not-decoded mechanism; if that mechanism does not hold up under scrutiny, the paper reads as a grab-bag. → Make the mechanism the spine, not the table.
- **Judge-vs-guard fairness.** Scoring a WildGuard (own-taxonomy input guard) as if it were a HarmBench completion judge invites a "wrong tool" rebuttal. → Fix the rubric (HarmBench completion) and frame the finding as calibration-against-a-fixed-rubric, per `project_wildguard_invalid_as_asr_judge`.

**Verdict (provisional, internal):** promising and de-risked on *results*, but its ceiling is set entirely by the S4 scoop gate. Advance to the literature/scoop loop first; commit only if the encoding-indexed calibration is unclaimed. If scooped on the calibration, fold the judge-validation into Paper C (Round J) rather than run a weak standalone — do NOT downgrade to a workshop (owner rule 2026-07-19).
