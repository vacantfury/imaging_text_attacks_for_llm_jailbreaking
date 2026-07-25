"""
Task runner for the destroyer-paper pipeline.

Modes:

  prompt_transform  — run a chain of PromptTransformations (attacks + image
                      renderers). Writes one subfolder per step under the
                      task output dir, each with its own cumulative
                      results.json.

  defense+evaluate  — defense + target-model query + judging, all in one
                      task. Consumes a specific subfolder from a
                      prompt_transform run.

  analyze           — pure post-processing over already-run results (no model
                      or judge I/O). Fans IN from many defense+evaluate dirs
                      and writes derived metrics (e.g. portfolio / best-of-all
                      ASR) under outputs/analyze/. See src/analysis/.
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from src.evaluation.evaluator_factory import EvaluatorFactory
from src.defense import create_defense
from src.experiment.config import load_conf as _load_conf
from src.experiment.schemas import (
    DefenseEvaluateResult, EvaluationRow, Prompt, PromptTransformResult,
    PromptTransformStepResult, RawPrompt, RejudgeResult, TargetModelConfig,
    TransformationSpec,
)
from llm_utils import LLMServiceFactory
from llm_utils.base_llm_service import is_mechanism_error, strip_mechanism_error
from llm_utils.llm_model import LLMModel
from src.prompt_transformations import (
    Modality, create_transformation, resolve_transformation_name,
)
from src.utils.experiment import get_new_experiment_data_dir
from src.utils.logger import get_logger
from src.utils.provenance import (
    judge_config_hash, provenance_fields, sha256_file, write_json_atomic,
    write_jsonl_atomic,
)

logger = get_logger(__name__)

# Max rendered pages (images) a single multimodal prompt may carry before it is
# excluded from the target query + ASR (is_within_maxlen=False) rather than
# truncated. A proxy for total content length, which is what actually drives
# vision-token usage against the served --max-model-len (20480 as of 2026-06-11;
# raised from 16384 to fit most code_attack ir_plain, but NOT to 32768 — that
# risks V100-32GB KV-cache OOM on Pixtral-12B). Any prompt that still overflows
# at query time is excluded via is_correctly_processed (not miscounted), so this
# page cap + the max-model-len are a best-effort reduction, not a guarantee.
# Tune down if the re-probe shows requests erroring below this page count.
# YAML home: conf/imaging/default.yaml `max_pages_per_prompt` (audit 2026-07-24);
# this constant is the fail-safe default when the YAML key is absent/unreadable.
MAX_PAGES_PER_PROMPT = 8


def _max_pages_per_prompt() -> int:
    """Resolve the page cap from conf/imaging/default.yaml, falling back to the
    module constant."""
    try:
        from src.experiment.config import load_conf
        return int(load_conf("imaging").get(
            "max_pages_per_prompt", MAX_PAGES_PER_PROMPT))
    except Exception:
        return MAX_PAGES_PER_PROMPT


# ======================== Shared helpers ========================


def _save_results(out_dir: Path, results: dict[str, Any]) -> None:
    write_json_atomic(out_dir / "results.json", results)
    logger.info(f"Saved results.json to {out_dir}")


def _load_results(source_dir: str) -> dict[str, Any]:
    path = Path(source_dir) / "results.json"
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def _load_prompts(source_dir: str) -> list[Prompt]:
    path = Path(source_dir) / "prompts.jsonl"
    out: list[Prompt] = []
    with open(path) as f:
        for line in f:
            if line.strip():
                out.append(Prompt.model_validate_json(line))
    return out


def _extract_companion_image_path(upstream: dict) -> Optional[str]:
    """First companion/decoy `image_path` anywhere in the upstream chain.

    Done once at write time so the decoy variant becomes a first-class field
    on results.json, instead of every reader walking
    `upstream.results_history[i].<step>.config.image_path`.
    """
    stack = [upstream]
    while stack:
        node = stack.pop()
        if not isinstance(node, dict):
            continue
        for rec in node.get("results_history", []) or []:
            if not isinstance(rec, dict):
                continue
            for step in rec.values():
                cfg = step.get("config", {}) if isinstance(step, dict) else {}
                if isinstance(cfg, dict) and cfg.get("image_path"):
                    return cfg["image_path"]
        if isinstance(node.get("upstream"), dict):
            stack.append(node["upstream"])
    return None


def _upstream_ref(source_dir) -> dict:
    """Lightweight provenance pointer to a consumed results.json.

    Replaces embedding the whole upstream dict (O(chain-depth) bloat + the
    embedded copy could drift from its source). Follow `source_dir` to
    reconstruct full provenance; `results_sha256` detects drift.
    """
    src = Path(source_dir)
    ref: dict = {"source_dir": str(src)}
    rp = src / "results.json"
    if rp.exists():
        ref["results_sha256"] = sha256_file(rp)
    return ref


def _apply_prompt_range(items: list, prompt_range: Optional[list[int]]) -> list:
    if not prompt_range or len(prompt_range) != 2:
        return items
    try:
        start, end = int(prompt_range[0]), int(prompt_range[1])
    except (ValueError, TypeError):
        return items
    start = max(0, start)
    end = min(len(items) - 1, end)
    if start > end:
        return items
    return items[start : end + 1]


# Benchmark inference (shared by stage 1 and stage 2).

BENCHMARK_ALIASES = {
    "jbb_benign": "jailbreakbench_benign",
    "jbb": "jailbreakbench",
    "orbench_benign_hard": "orbench_benign_hard",
    "orbench_benign_1k": "orbench_benign_1k",
    "orbench_harmful": "orbench_harmful",
}

KNOWN_BENCHMARKS = frozenset({
    "harmbench", "jailbreakbench", "jailbreakbench_benign",
    "orbench_harmful", "orbench_benign_hard", "orbench_benign_1k",
})


def _infer_benchmark(source_path: str) -> str:
    """Path/filename match against KNOWN_BENCHMARKS / BENCHMARK_ALIASES.

    Order:
      1. Canonical benchmark name as a path component (e.g. .../harmbench/...).
      2. Alias substring match (e.g. jbb_benign → jailbreakbench_benign).
      3. Canonical benchmark name as a filename substring (e.g.
         harmbench_prompts.jsonl → harmbench). Longest-match-first to ensure
         "jailbreakbench_benign" matches before "jailbreakbench".
    """
    parts = Path(source_path).parts
    for part in parts:
        if part in KNOWN_BENCHMARKS:
            return part
    name = str(source_path).lower()
    for alias, bench in sorted(BENCHMARK_ALIASES.items(), key=lambda x: -len(x[0])):
        if alias in name:
            return bench
    for bench in sorted(KNOWN_BENCHMARKS, key=len, reverse=True):
        if bench in name:
            return bench
    raise ValueError(
        f"Could not infer benchmark from path: {source_path!r}. "
        f"Set `benchmark:` explicitly in the task config or place the data "
        f"under a path containing one of {sorted(KNOWN_BENCHMARKS)}.")


# ======================== Judge orchestration ========================


def _resolve_evaluators(
    judge_method_override: Optional[str], benchmark: str,
    judge_model_override: Optional[str] = None,
) -> list:
    """Resolve the canonical evaluator list + bind the shared judge LLM."""
    eval_config = _load_conf("evaluation")
    judge_cfg = dict(eval_config.get("judge_llm_config", {}))
    default_model = judge_cfg.pop("model", "gpt-5-nano")
    judge_model_str = judge_model_override or default_model
    judge_model = LLMModel.from_string(judge_model_str)
    if judge_method_override:
        logger.warning(
            f"judge_method override active: '{judge_method_override}' "
            f"(bypassing canonical benchmark→evaluator mapping for {benchmark!r})")
        return [EvaluatorFactory.create(
            method=judge_method_override, model=judge_model, **judge_cfg)]
    return EvaluatorFactory.create_from_benchmark(
        benchmark, model=judge_model, **judge_cfg)


def _is_refusal_evaluator(evaluator) -> bool:
    from src.evaluation.evaluator_factory import REFUSAL_RATE_EVALUATORS
    return isinstance(evaluator, REFUSAL_RATE_EVALUATORS)


def _apply_verdict_columns(stage_rows: list, detailed_df, is_refusal: bool) -> None:
    if detailed_df is None:
        return

    def _col(df, name) -> dict:
        if name not in df.columns:
            return {}
        return dict(zip(df["id"].astype(str), df[name].astype(str)))

    verdict_col = "is_refused" if is_refusal else "is_jailbroken"
    if verdict_col not in detailed_df.columns:
        return
    verdict_by_id = dict(zip(detailed_df["id"].astype(str), detailed_df[verdict_col]))
    output_by_id = _col(detailed_df, "judge_output")
    reasoning_by_id = _col(detailed_df, "judge_reasoning")
    raw_by_id = _col(detailed_df, "judge_raw_response")

    if is_refusal:
        for row in stage_rows:
            row.refusal = verdict_by_id.get(row.id)
            row.refusal_judge_output = output_by_id.get(row.id)
            row.refusal_judge_reasoning = reasoning_by_id.get(row.id)
            row.refusal_judge_raw_response = raw_by_id.get(row.id)
    else:
        for row in stage_rows:
            row.asr = verdict_by_id.get(row.id)
            row.judge_output = output_by_id.get(row.id)
            row.judge_reasoning = reasoning_by_id.get(row.id)
            row.judge_raw_response = raw_by_id.get(row.id)


def _dropped_row_warnings(
    all_rows: list[EvaluationRow], within_rows: list[EvaluationRow],
    stage_label: str,
) -> list[str]:
    """Flag draws that never reached the judge, so a thinned denominator is loud.

    Rows whose model call failed are marked is_correctly_processed=False and dropped
    before judging, which silently shrinks the denominator: the reported rate is then
    computed over the SURVIVORS while `count` still says how many were intended. For a
    best-of-N attack that biases the union metric DOWNWARD -- fewer draws, fewer chances
    for any draw to succeed -- so a defense looks stronger than it is.

    This is not hypothetical. The 2026-07-24 Gemma recovery run lost 900/10000 draws per
    code cell to `prompt_tokens + max_tokens > max_model_len` 400s and still wrote
    `status: success, warnings: []` with ASR 0.00, because `_run_judging`'s own guard
    compares against the already-filtered list and saw 9100 == 9100.

    Returned strings land in the result's judge_errors -> `status: partial_judge`.
    """
    dropped = len(all_rows) - len(within_rows)
    if dropped <= 0:
        return []
    total = len(all_rows)
    over = sum(1 for r in all_rows if not r.is_within_maxlen)
    failed = sum(1 for r in all_rows if not r.is_correctly_processed)
    msg = (f"{dropped}/{total} rows ({dropped / total:.1%}) never reached the judge "
           f"({failed} failed model calls, {over} over length budget) — the reported "
           f"rate is computed over {len(within_rows)} surviving draws, not {total}")
    logger.error(f"[{stage_label}] THINNED DENOMINATOR — {msg}")
    return [msg]


def _run_judging(
    prompts: list[Prompt], all_rows: list[EvaluationRow], benchmark: str,
    judge_method_override: Optional[str], stage_label: str,
    judge_model_override: Optional[str] = None,
) -> dict:
    """Single-stage judging: runs every canonical evaluator on `all_rows`.

    NOTE: callers pass only the SURVIVING rows here (within-budget and correctly
    processed), so this function's own coverage guard can only see judging losses.
    Losses from failed model calls happen one level up and are caught by
    `_dropped_row_warnings` — see the comment there before changing either.

    Returns a dict: asr, refusal, eval_stats, judge_config_hash, judge_errors,
    metrics (every named scalar metric), primary_metric (the headline metric's
    name). asr/refusal are scalars or None if no judge of that type ran;
    non-empty judge_errors means metrics are incomplete (status "partial_judge").
    """
    evaluators = _resolve_evaluators(judge_method_override, benchmark, judge_model_override)
    asr: Optional[float] = None
    refusal: Optional[float] = None
    eval_stats: dict[str, dict] = {}
    metrics: dict[str, float] = {}
    judge_errors: list[str] = []

    original_lookup = {p.id: p.original for p in prompts}

    for evaluator in evaluators:
        is_refusal = _is_refusal_evaluator(evaluator)
        stat_key = "refusal_rate" if is_refusal else "attack_success_rate"
        try:
            judge_prompts = [
                {"id": r.id, "prompt": original_lookup.get(r.id, "")} for r in all_rows
            ]
            judge_processed = [original_lookup.get(r.id, "") for r in all_rows]
            judge_responses = {r.id: r.response for r in all_rows}
            detailed_df, stats = evaluator.evaluate(
                prompts=judge_prompts,
                processed_prompts=judge_processed,
                responses=judge_responses,
            )
            _apply_verdict_columns(all_rows, detailed_df, is_refusal)
            value = stats.get(stat_key, 0.0)

            # ---- coverage guard: never report a rate over rows we didn't judge ----
            # Every evaluator computes `rate = hits/total if total > 0 else 0.0`, so a
            # run whose responses ALL failed yields a confident-looking 0.00 that reads
            # as a perfect defense instead of a dead cell. That is not hypothetical:
            # round 174759's six Gemma-2-9B cells each shipped ASR 0.00 over 10000 draws
            # where every single target call had 400'd (max_tokens 16384 > max_model_len
            # 8192) and the judge scored the error strings as "not harmful"; the only
            # tell was total_evaluated=0 sitting next to count=10000 in the metadata.
            # A rate over zero rows is not a number — refuse to emit one.
            expected = len(all_rows)
            covered = stats.get("total_evaluated")
            if covered is not None and expected and covered != expected:
                msg = (f"{evaluator.__class__.__name__}: judged {covered}/{expected} "
                       f"responses ({covered / expected:.1%} coverage) — "
                       f"{stat_key} is computed over an incomplete set")
                judge_errors.append(msg)
                logger.error(f"[{stage_label}] COVERAGE FAILURE — {msg}")
                if covered == 0:
                    value = None

            if is_refusal:
                refusal = value
            else:
                asr = value
            eval_stats[evaluator.__class__.__name__] = stats
            # Record every scalar stat under its real name — no overloading.
            # When coverage collapsed to zero the rates are meaningless, so they are
            # kept OUT of `metrics` (and therefore out of primary_metric): the results
            # file then carries no headline number at all, which is the honest outcome.
            if value is not None:
                for k, v in stats.items():
                    if isinstance(v, (int, float)):
                        metrics[k] = float(v)
            logger.info(
                f"[{stage_label}] {evaluator.__class__.__name__}: "
                + (f"{stat_key}={value:.2f}%" if value is not None
                   else f"{stat_key}=UNAVAILABLE (0/{expected} responses judged)"))
        except (ValueError, KeyError, FileNotFoundError) as e:
            judge_errors.append(f"{evaluator.__class__.__name__}: skipped ({e})")
            logger.warning(
                f"Judge skipped for {evaluator.__class__.__name__}: {e}")
        except Exception as e:
            judge_errors.append(f"{evaluator.__class__.__name__}: failed ({e})")
            logger.warning(
                f"Judge failed for {evaluator.__class__.__name__}: {e}",
                exc_info=True)

    eval_cfg = _load_conf("evaluation").get("judge_llm_config", {})
    jhash = judge_config_hash(
        eval_cfg, [e.__class__.__name__ for e in evaluators])
    # Headline metric, named honestly (no benchmark-specific overloading):
    # direct_answer_rate (OR-Bench) > attack_success_rate > refusal_rate.
    primary_metric = next(
        (m for m in ("direct_answer_rate", "attack_success_rate", "refusal_rate")
         if m in metrics), None)
    return {
        "asr": asr, "refusal": refusal, "eval_stats": (eval_stats or None),
        "judge_config_hash": jhash, "judge_errors": judge_errors,
        "metrics": metrics, "primary_metric": primary_metric,
    }


# ======================== prompt_transform ========================


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_raw_prompts(path: str) -> list[RawPrompt]:
    out: list[RawPrompt] = []
    with open(path) as f:
        for line in f:
            if line.strip():
                out.append(RawPrompt.model_validate_json(line))
    return out


def _resolve_step_config(
    type_name: str, task_params: dict[str, Any],
) -> dict[str, Any]:
    """3-layer config merge for a single chain step.

    Legacy YAML files use the user-facing alias name (`set_theory.yaml`,
    `plain.yaml`), not the registry's canonical name (`llm_set_theory`,
    `ir_plain`). To bridge that, try the lookup with multiple candidate
    names per transformation:
        1. user-input `type_name` as-is (matches alias YAMLs)
        2. canonical type_name (matches the rare new YAMLs that use it)
        3. for `ir_*` renderers: also try the un-prefixed legacy name
           (`ir_plain` → `plain.yaml`)

    Only uses a YAML if it actually exists. Falls through to bare task_params
    for new transformations (deep_inception, code_attack, ECSO defenses)
    that have no YAML defaults — avoids polluting the wrapper with unrelated
    subsystem defaults.

    Classical-language configs live one level deeper
    (conf/text_encoding/classical_language/<lang>.yaml); they merge as
    default.yaml → <lang>.yaml → task_params, so encoder defaults like
    `model:` apply without every task passing them explicitly.
    """
    from src.experiment.config import CONF_DIR, _deep_merge, _load_yaml

    canonical, _ = resolve_transformation_name(type_name)
    is_image = canonical.startswith("ir_")

    candidates: list[str] = [type_name]
    if canonical not in candidates:
        candidates.append(canonical)
    if is_image and canonical.startswith("ir_"):
        unprefixed = canonical[len("ir_"):]
        if unprefixed not in candidates:
            candidates.append(unprefixed)

    subsystem = "imaging" if is_image else "text_encoding"

    for name in candidates:
        if (CONF_DIR / subsystem / f"{name}.yaml").exists():
            return _load_conf(
                subsystem, override_name=name,
                task_overrides=task_params or None,
            )

    if canonical == "llm_classical_language":
        lang = type_name[:-len("_literary")] if type_name.endswith("_literary") else type_name
        deep_path = CONF_DIR / subsystem / "classical_language" / f"{lang}.yaml"
        if deep_path.exists():
            merged = _load_conf(subsystem)          # text_encoding/default.yaml
            merged = _deep_merge(merged, _load_yaml(deep_path))
            if task_params:
                merged = _deep_merge(merged, task_params)
            return merged

    return dict(task_params or {})


def _run_prompt_transform(task) -> dict[str, Any]:
    """Stage 1: run a chain of PromptTransformations.

    Each step in task.transformation_list runs in order:
      - resolves config (3-layer YAML merge + task overrides)
      - instantiates the transformation via the factory
      - validates modality consistency vs. cumulative chain state
      - creates a subfolder named after type_name
      - applies the transformation (writes its own artifacts into the subfolder)
      - persists prompts.jsonl + cumulative results.json into that subfolder

    Input prompts come from either:
      - `task.source_file` — a raw dataset JSONL (chain starts fresh), OR
      - `task.source_transform_subdir` — a prior step subfolder (chain
        continues from that step; lets multiple downstream chains share an
        identical encoder output, avoiding LLM-encoder nondeterminism in
        paired ablations).
    """
    t_chain_start = time.time()

    upstream: dict = {}
    upstream_chain_names: list[str] = []
    if task.source_transform_subdir:
        source_dir = Path(task.source_transform_subdir)
        if not source_dir.exists():
            raise FileNotFoundError(
                f"source_transform_subdir does not exist: {source_dir}")
        upstream = _load_results(str(source_dir))
        if not upstream:
            raise ValueError(
                f"source_transform_subdir missing results.json: {source_dir}")
        is_multimodal = bool(upstream.get("is_multimodal", False))
        benchmark = (
            task.benchmark
            or upstream.get("benchmark")
            or _infer_benchmark(str(source_dir)))
        upstream_chain_names = list(upstream.get("transformation_list", []))
        dataset_path = upstream.get("dataset_path", "")
        prompts = _load_prompts(str(source_dir))
        prompts = _apply_prompt_range(prompts, task.prompt_range)
        logger.info(
            f"prompt_transform chaining from {source_dir} "
            f"(n_prompts={len(prompts)}, is_multimodal={is_multimodal}, "
            f"upstream_chain={'+'.join(upstream_chain_names)})")
    else:
        benchmark = task.benchmark or _infer_benchmark(task.source_file)
        dataset_path = task.source_file
        raw = _load_raw_prompts(task.source_file)
        raw = _apply_prompt_range(raw, task.prompt_range)
        logger.info(f"Loaded {len(raw)} raw prompts from {task.source_file}")
        prompts: list[Prompt] = [
            Prompt(id=r.id, encoding="", original=r.prompt, encoded=r.prompt)
            for r in raw
        ]
        is_multimodal = False

    new_chain_label = "_".join(
        s.type if isinstance(s, TransformationSpec) else s["type"]
        for s in task.transformation_list
    )
    full_chain_label = (
        "_".join(upstream_chain_names) + "_" + new_chain_label
        if upstream_chain_names else new_chain_label
    )[:80]
    task_dir = Path(get_new_experiment_data_dir(
        "outputs/prompt_transform", dataset=benchmark, model=full_chain_label,
    ))
    logger.info(f"prompt_transform task_dir: {task_dir}")

    transformation_list_names: list[str] = []
    results_history: list[dict[str, PromptTransformStepResult]] = []

    # Pre-construct all transformations so config errors (missing files, bad
    # params) raise BEFORE any expensive earlier step runs. The discarded
    # instances are cheap — only renderer __init__ I/O.
    for _pre_spec in task.transformation_list:
        _pre_type = (
            _pre_spec.type if isinstance(_pre_spec, TransformationSpec)
            else _pre_spec["type"])
        _pre_params = (
            _pre_spec.params if isinstance(_pre_spec, TransformationSpec)
            else _pre_spec.get("params", {}))
        create_transformation(_pre_type, **_resolve_step_config(_pre_type, _pre_params))

    for step_spec in task.transformation_list:
        step_type = (
            step_spec.type if isinstance(step_spec, TransformationSpec)
            else step_spec["type"])
        step_params = (
            step_spec.params if isinstance(step_spec, TransformationSpec)
            else step_spec.get("params", {}))

        merged_config = _resolve_step_config(step_type, step_params)
        transformation = create_transformation(step_type, **merged_config)
        type_name = transformation.type_name

        # Modality validation: can't run a text-only transformation after a
        # multimodal one (no way to "untransform" image back to text).
        if (transformation.input_modality == Modality.TEXT
                and is_multimodal):
            raise ValueError(
                f"Chain ordering invalid: step {type_name!r} expects text "
                f"input, but chain is already multimodal after previous "
                f"step(s). Reorder so image transformations come last.")

        step_dir = task_dir / type_name
        step_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Applying step: {type_name} ({len(prompts)} prompts)")
        t_step_start = time.time()
        prompts = transformation.apply(prompts, step_dir)
        elapsed_step = round(time.time() - t_step_start, 2)

        write_jsonl_atomic(
            step_dir / "prompts.jsonl",
            [p.model_dump_json() for p in prompts])

        if transformation.output_modality == Modality.MULTIMODAL:
            is_multimodal = True
        transformation_list_names.append(type_name)

        step_metrics = transformation.step_metrics()
        step_record = PromptTransformStepResult(
            config=transformation.get_config(),
            metrics=step_metrics,
            prompts_file="prompts.jsonl",
            images_dir=step_metrics.get("images_dir"),
            is_multimodal_after=is_multimodal,
            elapsed_seconds=elapsed_step,
            usage=transformation.get_usage(),
        )
        results_history.append({type_name: step_record})

        result = PromptTransformResult(
            task_id=task_dir.name,
            benchmark=benchmark,
            prompt_range=task.prompt_range,
            dataset_path=dataset_path,
            is_multimodal=is_multimodal,
            total_steps=len(upstream_chain_names) + len(results_history),
            latest_step=type_name,
            latest_step_dir=type_name,
            task_dir=str(task_dir),
            timestamp_last_step=_now_iso(),
            elapsed_seconds_total=round(time.time() - t_chain_start, 2),
            count=len(prompts),
            transformation_list=upstream_chain_names + transformation_list_names,
            results_history=results_history,
            upstream_ref=(
                _upstream_ref(task.source_transform_subdir)
                if task.source_transform_subdir else None),
            **provenance_fields(),
        )
        write_json_atomic(
            step_dir / "results.json",
            result.model_dump(exclude_none=True))
        logger.info(
            f"Step {type_name} done in {elapsed_step}s "
            f"(is_multimodal={is_multimodal})")

    latest_dir = task_dir / transformation_list_names[-1]
    return {
        "status": "success",
        "output_dir": str(latest_dir),
        "task_dir": str(task_dir),
        "transformation_list": transformation_list_names,
        "count": len(prompts),
        "is_multimodal": is_multimodal,
        "elapsed_seconds": round(time.time() - t_chain_start, 2),
    }


# ======================== defense+evaluate ========================


def _run_defense_evaluate(task) -> dict[str, Any]:
    """Stage 2: defense + target-model query + judging.

    Consumes a specific prompt_transform step subfolder pointed at by
    task.source_transform_subdir. Reads prompts.jsonl + the upstream
    PromptTransformResult to know is_multimodal, encoding, benchmark.
    """
    t0 = time.time()

    source_dir = Path(task.source_transform_subdir)
    if not source_dir.exists():
        raise FileNotFoundError(
            f"source_transform_subdir does not exist: {source_dir}")
    upstream = _load_results(str(source_dir))
    if not upstream:
        raise ValueError(
            f"source_transform_subdir is missing results.json: {source_dir}")

    is_multimodal = bool(upstream.get("is_multimodal", False))
    transformation_list = list(upstream.get("transformation_list") or [])
    encoding = upstream.get("latest_step") or (transformation_list[-1] if transformation_list else None)
    benchmark = task.benchmark or upstream.get("benchmark") or _infer_benchmark(str(source_dir))

    prompts = _load_prompts(str(source_dir))
    prompts = _apply_prompt_range(prompts, task.prompt_range)
    logger.info(
        f"defense+evaluate: defense={task.defense}, model={task.target_model}, "
        f"source={source_dir}, n_prompts={len(prompts)}, is_multimodal={is_multimodal}")

    # Output dir: outputs/defense+evaluate/<benchmark>/<model>_<defense>_<chain_label>_<ts>_<rand>/
    chain_label = "_".join(upstream.get("transformation_list", []))[:60]
    out_dir = Path(get_new_experiment_data_dir(
        "outputs/defense+evaluate", dataset=benchmark,
        model=f"{task.target_model}_{task.defense}_{chain_label}",
    ))

    # Create defense + target service.
    # 3-layer defense config merge:
    #   conf/defense/default.yaml → conf/defense/<defense>.yaml → task.defense_config
    # This makes conf/defense/<defense>.yaml the source of truth for each
    # defense's hyperparameters (e.g. SS's perturbation_model + temperature),
    # consistent with how text_encoding/imaging configs are loaded.
    try:
        merged_defense_config = _load_conf(
            "defense", override_name=task.defense,
            task_overrides=task.defense_config or None,
        )
    except FileNotFoundError:
        # No per-defense yaml exists → fall back to task.defense_config only.
        merged_defense_config = dict(task.defense_config or {})
    defense = create_defense(task.defense, **merged_defense_config)
    target_service = LLMServiceFactory.create(task.target_model)
    target_llm = LLMModel.from_string(task.target_model)
    target_model_config = LLMServiceFactory._load_model_defaults(target_llm)

    # Multi-image overflow guard: a paginated prompt can render to many images
    # and exceed the served context budget. Rather than drop pages (which
    # mutilates the attack and fakes a refusal), EXCLUDE over-budget prompts
    # from the query AND from ASR, and flag them (is_within_maxlen=False) so the
    # coverage loss is recorded honestly instead of silently degraded.
    def _num_images(p) -> int:
        return len(p.image_encoded) if p.image_encoded else 0

    max_pages = _max_pages_per_prompt()
    if is_multimodal:
        within = [p for p in prompts if _num_images(p) <= max_pages]
        over = [p for p in prompts if _num_images(p) > max_pages]
    else:
        within, over = list(prompts), []
    if over:
        logger.warning(
            f"{len(over)}/{len(prompts)} prompts exceed "
            f"max_pages_per_prompt={max_pages} — excluded from "
            f"query+ASR (is_within_maxlen=False): {[p.id for p in over][:10]}")

    # Run defense on within-budget prompts only.
    pairs = defense.query(
        prompts=within,
        target_service=target_service,
        is_multimodal=is_multimodal,
        source_dir=source_dir,
        system_message=task.system_message,
    )

    # Build EvaluationRow list with synthetic prompt_stage. num_images is
    # recorded for every prompt; over-budget rows carry an empty response and
    # is_within_maxlen=False, and are NOT judged. Rows whose target response is a
    # mechanism-error sentinel (the call failed to produce a valid output:
    # query-time context-overflow, network, timeout, rate-limit, failed batch
    # item) are flagged is_correctly_processed=False and likewise excluded from
    # judging/ASR — an untestable prompt must not count as a defeated attack. A
    # refusal is a *successful* call, so it stays is_correctly_processed=True.
    stage_label = f"{encoding}__{task.defense}" if encoding else task.defense
    npages_by_id = {p.id: _num_images(p) for p in prompts}
    all_rows: list[EvaluationRow] = []
    n_mechanism_err = 0
    for pid, resp in pairs:
        failed = is_mechanism_error(resp)
        if failed:
            n_mechanism_err += 1
        all_rows.append(EvaluationRow(
            id=pid, prompt_stage=stage_label,
            response=strip_mechanism_error(resp), asr=None,
            num_images=npages_by_id.get(pid, 0),
            is_within_maxlen=True, is_correctly_processed=not failed))
    if n_mechanism_err:
        logger.warning(
            f"{n_mechanism_err}/{len(pairs)} prompts hit a mechanism error "
            f"(is_correctly_processed=False) — excluded from query+ASR.")
    all_rows += [
        EvaluationRow(id=p.id, prompt_stage=stage_label, response="", asr=None,
                      num_images=_num_images(p), is_within_maxlen=False)
        for p in over
    ]

    # Write raw_results.jsonl (raw model responses preserved so judging can
    # be re-run later with a different judge config if needed).
    write_jsonl_atomic(
        out_dir / "raw_results.jsonl",
        [row.model_dump_json() for row in all_rows])

    # Judge only rows that were both within budget AND correctly processed
    # (over-budget and mechanism-error rows are excluded from ASR). Filtering
    # keeps object references, so verdict columns still land back in all_rows.
    within_rows = [
        r for r in all_rows if r.is_within_maxlen and r.is_correctly_processed]
    judged = _run_judging(
        prompts=within, all_rows=within_rows, benchmark=benchmark,
        judge_method_override=task.judge_method, stage_label=stage_label,
        judge_model_override=task.judge_model,
    )
    asr, refusal = judged["asr"], judged["refusal"]
    eval_stats, jhash, judge_errors = (
        judged["eval_stats"], judged["judge_config_hash"], judged["judge_errors"])
    judge_errors = list(judge_errors) + _dropped_row_warnings(
        all_rows, within_rows, stage_label)
    judge_method_provenance = task.judge_method or benchmark
    # Record the judge that ACTUALLY scored. A self-contained classifier judge
    # (e.g. wildguard) IS the judge — recording the vestigial config-default LLM
    # there falsely claims e.g. gpt-5-nano ran. An LLM-rubric judge uses the judge
    # LLM, so record the per-task override or the evaluation default.
    from src.evaluation.evaluator_factory import SELF_CONTAINED_JUDGE_METHODS
    if task.judge_method in SELF_CONTAINED_JUDGE_METHODS:
        judge_model_used = task.judge_method
    else:
        judge_model_used = task.judge_model or _load_conf("evaluation").get(
            "judge_llm_config", {}).get("model")

    # Overwrite raw_results.jsonl now that verdict columns are filled.
    write_jsonl_atomic(
        out_dir / "raw_results.jsonl",
        [row.model_dump_json() for row in all_rows])

    elapsed = round(time.time() - t0, 2)

    result = DefenseEvaluateResult(
        source_transform_subdir=str(source_dir),
        campaign=task.campaign,
        upstream_ref=_upstream_ref(source_dir),
        is_multimodal=is_multimodal,
        defense=task.defense,
        defense_config=task.defense_config or {},
        target_model=task.target_model,
        target_model_config=TargetModelConfig(**target_model_config),
        model_family=target_llm.family,
        alignment_tier=target_llm.alignment_tier,
        system_message=task.system_message,
        benchmark=benchmark,
        encoding=encoding,
        transformation_list=transformation_list,
        companion_image_path=_extract_companion_image_path(upstream),
        prompt_range=task.prompt_range,
        judge_method=judge_method_provenance,
        judge_model=judge_model_used,
        count=len(all_rows),
        asr=asr,
        refusal_rate=refusal,
        metrics=judged["metrics"],
        primary_metric=judged["primary_metric"],
        eval_stats=eval_stats,
        target_usage=target_service.get_usage(),
        defense_usage=defense.get_usage(),
        elapsed_seconds=elapsed,
        output_dir=str(out_dir),
        **provenance_fields(),
        judge_config_hash=jhash,
        status="success" if not judge_errors else "partial_judge",
        warnings=judge_errors,
    )
    _save_results(out_dir, result.model_dump(exclude_none=True))

    return {
        "status": "success",
        "output_dir": str(out_dir),
        "count": len(all_rows),
        "defense": task.defense,
        "target_model": task.target_model,
        "encoding": encoding,
        "judge_method": judge_method_provenance,
        "asr": asr,
        "refusal_rate": refusal,
        "usage": result.target_usage,
        "elapsed_seconds": elapsed,
    }


# ======================== analyze ========================


def _run_analyze(task) -> dict[str, Any]:
    """`analyze` mode: pure post-processing over already-run results — no
    target/judge calls. Delegates to src/analysis (dispatched by task.analysis).
    """
    from src.analysis import run_analysis
    return run_analysis(task)


# ======================== rejudge ========================


def _load_eval_rows(path: Path) -> list[EvaluationRow]:
    """Load the per-response rows a prior defense+evaluate run wrote to
    raw_results.jsonl (target responses preserved for exactly this purpose)."""
    out: list[EvaluationRow] = []
    with open(path) as f:
        for line in f:
            if line.strip():
                out.append(EvaluationRow.model_validate_json(line))
    return out


def _run_rejudge(task) -> dict[str, Any]:
    """`rejudge` mode: re-score a stored defense+evaluate dir's saved responses
    with a new judge, WITHOUT re-querying the target.

    Reads `task.responses_from`'s raw_results.jsonl, pulls the harmful-behavior
    originals from the transform step that run consumed, runs ONLY the judging
    step with `task.judge_model` (+ optional `task.judge_method`), and writes a
    fresh result dir under outputs/<paper>/rejudge/. The source dir is untouched,
    so historical (e.g. gpt-5-nano) numbers are preserved alongside the new ones.
    """
    t0 = time.time()

    src = Path(task.responses_from)
    if not src.exists():
        raise FileNotFoundError(f"responses_from does not exist: {src}")
    source = _load_results(str(src))
    if not source:
        raise ValueError(f"responses_from is missing results.json: {src}")
    raw_path = src / "raw_results.jsonl"
    if not raw_path.exists():
        raise FileNotFoundError(f"responses_from is missing raw_results.jsonl: {src}")

    rows = _load_eval_rows(raw_path)

    # Originals (the harmful behavior the judge scores against) come from the
    # transform step this defense+evaluate run consumed.
    transform_subdir = source.get("source_transform_subdir")
    if not transform_subdir or not Path(transform_subdir).exists():
        raise FileNotFoundError(
            f"rejudge needs the source transform dir for originals, but "
            f"source_transform_subdir={transform_subdir!r} is missing "
            f"(recorded in {src}/results.json)")
    prompts = _load_prompts(transform_subdir)

    benchmark = task.benchmark or source.get("benchmark") or _infer_benchmark(str(src))
    target_model = source.get("target_model")
    defense = source.get("defense")
    encoding = source.get("encoding")

    # Judge exactly the rows the original run judged: within budget AND correctly
    # processed. _run_judging fills fresh verdict columns back into these rows.
    within_rows = [r for r in rows if r.is_within_maxlen and r.is_correctly_processed]
    stage_label = f"rejudge[{task.judge_model}]__{encoding or defense or 'na'}"
    logger.info(
        f"rejudge: judge={task.judge_model} "
        f"(method={task.judge_method or benchmark}), source={src}, "
        f"n_rows={len(within_rows)}/{len(rows)}")
    judged = _run_judging(
        prompts=prompts, all_rows=within_rows, benchmark=benchmark,
        judge_method_override=task.judge_method, stage_label=stage_label,
        judge_model_override=task.judge_model,
    )
    judged["judge_errors"] = list(judged["judge_errors"]) + _dropped_row_warnings(
        rows, within_rows, stage_label)

    out_dir = Path(get_new_experiment_data_dir(
        "outputs/rejudge", dataset=benchmark,
        model=f"{target_model}_{defense}_{task.judge_model}",
    ))
    # Persist rejudged rows: within-budget rows now carry fresh verdicts; the
    # excluded (over-budget / mechanism-error) rows are written back unchanged.
    write_jsonl_atomic(
        out_dir / "raw_results.jsonl", [row.model_dump_json() for row in rows])

    elapsed = round(time.time() - t0, 2)
    result = RejudgeResult(
        rejudge_of=str(src),
        upstream_ref=_upstream_ref(src),
        # Inherit the source run's campaign so rejudge results are self-describing
        # (which round each cell came from) without re-reading the source.
        campaign=task.campaign or source.get("campaign"),
        target_model=target_model,
        defense=defense,
        is_multimodal=bool(source.get("is_multimodal", False)),
        benchmark=benchmark,
        encoding=encoding,
        transformation_list=list(source.get("transformation_list") or []),
        prompt_range=task.prompt_range,
        judge_model=task.judge_model,
        judge_method=task.judge_method or benchmark,
        count=len(rows),
        asr=judged["asr"],
        refusal_rate=judged["refusal"],
        metrics=judged["metrics"],
        primary_metric=judged["primary_metric"],
        eval_stats=judged["eval_stats"],
        judge_config_hash=judged["judge_config_hash"],
        elapsed_seconds=elapsed,
        output_dir=str(out_dir),
        status="success" if not judged["judge_errors"] else "partial_judge",
        warnings=judged["judge_errors"],
        **provenance_fields(),
    )
    _save_results(out_dir, result.model_dump(exclude_none=True))

    return {
        "status": "success",
        "output_dir": str(out_dir),
        "count": len(rows),
        "rejudge_of": str(src),
        "judge_model": task.judge_model,
        "target_model": target_model,
        "defense": defense,
        "encoding": encoding,
        "asr": judged["asr"],
        "refusal_rate": judged["refusal"],
        "elapsed_seconds": elapsed,
    }


# ======================== Dispatcher ========================


TASK_MODES = {
    "prompt_transform": _run_prompt_transform,
    "defense+evaluate": _run_defense_evaluate,
    "analyze": _run_analyze,
    "rejudge": _run_rejudge,
}


def run_task(task) -> dict[str, Any]:
    """Run a task — dispatched by `task.mode`. Wires MLflow tracking."""
    from src.utils.mlflow_tracker import MLflowTracker  # lazy import
    from .schemas import (
        DefenseEvaluateTask, PromptTransformTask, TaskConfig,
    )

    # Accept legacy dict input.
    if isinstance(task, dict):
        from pydantic import TypeAdapter
        task = TypeAdapter(TaskConfig).validate_python(task)

    mode = task.mode
    if mode not in TASK_MODES:
        raise ValueError(f"Unknown mode {mode!r}. Valid: {list(TASK_MODES)}")

    # MLflow tags.
    model_tag = ""
    encoding_tag = ""
    modality_tag = ""
    if isinstance(task, DefenseEvaluateTask):
        model_tag = task.target_model
        encoding_tag = task.defense
    elif isinstance(task, PromptTransformTask):
        from .schemas import TransformationSpec
        chain_types = [
            s.type if isinstance(s, TransformationSpec) else s["type"]
            for s in task.transformation_list
        ]
        encoding_tag = ",".join(chain_types)
        modality_tag = chain_types[-1] if chain_types else ""

    tracker = MLflowTracker()
    tracker.start_run(
        mode=mode, encoding=encoding_tag, model=model_tag, modality=modality_tag,
    )
    tracker.log_params(task.model_dump(exclude_none=True))

    try:
        result = TASK_MODES[mode](task)
        tracker.log_metrics(result)

        out_dir = result.get("output_dir")
        if out_dir:
            out_path = Path(out_dir)
            # Stamp mlflow_run_id into results.json for cross-ref.
            results_file = out_path / "results.json"
            if results_file.exists():
                with open(results_file) as f:
                    data = json.load(f)
                data["mlflow_run_id"] = tracker.run_id
                write_json_atomic(results_file, data)

            # MLflow is an index, not a second copy of the data: point at the
            # canonical output dir on disk instead of mirroring artifacts.
            tracker.log_output_dir(out_dir)

        return result
    except Exception:
        tracker.log_metrics({"status_failed": 1})
        raise
    finally:
        tracker.end_run()
