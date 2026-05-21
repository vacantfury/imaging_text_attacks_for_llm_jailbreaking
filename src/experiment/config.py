"""
Configuration loading and schema definitions.

Structured dataclasses define the YAML schema — OmegaConf validates types
at load time (e.g. max_tokens: "abc" → immediate ValidationError).

load_conf() implements 3-layer YAML merge: default → override → task-level.
Used by task runners, the experiment orchestrator, and the LLM service factory.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional

from omegaconf import MISSING, OmegaConf, DictConfig


# ====================================================================
# Structured config schemas — TYPE ONLY, no defaults.
# All default values live in conf/*.yaml (single source of truth).
# If YAML doesn't provide a field, OmegaConf raises immediately.
# ====================================================================


@dataclass
class ModelConfig:
    """LLM request parameters. Maps to conf/llm/*/model: section."""
    model: str = MISSING
    max_tokens: int = MISSING
    temperature: float = MISSING
    top_p: float = MISSING
    top_k: int = MISSING
    frequency_penalty: float = MISSING
    presence_penalty: float = MISSING
    stop_sequences: List[str] = MISSING
    seed: int = MISSING
    n_completions: int = MISSING
    stream: bool = MISSING
    max_concurrency: int = MISSING
    max_retries: int = MISSING
    batch_poll_interval: int = MISSING
    batch_timeout: int = MISSING


@dataclass
class ClusterConfig:
    """Cluster/vLLM server parameters. Maps to conf/llm/*/cluster: section."""
    partition: str = MISSING
    excluded_nodes: List[str] = MISSING
    gpu_types_excluded: List[str] = MISSING
    num_gpus: int = MISSING
    num_instances: int = MISSING
    cpus_per_task: int = MISSING
    mem_gb: int = MISSING
    time_limit: str = MISSING
    port: int = MISSING
    gpu_memory_utilization: float = MISSING
    max_model_len: int = MISSING
    dtype: Optional[str] = MISSING
    chat_template: Optional[str] = MISSING
    server_start_timeout: int = MISSING
    endpoint_wait_timeout: int = MISSING
    cluster_server_endpoint_timeout: int = MISSING
    monitor_poll_interval: int = MISSING
    health_check_timeout: int = MISSING
    slurm_cmd_timeout: int = MISSING
    conda_env: str = MISSING
    cuda_module: str = MISSING
    hf_home: str = MISSING


@dataclass
class LLMConf:
    """Top-level LLM config. Maps to conf/llm/*.yaml."""
    model: ModelConfig = field(default_factory=ModelConfig)
    cluster: ClusterConfig = field(default_factory=ClusterConfig)


@dataclass
class EvaluationConf:
    """Top-level evaluation config. Maps to conf/evaluation/*.yaml.

    Note: judge model, temperature, and max_tokens are NOT YAML-configurable —
    each evaluator hard-binds its canonical judge via its own constants.py.

    judge_method is also normally NOT used — evaluator selection is derived
    from the benchmark slug in source_dir (see _infer_benchmark and
    EvaluatorFactory.create_from_benchmark). It exists here as an optional
    field for the rare ad-hoc override case.
    """
    judge_method: Optional[str] = None


# ====================================================================
# Config loading
# ====================================================================

CONF_DIR = Path(__file__).resolve().parent.parent.parent / "conf"

# Map subdirectory names to their structured config schemas.
_SCHEMAS = {
    "llm": LLMConf,
    "evaluation": EvaluationConf,
}

# Hydra directives to strip before OmegaConf merge.
_HYDRA_DIRECTIVES = {"defaults"}


def _strip_hydra(cfg: DictConfig) -> DictConfig:
    """Remove Hydra-only directives from a loaded config.
    
    Note: Mutates cfg in place and returns it. Safe because callers always
    pass freshly loaded DictConfig objects from OmegaConf.load().
    """
    for key in _HYDRA_DIRECTIVES:
        if key in cfg:
            del cfg[key]
    return cfg


def load_conf(subdir: str, override_name: Optional[str] = None, *,
              section: Optional[str] = None, match_field: Optional[str] = None,
              match_value: Optional[str] = None,
              task_overrides: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """3-layer YAML config merge: default → override → task-level.

    Works for any conf/ subdirectory (llm, text_encoding, imaging, evaluation).

    Args:
        subdir: Config subdirectory under conf/ (e.g. "llm", "imaging")
        override_name: Specific config file stem to overlay (e.g. "plain", "gpt_4o").
                       If None, searches by match_field/match_value.
        section: If set, return only this top-level key from the merged config.
        match_field: Field name to match when searching for the right override file
                     (e.g. "model.model" to match by nested key)
        match_value: Value to match against match_field.
        task_overrides: Additional overrides from the task config dict (highest priority).

    Returns:
        Merged config as a plain dict.

    Examples:
        load_conf("llm", section="model", match_field="model.model", match_value="gpt-4o")
        load_conf("imaging", override_name="plain")
        load_conf("text_encoding", override_name="formal_logic", task_overrides={...})
    """
    conf_path = CONF_DIR / subdir

    # Base: structured schema (if available) provides typed defaults
    schema_cls = _SCHEMAS.get(subdir)
    if schema_cls is not None:
        config = OmegaConf.structured(schema_cls)
    else:
        config = OmegaConf.create({})

    # Layer 1: default.yaml
    default_path = conf_path / "default.yaml"
    if default_path.exists():
        loaded = _strip_hydra(OmegaConf.load(default_path))
        config = OmegaConf.merge(config, loaded)

    # Layer 2: named override file OR search by match_field
    if override_name:
        override_path = conf_path / f"{override_name}.yaml"
        if override_path.exists():
            loaded = _strip_hydra(OmegaConf.load(override_path))
            config = OmegaConf.merge(config, loaded)
    elif match_field and match_value:
        for yaml_file in sorted(conf_path.glob("*.yaml")):
            if yaml_file.stem == "default":
                continue
            candidate = _strip_hydra(OmegaConf.load(yaml_file))
            # Support nested match: "model.model" → check candidate.model.model
            val = OmegaConf.select(candidate, match_field, default=None)
            if val == match_value:
                config = OmegaConf.merge(config, candidate)
                break

    # Layer 3: task-level overrides (highest priority)
    if task_overrides:
        config = OmegaConf.merge(config, task_overrides)

    # Convert to plain dict for downstream use
    result = OmegaConf.to_container(config, resolve=True)

    if section:
        return result.get(section, {})
    return result
