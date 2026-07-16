# Research Proposal — Paper D: Canonicalization Defense Against Best-of-N (`bestofn_defense`)

**Workflow stage:** S9 run — code built (S7 done) + **pilot prep DONE** (dataset built, judges wired to `gpt-5-mini`, docs reconciled — 2026-07-15). The cluster run itself is **GATED on the owner's go signal**.

*Full idea writeup + cspaper idea-check + internal reviewer analysis (R1–R6): `new_papers/paperd_bestofn_canonicalization_defense_idea.md` (local, gitignored — persists on this machine across /clear). Reference impl cloned at `other_repos/bon-jailbreaking/`. Origin: `text_docs/shared/future_work.md` §4.*

> **Judge (SHARED, ✅ resolved 2026-07-15):** report HarmBench ASR with **`gpt-5-mini`** (the validated headline judge) + a **WildGuard** own-policy robustness pass (rejudge) — NOT `gpt-5-nano`. Reuse the shared Round-J resolution; do not re-run judge selection. Report `judge_model_issue/JUDGE_MODEL_REPORT.md`; summary `text_docs/shared/judge_validation_sample.md`.

---

## 1. Decision & posture (settled 2026-07-13 — do NOT relitigate)

- **Paper D = §4** (best-of-N canonicalization defense), chosen over **§9** (judge-reliability). §4 and §9 are *opposite postures*.
- **Posture: BELIEVE Best-of-N is a real threat** (published NeurIPS'25 attack) **and DEFEND it.** Do **NOT** inject judge-doubt or run a "is BoN real under a good judge?" gate — that judge-doubt IS §9's contribution; mixing it into §4 is incoherent. (Earlier I wrongly proposed an "R1 motivation gate" — it was §9 smuggled in; it's dropped.) If you ever genuinely doubt BoN under an honest judge, that's the signal to switch to §9 *wholesale*, not to hedge inside §4.
- **Home:** THIS repo, `bestofn_defense` namespace. **Conceptually independent of Paper C** (decode-gap): canonicalization targets BoN's *own* stochastic augmentations, NEVER semantic encoding/decoding — do not reuse C's OCR-decode.
- **Venue:** AAAI-27 AI Alignment special track (abstract Jul 21 / paper Jul 28) *if* timeline allows; else a later venue (EMNLP/NeurIPS). Timeline-gated.

## 2. The idea

Best-of-N (Hughes et al., NeurIPS 2025) is a black-box **budget** attack: sample N stochastically-augmented variants of one request, succeed if *any* lands; ASR is power-law in N, defeating per-input guards (`1-(1-p)^N → 1`). **Contribution:** collapse the attacker's **effective N** by *canonicalizing* the input (not lowering per-try p). **Carve** BoN's augmentation space: *canonicalizable head* (caps/whitespace/Unicode → collapse) vs *irreducible tail* (word-scramble/ASCII-noise/image → survive). Measure with the **security work-factor** (ASR-vs-N scaling transformation: slope-bend vs constant-shift), against an **adaptive attacker**.

**Prior art to cite + differentiate (mechanism exists ad-hoc; novelty = the principled framing):** TRYLOCK (Layer-0 canonicalization), RLM-JB (ad-hoc canon + base64 de-obfuscation). Both in `paper/literature/my_base.bib`; RLM-JB entered in `text_docs/shared/literature_review.md` §6.4. cspaper idea-check: **net-positive on novelty** (the effective-N framing fills a gap; the *mechanism* is not novel). Deepest risk lives in the idea doc §R1–R6.

## 3. Judge methodology (settled — shared Round-J resolution, 2026-07-15)

Report with the **shared** judges (same as Papers B/C — do NOT re-run judge selection; `text_docs/shared/judge_validation_sample.md`). This is NOT a multi-judge-correction study (that's §9); it is one consistent headline judge plus a robustness cross-view.
- **Headline:** `gpt-5-mini` — the validated headline judge, HarmBench rubric (API). Set as the pilot's per-task `judge_model`.
- **Robustness:** `WildGuard` — own-policy response-harm view, applied as a **rejudge** pass on the saved responses (no target re-query), via `scripts/build_rejudge_preset.py --paper bestofn_defense --campaigns bestofn_pilot --judges "wildguard:wildguard"`.
- **Cheap-smoke alt:** `llama_3_3_70b_instruct` (cluster-served, ~free, JBB official judge, >90% human agreement) as a temporary primary for a zero-cost first integration smoke, then rejudge to `gpt-5-mini`.
- **Optional BoN-parity appendix:** `gpt-4o` (BoN's own judge) for a direct-comparability check only — NOT the headline. (Supersedes the earlier gpt-4o-as-final plan.)

## 4. What's BUILT (committed + pushed, through `8ea4f73`)

| Layer | File | Notes |
|---|---|---|
| Attack | `src/prompt_transformations/text/encoders/non_llm_best_of_n_encoder.py` (`type_name: non_llm_best_of_n`) | scramble+caps+ASCII, `sigma`, seeded. Config `conf/text_encoding/best_of_n.yaml`. |
| Fan-out | `scripts/expand_bon_dataset.py` | behavior → N rows `<id>__bonK` (gitignored dir; local). |
| Defense | `src/defense/canonicalize.py` (`type_name: canonicalize`) | NFKC + strip-control + case-fold + whitespace. Config `conf/defense/canonicalize.yaml`. Carve unit-tested: caps-only→effective-N=1; full-augment→tail survives. |
| Judge infra | per-task `judge_model` field (`schemas.py` `DefenseEvaluateTask`, threaded in `task.py`) + `rejudge` mode (`RejudgeTask`) for the WildGuard robustness pass | parallel-paper-safe (each paper sets its own `judge_model`). |
| Analysis | `src/analysis/bon_asr.py` | ASR(N) = mean_i[1-(1-p_i)^N] + log-log slope. Stdlib, standalone CLI. Unit-tested. |
| Preset | `conf/experiment/bestofn_defense/reproduce_bon.yaml` | stage1 augment → stage2 `no_defense` **and** `canonicalize`, judged `gpt-5-mini`, tagged `campaign: bestofn_pilot`. |

**Verification status:** every piece unit-verified (syntax + logic). Local `python3` is now **3.13** (the earlier "3.9" blocker is stale) and the pilot dataset is **built** (`data/harmbench_bon_pilot.jsonl`, 8000 rows), but the **full model-serving + judging pipeline is still UNRUN** — per the cluster-first rule the first cluster run IS that smoke; expect small integration fixes (transform registration, preset/chain load, gpt-5-mini judging path, WildGuard serving/parse).

## 5. The decisive experiment — R2 defense gate

Run the pilot → `no_defense` vs `canonicalize` ASR(N) → **does canonicalization bend the slope or just shift the constant?** The carve unit-test already shows the head collapses and the scramble/ASCII tail survives, so the run measures *how big the surviving tail is*. The **full** R2 gate adds an **adaptive attacker** that relocates onto the irreducible tail (deferred).

## 6. HOW TO RUN THE PILOT (cold-resume recipe) — GATED on the owner's go signal

Prep DONE this session: dataset built, judges wired to `gpt-5-mini` in the preset, `campaign: bestofn_pilot` tag added, docs reconciled. The run itself is one gated sequence — **do not launch without the owner's go**:

1. ✅ **Dataset built** — `data/harmbench_bon_pilot.jsonl` (40 behaviors × 200 variants = 8000 rows). (Halve `--n-variants` to 100 to cut cost/time.)
2. **Stage 1** (BoN augment) — `sbatch scripts/run_experiment.sbatch bestofn_defense/reproduce_bon` runs the whole preset; or run stage 1 alone, read its output timestamp under `outputs/bestofn_defense/prompt_transform/harmbench/<ts>/`, and fill `CHAIN_TIMESTAMP` in the preset's stage-2 tasks.
3. **Stage 2** (`no_defense` + `canonicalize`, target `qwen2_5_vl_7b` served, judge `gpt-5-mini`). Writes two dirs under `outputs/bestofn_defense/defense+evaluate/harmbench/` tagged `campaign: bestofn_pilot`, each with `raw_results.jsonl`.
4. **WildGuard robustness rejudge** (no target re-query) — `python scripts/build_rejudge_preset.py --paper bestofn_defense --campaigns bestofn_pilot --judges "wildguard:wildguard" --out conf/experiment/bestofn_defense/rejudge_bon.yaml`, then `sbatch scripts/run_experiment.sbatch bestofn_defense/rejudge_bon` (serves WildGuard, re-scores the two dirs into `outputs/bestofn_defense/rejudge/`).
5. **ASR(N):** `python3 src/analysis/bon_asr.py <no_defense_dir>` and `<canonicalize_dir>` (gpt-5-mini headline) — compare curves; slope-bend vs constant-shift is the R2 gate read.

**Cost estimate (house rule):** target queries on served `qwen2_5_vl_7b` ≈ free; `gpt-5-mini` judging ≈ 16k judgments × ~800 tok ≈ 12.8M input tok ≈ **$3–4** (@ $0.25/1M in, output negligible); WildGuard rejudge served ≈ free. **Total ≈ $3–4**, ~1–2 h cluster. Outputs land under `outputs/bestofn_defense/…`.

## 7. Deferred (post-pilot)

- **Adaptive attacker** → upgrades to the *full* R2 gate. (First mine `temporary_scripts/adaptive_attack.py` + `detector_gated_pilot.py` — likely reusable; kept locally, do NOT delete.)
- **Image BoN renderer** (`ir_bon`: text on randomized noisy background) — extends to the vision channel.
- **Full-N on-the-fly loop** — dataset expansion caps at pilot N (~hundreds); BoN's full N=10k needs a loop, not materialized rows.
- **Spell-correction** — canonicalize more of the scramble/ASCII tail (needs a dep; mature library per house rule).
- Promote this proposal to the full paper structure once the pilot lands.
