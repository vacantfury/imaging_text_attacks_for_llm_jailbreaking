# Experiments Plan — Coverage-Complete Defense · execution playbook

Companion to `proposal.md`. Cluster/open-weight VLMs are primary; closed API models are a late breadth layer. **Data collection freezes before the writing phase.** Run rounds in order; each round has a **gate** that decides whether/how to proceed.

> **▶ ACTIVE-PRESET CONVENTION (read first):** the only experiment file that is ever run is **`conf/experiment/experiment.yaml`** — via `sbatch scripts/run_experiment.sbatch experiment` (cluster) or `python main.py experiment` (local). **For every round/step, OVERWRITE `experiment.yaml`** with that round's tasks. Do **not** create separate per-round preset files (e.g. `c1_stage2.yaml`) and expect them to run — they won't; `experiment` is hard-coded as the run target. Keep prior rounds' YAML in git history, not as extra files.

> **▶ PROJECT SCOPE (read second):** this plan executes **only the current project** — the coverage-gap measurement (RQ1) and the coverage-complete guard (RQ2–RQ4). Compound attacks, cross-modal splitting, the `joint_verify` defender, mechanism probes, and API breadth are **Future Work** (proposal §11). Some of that code is already built (see §2) — it stays in the repo but is **not run** by this plan.

---

## 0. Status — where we are (done ✓ / next ▶)

**Done — do NOT redo:**
- ✓ 4 target models chosen; **all weights downloaded** to `/scratch/$USER/huggingface_cache` (job 7307844).
- ✓ Llama-3.2-11B-Vision + InternVL3-8B **wired** into `llm_model.py` (+ `family`/`alignment_tier`) and `conf/llm/{llama3_2_11b_vision,internvl3_8b}.yaml` (InternVL3 has `trust_remote_code: true`). Commit `5f283e3`.
- ✓ Experiment-infra refactor (commits `944f7b9`→`6bf960d`): every `results.json` now carries `git_sha`/`git_dirty`/`schema_version`/`judge_config_hash`/`status`, named `metrics`+`primary_metric` (no `asr` overload), first-class `model_family`/`alignment_tier`/`companion_image_path`, `upstream_ref` pointer, atomic writes. Tables read these fields — **filter by `schema_version`** to exclude any stray legacy dir.
- ✓ Paper ImgAug's old `outputs/` archived to `backup_files/arr_may_submission_files/outputs/`; `outputs/` is empty and current-project-only.
- ✓ **OCR-fidelity probe built as a standalone tool** (`temporary_scripts/ocr_probe.{sbatch,py}`): serves each VLM serially, transcribes sampled `ir_plain` images vs upstream encoded text, prints per-image fidelity + SUMMARY. NURC HTTP-proxy connectivity for loopback health-check/inference **fixed** (the manager's `ProxyHandler({})` pattern → `no_proxy`/`--noproxy` in the probe sbatch).
- ✓ **Image renderer reworked (2026-06-05):** `ir_plain` now renders at a **fixed readable font and paginates long content across multiple images** — was single-image *shrink-to-fit*, which made long encodings (esp. `code_attack`, ~13k chars) OCR-illegible. Multi-image plumbed end-to-end: schema `image_encoded: list[str]` (back-compat str→[str]), all 4 provider services already accept an image list, defenses load all pages. Over-budget prompts (> `MAX_PAGES_PER_PROMPT=8` pages) are **excluded + flagged `is_within_maxlen=False` / `num_images` in `raw_results`**, never truncated. `page_height=4096` keeps typical prompts to 1–3 images (code_attack→2, math→1). `--max-model-len` kept at 16384 (32768 risks V100 KV-OOM on Pixtral-12B). Old single-image renders demarcated in `experiment_results.md`.

**Next ▶:** Round 0 **re-probe** (paginated renderer) → Round 1 coverage gap → Round 2 guard + cost → Round 3/4 generalization. (Direction set 2026-06-06: current project is the **coverage-complete defense**; attack-side work moved to Future Work.)

---

## 1. Fixed pieces (reference)

| Axis | Values |
|---|---|
| **Targets** | `qwen2_5_vl_7b` (workhorse), `pixtral_12b`, `llama3_2_11b_vision`, `internvl3_8b` — all NU-cluster, 1–2 GPU each |
| **Encoders** (Stage 1, exist) | `set_theory`, `formal_logic`, `code_attack` |
| **Image transforms** (Stage 1, exist) | `ir_plain` (render attack into image — **fixed-font, paginated multi-image**), `constant_image` (decoy; `params.image_path`), `blank_image` |
| **Attack suite (current project)** | the existing encoders × image transforms above, used as **single-method portfolio** queries. **No new attacks built this project.** |
| **Defenses (Stage 2)** | `no_defense`, `sage`, `ecso`, `decoy`-lever, **`modality_complete` (the contribution)** · **SOTA baselines (breadth, built):** `eta` (CLIP image + ArmoRM output gates + safe-regen), `mllm_protector` (output-side detector+detoxifier). ⚠️ `eta`/`mllm_protector` load HF aux models → orchestrator job needs a **GPU** (or serve separately), checkpoints pulled/merged first. |
| **Benchmarks** | HarmBench-harmful (rows 0–99) = ASR; JailbreakBench-benign (0–99) = utility |
| **Judge** | `gpt-5-nano` (API), ImgAug-parity; HarmBench + JBB-refusal evaluators |
| **Decoding** | temp 0, top_p 1, seed 42 |

**How to run a stage** (preset = `conf/experiment/<name>.yaml`):
```bash
sbatch scripts/run_experiment.sbatch <preset>     # cluster (auto-serves vLLM targets)
python main.py <preset>                            # local smoke (API targets only)
```
**Pipeline:** Stage 1 `prompt_transform` (render attack chains, model-independent) → Stage 2 `defense+evaluate` (consumes a Stage-1 step subdir via `source_transform_subdir`; applies defense, queries target, judges). Stage 1 is cheap and shared across all targets — render once, reuse.

---

## 2. Build status (code) — ✅ all built, registered, smoke-verified, committed

| Item | Status | Where | Used this project? |
|---|---|---|:--:|
| **`modality_complete` defender** (the contribution) | ✅ `35897be` | `src/defense/modality_complete.py` — RECOVER image→text, then one SAGE-style check over the *union* of both channels, eyes-closed | **YES** |
| **`eta` defender** (breadth baseline) | ✅ `4cbb7b2` | `src/defense/eta.py` — faithful CLIP image pre-eval + ArmoRM output post-eval; white-box align → black-box safe-regen | breadth |
| **`mllm_protector` defender** (breadth baseline) | ✅ `4cbb7b2` | `src/defense/mllm_protector.py` — output-side harm detector + detoxifier | breadth |
| **`joint_verify` defender** | ✅ `35897be` | `src/defense/joint_verify.py` — judge the joint (text+image) request, then answer-or-refuse | **Future Work** (§11.2) |
| **`ecso_evade` attack** | ✅ `6c26a74` | `src/prompt_transformations/text/ecso_evade.py` — output-framing wrapper | **Future Work** (compound) |
| **`cross_modal_split` attack** | ✅ `6c26a74` | `src/prompt_transformations/image/cross_modal_split.py` — scaffold (positional split) | **Future Work** (§11.2) |

All resolve via `create_defense(...)` / `create_transformation(...)` and pass parse+construct+apply smoke tests. **For this project the only defender that matters is `modality_complete`** (+ the existing `sage`/`ecso`/`decoy` baselines; `eta`/`mllm_protector` if their aux-model checkpoints are pulled/merged and the orchestrator has a GPU — verify ETA's ArmoRM formatting against `other_repos/ETA` first). The attack-side code (`ecso_evade`, `cross_modal_split`) and `joint_verify` are **built but reserved for Future Work** — do not run them in this plan. Reporting follows the **coverage map** in proposal §1/§4.4/§8 (every cell is a finding — never claim a "sweep").

---

## 3. Rounds (do in order)

### Round 0 — Serve + smoke + OCR fidelity check  ▶ START HERE
**Goal:** confirm the serving models can *read rendered text* (else the image-channel cells are impossible on them).
**Steps:**
1. Overwrite `experiment.yaml` with a few `defense+evaluate`/`no_defense` tasks on `llama3_2_11b_vision` + `internvl3_8b` over ~4 prompts, one text-only and one with an `ir_plain` image of a benign sentence. `sbatch scripts/run_experiment.sbatch experiment`.
2. **Check:** server logs clean (InternVL3: `--trust-remote-code`, chat template resolved). **Llama-3.2-11B-Vision serving is currently BLOCKED** by a vLLM/transformers Mllama incompatibility (`MllamaProcessor has no attribute _get_num_multimodal_tokens`) — pin/upgrade the vLLM+transformers pair or **text-restrict Llama**; `--enforce-eager` alone does **not** fix it. Responses non-empty.
3. **OCR re-probe (built tool):** `sbatch temporary_scripts/ocr_probe.sbatch qwen2_5_vl_7b internvl3_8b pixtral_12b`. First run (job 7454645, **OLD single-image renderer**) found `code_attack` unreadable on all 3 (qwen 0.45 / internvl3 0.10 / pixtral 0.00) while `set_theory`/`formal_logic` read ~0.8–1.0 — this drove the renderer rework (§0). **The live R0 gate is the RE-PROBE on the paginated renderer.**
**Gate R0:** each *serving* model reads the paginated rendered attack at acceptable fidelity. `code_attack` should clear toward ~1.0 at the fixed font; **watch Pixtral on the longest encodings** (marginal). A model still failing OCR → text-restrict it (note in `experiment_results.md`). Over-budget prompts are reported-excluded (`is_within_maxlen=False`), not dropped. Llama gated on the serve fix; Qwen + InternVL3 carry the project if Llama slips.

### Round 1 — Coverage gap (RQ1, motivation)  → Gate G1
**Goal:** measure that **no single specialist defense covers the union** of the attack suite. **No new code.**
**Steps:**
1. **Stage 1** — `prompt_transform` chains on HarmBench (+ JBB-benign for later) for `{set_theory, formal_logic, code_attack}` × `{(text), ir_plain, decoy(=mountain.png)}`. Render once; note the step subdirs under `outputs/prompt_transform/`.
2. **Stage 2** — `defense+evaluate`, defenses `{no_defense, sage, ecso, decoy}` × the Stage-1 chains × the serving models. Record **per-cell ASR** and the **portfolio ASR per defense** (fraction of prompts on which ≥1 suite attack defeats that defense).
3. **Check** each `results.json`: `git_dirty:false`, `primary_metric` set, `model_family`/`companion_image_path` populated.
4. Build the **coverage map** (which surface each defense covers; which attack each defense lets through) into `experiment_results.md` §C0, and the portfolio-ASR summary into `experiments_findings.md` §1.
**Gate G1:** on ≥2 models, **every single defense leaves at least one suite attack that defeats it** (no single defense covers the union). If some single defense covers everything → the motivation weakens; pivot the headline to the **cost-of-completeness** characterization (still a paper — RQ3).

### Round 2 — The coverage-complete guard (RQ2) + cost (RQ3)  → Gate G2
**Goal:** the constructive result — the guard closes the gap, at a quantified utility cost.
**Steps:**
1. **2a — safety:** Stage 2 with `modality_complete` × the Round-1 attack suite × serving models on HarmBench. Does it reduce ASR across the *whole* suite below every specialist's worst case (G1's portfolio ASR)?
2. **2b — cost:** the same defenses (incl. `modality_complete`, `decoy`, `sage`, `ecso`) × **JBB-benign** → benign-refusal. ImgAug saw 76–100% benign refusal under SAGE+decoy on Gemini — does completeness recur it on the open models?
3. **Plot the safety–utility plane:** every (model, defense) as an (ASR, benign-refusal) point. Headline = does `modality_complete` **dominate the decoy lever** (≤ refusal at ≤ ASR) and the specialists?
4. Record §C1 (safety) + §C2 (cost) per the coverage map.
**Gate G2:** `modality_complete` covers the union (ASR ≤ every specialist's worst case across the suite). Near-guaranteed by construction; the real output is the *cost geometry* — report it whatever it is.

### Round 3 — SOTA baselines (breadth, conditional)
**Goal:** pre-empt "you only beat weak defenses." **Conditional** on the `eta`/`mllm_protector` checkpoints being pulled/merged and the orchestrator having a GPU (§1/§2).
**Steps:**
1. Stage 2: the Round-1/2 suite × `{eta, mllm_protector}` × serving models, ASR + benign-refusal.
2. For **`eta`**, record *image-gate-fired* vs *output-gate-fired* separately (a benign `decoy` should make ETA's image-gate read "safe" → disable it). For **`mllm_protector`** (output-axis), expect it to be *complementary* to our input-coverage guard — where it holds, that strengthens the "input-coverage and output-checking are orthogonal axes" framing (proposal §8).
3. Add these defenses to the coverage map and the safety–utility plane. Record §C3.
**If checkpoints/GPU are not affordable:** skip — the paper stands on SAGE/ECSO/decoy; note the omission honestly.

### Round 4 — Held-out generalization (RQ4) + statistics  → Freeze
**Goal:** show the guard's coverage is **structural, not benchmark-overfit** — the anti-bake-off result (P4).
**Steps:**
1. Configure/tune any guard knobs (caption prompt, discrimination threshold) on a **subset** of the attack suite (e.g. `set_theory` + `formal_logic`); then evaluate `modality_complete` on the **held-out** attack(s) (e.g. `code_attack`, `ir_plain` of a held-out encoder). The guard should cover the held-out attacks too.
2. **Statistics:** bootstrap 95% CIs on every headline cell; paired permutation tests (guard-vs-decoy, guard-vs-specialist) on per-prompt verdicts.
3. Finalize the safety–utility plane and the coverage map. Record §C4. **Freeze data, then writing begins.**

### Round 5 — API-model breadth (optional, budget-permitting)
**Goal:** show it isn't open-model-specific. Port the confirmed guard + suite to `gemini-2.x-flash` / `gpt-4o-mini` / `claude-sonnet-4-6`. Run only after Rounds 1–4 are locked; degrade gracefully if API access is restricted. Record §C5.

---

## 4. Decision gates

| Gate | Test | Branch |
|---|---|---|
| **R0** | serving models read **paginated** rendered text (`ocr_probe` re-probe); Llama mllama-serve fix | fail OCR → text-restrict; >MAX_PAGES → `is_within_maxlen` exclude |
| **G1** | Round 1: no single specialist defense covers the union, on ≥2 models | covered-by-one → pivot headline to cost-of-completeness (RQ3) |
| **G2** | Round 2: `modality_complete` covers the union; cost geometry quantified | near-guaranteed; output is the cost frontier regardless |
| **P4** | Round 4: guard covers **held-out** attacks | fails → coverage is overfit; narrow the claim to the tested suite |
| **Freeze** | Rounds 1–4 done (+ R3/R5 if affordable) | writing begins |

**Sequencing:** Round 0 → 1 → 2 → 4 always; Round 3 (SOTA baselines) and Round 5 (API breadth) if affordable. Then freeze → write. Attack-side / splitting / mechanism rounds are **Future Work** (proposal §11), not scheduled here.

---

## 5. Risks

| Risk | Mitigation |
|---|---|
| G1 weak — a single defense already covers the union | Pre-planned pivot: headline becomes the **cost-of-completeness** characterization (RQ3) — still a paper. Known early (Round 1). |
| Guard over-refuses as badly as the decoy lever (P3 fails) | That *is* a finding — the cost of completeness is high; report the frontier and a simple utility-recovery tweak. The paper is the characterization, not a guaranteed win. |
| New model fails OCR / serving | Fixed-font pagination mitigates long-content OCR failure; R0 re-probe confirms. Llama-3.2-Vision serve blocked by Mllama vLLM bug → version-pin or text-restrict; Qwen+InternVL3 carry the project. Pixtral marginal on longest encodings. Over-budget prompts excluded-and-flagged. |
| SOTA-baseline (eta/mllm_protector) checkpoint + GPU cost | Round 3 is **conditional/breadth** — skip cleanly if unaffordable; the paper stands on SAGE/ECSO/decoy. |
| "You just combined SAGE + ECSO" criticism of the guard | Frame the contribution as the **coverage principle + held-out generalization (RQ4)**, with the guard as its minimal instantiation; the cost frontier (RQ3) is the real content, not the existence of the guard. |
| Judge (`gpt-5-nano`) cost on a large cell count | Targets free; judging is modest; raw verdicts stored so re-judging never re-queries targets. |
