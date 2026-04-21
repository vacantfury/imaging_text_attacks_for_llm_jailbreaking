"""
Task runner for Encoding × Modality jailbreaking experiments.

Dispatches to appropriate handler based on mode:
  - text_encode: encode prompts → save JSONL
  - imaging:     render encoded text → save PNG images
  - evaluate:    query target model + judge responses → save results
"""
import os
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)


def _make_output_dir(prefix: str, benchmark: str = "harmbench") -> Path:
    """Create timestamped output directory under benchmark folder.
    
    Structure: outputs/<benchmark>/<prefix>_<timestamp>/
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path("outputs") / benchmark / f"{prefix}_{timestamp}"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _save_config(out_dir: Path, config: dict):
    """Save frozen config alongside output data."""
    with open(out_dir / "config.yaml", "w") as f:
        yaml.dump(config, f, default_flow_style=False)



# Mapping from user-facing encoding names to ProcessorType values
ENCODING_MAP = {
    "plain": "non_llm_baseline",
    "math": "llm_set_theory",
    "set_theory": "llm_set_theory",
    "formal_logic": "llm_formal_logic",
    "quantum": "llm_quantum_mechanics",
    "classical_chinese": "llm_set_theory",  # TODO: implement ClassicalChineseEncoder
    "addition_equation": "non_llm_addition_equation_split_reassemble",
    "conditional_probability": "non_llm_conditional_probability",
    "symbol_injection": "non_llm_symbol_injection",
}


# Derive benchmark name from source file path
BENCHMARK_MAP = {
    "harmbench": "harmbench",
    "jbb": "jailbreakbench",
    "benign": "jailbreakbench",
}


def _infer_benchmark(source_path: str) -> str:
    """Infer benchmark name from source file/dir path."""
    name = str(source_path).lower()
    for key, bench in BENCHMARK_MAP.items():
        if key in name:
            return bench
    return "harmbench"  # default


def _run_text_encode(config: dict) -> dict[str, Any]:
    """
    Mode: text_encode
    
    Reads raw prompts from data/, encodes them with the specified processor,
    and writes encoded prompts to outputs/.
    """
    from src.text_encoding import create_processor, ProcessorType
    from src.data_loader.schemas import RawPrompt, EncodedPrompt
    
    encoding = config.get("encoding", "plain")
    source_file = config.get("source_file", "data/harmbench_prompts.jsonl")
    
    # Resolve encoding name to processor type
    processor_type = ENCODING_MAP.get(encoding)
    if processor_type is None:
        raise ValueError(
            f"Unknown encoding: '{encoding}'. "
            f"Available: {list(ENCODING_MAP.keys())}"
        )
    
    logger.info(f"Text encoding: {encoding} → {processor_type} from {source_file}")
    
    # Load raw prompts
    prompts = []
    with open(source_file) as f:
        for line in f:
            if line.strip():
                prompts.append(RawPrompt.model_validate_json(line))
    
    logger.info(f"Loaded {len(prompts)} prompts")
    
    # Create processor and encode
    processor = create_processor(ProcessorType(processor_type))
    raw_texts = [p.prompt for p in prompts]
    encoded_texts = processor.batch_process(raw_texts)
    
    # Build output
    benchmark = config.get("benchmark", _infer_benchmark(source_file))
    out_dir = _make_output_dir(f"text_encode_{encoding}", benchmark=benchmark)
    _save_config(out_dir, config)
    
    with open(out_dir / "prompts.jsonl", "w") as f:
        for prompt, encoded in zip(prompts, encoded_texts):
            record = EncodedPrompt(
                id=prompt.id,
                encoding=encoding,
                original=prompt.prompt,
                encoded=encoded,
            )
            f.write(record.model_dump_json() + "\n")
    
    logger.info(f"Wrote {len(prompts)} encoded prompts to {out_dir}")
    return {"status": "success", "output_dir": str(out_dir), "count": len(prompts)}



def _run_imaging(config: dict) -> dict[str, Any]:
    """
    Mode: imaging
    
    Reads encoded prompts from source_dir, renders each as an image,
    and writes PNGs to outputs/.
    """
    from src.imaging import ImageRenderer
    from src.data_loader.schemas import EncodedPrompt, ImagePrompt
    
    source_dir = config.get("source_dir")
    if not source_dir:
        raise ValueError("imaging mode requires 'source_dir' in config")
    
    logger.info(f"Imaging from {source_dir}")
    
    # Load encoded prompts
    prompts = []
    with open(Path(source_dir) / "prompts.jsonl") as f:
        for line in f:
            if line.strip():
                prompts.append(EncodedPrompt.model_validate_json(line))
    
    logger.info(f"Loaded {len(prompts)} encoded prompts")
    
    # Create renderer
    renderer_config = config.get("renderer", {})
    renderer = ImageRenderer(**renderer_config)
    
    # Render images
    encoding = prompts[0].encoding if prompts else "unknown"
    benchmark = config.get("benchmark", _infer_benchmark(source_dir))
    out_dir = _make_output_dir(f"imaging_{encoding}", benchmark=benchmark)
    _save_config(out_dir, config)
    
    image_records = []
    for prompt in prompts:
        img_filename = f"{prompt.id}.png"
        img_path = out_dir / img_filename
        renderer.render_to_file(prompt.encoded, str(img_path))
        
        image_records.append(ImagePrompt(
            id=prompt.id,
            encoding=prompt.encoding,
            image_path=img_filename,
        ))
    
    # Write image manifest
    with open(out_dir / "images.jsonl", "w") as f:
        for record in image_records:
            f.write(record.model_dump_json() + "\n")
    
    logger.info(f"Rendered {len(prompts)} images to {out_dir}")
    return {"status": "success", "output_dir": str(out_dir), "count": len(prompts)}


def _run_evaluate(config: dict) -> dict[str, Any]:
    """
    Mode: evaluate
    
    Reads encoded text or images from source_dir, queries the target model,
    collects responses, and runs ASR judging.
    """
    from src.data_loader.schemas import EncodedPrompt, ImagePrompt, ModelResponse
    
    source_dir = config.get("source_dir")
    model = config.get("model")
    modality = config.get("modality", "text")
    encoding = config.get("encoding", "unknown")
    
    if not source_dir:
        raise ValueError("evaluate mode requires 'source_dir' in config")
    if not model:
        raise ValueError("evaluate mode requires 'model' in config")
    
    logger.info(f"Evaluating: model={model}, encoding={encoding}, modality={modality}")
    
    source_path = Path(source_dir)
    benchmark = config.get("benchmark", _infer_benchmark(source_dir))
    out_dir = _make_output_dir(f"eval_{model}_{encoding}_{modality}", benchmark=benchmark)
    _save_config(out_dir, config)
    
    # Load prompts based on modality
    if modality == "text":
        prompts = []
        with open(source_path / "prompts.jsonl") as f:
            for line in f:
                if line.strip():
                    prompts.append(EncodedPrompt.model_validate_json(line))
        logger.info(f"Loaded {len(prompts)} text prompts")
    elif modality == "image":
        image_records = []
        with open(source_path / "images.jsonl") as f:
            for line in f:
                if line.strip():
                    image_records.append(ImagePrompt.model_validate_json(line))
        logger.info(f"Loaded {len(image_records)} image prompts")
    else:
        raise ValueError(f"Unknown modality: {modality}")
    
    # TODO: Query target model via llm_utils
    # TODO: Run ASR judging via evaluation/
    
    logger.info(f"Evaluate mode: model query + judging not yet implemented")
    return {
        "status": "success",
        "output_dir": str(out_dir),
        "model": model,
        "encoding": encoding,
        "modality": modality,
    }


# ======================== Dispatcher ========================

TASK_MODES = {
    "text_encode": _run_text_encode,
    "imaging": _run_imaging,
    "evaluate": _run_evaluate,
}


def run_task(config: dict[str, Any]) -> dict[str, Any]:
    """
    Run a task based on the mode specified in config.
    
    Each task is tracked as an MLflow run with params, metrics, and artifacts.
    
    Args:
        config: Dict containing:
            - mode: "text_encode", "imaging", or "evaluate"
            - (mode-specific parameters)
    
    Returns:
        Dict with results
    """
    from src.utils.mlflow_tracker import MLflowTracker
    
    mode = config.get("mode", "").lower()
    
    if mode not in TASK_MODES:
        valid = list(TASK_MODES.keys())
        raise ValueError(f"Unknown mode: '{mode}'. Valid modes: {valid}")
    
    logger.info(f"Running task in mode: {mode}")
    
    # Start MLflow run
    tracker = MLflowTracker()
    tracker.start_run(
        mode=mode,
        encoding=config.get("encoding", ""),
        model=config.get("model", ""),
        modality=config.get("modality", ""),
    )
    tracker.log_params(config)
    
    try:
        result = TASK_MODES[mode](config)
        
        # Log metrics (ASR, counts, etc.)
        tracker.log_metrics(result)
        
        # Log output artifacts (config.yaml, results files)
        out_dir = result.get("output_dir")
        if out_dir:
            out_path = Path(out_dir)
            for artifact_name in ("config.yaml", "prompts.jsonl", "images.jsonl", "results.jsonl"):
                artifact = out_path / artifact_name
                if artifact.exists():
                    tracker.log_artifact(str(artifact))
        
        return result
    except Exception:
        tracker.log_metrics({"status_failed": 1})
        raise
    finally:
        tracker.end_run()

