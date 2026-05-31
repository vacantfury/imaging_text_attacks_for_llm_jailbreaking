#!/bin/bash
#SBATCH --job-name=mj
#SBATCH --partition=short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=08:00:00
#SBATCH --output=logs/mj_%j.out
#SBATCH --error=logs/mj_%j.err

# Main experiment orchestrator (Python `main.py <preset>`).
#
# Runs on the `short` partition WITHOUT a GPU. The orchestrator process
# itself is fully CPU-side — it only:
#   - reads YAML, validates Pydantic configs
#   - submits sbatch sub-jobs for vLLM judge/target servers (each on its
#     own gpu-partition node — that's where the actual GPU work happens)
#   - polls SLURM / scontrol / health endpoints
#   - dispatches batch_chat() HTTP calls to remote endpoints
#
# Why CPU by default (no --gres=gpu:1):
#   The cluster's watchdog scancels jobs whose allocated GPU sits idle
#   for ~15 minutes. The orchestrator never runs CUDA itself, so its
#   GPU allocation was 100% idle — got killed at mj_6974931 / 22:00 EDT.
#   Post-refactor everything is HTTP, so the orchestrator should not
#   occupy a GPU slot. EXCEPTION: a preset using `mllm_protector` loads
#   that defender's models in-process and DOES need a GPU — the Auto-GPU
#   guard below re-submits those (and only those) to the gpu partition.
#   (Caveat: keep mllm_protector waves GPU-busy; long idle stretches
#   waiting on remote targets could still trip the idle watchdog.)
#
# Time-limit alignment: gpu partition QOS caps any single job at 8h, and
# vLLM judge sub-jobs inherit that. Running the orchestrator longer than
# its judges is pointless (every task acquire would time out after the
# judges die). Hence 8h here too.

cd ~/projects/imaging_text_attacks_for_llm_jailbreaking
mkdir -p logs

# Usage: sbatch scripts/run_experiment.sbatch [preset] [--keep]
#        sbatch scripts/run_experiment.sbatch baseline
#        sbatch scripts/run_experiment.sbatch experiment --keep
EXPERIMENT=${1:-experiment}

# ── Auto-GPU guard ────────────────────────────────────────────────────────────
# Most presets are CPU-only (targets/judges run as separate vLLM gpu jobs; this
# orchestrator just does HTTP). The exception is a preset using `mllm_protector`,
# whose detector+detoxifier load IN-PROCESS and need a local GPU. Rather than make
# the user remember a second command, detect that case and re-submit THIS script
# once to the gpu partition, then exit. Normal runs fall through unchanged.
# MJ_GPU_RESUBMITTED breaks the resubmit loop (set on the gpu re-submission).
PRESET_YAML="conf/experiment/${EXPERIMENT}.yaml"
if [ -z "${MJ_GPU_RESUBMITTED:-}" ] && grep -q "mllm_protector" "$PRESET_YAML" 2>/dev/null; then
    echo "Preset '$EXPERIMENT' uses mllm_protector (GPU-local) → re-submitting to gpu partition."
    sbatch --partition=gpu --gres=gpu:1 --mem=48G \
           --export=ALL,MJ_GPU_RESUBMITTED=1 \
           scripts/run_experiment.sbatch "$@"
    exit 0
fi
# ──────────────────────────────────────────────────────────────────────────────

# Conda env activation only — no CUDA module needed for CPU-only runs; the vLLM
# sbatch sub-jobs load their own cuda module on their own nodes. (On a gpu re-
# submission MJ_GPU_RESUBMITTED=1, the GPU is for the in-process mllm_protector.)
module load anaconda3/2024.06
source activate AI_security

# Auto-delete old log files unless --keep is passed (preserves current job's logs)
if [ "$2" = "--keep" ]; then
    echo "Keeping existing logs/"
else
    echo "Cleaning old logs (keeping job $SLURM_JOB_ID) ..."
    find logs/ -type f ! -name "*${SLURM_JOB_ID}*" -delete 2>/dev/null || true
fi

# Stamp code provenance into the env so every results.json this run writes
# records the exact commit (provenance.py reads GIT_SHA/GIT_DIRTY first, then
# falls back to live `git`). Belt-and-suspenders for any node lacking .git.
export GIT_SHA=$(git rev-parse HEAD 2>/dev/null || cat .git_sha 2>/dev/null || echo unknown)
export GIT_DIRTY=$([ -n "$(git status --porcelain 2>/dev/null)" ] && echo true || echo false)
echo "Provenance: GIT_SHA=$GIT_SHA GIT_DIRTY=$GIT_DIRTY"

python main.py $EXPERIMENT
