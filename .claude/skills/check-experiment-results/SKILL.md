---
name: check-experiment-results
description: Triage a completed (or failed) experiment run for this repo. Walks logs → cleanup → result correctness → spot-check raw outputs → bad-logic detection → update experiment_results.md → discuss findings. The user wants a *collaborative* triage: many steps end with "wait for the user" — never run destructive commands and never edit experiment_results.md without an explicit go-ahead.
---

# Check Experiment Results

Use this when the user says "check experiment results", "check the latest job", "triage mj_<id>", or otherwise asks you to review a SLURM run or a batch of experiment folders.

## Operating principles

- **You propose, the user disposes.** All deletions, code fixes, and writes to `text_docs/experiment_results.md` require explicit user approval. Print the command/diff and stop.
- **Stop at the wait points.** Several steps below say *WAIT FOR USER*. That means: post your findings, ask the targeted question, and stop emitting tool calls until the user replies.
- **One pass per invocation.** Don't loop back to step 1 after step 8 unless the user asks for another run.

## Inputs to identify first

Before starting, figure out:
1. **Which job?** Latest `logs/mj_*.out` / `.err` pair by mtime, or a specific `mj_<id>` the user named.
2. **Which experiment folders does this job own?** Cross-reference the `.out` log timestamps with `outputs/<mode>/<benchmark>/*` mtimes (the run timestamp is also embedded in the folder name, e.g. `..._20260519_055518_82362539`).

If either is ambiguous, ask the user before proceeding.

---

## Step 1 — Scan logs for errors

```bash
ls -lt logs/ | head
# pick the relevant mj_<id>.{out,err} pair, then:
tail -200 logs/mj_<id>.err
grep -niE "error|exception|traceback|timeout|failed|killed" logs/mj_<id>.out logs/mj_<id>.err | head -50
```

Classify each error as:
- **Infrastructure** (SLURM OOM, node failure, vLLM startup timeout, batch-API timeout for Anthropic/Google) — folders are likely incomplete, candidates for cleanup.
- **Code bug** (Python traceback, schema validation, JSON decode) — folders may be partial; need user discussion before fixing.
- **API refusal/safety** (Google "content flagged", OpenAI account restriction) — not a bug; record but don't delete unless user says so.
- **Benign warnings** (deprecation, retry-then-succeed) — ignore.

Output a short table: `error_class | count | sample_message | suspected_folders`.

**If errors exist → go to Step 2. If clean → skip to Step 4.**

---

## Step 2 — Propose cleanup commands (DO NOT RUN)

The repo's helper is `scripts/cleanup_failed.py` — prefer it over manual `rm -rf`.

```bash
# dry-run first, scoped to recent activity if the job is fresh
python scripts/cleanup_failed.py --recent 1d
# then user-approved delete
python scripts/cleanup_failed.py --recent 1d --delete
```

For folders that have `results.json` but are still invalid (judge bug, wrong config, etc.) — `cleanup_failed.py` will NOT catch them. Print explicit `rm -rf` commands per folder, grouped by reason. Also print the matching `mlruns/<exp_id>/<run_id>` paths (read `mlflow_run_id` from each `results.json`).

**WAIT FOR USER** — do not execute deletions.

---

## Step 3 — Discuss code bugs (if any)

For each code-level error: post the file:line, the exception, your one-paragraph hypothesis of root cause, and the minimal fix you'd propose. Do not start editing.

**WAIT FOR USER** — they'll say "go ahead", "different approach", or "skip for now".

---

## Step 4 — Result correctness check

For every successful folder owned by this job:

```bash
# Quick scan: extract the headline metric from each results.json
find outputs/<mode>/<benchmark> -name results.json -newer logs/mj_<id>.out \
  -exec sh -c 'echo "=== $1 ==="; python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print({k:d.get(k) for k in [\"attack_success_rate\",\"refusal_rate\",\"total_rows\",\"target_model\",\"encoding_name\",\"prompt_stages\"]})" "$1"' _ {} \;
```

Sanity rules (project-specific, based on `text_docs/experiment_results.md` patterns):
- `text_original` ASR on JBB harmful is normally **3–20%** depending on model. >40% → suspicious unless it's OR-Bench.
- `image_original` ASR is normally **0–7%**. Higher → check whether the image renderer was bypassed.
- ASR exactly **0%** on `text_encoded` with a frontier model is suspicious — could be the empty-response judge bug recurring (see P12b/P15 corrections in experiment_results.md).
- `total_rows` should equal the configured `prompt_range` span. Mismatches mean partial completion.

**If everything looks reasonable → skip to Step 7.**

---

## Step 5 — Spot-check `raw_results.jsonl` for outliers

For any folder flagged in Step 4:

```bash
# inspect a few rows
head -3 outputs/<mode>/<benchmark>/<folder>/raw_results.jsonl | python3 -m json.tool
# specifically check empty responses (the May 8 bug pattern)
python3 -c "
import json
rows = [json.loads(l) for l in open('outputs/<mode>/<benchmark>/<folder>/raw_results.jsonl')]
empty = [r for r in rows if not (r.get('response') or '').strip()]
print(f'{len(empty)}/{len(rows)} empty responses')
print(f'Empty marked harmful: {sum(1 for r in empty if r.get(\"is_harmful\") or r.get(\"label\")==\"unsafe\")}')
"
```

Look for: empty responses misclassified as unsafe, judge LLM errors, truncated generations, refused-but-marked-success patterns.

---

## Step 6 — Identify problematic logic & list folders to delete (DO NOT RUN)

For each folder whose *logic* is wrong (not just incomplete), output:
- Folder path
- Why it's wrong (one sentence)
- The `mlruns/.../<run_id>` to delete alongside it
- The proposed `rm -rf` command

Then describe the suspected bug in the pipeline code (file:line if you can pinpoint it). **WAIT FOR USER** before either deleting or editing code.

---

## Step 7 — Append correct results to `experiment_results.md`

Only after Steps 1–6 are resolved (errors handled, bad folders flagged). Match the existing structure exactly:

- New experiment block goes under the next `## P<N>:` heading. Read the current max P-number first.
- Use the same table columns as the nearest comparable section (P7c-style for HarmBench, P9-style for OR-Bench, etc.).
- Include: model, encoding, all available `prompt_stages` ASRs, `Δ (img−txt enc)` if both present, judge, rows, experiment dir (basename only).
- Add a brief "Key findings" subsection if there's something notable (defense effect direction, baseline shift, anomaly).
- Update the "Total evaluations" counter at the bottom.

Show the user the diff (or the new section as a code block) **before** writing — wait for approval, then `Edit`.

---

## Step 8 — Discuss findings

Post a 3–6 bullet summary:
- What this run confirms or contradicts vs. existing P-sections.
- Any new direction this suggests (new encodings to try, defense gaps, model-specific anomalies).
- Open questions for the user.

**WAIT FOR USER** — they'll steer the next experiment from here.

---

## Quick reference — repo conventions

- Output layout: `outputs/<mode>/<benchmark>/<shortname>_<timestamp>_<rand>/results.json`
- Modes: `text_encode`, `defense_transform`, `imaging`, `evaluate`, `defense`
- Benchmarks: `jailbreakbench`, `jailbreakbench_benign`, `harmbench`, `orbench_harmful`, `orbench`
- Each `results.json` contains `mlflow_run_id` → maps to `mlruns/<exp_id>/<run_id>/`
- SLURM log naming: `mj_<jobid>.out` / `mj_<jobid>.err` (sbatch script: `scripts/run_experiment.sbatch`)
- Known judge bug history: empty Claude responses → use the empty-response-safe logic already in evaluators (`src/evaluation/*`); if results predate May 8, suspect this bug.
