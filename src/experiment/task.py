"""
Task runner for the destroyer-paper pipeline.

Two modes only:

  prompt_transform  — run a chain of PromptTransformations (attacks + image
                      renderers). Writes one subfolder per step under the
                      task output dir, each with its own cumulative
                      results.json.

  defense+evaluate  — defense + target-model query + judging, all in one
                      task. Consumes a specific subfolder from a
                      prompt_transform run.
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
    PromptTransformStepResult, RawPrompt, TargetModelConfig,
    TransformationSpec,
)
from src.llm_utils import LLMServiceFactory
from src.llm_utils.llm_model import LLMModel
from src.prompt_transformations import (
    Modality, create_transformation, resolve_transformation_name,
)
from src.utils.experiment import get_new_experiment_data_dir
from src.utils.logger import get_logger
from src.utils.provenance import (
    judge_config_hash, provenance_fields, write_json_atomic, write_jsonl_atomic,
)

logger = get_logger(__name__)


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
) -> list:
    """Resolve the canonical evaluator list + bind the shared judge LLM."""
    eval_config = _load_conf("evaluation")
    judge_cfg = dict(eval_config.get("judge_llm_config", {}))
    judge_model_str = judge_cfg.pop("model", "gpt-5-nano")
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


def _run_judging(
    prompts: list[Prompt], all_rows: list[EvaluationRow], benchmark: str,
    judge_method_override: Optional[str], stage_label: str,
) -> tuple:
    """Single-stage judging: runs every canonical evaluator on `all_rows`.

    Returns (asr_scalar, refusal_scalar, eval_stats_dict, judge_config_hash,
    judge_errors). asr/refusal are scalars (defense+evaluate has one logical
    stage) or None if no judge of that type ran. judge_errors is the list of
    evaluators that were skipped/failed — non-empty means the result's metrics
    are incomplete (status becomes "partial_judge").
    """
    evaluators = _resolve_evaluators(judge_method_override, benchmark)
    asr: Optional[float] = None
    refusal: Optional[float] = None
    eval_stats: dict[str, dict] = {}
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
            if is_refusal:
                refusal = value
            else:
                asr = value
            eval_stats[evaluator.__class__.__name__] = stats
            # OR-Bench exposes direct_answer_rate as asr.
            if "direct_answer_rate" in stats and is_refusal:
                asr = stats["direct_answer_rate"]
            logger.info(
                f"[{stage_label}] {evaluator.__class__.__name__}: "
                f"{stat_key}={value:.2f}%")
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
    return asr, refusal, (eval_stats or None), jhash, judge_errors


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
    """
    from src.experiment.config import CONF_DIR

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
            upstream=upstream or None,
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
    target_model_config = LLMServiceFactory._load_model_defaults(
        LLMModel.from_string(task.target_model))

    # Run defense — owns the target-model interaction loop.
    pairs = defense.query(
        prompts=prompts,
        target_service=target_service,
        is_multimodal=is_multimodal,
        source_dir=source_dir,
        system_message=task.system_message,
    )

    # Build EvaluationRow list with synthetic prompt_stage.
    stage_label = f"{encoding}__{task.defense}" if encoding else task.defense
    all_rows: list[EvaluationRow] = [
        EvaluationRow(id=pid, prompt_stage=stage_label, response=resp, asr=None)
        for pid, resp in pairs
    ]

    # Write raw_results.jsonl (raw model responses preserved so judging can
    # be re-run later with a different judge config if needed).
    write_jsonl_atomic(
        out_dir / "raw_results.jsonl",
        [row.model_dump_json() for row in all_rows])

    # Judge.
    asr, refusal, eval_stats, jhash, judge_errors = _run_judging(
        prompts=prompts, all_rows=all_rows, benchmark=benchmark,
        judge_method_override=task.judge_method, stage_label=stage_label,
    )
    judge_method_provenance = task.judge_method or benchmark
    judge_model_used = _load_conf("evaluation").get(
        "judge_llm_config", {}).get("model")

    # Overwrite raw_results.jsonl now that verdict columns are filled.
    write_jsonl_atomic(
        out_dir / "raw_results.jsonl",
        [row.model_dump_json() for row in all_rows])

    elapsed = round(time.time() - t0, 2)

    result = DefenseEvaluateResult(
        source_transform_subdir=str(source_dir),
        upstream=upstream,
        is_multimodal=is_multimodal,
        defense=task.defense,
        defense_config=task.defense_config or {},
        target_model=task.target_model,
        target_model_config=TargetModelConfig(**target_model_config),
        system_message=task.system_message,
        benchmark=benchmark,
        encoding=encoding,
        transformation_list=transformation_list,
        prompt_range=task.prompt_range,
        judge_method=judge_method_provenance,
        judge_model=judge_model_used,
        count=len(all_rows),
        asr=asr,
        refusal_rate=refusal,
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


# ======================== Dispatcher ========================


TASK_MODES = {
    "prompt_transform": _run_prompt_transform,
    "defense+evaluate": _run_defense_evaluate,
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

            for art in ("results.json", "prompts.jsonl", "raw_results.jsonl"):
                p = out_path / art
                if p.exists():
                    tracker.log_artifact(str(p))

        return result
    except Exception:
        tracker.log_metrics({"status_failed": 1})
        raise
    finally:
        tracker.end_run()
