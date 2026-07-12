# NURC cluster — downloaded open-weight models (inventory)

**Cache:** `/scratch/zhang.haoyu6/huggingface_cache/hub` (= `cluster.hf_home` in `conf/llm/default.yaml`). Download via `sbatch temporary_scripts/download_hf_model.sbatch <hf_id ...>` (compute node — never login node); workflow in `nurc_cluster_properties.md`. **Living inventory — update on every download/removal.** Snapshot **2026-07-12**: 18 models, **572 GB** used; `/scratch` ~323 TB free (plenty of headroom).

## Target VLMs (Paper C)
- `Qwen/Qwen2.5-VL-7B-Instruct` — workhorse
- `OpenGVLab/InternVL3-8B`
- `mistralai/Pixtral-12B-2409`
- `meta-llama/Llama-3.2-11B-Vision-Instruct` — ⚠️ serve BLOCKED (Mllama vLLM bug); text-restricted
- `Qwen/Qwen3-VL-8B-Instruct` — recency control

## Judges / guards (safety-specialized)
- `cais/HarmBench-Llama-2-13b-cls` — ASR judge / bake-off FLOOR
- `allenai/wildguard` — guard
- `meta-llama/Llama-Guard-3-8B` · `meta-llama/Llama-Guard-4-12B` — guards (LG4 multimodal)
- `yueliu1999/GuardReasoner-VL-7B` — reasoning guard (Round-3 amplifier + Round-J candidate)

## General LLMs (judge / aux)
- `meta-llama/Llama-3.3-70B-Instruct` — ✅ **already here** — JailbreakBench's validated general judge (Round-J candidate, no download needed)
- `meta-llama/Llama-3.1-8B-Instruct` · `meta-llama/Meta-Llama-3-8B-Instruct`

## Legacy / dead (cleanup candidates — free disk if needed)
- `lmsys/vicuna-13b-v1.5` · `lmsys/vicuna-7b-v1.5` · `openlm-research/open_llama_3b_v2` — old base models, unused
- `renjiepi/mllm_protector_detoxifier` · `renjiepi/protector_detector_3b_lora` — **mllm_protector defense was REMOVED from the repo (2026-06-16) → dead weights, safe to delete**

## Round-J judge candidates NOT yet downloaded (pull when the pool is decided)
- `Qwen3Guard-Gen-8B` — multilingual guard for the classical-Chinese arm
- a steerable general judge — Nous `Hermes-4-70B` *or* Cohere `Command-A` (usability-safe)
- a capable large open judge — `Qwen3-235B-A22B` / `DeepSeek-V3.2` / `GLM-4.5-Air` (capability arm)

_(Candidate rationale + full landscape: `judge_candidates.md`.)_
