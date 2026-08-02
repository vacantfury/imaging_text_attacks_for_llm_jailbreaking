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
