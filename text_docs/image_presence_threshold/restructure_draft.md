# Paper B (AS-2) — post-split spine

**Status: spine REWRITTEN into `paper.tex` on 2026-08-08.** The title, abstract,
introduction and contribution list in the LaTeX source are now the truth; this
file records *what was decided and why*, so the body pass does not re-derive it.

⚠️ **The pre-split content of this file is dead.** It planned a spine —
*"one mechanism, three surfaces"* — that AS-2's own data refuted. Do not restore
it from git; it is preserved only in history.

---

## 1. The settled claim

> Safety-aligned VLMs condition their refusal threshold on whether an image is
> attached — a property of the interface, not of the request. The behaviour is a
> property of **particular aligned checkpoints**, arrives as a discrete
> post-training change, scales with the amount of uninterpretable visual input,
> cannot be instructed away, and is paid whether or not there is any harm to
> prevent.

**Every measurement in this paper is defense-free.** That is the paper's scope
boundary and its control against AS-7 in one sentence: no result here can be
attributed to a guardrail's design, coverage, or evaluation protocol, because
there is no guardrail. State it in the paper (it is in the Scope paragraph now),
not just here — the two papers are concurrent anonymous submissions and neither
may cite the other.

---

## 2. Forks that are now CLOSED

### 2.1 Ratio vs decoupling as the headline quantity → **DECOUPLING**

Settled 2026-08-08 during the spine rewrite. The exchange rate stays in the
paper as the hosted-model instantiation; the *decoupling* is the claim.

**Why the ratio cannot carry the paper:**

* Only `claude-sonnet-4-6`'s rate is well determined (2.8, CI [1.9, 4.8]). The
  others are [1.8, 12.5] and [3.2, 29.0] — consistent with almost anything.
* It is **undefined** on `gemini-2.5-flash` (already excluded) and on
  `qwen3-vl-8b` (2% plain-harmful ASR). Both exclusions happen for the same
  reason: no harmful headroom.
* That reason is not going away. The harmful denominators across our set run
  18 → 14 → 11 → 6 → 2%. **A quantity that becomes undefined precisely as models
  improve cannot be the headline of a paper about deployed models.**

**What the decoupling says instead:** the benign cost does not depend on there
being anything to buy. `qwen3-vl-8b` yields a harmful completion on 2% of plain
harmful requests and still pays a +29pp benign tax.

⚠️ **INTEGRITY GUARD — do not write "the cue buys nothing."** The qwen3-vl
harmful arm is an **underpowered null**, not a demonstrated zero (1 vs 2
discordant pairs). The defensible claim is the *asymmetry across the set*: the
denominator collapses as models improve while the benign cost does not track it
down. The paper states this limitation explicitly in the decoupling paragraph.

### 2.2 Title → **KEPT**

`The Presence Tax: Vision--Language Models Condition Refusal on Image Attachment
Rather Than Harm`

Accurate under the new spine, and the codename `Presence Tax` is already
registered in `text_docs/shared/papers.md` and the science `portfolio.md`. The
split changed what the paper *demonstrates*, not what the title *claims*.
(EMNLP/arXiv titles are submitted artifacts and stay untouched.)

---

## 3. What the spine now leads with

Ordered as the introduction runs:

1. **The finding** — blank canvas, defense-free, zero per-prompt information.
2. **Threshold shift, not blanket caution** — the ladder; who pays.
3. **Presence sufficient, properties set the price** — 10-arm ablation; on the
   open checkpoint the carrying axis is *size* (p=0.0004), colour and JPEG inert.
4. **Not instructable away** — ~3/4 survives; `gemini-2.5-flash` inverts +33pp.
5. **Where the effect lives** *(the new backbone)* — serving stack ruled out
   (same-weights control) → VLMs-as-such ruled out (three nulls) → **particular
   aligned checkpoints**, exhibited on open `qwen3-vl-8b` at +32/+28/+29pp.
   The tier label fails to predict it (four of five models, same label,
   +32 → +0pp).
6. **A step, not a gradient** — qwen2-vl +8 n.s. / qwen2.5-vl +1 / qwen3-vl +28.
   Post-training, not architecture or scale.
7. **Cost vs benefit, and their decoupling** — §2.1 above.
8. **The sign is not fixed** — pixtral 48→83%.
9. Alignment framing · Scope · What we do not claim · Contributions.

---

## 4. What the body pass still owes the spine

The introduction now promises results the body does not yet contain or
contradicts. In rough dependency order:

1. **Remove the AS-7 sections.** `sec:res-pareto`, `sec:res-amplification`,
   `sec:res-safety-utility`, `sec:res-decoy`, `sec:res-redundancy`,
   `sec:res-stacked`, `sec:res-deployable`, `sec:res-gated`, `sec:res-adaptive`
   — plus their tables, appendices and case studies.
2. **Rewrite `sec:res-threshold`'s open-weight paragraphs.** They currently
   assert the benign cost "does not reproduce" on open-weight models and
   conclude it is "a property of an aligned, moderated serving stack." That is
   false as written — see `experiment_matrix.md`, tier scan (xc 215).
3. **New tables** for: the tier scan, the qwen3-vl property ablation, the
   generational ladder, the qwen3-vl exchange-rate ladder.
4. **Rewrite `sec:method`.** It still describes an encoded-attack threat model
   with a defender — AS-7's framing. AS-2's manipulation is attachment alone.
5. **Limitations** — the open-weight boundary sentence needs replacing for the
   same reason as (2).
6. **Related work** — `zou2026understanding` is the closest prior work and the
   positioning still holds; re-check it once the body settles.

---

## 5. Files

* Truth: `paper/image_presence_threshold/aaai_2027_ai_alignment/aaai_aia_latex/paper.tex`
* Pre-spine-rewrite backup: `paper.tex.presplit-backup` in the same directory
  (⚠️ `paper/` is **gitignored** — there is no git history for the draft, so that
  file is the only rollback point).
* Measured numbers + integrity notes: `experiment_matrix.md` in this directory.
