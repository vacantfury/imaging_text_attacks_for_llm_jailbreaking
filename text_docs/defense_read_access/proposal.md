# AS-7 · Read Access — proposal

**Title (working):** *What the Defense Can Read: Channel Scope and Evaluation Protocol in Black-Box Multimodal Guardrails*

**ID:** AS-7 · **Codename:** Read Access · **Namespace:** `defense_read_access` · **Venue target:** AAAI-27 AI Alignment track · **Registered:** 2026-08-08 (owner order), split out of AS-2.

---

## 1. Why this paper exists (read this first)

AS-7 is not a new investigation. It is the **defense-and-evaluation half of AS-2 (Paper B)**, separated when AS-2's own data refuted the single-paper framing.

AS-2 claimed *"one mechanism, three surfaces"*: a presence cue visible in (i) defense control flow, (ii) defense coverage, and (iii) the model's own refusal threshold. **The paper's own tables refute the unity.** `internvl3-8b` and `pixtral-12b` show **−43pp and −37pp** of ECSO decoy amplification while their benign refusal threshold does not move at all (**+7pp n.s., −2pp n.s.**). The defense-level effect occurs at full strength on models with *no* model-level presence sensitivity — so the two are **causally independent**. They shared a description, not a mechanism.

That dissociation does three things at once, and every one of them matters for this paper:

1. It **justifies the split** on correctness grounds rather than taste.
2. It gives AS-7 a **free control**: this paper can state that its effects do not require the model-level threshold effect, and prove it from data it reports itself.
3. It **removes AS-7's dependence on AS-2**, which is required because the two are submitted concurrently and neither may cite the other (see §6).

---

## 2. The claim

> **What a black-box input defense can read determines what it catches; what the evaluation lets it read determines how safe it looks.**

One idea with a deployment side and a measurement side. Everything below is an instance of it — this is deliberately *not* a list of four unrelated failure modes (an earlier framing called this a "decomposition"; that was wrong, because the components are not additive on a given cell — see §7).

---

## 3. Evidence in hand

### 3.1 Channel scope — gate defenses *(measured 2026-08-08, xc job 245)*

One harmful payload, two channels, no encoding on either arm:

* **ARM T** — payload in text, no image.
* **ARM I** — the same payload rendered as plain text on a canvas; text channel replaced by the fixed placeholder `"Answer the question shown in the image."`

| defense | TEXT: blocked | IMAGE: blocked |
|---|---|---|
| wildguard (text-only) | **100/100** | **4/100** |
| llama-guard-3-8b (text-only) | 81/100 | **4/100** |
| guardreasoner-vl-7b (multimodal) | 99/100 | **99/100** |

Text-only classifiers collapse from 100% / 81% to 4% when the payload merely changes channel. A multimodal guard closes the gap completely.

**Two design points that are load-bearing — do not lose them in a rewrite:**

* **The arms are deliberately UN-ENCODED.** Every earlier channel experiment in this line moved the payload *and* encoded it, so a guard's miss could always be attributed to obfuscation. Here nothing is obfuscated: the classifier misses the payload purely because the bytes are pixels. This removes the last alternative explanation and is the reason this experiment is worth more than the older ones.
* **Read the BLOCK RATE, not the ASR.** The target (`qwen3-vl-8b`) has an undefended ASR of 3–6% on this set, so ASR is floor-bound and cannot show the effect. The guard's own decision is not floor-bound. Any rewrite that reports this result as an ASR delta has thrown the signal away.

### 3.2 Channel scope — transform defenses *(inherited from AS-2's collection)*

* **SAGE** sanitises the text channel and leaves the image uncovered: an image rendering the payload the text *already carries* — supplying no new information — restores **+36pp** of attack success on `gpt-4o-mini` (p = 2.9e−11), replicated across two collection windows.
* **ECSO** is caption-mediated and branches on image presence: against a text-only encoded jailbreak it is inert **by construction**, returning byte-identical responses to the undefended model on all 100 prompts, while a decoy image triggers it fully (up to −63pp ASR). Framed correctly this is a **threat-model** observation — *the attacker, not the defender, decides whether the defense executes* — not a bug report.
* **Stacking both** narrows the gap from +36 to +16pp and does not close it.

### 3.3 Protocol grant — the evaluation side *(inherited)*

Scored under an **oracle** protocol that hands the defense the *unencoded* request — an oracle no defender facing an encoded attack possesses — ECSO's measured benefit is inflated by **18 to 60pp on six of seven cells**, against **15 to 27pp on three of seven** under the deployable protocol. **The largest single effect previously published by this line does not survive the correction.** Reporting this is a feature of the paper, not an embarrassment: it is the same lesson as the rest of the work applied to ourselves.

### 3.4 Trivial reject *(inherited)*

SAGE + decoy on the Gemini family reaches **74–100% benign refusal**. Its near-zero ASR is *bought* by refusing benign traffic, not earned by detection. Pair every ASR number with its benign counterpart or the safety claim is unreadable.

### 3.5 The deployable mitigation and its limit *(inherited)*

Detector-gated attachment recovers the safety benefit at **zero** benign inflation where detector recall is high (~100% on `code_attack`) and collapses where it is not (9–16% on `formal_logic`). **Detector recall — not the image — is the binding constraint** on any deployment of this cue.

### 3.6 Adaptive attacks *(inherited)*

Two attacks targeting the caption-mediated re-check on `gpt-4o-mini` (n=50): best recovery 6→24% against 78% undefended. Naive stacking of adaptive tricks *backfires* (A&B ends lower than A alone, because the aggressive preamble triggers the model's own refusals).

---

## 4. The one open gap before submission

**The oracle-inflation artifact is demonstrated on ONE defense family (ECSO).** That is the paper's most generalizable component and its narrowest evidence.

**Task:** show the oracle-vs-deployable gap on **≥3 defense families**, ideally including one that is not caption-mediated (SAGE, SemanticSmooth, and a guard-model gate are the natural three). Self-served targets and guards make this cheap — judge cost only.

**Why it is the gate:** with one family the contribution is *"we mis-measured ECSO."* With three it is *"this is how input defenses get mis-measured,"* which is the difference between a correction and a paper.

---

## 5. Proposed section arc

1. Defenses are channel-scoped, and the gap is enormous (§3.1) — lead with the un-encoded gate result; it is the cleanest evidence in the paper.
2. It is a design choice, not a law — the multimodal guard closes it (§3.1).
3. Transform defenses have the same shape (§3.2).
4. Defense-in-depth narrows without closing (§3.2).
5. The measurement analogue: protocol grant (§3.3), with the self-correction stated plainly.
6. Safety that was bought rather than earned (§3.4).
7. The deployable mitigation and its binding constraint (§3.5).
8. Adaptive attacker (§3.6).
9. **Scope boundary** (§6) — explicit, in the paper, not just here.

---

## 6. Scope boundaries — these go IN the paper

**vs AS-2 (concurrent submission).** AAAI's dual-submission bar is on work that does *"not constitute distinct scientific contributions, whether submitted to AAAI-27 **or another archival conference or journal**"* — it is **cross-venue**, so routing the two papers to different tracks or venues softens it by exactly nothing. Distinctness must be carried *in the papers*:

* AS-7 states that it makes **no claim about model-level refusal behaviour**.
* AS-7 **runs and reports the dissociation as a control** — internvl3 / pixtral, full amplification with no threshold shift — to rule out AS-2's mechanism as an explanation of its own effects. A control is not a contribution, so reporting it here is not overlap.
* Neither paper may cite the other; both are anonymous concurrent submissions. **AS-7 must therefore motivate itself entirely from evaluation correctness and deployment coverage**, never from "the model has a presence bias."

**vs AS-6 (guard internals, repo `model_internals_safety`).** AS-6 probes guard **activations** to separate *never decoded* from *decoded but never blocked*. **AS-7 is black-box throughout and claims no mechanism inside the guard.** AS-7's channel result — a text guard never *receives* an image payload — sits upstream of both of AS-6's links and supplies it a hypothesis; per AS-6's own scope note the siblings provide "hypotheses, not measurements," and AS-6 re-measures in its own harness. Keep the division: **AS-7 behaviour, AS-6 activations.**

---

## 7. Framing traps recorded from the split deliberation

* **Do not call §3 a "decomposition."** It is a taxonomy of ways a reported number misleads, with one quantified instance each. A decomposition would be additive — *gain = detection + protocol + gating + coverage* summing on a given cell — and we cannot do that. Overclaiming this was corrected on 2026-08-08.
* **Do not frame the paper as "these defenses have blind spots."** That invites the fatal objection that ECSO was never designed for text-only input. Frame around **what the evaluation and the deployment let the defense read**; the ECSO fact then enters as a threat-model observation rather than a criticism.
* **Do not report the gate result as an ASR delta** (§3.1).
* **Do not assume the target's ASR floor is informative.** On well-aligned targets ASR saturates near zero; that is a power problem, not a finding.

---

## 8. Where the data is

⚠️ **Pre-split runs live under `outputs/image_presence_threshold/`, not under this paper's namespace.** The output tree was renamed wholesale at the split rather than divided, because splitting it would have broken the `upstream_ref.source_dir` provenance chains. **AS-7's historical cells are identified by their `campaign` field, never by directory** — `paper_b_guard_channel`, `paper_b_channel_coverage`, `paper_b_deployable_*`. New AS-7 runs write to `outputs/defense_read_access/`.

* Presets: `conf/experiment/defense_read_access/`
* Measured results + integrity notes: `text_docs/defense_read_access/experiment_results.md` *(gitignored)*
* Pre-split working record (both papers): `text_docs/image_presence_threshold/experiment_matrix.md` *(gitignored)*
* Paper source: `paper/as-7/aaai_2027_ai_alignment/aaai_aia_latex/`
* Registry of record: science repo `portfolio.md` → the AS-7 card.
