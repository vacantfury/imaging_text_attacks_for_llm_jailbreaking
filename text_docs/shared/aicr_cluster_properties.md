# AICR cluster properties

**AICR = Massachusetts AI Compute Resource** — a multi-institutional GPU cluster (BU, Harvard,
MIT, Northeastern, UMass ×5, Yale + the Massachusetts AI Hub), housed at MGHPCC in Holyoke, MA.
Second SLURM cluster available to this project alongside NURC/Explorer
(see `nurc_cluster_properties.md`) and Xiangchen's direct-SSH A100 box.

Account granted 2026-07-13. This doc is the AICR twin of `nurc_cluster_properties.md`; the concrete
SSH username + one-off gotchas that shouldn't be public stay in project-local memory
(`reference_aicr_cluster_access`), not in this committed doc — public-repo PII discipline.

> **Status: DOCS-ONLY so far.** Everything below the "From the docs" line is confirmed from
> https://docs.aicr.ai. Everything under "PROBE CHECKLIST" is UNVERIFIED — it needs an SSH session
> to fill in (blocked on the owner's one-time key setup; see the SSH access section). Do not wire
> the pipeline against the probe items until they're confirmed on the box.

## Access

- **Login node:** `login.aicr.ai` (public, per the AICR docs).
- **AICR username:** kept in project memory `reference_aicr_cluster_access` (account ID → not in this
  public doc). For the OnDemand web portal, authenticate with the *home institution* NEU username +
  password via SSO, NOT the AICR username.
- **Web portal (OnDemand):** https://ood.aicr.ai — institutional SSO. Used once to download the SSH keys.
- **SSH:** cert-based ed25519 key `~/.ssh/id_ed25519_aicr` (+ `-cert.pub` certificate).
  A `Host aicr` alias is wired into the local Mac `~/.ssh/config` → `ssh aicr` once the key is placed.
- **Docs:** https://docs.aicr.ai/ · SSH setup https://docs.aicr.ai/connecting/ssh · getting-started
  https://docs.aicr.ai/getting-started/ · help https://docs.aicr.ai/getting-help.

### SSH key setup (owner one-time, owner's hands — the current blocker)
The key is distributed through the OnDemand portal (institutional-SSO download), so this step is
owner-hands. Exact steps live in the session hand-off / TODO item 3. Summary: OnDemand → File
Browser → download the `aicr_keys/` dir → unzip → `cp aicr_keys/id_ed25519_aicr* ~/.ssh/` →
`chmod 600 ~/.ssh/id_ed25519_aicr` → `ssh-keygen -p -f ~/.ssh/id_ed25519_aicr` (change the initial
passphrase found in `aicr_keys/.passphrase`; **set an EMPTY new passphrase for headless automation**).
The `id_ed25519_aicr-cert.pub` is a **certificate** — it likely EXPIRES, so a periodic re-download
from OnDemand may be needed (confirm the cert lifetime on first probe).

## From the docs (confirmed 2026-07-13, https://docs.aicr.ai)

### Scheduler
- **SLURM.** Same scheduler family as NURC → the existing `ClusterModelServerManager` SLURM path
  should largely transfer, with sbatch-directive differences noted below.
- Interactive GPU session via `salloc`, e.g. `salloc -t 01:00:00 -p rtx-devel -c 4 -G 1`
  (4 cores + 1 GPU for 1h).

### GPU partitions (four; partitions are **homogeneous** — one GPU type each)
| Partition    | GPU type      | GPUs/node | Max wall |
|--------------|---------------|-----------|----------|
| `rtx-batch`  | RTX PRO 6000  | 8         | 24 h     |
| `rtx-devel`  | RTX PRO 6000  | 8         | 4 h      |
| `b200-batch` | B200          | 8         | 24 h     |
| `b200-devel` | B200          | 8         | 4 h      |

- VRAM (from vendor spec, **confirm on probe**): RTX PRO 6000 Blackwell ≈ **96 GB** GDDR7;
  NVIDIA B200 ≈ **180 GB** HBM3e. Both far larger than NURC's V100-32GB / A100-80GB.
- **GPU request syntax differs from NURC.** AICR docs say request GPUs with **`--gpus=N`** /
  `--gpus-per-node=N`, and the **partition alone selects the GPU type** (homogeneous partitions) —
  do NOT use `--gres=gpu:<type>:N` here. NURC uses `--gres=gpu:N`. This is the main sbatch-generation
  fork the wiring must parameterize.
- **Longer wall clock** (24 h batch vs NURC's 8 h cap) and **8 GPUs/node** — if this account is
  allowed multi-GPU jobs (PROBE), tensor-parallel serving is possible here, unlike NURC (which caps
  this account at 1 GPU/job under the `normal` QOS and forces fp8-onto-one-GPU). That would let AICR
  host large judge/target models natively → directly helps Paper C (item 5) and Paper D.

### Filesystems
| Space   | Path                              | Quota      | Backup       | Notes |
|---------|-----------------------------------|------------|--------------|-------|
| Home    | `/home/<user>`                    | 100 GiB    | 7-day snaps  | code + software |
| Scratch | `/scratch/<user>/`                | 10 TiB     | none         | **30-day purge**; active-job temp only |
| Work    | `/work/<institution>/<group>/`    | varies     | 7-day snaps  | shared project data |
- **HF model cache home:** put it on `/scratch/<user>/huggingface_cache` for active runs (big, fast,
  purge-tolerant since weights re-download), OR `/work/...` if a persistent shared cache is wanted.
  This becomes `cluster.hf_home` in the AICR `conf/llm` profile (mirror of NURC's scratch cache).
- Nothing is backed up beyond snapshots → keep the repo in git, results synced back to the Mac.

### Software
- **Module system** (`module avail` / `module load`) with common-core + institution-specific modules.
  Exact module names (Anaconda/conda? CUDA? Python?) are UNVERIFIED — see probe checklist.

## PROBE CHECKLIST (run on first SSH — fills the gaps; mirrors item-4's Xiangchen probe)
Once `ssh aicr` works, run these on the login node and record results here:
1. `sinfo -o "%20P %5a %10l %6D %25f %30G"` — real partition list, features, GRES strings, availability.
2. `sinfo -p rtx-devel -N -o "%20N %10c %10m %30G %25f"` and same for `b200-devel` — per-node CPUs/mem/GPU.
3. `sacctmgr -n show assoc user=$USER format=Account,QOS,MaxTRESPerJob%30,GrpTRES%30` —
   **the multi-GPU question**: is this account allowed >1 GPU/job? which QOS? any GPU/job or GPU/user cap?
4. `scontrol show partition | grep -E "PartitionName|MaxTime|QoS|MaxTRES"` — per-partition limits.
5. `module avail 2>&1 | head -80` — is there anaconda/miniconda? CUDA module names? Python versions?
   (NURC uses `module load anaconda3/2024.06` + `source activate <env>`; AICR's equivalent is TBD.)
6. `echo $HOME; df -h /home/$USER /scratch/$USER 2>/dev/null; ls -la /work/ 2>/dev/null` — confirm
   paths + which `/work/<institution>/<group>/` this account can write.
7. Internet on compute nodes? (NURC compute nodes are offline → HF_HUB_OFFLINE=1 + pre-download on a
   CPU node.) Test with an salloc'd node: `curl -sI https://huggingface.co | head -1`.
8. `nvidia-smi` inside an `salloc -p rtx-devel -G 1 -t 00:20:00` session — exact GPU model + VRAM,
   driver/CUDA version. Repeat on `b200-devel` if reachable.
9. Cert lifetime: `ssh-keygen -L -f ~/.ssh/id_ed25519_aicr-cert.pub` (run locally) — note the
   "Valid: ... to ..." window so we know the re-download cadence.

## Wiring plan (gated on the probe — do not build against guesses)
AICR is a **second SLURM cluster**. Each run's orchestrator (`main.py`) uses *local* `sbatch`/`squeue`/
`scontrol`, so "which cluster" = where the orchestrator runs; the repo gets cloned onto AICR and runs
happen there, exactly as on NURC. Minimal wiring:
1. **Repo on AICR:** clone into `/home/<user>/projects/...` (or `/work/...`); set up the Python env per
   the module system found in probe step 5 (conda env `AI_security` mirror, or a `uv` venv if no conda).
2. **Cluster profile in `conf/llm/`:** a new AICR flavor carrying `partition` (`rtx-batch`/`b200-batch`),
   the `--gpus=N` GPU-request style, module-load line, `hf_home` (scratch path), and multi-GPU/`qos`
   fields per probe. The NURC values are the current defaults in `conf/llm/default.yaml`.
3. **`ClusterModelServerManager._generate_sbatch` parameterization:** fork the GPU-request directive
   (`--gres=gpu:N` for NURC vs `--gpus=N` for AICR) and the module-load line on the profile — everything
   else (endpoint discovery via scontrol, health-check pool, acquire/release) is scheduler-generic and
   reused as-is. Prefer a config-driven `gpu_request_style` + `module_load_cmd` over a new `Provider`
   enum value, since the endpoint plumbing is identical (decide at wiring time).
4. **run-experiment route + sbatch:** an AICR variant of `scripts/run_experiment.sbatch` (partition +
   module + `op run` secret injection) and a `run-experiment` skill note on picking the cluster.
5. **Secrets:** same v2 `op run` path as NURC (item 2) — needs `op` CLI + the dev service-account token
   in `~/.secrets` on AICR too. Fold into the item-2 remote setup.
