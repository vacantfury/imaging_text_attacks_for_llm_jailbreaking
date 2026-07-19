# Research Proposal — Smuggled Actions: Encoded Indirect Prompt Injection on LLM Agents (`agent_injection`)

**Workflow stage:** S3 · project init — **preliminary proposal** (as of 2026-07-19). **Order from here (owner-corrected 2026-07-19 — keep this sequence):** (1) this preliminary proposal → (2) **S4 literature / scoop search** → (3) **`idea_check.md` written AFTER the search** so its novelty claims are grounded → (4) S5 main story → (5) S6 design + cost. Paper E, off the July AAAI crunch (Papers C/D own that); targets a later cycle (§8).

*Codename: **Smuggled Actions** (Paper E — the alias **E was reassigned from `judge_reliability`**, which parked 2026-07-19 after two Medium/High scoop results; see `text_docs/judge_reliability/proposal.md §11`). Origin: `text_docs/shared/future_work.md §5` (the agent-side line) + the §7.1 compositional-harm identity. **Attack-first** (§5.1); the defense is the deliberately-later half (§5.2). Full paper-facing title refined at writing.*

---

## 1. Decision & posture (provisional — ratify at S5)

- **Paper E = an ATTACK-FIRST agent-security paper.** The question: does an **encoded** indirect-injection payload defeat **injection-specific defenses** and drive a harmful agent **action**? It leaves the model-only setting of Papers A–C entirely — a *separate line*, not a follow-on.
- **Home: THIS repo, `agent_injection` namespace.** It reuses this line's encoder suite and image transforms **as payloads**; the genuinely new build is the agent-harness integration + the injection-defense baselines + the action-completion metric.
- **One-line identity — the AGENT coordinate of the coverage / decode-gap thesis.** Papers A–C study *where harmful content is placed* (encoding, modality) against a **model** whose only output is text and whose only adversary is the prompt author. This paper moves **both axes at once**: the adversary becomes a **third party** controlling data the agent *ingests* (a tool output, a retrieved document, an on-screen image — *indirect* injection), and the harm becomes an **action the agent takes**. The claim: **injection defenses tuned on natural-language injections inherit a decode blind spot** — an *encoded* instruction slips past them exactly as encoded harm slips past content guards in Paper C.
- **Attack-first, by design.** A payload is portable — a data blob dropped into any harness — whereas a defense must hook the agent's internals. §5.1 (the attack) stays eval-only and decoupled; §5.2 (the defense + flagship demo) is the coupled, later half. **This paper's core is the attack.**
- **Scope discipline (the lesson of this very line).** Target the **minimal agent pattern** — untrusted-data → context → action — on a **standard harness** (AgentDojo / InjecAgent) swept across backbones. **Not** a bespoke complete agent whose idiosyncratic structure would make the result coupled and un-general. Generality comes from the multi-scaffold × multi-backbone sweep, exactly as the model results here generalize across VLMs. **Multi-agent composition is a SEPARATE, later paper** (`future_work.md §7.2`), explicitly not this one.
- **Posture on scoop (honest, load-bearing).** Agent indirect-injection is a crowded field; the unclaimed sliver is **ENCODING as an evasion axis against injection-specific defenses, scored by action completion**. §4 is the make-or-break gate — run BEFORE `idea_check.md` and before any commitment.

## 2. The idea (core claim)

**Claim.** An **encoded** indirect-injection payload raises **injected-action success** over a plain-language payload against **deployed injection defenses** — spotlighting, delimiter / data-isolation, prompt-shield / classifier guards — that are tuned on natural-language injections. These defenses have **no pure-model analog**, so defeating them is a genuinely new result, not a re-run of text-side jailbreaking.

**Mechanism (the through-line).** Injection defenses detect or neutralize instructions hidden in ingested data by recognizing an imperative **natural-language surface form** (delimiting the data, datamarking it, or classifying it). An **encoded** instruction (set-theory / cipher / code / classical-Chinese, or image-rendered) presents a surface the defense was never tuned on — yet the backbone still **decodes-and-obeys** it. This is the same **surface-vs-decoded gap** as Paper C, now relocated to the agent's untrusted *data channel*.

- **Success = action completion** (the agent actually executed the injected instruction / called the sensitive tool) — the agent-native metric, **not** a harmful-text verdict.
- **Falsifiable:** encoded payloads raise injected-action success over plain-language payloads against deployed injection defenses, **across ≥3 scaffolds × backbones**. **Refutation is itself a finding** — if encoding gives no lift once an injection guard is present, that says injection defenses, unlike alignment, are encoding-robust (a clean, publishable negative).

## 3. Experiment design (preliminary — firmed at S6)

The core artifact is a matrix — **payload-encoding × injection-defense × scaffold × backbone** — measuring **injected-action success** against a programmatic ground truth of whether the sensitive action fired.

- **Payload axis.** Plain-language injection (control) vs this line's encoders (set-theory / formal-logic / code / classical-Chinese / cipher / homoglyph) vs **image-rendered** (`ir_plain`, for VLM / computer-use agents). The encoders + transforms are reused verbatim as payloads.
- **Defense axis.** No-defense (control) vs deployed injection defenses: **spotlighting** (delimiting / datamarking / encoding the data boundary), **delimiter / quarantine isolation**, **prompt-shield / classifier guards** on ingested content. Each wrapped as an evaluatable baseline, deployed as its authors intend.
- **Scaffold × backbone.** ≥3 agent scaffolds on a standard harness (AgentDojo / InjecAgent — tool-use injection benchmarks with built-in attack + utility scoring) × multiple backbones (the repo's served + API models), for generality.
- **Metric.** Injected-action success rate (attack) **and** benign-task utility (the harness's own utility score, to bound over-blocking), per cell. **Headline** = encoded payloads lift injected-action success over plain payloads *specifically where an injection defense is present*.

## 4. Novelty & prior-art — THE gate (S4, UNRUN — make-or-break; it GROUNDS `idea_check.md`)

**Preliminary — the literature search is the next step, and `idea_check.md` is written from its findings (owner-corrected order).** Agent indirect-injection is an active, crowded field; the paper survives only if ENCODING-as-evasion-axis against injection-specific defenses is unclaimed.

- **Adjacent prior art to differentiate (to be verified by the search):** AgentDojo / InjecAgent / ASB (agent-injection benchmarks) · spotlighting (Hines et al.) / data-isolation / prompt-shield (the injection defenses we test) · Imprompter and obfuscated / adversarial-suffix injection work · the general indirect-injection framing (Greshake et al.). **The most dangerous partial scoop** would be an existing "obfuscated / encoded indirect injection defeats spotlighting / prompt-shield" result — the search must find it if it exists.
- **Provisional delta:** nobody has systematically measured ENCODING (semantic + image) as an evasion axis against **injection-specific** defenses, scored by **action** completion, **across scaffolds × backbones** — the agent coordinate of this line's coverage / decode-gap identity, with a plain-vs-encoded control isolating the encoding effect.
- **Gate procedure (the corrected order):** `scoop-check` (dual-channel — signature terms + adjacent-subfield aliases: indirect prompt injection, tool-use / agent security, spotlighting / data-isolation, obfuscated / encoded injection, computer-use-agent attacks) → `lit-review-loop` (stage bib → owner verify + download → read → write the review) → **THEN write `idea_check.md`** grounded in the findings → **advance only if the delta survives.** Note: `judge_reliability` has had two scoop passes to this line's zero, so this rigor pass is owed before the two directions are compared on novelty.

## 5. Contributions (provisional)

1. **The first systematic measurement** of ENCODED indirect prompt injection as an evasion axis against injection-specific defenses (spotlighting / isolation / prompt-shield), scored by **action completion**.
2. **The agent coordinate of the coverage / decode-gap thesis:** injection defenses inherit the *surface-not-decoded* blind spot — a unifying account, not a new widget.
3. **A generality result** across ≥3 scaffolds × backbones (not a single-agent anecdote), with the plain-vs-encoded control isolating the encoding effect.
4. **(Later half, §5.2)** an action-level *recover-before-act* defense + a flagship demonstration on a deployed, recognizable agent (responsible disclosure) — the coupled, engineering-heavier second contribution.

## 6. Threats to validity

- **Scoop (§4)** — the dominant risk; gated before commitment and before `idea_check.md`.
- **Harness realism** — a benchmark harness (AgentDojo / InjecAgent) may not reflect deployed agents; mitigate with multi-scaffold coverage plus one realistic scaffold; the flagship demo (§5.2) addresses external validity but is the later half.
- **Defense fairness** — test each injection defense as its authors intend (spotlighting on the data channel, prompt-shield on ingested content) so a bypass reads as "encoding evades a *correctly-deployed* defense," not a misconfiguration (the `project_wildguard_invalid_as_asr_judge` lesson, transposed).
- **Decoder dependency** — if the backbone must itself decode the payload to act, that is the attack's *mechanism*, not a confound; note that stronger backbones (better decoders) may show MORE lift (a capability-gap echo — cite the scalable-oversight framing, do not re-own it).
- **Dual-use / disclosure** — action-harm on agents; keep the attack eval-only on benchmarks and follow responsible disclosure for any real-system demonstration.

## 7. Reused machinery + new code owed

- **Reused (no new attack build):** the encoder factory (`src/prompt_transformations/text/`) + image renderer (`ir_plain`) as **payloads**; the model registry / serving for backbones.
- **New (the real cost — be honest):** integration with an **external agent harness** (AgentDojo / InjecAgent — clone into gitignored `other_repos/` and read before wiring, per standing feedback); **injection-defense wrappers** (spotlighting / isolation / prompt-shield) as baselines; the **action-completion metric** + attack/utility scoring. This is materially bigger than the eval-only VLM setup — the honest cost of choosing this direction over the (occupied) judge line.

## 8. Publication strategy (candidate — LIVE deadline re-check at S10)

- **Target = a MAIN conference** (owner rule 2026-07-19; workshops fallback-only). Agent / LLM security maps to **IEEE SaTML / S&P / USENIX Security** and to the *ACL family (EACL / ACL / EMNLP via ARR). Off the July AAAI crunch; a later cycle. Deadlines from `text_docs/shared/conference_timeline.md` (single source); the pick stays deferred until the story / results firm up (EMNLP-vs-AACL precedent).
- **Fit:** a distinct contribution axis (agent action-harm + indirect-injection surface) from the model-side defense / attack / eval papers, inheriting this line's encoder / modality assets as payloads.

## 9. Next actions (gates — the corrected order)

1. ✅ **Preliminary proposal** (this doc).
2. **S4 · literature / scoop search — NEXT, make-or-break:** `scoop-check` on the encoded-indirect-injection claim → `lit-review-loop` (stage bib → owner verify + download → read → write the review). This grounds the novelty claim.
3. **`idea_check.md` — written AFTER the search** (owner-corrected order), carrying grounded novelty claims → cspaper.org/idea-check (owner hands); fallback = internal adversarial check, marked `idea-check: internal-only (debt)`.
4. **S5 · main story** — lock the delta + positioning; ratify with owner.
5. **S6 · design + cost** — the scaffold × backbone × payload matrix with a first-class cost estimate (external-harness API / compute footprint); owner ratifies before any run. **Nothing runs without the owner's go.**
