#!/bin/bash
#SBATCH --job-name=ocr_probe
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=02:00:00
#SBATCH --output=logs/ocr_probe_%j.out
#SBATCH --error=logs/ocr_probe_%j.err

set -uo pipefail

# Self-contained OCR-fidelity probe (Round-0 gate). Serves ONE VLM on this GPU
# node with the SAME flags the real experiment uses (resolved from conf/llm),
# probes localhost with temporary_scripts/ocr_probe.py over the ir_plain images,
# then tears the server down. You just submit it.
#
# Usage:
#   sbatch temporary_scripts/ocr_probe.sbatch                 # default qwen2_5_vl_7b
#   sbatch temporary_scripts/ocr_probe.sbatch internvl3_8b
#   sbatch temporary_scripts/ocr_probe.sbatch pixtral_12b
#   sbatch temporary_scripts/ocr_probe.sbatch llama3_2_11b_vision
# Read results in logs/ocr_probe_<jobid>.out (per-image fidelity + SUMMARY).
# Extra vllm flags (e.g. mllama): VLLM_EXTRA="--enforce-eager" sbatch ... llama3_2_11b_vision

cd ~/projects/imaging_text_attacks_for_llm_jailbreaking
mkdir -p logs

MODEL=${1:-qwen2_5_vl_7b}
PORT=$((8000 + SLURM_JOB_ID % 1000))   # avoid clashes with real server jobs

module load anaconda3/2024.06 cuda/12.1.1
source activate AI_security

# Compute nodes are offline — weights must already be in HF_HOME (download sbatch).
export HF_HOME="${HF_HOME:-/scratch/zhang.haoyu6/huggingface_cache}"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

# Resolve vLLM serve args from conf/llm exactly like ClusterModelServerManager.
SERVE_ARGS=$(python - "$MODEL" "$PORT" <<'PY'
import sys
from pathlib import Path
from src.experiment.config import load_conf
from src.llm_utils.llm_model import LLMModel
model, port = sys.argv[1], sys.argv[2]
m = LLMModel.from_string(model)
c = load_conf("llm", model)["cluster"]
args = [f"--model {m.model_id}", "--host 0.0.0.0", f"--port {port}",
        f"--gpu-memory-utilization {c['gpu_memory_utilization']}",
        f"--max-model-len {c['max_model_len']}"]
if c.get("dtype"):
    args.append(f"--dtype {c['dtype']}")
if c.get("trust_remote_code"):
    args.append("--trust-remote-code")
ct = c.get("chat_template") or m.chat_template
if ct:
    args.append(f"--chat-template {(Path('src/llm_utils/chat_templates') / (ct + '.jinja')).resolve()}")
print(" ".join(args))
PY
)
if [ -z "$SERVE_ARGS" ]; then echo "ERROR: failed to resolve serve args for '$MODEL'." >&2; exit 1; fi

SERVE_LOG="logs/ocr_probe_vllm_${MODEL}_${SLURM_JOB_ID}.log"
echo "=================================================================="
echo "OCR probe — model=$MODEL  port=$PORT  node=$(hostname)"
echo "  vllm args : $SERVE_ARGS ${VLLM_EXTRA:-}"
echo "  serve log : $SERVE_LOG"
echo "=================================================================="

# Start vLLM in the background; ensure it's killed however we exit.
python -m vllm.entrypoints.openai.api_server $SERVE_ARGS ${VLLM_EXTRA:-} > "$SERVE_LOG" 2>&1 &
SERVE_PID=$!
trap 'echo "Tearing down vLLM (pid $SERVE_PID)"; kill $SERVE_PID 2>/dev/null; wait $SERVE_PID 2>/dev/null' EXIT

# Wait for health (up to ~20 min for cold weight load).
echo "Waiting for server health on :$PORT ..."
READY=0
for i in $(seq 1 120); do
    if ! kill -0 $SERVE_PID 2>/dev/null; then
        echo "ERROR: vLLM died during startup — see $SERVE_LOG" >&2; tail -30 "$SERVE_LOG" >&2; exit 1
    fi
    if curl -sf "http://localhost:$PORT/health" >/dev/null 2>&1; then READY=1; break; fi
    sleep 10
done
if [ "$READY" -ne 1 ]; then echo "ERROR: server not healthy in time — see $SERVE_LOG" >&2; tail -30 "$SERVE_LOG" >&2; exit 1; fi
echo "Server healthy. Running probe ..."
echo

# Probe all rendered ir_plain chains on HarmBench.
python temporary_scripts/ocr_probe.py \
    --endpoint "http://localhost:$PORT/v1" \
    --model "$(python -c "from src.llm_utils.llm_model import LLMModel; print(LLMModel.from_string('$MODEL').model_id)")" \
    outputs/prompt_transform/harmbench/*ir_plain*/ir_plain

echo
echo "Probe done for $MODEL."
