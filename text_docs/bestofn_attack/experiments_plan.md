# Experiments plan — `bestofn_attack` (Paper D, attack-primary)

**Status (2026-07-17):** S7 code built (paraphrase transform + variance-channel wrapper, structurally tested offline). This doc is the S6/S8 experiment design. **Round 1 = a FREE cheap-first PILOT** — validate the pipeline end-to-end and get first directional signal on the core claim. The API-judged headline run is RESERVED for owner approval (see §Judge).

## The question Round 1 answers
Does moving Best-of-N's variance from the **surface** channel into the **paraphrase** / **strategy** channels raise ASR(N) **against an input-normalization defense** (canonicalize), while surface BoN collapses? I.e. the channel-depth → defense-survival claim, in miniature.

## Round 1 matrix (all FREE cluster models)
- **Attack (variance channel)** = `variance_channel_bon` with `channel ∈ {surface, paraphrase, strategy}` — 3 prompt_transform arms over the *same* expanded behaviors.
- **Defense** = `no_defense` (raw ASR(N)) and `canonicalize` (the input-normalization defense the paper targets) — 2 arms.
- **Target** = `qwen2_5_vl_7b` (free, cluster-served; smallest served model, handles text).
- **Judge** = `wildguard` (`judge_method: wildguard`) — the decided FREE 7B judge. No API.
- **Helper** (paraphrase + LLM attacks in the strategy bank) = `vicuna_13b_cluster` (free, cluster; permissive → low paraphraser-refusal).
- **Data** = `data/harmbench_bon_r4.jsonl` (40 behaviors × 100 draws already expanded), pilot slice `prompt_range: [0, 499]` = **5 behaviors × 100 draws**.
- **Metric** = ASR(N) per channel×defense via `src/analysis/bon_asr.py` (OR-reduce over `__bonK` draws per behavior); compare the ASR(N) curves.

Cells = 3 channels × 2 defenses = **6 defense+evaluate cells**, preceded by 3 prompt_transform arms.

## Cost & footprint
- **$0 — entirely free cluster models** (qwen target + wildguard judge + vicuna helper). GPU hours only, no API spend.
- Servers = 3 distinct cluster models (target + judge + helper) → `num_cluster_jobs = 4`. Fits **AICR** (budget 7, comfortable; preferred) or NURC (budget 4, needs 0 other jobs).
- Scale ≈ 500 rows × 3 channels = 1500 transformed prompts → × 2 defenses = 3000 target queries + 3000 judge calls, all free.
- Wall-clock: server queue wait (wildcard) + inference; rough ~30–90 min once servers are up.

## Judge methodology (shared Round-J)
- **Pilot/intermediate = `wildguard`** (free) — THIS round.
- **Headline = `gpt-5-mini`** (API, validated) — **RESERVED**: applied only as a `rejudge` pass over the pilot's SAVED responses (no re-query), and only after an explicit owner OK under the API HARD GATE. Never bundled into the pilot.

## Run procedure (two-pass, mirrors `bestofn_defense/reproduce_bon.yaml`)
The pipeline doesn't auto-chain across a timestamp, so:
1. **Stage 1** — submit the 3 `prompt_transform` arms (surface/paraphrase/strategy). They write `outputs/bestofn_attack/prompt_transform/harmbench/<ts>/variance_channel_bon/`.
2. Read each arm's `<ts>`, fill the 3 `source_transform_subdir` placeholders in the Stage-2 tasks.
3. **Stage 2** — submit the 6 `defense+evaluate` cells.
4. `check-experiment-results` + `bon_asr` on the 6 output dirs → compare ASR(N).
(A ~20-row smoke — `prompt_range: [0, 19]`, surface channel, no_defense — is worth firing first to validate the new `variance_channel_bon` serving path before the full pilot.)

## BLOCKER to launch (verified 2026-07-17) — one owner action on return
The cluster checkout `~/projects/llm_guardrail_security` is an **rsync target, not a git repo** (probed 2026-07-17: `git log` → "not a git repository"). So the new code (`variance_channel.py`, `llm_paraphrase_encoder.py`, the two confs, the preset) **cannot be delivered by git-pull** — it needs the owner's **Cursor Sync-Rsync (local→remote)**, which the session cannot invoke. Everything else is ready.
- **On return:** run Cursor Sync-Rsync (Cmd+Shift+P → sync local→remote), reply "synced" → the session runs the smoke, then Stage 1 → fills timestamps → Stage 2, and reports job ids. No other owner action needed until results.

## Reserved / later rounds
- **R2 (headline):** rejudge R1 saved responses with `gpt-5-mini` (owner-gated); add SmoothLLM / SemanticSmooth defenses (SemanticSmooth needs a free cluster `perturbation_model` override); more behaviors + the full N-budget curve.
- **R3:** channel-depth sweep (effective-N slopes), work-factor (total attacker compute per channel), the I-FSJ carve baseline.

---

# Round 8 — the variation-type × encoding factorial (designed 2026-08-03)

**Owner-approved 2026-08-03** ("I agreed the experiment"), docs-first by owner
instruction. Origin: the owner identified during cspaper review-7 triage that we have
**two different kinds of best-of-N** and had been treating them as one.

## Why this round exists — the confound, stated plainly

Every draw of a best-of-N attack can differ in the **prompt** (a new attack string each
draw) or not (the same string, resampled through a stochastic target). These are two
different attacks. We ran only the diagonal:

|  | **varied** — new prompt each draw | **fixed** — same prompt, resampled |
|---|---|---|
| **plain** (no encoding) | ✅ original BoN — <5% on SAGE | ❌ **MISSING** |
| **code** (CodeAttack) | ❌ **MISSING** | ✅ headline — **67%** on SAGE (Llama) |

**Encoding and variation-type change together, so neither can be credited.** The
headline 67-vs-5 gap is currently unattributable. This is the root cause under cspaper
review-7 cons 1 and 2, and review-7 Q1 explicitly states the reviewer's assessment
would improve if the two were separated.

Measured basis for the split (`experiment_results.md` §STRUCTURAL FINDING): across 100
draws the code arm has **1 distinct prompt per behavior**, the surface arm has **100**;
at a gate the code arm is perfectly bimodal (0 partial across all 8 gate cells, every
target) while the surface arm is 53–100 partial; against SAGE the same fixed code
prompt gives 21/100 partial.

## The two missing arms

- **`plain × fixed`** — the raw harmful request, unmodified, sent N=100 at T=1.0.
  Transform = `non_llm_baseline`. No new code.
- **`code × varied`** — vary the request, THEN encode, so the payload differs each
  draw while the code structure stays intact. This is what "BoN-wrapped CodeAttack"
  should have meant. Two routes, both config-only:
  - *(primary)* `channel: paraphrase` + `single_attack: {type: code_attack}` —
    already supported, `variance_channel.py:152-158`.
  - *(alternative)* preset chain `[variance_channel(surface), code_attack]` — the
    `prompt_transform` chain runs steps in order, so no code change is needed either.
- **`code × varied`, ablation (secondary, only if cheap)** — encode FIRST, then perturb
  the code (`[code_attack, variance_channel(surface)]`). Tests whether the code
  structure is fragile to character noise. Expect syntax damage; that is the point.

## PRE-REGISTERED predictions — recorded BEFORE the run

Derived from the mechanism (a transform routes the request through the target, so the
target's sampling is searchable at a fixed prompt; a gate screens only the prompt, so a
fixed prompt is one probe regardless of N).

| # | Cell | Prediction | Falsifies what if wrong |
|---|---|---|---|
| P1 | `code × varied` at a **gate** | **RISES SHARPLY** vs `code × fixed` (14 → toward the surface arm's 53), because prompt variation converts a 1-probe attack into an N-probe one | **The probe-count mechanism itself.** If it does not rise, probe count is wrong. |
| P2 | `code × varied` (paraphrase→code) under **SAGE** | **≥** `code × fixed` — a transform already exposes the target channel; prompt variation adds a second one | The "variation is free at a transform" reading |
| P3 | `code × varied` (surface→code, ablation) under SAGE | **≤** `code × fixed` — character noise garbles the payload the target must complete | The structure-fragility hypothesis |
| P4 | `plain × fixed` under **SAGE** | **LOW**, far below `code × fixed` — SAGE's self-check catches an unencoded harmful request. Prior: R4's undefended raw-prompt floor is 0.19 (per-draw 15.2%) on qwen2.5-VL | ⚠️ **THE STORY-KILLER.** If plain×fixed ≈ 67%, the code encoding contributes nothing and this paper is about resampling alone. |

P4 is the one we most need and least want. Recording it here so the answer counts
either way, and so it is not discovered by a reviewer first.

## Cells and cost

Judge = `gpt-5-mini` (judge of record). Basis for the estimate: the R3 rejudge was
~$47 for ~60k responses → **~$8 per 10,000-draw cell**. Cluster GPU is free.

**Pilot (recommended), target Llama-3.1-8B** — where the effect is largest:

| Arm | no_defense | SAGE | canon.+WildGuard |
|---|---|---|---|
| `plain × fixed` | ✔ | ✔ | ✔ |
| `code × varied` (paraphrase→code) | ✔ | ✔ | ✔ |

= **6 cells ≈ $47.** (A 4-cell version dropping the gate column is ~$31, but the gate
column is where P1 — the sharpest falsifiable prediction — lives, so it earns its $16.)

Extensions, only if the pilot is clean: all four targets ≈ $125; the surface→code
ablation +2 cells ≈ $16.

## What each outcome buys

- **P1 holds + P4 low** → the factorial is clean: encoding and variation-type are
  separable, both matter, and the mechanism predicts the gate behaviour. Best case;
  the paper gets a real 2×2 and a confirmed mechanism.
- **P1 fails** → probe count is wrong and must be withdrawn, not patched. Cheap to
  learn now, fatal to learn post-acceptance.
- **P4 fails (plain×fixed high)** → CodeAttack is not load-bearing; the contribution is
  inference-time resampling against self-check defenses. A smaller but honest paper.
- **P2/P3 split as predicted** → we can say *which kind* of variation helps at a
  transform, which no prior work distinguishes.

## Run procedure

1. Write presets under `conf/experiment/bestofn_attack/` (named per the standing
   preset convention — one named preset per round, never overwrite `experiment.yaml`).
2. Stage 1 `prompt_transform` for the two new arms; verify distinct-prompt counts per
   behavior BEFORE stage 2 (**plain×fixed must be 1, code×varied must be 100** — this
   is the check whose absence caused the original confound).
3. Stage 2 `defense+evaluate` on the cluster, AICR-first.
4. Canaries before trusting anything: `fallback_parse_count == 0`,
   `total_evaluated == 10000`, wall time consistent with the cell count.
5. Record to `experiment_results.md`; the pre-registered predictions above are scored
   as stated, including any that fail.

## Round 8 — build addendum (2026-08-03, after writing the presets)

Four things settled while building; they supersede the design text above where they differ.

1. **Gate column is `guard_baseline` + `llama_guard_3_8b` (as shipped), NOT
   canon.+WildGuard.** The shipped gate is where the existing code-vs-surface gap is
   widest (14 vs 53 behaviors admitted), so P1 is stated in those units and is
   falsified most cleanly there.
2. **Cost refined to the MEASURED rate.** `p7_probe_paraphrase.yaml` records
   $0.00090/call, so 6 cells x 10,000 = 60,000 generations is **~$36–54** for the
   gpt-5-mini rejudge, against the ~$47 quoted from my own derivation. Same
   ballpark, but the measured figure governs. **Stage 1 and Stage 2 themselves are
   $0** — free cluster models, wildguard first pass; the API spend is entirely in
   the follow-on rejudge, which is a separate preset and a separate ask.
3. **`data/harmbench_bon_100.jsonl` REBUILT BY ALIGNMENT, not re-expansion.** It had
   been deleted (see the HISTORICAL banner on `baselines_stage1.yaml`). Rebuilt by
   reading ids + originals straight off the existing code arm's `prompts.jsonl` and
   joining `data/harmbench_prompts.jsonl` for `category` (100/100 matched). Verified:
   10,000 rows, id sequence byte-identical to the code arm, 100 behaviors x exactly
   100 draws. This is a stronger comparability guarantee than
   `scripts/expand_bon_dataset.py` would give, because arm A aligns draw-for-draw
   with the arms it is compared against.
4. **Arm B reuses the stored paraphrase output** rather than regenerating it —
   `code_attack` is chained onto the existing `variance_channel_bon` (channel
   paraphrase, seed 0, helper qwen2_5_vl_7b, batch 20260718). Zero helper-LLM cost,
   and arm B becomes exactly "the existing paraphrase arm + code encoding", so it is
   comparable to the paraphrase arm AND the code arm.

**Provenance note worth keeping:** `baselines_stage1.yaml` (R4, 2026-07-19) already
stated in its own comments that both arms are "BoN via TARGET TEMPERATURE ... 100
identical draws". The fact was known in July and never reached the paper's framing.
The defect was in the write-up, not in the understanding of the pipeline.

**Deployment:** presets deploy by commit → push → `git pull` on the box, with no owner
sync. Confirmed on AICR 2026-08-03 (`~/projects/llm_guardrail_security` is a real git
clone). This matches the repo `CLAUDE.md`, which another session had already corrected
on 2026-08-02 after verifying all three boxes — an earlier draft of this addendum
claimed that line was still stale; it was not, and the error was mine (a stale
CLAUDE.md snapshot in session context, not a stale file).

## Round 8 — execution record (2026-08-03)

**Stage 1 — AICR job `256948`, COMPLETED in 31 s, $0.** Both transforms are non-LLM and
arm B reuses stored paraphrase output, so no vLLM server was needed. Outputs:

- ARM A `non_llm_baseline_20260803_033658_62709884/non_llm_baseline`
- ARM B `variance_channel_bon_code_attack_20260803_033658_17867502/code_attack`

**THE GATE — passed, and this is the round's licence to proceed.** Distinct `encoded`
values per behavior, measured over all 10,000 rows of each arm:

| arm | distinct encoded prompts / behavior | required | verdict |
|---|---|---|---|
| ARM A — plain × fixed | **1** for all 100 behaviors | 1 | ✅ |
| ARM B — code × varied | **100** (66 beh.), 99 (18), 98 (4) | ~100 | ✅ |
| *(control)* existing code arm | **1** for all 100 | — | the confound, re-confirmed |
| *(control)* surface arm | **100** for all 100 | — | the confound, re-confirmed |

ARM B's 99/98 tail is **inherited, not a collapse**: the upstream paraphrase arm has the
identical histogram (100/99/98 → 66/18/4), i.e. the paraphraser occasionally repeats
itself across draws. `code_attack` preserved every distinction it was given.

**Two process notes worth keeping.**

1. *The first run of this check read a field that does not exist.* `prompts.jsonl` stores
   the encoded text under `encoded`, not `prompt`; reading `prompt` returned `None` for
   every row, which collapsed to "1 distinct" and looked exactly like a real failure of
   arm B. The schema is `id, encoding, original, encoded, image_original, image_encoded`.
   A distinctness check that reads the wrong key fails **toward** the alarming answer, so
   the control rows above (existing code arm = 1, surface arm = 100) are not decoration —
   they are what proves the probe itself is live.
2. *`num_cluster_jobs` is a load-bearing parameter, not a round number.* The allocator in
   `Experiment._prepare_cluster_servers` sets `servers_wanted = N - 1` and caps **only if**
   `total_requested > available_slots`, by floor division `available_slots // n_models`,
   never promoting above the YAML request. This round serves 3 distinct models and
   requests 6 instances (llama 4 + wildguard 1 + llama_guard_3 1):
   - `N=5` → 4 slots → 6 > 4 → cap `4//3 = 1` → **llama collapses 4 → 1**, and since
     load-balancing is per-cell, all six cells serialize onto one endpoint (~22 h
     projected against the 24 h wall — the round-174759 failure mode).
   - `N=7` → 6 slots → `6 > 6` is false → **no capping at all**, llama keeps 4.
   The preset was written at 5 and corrected to 7 before submission. Verified at submit
   time: AICR `max_gpu_jobs: 12`, 0 GPU jobs running, so 7 jobs sits inside both that and
   `MAX_SUBMIT_JOBS_PER_USER = 8`.

**Stage 2 — AICR job `257350`, submitted 2026-08-03, $0** (6 cells, wildguard first pass).
Verify on landing: all 6 cells `total_evaluated == 10000`, status success,
`fallback_parse_count == 0`. Expect low draw-diversity on ARM A's gate cell — a blocked
prompt returns a byte-identical canned refusal, which is the documented gate exemption,
not the Section-4 variation-channel defect.

**No number from the wildguard pass is reportable.** It over-flags the code arm 41–68 %
and *both* arms in this round are code-bearing. The follow-on gpt-5-mini rejudge
(~$36–54 at the measured $0.00090/call) is the approved spend and a separate ask.
