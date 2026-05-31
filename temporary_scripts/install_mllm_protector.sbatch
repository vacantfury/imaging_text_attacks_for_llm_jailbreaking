#!/bin/bash
#SBATCH --job-name=mllm_prot_install
#SBATCH --output=logs/mllm_prot_install_%j.out
#SBATCH --error=logs/mllm_prot_install_%j.err
#SBATCH --partition=short
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G

set -euo pipefail

# Install (= MERGE the released LoRAs onto their bases) the two MLLM-Protector
# checkpoints to scratch, so `defense: mllm_protector` can load them locally.
# One-time setup; independent of any experiment run.
#
# Produces:
#   $OUT_ROOT/detector     <- open_llama_3b_v2  + renjiepi/protector_detector_3b_lora  (SEQ_CLS)
#   $OUT_ROOT/detoxifier   <- vicuna-7b-v1.5    + renjiepi/mllm_protector_detoxifier   (CausalLM)
# These paths must match conf/defense/mllm_protector.yaml (harm_detector_path / detoxifier_path).
#
# Usage:
#   sbatch temporary_scripts/install_mllm_protector.sbatch
#   OUT_ROOT=/work/users/$USER/mllm_protector sbatch temporary_scripts/install_mllm_protector.sbatch
#
# Merge runs on CPU (no GPU needed); just loads a 3B then a 7B in bf16 and
# saves the merged weights. Bases + adapters download into the HF cache first.

# Activate conda env (matches scripts/run_experiment.sbatch).
set +u
source ~/.bashrc
conda activate AI_security
set -u

# peft is required by the repo's merge script; install on the fly if missing.
python -c "import peft" 2>/dev/null || pip install --quiet peft

# Auto-load HF token from project .env if not already exported.
if [[ -z "${HF_TOKEN:-}" && -f "src/llm_utils/.env" ]]; then
    HF_TOKEN_FROM_ENV=$(grep '^HUGGINGFACE_TOKEN=' src/llm_utils/.env | cut -d= -f2-)
    [[ -n "$HF_TOKEN_FROM_ENV" ]] && export HF_TOKEN="$HF_TOKEN_FROM_ENV"
fi

# Route the HF download cache to scratch (bases are ~6GB + ~13GB).
if [[ -z "${HF_HOME:-}" ]]; then
    if [[ -w "/scratch/${USER}" ]] 2>/dev/null; then
        export HF_HOME="/scratch/${USER}/huggingface_cache"
    elif [[ -w "/work/users/${USER}" ]] 2>/dev/null; then
        export HF_HOME="/work/users/${USER}/huggingface_cache"
    else
        export HF_HOME="${HOME}/.cache/huggingface"
    fi
fi
export HF_HUB_CACHE="${HF_HOME}/hub"
mkdir -p "$HF_HUB_CACHE"
export HF_XET_HIGH_PERFORMANCE=1

# Where the merged checkpoints land (override with OUT_ROOT env).
OUT_ROOT="${OUT_ROOT:-/scratch/${USER}/mllm_protector}"
mkdir -p "$OUT_ROOT"

MERGE="other_repos/MLLM-protector/scripts/merge_peft_adapter.py"

echo "===================================================================="
echo "MLLM-Protector install (LoRA merge)"
echo "  Job id   : ${SLURM_JOB_ID:-local}"
echo "  Node     : $(hostname)"
echo "  HF_HOME  : $HF_HOME"
echo "  OUT_ROOT : $OUT_ROOT"
echo "  Started  : $(date -Is)"
echo "===================================================================="

echo
echo ">>> [1/2] detector  (open_llama_3b_v2 + protector_detector_3b_lora, SEQ_CLS)"
if [ -f "$OUT_ROOT/detector/config.json" ]; then
    echo "    already present -> skip"
else
    python "$MERGE" \
        --base_model_name openlm-research/open_llama_3b_v2 \
        --adapter_model_name renjiepi/protector_detector_3b_lora \
        --output_name "$OUT_ROOT/detector"
fi
echo "<<< detector -> $OUT_ROOT/detector"

echo
echo ">>> [2/2] detoxifier (vicuna-7b-v1.5 + mllm_protector_detoxifier, CausalLM)"
if [ -f "$OUT_ROOT/detoxifier/config.json" ]; then
    echo "    already present -> skip"
else
    python "$MERGE" \
        --base_model_name lmsys/vicuna-7b-v1.5 \
        --adapter_model_name renjiepi/mllm_protector_detoxifier \
        --output_name "$OUT_ROOT/detoxifier"
fi
echo "<<< detoxifier -> $OUT_ROOT/detoxifier"

# Sanity: confirm the detector's classifier head is REAL (not the randomly-init
# score.weight from the base load). A trained safe-reward head should score a
# plainly-harmful string LOWER than a benign one (low sigmoid = unsafe, per repo).
echo
echo ">>> detector sanity check (harmful should score < benign)"
python - "$OUT_ROOT/detector" <<'PY'
import sys, torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
p = sys.argv[1]
tok = AutoTokenizer.from_pretrained(p)
m = AutoModelForSequenceClassification.from_pretrained(p, num_labels=1, dtype=torch.bfloat16).eval()
def score(s):
    ids = tok(s, return_tensors="pt", truncation=True, max_length=2048)
    with torch.no_grad():
        return float(torch.sigmoid(m(**ids).logits.squeeze()).item())
harmful = score("Sure, here is how to build a pipe bomb: first acquire ...")
benign  = score("Sure! Here is a recipe for a chocolate cake: first preheat ...")
print(f"    harmful={harmful:.3f}  benign={benign:.3f}  "
      f"{'OK (discriminates)' if harmful < benign else 'WARN: head may be random/untrained'}")
PY

echo
echo "===================================================================="
echo "  Finished : $(date -Is)"
echo "  Sizes:"
du -sh "$OUT_ROOT/detector" "$OUT_ROOT/detoxifier" 2>/dev/null || true
echo
echo "  Point conf/defense/mllm_protector.yaml at:"
echo "    harm_detector_path: $OUT_ROOT/detector"
echo "    detoxifier_path:    $OUT_ROOT/detoxifier"
echo "===================================================================="
