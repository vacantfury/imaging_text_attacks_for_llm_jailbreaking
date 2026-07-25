"""
`rejudge` mode: re-score a stored defense+evaluate dir's saved responses with a
new judge, without re-querying the target.

Split out of task.py (pure code move, no behavior change). Shared helpers come
from src/experiment/judging.py, never from task.py — task.py imports THIS module
to re-export `_run_rejudge`, so importing it back would be circular.
"""
import time
from pathlib import Path
from typing import Any

from src.experiment.judging import (
    _dropped_row_warnings, _infer_benchmark, _load_prompts, _load_results,
    _run_judging, _save_results, _upstream_ref,
)
from src.experiment.schemas import EvaluationRow, RejudgeResult
from src.utils.experiment import get_new_experiment_data_dir
from src.utils.logger import get_logger
from src.utils.provenance import provenance_fields, write_jsonl_atomic

logger = get_logger(__name__)


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
