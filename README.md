# LLM Guardrail Security — Encoded & Image-Rendered Jailbreaks vs. Black-Box Defenses

Research codebase on the security of the **guardrail layer** — the out-of-model safety mechanisms (guard classifiers, filters, caption/decode pipelines) deployed around LLMs and VLMs. The through-line: encoded and image-rendered jailbreaks route past deployed guards, which *inspect or reason about* content but never *decode* an obfuscated payload (the **decode gap**) — we measure that gap from the attack side and close it from the defense side with a black-box **recover→decode→guard** amplifier.

This repo is the shared harness for a line of work:

- **MathEnc** — *Exposing LLM Safety Gaps Through Mathematical Encoding* (published): text-side encoders (set theory, formal logic, code) that recast harmful queries into out-of-distribution surface forms.
- **ImgAug** — *Image Augmentation Strengthens VLM Defenses Against Encoded Jailbreak Attacks* (under review): adding an image — even a content-unrelated decoy — changes a defense's behavior, because the defense's coverage happens to line up (or not) with where the encoded content lives.
- **The Decode Gap** (in progress, `autoattack_defense/`): deployed black-box defenses — including the newer multimodal and reasoning guards — *inspect or reason about* content but never **decode** an obfuscated payload, so semantically-encoded harm (in text or rendered into an image) routes past them. We build the minimal black-box **recover→decode→guard** amplifier that closes this gap, show it is guard-agnostic by plugging in external guards, and quantify its over-refusal cost. The argument is structural — read off the guards' own published designs — not a leaderboard.
- **Variance Channels** (in progress, `bestofn_attack/`): *Best-of-N Jailbreaking Beyond Surface Noise*. A Best-of-N attack's power is governed by its **variance channel** — what actually differs between sampled draws (surface noise vs. semantic paraphrase vs. sampled attack strategy). Repeatedly sampling one strong *structural* attack beats vanilla surface-noise BoN both defended and undefended, and survives the input-normalization defenses that neutralize surface BoN. Depth, not breadth: a diverse bank of attack families barely beats the single best attack while costing far more queries. The `bestofn_defense/` namespace holds this paper's **supportive** canonicalize→guard defense section — it maps where normalization still holds (the surface channel) versus where it fails (the deeper strategy channel). It is **not** a separate paper.

> This is an active **multi-paper** repo whose direction shifts; docs, presets, and outputs are namespaced per paper (`text_docs/<paper>/`, `conf/experiment/<paper>/`, `outputs/<paper>/` — see `text_docs/shared/papers.md` for the alias index). Each paper's `proposal.md` and `experiments_plan.md` under `text_docs/<paper>/` state what is currently in scope. Working result logs (`experiment_results.md`, `experiment_matrix.md`) are deliberately **not published** — analyzed results appear in the papers, not as untracked working notes.

---

## How it works

The **amplifier** and the **defense** are two separate things; conflating them is the single most common misreading of this pipeline.

```
        ATTACK                    DEFENSE                        MEASURE
  ┌───────────────┐    ┌──────────────────────────┐    ┌──────────────────┐
  │ text encoder  │    │ amplifier: recover+decode│    │ target VLM answer│
  │  ± image      │───▶│         ↓                │───▶│        ↓         │
  │  renderer     │    │ defense: transform OR gate│   │ judge → ASR / OR │
  └───────────────┘    └──────────────────────────┘    └──────────────────┘
```

1. **Attack** (`prompt_transform` mode) — a prompt (harmful, or benign for the over-refusal axis) is encoded into an alternative representation and/or rendered into an image.
2. **Amplifier** — *recover* (the target VLM transcribes the image back to text) then *decode* (the target VLM restates the encoding in plain English). This is a **transform**, not a safety mechanism: it exists so the defense can see the hidden payload. It is guard-agnostic — prepend it to any guard.
3. **Defense** (`defense+evaluate` mode) — the safety mechanism acting on the (decoded) prompt, in two kinds:
   - **Transform defense** (e.g. SAGE): rewrites the text into a safety-check prompt the target answers.
   - **Gate defense** (e.g. WildGuard, LlamaGuard-3, Qwen3Guard): a *classifier* that blocks with a canned refusal or passes the **original** prompt through unchanged. A gate never rewrites.
4. **Judge** — external measurement, never the target and never a defense classifier. Harm is scored with the HarmBench rubric (→ ASR) and refusal with the OR-Bench 3-class rubric (→ over-refusal).

The amplifier's contribution is measured as `modality_complete` vs. `guard_baseline` **holding the defense fixed**. Over-refusal is a property of the chosen defense's own calibration, not of the amplifier.

### Headline metric: ensemble (best-of-N) ASR

Because the attack side is a *suite* of ~10 elementary encoders and renderers, a behavior counts as jailbroken under a condition if **any** attack in the suite breaks it — an AutoAttack-style OR-reduction over per-prompt `asr` (`src/analysis/portfolio.py`). Headline comparisons run `no_defense` → `guard_baseline` → `modality_complete` on that ensemble number.

Per-attack ASR, and its mean across the suite, is a **diagnostic view only**: different attacks break different inputs, so the per-attack mean understates the attacker's real union power and flatters the defense.

### Judge

`gpt-5-mini` is the decided main judge across papers, selected by a human-calibration bake-off against a more lenient earlier judge. WildGuard appears only as a secondary robustness/calibration lens — it does not follow a completion rubric and is **not** valid as a primary ASR judge. The `rejudge` mode re-scores stored responses with a different judge without re-querying the target, so judge changes cost nothing on the target side.

---

## Attacks

Text encoders and image renderers share **one** registry (`src/prompt_transformations/transformation_factory.py`); `text/` vs `image/` is directory organization only. Steps compose into chains, so an encoding can be rendered into an image by appending a renderer.

| Family | `type_name`s |
|---|---|
| Baselines / non-LLM | `non_llm_baseline`, `non_llm_homoglyph`, `non_llm_artprompt`, `non_llm_cipher` (base64 / caesar), `non_llm_symbol_injection` |
| Semantic encodings (LLM) | `llm_set_theory`, `llm_formal_logic`, `llm_quantum_mechanics`, `llm_classical_language`, `llm_semantic_camo` |
| Decomposition | `non_llm_addition_equation_split_reassemble`, `non_llm_conditional_probability`, `deep_inception`, `ecso_evade`, `code_attack` |
| Image renderers | `ir_plain` (fixed-font paginated), `ir_figstep`, `ir_fc_typo`, `ir_fc_flowchart`, `ir_blank`, `ir_constant` |
| Established multimodal attacks | `ir_low_contrast`, `ir_occluded` (perceptual blindness), `ir_mm_typo` (MM-SafetyBench), `ir_distraction_grid` (Text-DJ/CS-DJ) |
| **Best-of-N (Paper D)** | `non_llm_best_of_n`, `llm_paraphrase`, **`variance_channel_bon`** |
| **Adaptive (against our own defense)** | `llm_decode_evasion`, `cross_modal_split`, `ir_semantic_split` |

**`variance_channel_bon`** is Paper D's apparatus: one Best-of-N transform, parameterized by *where* the N draws differ. `surface` delegates to vanilla character/caps/ASCII noise — correlated draws that an input-normalization defense collapses to an effective N of ~1. `paraphrase` rewords per draw, surviving normalization. `strategy` samples an attack *family* per draw from a configured bank — anti-correlated draws, strongest defense-survival.

The **adaptive attacks** are the honest stress tests, aimed at this repo's own defense rather than at someone else's. `llm_decode_evasion` reframes a prompt so the amplifier's short decode reads benign while the full answer stays harmful. `cross_modal_split` and `ir_semantic_split` place harm so it exists only in the *joint* text+image reading, each channel alone reading benign — the amplifier decodes **per channel**, so these probe its stated boundary rather than its strong case. All three are built and evaluated as appendix probes of those limitations.

The **ImgAug decoy lever** is not a defense — it is the attack-side condition of pairing a prompt with a content-unrelated constant image, implemented as the `ir_constant` renderer.

---

## Defenses

All registered under `src/defense/defender_factory.py` (`@register_defense`). Every defense implements one interface, `query(prompts, target_service, is_multimodal, source_dir, system_message)`, and **owns** its target-model interaction — wrap the input, query once, or query→inspect→re-query.

| `type_name` | Kind | Notes |
|---|---|---|
| `no_defense` | — | passthrough baseline (the attack floor) |
| `sage` | transform | prompt-level safety guard, input-text surface |
| `semantic_smooth` | transform | semantic-perturbation smoothing baseline |
| `ecso` | transform | caption-mediated re-verification, gated on `has_image` |
| `amia_ia` | transform | intention-analysis only — the "inspects but never decodes" comparison |
| `guard_baseline` | gate | a published guard classifier alone, **no amplifier** — the comparison arm |
| **`modality_complete`** | **amplifier + defense** | **the contribution** — recover **and** decode every channel, then one unified safety check. `guard_model=None` uses the SAGE transform; `guard_model=<classifier>` makes it a gate. |
| `canonicalize` | transform | input-normalization defense (Paper D's supportive section) |
| `canonicalize_guard` | gate | canonicalize → guard composition, with an AND/OR compose knob and verdict persistence |
| `joint_verify` | joint | joint text+image verification; built, **Future Work** |

Guard checkpoints available as gates or panel members: LlamaGuard-3-8B, LlamaGuard-4-12B, WildGuard, Qwen3Guard-Gen-8B, GuardReasoner-VL-7B, ShieldLM-7B, ThinkGuard. Panel membership is set per preset.

---

## Installation

```bash
pip install -e .
```

Python ≥ 3.12. Dependencies in `pyproject.toml`.

API keys (for judge + API targets) are read as plain environment variables (see `.env.example`). Supply them however you prefer: export them in your shell, drop a gitignored `.env` at the repo root, or feed them from your own secret manager. The variables:

```bash
OPENAI_API_KEY=...        # judge + OpenAI targets/encoders
ANTHROPIC_API_KEY=...     # Anthropic targets (Message Batches API)
GOOGLE_API_KEY=...        # Gemini targets (Batch API)
HUGGINGFACE_TOKEN=...     # gated HF model downloads (cluster vLLM serving)
DEEPSEEK_API_KEY=...      # DeepSeek (OpenAI-compatible; judge/eval)
ZAI_API_KEY=...           # Z.AI / GLM (OpenAI-compatible; judge/eval)
XAI_API_KEY=...           # xAI / Grok (OpenAI-compatible)
MOONSHOT_API_KEY=...      # Moonshot / Kimi (OpenAI-compatible; judge/eval/target)
OLLAMA_BASE_URL=...       # optional; only for local Ollama-served models
```

The real `.env` is gitignored — never commit key values. AWS Bedrock uses the standard AWS credential chain (`AWS_PROFILE`), not a bearer key.

Non-Latin-script encoders and image rendering require Noto fonts under `fonts/` (gitignored).

---

## Running

```bash
python main.py test                   # smoke test end-to-end (~$0.01); verifies install + keys
python main.py <paper>/<preset>       # any conf/experiment/<paper>/<preset>.yaml
```

**Preset convention:** each experiment round is its own named preset under its paper dir (e.g. `conf/experiment/autoattack_defense/reguard_5guard.yaml`); retired presets carry a `HISTORICAL` header banner rather than being deleted, so provenance stays greppable.

### Cluster (SLURM)

Open-weight targets, guards, and judges are served as separate vLLM SLURM jobs by the orchestrator. Cluster profiles live in `conf/clusters/`; which cluster you are on is where the orchestrator process runs plus `CLUSTER_PROFILE`.

```bash
sbatch scripts/run_experiment.sbatch <paper>/<preset>       # default profile; keeps old logs
sbatch scripts/run_experiment_aicr.sbatch <paper>/<preset>  # AICR profile
sbatch scripts/run_experiment_xc.sbatch <paper>/<preset>    # xc profile (AWS box; Bedrock API-first)
```

### Multi-cluster dispatch

A single orchestrator run is single-cluster — every `sbatch`/`squeue` call is a local subprocess. To use more than one cluster, `dispatch.py` splits one preset's task matrix ahead of submission, writes one sub-preset per cluster under the same paper subdir, and submits each over ssh. **Dry-run by default:**

```bash
python dispatch.py <paper>/<preset>            # print the plan + ssh commands; submit nothing
python dispatch.py <paper>/<preset> --submit   # place + sbatch each sub-preset (sync code first)
```

The split key is the set of *cluster-served* models each task needs (target ∪ judge ∪ guard), so API judges drop out of the key. A cell is atomic — it runs on one cluster that serves all its models; a pipeline is never split. Pool order and per-cluster budgets live in `conf/cluster_pool.yaml` (gitignored; template at `conf/cluster_pool.example.yaml`).

### OCR fidelity probe (gate before image-channel runs)

```bash
sbatch temporary_scripts/ocr_probe.sbatch qwen2_5_vl_7b internvl3_8b pixtral_12b
```

Serves each VLM serially and transcribes sampled `ir_plain` images against the upstream encoded text — confirms the model can actually read the rendered attack before image-side cells are meaningful.

---

## Models

**Open-weight targets (cluster / vLLM):** `qwen2_5_vl_7b` (workhorse), `internvl3_8b` (`trust_remote_code`), `qwen3_vl_8b_instruct`, `pixtral_12b` (marginal OCR on the longest encodings), `llava_next`, `llama_3_3_70b_instruct`, `qwen2_5_7b_instruct`, `gemma2_9b_it`, `llama3_1_8b_cluster`. `llama3_2_11b_vision` serving is blocked by a vLLM/Mllama incompatibility — text-restrict or version-pin.

**API breadth:** `gpt-4o-mini`, `gpt-4.1-mini`, `gemini-2.5-pro`, `kimi-k2-instruct`, `deepseek-v3.2-exp`, `glm-4.5-air`, `qwen3-235b-a22b-instruct`, `command-a`, `hermes-4-70b`.

Per-model request/serving overrides live in `conf/llm/<model>.yaml`. Fine-tuned classifier checkpoints must set `chat_template: passthrough`, or the vLLM chat endpoint rejects every request.

Provider routing sits behind one unified call shape, `service.batch_chat(conversations, system_message, is_test)`:

| Provider | Strategy |
|---|---|
| OpenAI | realtime `AsyncOpenAI` + `asyncio.gather`, or native Batch API (50% cheaper) when the estimated job cost crosses the batch threshold (default $1) |
| Anthropic | realtime SDK fan-out, or native Message Batches API (50% cheaper) past the same threshold |
| Google | realtime, or native inline Batch API (50% cheaper) past the same threshold |
| SLURM cluster (vLLM) | `AsyncOpenAI` against the endpoint registered by the server manager; base64 `image_url` for image input |
| AWS Bedrock | boto3 `bedrock-runtime.converse` (Claude / Qwen / DeepSeek / Nova / …) |
| Local | Ollama-served models |

Model registry + pricing live in the pinned external package [`llm_utils`](https://github.com/vacantfury/llm_utils) (`llm_utils.llm_model::LLMModel`) — a git dependency, not vendored code.

---

## Project structure

```
conf/
├── experiment/<paper>/  # YAML task presets, namespaced per paper (one named preset per round)
├── llm/                 # per-model request/serving overrides
├── clusters/            # SLURM cluster profiles (nurc, aicr, xc)
├── text_encoding/       # encoder configs (set_theory, formal_logic, cipher, classical_language/, ...)
├── imaging/             # renderer configs (ir_plain, figstep, mm_typo, semantic_split, ...)
├── defense/             # sage, semantic_smooth, canonicalize(_guard), amia_ia, modality_complete
├── evaluation/          # judge LLM config (evaluator choice derives from the benchmark)
└── analysis/            # analysis-tool configs (guard-threshold sweep, ...)

src/
├── experiment/          # orchestrator (experiment.py), task dispatcher (task.py, 4 modes),
│                        #   judging.py, stage_rejudge.py, model_discovery.py,
│                        #   multi_cluster.py, Pydantic schemas, cluster_health.py
├── prompt_transformations/  # ONE unified registry: text/ encoders + image/ renderers
├── defense/             # all defenders incl. modality_complete (contribution) + shared guard_utils
├── evaluation/          # HarmBench / JBB / JBB-refusal / OR-Bench judges (+ WildGuard robustness lens)
├── analysis/            # ensemble ASR (portfolio.py), guard-threshold sweeps + logprob verification,
│                        #   paired stats (McNemar, bootstrap CIs), severity grading, middle-band and
│                        #   over-refusal decomposition, decode-fidelity, per-paper figure/table scripts
└── utils/               # logger, MLflow tracker, provenance helpers

dispatch.py              # multi-cluster preset split (dry-run by default)
scripts/*.sbatch         # SLURM submission wrappers (default / _aicr / _xc / rejudge variants)
text_docs/<paper>/       # per-paper proposal + experiments plan (+ shared/ for cross-paper material)
data/                    # prompt benchmarks (HarmBench, JBB, OR-Bench)
outputs/<paper>/         # experiment outputs (gitignored)
fonts/ · mlruns/         # fonts + MLflow tracking (gitignored)
```

### Pipeline modes

`src/experiment/task.py::run_task` dispatches on `task.mode` (a discriminated Pydantic union):

- **`prompt_transform`** — run a chain of transformation steps; one subfolder per step, each with a cumulative `results.json`. Input is a raw dataset JSONL or a prior step (so one encoding is shared across ablations rather than re-encoded).
- **`defense+evaluate`** — defense + target query + judging, fused into one mode.
- **`analyze`** — pure post-processing, no model or judge I/O; fans *in* from many `defense+evaluate` dirs (ensemble ASR, complementarity gap, paired stats).
- **`rejudge`** — re-score a stored run's saved responses with a different judge, without re-querying the target.

---

## Output layout

```
outputs/<paper>/<mode>/<benchmark>/<short_name>_<timestamp>_<rand>/
├── results.json         # config + metrics + primary_metric + git_sha + upstream_ref
├── prompts.jsonl        # per-prompt Prompt records (src/experiment/schemas.py)
├── raw_results.jsonl    # per-prompt response + judge_output + judge_reasoning + judge_raw_response
└── images/              # rendered image artifacts (image-variant tasks only)
```

Every `results.json` carries an `upstream_ref: {source_dir, results_sha256}` pointer, so any data point's full provenance is reconstructable and upstream drift is detectable by hash. The full judge audit trail is stored per prompt, so any judgment can be inspected — or re-judged with a different classifier — without re-querying the target.

---

## Tracking

Each task is an MLflow run (params, metrics, artifacts), local file store under `mlruns/`:

```bash
mlflow ui              # http://localhost:5000
```

Per-run target token/USD usage is recorded in `results.json`.

---

## Reproducibility notes

- **Pairing:** all variants in a (model, defense, encoding) cell share one canonical encoded text, encoded once and reused via `source_transform_subdir` references rather than re-encoded.
- **Empty-response handling:** the judge auto-classifies empty responses as refusals — correctly handling upstream API content-filtering on encodings a provider blocks at the API layer.
- **Schema versioning:** every `results.json` carries `schema_version`/`git_sha`/`git_dirty`; table builders filter on `schema_version` to exclude stray legacy dirs.
- **Judge integrity:** a silently-failing judge is the main threat to these numbers. A nonzero `fallback_parse_count` voids a cell; wall time far under expectation means the judge failed instantly; identical ASR across the undefended floor and a defended arm is a judge failure, not a result.
- **Renderer change:** image-side data use the **fixed-font paginated** renderer; older single-image (shrink-to-fit) renders are not directly comparable.
- **Ranges:** `prompt_range: [start, end]` is inclusive on both ends, 0-indexed, applied after loading.

---

## License

Code: MIT. Datasets: see the original HarmBench / JailbreakBench / OR-Bench licenses for the evaluation prompts.
