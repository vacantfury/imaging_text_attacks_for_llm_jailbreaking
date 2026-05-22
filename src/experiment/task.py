"""
Task runner for Encoding × Modality jailbreaking experiments.

Pipeline stages:
  text_encode → [defense_transform] → [imaging] → evaluate
                                    └→ evaluate (text-only)

Modes:
  text_encode       — encode harmful prompts (LLM-based or rule-based)
  defense_transform — apply transform-only defense (e.g., SAGE wrapping)
  imaging           — render text prompts as images
  evaluate          — query target model + ASR judging
  defense           — coupled defense+query+judge (e.g., SemanticSmooth)

Prompt stages (2×2 grid):
              Text modality    Image modality
  Original    text_original    image_original
  Encoded     text_encoded     image_encoded
"""
import json
import time
from pathlib import Path
from typing import Any, Optional

from PIL import Image

from src.utils.logger import get_logger
from src.utils.experiment import get_new_experiment_data_dir
from src.text_encoding import create_encoder
from src.text_encoding.encoder_factory import resolve_encoding_name
from src.imaging import create_renderer
from src.llm_utils import LLMServiceFactory
from src.llm_utils.llm_model import LLMModel
from src.evaluation.evaluator_factory import EvaluatorFactory
from .config import load_conf as _load_conf
from .schemas import (
    RawPrompt, Prompt, EvaluationRow,
    TextEncodeResult, ImagingResult,
    EvaluateResult, DefenseTransformResult, DefenseResult,
    TargetModelConfig,
)

logger = get_logger(__name__)


# ======================== Helpers ========================

def _save_results(out_dir: Path, results: dict[str, Any]) -> None:
    """Save results.json — task config, provenance, and aggregate metrics."""
    with open(out_dir / "results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Saved results.json to {out_dir}")


def _load_results(source_dir: str) -> dict[str, Any]:
    """Load results.json from an upstream task's output directory."""
    path = Path(source_dir) / "results.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}





def _load_prompts(source_dir: str) -> list[Prompt]:
    """Load prompts.jsonl from a task output directory."""
    source_path = Path(source_dir) / "prompts.jsonl"
    prompts = []
    with open(source_path) as f:
        for line in f:
            if line.strip():
                prompts.append(Prompt.model_validate_json(line))
    return prompts


def _load_and_slice_prompts(source_dir: str, prompt_range: Optional[list[int]]) -> list[Prompt]:
    """Load prompts from source_dir and apply prompt_range slice."""
    prompts = _load_prompts(source_dir)
    prompts = _apply_prompt_range(prompts, prompt_range)
    logger.info(f"Loaded {len(prompts)} prompts from {source_dir}")
    return prompts


def _apply_prompt_range(items: list, prompt_range: Optional[list[int]]) -> list:
    """Slice items by prompt_range = [start, end] (0-based, both inclusive).

    Examples:
        prompt_range = [0, 99]  → first 100 items (indices 0–99)
        prompt_range = [10, 19] → items 10–19 (10 items)
    """
    if not prompt_range or not isinstance(prompt_range, list) or len(prompt_range) != 2:
        return items
    
    try:
        start, end = int(prompt_range[0]), int(prompt_range[1])
    except (ValueError, TypeError):
        logger.warning(f"Invalid prompt_range {prompt_range}, using all {len(items)} prompts")
        return items
    
    start = max(0, start)
    end = min(len(items) - 1, end)
    if start > end:
        logger.warning(f"prompt_range [{start}, {end}] is empty, using all {len(items)} prompts")
        return items
    
    sliced = items[start:end + 1]
    logger.info(f"Applied prompt_range [{start}, {end}]: {len(sliced)} of {len(items)} prompts")
    return sliced



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
    """Infer benchmark name from a source file or directory path.

    For directory paths (outputs/text_encode/harmbench/...),
    extracts the benchmark directly from the path components.
    For file paths (data/jbb_prompts.jsonl), checks known aliases.

    Strict: raises ValueError if no benchmark can be identified, rather
    than silently defaulting. The benchmark drives evaluator selection
    downstream — a silent wrong guess would send harmful prompts to the
    wrong classifier. Fail loud at config time instead.
    """
    parts = Path(source_path).parts
    for part in parts:
        if part in KNOWN_BENCHMARKS:
            return part
    # File-based fallback: check aliases in the filename/path.
    # Longer aliases first so 'jbb_benign' matches before 'jbb'.
    name = str(source_path).lower()
    for alias, bench in sorted(BENCHMARK_ALIASES.items(), key=lambda x: -len(x[0])):
        if alias in name:
            return bench
    raise ValueError(
        f"Could not infer benchmark from path: {source_path!r}. "
        f"Expected one of {sorted(KNOWN_BENCHMARKS)} as a path component, "
        f"or a matching alias from {sorted(BENCHMARK_ALIASES)}. "
        f"If this is a non-standard source, set `benchmark:` explicitly "
        f"in the task config.")


# Valid prompt stages
VALID_PROMPT_STAGES = {"text_original", "text_encoded", "image_original", "image_encoded"}
VALID_RENDER_STAGES = {"original", "encoded"}


# ======================== text_encode ========================

def _run_text_encode(task) -> dict[str, Any]:
    """Mode: text_encode. Reads raw prompts, encodes them, writes prompts.jsonl."""
    t0 = time.time()

    logger.info(f"Text encoding: {task.encoding} from {task.source_file}")

    # Load raw prompts
    prompts = []
    with open(task.source_file) as f:
        for line in f:
            if line.strip():
                prompts.append(RawPrompt.model_validate_json(line))

    prompts = _apply_prompt_range(prompts, task.prompt_range)
    logger.info(f"Loaded {len(prompts)} prompts")

    # Create encoder: 3-layer merge (default → encoding-specific → task-level)
    encoder_config = _load_conf(
        "text_encoding", override_name=task.encoding,
        task_overrides=task.encoder or None)

    resolved_type, _ = resolve_encoding_name(task.encoding)
    encoder = create_encoder(task.encoding, **encoder_config)
    raw_texts = [p.prompt for p in prompts]
    encoded_texts = encoder.batch_process(raw_texts)

    elapsed = round(time.time() - t0, 2)
    usage = encoder.get_usage()

    benchmark = task.benchmark or _infer_benchmark(task.source_file)
    out_dir = Path(get_new_experiment_data_dir(
        "outputs/text_encode", dataset=benchmark, model=task.encoding))

    with open(out_dir / "prompts.jsonl", "w") as f:
        for prompt, encoded in zip(prompts, encoded_texts):
            record = Prompt(
                id=prompt.id,
                encoding=task.encoding,
                original=prompt.prompt,
                encoded=encoded,
            )
            f.write(record.model_dump_json() + "\n")

    logger.info(f"Wrote {len(prompts)} encoded prompts to {out_dir} ({elapsed}s)")

    result = TextEncodeResult(
        encoding=task.encoding,
        encoder_type=resolved_type,
        encoder_config=encoder_config,
        benchmark=benchmark,
        source_file=task.source_file,
        prompt_range=task.prompt_range,
        count=len(prompts),
        elapsed_seconds=elapsed,
        output_dir=str(out_dir),
        usage=usage if usage else None,
    )
    _save_results(out_dir, result.model_dump(exclude_none=True))

    return {"status": "success", "output_dir": str(out_dir), "count": len(prompts),
            "elapsed_seconds": elapsed, "usage": usage}


# ======================== imaging ========================

def _verify_image_quality(
    images_dir: Path, sample_size: int = 5,
    fail_threshold: float = 1.0, warn_threshold: float = 3.0,
) -> None:
    """Sample rendered images and catch blank / tofu rendering.

    Two-tier check on the percentage of non-white (< 240) pixels:
      - Below *fail_threshold* %: certainly broken → raise RuntimeError.
      - Below *warn_threshold* %: suspicious → log WARNING for review.
      - Above *warn_threshold* %: OK.

    Empirical reference (from Stage 7 bug investigation):
      - Confirmed tofu (no glyphs): 1.3 – 1.9 %
      - Sparse but readable text:   2.9 – 3.0 %
      - Normal rendered images:      10 – 22 %
    """
    import numpy as np

    pngs = sorted(images_dir.glob("*.png"))[:sample_size]
    if not pngs:
        return

    failed: list[str] = []
    warned: list[str] = []
    for png_path in pngs:
        img = Image.open(png_path)
        arr = np.array(img)
        ink_pct = (arr < 240).sum() / arr.size * 100
        if ink_pct < fail_threshold:
            failed.append(f"{png_path.name} ({ink_pct:.1f}%)")
        elif ink_pct < warn_threshold:
            warned.append(f"{png_path.name} ({ink_pct:.1f}%)")

    if warned:
        logger.warning(
            f"Image quality: {len(warned)}/{len(pngs)} sampled images have "
            f"low ink (<{warn_threshold}%) — review manually: "
            + ", ".join(warned))

    if failed:
        logger.error(
            f"IMAGE QUALITY CHECK FAILED — {len(failed)}/{len(pngs)} "
            f"sampled images appear blank (likely tofu/missing glyphs): "
            + ", ".join(failed))
        raise RuntimeError(
            f"Rendering produced blank images — check font availability. "
            f"Failing: {failed}")

    logger.info(
        f"Image quality check passed: {len(pngs)} sampled, "
        f"{len(warned)} warned, {len(failed)} failed")


def _run_imaging(task) -> dict[str, Any]:
    """
    Mode: imaging
    
    Reads prompts from text_encode output, renders images.
    
    Parameter: render — list from ["original", "encoded"]
      - "original" → renders .original field → stores in image_original
      - "encoded"  → renders .encoded field  → stores in image_encoded
    
    Output:
      results.json
      prompts.jsonl     — copied from input + image_original/image_encoded paths added
      images/           — rendered PNGs (named {id}_original.png, {id}_encoded.png)
    """
    t0 = time.time()

    invalid = set(task.render) - VALID_RENDER_STAGES
    if invalid:
        raise ValueError(f"Invalid render stages: {invalid}. Valid: {VALID_RENDER_STAGES}")

    logger.info(f"Imaging from {task.source_dir}, render={task.render}")

    # Load prompts
    prompts = _load_and_slice_prompts(task.source_dir, task.prompt_range)

    # Create renderer: 3-layer merge (default → renderer-specific → task-level)
    renderer_config = _load_conf(
        "imaging", override_name=task.renderer_type,
        task_overrides=task.renderer or None)
    renderer_config.pop("renderer_type", None)
    quality_check_conf = renderer_config.pop("quality_check", {})
    logger.info(f"Loaded imaging config for renderer={task.renderer_type}")

    renderer = create_renderer(task.renderer_type, **renderer_config)

    # Output dir
    encoding = prompts[0].encoding if prompts else "unknown"
    benchmark = task.benchmark or _infer_benchmark(task.source_dir)
    out_dir = Path(get_new_experiment_data_dir(
        "outputs/imaging", dataset=benchmark, model=f"{encoding}_{task.renderer_type}"))

    images_dir = out_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    # Render images and augment prompts
    augmented = []
    image_count = 0
    for prompt in prompts:
        updates = {}

        if "original" in task.render:
            img_name = f"{prompt.id}_original.png"
            renderer.render_to_file(prompt.original, str(images_dir / img_name))
            updates["image_original"] = f"images/{img_name}"
            image_count += 1

        if "encoded" in task.render:
            img_name = f"{prompt.id}_encoded.png"
            renderer.render_to_file(prompt.encoded, str(images_dir / img_name))
            updates["image_encoded"] = f"images/{img_name}"
            image_count += 1

        augmented.append(prompt.model_copy(update=updates))

    with open(out_dir / "prompts.jsonl", "w") as f:
        for record in augmented:
            f.write(record.model_dump_json() + "\n")

    _verify_image_quality(
        images_dir,
        sample_size=min(quality_check_conf.get("sample_size", 5), image_count),
        fail_threshold=quality_check_conf.get("fail_threshold", 1.0),
        warn_threshold=quality_check_conf.get("warn_threshold", 3.0),
    )

    elapsed = round(time.time() - t0, 2)
    logger.info(f"Rendered {image_count} images to {out_dir}/images/ ({elapsed}s)")

    result = ImagingResult(
        encoding=encoding,
        renderer_type=task.renderer_type,
        renderer_config=renderer_config,
        render=task.render,
        source_dir=task.source_dir,
        prompt_range=task.prompt_range,
        count=len(prompts),
        image_count=image_count,
        elapsed_seconds=elapsed,
        output_dir=str(out_dir),
        upstream=_load_results(task.source_dir) or None,
    )
    _save_results(out_dir, result.model_dump(exclude_none=True))

    return {"status": "success", "output_dir": str(out_dir), "count": len(prompts),
            "image_count": image_count, "elapsed_seconds": elapsed}


# ======================== evaluate helpers ========================

def _build_conversations_for_stage(
    stage: str, prompts: list[Prompt], source_path: Path, image_instruction: str
) -> tuple[list[tuple[str, list]], dict[str, Prompt]]:
    """Build conversation tuples and a lookup dict for a single prompt stage."""
    conversations = []
    prompt_lookup = {}

    for prompt in prompts:
        conv_id = f"{prompt.id}__{stage}"

        if stage == "text_original":
            conversations.append((conv_id, [(prompt.original, None)]))
        elif stage == "text_encoded":
            conversations.append((conv_id, [(prompt.encoded, None)]))
        elif stage == "image_original":
            pil_image = Image.open(source_path / prompt.image_original)
            conversations.append((conv_id, [(image_instruction, pil_image)]))
        elif stage == "image_encoded":
            pil_image = Image.open(source_path / prompt.image_encoded)
            conversations.append((conv_id, [(image_instruction, pil_image)]))

        prompt_lookup[conv_id] = prompt

    return conversations, prompt_lookup


def _resolve_evaluators(judge_method_override: Optional[str], benchmark: str) -> list:
    """Resolve the evaluator list + configure each one's judge LLM.

    Reads `judge_llm_config` from conf/evaluation/default.yaml — model,
    max_tokens, temperature — and passes them to every evaluator
    constructor. Same judge model for all evaluators in a run.

    Canonical path (default): the benchmark slug picks the evaluator
    class(es). jailbreakbench → [harmful, refusal]; everything else →
    single evaluator.

    Emergency override: `judge_method_override` (set in task YAML)
    bypasses the canonical benchmark→evaluator mapping and runs only
    the explicitly-named evaluator. Rare; ad-hoc sanity checks only.
    """
    from src.llm_utils import LLMModel

    eval_config = _load_conf("evaluation")
    judge_cfg = eval_config.get("judge_llm_config", {})
    judge_kwargs = dict(judge_cfg)
    judge_model_str = judge_kwargs.pop("model", "gpt-5-nano")
    judge_model = LLMModel.from_string(judge_model_str)

    if judge_method_override:
        logger.warning(
            f"judge_method override active: '{judge_method_override}' "
            f"(bypassing canonical benchmark→evaluator mapping for {benchmark!r})")
        return [EvaluatorFactory.create(
            method=judge_method_override, model=judge_model, **judge_kwargs)]
    return EvaluatorFactory.create_from_benchmark(
        benchmark, model=judge_model, **judge_kwargs)


def _is_refusal_evaluator(evaluator) -> bool:
    """Whether this evaluator reports refusal_rate (vs attack_success_rate)."""
    from src.evaluation.evaluator_factory import REFUSAL_RATE_EVALUATORS
    return isinstance(evaluator, REFUSAL_RATE_EVALUATORS)


def _apply_verdict_columns(
    stage_rows: list, detailed_df, is_refusal: bool,
) -> None:
    """Copy a judge's per-row verdict into the right column group on rows.

    The harmful judge writes to (asr, judge_output, judge_reasoning,
    judge_raw_response). The refusal judge writes to (refusal,
    refusal_judge_output, refusal_judge_reasoning, refusal_judge_raw_response).
    For benchmarks that run both (jailbreakbench), both column groups end
    up populated on every row.
    """
    if detailed_df is None:
        return

    def _col(df, name) -> dict:
        if name not in df.columns:
            return {}
        return dict(zip(df["id"].astype(str), df[name].astype(str)))

    verdict_col = "is_refused" if is_refusal else "is_jailbroken"
    if verdict_col not in detailed_df.columns:
        return
    verdict_by_id = dict(
        zip(detailed_df["id"].astype(str), detailed_df[verdict_col]))
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


def _run_asr_judging(
    judge_method_override: Optional[str], prompts: list[Prompt],
    all_rows: list[EvaluationRow], prompt_stages: list[str],
    benchmark: str,
) -> tuple[dict[str, Optional[float]], dict[str, Optional[float]]]:
    """Run every canonical judge for the benchmark across all stages.

    Returns (asr_per_stage, refusal_per_stage). A stage that no judge of
    a given type ran for is `None` in the corresponding dict — distinguishes
    "not applicable" (canonical mapping has no refusal judge here) from
    "0%".

    Side effect: writes verdict columns onto each EvaluationRow in `all_rows`.
    """
    evaluators = _resolve_evaluators(judge_method_override, benchmark)
    asr_per_stage: dict[str, Optional[float]] = {s: None for s in prompt_stages}
    refusal_per_stage: dict[str, Optional[float]] = {s: None for s in prompt_stages}

    original_lookup = {p.id: p.original for p in prompts}

    for evaluator in evaluators:
        is_refusal = _is_refusal_evaluator(evaluator)
        stat_key = "refusal_rate" if is_refusal else "attack_success_rate"
        metric_label = "Refusal rate" if is_refusal else "ASR"
        target_per_stage = refusal_per_stage if is_refusal else asr_per_stage

        logger.info(
            f"Judging with {evaluator.__class__.__name__} "
            f"(metric: {metric_label})")

        try:
            for stage in prompt_stages:
                stage_rows = [r for r in all_rows if r.prompt_stage == stage]
                if not stage_rows:
                    continue

                judge_prompts = [
                    {"id": r.id, "prompt": original_lookup[r.id]} for r in stage_rows
                ]
                judge_processed = [original_lookup[r.id] for r in stage_rows]
                judge_responses = {r.id: r.response for r in stage_rows}

                detailed_df, stats = evaluator.evaluate(
                    prompts=judge_prompts,
                    processed_prompts=judge_processed,
                    responses=judge_responses,
                )

                _apply_verdict_columns(stage_rows, detailed_df, is_refusal)
                target_per_stage[stage] = stats.get(stat_key, 0.0)
                logger.info(
                    f"  {metric_label} for {stage}: {target_per_stage[stage]:.2f}%")

                # ORBench returns BOTH direct_answer_rate and refusal_rate in
                # its stats. Expose direct_answer_rate as the `asr` metric so
                # results.json has both:
                #   asr           = direct_answer_rate (= jailbreak success on
                #                   harmful prompts; compliance on benign)
                #   refusal_rate  = direct_refusal + indirect_refusal
                # Preserves historical "asr" field semantics for ORBench dirs.
                # JBB/HarmBench evaluators don't return direct_answer_rate so
                # this branch is a no-op for them.
                if "direct_answer_rate" in stats and is_refusal:
                    asr_per_stage[stage] = stats["direct_answer_rate"]
                    logger.info(
                        f"  ASR (direct_answer_rate) for {stage}: "
                        f"{stats['direct_answer_rate']:.2f}%")

        except (ValueError, KeyError, FileNotFoundError) as e:
            logger.warning(
                f"Judging skipped for {evaluator.__class__.__name__} — "
                f"config/data issue: {e}")
        except Exception as e:
            logger.warning(
                f"Judging failed for {evaluator.__class__.__name__}: {e}",
                exc_info=True)

    return asr_per_stage, refusal_per_stage


# ======================== evaluate ========================

def _run_evaluate(task) -> dict[str, Any]:
    """
    Mode: evaluate
    
    Takes an imaging experiment folder, queries target model per prompt_stage,
    runs ASR judging, outputs long-format results.
    
    Parameter: prompt_stages — list from
      ["text_original", "text_encoded", "image_original", "image_encoded"]
    
    Output:
      results.json        — parameters + ASR per prompt_stage
      raw_results.jsonl   — long format: one row per (prompt × prompt_stage)
    """
    t0 = time.time()

    invalid = set(task.prompt_stages) - VALID_PROMPT_STAGES
    if invalid:
        raise ValueError(f"Invalid prompt_stages: {invalid}. Valid: {VALID_PROMPT_STAGES}")

    logger.info(
        f"Evaluating: model={task.target_model}, prompt_stages={task.prompt_stages}")

    source_path = Path(task.source_dir)
    prompts = _load_and_slice_prompts(task.source_dir, task.prompt_range)

    # Validate image stages have images
    image_stages = [s for s in task.prompt_stages if s.startswith("image_")]
    for stage in image_stages:
        missing = [p for p in prompts if getattr(p, stage) is None]
        if missing:
            raise ValueError(
                f"prompt_stages includes '{stage}' but {len(missing)} prompts "
                f"have no {stage} field. Did imaging render this stage?")

    encoding = (
        prompts[0].encoding if prompts
        else (task.encoding or "unknown"))
    benchmark = task.benchmark or _infer_benchmark(task.source_dir)
    stages_label = "+".join(task.prompt_stages)
    out_dir = Path(get_new_experiment_data_dir(
        "outputs/evaluate", dataset=benchmark,
        model=f"{task.target_model}_{stages_label}_{encoding}"))

    service = LLMServiceFactory.create(task.target_model)
    target_model_config = LLMServiceFactory._load_model_defaults(
        LLMModel.from_string(task.target_model))

    # Query model per stage, collect results
    all_rows: list[EvaluationRow] = []
    stage_counts: dict[str, int] = {}
    for stage in task.prompt_stages:
        logger.info(f"  Stage: {stage} ({len(prompts)} prompts)...")
        conversations, prompt_lookup = _build_conversations_for_stage(
            stage, prompts, source_path, task.image_instruction)
        if not conversations:
            continue

        results = service.batch_chat(
            conversations=conversations,
            system_message=task.system_message,
            is_test=True,
        )
        for conv_id, response_text in results:
            prompt_obj = prompt_lookup[conv_id]
            all_rows.append(EvaluationRow(
                id=prompt_obj.id,
                prompt_stage=stage,
                response=response_text,
                asr=None,
            ))
        stage_counts[stage] = len(results)
        logger.info(f"  Stage {stage}: {len(results)} responses")

    # Judging: every canonical judge for the benchmark runs in one task.
    # jailbreakbench → both harmful (→ asr) and refusal (→ refusal_rate).
    asr_per_stage, refusal_per_stage = _run_asr_judging(
        task.judge_method, prompts, all_rows, task.prompt_stages, benchmark)
    asr_per_stage = {k: v for k, v in asr_per_stage.items() if v is not None} or None
    refusal_per_stage = {
        k: v for k, v in refusal_per_stage.items() if v is not None
    } or None

    # Provenance: explicit override if set, otherwise the benchmark slug
    # (which uniquely identifies the canonical evaluator set).
    judge_method_provenance = task.judge_method or benchmark
    # Actual judge LLM used (from conf/evaluation/default.yaml::judge_llm_config.model)
    judge_model_used = _load_conf("evaluation").get(
        "judge_llm_config", {}).get("model")

    # Write raw_results.jsonl
    results_path = out_dir / "raw_results.jsonl"
    with open(results_path, "w") as f:
        for row in all_rows:
            f.write(row.model_dump_json() + "\n")
    logger.info(f"Saved {len(all_rows)} rows to {results_path}")

    elapsed = round(time.time() - t0, 2)

    result = EvaluateResult(
        target_model=task.target_model,
        target_model_config=TargetModelConfig(**target_model_config),
        encoding=encoding,
        benchmark=benchmark,
        prompt_stages=task.prompt_stages,
        prompt_range=task.prompt_range,
        source_dir=task.source_dir,
        system_message=task.system_message,
        image_instruction=task.image_instruction,
        judge_method=judge_method_provenance,
        judge_model=judge_model_used,
        count=len(all_rows),
        count_per_stage=stage_counts,
        asr=asr_per_stage,
        refusal_rate=refusal_per_stage,
        usage=service.get_usage(),
        elapsed_seconds=elapsed,
        output_dir=str(out_dir),
        upstream=_load_results(task.source_dir),
    )
    _save_results(out_dir, result.model_dump(exclude_none=True))

    return {
        "status": "success",
        "output_dir": str(out_dir),
        "count": len(all_rows),
        "prompt_stages": task.prompt_stages,
        "target_model": task.target_model,
        "encoding": encoding,
        "judge_method": judge_method_provenance,
        "asr": asr_per_stage,
        "refusal_rate": refusal_per_stage,
        "usage": result.usage,
        "elapsed_seconds": elapsed,
    }


# ======================== defense_transform ========================

def _run_defense_transform(task) -> dict[str, Any]:
    """
    Mode: defense_transform

    Applies a transform-only defense (e.g., SAGE wrapping) to encoded prompts.
    No model querying or judging — just text transformation.

    Input: text_encode output dir (prompts.jsonl with encoded field).
    Output: new prompts.jsonl where 'encoded' = defense-wrapped text.
            Compatible as source_dir for imaging or evaluate stages.
    """
    from src.defense import create_defender

    t0 = time.time()

    logger.info(f"Defense transform: method={task.defense_method}")

    prompts = _load_and_slice_prompts(task.source_dir, task.prompt_range)
    encoding = prompts[0].encoding if prompts else (task.encoding or "unknown")
    benchmark = task.benchmark or _infer_benchmark(task.source_dir)

    defense_config = _load_conf(
        "defense", override_name=task.defense_method,
        task_overrides=task.defense_config or None)
    defense_config.pop("perturbation_model", None)

    defender = create_defender(task.defense_method, **defense_config)

    if not getattr(defender, "is_transform_only", False):
        raise ValueError(
            f"Defense '{task.defense_method}' does not support transform-only mode. "
            f"Use 'defense' mode instead.")

    prompt_dicts = [{"id": p.id, "encoded": p.encoded} for p in prompts]
    transformed = defender.transform(prompt_dicts)

    out_dir = Path(get_new_experiment_data_dir(
        "outputs/defense_transform", dataset=benchmark,
        model=f"{task.defense_method}_{encoding}"))

    with open(out_dir / "prompts.jsonl", "w") as f:
        for orig_prompt, t_dict in zip(prompts, transformed):
            record = Prompt(
                id=t_dict["id"],
                encoding=encoding,
                original=orig_prompt.original,
                encoded=t_dict["encoded"],
            )
            f.write(record.model_dump_json() + "\n")

    elapsed = round(time.time() - t0, 2)
    logger.info(
        f"Defense transform complete: {len(prompts)} prompts → {out_dir} ({elapsed}s)")

    result = DefenseTransformResult(
        defense_method=task.defense_method,
        defense_config=defense_config if defense_config else None,
        encoding=encoding,
        benchmark=benchmark,
        prompt_range=task.prompt_range,
        source_dir=task.source_dir,
        count=len(prompts),
        elapsed_seconds=elapsed,
        output_dir=str(out_dir),
        upstream=_load_results(task.source_dir) or None,
    )
    _save_results(out_dir, result.model_dump(exclude_none=True))

    return {
        "status": "success",
        "output_dir": str(out_dir),
        "count": len(prompts),
        "defense_method": task.defense_method,
        "encoding": encoding,
        "elapsed_seconds": elapsed,
    }


# ======================== defense ========================

def _run_defense(task) -> dict[str, Any]:
    """
    Mode: defense

    Applies a defense strategy (SAGE, SemanticSmooth) to encoded prompts,
    queries the target model through the defense, runs ASR judging.

    Input: text_encode output dir (prompts.jsonl with encoded field).
    Output: same format as evaluate (raw_results.jsonl + results.json).
    """
    from src.defense import create_defender

    t0 = time.time()

    logger.info(f"Defense: method={task.defense_method}, model={task.target_model}")

    prompts = _load_and_slice_prompts(task.source_dir, task.prompt_range)
    encoding = prompts[0].encoding if prompts else (task.encoding or "unknown")
    benchmark = task.benchmark or _infer_benchmark(task.source_dir)

    defense_config = _load_conf(
        "defense", override_name=task.defense_method,
        task_overrides=task.defense_config or None)
    logger.info(f"Loaded defense config for method={task.defense_method}: {defense_config}")

    # Extract perturbation_model before passing the rest to the defender ctor
    perturbation_model = defense_config.pop("perturbation_model", None)
    defender = create_defender(task.defense_method, **defense_config)

    service = LLMServiceFactory.create(task.target_model)

    if perturbation_model:
        from src.defense.defenders.semantic_smooth_defender import SemanticSmoothDefender
        if isinstance(defender, SemanticSmoothDefender):
            perturbation_service = LLMServiceFactory.create(perturbation_model)
            defender.set_perturbation_service(perturbation_service)

    prompt_dicts = [{"id": p.id, "encoded": p.encoded} for p in prompts]
    results = defender.defend_and_query(
        prompts=prompt_dicts,
        service=service,
        system_message=task.system_message,
    )

    all_rows: list[EvaluationRow] = []
    for prompt_id, response_text in results:
        all_rows.append(EvaluationRow(
            id=prompt_id,
            prompt_stage=f"text_encoded__{task.defense_method}",
            response=response_text,
            asr=None,
        ))

    out_dir = Path(get_new_experiment_data_dir(
        "outputs/defense", dataset=benchmark,
        model=f"{task.target_model}_{task.defense_method}_{encoding}"))

    # Judging: defense mode has a single prompt_stage. Reuse _run_asr_judging
    # with a 1-element prompt_stages list; collapse the per-stage dicts to
    # scalars to match DefenseResult's schema.
    defense_stage = f"text_encoded__{task.defense_method}"
    asr_per_stage, refusal_per_stage = _run_asr_judging(
        task.judge_method, prompts, all_rows, [defense_stage], benchmark)
    asr_value = asr_per_stage.get(defense_stage)
    refusal_value = refusal_per_stage.get(defense_stage)
    judge_method_provenance = task.judge_method or benchmark
    judge_model_used = _load_conf("evaluation").get(
        "judge_llm_config", {}).get("model")

    results_path = out_dir / "raw_results.jsonl"
    with open(results_path, "w") as f:
        for row in all_rows:
            f.write(row.model_dump_json() + "\n")

    elapsed = round(time.time() - t0, 2)
    logger.info(f"Defense complete: {len(all_rows)} prompts, {elapsed}s")

    result = DefenseResult(
        defense_method=task.defense_method,
        defense_config=defense_config if defense_config else None,
        target_model=task.target_model,
        encoding=encoding,
        benchmark=benchmark,
        prompt_range=task.prompt_range,
        source_dir=task.source_dir,
        system_message=task.system_message,
        judge_method=judge_method_provenance,
        judge_model=judge_model_used,
        count=len(all_rows),
        asr=asr_value,
        refusal_rate=refusal_value,
        usage=service.get_usage(),
        defense_usage=defender.get_usage(),
        elapsed_seconds=elapsed,
        output_dir=str(out_dir),
        upstream=_load_results(task.source_dir) or None,
    )
    _save_results(out_dir, result.model_dump(exclude_none=True))

    return {
        "status": "success",
        "output_dir": str(out_dir),
        "count": len(all_rows),
        "defense_method": task.defense_method,
        "target_model": task.target_model,
        "encoding": encoding,
        "judge_method": judge_method_provenance,
        "asr": asr_value,
        "refusal_rate": refusal_value,
        "usage": service.get_usage(),
        "elapsed_seconds": elapsed,
    }


# ======================== Dispatcher ========================

TASK_MODES = {
    "text_encode": _run_text_encode,
    "imaging": _run_imaging,
    "evaluate": _run_evaluate,
    "defense_transform": _run_defense_transform,
    "defense": _run_defense,
}


def run_task(task) -> dict[str, Any]:
    """Run a task. `task` is a TaskConfig (discriminated union variant).

    Each task is tracked as an MLflow run with params, metrics, and artifacts.
    """
    from src.utils.mlflow_tracker import MLflowTracker  # lazy: optional dependency
    from .schemas import (EvaluateTask, DefenseTask, ImagingTask)

    # Accept legacy dict input for backward-compat callers (tests, ad-hoc use).
    if isinstance(task, dict):
        from pydantic import TypeAdapter
        from .schemas import TaskConfig as _TaskConfigAlias
        task = TypeAdapter(_TaskConfigAlias).validate_python(task)

    mode = task.mode
    if mode not in TASK_MODES:
        raise ValueError(f"Unknown mode: '{mode}'. Valid: {list(TASK_MODES.keys())}")

    logger.info(f"Running task in mode: {mode}")

    # MLflow params/tags from the typed task
    model_for_mlflow = ""
    if isinstance(task, (EvaluateTask, DefenseTask)):
        model_for_mlflow = task.target_model

    modality = ""
    if isinstance(task, EvaluateTask):
        modality = ",".join(task.prompt_stages)
    elif isinstance(task, ImagingTask):
        modality = ",".join(task.render)

    tracker = MLflowTracker()
    tracker.start_run(
        mode=mode,
        encoding=getattr(task, "encoding", "") or "",
        model=model_for_mlflow,
        modality=modality,
    )
    tracker.log_params(task.model_dump(exclude_none=True))

    try:
        result = TASK_MODES[mode](task)
        tracker.log_metrics(result)
        
        out_dir = result.get("output_dir")
        if out_dir:
            out_path = Path(out_dir)
            
            # Write mlflow_run_id into results.json for cross-referencing
            results_file = out_path / "results.json"
            if results_file.exists():
                with open(results_file) as f:
                    results_data = json.load(f)
                results_data["mlflow_run_id"] = tracker.run_id
                with open(results_file, "w") as f:
                    json.dump(results_data, f, indent=2, default=str)
            
            for artifact_name in ("results.json",
                                  "prompts.jsonl", "raw_results.jsonl"):
                artifact = out_path / artifact_name
                if artifact.exists():
                    tracker.log_artifact(str(artifact))
        
        return result
    except Exception:
        tracker.log_metrics({"status_failed": 1})
        raise
    finally:
        tracker.end_run()
