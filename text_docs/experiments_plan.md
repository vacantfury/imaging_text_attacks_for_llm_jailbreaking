# Experiment Plan — Defense Destroyer (post-refactor, May 23 2026)

## Story

IR (image rendering) is a **defense destroyer**, not a defense and not an
attack: a wrapper applied on top of an existing text-encoded attack that
defeats advanced black-box defenses (SAGE, ECSO, SemanticSmooth) which
successfully block the bare encoded attack. No published defense-destroyer
method exists to compete with — the contribution is to establish the
category and demonstrate cross-defense generality.

**Core empirical claim (per defense D and encoded attack A):**

- `ASR(A | no defense)` is moderate-to-high.
- `ASR(A | D)` is low (D defends against the bare attack).
- `ASR(IR(A) | D) ≫ ASR(A | D)` (IR wrapping destroys D).
- `ASR(IR(A) | no defense) ≈ ASR(A | no defense)` (destroyer effect is
  *defense-specific*, not a generic ASR boost).

See `proposal.md` and `old_experiments_plan.md` for the full pivot rationale.

---

## Past-data destroyer-gap ranking (basis for model prioritization)

From the Stage 10b SAGE-on-frontier + Stage 10e Round 1 destroyer probes
already in the bag. **Destroyer gap = `ASR(ir_plain-wrapped + SAGE) − ASR(text + SAGE)`** (larger = easier to destroy):

| Model | set_theory gap | formal_logic gap | Tier |
|---|---:|---:|---|
| **Gemini 2.5 Flash Lite** | **+29pp** | **+14pp** | **A (proven strong destroyer)** |
| **Gemini 2.5 Flash** | **+11pp** | **+18pp** | **A (proven strong destroyer)** |
| Claude Sonnet 4.6 | +2pp | +5pp | B (modest) |
| GPT-5-mini | −1pp | +4pp | C (essentially zero) |
| GPT-5.4 | 0pp | +2pp | C (essentially zero) |
| GPT-5.4-mini | 0pp | 0pp | C (essentially zero) |
| GPT-5.4-nano | +1pp | 0pp | C (essentially zero) |

**Pattern: destroyer fires hard on Gemini-flash family, modestly on Claude,
essentially never on GPT family.** Likely mechanism: GPT has strong
image-safety alignment (Stage 9c shows IR alone reduces ASR −22 to −32pp on
GPT-5.4 — the model refuses images harder than text); when image safety is
strong, IR triggers refusal regardless of upstream defense, so the destroyer
can't fire. When image safety is weak (Gemini-flash), the encoded text
passes through and bypasses the text-side terminal defense check.

**Cost-first prioritization (cheaper models first; Claude deferred):**
The expensive frontier-tier models (GPT-5.4 $2.50/$15.00, Claude Sonnet 4.6
$3.00/$15.00, Gemini 2.5 Pro $1.25/$10.00) are *deferred* to a later round.
Round 1 runs on cheap models only:

- **Gemini 2.5 Flash Lite** ($0.075/$0.30) — cheapest AND biggest destroyer signal.
- **Gemini 2.5 Flash** ($0.30/$2.50) — cheap, also strong destroyer signal.
- **GPT-5.4-nano** ($0.20/$1.25) — cheap, GPT-family scope-bound check.
- **GPT-5-mini** ($0.25/$2.00) — cheap, GPT-family extra coverage.

Both GPT and Gemini families covered, no model > $0.30/M input. Claude is
deferred to future rounds when budget permits.

---

## Pipeline (post-refactor)

Two modes only.

| Mode | What | Output |
|---|---|---|
| `prompt_transform` | chain of transformations one-by-one, one subfolder per step with cumulative results.json | `outputs/prompt_transform/<benchmark>/<chain>_<ts>_<rand>/<step_name>/` |
| `defense+evaluate` | reads a `prompt_transform` subfolder, runs Defense+model+judge | `outputs/defense+evaluate/<benchmark>/<model>_<defense>_<chain>_<ts>_<rand>/` |

Defenses: `no_defense`, `sage`, `ecso`, `semantic_smooth`.
Transformations: 9 legacy encoders, 2 new attacks (`deep_inception`,
`code_attack`), 4 image renderers (`ir_plain`, `ir_fc_typo`, `ir_figstep`,
`ir_fc_flowchart`), 2 companion-image transforms (`blank_image`,
`constant_image`).

---

## Prerequisites — one-time migration of past data (USER-RUN before any experiment)

Old `outputs/text_encode/...` + `outputs/imaging/...` dirs are reusable as
`prompt_transform` chain inputs after a one-off conversion. The script

    temporary_scripts/migrate_old_to_prompt_transform.py

does this. Run it ONCE up front; chains that are migrated then count as
"already done" for any Round X.1 below.

**Recommended migration commands (run all before any experiment):**

```bash
# Harmful benchmarks (set_theory + formal_logic + classical-language family,
# plain renderer → ir_plain chain).
python temporary_scripts/migrate_old_to_prompt_transform.py \
    --benchmark harmbench --renderer plain
python temporary_scripts/migrate_old_to_prompt_transform.py \
    --benchmark jailbreakbench --renderer plain
python temporary_scripts/migrate_old_to_prompt_transform.py \
    --benchmark orbench_harmful --renderer plain

# Benign benchmarks (for Block 6 over-refusal — uses pure-text chains only,
# but the migrator still produces both encoder + renderer subfolders; defense+
# evaluate just consumes the encoder subfolder).
python temporary_scripts/migrate_old_to_prompt_transform.py \
    --benchmark jailbreakbench_benign --renderer plain
python temporary_scripts/migrate_old_to_prompt_transform.py \
    --benchmark orbench_benign_hard --renderer plain

# Optional: fc_typography pairs where they exist (Block 4 renderer-variant).
python temporary_scripts/migrate_old_to_prompt_transform.py \
    --benchmark harmbench --renderer fc_typography
```

After migration, each Round X.1 below only schedules **chains that have NO
past-data counterpart** (new encoders like `semantic_camo`, new attacks
like `deep_inception` / `code_attack`, new companion-image transforms like
`blank_image` / `constant_image`, new renderer variants like `ir_fc_typo`
if no past fc_typography dir exists for that encoding).

---

## Datasets / Row Limits

Eval-stage row limit: first 100 rows (`prompt_range: [0, 99]`). Upstream
uses full datasets.

Primary harmful: **HarmBench (100 rows)**. Supporting: JailbreakBench
harmful (100). Over-refusal: JBB benign + OR-Bench benign_hard (100 each).

---

## Experimental Blocks

### Block 1 — Headline destroyer matrix [CRITICAL, gating]

The centerpiece. Encoders: `set_theory`, `formal_logic` (primary).
Defenses: `no_defense`, `sage`, `ecso`, `semantic_smooth`. Multimodal:
`(none)` vs `ir_plain` (`keep_text=false`). Models per the **Target
Models** table below.

**Past-data reuse:** SAGE and no_defense cells on R1 models are already in
P2 (`experiment_results.md`). Block 1 only schedules NEW runs (ECSO + SS
on R1 models, plus all cells for untested models). SemanticSmooth on
`ir_plain` is N/A — multimodal SS is undefined; documented out-of-scope.

#### Round 1.1 — Stage 1 (`prompt_transform`)

**No new chains.** T1–T4 (`[set_theory]`, `[set_theory, ir_plain]`,
`[formal_logic]`, `[formal_logic, ir_plain]`) come from the one-time
migration (see Prerequisites). After migration they sit at
`outputs/prompt_transform/harmbench/migrated_llm_set_theory_ir_plain_*/`
and `outputs/prompt_transform/harmbench/migrated_llm_formal_logic_ir_plain_*/`,
each with `llm_set_theory/` and `ir_plain/` subfolders.

When Round 1.2 below refers to T1 / T2 / T3 / T4, those are the migrated
subfolders.

#### Round 1.2 — Stage 2 (`defense+evaluate`), R1 cheap models [GATING]

Consumes Round 1.1 chains. Models: Gemini 2.5 Flash Lite, Gemini 2.5
Flash, GPT-5.4-nano, GPT-5-mini (4 models). Tasks:

| Group | Defense | Chains used | Models | Count |
|---|---|---|---|---|
| ECSO (NEW) | `ecso` | T1, T2, T3, T4 | 4 R1 models | 16 |
| SS-text (NEW) | `semantic_smooth` | T1, T3 (pure-text only) | 4 R1 models | 8 |
| Backfill | `no_defense` | T1, T2, T3, T4 | GPT-5-mini only (P2 missing) | 4 |

**Total Round 1.2: 28 tasks**. Estimated cost: **~$10–18**.

SAGE + no_defense for the other 3 R1 models reused from P2 — no new runs.

**Gating decisions at end of Round 1.2** (before Round 1.3 / 1.4 / 1.5):
- If destroyer gap fires on **ECSO across both Gemini models on ≥1 encoding**: cross-family destroyer is the centerpiece. Proceed to all later rounds.
- If only SAGE shows the gap (ECSO + SS resist): narrow to a SAGE-specific finding (publishable; Findings tier). Skip Round 1.6 (expensive frontier).
- If only Gemini 2.5 Flash Lite fires (Gemini 2.5 Flash collapses): model-specific finding (AIES). Replicate on 1 more mid-tier Gemini-family model before final scoping.
- If GPT-family models also show ECSO destroyer gap (they shrugged off SAGE in past data): MAJOR upgrade — paper becomes "destroyer breaks multimodal-aware defenses." Re-prioritize.

#### Round 1.3 — Stage 1, encoding expansion [conditional on 1.2 passing]

Mixed: classical_chinese is migrated; semantic_camo is NEW.

| Task | Chain | Source |
|---|---|---|
| T5 | `[classical_chinese_simplified_literary]` | migrated (Prerequisites) |
| T6 | `[classical_chinese_simplified_literary, ir_plain]` | migrated (Prerequisites) |
| T7 | `[llm_semantic_camo]` | **NEW** — run prompt_transform |
| T8 | `[llm_semantic_camo, ir_plain]` | **NEW** — run prompt_transform |

NEW work: 2 prompt_transform tasks (~$1–2 for semantic_camo encoder LLM
calls + local rendering).

#### Round 1.4 — Stage 2, R2 cluster (Qwen + Pixtral) [free; depends on Round 1.1]

Consumes Round 1.1 chains. These models are completely untested under any
defense, so the full matrix is new:

4 defenses × 4 chains (T1–T4) × 2 cluster models = **32 tasks**. Cost: **$0** (NURC cluster).

#### Round 1.5 — Stage 2, R2 mid-cost + encoding expansion [conditional]

Two sub-groups, both consume earlier Stage-1 chains:

| Sub-group | Defense | Chains | Models | Count |
|---|---|---|---|---|
| Mid-cost models, primary encodings (new cells only) | ecso, ss-text | T1–T4 (ecso), T1+T3 (ss) | GPT-5.4-mini, Gemini 3 Flash Preview | (8+4) × 2 = 24 |
| R1 models, expansion encodings (full matrix — no past data) | all 4 | T5–T8 | 4 R1 models | 4 × 4 × 4 = 64 |

**Total Round 1.5: ~88 tasks**. Estimated cost: **~$25–40**.

#### Round 1.6 — Stage 2, R3 expensive frontier [deferred; budget-gated]

Consumes Round 1.1 chains. Only new cells (P2 covers SAGE + no_defense
for these models already):

4 defenses × 4 chains × 2 models (GPT-5.4, Claude Sonnet 4.6), minus
past-data cells = **~20 tasks**. Cost: **~$20–35**.

Only run after Round 1.2 + Round 1.4 + Round 1.5 results are in and
justify the spend.

### Block 2 — Specificity ablation [SUPPORTING, runs in parallel with Block 1.2]

Rules out "destruction is just from any image input." Swap `ir_plain` for
`blank_image` (true blank PNG) or `constant_image` (rabit.jpeg) — both
default `keep_text=true` (text+companion-image ablations).

**Expected if destroyer is IR-specific:**
`ASR(blank_image + encoded text | D)` ≈ `ASR(constant_image + encoded text | D)` ≈ `ASR(A | D)` — defenses still hold for blank/constant.

#### Round 2.1 — Stage 1 (`prompt_transform`), cheap setup

Run 2 `prompt_transform` tasks on HarmBench (~$1):

| Task | Chain |
|---|---|
| T9  | `[set_theory, blank_image]` |
| T10 | `[set_theory, constant_image]` |

(Re-uses encoded set_theory text — only the companion image is new.)

#### Round 2.2 — Stage 2 (`defense+evaluate`), cheap Gemini models

Consumes Round 2.1 chains. Models: Gemini 2.5 Flash Lite + Gemini 2.5
Flash.

4 defenses × 2 chains (T9, T10) × 2 models = **16 tasks**. Cost: **~$5–10**.

If Block 1 Round 1.2 shows GPT-family ECSO destroyer signal, optionally
extend to GPT-5.4-nano (+8 tasks).

### Block 3 — Cross-attack-family probe [STRENGTHENS GENERALITY; after Block 1.2 passes]

Show destroyer also breaks defenses for non-symbolic attacks. Replace
the encoder (set_theory / formal_logic) with `deep_inception` (prose
template) or `code_attack` (Python-stack code template).

#### Round 3.1 — Stage 1 (`prompt_transform`), template-attack chains

Run 4 `prompt_transform` tasks on HarmBench (~$0 — pure templates, no
encoder LLM):

| Task | Chain |
|---|---|
| T11 | `[deep_inception]` |
| T12 | `[deep_inception, ir_plain]` |
| T13 | `[code_attack]` |
| T14 | `[code_attack, ir_plain]` |

#### Round 3.2 — Stage 2 (`defense+evaluate`), cheap Gemini models

Consumes Round 3.1 chains. Models: Gemini 2.5 Flash Lite + Gemini 2.5
Flash. SS-text only on pure-text chains (T11, T13).

| Defense | Chains | Models | Count |
|---|---|---|---|
| no_defense | T11–T14 | 2 | 8 |
| sage | T11–T14 | 2 | 8 |
| ecso | T11–T14 | 2 | 8 |
| semantic_smooth | T11, T13 (pure-text only) | 2 | 4 |

**Total Round 3.2: 28 tasks**. Cost: **~$10–15**.

### Block 4 — Renderer variant [LIGHT ABLATION; after Block 1.2 passes]

Confirm destroyer survives different rendering styles. Swap `ir_plain`
for `ir_fc_typo` on one cheap Gemini model + 1 encoding.

#### Round 4.1 — Stage 1 (`prompt_transform`), new renderer chain

Run 1 `prompt_transform` task on HarmBench (~$0.5):

| Task | Chain |
|---|---|
| T15 | `[set_theory, ir_fc_typo]` |

Pure-text baseline (T1) reused from Block 1 Round 1.1.

#### Round 4.2 — Stage 2 (`defense+evaluate`), one cheap Gemini model

Consumes T1 + T15. Model: Gemini 2.5 Flash Lite.

| Defense | Chains | Count |
|---|---|---|
| no_defense | T1, T15 | 2 |
| sage | T1, T15 | 2 |
| ecso | T1, T15 | 2 |
| semantic_smooth | T1 only (text) | 1 |

**Total Round 4.2: 7 tasks** (no_defense T1 reused from P2 — drops to
**6 new tasks**). Cost: **~$1–2**.

### Block 5 — Mechanism analysis on open-source VLMs [QUALITATIVE; after Block 1.4]

Hidden-state PCA on Qwen2.5-VL-7B / Pixtral-12B for (pure encoded text,
ir_plain-wrapped image-only) under each defense. Probes WHERE in each
defense pipeline the destroyer slips through.

#### Round 5.1 — no new Stage 1

Reuses Block 1 Round 1.1 chains (T1–T4) — already consumed by Block 1
Round 1.4. Hidden states extracted directly from those `defense+evaluate`
runs (Qwen + Pixtral).

#### Round 5.2 — analysis only (not a new `defense+evaluate`)

Hidden-state PCA + attention probing on saved activations from Block 1
Round 1.4. Output: figures for the paper's mechanism section.

**Cost:** $0 (cluster + local computation only; no API calls).

### Block 6 — Over-refusal cost [SUPPORTING; parallel with Block 1.2, independent infra]

Each defense's benign refusal on JBB-benign + OR-Bench benign_hard
(100 rows each). Pair with destroyer-matrix harmful ASR for the
safety-utility Pareto frontier.

#### Round 6.1 — Stage 1 (`prompt_transform`), benign encoding

**No new chains.** T16–T19 (set_theory + formal_logic on JBB-benign and
OR-Bench benign_hard) come from the one-time migration. After running
the Prerequisites commands for `jailbreakbench_benign` and
`orbench_benign_hard`, the migrated `llm_set_theory/` and `llm_formal_logic/`
subfolders are what Round 6.2 consumes.

(No `ir_plain` destroyer needed here — over-refusal is about defenses,
not the destroyer. Only the pure-text encoder subfolders are used.)

#### Round 6.2 — Stage 2 (`defense+evaluate`), cheap models × benign

Consumes Round 6.1 chains. Models: Gemini 2.5 Flash Lite, GPT-5.4-nano,
GPT-5-mini (3 cheap models — drop Gemini 2.5 Flash to halve cost).

4 defenses × 4 chains (T16–T19) × 3 models = **48 tasks**. Cost: **~$5–10**.

Judge: `jbb_refusal` for JBB-benign chains, `orbench` for OR-Bench
chains (canonical per-benchmark dispatch).

---

## Target Models (consolidated, cost-tiered)

| Round | Model | Provider | Cost ($/M in/out) | Past destroyer signal |
|---|---|---|---|---|
| **R1 (cheap)** | Gemini 2.5 Flash Lite | Google | 0.075 / 0.30 | **+29pp / +14pp** (anchor) |
| **R1 (cheap)** | Gemini 2.5 Flash | Google | 0.30 / 2.50 | +11pp / +18pp |
| **R1 (cheap)** | GPT-5.4-nano | OpenAI | 0.20 / 1.25 | ~0pp (scope bound) |
| **R1 (cheap)** | GPT-5-mini | OpenAI | 0.25 / 2.00 | ~0pp / +4pp (borderline) |
| **R2 (cluster, free)** | Qwen2.5-VL-7B | NURC | $0 | untested (mechanism) |
| **R2 (cluster, free)** | Pixtral-12B | NURC | $0 | untested (mechanism) |
| **R2 (mid-cost)** | GPT-5.4-mini | OpenAI | 0.75 / 4.50 | ~0pp (more GPT data) |
| **R2 (mid-cost)** | Gemini 3 Flash Preview | Google | 0.50 / 3.00 | unknown (Google frontier fallback) |
| **R3 (expensive, deferred)** | GPT-5.4 | OpenAI | 2.50 / 15.00 | 0pp / +2pp |
| **R3 (expensive, deferred)** | Claude Sonnet 4.6 | Anthropic | 3.00 / 15.00 | +2pp / +5pp |
| **R3 (expensive, deferred)** | Gemini 2.5 Pro | Google | 1.25 / 10.00 | unknown (batch API access pending) |

**Round 1 model set covers both GPT and Gemini families with no model
above $0.30/M input.** Claude entirely deferred (most expensive provider).

**Excluded:** Claude 4.5 Haiku (batch API timeout), Gemini 3 Pro Preview
(batch API timeout).

---

## Execution Order — cross-block round sequencing

Per-block rounds are listed inside each block. The cross-block sequence
respects the Stage 1 → Stage 2 dependencies between blocks and the
gating decision at the end of Block 1 Round 1.2.

```
Wave A (cheap setup, no API budget):
  Block 1 R1.1   → produces T1–T4
  Block 2 R2.1   → produces T9–T10   (parallel with R1.1)
  Block 6 R6.1   → produces T16–T19  (parallel; benign benchmarks)

Wave B (Stage 2 gating, cheap models only):
  Block 1 R1.2   ← consumes T1–T4               [~$10–18, GATING]
  Block 2 R2.2   ← consumes T9–T10              [~$5–10, parallel]
  Block 6 R6.2   ← consumes T16–T19             [~$5–10, parallel infra]

  >>> Gating decision <<< — see Block 1 R1.2 rules.

Wave C (Stage 1 expansion, cheap; conditional on Wave B):
  Block 1 R1.3   → produces T5–T8
  Block 3 R3.1   → produces T11–T14
  Block 4 R4.1   → produces T15

Wave D (Stage 2 expansion):
  Block 1 R1.4   ← consumes T1–T4 on Qwen + Pixtral  [free cluster]
  Block 1 R1.5   ← consumes T1–T8 on mid-cost + R1   [~$25–40]
  Block 3 R3.2   ← consumes T11–T14                  [~$10–15]
  Block 4 R4.2   ← consumes T1, T15                  [~$1–2]

Wave E (mechanism, free):
  Block 5 R5.1+5.2  ← hidden-state PCA on Block 1 R1.4 saved activations

Wave F (expensive frontier, deferred):
  Block 1 R1.6   ← consumes T1–T4 on GPT-5.4 + Claude 4.6  [~$20–35]

Wave G (analysis + writing):
  Statistical analysis (bootstrap CIs, permutation tests)
  Paper writing per `proposal.md` §9
```

Total expected spend if all waves run: ~$80–130. Gating spend (Wave A + B
only): ~$20–40.

---

## Statistical Analysis

| Analysis | Method | Answers |
|---|---|---|
| Destroyer gap CIs per (encoding, defense, model) cell | Bootstrap 10K resamples on ASR rate | "is the +Xpp gap real?" |
| Pure-attack vs ir_plain-wrapped paired comparison | Permutation test on per-prompt verdicts | sharper than independent-sample comparison |
| Destroyer specificity (IR vs blank vs constant) | 3-way comparison with multiple-test correction | "is the destroyer specific to IR-rendered encoded text?" |
| Cross-defense generality | Per-defense gap × {SAGE, ECSO, SemSmooth} ranked overlap | "does destroyer break all three?" |
| Capability-tier vs destroyer-gap | Regress gap on (text-ASR, IR-defense-effect) | tests the "weak image safety → destroyer fires" hypothesis |

---

## Compute Budget (estimated, cost-first — accounting for past data)

| Block | Round | New tasks | Cost |
|---|---|---|---|
| Block 1 Round 1 (ECSO + SS-text on R1 set; SAGE/NoDef reused from past data) | R1 | ~40 new + 4 backfill + ~8 prompt_transform | **$8–15** |
| Block 2 specificity ablation (2 cheap Gemini) | R1 | ~16 | $5–10 |
| Block 6 over-refusal (cheap × benign) | R1 | ~24 | $5–10 |
| Block 1 Round 2 cluster (Qwen + Pixtral, full matrix — untested) | R2 | ~32 | $0 (cluster) |
| Block 1 Round 2 mid-cost (GPT-5.4-mini + Gemini 3 Flash Preview, new cells) | R2 | ~24 | $10–20 |
| Block 1 Round 2 encoding expansion (CC + semantic_camo, full matrix on R1) | R2 | ~64 | $15–25 |
| Block 3 cross-attack-family (cheap Gemini, full matrix — untested) | R2 | ~32 | $5–10 |
| Block 4 renderer variant | R2 | 8 | $1–3 |
| Block 5 mechanism (cluster) | R2 | small | $0 |
| Block 1 Round 3 expensive frontier (GPT-5.4 + Claude 4.6, new cells only) | R3 | ~20 | **$20–35** |
| **Round 1 only (gating cost)** | | **~95 new tasks** | **~$18–35** |
| **Round 1 + 2 (full minus expensive frontier)** | | **~220 new tasks** | **~$45–90** |
| **All rounds including expensive frontier** | | **~240 new tasks** | **~$65–125** |

Round 1 gating spend dropped from ~$25–45 to ~$18–35 by reusing past P2
data for the SAGE and no_defense cells (already-collected destroyer
anchor data). Only ECSO + SemanticSmooth-on-cheap-R1-models are new.

---

## Configuration Notes

- Encoder LLM (for set_theory / formal_logic / classical_chinese /
  semantic_camo): `gpt-4.1-mini`.
- Judge model: `gpt-5-nano` (`max_tokens: 16384`), set in
  `conf/evaluation/default.yaml::judge_llm_config`.
- Canonical evaluator dispatch is benchmark-driven
  (`EvaluatorFactory.create_from_benchmark`).
- Image transformations (new chain syntax):
  - `ir_plain` — defaults: `keep_text=false`, `image_content=current_text`
    (image-only delivery; text channel replaced with stock "check the image"
    instruction).
  - `ir_plain` with `keep_text=true` — text+ir multimodal ablation.
  - `blank_image` — true blank PNG; default `keep_text=true`.
  - `constant_image` — fixed image (default: bundled `rabit.jpeg`);
    default `keep_text=true`.
- Defenses: `no_defense`, `sage`, `ecso` (3-call response-coupled,
  reimplemented on `LLMService` so it works with any VLM),
  `semantic_smooth` (N=5 paraphrase + vote; text-only).
- All new experiments write to `outputs/prompt_transform/` and
  `outputs/defense+evaluate/`. Old `outputs/text_encode/`, `outputs/imaging/`,
  `outputs/defense/`, `outputs/defense_transform/`, `outputs/evaluate/`
  preserved unchanged — `experiment_results.md` still references them by
  basename.

---

## Known Risks / Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| ECSO destroyer gap is much smaller than SAGE's (caption captures encoded text differently than OCR-then-text) | Medium | Cross-family generality story still holds with SAGE + SemanticSmooth alone; ECSO becomes "third defense" support rather than centerpiece. |
| Block 2 specificity ablation shows blank/constant_image ALSO destroys defenses | Medium | Reframe contribution as "image-input modality is a structural weakness for text-side-terminal defenses." Smaller but still novel. |
| SemanticSmooth multimodal undefined (paraphrasing an image is not well-defined) | Confirmed limitation | Run SemanticSmooth on text-only inputs; document multimodal as out-of-scope. |
| Destroyer effect concentrates only on Gemini family (GPT confirms scope bound but Claude doesn't replicate) | Medium-High | Bound the claim to "image-safety-weak VLMs"; add capability correlation to make the bound informative. |
| Frontier API accounts blocked again | Medium | Tier A + cluster slice gives independent evidence; degrade gracefully. |
| Reviewers say "all three defenses share a text-side terminal check, so destruction is a single-mechanism finding" | High | Lean in: structural finding about the entire deployable black-box defense surface, not a single-defense bug. See `proposal.md` §6 mechanism narrative. |
| ReNeLLM expected but not implemented | Already excused | Documented in proposal as deferred per scope decision. |
