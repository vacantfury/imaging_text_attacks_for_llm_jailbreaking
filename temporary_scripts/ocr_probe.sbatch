#!/bin/bash
#SBATCH --job-name=ocr_probe
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH --output=logs/ocr_probe_%j.out
#SBATCH --error=logs/ocr_probe_%j.err

set -uo pipefail

# Self-contained OCR-fidelity probe (Round-0 gate). ONE job, ONE command, ALL
# models: on a single GPU it serves each VLM in turn (same flags the real
# experiment uses, resolved from conf/llm), probes localhost over the ir_plain
# images with temporary_scripts/ocr_probe.py, tears it down, moves to the next.
#
# Usage:
#   sbatch temporary_scripts/ocr_probe.sbatch                       # all 4 models
#   sbatch temporary_scripts/ocr_probe.sbatch qwen2_5_vl_7b pixtral_12b   # a subset
# Read results in logs/ocr_probe_<jobid>.out — one fidelity SUMMARY per model.

cd ~/projects/imaging_text_attacks_for_llm_jailbreaking
mkdir -p logs

# Default: every Paper-C cluster VLM, serially.
if [ "$#" -ge 1 ]; then
    MODELS=("$@")
else
    MODELS=(qwen2_5_vl_7b internvl3_8b pixtral_12b llama3_2_11b_vision)
fi

module load anaconda3/2024.06 cuda/12.1.1
source activate AI_security

# Compute nodes are offline — weights must already be in HF_HOME (download sbatch).
export HF_HOME="${HF_HOME:-/scratch/zhang.haoyu6/huggingface_cache}"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

IR_DIRS=(outputs/prompt_transform/harmbench/*ir_plain*/ir_plain)

# Serve one model, probe it, tear it down. Never aborts the whole job on a
# single model's failure — logs it and moves on (so one bad model ≠ no results).
run_one() {
    local MODEL="$1"
    local PORT=$((8000 + (SLURM_JOB_ID + RANDOM) % 1000))
    echo
    echo "############################################################"
    echo "# MODEL: $MODEL   (port $PORT, node $(hostname))"
    echo "############################################################"

    local SERVE_ARGS
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
    if [ -z "$SERVE_ARGS" ]; then echo "  ERROR: could not resolve serve args for '$MODEL' — skipping." >&2; return 1; fi

    # mllama needs eager on some vLLM versions; harmless elsewhere via per-model map.
    local EXTRA="${VLLM_EXTRA:-}"
    case "$MODEL" in llama3_2_11b_vision) EXTRA="$EXTRA --enforce-eager" ;; esac

    local SERVE_LOG="logs/ocr_probe_vllm_${MODEL}_${SLURM_JOB_ID}.log"
    echo "  vllm args : $SERVE_ARGS $EXTRA"
    echo "  serve log : $SERVE_LOG"

    python -m vllm.entrypoints.openai.api_server $SERVE_ARGS $EXTRA > "$SERVE_LOG" 2>&1 &
    local PID=$!

    # Wait for health (up to ~20 min cold load); bail this model if it dies.
    local READY=0
    for _ in $(seq 1 120); do
        if ! kill -0 "$PID" 2>/dev/null; then
            echo "  ERROR: vLLM died during startup for $MODEL — tail:" >&2; tail -20 "$SERVE_LOG" >&2; break
        fi
        if curl -sf "http://localhost:$PORT/health" >/dev/null 2>&1; then READY=1; break; fi
        sleep 10
    done

    if [ "$READY" -eq 1 ]; then
        echo "  server healthy — probing"
        python temporary_scripts/ocr_probe.py \
            --endpoint "http://localhost:$PORT/v1" \
            --model "$(python -c "from src.llm_utils.llm_model import LLMModel; print(LLMModel.from_string('$MODEL').model_id)")" \
            "${IR_DIRS[@]}" || echo "  WARN: probe errored for $MODEL (see above)"
    else
        echo "  ERROR: $MODEL never became healthy — see $SERVE_LOG" >&2
    fi

    # Tear down this model before the next one.
    kill "$PID" 2>/dev/null
    wait "$PID" 2>/dev/null
    echo "  torn down $MODEL"
}

echo "=================================================================="
echo "OCR probe — models: ${MODELS[*]}"
echo "  ir_plain dirs: ${IR_DIRS[*]}"
echo "=================================================================="
for MODEL in "${MODELS[@]}"; do
    run_one "$MODEL"
done
echo
echo "ALL MODELS DONE — scroll up for per-model SUMMARY lines."
