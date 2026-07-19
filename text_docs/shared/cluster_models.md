# Cluster model inventory (per-cluster open-weight downloads)

Three SLURM clusters serve this project's open-weight models from an HF cache.
**Living inventory — update on every download/removal, per cluster.**

| Cluster | HF cache (`hf_home`/hub)                          | Download                                     | Env   | Compute-node net |
|---------|--------------------------------------------------|----------------------------------------------|-------|------------------|
| NURC    | `/scratch/zhang.haoyu6/huggingface_cache/hub`    | `temporary_scripts/download_hf_model.sbatch` | conda | offline (pre-download) |
| AICR    | `/scratch/zhang_haoyu6_neu/huggingface_cache/hub`| `scripts/download_hf_model_aicr.sbatch`      | uv    | online (`hf` pulls live) |
| xc      | `/home/thomas/huggingface_cache/hub`             | direct `hf download` (single node, no sbatch)| uv    | online (`hf` pulls live) |

NURC/AICR downloads run on a **compute node, never the login node** (NURC partition `short`,
AICR partition `cpu`, 24h wall); the sbatch scripts route the cache to the path above, which MUST
match `cluster.hf_home` in `conf/clusters/<cluster>.yaml`. **xc** is single-node (no scratch, big
home disk) so it downloads directly with `hf download` — the HF token is injected the standard op
way (transient over ssh stdin for a one-off; `op://dev/HuggingFace/credential`, in `scripts/op_refs`).

Disk headroom: NURC `/scratch` ~323 TB free; AICR `/scratch` = 10 TiB quota on a 2.6 PB filesystem
(2026-07-15). **xc** = 5.7 TB single disk, self-imposed ≤ 1/3 (~1.9 TB) for our weights (owner rule
2026-07-18); the disk is shared with the box owner (~420 GB his) but as of 2026-07-19 our files live
under a **dedicated `thomas` user** (isolated home, mode 750 — see below), no longer the shared
`ubuntu` account. xc is the GPU LAST-RESORT tier → keep it to the small/mid targets+guards+judges that
fit (its 8×A100-80G = 640 GB serves up to ~235B); the frontier capability arm (DeepSeek/Kimi) is AICR-only.

### xc runs under a dedicated `thomas` user (2026-07-19)
xc was a single shared `ubuntu` account (no isolation — same UID for everyone). Xiangchen permitted a
dedicated Linux user, so our work now runs as **`thomas`** (uid 1001, home `/home/thomas` mode 750 —
the box owner can't read it). Migrated there: repo (`~/projects/...`), venv (`~/venvs/imaging_xc`,
rebuilt), models (`~/huggingface_cache`, 348 GB), outputs. SSH: the `xc` alias = thomas; `xc-admin`
= ubuntu (kept for sudo + the Bedrock `arise-beta` creds, which live in ubuntu's `~/.aws` and are his).
The sync `remotePath` (`xc:~/...`) auto-resolves to `/home/thomas` via the thomas alias — no settings
change needed. Bedrock from thomas needs a cred path to ubuntu's `~/.aws` (handled when needed); GPU
serving / downloads work fully as thomas.

## Live set — presence per cluster
NURC/AICR snapshot **2026-07-15**; xc snapshot **2026-07-18**. ✓ = present, ⏳ = downloading, — = absent.

| Model | Role | NURC | AICR | xc |
|---|---|:--:|:--:|:--:|
| Qwen/Qwen2.5-VL-7B-Instruct | VLM workhorse (Paper C) | ✓ | — | ✓ |
| OpenGVLab/InternVL3-8B | VLM | ✓ | — | ✓ |
| mistralai/Pixtral-12B-2409 | VLM | ✓ | — | ✓ |
| meta-llama/Llama-3.2-11B-Vision-Instruct | VLM (serve-blocked, text-restricted) | ✓ | — | ✓ |
| Qwen/Qwen3-VL-8B-Instruct | VLM recency control | ✓ | — | ✓ |
| cais/HarmBench-Llama-2-13b-cls | ASR judge / bake-off floor | ✓ | — | ✓ |
| allenai/wildguard | guard | ✓ | — | ✓ |
| meta-llama/Llama-Guard-3-8B | guard | ✓ | — | ✓ |
| meta-llama/Llama-Guard-4-12B | guard (multimodal) | ✓ | — | ✓ |
| yueliu1999/GuardReasoner-VL-7B | reasoning guard | ✓ | — | ✓ |
| Qwen/Qwen3Guard-Gen-8B | guard (zh arm) | ✓ | — | ✓ |
| thu-coai/ShieldLM-7B-internlm2 | guard (zh/en) | ✓ | — | ✓ |
| OpenSafetyLab/MD-Judge-v0.1 | judge classifier | ✓ | — | ✓ |
| Rakancorle1/ThinkGuard | reasoning guard | ✓ | — | ✓ |
| meta-llama/Llama-3.3-70B-Instruct | general judge (JBB-validated) | ✓ | — | — |
| meta-llama/Llama-3.1-8B-Instruct | general | ✓ | — | ✓ |
| meta-llama/Meta-Llama-3-8B-Instruct | general | ✓ | — | ✓ |
| NousResearch/Hermes-4-70B | steerable judge | ✓ | — | — |
| zai-org/GLM-4.5-Air | capability + zh judge | ✓ | — | — |
| CohereLabs/c4ai-command-a-03-2025 | steerable judge (gated:auto) | ✓ | — | — |
| Qwen/Qwen2.5-0.5B-Instruct | smoke-test model | ✓ | ✓ | ✓ |

**xc set (COMPLETE 2026-07-18):** all 17 small/mid targets+guards+judges present (~348 GB, well within
the 1/3 budget). The **70B+/200B general judges** (Llama-3.3-70B, Hermes-4-70B, GLM-4.5-Air, Command-A)
are `—` on xc by choice: xc is GPU last-resort, so pull them only if xc needs to serve overflow
judge-bake-off runs (they fit its 8×A100 but are big; ~808 GB, still within the 1/3 budget if wanted).
The HF token was injected the standard op way (`op read op://dev/HuggingFace/credential` piped over ssh
stdin, transient — never persisted on the shared box). xc's venv lives at `~/venvs/imaging_xc`
(OUTSIDE the repo → sync-proof; see below).

### venv location — OUTSIDE the repo (2026-07-18, sync-proof)
The Cursor local→remote sync operates on the repo dir and was silently clobbering each cluster's
in-repo `.venv` with the local **macOS** venv (the `**/.venv` exclude fails; broke xc AND AICR). Fix:
venvs now live OUTSIDE the repo — `~/venvs/imaging_aicr`, `~/venvs/imaging_xc` (NURC already on
`/scratch/$USER/venvs/imaging_uv`) — so the sync structurally cannot touch them. `setup_env.sh`,
the `env_setup` in `conf/clusters/{aicr,xc}.yaml`, and the `run_experiment_{aicr,xc}.sbatch` wrappers
all point there. A bare `.venv/` sync-exclude was also added as defense-in-depth.

### Cross-cluster OUTPUTS workflow (STANDARD — via local as the hub)
Clusters can't reach each other directly for our data; **local is the hub**. Each cluster's Cursor
sync has an UP-sync (local→cluster, `outputs/` normally EXCLUDED — results only flow DOWN) and
DOWN-syncs (cluster→local for `outputs/` `logs/` `mlruns/`). So `outputs/` normally moves cluster→local
only. To move outputs FROM one cluster TO another (e.g. a prompt_transform produced on NURC that xc's
defense+evaluate must consume):
1. **Down-sync A→local:** Cursor "Sync-Rsync: Sync Down" pulls A's `outputs/` into local `outputs/`.
2. **Temporarily un-exclude `outputs/` on B's UP-sync** (remove the `outputs/` line from B's up-sync
   `exclude` in `settings.json`).
3. **Up-sync local→B:** "Sync-Rsync: Sync Up" pushes `outputs/` up to B (only B's up-sync carries it;
   the others still exclude it).
4. **RE-EXCLUDE `outputs/` on B's up-sync** immediately after (back to normal — outputs must not
   routinely sync UP, or a stale local outputs/ could overwrite a cluster's fresh results).
This is a DELIBERATE, temporary un-exclude each time — never leave `outputs/` un-excluded on an
up-sync. (Done once already 2026-07-18: pushed local `outputs/` up to xc so it had the upstream data.)

**AICR: 20-model live set download PENDING** (this session, 2026-07-15) — mirror NURC's live
set (everything above except the already-present 0.5B smoke model) via
`scripts/download_hf_model_aicr.sbatch`. Flip each row's AICR cell to ✓ as the jobs complete.

### Gated repos
`meta-llama/*` and `CohereLabs/c4ai-command-a-03-2025` are gated; the HF account behind
`HUGGINGFACE_TOKEN` already accepted these licenses (used for the NURC downloads). Acceptance
is **account-scoped**, so the same token pulls them on AICR — no per-cluster re-accept needed.

### Capability arm — AICR only (owner-approved 2026-07-15; 3 models)
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
  Modified-MIT. **DOWNLOADED + verified** (61/61 shards, 2026-07-15; needed 128G RAM to avoid OOM).
  ⚠️ size at node ceiling → serve-smoke.

**Considered and DROPPED (2026-07-15):**
- `mistralai/Mistral-Large-3-675B-Instruct-2512` (Western minimal-alignment) — riskiest serve of
  the arm (675B on-the-fly fp8 OOM risk) + slow download; its permissive/minimal-alignment axis is
  already covered by Kimi-K2 + DeepSeek-V3.2. Download cancelled + partial data deleted mid-download.
- `meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8` — its only distinct axis was native-multimodal
  *image*-judging, but Round-J judges score the response TEXT only, so multimodality is unused; the
  Meta family is already covered by Llama-3.3-70B. (Also the sole gated repo of the set.)

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
