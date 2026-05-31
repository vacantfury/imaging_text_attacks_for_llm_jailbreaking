# Experiments Plan — Paper C (AAAI-27)

Companion to `proposal.md`. **Cluster/open-weight VLMs are primary this time**; closed API models (Gemini / GPT-4o-mini / Claude, from Paper B) are a *generalization layer* run late, not the spine. All data collection freezes **~June 20** (see proposal §7).

## 0. Strategy

**Why cluster-first (changed from B):**
- **White-box access.** The deep result (cross-modal splitting, RQ-D) hinges on *whether and where the model reassembles split content internally*. Only open weights let us probe hidden states / attention to answer that — the closed-API black box can't.
- **Free, fast iteration** for the risky parts — we can run hundreds of attack variants while tuning.
- **No API-filter confound.** B had to discard cells (e.g. Claude `code_attack`, 82–93% empty) because provider filters fired upstream. Open targets remove that confound — every refusal is in-band model behavior.
- **Reproducibility / artifact.** Open target models + a full per-prompt judge audit trail = a re-runnable release. (Judge stays `gpt-5-nano`, B parity — see §1.)

**Why Phase 0 gates everything (the honest part):** the paper's *strength* lives in cross-modal splitting, which is both schedule-risky and conceptually uncertain (truly "joint-only" harm may be hard to construct). We therefore **test the ceiling in week 1**, before building the rest. Phase 0's outcome decides whether the spine is splitting (strong paper) or the modality-placement floor + over-refusal core (modest paper). We do **not** commit eight weeks to a direction whose upside is untested.

---

## 1. Models (4 total — trimmed)

Selection criteria: (i) **strong OCR** (read rendered/encoded text in the image channel); (ii) **compositional cross-modal reasoning** (split-attack reassembly); (iii) a **safety-alignment spread** so the intrinsic-image-safety pathway (B's pathway 2) can be studied across strong→weak alignment; (iv) **family diversity** — a robustness claim must not be one model's quirk; (v) open weights, vLLM-servable + HF-loadable for activation probing. Capability *scale* is deprioritized: family diversity matters more than size for a robustness result, and 7–12B targets keep iteration fast within the SLURM budget.

| # | Model | Family | Params | Role | Alignment | Status |
|---|---|---|---|---|---|---|
| 1 | **Qwen2.5-VL-7B-Instruct** | Alibaba | 7B | Workhorse (iterate here); best OCR; B anchor | mid | ✅ in registry |
| 2 | **Pixtral-12B** (`mistralai/Pixtral-12B-2409`) | Mistral | 12B | Breadth; weakly-aligned contrast | weak | ✅ in registry |
| 3 | **Llama-3.2-11B-Vision-Instruct** | Meta | 11B | Strongly safety-aligned target | strong | ⛔ **get** (gated repo) |
| 4 | **InternVL3-8B** (`OpenGVLab/InternVL3-8B`) | OpenGVLab | 8B | Cross-family generality; strong OCR | mid | ⛔ **get** |

**To acquire: only #3 and #4** — `meta-llama/Llama-3.2-11B-Vision-Instruct` (accept Meta's license on HF first) and `OpenGVLab/InternVL3-8B`. All four serve on 1–2 GPUs. Four distinct families, alignment spread strong→weak (Llama → Qwen/InternVL → Pixtral).

**Judge:** **`gpt-5-nano` (API), unchanged from B** — both the HarmBench ASR evaluator and the JailbreakBench refusal evaluator use it as backbone. Targets are open; the judge stays API for parity with B's recorded numbers. No classifier serving needed.

### 1.1 Getting a new model before experiments (onboarding checklist)

Do this once per new model (#3, #4) before it can be a task target:

1. **Weights.** Confirm it downloads on the cluster. Llama-3.2-11B-Vision is a **gated** HF repo — accept the license with the HF account, set `HF_TOKEN`, then `huggingface-cli download <id>`. InternVL3 is ungated.
2. **Registry row.** Add `LLMModel.<NAME> = ModelSpec("<hf_id>", Provider.NU_CLUSTER, max_context_len=<from config.json>)` in `src/llm_utils/llm_model.py`. Leave `chat_template=None` (modern VL checkpoints ship their own); set one only if vLLM can't derive it.
3. **Deploy config.** Add `conf/llm/<name>.yaml`: `num_gpus`, `max_model_len` (≤ `max_context_len`), `gpu_types_excluded`, and `trust_remote_code` if needed (**InternVL3 requires `trust_remote_code`**).
4. **Serve + smoke-test.** Bring the server up via `ClusterModelServerManager`; run a 4-row preset hitting the model with one text and one image prompt; confirm a non-empty response.
5. **OCR fidelity check (VL-specific, gating).** Render one encoded prompt as an image and ask the model to transcribe it. If it can't read rendered text, the image-channel attacks are unrealizable on that model → drop it, or restrict it to text-channel cells.

Models #1–#2 are already onboarded.

---

## 2. Fixed pieces (reused from B's harness)

- **Defenses:** `no_defense`, `sage` (system-message), `ecso`, **decoy-lever** (B's baseline: encoded text + fixed decoy image), and **`modality_complete` (NEW** — unconditionally caption/OCR the image *and* read text, run one unified safety check over the union; built from ECSO's caption + SAGE's discrimination primitives). *(Stretch: `joint_verify` — one safety judgment over the joint (text,image) input.)*
- **Attacks (transforms):** `modality_relocate` (payload → uncovered modality), `ecso_evade` (obfuscated output that passes ECSO's TELL self-judge), **`cross_modal_split` (NEW, stretch** — payload distributed across text+image). Encoders reused: `set_theory`, `formal_logic`, `code_attack`.
- **Benchmarks:** HarmBench-harmful (100) for ASR; JailbreakBench-benign (100) for utility. Rows 0–99.
- **Metrics:** ASR (HarmBench evaluator, lower=safer; empty→refusal) and benign-refusal (JBB-refusal evaluator, lower=better), both judged by **`gpt-5-nano`** (B parity); safety–utility plane per (model, defense, attack) cell. Bootstrap 95% CIs; paired permutation tests for attack-vs-baseline and guard-vs-decoy.
- **Decoding:** deterministic, temp 0, seed 42 (B parity).

---

## 3. Phased plan

### Phase 0 — Ceiling test + baseline (GATING, week 1, cluster)

**0a — Reproduce B's image-presence effect on open models.** Run `{no_defense, sage, ecso, decoy}` × `{set_theory, formal_logic, code_attack}` on all 4 models. *Purpose:* confirm the harness works open-weight and that B's "image lowers ASR" / "ECSO+decoy is strong" effect exists on cluster models (the thing C refutes). 4 models × 4 defenses × 3 encoders ≈ **48 cells**. **If B's effect doesn't even appear open-weight, the premise needs rework — surface immediately.**

**0b — Cross-modal splitting feasibility probe (THE CEILING TEST).** On Qwen2.5-VL-7B (+ InternVL3-8B), hand-construct ~10–20 candidate split attacks per encoder where the harmful instruction is distributed across text+image. For each, measure: (i) does **each channel individually** pass SAGE/ECSO/captioning as benign? (ii) does the model **reassemble harmful output** in its answer (ASR)? A "clean" split = both true.
> **Gate G0 (~Jun 6):** ≥ a handful of clean joint-only splits reproducing across 2 models → **splitting becomes the spine (Phase 3 promoted, strong-paper track).** If splits collapse to "payload mostly in one channel" (caught by per-channel checks) → **drop RQ-D; spine = floor (Phase 1–2) + over-refusal core (Phase 2b); modest-paper track.** Decided here, with ~2 weeks of slack.

### Phase 1 — Modality-placement attacks (floor, RQ-A/B, weeks 1–2)

Build `modality_relocate` + `ecso_evade`. Matrix: `{relocate, ecso_evade}` × `{sage, ecso, decoy}` × encoders × all 4 models + no-defense controls (specificity: attack must ≈ baseline ASR with no defense, large gap with defense). **RQ-A headline:** does `ecso_evade` recover ASR under **ECSO+decoy** (refuting B's Pareto-optimal claim)? ~ (2 attacks × 3 defenses + controls) × 3 encoders × 4 models ≈ **110–130 cells**. Iterate on the 7–8B subset, then complete the matrix.

### Phase 2 — The modality-complete guard + cost (RQ-C, weeks 2–3)

**2a:** run `modality_complete` guard vs Phase-1 attacks (does it restore protection?) + benign-refusal on JBB-benign (cost). Plot the safety–utility plane vs B's decoy lever — headline = does the guard dominate (lower refusal at equal/lower ASR)?
**2b (over-refusal core — the modest-track backbone if G0 is red):** systematic safety–utility audit of all defenses incl. the trivial-reject regime (B saw 76–100% benign refusal under SAGE+decoy on Gemini — does it recur open-weight?), plus a simple utility-recovery tweak. ~ all defenses × {harmful, benign} × 4 models.

### Phase 3 — Cross-modal splitting (deep result, RQ-D, CONDITIONAL on G0 green)

Full `cross_modal_split` matrix vs **all** defenses incl. `modality_complete`; show per-channel completeness is necessary-but-insufficient. Add `joint_verify` and characterize the per-channel-vs-joint boundary + cost. **Mechanism (white-box):** HF-load Qwen2.5-VL-7B / InternVL3-8B (not vLLM), probe whether/where split content is reassembled (hidden-state / attention analysis on a small prompt set). Validate the confirmed splits across all 4 models.

### Phase 4 — Generalization to API models (breadth, late, budget-permitting)

Port the *confirmed* attacks + guard to B's closed VLMs (gemini-2.x-flash, gpt-4o-mini, claude-sonnet-4-6). Shows the principle isn't open-model-specific. Run only after Phases 1–3 are locked; degrade gracefully if API access is restricted.

### Phase 5 — Statistics & figures

Bootstrap CIs on every headline cell; permutation tests on paired per-prompt verdicts; the safety–utility plane; mechanism figures; cross-family consistency + the alignment-spread (strong→weak) comparison.

---

## 4. Cluster execution (NURC)

- vLLM servers submitted as separate SLURM jobs via `ClusterModelServerManager`; orchestrator + servers count against `MAX_SUBMIT_JOBS_PER_USER = 8`. All four targets are 7–12B (1–2 GPUs each), so they co-serve comfortably within the cap.
- Judge is `gpt-5-nano` (API) — no classifier serving. VL target inputs go as base64 `image_url` on the vLLM OpenAI-compatible path (already supported).
- GPU budget: every target is 7–12B → 1–2 GPUs each; the full 4-model matrix fits without large-model staging.
- Mechanism work (Phase 3) uses HF `transformers` directly (activation hooks), separate from vLLM serving, on the 7–8B models for tractability.

---

## 5. Decision gates & calendar

| Gate | When | Test | Branch |
|---|---|---|---|
| **G0** | ~Jun 6 | Phase 0b: clean joint-only splits exist on ≥2 models? | yes → splitting spine (strong) · no → floor + over-refusal (modest) |
| **G0′** | ~Jun 6 | Phase 0a: B's image-presence effect reproduces open-weight? | no → premise rework, surface immediately |
| **G1** | ~Jun 13 | Phase 1: `ecso_evade` refutes ECSO+decoy; placement is defense-specific (not generic ASR boost)? | weak → narrow claim; lean on guard + over-refusal |
| **Freeze** | **~Jun 20** | all data collection done | writing begins (job started Jun 22) |

Calendar: **Now→Jun 6** Phase 0 + start Phase 1 (full-time). **Jun 6→Jun 20** Phases 1–2 always; Phase 3 if G0 green; pilot Phase 4 if ahead. **Jun 22→Jul 21** write (part-time); freeze governs.

---

## 6. Risks (cluster-specific)

| Risk | Mitigation |
|---|---|
| Splitting yields no clean joint-only attack (G0 red) | Pre-planned: fall back to floor + over-refusal core (Phase 2b) → modest but solid paper (EACL-Findings tier). Decided Jun 6 with slack. |
| Open models' OCR too weak to read rendered encoded text → image-channel attacks unrealizable | Qwen/InternVL are OCR-strong by design; run the §1.1 OCR check per model before relying on image-channel cells; drop or text-restrict weak-OCR models. |
| Weakly-aligned base model has no intrinsic image-safety → pathway-2 effects absent | Expected for Pixtral; that's the point of the alignment spread. Report intrinsic-safety results on Llama-3.2-Vision / Qwen / InternVL; use Pixtral for defense-wrapper cells + the weak-alignment contrast. |
| New-model onboarding blocks: InternVL3 `trust_remote_code` / vLLM version, or gated Llama-3.2-Vision access | Run §1.1 (incl. OCR check) before Phase 1; Qwen2.5-VL-7B (already serving) carries Phase 0 alone if either slips. |
| Judge (`gpt-5-nano`) cost on a large cell count | Targets are free; only judging costs, and it's modest (4 models × matrix × 100 rows). Batch judge calls; raw verdicts are stored (B parity) so re-judging never re-queries targets. |
