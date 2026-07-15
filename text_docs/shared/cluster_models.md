# Cluster model inventory (per-cluster open-weight downloads)

Two SLURM clusters serve this project's open-weight models from a scratch HF cache.
**Living inventory — update on every download/removal, per cluster.**

| Cluster | HF cache (`hf_home`/hub)                          | Download script                              | Env   | Compute-node net |
|---------|--------------------------------------------------|----------------------------------------------|-------|------------------|
| NURC    | `/scratch/zhang.haoyu6/huggingface_cache/hub`    | `temporary_scripts/download_hf_model.sbatch` | conda | offline (pre-download) |
| AICR    | `/scratch/zhang_haoyu6_neu/huggingface_cache/hub`| `scripts/download_hf_model_aicr.sbatch`      | uv    | online (`hf` pulls live) |

Download runs on a **compute node, never the login node** — NURC partition `short`, AICR
partition `cpu` (24h wall). Both scripts take one or more HF ids and route the cache to the
path above, which MUST match `cluster.hf_home` in `conf/clusters/<cluster>.yaml`.

Disk headroom is ample on both: NURC `/scratch` had ~323 TB free; AICR `/scratch` = 10 TiB
quota on a 2.6 PB filesystem (2026-07-15).

## Live set — presence per cluster
Snapshot **2026-07-15** (`ls` of each scratch hub). ✓ = present, — = absent.

| Model | Role | NURC | AICR |
|---|---|:--:|:--:|
| Qwen/Qwen2.5-VL-7B-Instruct | VLM workhorse (Paper C) | ✓ | — |
| OpenGVLab/InternVL3-8B | VLM | ✓ | — |
| mistralai/Pixtral-12B-2409 | VLM | ✓ | — |
| meta-llama/Llama-3.2-11B-Vision-Instruct | VLM (serve-blocked, text-restricted) | ✓ | — |
| Qwen/Qwen3-VL-8B-Instruct | VLM recency control | ✓ | — |
| cais/HarmBench-Llama-2-13b-cls | ASR judge / bake-off floor | ✓ | — |
| allenai/wildguard | guard | ✓ | — |
| meta-llama/Llama-Guard-3-8B | guard | ✓ | — |
| meta-llama/Llama-Guard-4-12B | guard (multimodal) | ✓ | — |
| yueliu1999/GuardReasoner-VL-7B | reasoning guard | ✓ | — |
| Qwen/Qwen3Guard-Gen-8B | guard (zh arm) | ✓ | — |
| thu-coai/ShieldLM-7B-internlm2 | guard (zh/en) | ✓ | — |
| OpenSafetyLab/MD-Judge-v0.1 | judge classifier | ✓ | — |
| Rakancorle1/ThinkGuard | reasoning guard | ✓ | — |
| meta-llama/Llama-3.3-70B-Instruct | general judge (JBB-validated) | ✓ | — |
| meta-llama/Llama-3.1-8B-Instruct | general | ✓ | — |
| meta-llama/Meta-Llama-3-8B-Instruct | general | ✓ | — |
| NousResearch/Hermes-4-70B | steerable judge | ✓ | — |
| zai-org/GLM-4.5-Air | capability + zh judge | ✓ | — |
| CohereLabs/c4ai-command-a-03-2025 | steerable judge (gated:auto) | ✓ | — |
| Qwen/Qwen2.5-0.5B-Instruct | smoke-test model | ✓ | ✓ |

**AICR: 20-model live set download PENDING** (this session, 2026-07-15) — mirror NURC's live
set (everything above except the already-present 0.5B smoke model) via
`scripts/download_hf_model_aicr.sbatch`. Flip each row's AICR cell to ✓ as the jobs complete.

### Gated repos
`meta-llama/*` and `CohereLabs/c4ai-command-a-03-2025` are gated; the HF account behind
`HUGGINGFACE_TOKEN` already accepted these licenses (used for the NURC downloads). Acceptance
is **account-scoped**, so the same token pulls them on AICR — no per-cluster re-accept needed.

### Capability arm — AICR only (owner-approved 2026-07-15; expanded to 4 models)
Promoted into the active Round-J pool now that AICR serves 200B+ natively (8-GPU
tensor-parallel, no NURC fp8-onto-one-GPU workaround). AICR only — NOT mirrored to NURC
(NURC's 1-GPU/job cap can't serve them). Each is served + scored TEXT-only via the
HarmBench rubric (the judge never sees the attack image). **All four are OPEN-license —
none is gated, so no HF access grant is needed** (flag on sight if a download 401s).
Serve configs: `conf/llm/{qwen3_235b_a22b_instruct,deepseek_v3_2_exp,kimi_k2_instruct,mistral_large_3}.yaml`.
- `Qwen/Qwen3-235B-A22B-Instruct-2507` — capability + strongest Chinese (classical-Chinese arm);
  MoE 235B/22B-active, bf16 ≈ 470 G, fits one 8×RTX PRO 6000 node (rtx-batch). Apache-2.0.
  Job **157576** (2026-07-15).
- `deepseek-ai/DeepSeek-V3.2-Exp` — capability + permissive + published ASR-judge precedent;
  native FP8 ≈ 671 G, b200 node. MIT. Job **157577** (2026-07-15). ⚠️ V3.2's sparse attention
  (DSA) may need a vLLM-version check before it serves — serve-smoke before the bake-off.
- `moonshotai/Kimi-K2-Instruct` — the PERMISSIVE-CEILING arm (lowest documented general-harm
  refusal of the survey); 1T/32B-active MoE, block-fp8 ≈ 1 TB, one b200 node (tight).
  Modified-MIT. Download **PENDING** (2026-07-15). ⚠️ size at node ceiling → serve-smoke.
- `mistralai/Mistral-Large-3-675B-Instruct-2512` — Western MINIMAL-ALIGNMENT baseline;
  675B/41B-active MoE, fp8 ≈ 675 G, b200 node. Apache-2.0. Download **PENDING** (2026-07-15).
  ⚠️ highest serving risk (on-the-fly fp8 may OOM at load → may need a pre-quantized fp8 ckpt).

**Considered and DROPPED (2026-07-15):** `meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8` —
its only distinct axis was native-multimodal *image*-judging, but Round-J judges score the
response TEXT only, so multimodality is unused; the Meta family is already covered by
Llama-3.3-70B. (Also the sole gated repo of the set — dropping it removes the one license accept.)

Serving configs (`conf/llm/*.yaml`) still to be written AICR-aware (`num_gpus: 8` tensor-parallel,
`partition: rtx-batch`/`b200-batch`) — the existing `command_a.yaml`/`glm_4_5_air.yaml` are
NURC-only (fp8-on-1-GPU + `cascadelake`). API judges (gpt-5-nano/-mini · gemini-flash-lite ·
deepseek-v4-flash · glm-4.7-flashx) need no download.

### Still deferred (neither cluster)
`DeepSeek-V4-Pro` (1.6T) / `GLM-5.x` (~750B) — >1 node or API-only; pull only if the calibration
curve demands an even higher point. (Kimi-K2 1T is NO LONGER deferred — it fits one b200 node at
fp8 ≈ 1 TB < 1.44 TB, so it was promoted into the active capability arm above.)

## NURC-only dead / legacy (do NOT mirror — cleanup candidates)
Present on NURC scratch but unused; safe to delete to free disk, never replicated to AICR:
- `lmsys/vicuna-13b-v1.5` · `lmsys/vicuna-7b-v1.5` · `openlm-research/open_llama_3b_v2` — old base models
- `renjiepi/mllm_protector_detoxifier` · `renjiepi/protector_detector_3b_lora` — mllm_protector defense
  REMOVED from the repo (2026-06-16) → dead weights

_(Candidate rationale + full judge landscape: `judge_candidates.md`. Cluster access + serving
runbooks: `cluster_files/nurc_cluster_properties.md`, `cluster_files/aicr_cluster_properties.md`.)_
