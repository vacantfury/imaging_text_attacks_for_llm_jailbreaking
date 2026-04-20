"""
Experiment configuration and validation.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class OptimizationMode(str, Enum):
    """Optimization modes for prompt optimization experiments."""
    BASELINE = "baseline"
    NAIVE = "naive"
    # Future modes:
    # GRADIENT = "gradient"
    # BEAM_SEARCH = "beam_search"


@dataclass
class ExperimentConfig:
    """Configuration for an experiment batch.

    Maps to conf/experiment/*.yaml presets.
    Validates fields and provides defaults.
    
    All defaults are in conf/experiment/default.yaml — this dataclass
    only defines the schema and validation logic.
    """

    tasks: list[dict[str, Any]] = field(default_factory=list)
    llm: str = ""
    api_workers: int = 0
    cluster_workers: int = 0
    test_size: Optional[int] = None

    def __post_init__(self):
        """Validate fields after initialization."""
        for task_def in self.tasks:
            if "mode" not in task_def:
                raise ValueError(f"Each task must have a 'mode', got: {task_def}")
            if "dataset" not in task_def:
                raise ValueError(f"Each task must have a 'dataset', got: {task_def}")
            try:
                OptimizationMode(task_def["mode"].lower())
            except ValueError:
                valid = [m.value for m in OptimizationMode]
                raise ValueError(f"Unknown mode: '{task_def['mode']}'. Valid: {valid}")

        if self.api_workers < 0:
            raise ValueError(f"api_workers must be >= 0, got {self.api_workers}")
        if self.cluster_workers < 0:
            raise ValueError(f"cluster_workers must be >= 0, got {self.cluster_workers}")
        if self.test_size is not None and self.test_size < 1:
            raise ValueError(f"test_size must be >= 1 or None, got {self.test_size}")

    @classmethod
    def from_dict(cls, data: dict) -> "ExperimentConfig":
        """Create ExperimentConfig from a dictionary (e.g., parsed YAML).

        Args:
            data: Dict with config values from conf/experiment/*.yaml

        Returns:
            Validated ExperimentConfig instance
        """
        if not data:
            return cls()
        # Only pass known fields to avoid TypeError on unknown keys
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)
