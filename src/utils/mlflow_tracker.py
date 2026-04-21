"""
MLflow experiment tracking for Encoding × Modality jailbreaking.

Thin wrapper around MLflow that handles run lifecycle, param/metric logging,
and artifact storage. All data is stored locally in mlruns/ (no server needed).

Usage (called by task.py — not directly):
    tracker = MLflowTracker()
    run_id = tracker.start_run(mode="evaluate", encoding="math", model="gpt-4o", modality="image")
    tracker.log_params(task_config)
    tracker.log_metrics({"attack_success_rate": 45.2, "success_count": 108})
    tracker.log_artifact("/path/to/results.jsonl")
    tracker.end_run()
"""
import os
from typing import Any, Optional

import mlflow

from src.paths import PROJECT_ROOT
from src.utils.logger import get_logger

logger = get_logger(__name__)

# MLflow experiment name
EXPERIMENT_NAME = "encoding_modality_jailbreak"

# Local tracking directory (relative to project root)
TRACKING_URI = f"file://{PROJECT_ROOT / 'mlruns'}"


class MLflowTracker:
    """Thin wrapper for MLflow experiment tracking.
    
    Manages run lifecycle and provides simple methods for logging
    params, metrics, and artifacts. All data stored locally in mlruns/.
    """
    
    def __init__(self):
        self._run_id: Optional[str] = None
        self._active = False
        
        # Point MLflow to local storage
        mlflow.set_tracking_uri(TRACKING_URI)
    
    @property
    def run_id(self) -> Optional[str]:
        """Get the current run ID (None if no active run)."""
        return self._run_id
    
    def start_run(self, mode: str, encoding: str = "",
                  model: str = "", modality: str = "") -> str:
        """Start an MLflow run.
        
        Args:
            mode: Task mode ("text_encode", "imaging", "evaluate")
            encoding: Encoding strategy ("plain", "math", "classical_chinese")
            model: Target model ("gpt-4o", "llava-next", etc.)
            modality: Input modality ("text", "image")
        
        Returns:
            The MLflow run ID (UUID string)
        """
        mlflow.set_experiment(EXPERIMENT_NAME)
        
        parts = [mode]
        if encoding:
            parts.append(encoding)
        if model:
            parts.append(model)
        if modality:
            parts.append(modality)
        run_name = "_".join(parts)
        
        run = mlflow.start_run(run_name=run_name)
        self._run_id = run.info.run_id
        self._active = True
        
        # Set tags for easy filtering in MLflow UI
        tags = {"mode": mode}
        if encoding:
            tags["encoding"] = encoding
        if model:
            tags["model"] = model
        if modality:
            tags["modality"] = modality
        mlflow.set_tags(tags)
        
        logger.info(f"MLflow run started: {run_name} (ID: {self._run_id})")
        return self._run_id
    
    def log_params(self, task_config: dict) -> None:
        """Log task config as MLflow parameters.
        
        Args:
            task_config: The task configuration dict from experiment YAML
        """
        if not self._active:
            return
        
        try:
            params = {}
            for key, value in task_config.items():
                if isinstance(value, dict):
                    # Flatten one level: renderer.font_size, etc.
                    for sub_key, sub_val in value.items():
                        params[f"{key}.{sub_key}"] = str(sub_val)
                else:
                    params[key] = str(value)
            
            mlflow.log_params(params)
            logger.debug(f"Logged {len(params)} params to MLflow")
        except Exception as e:
            # Don't let MLflow errors break the experiment
            logger.warning(f"MLflow param logging failed (non-fatal): {e}")
    
    def log_metrics(self, metrics: dict[str, Any]) -> None:
        """Log evaluation metrics.
        
        Only logs numeric values (int, float). Skips non-numeric fields.
        
        Args:
            metrics: Dict with evaluation metrics (e.g., attack_success_rate)
        """
        if not self._active:
            return
        
        try:
            numeric = {k: v for k, v in metrics.items() if isinstance(v, (int, float))}
            if numeric:
                mlflow.log_metrics(numeric)
                logger.debug(f"Logged {len(numeric)} metrics to MLflow: {list(numeric.keys())}")
        except Exception as e:
            logger.warning(f"MLflow metric logging failed (non-fatal): {e}")
    
    def log_artifact(self, file_path: str) -> None:
        """Log a file as an MLflow artifact.
        
        Args:
            file_path: Absolute path to the file to log
        """
        if not self._active:
            return
        
        try:
            if os.path.exists(file_path):
                mlflow.log_artifact(file_path)
                logger.debug(f"Logged artifact to MLflow: {os.path.basename(file_path)}")
        except Exception as e:
            logger.warning(f"MLflow artifact logging failed (non-fatal): {e}")
    
    def end_run(self) -> None:
        """End the current MLflow run."""
        if not self._active:
            return
        
        try:
            mlflow.end_run()
            logger.info(f"MLflow run ended: {self._run_id}")
        except Exception as e:
            logger.warning(f"MLflow end_run failed (non-fatal): {e}")
        finally:
            self._active = False
