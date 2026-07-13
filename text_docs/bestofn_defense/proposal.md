# Research Proposal — Paper D: Canonicalization Defense Against Best-of-N (`bestofn_defense`)

**Workflow stage:** S9 run — code built (S7 done), pilot **GATED on Paper C freeing the cluster** (as of 2026-07-13)

*Full idea writeup + cspaper idea-check + internal reviewer analysis (R1–R6): `new_papers/paperd_bestofn_canonicalization_defense_idea.md` (local, gitignored — persists on this machine across /clear). Reference impl cloned at `other_repos/bon-jailbreaking/`. Origin: `text_docs/shared/future_work.md` §4.*

---

## 1. Decision & posture (settled 2026-07-13 — do NOT relitigate)

- **Paper D = §4** (best-of-N canonicalization defense), chosen over **§9** (judge-reliability). §4 and §9 are *opposite postures*.
- **Posture: BELIEVE Best-of-N is a real threat** (published NeurIPS'25 attack) **and DEFEND it.** Do **NOT** inject judge-doubt or run a "is BoN real under a good judge?" gate — that judge-doubt IS §9's contribution; mixing it into §4 is incoherent. (Earlier I wrongly proposed an "R1 motivation gate" — it was §9 smuggled in; it's dropped.) If you ever genuinely doubt BoN under an honest judge, that's the signal to switch to §9 *wholesale*, not to hedge inside §4.
- **Home:** THIS repo, `bestofn_defense` namespace. **Conceptually independent of Paper C** (decode-gap): canonicalization targets BoN's *own* stochastic augmentations, NEVER semantic encoding/decoding — do not reuse C's OCR-decode.
- **Venue:** AAAI-27 AI Alignment special track (abstract Jul 21 / paper Jul 28) *if* timeline allows; else a later venue (EMNLP/NeurIPS). Timeline-gated.

## 2. The idea

Best-of-N (Hughes et al., NeurIPS 2025) is a black-box **budget** attack: sample N stochastically-augmented variants of one request, succeed if *any* lands; ASR is power-law in N, defeating per-input guards (`1-(1-p)^N → 1`). **Contribution:** collapse the attacker's **effective N** by *canonicalizing* the input (not lowering per-try p). **Carve** BoN's augmentation space: *canonicalizable head* (caps/whitespace/Unicode → collapse) vs *irreducible tail* (word-scramble/ASCII-noise/image → survive). Measure with the **security work-factor** (ASR-vs-N scaling transformation: slope-bend vs constant-shift), against an **adaptive attacker**.

**Prior art to cite + differentiate (mechanism exists ad-hoc; novelty = the principled framing):** TRYLOCK (Layer-0 canonicalization), RLM-JB (ad-hoc canon + base64 de-obfuscation). Both in `paper/literature/my_base.bib`; RLM-JB entered in `text_docs/shared/literature_review.md` §6.4. cspaper idea-check: **net-positive on novelty** (the effective-N framing fills a gap; the *mechanism* is not novel). Deepest risk lives in the idea doc §R1–R6.

## 3. Judge methodology (settled)

**ONE consistent judge** = an LLM applying the HarmBench rubric (BoN's setting). This is NOT a multi-judge-correction study (that's §9).
- **TEST runs:** `llama_3_3_70b_instruct` — already cluster-served, JailbreakBench's official judge (>90% human agreement), ~free.
- **FINAL / headline:** `gpt-4o` (BoN's own judge, for direct comparability). Swap via the per-task `judge_model` field.

## 4. What's BUILT (committed + pushed, through `8ea4f73`)

| Layer | File | Notes |
|---|---|---|
| Attack | `src/prompt_transformations/text/encoders/non_llm_best_of_n_encoder.py` (`type_name: non_llm_best_of_n`) | scramble+caps+ASCII, `sigma`, seeded. Config `conf/text_encoding/best_of_n.yaml`. |
| Fan-out | `scripts/expand_bon_dataset.py` | behavior → N rows `<id>__bonK` (gitignored dir; local). |
| Defense | `src/defense/canonicalize.py` (`type_name: canonicalize`) | NFKC + strip-control + case-fold + whitespace. Config `conf/defense/canonicalize.yaml`. Carve unit-tested: caps-only→effective-N=1; full-augment→tail survives. |
| Judge infra | per-task `judge_model` field (`schemas.py` `DefenseEvaluateTask`, threaded in `task.py::_resolve_evaluators`/`_run_judging`) | parallel-paper-safe (C keeps gpt-5-nano default). |
| Analysis | `src/analysis/bon_asr.py` | ASR(N) = mean_i[1-(1-p_i)^N] + log-log slope. Stdlib, standalone CLI. Unit-tested. |
| Preset | `conf/experiment/bestofn_defense/reproduce_bon.yaml` | stage1 augment → stage2 `no_defense` **and** `canonicalize` (the R2 comparison in one run). |

**Verification status:** every piece unit-verified on this machine (syntax + logic), BUT the local `python3` is **3.9** — the project needs **3.12**, so the **full-pipeline end-to-end run is UNRUN**. The first cluster run IS that smoke; expect to fix small integration issues (registration, preset load, judge serving).

## 5. The decisive experiment — R2 defense gate

Run the pilot → `no_defense` vs `canonicalize` ASR(N) → **does canonicalization bend the slope or just shift the constant?** The carve unit-test already shows the head collapses and the scramble/ASCII tail survives, so the run measures *how big the surviving tail is*. The **full** R2 gate adds an **adaptive attacker** that relocates onto the irreducible tail (deferred).

## 6. HOW TO RUN THE PILOT (cold-resume recipe) — GATED on Paper C freeing the cluster

1. `python3 scripts/expand_bon_dataset.py --src data/harmbench_prompts.jsonl --out data/harmbench_bon_pilot.jsonl --n-variants 200 --n-behaviors 40`
2. Serve `llama_3_3_70b_instruct` (auto-served when a task targets it; or pre-serve on an H200 node). Target model in the preset is `qwen2_5_vl_7b` (already served) — swap if desired.
3. Run **stage 1** (prompt_transform) via `sbatch scripts/run_experiment.sbatch bestofn_defense/reproduce_bon`, or run stage 1 alone, read its output timestamp, and fill `CHAIN_TIMESTAMP` in the preset's stage-2 tasks.
4. Run **stage 2** (`no_defense` + `canonicalize`).
5. ASR(N): `python3 src/analysis/bon_asr.py <no_defense_run_dir>` and `<canonicalize_run_dir>`; compare curves.

Cost ≈ free (open judge on cluster), ~1–2 h cluster time. Outputs land under `outputs/bestofn_defense/…` (paper key auto-inferred from the preset subdir).

## 7. Deferred (post-pilot)

- **Adaptive attacker** → upgrades to the *full* R2 gate. (First mine `temporary_scripts/adaptive_attack.py` + `detector_gated_pilot.py` — likely reusable; kept locally, do NOT delete.)
- **Image BoN renderer** (`ir_bon`: text on randomized noisy background) — extends to the vision channel.
- **Full-N on-the-fly loop** — dataset expansion caps at pilot N (~hundreds); BoN's full N=10k needs a loop, not materialized rows.
- **Spell-correction** — canonicalize more of the scramble/ASCII tail (needs a dep; mature library per house rule).
- Promote this proposal to the full paper structure once the pilot lands.
