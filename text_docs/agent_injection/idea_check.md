# S1 idea-check package — `agent_injection` (Paper E · "Smuggled Actions")

*Ready-to-paste distillation for cspaper.org/idea-check (S1, owner hands). Bring back: the verdict + the main critiques, especially on the novelty/scoop axis (§ "three things"). Written AFTER the S4 literature/scoop search (owner-corrected order 2026-07-19), so its novelty claims are grounded in the deep-read (`literature_review.md §14`). Fallback if cspaper is skipped: the internal adversarial pass in `# Idea Review` below, marked `idea-check: internal-only (debt)`.*

## The idea in one line

Automated **indirect-prompt-injection defenses** — spotlighting, delimiter/data-isolation, prompt-shield classifiers — are tuned on *natural-language* injections, so they share the same **decode blind spot** this line's earlier work found in content guards: an **encoded** injected instruction (a text encoding — cipher / code / set-theory / classical-Chinese — or an image render) rides *through* the defense, and the agent **decodes it and takes the harmful action**.

## Background

Prior work in this line (Papers A–C) shows *content* safety fails on **encoded / image-rendered** harm because guards inspect surface form without decoding the payload. That work targets a **model** whose only output is text. **Agents** change the setting on two axes at once: the adversary becomes a **third party** who controls data the agent *ingests* (a tool output, a retrieved document, an on-screen image — *indirect* injection), and the harm becomes an **action the agent takes** (calling a sensitive tool, exfiltrating data). Agents also carry a *new* defense layer with no pure-model analog — **injection-specific** defenses (spotlighting, data-isolation, prompt-shield). Those defenses have never been calibrated against encoded payloads.

## The problem / gap

No published work systematically measures whether an **encoded** indirect-injection payload evades **injection-specific** defenses on an agent, scored by whether the agent **completes the injected action** — nor frames it as the agents' injection defenses inheriting the content guards' decode blind spot. The literature has only scattered pieces (all confirmed by a full deep-read):
- The two rigorous agentic-IPI harnesses (**AgentDojo**, **InjecAgent**) test **natural-language** injections only.
- The founding IPI paper (**Greshake 2023**) and a NeurIPS'25 firewall paper (**Bhagwatkar**) each show **one** anecdotal encoded bypass (a Base64 Bing-Chat demo; a single Braille example vs the authors' own bespoke sanitizer, in a v2 appendix, where base64 and whitespace *failed*) — neither systematic, both explicitly "future work" or a narrow "rare-token" aside.
- Encoding-as-evasion is studied **non-agentically** (Uysal 2026: base64/hex/ROT13 on plain chatbots, no defense, no action).
- Two papers name our exact contribution as **untested future work**: **VPI-Bench** (ICLR'26) asks for "techniques to conceal malicious prompts from users while keeping them detectable by screenshot-based agents"; **Spotlighting** §5.4 flags a reversible-encoding attacker who pre-encodes the payload — never built.

## The idea (core claim)

Injection defenses recognize an *imperative natural-language surface* in ingested data (delimiting it, datamarking it, classifying it). An **encoded** instruction presents a surface they were never tuned on, yet the backbone still **decodes-and-obeys** it — the surface-vs-decoded gap of Paper C, relocated to the agent's untrusted **data channel**. We measure it directly and fix-check it:
- **Attack (§5.1, the core):** an encoded indirect-injection payload raises **injected-action success** over a plain-language payload against deployed injection defenses, **across ≥3 scaffolds × backbones**, on a standard harness (AgentDojo / InjecAgent). Success = the agent completes the injected action (agent-native metric), *not* a harmful-text verdict.
- **Falsifiable, refutation-is-a-finding:** if encoding gives no lift once an injection guard is present, that itself is a result — injection defenses, unlike alignment, would be encoding-robust.

**Seed plausibility (not hypothetical):** Reverse CAPTCHA (2026) quantifies that **tool-use amplifies compliance** with an encoded (invisible-Unicode) payload — Cohen's *h* up to **1.37**, compliance → 98–100% with tools; and this line already owns the encoders (MathEnc) and image transforms (ImgAug) that become the payloads.

## Intended contributions

1. The **first systematic, controlled** measurement of encoded indirect prompt injection as an evasion axis against **injection-specific** defenses (spotlighting / datamarking / isolation / sandwich / prompt-shield classifier), scored by **action completion**.
2. A **unifying account** — injection defenses inherit the content guards' *surface-not-decoded* blind spot (the agent coordinate of this line's coverage / decode-gap thesis).
3. A **generality result** across scaffolds × backbones, with a **plain-vs-encoded control** isolating the encoding effect, plus the **image-rendered** payload variant for VLM / computer-use agents.
4. (Later half, §5.2) an action-level **recover-before-act** defense + a flagship deployed-agent demonstration (responsible disclosure).

## Closest prior art + our delta (to pre-empt "isn't this already done?")

- **Greshake 2023 / Bhagwatkar 2025** — *one anecdotal* encoded bypass each; no sweep, no control, one defense, narrow explanation. → own only "it can happen once," not the systematic characterization.
- **Adaptive Attacks Break IPI Defenses (Zhan 2025)** — same metric + "defenses fall to evasion" frame, but **white-box GCG gibberish suffixes, not semantic encoding**. → the white-box optimizer analogue; ours is the black-box, human-readable-encoding route.
- **Spotlighting (Hines 2024)** — the defense we test; its "encoding" variant encodes the *whole document as a defender signal*, attack payload always plain English; §5.4 flags our attack and never builds it.
- **VPI-Bench (2026)** — image + agent + action, but a *plaintext* pop-up (no decode step) and no injection guard; names our gap as future work.
- **Our delta:** the *encoded/rendered payload × injection-specific defense × agent action-completion × decode-blind-spot frame* combination, systematic and controlled, is unclaimed. (S4 scoop verdict: **Level 3 / Medium Overlap, delta defensible** — more defensible than the parked `judge_reliability` line, whose insight was owned by an active subfield.)

## Venue class

AI-agent / LLM **security** — target a MAIN conference (IEEE SaTML / S&P / USENIX Security, or *ACL via ARR). Off the July AAAI crunch; a later cycle. **Workshops are fallback-only, never the target** (owner rule 2026-07-19).

## The three things we most want the idea-check to stress-test

1. **Scoop / novelty (make-or-break).** Given that the *phenomenon* has one-off anecdotes (Greshake Base64, Bhagwatkar Braille) and two papers flag the systematic version as future work, is "first systematic characterization + decode-blind-spot frame" a strong enough contribution for a main venue — or will a reviewer read it as "obvious next step, already anticipated"? This is a **hot, fast-moving field** — how much scoop-race risk?
2. **Is the framing a real contribution or a re-label?** Does "injection defenses inherit the content guards' decode blind spot" carry weight beyond "encoding evades defenses," given the field already knows encoding evades things?
3. **Is the metric/setup convincing?** Is "action completion on AgentDojo/InjecAgent, plain-vs-encoded, across scaffolds × backbones" the right rigorous design, and is the external-agent-harness build cost worth it versus a cheaper approximation?

---

# Idea Review

*(Internal adversarial pass — the S1 fallback if cspaper is skipped. Run a FRESH-context critique before trusting this; author-context rubber-stamps. Replace with the cspaper verdict when it returns.)*

**Strongest case FOR.** The gap is real and triangulated by a full deep-read: no paper unifies the four axes, two papers explicitly name the contribution as future work, and the agent-amplification premise is already quantified (Reverse CAPTCHA, Cohen's *h* 1.37). The payloads and encoders are reused from prior work, and AgentDojo gives deterministic action-level scoring (not an LLM judge an injection could also hijack). The through-line ("per-unit safety is incomplete against composed harm") makes it a clean identity extension, not a topic pivot.

**Strongest case AGAINST (the risks to clear).**
- **Hot-field scoop race.** Two papers flag this as future work → others see it too. The systematic version is an obvious next step; timing/speed matters. → Move fast; lead with the decode-blind-spot *frame* + the plain-vs-encoded *control* + the image-rendered axis, which the anecdotes lack, so the contribution is more than "we ran the sweep."
- **Build cost.** An external agent harness is a materially bigger build than the eval-only VLM setup — the honest cost of this direction. → Anchor on AgentDojo (encoders slot in as a new `attack()`), keep the attack eval-only and decoupled; defer the coupled defense (§5.2).
- **"Encoding evades" is not surprising.** The reviewer's reflex is "of course encoding evades a classifier." → The non-obvious, load-bearing results are (a) it survives against *injection-specific, provenance-based* defenses (spotlighting/isolation), not just a content classifier, and (b) the plain-vs-encoded control quantifies *how much* of the defense's protection is surface-pattern-matching.

**Verdict (provisional, internal):** a real, defensible gap (Medium overlap), with a stronger novelty position than the parked judge-reliability line — gated on moving before the fast-moving field closes it, and on accepting the external-harness build cost. Advance to S5 (main story) and an S6 design + cost estimate.
