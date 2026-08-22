# AS-7 · Read Access — proposal

**Title (CHANGED 2026-08-21, owner delegated: "you think deep on it and you decide"):** *Who Controls What a Guardrail Reads? The Attacker Chooses the Channel, the Evaluator Chooses the Prompt*

*(Set when the paper was re-spined onto READ ACCESS: the attacker sets the read's SCOPE (which channel carries the payload), the evaluator sets its CONTENT (which prompt fills the internal read), and the deployer sets neither. The refusal decomposition is now the INSTRUMENT that makes the read visible, not the thesis. Retired the same day: "Whose Refusal Is It? Reported Guardrail Safety Measures the Pipeline, Not the Guardrail" and "Whose Refusal Is It? The Unmeasured Contribution of Black-Box Multimodal Guardrails" (settled 2026-08-09), both of which led with attribution. Full reasoning, including the rejected alternatives, is in the title comment block at the top of `paper.tex`.)*

*(Previous working titles, retired: "What the Defense Can Read: Channel Scope and Evaluation Protocol…"; "Read Access: Channel Coverage and Oracle Inflation…". **The word "oracle" is retired from the paper** — `jailbreak oracle` (Lin et al., MLSys 2026) already names an unrelated object in this subfield. The protocol is now **granted** vs **deployable**, with one footnote recording the rename.)*

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

> **A guardrail's reported benefit is not a property of the guardrail.** A defended pipeline holds two components that can refuse — the guard and the target model's own alignment — and every headline metric is a sum over both. Two variables no evaluation records (which channel carries the payload; what text fills the defense's internal read) move the guard's own share of that safety from **0% → 41–45% → 99%**, with the pipeline described identically throughout.

**Owner-approved 2026-08-09.** The old claim — *"what a defense can read determines what it catches; what the evaluation lets it read determines how safe it looks"* — is now the **mechanism**, not the thesis. It explains *why* the share moves; the thesis is that the share is never measured and swings across essentially its whole range.

Three supporting pillars, all measured:
1. **The split is recoverable at zero cost.** A guard block substitutes a fixed string for the model's response, so guard blocks (exact match, judge-free) and model refusals (judged) are disjoint. Any collected campaign can be decomposed retrospectively.
2. **The read matters only where it reaches generation.** ECSO stage isolation: harm-verdict −7%, captioning +4%, answer-regeneration +38%. Explains the SemanticSmooth null exactly (a selection-only read conditions no candidate's text).
3. **The inflated setting is what released code produces.** ECSO's reference implementation builds TELL/CAP/SAFE from a single `line['prompt']` field with no attacker-sent vs benchmark-behaviour distinction. Under a request-transforming attack a faithful port silently evaluates on a prompt the attacker never sent. Nobody chooses it.

✅ **Joint (a) CLOSED 2026-08-10 — pre-registered and confirmed out of sample. Full record `experiment_results.md` §15.** The decomposition was specified after collection on 8 cells of one campaign and one guard family; its predictions were then written into the git-tracked preset `refusal_attribution_confirm.yaml` (commit `96a7b4e`) and **pushed before the run**, and tested on **20 cells it had never seen** (AICR job 333243, rejudge only, no target queries, no GPU; 20/20 success, n=100, fallback 0).

* **P1 — independent replicate** of the protocol grid (8 cells): deployable 28–30 blocks vs **33–45** target-own; granted 98 vs **1**. Original was 28–30 / 34–44 and 98 / ~1. Pre-registered bar (own > blocks on all 4 deployable; blocks ≥ 90 & own ≤ 10 on all 4 granted) met **8/8**.
* **P2 — guard-family generality** (12 cells, three guard families): on the IMAGE arm both text-only guards block **0/100** while the target produces **34–91** refusals; the multimodal guard blocks **98–99**. Pre-registered bar met on all 6 IMAGE cells.
* ✅ **The sharpest form of the thesis, on a design unrelated to the protocol grid:** internvl3/IMAGE, two pipelines reporting **100/100** and **91/100** judged refusals, owing **99%** vs **0%** of them to the guard.

⚠️ **Caveat reported, not smoothed:** the harm judge and the refusal judge both fire on **39/2000** held-out responses (1.9%), so ASR + refusal + neither is **not a partition**. The decomposition is unaffected — it subtracts blocks from refusals and never reads ASR. Stated in the paper's *Evidentiary status* paragraph.

ℹ️ **The 4/100 image-arm block counts in §3.1 above were the retracted prefix-heuristic number and are corrected to 0/100 here.** The paper always printed 0/100; only this file carried the stale value.

✅ **Joint (b) CLOSED 2026-08-09 — released-code audit run, full record `experiment_results.md` §14 ($0, no API, no clones).** Four further harnesses + the benchmark itself, read for two things: how many text slots one record carries, and which slot the defense's internal call reads. Result: **MM-SafetyBench** ships the plaintext (`Question` / `Changed Question`) and the attacker-sent carrier (`Rephrased Question`) as *adjacent unmarked keys of the same record* — the grant is one dictionary key away wherever that benchmark is used; **ETA** (ICLR 2025) writes a plaintext `text_only_question` into every FigStep record and reads it **nowhere in the repository** — deployable-correct by one unwired line; **MLLM-Protector** (EMNLP 2024) is structurally immune because its detector reads the target's *output*, not a prompt — which is our own read-position result holding in code we did not write; **CIDER** (EMNLP 2024 Findings) carries model-input and benchmark-behaviour as distinct documented fields — the fix, already implemented.

⚠️ **The upgrade is SMALLER than the one this section originally hoped for — do not overwrite it with the stronger sentence.** No published *number* was shown inflated: ETA never reads its dead slot, MLLM-Protector cannot be granted, CIDER is clean. The claim is **a structural hazard in how these harnesses represent an attacked prompt, with one realized instance (ours)** — *not* a documented field-wide error. Landed in the paper as two `\paragraph{}`s in §res-deployable plus a broadened contribution (iv); the second paragraph exists specifically to state this bound.

⚠️ **Do NOT cite ECSO's `model_mmsafe.py` as a second smoking gun.** Its `line["Question"]` reads sit inside the text-only baseline branch, where `Question` *is* the attacker-sent string; ECSO's own MM-SafetyBench pipeline is internally consistent and was never self-granted. The paper's claim is about the data model's inability to represent the distinction under a *request-transforming* attack, never about ECSO's own published numbers.

---

## 3. Evidence in hand

### 3.1 Channel scope — gate defenses *(measured 2026-08-08, xc job 245)*

One harmful payload, two channels, no encoding on either arm:

* **ARM T** — payload in text, no image.
* **ARM I** — the same payload rendered as plain text on a canvas; text channel replaced by the fixed placeholder `"Answer the question shown in the image."`

| defense | TEXT: blocked | IMAGE: blocked |
|---|---|---|
| wildguard (text-only) | **100/100** | **0/100** |
| llama-guard-3-8b (text-only) | 81/100 | **0/100** |
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

---

## 9. Spine and title decisions — 2026-08-21

*(This section is the home for AS-7's frame reasoning. It does NOT belong in `paper/as-7/aaai_2027_main/reviews.md`, which stores reviews. Owner correction 2026-08-21.)*

### 9.1 The paper was re-spined onto READ ACCESS

Owner asked "should we think on the main story?", then "continue, but you need think deep then act".

**Diagnosis.** The draft declared three spines in three places:

1. Title + abstract opening + contribution (i): attribution ("Whose Refusal Is It?").
2. Limitations, §"The input side may be the wrong read entirely": *"If read access is the variable that matters, which is this paper's thesis"*.
3. Conclusion's close: "state the read / state the protocol / state the split", then *"the last of these is the one we would most like to see adopted"*, back to attribution.

Symptoms beyond the inconsistency: the title promised a decomposition while the Results delivered one attribution subsection against nine on read scope and read content; and the abstract, introduction and conclusion each had to warn the reader that the two halves carry different consequences. A frame that needs the reader told twice that its branches differ in kind is a container, not a thesis.

**The body already believed the read spine**, which is why this was a correction rather than something imposed. The Results intro already read "Part 1 is the *attacker's* variable: what a defense reads *in deployment* … Part 2 is the *evaluator's*: what an *evaluation* lets it read". `tab:attribution`'s first column is headed "What the guard reads". The 2026-08-08 title note already recorded "Read access is the paper's one variable".

**The spine.** A black-box defense is a component that reads. What it is permitted to read is set by the attacker (scope: which channel carries the payload) and by the evaluator (content: which prompt fills the internal read), never by the deployer. Scope decides what the defense catches, a deployment exposure. Content decides what it appears to be worth, a literature artifact. The refusal decomposition is the INSTRUMENT that makes either visible, and it is free.

**Why not grant inflation alone** (the sharper, narrower alternative, considered and rejected): read position is predictive rather than merely organizing. It predicts the inflation ordering across four defense types (gate, where the read *is* the decision, 24–47 points; caption-mediated re-check, 12–36; selection-only smoother, ~0; wrapper, where the grant is not definable). It predicted the within-defense stage result and was *corrected* by it, since we predicted the verdict stage and the regeneration stage carries the effect. It predicts the channel blindness and its fix. It predicts ECSO's inertness against a text-only attack. A frame sharpened by data is a thesis. Taking grant inflation alone would also have discarded the channel half, which is the cleanest experiment in the paper (nothing obfuscated on either arm) and its only deployment recommendation.

**Changed, prose only, zero numbers touched.** Abstract rebuilt as read-claim / scope + instrument / content. Intro paragraphs 1–3 re-spined. `\paragraph{The split can be measured directly.}` → `\paragraph{The read is visible in the split, and the split is free.}`, its lead-in now "three settings that differ only in what the guard reads". Contribution (i) reheaded to the variable itself, decomposition demoted to instrument. Results intro: "the two halves of the read". Conclusion paragraphs 1–2 re-spined; the closing "state the split" recast as the check that catches the other two rather than the headline. Build clean; all four drift guards green; new prose carries zero dash-line connectors. Backup `paper.tex.bak-pre-read-spine`.

### 9.2 The title that followed

Owner delegated it: "you think deep on it and you decide".

**`Who Controls What a Guardrail Reads? The Attacker Chooses the Channel, the Evaluator Chooses the Prompt`**

The deciding argument: the paper's live risk is that its two halves read as two papers stapled together, and the parallel subtitle *is* the unification. One question establishes the variable; the two clauses show the same variable moved by two parties toward two different consequences.

Rejected, so they are not re-litigated:

- *"...The Attacker and the Evaluator, Not the Deployer"* — delivers the alignment sting (the party responsible for safety controls neither dimension) but names actors without showing they act on one variable, so it could describe two unrelated findings. The sting is kept in sentence 2 of the abstract, where it costs nothing.
- Identity forms (*"A Guardrail Is What It Is Allowed to Read"*) — an identity claim reads as a universal law and collides with the paper's own scope discipline ("not as a universal characterization of black-box input defenses, a claim our grid is too narrow to support"). Same failure class as the grand words the 2026-08-08 title note warns about.
- *"Guardrails Are Evaluated on a Read They Never Get"* — the sharpest and most memorable candidate, but it covers only the evaluation half and orphans Part 1.
- Abstract subtitle pairs (*the Attacker Sets the Scope, the Evaluator Sets the Content*) — precise and matched to the paper's own vocabulary, but a cold reader does not know that scope means channel. Concrete beats precise in a title.

Wording: "Controls" rather than "decides", because the claim is about standing control and not a single act. "Chooses the Prompt" is disambiguated by the question, which has already established that the subject is what the *guardrail* reads.

**`paper.tex`'s title comment block is the canonical home of this reasoning; this section is its record in the proposal.** Three consumers follow `paper.tex` and were synced in the same act: this file's title line, the `text_docs/shared/papers.md` roster row, and the artifact bundle's `scripts/artifact_files/as7/{README.md,pyproject.toml}` (both had carried the old title into a reviewer-visible file). Bundle rebuilt after the sync: 598 files, 1.7 MB, anonymization verify passed.
