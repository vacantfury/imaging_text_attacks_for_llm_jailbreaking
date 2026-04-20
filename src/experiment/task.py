"""
Task runner for PTP experiments.
Dispatches to appropriate optimizer based on mode.
"""
from typing import Any
from omegaconf import OmegaConf
from types import SimpleNamespace

from .config import OptimizationMode
from src.llm_utils.llm_model import LLMModel
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _build_optimizer_config(config: dict) -> SimpleNamespace:
    """Build optimizer config namespace from task config dict.
    
    Creates a SimpleNamespace with:
        - llm_config: DictConfig from Hydra's llm/model section
        - data_loader_config: DictConfig from Hydra's data_loader section
        - evaluation_config: DictConfig from Hydra's evaluation section
        - experiment_dir: str or None
        - naive_extra_instructions: dict or None
        - llm_model: LLMModel enum (resolved from model string)
    """
    # Build LLM config (Hydra: "model", legacy: "llm_config")
    llm_config_data = config.get("model", {}) or config.get("llm_config", {})
    llm_config = OmegaConf.create(llm_config_data) if isinstance(llm_config_data, dict) else llm_config_data
    
    # Resolve LLMModel enum from model string
    model_str = llm_config_data.get("model", "") if isinstance(llm_config_data, dict) else getattr(llm_config_data, "model", "")
    llm_model = LLMModel.from_string(str(model_str)) if model_str else None
    
    # Build data loader config (Hydra: "data_loader", legacy: "data_loader_config")
    data_loader_config_data = config.get("data_loader", {}) or config.get("data_loader_config", {})
    data_loader_config = OmegaConf.create(data_loader_config_data) if isinstance(data_loader_config_data, dict) else data_loader_config_data
    
    # Build evaluation config (Hydra: "evaluation", legacy: "evaluation_config")
    evaluation_config_data = config.get("evaluation", {}) or config.get("evaluation_config", {})
    evaluation_config = OmegaConf.create(evaluation_config_data) if isinstance(evaluation_config_data, dict) else evaluation_config_data
    
    return SimpleNamespace(
        llm_config=llm_config,
        llm_model=llm_model,
        data_loader_config=data_loader_config,
        evaluation_config=evaluation_config,
        experiment_dir=config.get("experiment_dir"),
        naive_extra_instructions=config.get("naive_extra_instructions"),
    )


def run_task(config: dict[str, Any], llm_service=None) -> dict[str, Any]:
    """
    Run a task based on the mode specified in config.
    
    Args:
        config: Dict containing:
            - mode: "baseline" or "naive" (case insensitive)
            - model/llm_config: Dict with LLM configuration
            - data_loader/data_loader_config: Dict with data loader configuration
            - naive_extra_instructions: (optional) Dict for naive mode
        llm_service: Optional pre-initialized LLM service to reuse.
    
    Returns:
        Dict with results including accuracy and experiment_dir
    """
    from src.prompt_optimization.baseline import BaselineOptimizer
    
    mode_str = config.get("mode", "").lower()
    try:
        mode = OptimizationMode(mode_str)
    except ValueError:
        valid_modes = [m.value for m in OptimizationMode]
        raise ValueError(f"Unknown mode: '{mode_str}'. Valid modes: {valid_modes}")
    
    logger.info(f"Running task in mode: {mode.value}")
    
    optimizer_config = _build_optimizer_config(config)
    optimizer = BaselineOptimizer(optimizer_config, llm_service=llm_service)
    
    # Run appropriate method based on mode
    if mode == OptimizationMode.BASELINE:
        result = optimizer.run_baseline()
    elif mode == OptimizationMode.NAIVE:
        result = optimizer.run_naive_optimization()
    
    eval_results = result.get("evaluation", {})
    if "accuracy" in eval_results:
        logger.info(f"Task completed. Accuracy: {eval_results['accuracy']:.2%}")
    else:
        logger.info(f"Task completed. Results: {eval_results}")
    
    return result
