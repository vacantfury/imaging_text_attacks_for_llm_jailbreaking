# Research Proposal — Smuggled Actions: Encoded Indirect Prompt Injection on LLM Agents (`agent_injection`)

**Workflow stage:** **S3 · project init** (as of 2026-07-19) — FOUNDED: running name settled, namespace + subdirs created (`text_docs/` · `conf/experiment/` · `outputs/agent_injection/`), roster row added (`text_docs/shared/papers.md`, alias **E**). **This is the founding SEED, not the full proposal** — the full S3/S5 write + the S1 `idea_check.md` are the immediate next step (owner-paced). Next gate after that: **S4 literature/scoop loop** — agent injection is a crowded field, so the delta (encoding as an evasion axis) must clear its own scoop-check before any commitment.

*Codename: **Smuggled Actions** (Paper E — the alias **E was reassigned from `judge_reliability`**, which parked on 2026-07-19 after two Medium/High scoop results; see `text_docs/judge_reliability/proposal.md §11`). Origin: `text_docs/shared/future_work.md §5` (the agent-side line). **Attack-first** (§5.1); the defense is the deliberately-later half (§5.2). Full paper-facing title refined at writing.*

---

## 1. Identity & one-line posture (provisional — ratify at S5)

**The coverage / decode-gap thesis lifted from *models* to *agents*.** Papers A–C study *where harmful content is placed* (encoding, modality) against a **model** whose only output is text and whose only adversary is the prompt author. This paper changes **both axes at once**:

- The adversary becomes a **third party** who controls data the agent *ingests* — a tool output, a retrieved document, an on-screen image (**indirect** prompt injection), not the user prompt.
- The harm becomes an **action the agent takes** (calls a sensitive tool, exfiltrates data, sends on the user's behalf), not text it emits.

The through-line: this line's **MathEnc encoders** (set-theory / formal-logic / code / classical-Chinese / cipher) and **ImgAug image transforms** become the **payloads**, now delivered through the agent's untrusted data channel. The claim is that **injection-specific defenses inherit a decode blind spot** — they are tuned on *natural-language* injections, so an *encoded* payload slips past them exactly as encoded harm slips past content guards in Paper C.

## 2. Core claim (from future_work §5.1 — attack-first, provisional)

**Claim.** An **encoded** indirect-injection payload raises **injected-action success** over a plain-language payload against **deployed injection defenses** — spotlighting, delimiter/data-isolation, prompt-shield / classifier guards — that are tuned on natural-language injections. These defenses have **no pure-model analog**, so defeating them is a genuinely new result, not a re-run of text-side jailbreaking.

- **Success metric = action completion** (the agent actually executed the injected instruction / called the sensitive tool), *not* a harmful-text verdict. This is the agent-native metric.
- **Falsifiable:** encoded payloads raise injected-action success over plain-language payloads against deployed injection defenses, **across ≥3 scaffolds × backbones**. Refutation (encoding gives no lift once an injection guard is present) is **itself a finding** — it would say injection defenses, unlike alignment, are encoding-robust.
- **Why attack-first:** a payload is portable (a data blob dropped into any harness); a defense must hook the agent's internals. The attack stays eval-only and decoupled; the defense (§5.2) is the coupled, later half.

## 3. Setting & harness (scope discipline — the lesson of this very line)

Target the **minimal agent pattern** — untrusted-data → context → action — instantiated on a **standard harness** (AgentDojo / InjecAgent), swept across backbones. **Not** a bespoke complete agent whose idiosyncratic structure would make the result coupled and un-general. Generality comes from the **multi-scaffold × multi-backbone** sweep, exactly as the model results here generalize across VLMs. (Multimodal / image-borne injection and a deployed-agent flagship demo are §5.2 — the later, defense-side half; the flagship demo follows responsible disclosure.)

## 4. Novelty gate (S4 — UNRUN, make-or-break)

Agent indirect-injection is an **active, crowded field** (AgentDojo, InjecAgent, Imprompter, spotlighting, prompt-shield). **The delta is ENCODING as an evasion axis against injection-specific defenses**, measured by action completion. Before any commitment: run `scoop-check` on the specific claim (dual-channel — signature terms + adjacent-subfield aliases: indirect prompt injection, tool-use/agent security, spotlighting/data-isolation defenses, obfuscated/encoded injection, computer-use-agent attacks), then the `lit-review-loop`. The most dangerous partial scoop would be an existing "obfuscated / encoded indirect injection defeats spotlighting" result — find it if it exists. Advance only if the delta survives; note that `judge_reliability` has had two scoop passes to this line's zero, so a like-for-like rigor pass is owed here before comparing the two on novelty.

## 5. Reused assets vs new build

- **Reused (no new attack/encoder build):** the encoder factory (`src/prompt_transformations/text/`) and image renderer (`ir_plain`) — they become the **payloads**; the judge/completion-scoring machinery for the action-completion metric where it maps.
- **New (the real build cost — be honest):** an **external agent harness** integration (AgentDojo / InjecAgent), the injection-defense wrappers (spotlighting / delimiter-isolation / prompt-shield) as evaluatable baselines, and the action-completion metric. This is a materially bigger build than the eval-only VLM setup — the main honest cost of choosing this direction over the (occupied) judge line.

## 6. Publication strategy (candidate — LIVE deadline re-check owed at S10)

- **Target = a MAIN conference** (owner rule 2026-07-19; workshops fallback-only). Agent/LLM security maps to safety/security venues — **IEEE SaTML / S&P / USENIX Security** — and to the *ACL family (EACL/ACL/EMNLP via ARR). Off the July AAAI crunch (Papers C/D own that); this targets a later cycle. Deadlines from `text_docs/shared/conference_timeline.md` (single source); the pick stays deferred until the story/results firm up (EMNLP-vs-AACL precedent).
- **Fit:** a distinct contribution axis (agent action-harm + indirect-injection surface) from the model-side defense/attack/eval papers, inheriting this line's encoder/modality assets as payloads.

## 7. Next actions (gates)

- **NOW (owner-paced):** write the **full proposal** (this seed → S3/S5 body) + the **`idea_check.md`** S1 package (cspaper.org/idea-check, owner hands) — the same founding sequence used for `judge_reliability`.
- **S4 · literature / scoop loop (make-or-break):** `scoop-check` on the encoded-indirect-injection claim → `lit-review-loop`. Advance only if the encoding delta survives against the crowded agent-injection field.
- **S6 (after the gates):** design the scaffold × backbone × payload-encoding matrix with a first-class cost estimate (external-harness API/compute footprint); owner ratifies before any run. Nothing runs without the owner's go.
