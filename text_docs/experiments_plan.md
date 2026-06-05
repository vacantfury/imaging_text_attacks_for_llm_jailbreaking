# Experiments Plan — Paper C (AAAI-27) · execution playbook

Companion to `proposal.md`. Cluster/open-weight VLMs are primary; closed API models are a late generalization layer. **Data collection freezes before the writing phase.** Run rounds in order; each round has a **gate** that decides whether/how to proceed.

---

## 0. Status — where we are (done ✓ / next ▶)

**Done — do NOT redo:**
- ✓ 4 target models chosen; **all weights downloaded** to `/scratch/$USER/huggingface_cache` (job 7307844).
- ✓ Llama-3.2-11B-Vision + InternVL3-8B **wired** into `llm_model.py` (+ `family`/`alignment_tier`) and `conf/llm/{llama3_2_11b_vision,internvl3_8b}.yaml` (InternVL3 has `trust_remote_code: true`). Commit `5f283e3`.
- ✓ Experiment-infra refactor (commits `944f7b9`→`6bf960d`): every `results.json` now carries `git_sha`/`git_dirty`/`schema_version`/`judge_config_hash`/`status`, named `metrics`+`primary_metric` (no `asr` overload), first-class `model_family`/`alignment_tier`/`companion_image_path`, `upstream_ref` pointer, atomic writes. Tables read these fields — **filter by `schema_version`** to exclude any stray legacy dir.
- ✓ Paper B's old `outputs/` archived to `backup_files/arr_may_submission_files/outputs/`; `outputs/` is empty and Paper-C-only.
- ✓ **OCR-fidelity probe built as a standalone tool** (`temporary_scripts/ocr_probe.{sbatch,py}`): serves each VLM serially, transcribes sampled `ir_plain` images vs upstream encoded text, prints per-image fidelity + SUMMARY. NURC HTTP-proxy connectivity for loopback health-check/inference **fixed** (the manager's `ProxyHandler({})` pattern → `no_proxy`/`--noproxy` in the probe sbatch).
- ✓ **Image renderer reworked (2026-06-05):** `ir_plain` now renders at a **fixed readable font and paginates long content across multiple images** — was single-image *shrink-to-fit*, which made long encodings (esp. `code_attack`, ~13k chars) OCR-illegible. Multi-image plumbed end-to-end: schema `image_encoded: list[str]` (back-compat str→[str]), all 4 provider services already accept an image list, defenses load all pages. Over-budget prompts (> `MAX_PAGES_PER_PROMPT=8` pages) are **excluded + flagged `is_within_maxlen=False` / `num_images` in `raw_results`**, never truncated. `page_height=4096` keeps typical prompts to 1–3 images (code_attack→2, math→1). `--max-model-len` kept at 16384 (32768 risks V100 KV-OOM on Pixtral-12B). Old single-image renders demarcated in `experiment_results.md`.

**Next ▶:** Round 0 **re-probe** (paginated renderer) → build attacks/defender → Rounds 1–7.

---

## 1. Fixed pieces (reference)

| Axis | Values |
|---|---|
| **Targets** | `qwen2_5_vl_7b` (workhorse), `pixtral_12b`, `llama3_2_11b_vision`, `internvl3_8b` — all NU-cluster, 1–2 GPU each |
| **Encoders** (Stage 1, exist) | `set_theory`, `formal_logic`, `code_attack` |
| **Image transforms** (Stage 1, exist) | `ir_plain` (render attack into image — **fixed-font, paginated multi-image**), `constant_image` (decoy; `params.image_path`), `blank_image` |
| **Defenses** (Stage 2) | `no_defense`, `sage`, `ecso`, `modality_complete`, `joint_verify` (stretch) · **SOTA baselines (built):** `eta` (black-box adaptation: CLIP image + ArmoRM output gates + safe-regen), `mllm_protector` (output-side detector+detoxifier). ⚠️ `eta`/`mllm_protector` load HF aux models → the orchestrator job needs a **GPU** (or serve them separately), and their checkpoints must be pulled/merged first. |
| **Attacks** (Stage 2/transforms) | **to build:** `modality_relocate`, `ecso_evade` · stretch: `cross_modal_split` |
| **Benchmarks** | HarmBench-harmful (rows 0–99) = ASR; JailbreakBench-benign (0–99) = utility |
| **Judge** | `gpt-5-nano` (API), B-parity; HarmBench + JBB-refusal evaluators |
| **Decoding** | temp 0, top_p 1, seed 42 |

**How to run a stage** (preset = `conf/experiment/<name>.yaml`):
```bash
sbatch scripts/run_experiment.sbatch <preset>     # cluster (auto-serves vLLM targets)
python main.py <preset>                            # local smoke (API targets only)
```
**Pipeline:** Stage 1 `prompt_transform` (render attack chains, model-independent) → Stage 2 `defense+evaluate` (consumes a Stage-1 step subdir via `source_transform_subdir`; applies defense, queries target, judges). Stage 1 is cheap and shared across all targets — render once, reuse.

---

## 2. Build status (code) — ✅ all built, registered, smoke-verified, committed

| Item | Status | Where |
|---|---|---|
| **`modality_complete` defender** (Round 4) | ✅ `35897be` | `src/defense/modality_complete.py` — RECOVER image→text, then one SAGE-style check over the *union* of both channels, eyes-closed |
| **`joint_verify` defender** (Round 5) | ✅ `35897be` | `src/defense/joint_verify.py` — judge the joint (text+image) request, then answer-or-refuse |
| **`ecso_evade` attack** (Round 3) | ✅ `6c26a74` | `src/prompt_transformations/text/ecso_evade.py` — output-framing wrapper; exploits the TELL(self-judge) vs HarmBench-judge asymmetry |
| **`cross_modal_split` attack** (Round 5) | ✅ `6c26a74` | `src/prompt_transformations/image/cross_modal_split.py` — **scaffold** (positional split; Round 2 tunes the rule) |
| **`modality_relocate` attack** (Round 3) | ✅ reuse existing | = render payload into the image vs SAGE-system → the existing **`ir_plain`** transform; no new class. Add evasion knobs only if Round 1 needs them |
| **`eta` defender** (Rounds 3–4 baseline) | ✅ `4cbb7b2` | `src/defense/eta.py` — faithful CLIP image pre-eval + ArmoRM output post-eval; white-box align → black-box safe-regen. ⚠️ verify ArmoRM formatting vs `other_repos/ETA`; needs CLIP-336 + ArmoRM-8B on GPU |
| **`mllm_protector` defender** (Rounds 3–4 baseline) | ✅ `4cbb7b2` | `src/defense/mllm_protector.py` — output-side harm detector + detoxifier. ⚠️ merge released LoRAs (`other_repos/MLLM-protector`) onto bases; needs 3B+7B on GPU |

All resolve via `create_defense(...)` / `create_transformation(...)` and pass parse+construct+apply smoke tests. **Caveats:** the four core *defenders* are final; the two *adaptive attacks* (`ecso_evade` framing, `cross_modal_split` rule) are **starting templates** Rounds 1–2 tune. The two SOTA-baseline defenders (`eta`, `mllm_protector`) are wired but **need their aux-model checkpoints pulled/merged + a GPU on the orchestrator** before they run (verify ETA's ArmoRM formatting against the repo first). Reporting follows the **coverage map + pre-registered outcome interpretations** in proposal §6.1–6.3 (every cell is a finding, win or hold — never claim a "sweep").

---

## 3. Rounds (do in order)

### Round 0 — Serve + smoke + OCR fidelity check  ▶ START HERE
**Goal:** confirm the 2 new models serve and can *read rendered text* (else image-channel attacks are impossible on them).
**Prereq:** none (weights + configs done).
**Steps:**
1. Make `conf/experiment/c0_smoke.yaml`: a few `defense+evaluate`/`no_defense` tasks on `llama3_2_11b_vision` + `internvl3_8b` over ~4 prompts, one text-only and one with an image (`ir_plain` of a benign sentence).
2. `sbatch scripts/run_experiment.sbatch c0_smoke` — this triggers the orchestrator to auto-serve both vLLM models.
3. **Check:** server logs come up clean (InternVL3: confirm `--trust-remote-code` passed, chat template resolved). **Llama-3.2-11B-Vision serving is currently BLOCKED** by a vLLM/transformers Mllama incompatibility (`MllamaProcessor has no attribute _get_num_multimodal_tokens`) — pin/upgrade the vLLM+transformers pair or text-restrict Llama; `--enforce-eager` alone does **not** fix it. Responses non-empty.
4. **OCR check (now a built tool, not eyeballing):** `sbatch temporary_scripts/ocr_probe.sbatch qwen2_5_vl_7b internvl3_8b pixtral_12b`. First run (job 7454645, **OLD single-image renderer**) found **`code_attack` unreadable on all 3** (qwen 0.45 / internvl3 0.10 / pixtral 0.00) while `set_theory`/`formal_logic` read ~0.8–1.0 — this is what drove the renderer rework (§0). **The live R0 gate is the RE-PROBE on the paginated renderer** (after re-rendering `ir_plain`): code_attack fidelity should jump toward ~1.0 at the fixed font.
**Gate Round 0:** each *serving* model reads the paginated rendered attack at acceptable fidelity. Expectation post-pagination: `code_attack` clears; **watch Pixtral on the longest encodings** (marginal — was the weakest OCR). A model still failing OCR → text-restrict (note in `experiment_results.md`). Prompts exceeding `MAX_PAGES_PER_PROMPT` are reported-excluded (`is_within_maxlen=False`), not dropped. Qwen + InternVL3 known-good on short encodings; Llama gated on the serve fix.

### Round 1 — Phase 0a: reproduce B's image-presence effect (baseline)  → Gate G0′
**Goal:** confirm B's "image lowers ASR / ECSO+decoy is strong" effect exists on the 4 open models — the thing C refutes. **No new code.**
**Steps:**
1. **Stage 1** preset `c1_stage1.yaml`: `prompt_transform` chains on HarmBench (+ JBB-benign for later) for `{set_theory, formal_logic, code_attack}` × `{(text), ir_plain, constant_image(decoy=mountain.png)}`. Run once; note the step subdirs under `outputs/prompt_transform/`.
2. **Stage 2** preset `c1_stage2.yaml`: `defense+evaluate`, defenses `{no_defense, sage, ecso, decoy}` × the Stage-1 chains × all 4 models → **48 cells**. `sbatch … c1_stage2`.
3. **Check** each `results.json`: `git_dirty:false`, `primary_metric` set, `model_family`/`companion_image_path` populated; record ASR per cell.
4. Record the matrix into `experiment_results.md` §C0.
**Gate G0′:** B's effect reproduces on ≥2 models (decoy/ir_plain lowers ASR; ECSO+decoy strong). If it does **not** appear open-weight → premise rework, surface immediately.

### Round 2 — Phase 0b: cross-modal splitting feasibility  → **Gate G0 (THE gate)**
**Goal:** decide strong-vs-modest paper track. **No pipeline build yet — manual probe.**
**Steps:**
1. By hand, construct ~10–20 candidate *split* attacks per encoder: harmful instruction distributed across text + image so each channel alone looks benign.
2. For each candidate, on Qwen2.5-VL-7B (+ InternVL3-8B): (a) check each channel *individually* passes SAGE/ECSO/caption as benign; (b) query the joint input and judge whether the model **reassembles harmful output** (ASR). A "clean split" = both true.
3. Tally clean splits per model; log examples in `experiments_findings.md` §4.
**Gate G0:**
- **≥ a handful of clean joint-only splits reproducing across 2 models → STRONG track.** Promote Round 5; build `cross_modal_split`+`joint_verify`.
- **Splits collapse to "payload mostly in one channel" → MODEST track.** Drop Round 5; lean on Round 4's over-refusal core. Paper targets EACL/Findings (proposal §11).

### Round 3 — Phase 1: modality-placement attacks  → Gate G1
**Goal:** refute B's "ECSO+decoy is Pareto-optimal" (RQ-A) + show placement is defense-specific (RQ-B).
**Prereq:** build `modality_relocate` + `ecso_evade` (§2).
**Steps:**
1. **Stage 1** `c3_stage1.yaml`: render the new attack chains over HarmBench.
2. **Stage 2 — core** `c3_stage2.yaml`: `{modality_relocate, ecso_evade}` × `{sage, ecso, decoy}` × 3 encoders × 4 models **+ `no_defense` controls** → ~110–130 cells. Iterate on Qwen+InternVL (7–8B) first, then complete.
3. **Stage 2 — SOTA baselines** `c3_baselines.yaml` *(after the `eta`/`mllm_protector` checkpoints are pulled/merged and the orchestrator has a GPU — see §1/§2)*: same attacks × `{eta, mllm_protector}` × encoders × 4 models. For **`eta`**, record *image-gate-fired* vs *output-gate-fired* separately (attribution, proposal §6.3): the `decoy` attack should make ETA's image-gate read "safe" → disable it; `ecso_evade` tests `mllm_protector`'s output classifier.
4. **Headline check:** does `ecso_evade` recover ASR under **ECSO+decoy** (and slip ETA's gates) vs B's near-zero? Record §C1 **per the coverage map** (proposal §6.2 — report each cell as a coverage data point, never a "sweep").
**Gate G1:** `ecso_evade` refutes ECSO+decoy AND the effect is defense-specific (attack ≈ no_defense baseline, big gap only under a defense). If weak → narrow the claim; lean on the guard + over-refusal.

### Round 4 — Phase 2: modality-complete guard + over-refusal (RQ-C)
**Goal:** the constructive fix + its utility cost.
**Prereq:** build `modality_complete` (§2).
**Steps:**
1. **2a:** `c4_guard.yaml` — `modality_complete` vs the Round-3 attacks (does it restore protection?) **and** on JBB-benign (refusal cost). Plot the safety–utility plane vs B's decoy lever **and vs `eta` / `mllm_protector`** — headline = the guard dominates (≤ refusal at ≤ ASR) and recovers what ETA's CLIP-scoring / MLLM-Protector's output-check miss (the semantic-scoring-vs-content-recovery contrast, proposal §6.3).
2. **2b (modest-track backbone):** `c4_overrefusal.yaml` — all defenses (incl. `eta`, `mllm_protector`) × {harmful, benign} × 4 models; quantify the trivial-reject regime (B saw 76–100% benign refusal under SAGE+decoy — does it recur?). Add a simple utility-recovery tweak.
3. Record §C2.

### Round 5 — Phase 3: cross-modal splitting (STRONG track only, conditional on G0)
**Goal:** show per-channel completeness is necessary-but-insufficient → joint verification needed.
**Prereq:** G0 green; build `cross_modal_split` + `joint_verify`.
**Steps:**
1. `c5_split.yaml`: full `cross_modal_split` × **all** defenses incl. `modality_complete` (+ `joint_verify`) × models. Characterize where per-channel breaks and joint holds + its cost.
2. **Mechanism (white-box):** HF-load Qwen2.5-VL-7B / InternVL3-8B (not vLLM); probe whether/where split content is reassembled (hidden-state / attention on a small set).
3. Record §C3.

### Round 6 — Phase 4: API-model generalization (breadth, budget-permitting)
**Goal:** show it isn't open-model-specific.
**Steps:** port the *confirmed* attacks + guard to `gemini-2.x-flash` / `gpt-4o-mini` / `claude-sonnet-4-6`. Run only after Rounds 3–5 are locked; degrade gracefully if API access is restricted. Record §C4.

### Round 7 — Phase 5: statistics, figures, freeze
**Steps:** bootstrap 95% CIs on every headline cell; paired permutation tests (attack-vs-baseline, guard-vs-decoy); safety–utility plane; mechanism figures; cross-family + alignment-spread (strong→weak) comparison. **Freeze data, then writing begins.**

---

## 4. Decision gates

| Gate | Test | Branch |
|---|---|---|
| **R0** | serving models read **paginated** rendered text (`ocr_probe` re-probe); Llama mllama-serve fix | fail OCR → text-restrict; >MAX_PAGES → `is_within_maxlen` exclude |
| **G0′** | Round 1: B's image-presence effect reproduces open-weight | no → premise rework |
| **G0** | Round 2: clean joint-only splits on ≥2 models | yes → strong (Round 5) · no → modest (Round 4 core) |
| **G1** | Round 3: `ecso_evade` refutes ECSO+decoy, defense-specific | weak → narrow claim |
| **Freeze** | all data done | writing begins |

**Sequencing:** Rounds 0–2 first; then Rounds 3–4 always, Round 5 if G0 green, Round 6 if ahead; then freeze → write.

---

## 5. Risks

| Risk | Mitigation |
|---|---|
| G0 red (no clean split) | Pre-planned modest track: Round 4 over-refusal core → solid Findings-tier paper. Known early (Round 2) with slack. |
| New model fails OCR / serving | **Long-content OCR failure now mitigated by fixed-font pagination** (was the `code_attack` killer at single-image); R0 re-probe confirms. Llama-3.2-Vision serve blocked by Mllama vLLM bug → version-pin fix or text-restrict; Qwen+InternVL3 carry Phase 0 if Llama slips. Pixtral marginal on longest encodings. Over-budget prompts excluded-and-flagged, not dropped. |
| Weakly-aligned Pixtral shows no intrinsic image-safety | Expected — that's the alignment-spread contrast; report pathway-2 on Llama/Qwen/InternVL, use Pixtral for defense-wrapper + weak-alignment cells. |
| Placement attack is "just a stronger attack," not modality-specific (G1) | `no_defense` controls anchor specificity (attack ≈ baseline with no defense). |
| Judge (`gpt-5-nano`) cost on a large cell count | Targets free; judging is modest; raw verdicts stored so re-judging never re-queries targets. |
