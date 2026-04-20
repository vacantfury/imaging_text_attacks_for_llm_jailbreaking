"""
Base optimizer class for PTP experiments.
Contains shared logic for experiment setup, logging, and result saving.
"""
import json
import logging
import os
from src.llm_utils.base_llm_service import BaseLLMService
from abc import ABC
from typing import Any, Optional
from omegaconf import OmegaConf

from src.utils.mlflow_tracker import MLflowTracker
from src.llm_utils.llm_model import LLMModel

from .constants import (
    LOG_FILE,
    RESULTS_FILE,
    INTERMEDIATE_RESULTS_FILE,
)
from src.data_loader.data_loader import DataLoader
from src.data_loader.constants import MAP_FROM_DATASET_NAME_TO_CONSTANTS, QuestionType
from src.llm_utils.llm_service_factory import LLMServiceFactory
from src.utils.experiment import get_new_experiment_data_dir
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BaseOptimizer(ABC):
    """
    Abstract base class for prompt optimizers.
    
    Provides common functionality:
    - Data loader and LLM service initialization (in setup(), called by __init__)
    - Experiment directory setup
    - File logging setup/cleanup
    - Final result saving
    """
    
    def __init__(self, config, llm_service: Optional[BaseLLMService] = None):
        """
        Initialize optimizer and call setup().
        
        Args:
            config: Namespace/object with attributes:
                - llm_config: DictConfig with LLM settings (from conf/llm/*.yaml)
                - llm_model: LLMModel enum (resolved from model string)
                - data_loader_config: DictConfig with data loader settings
                - evaluation_config: DictConfig with evaluation settings
                - experiment_dir: str or None
            llm_service: Optional pre-initialized LLM service. If None or invalid,
                        a new service will be created based on config.llm_config.
        """
        self.config = config
        self.experiment_dir: Optional[str] = None
        self.data_loader: Optional[DataLoader] = None
        self.llm_service = llm_service
        self._file_handler: Optional[logging.StreamHandler] = None
        self._mlflow_tracker = MLflowTracker()
        
        # Setup data loader and LLM service (if not provided)
        self.setup()
    
    # ==================== Experiment Directory ====================
    
    def _setup_experiment_dir(self, experiment_base_dir: str):
        """
        Set up experiment directory.
        
        If config.experiment_dir is provided, use it directly.
        Otherwise, create a new experiment directory with timestamp.
        """
        if self.config.experiment_dir:
            self.experiment_dir = self.config.experiment_dir
            os.makedirs(self.experiment_dir, exist_ok=True)
            logger.info(f"Using provided experiment directory: {self.experiment_dir}")
        else:
            model = self.config.llm_model
            self.experiment_dir = get_new_experiment_data_dir(
                experiment_dir=experiment_base_dir,
                dataset=self.config.data_loader_config.name,
                model=model.model_id if model else None
            )
            logger.info(f"Created experiment directory: {self.experiment_dir}")
    
    # ==================== File Logging ====================
    
    def _setup_file_logging(self):
        """Set up file handler to save logs to experiment directory."""
        if self.experiment_dir is None:
            return
        
        log_path = os.path.join(self.experiment_dir, LOG_FILE)
        
        # Open file with line buffering (buffering=1) so each line is written immediately
        log_stream = open(log_path, mode='w', encoding='utf-8', buffering=1)
        self._file_handler = logging.StreamHandler(log_stream)
        self._file_handler.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self._file_handler.setFormatter(formatter)
        
        logging.getLogger().addHandler(self._file_handler)
        logger.info(f"Logging to file: {log_path}")
    
    def _cleanup_file_logging(self):
        """Remove file handler, close log file, and end MLflow run."""
        if self._file_handler is not None:
            self._file_handler.flush()
            logging.getLogger().removeHandler(self._file_handler)
            
            if hasattr(self._file_handler, 'stream') and self._file_handler.stream:
                self._file_handler.stream.close()
            self._file_handler.close()
            self._file_handler = None
        
        self._mlflow_tracker.end_run()
    
    # ==================== Setup (called in __init__) ====================
    
    def _is_valid_llm_service(self) -> bool:
        """Check if the current LLM service is valid and usable."""
        from src.llm_utils.base_llm_service import BaseLLMService
        return isinstance(self.llm_service, BaseLLMService)
    
    def setup(self):
        """
        Initialize data loader and LLM service.
        Called automatically by __init__().
        """
        # Setup data loader
        self.data_loader = DataLoader(self.config.data_loader_config)
        self.data_loader.load()
        logger.info(f"Loaded dataset: {self.config.data_loader_config.name}")
        
        # Setup LLM service only if not provided or invalid
        if self._is_valid_llm_service():
            logger.info(f"Using provided LLM service (reusing existing instance)")
        else:
            model = self.config.llm_model
            self.llm_service = LLMServiceFactory.create(
                model=model,
                temperature=getattr(self.config.llm_config, 'temperature', 0.0),
                max_tokens=getattr(self.config.llm_config, 'max_tokens', 0),
            )
            logger.info(f"Initialized LLM service: {model.model_id}")
    
    def _setup_experiment_run(self, experiment_base_dir: str, mode: str = "unknown"):
        """
        Setup for a specific run: experiment directory, file logging, and MLflow.
        """
        self._setup_experiment_dir(experiment_base_dir)
        self._setup_file_logging()
        
        # Start MLflow tracking
        dataset = self.config.data_loader_config.name
        model = self.config.llm_model
        model_id = model.model_id if model else "unknown"
        self._mlflow_tracker.start_run(mode=mode, dataset=dataset, model=model_id)
        self._mlflow_tracker.log_params(self.config.llm_config, self.config.data_loader_config)
    
    # ==================== Question Type ====================
    
    def _get_question_type(self) -> QuestionType:
        """Get the question type for the current dataset."""
        dataset_name = self.config.data_loader_config.name.lower()
        name_lookup = {k.lower(): k for k in MAP_FROM_DATASET_NAME_TO_CONSTANTS.keys()}
        canonical_name = name_lookup.get(dataset_name)
        if canonical_name:
            info = MAP_FROM_DATASET_NAME_TO_CONSTANTS[canonical_name]
            question_type = info.get("question_type", QuestionType.CONSTRAINED)
            return question_type
        return QuestionType.CONSTRAINED
    
    # ==================== Result Saving ====================
    
    def _save_final_results(self, eval_results: dict[str, Any]):
        """
        Save final results with evaluation metrics and full config.
        Also logs metrics and artifacts to MLflow.
        """
        # Deep-convert to plain Python types for JSON serialization
        from omegaconf import OmegaConf
        llm_config_dict = OmegaConf.to_container(self.config.llm_config, resolve=True)
        data_loader_config_dict = OmegaConf.to_container(self.config.data_loader_config, resolve=True)
        
        # Convert LLMModel enum to string for JSON serialization
        if "model" in llm_config_dict:
            llm_config_dict["model"] = str(llm_config_dict["model"])
        
        results = {
            "evaluation": eval_results,
            "config": {
                "llm_config": llm_config_dict,
                "data_loader_config": data_loader_config_dict,
            }
        }
        
        # Store MLflow run ID
        if self._mlflow_tracker.run_id:
            results["mlflow_run_id"] = self._mlflow_tracker.run_id
        
        output_path = os.path.join(self.experiment_dir, RESULTS_FILE)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Saved final results to: {output_path}")
        
        # Log to MLflow
        self._mlflow_tracker.log_metrics(eval_results)
        self._mlflow_tracker.log_artifact(output_path)
        
        # Also log intermediate results if they exist
        intermediate_path = os.path.join(self.experiment_dir, INTERMEDIATE_RESULTS_FILE)
        self._mlflow_tracker.log_artifact(intermediate_path)
