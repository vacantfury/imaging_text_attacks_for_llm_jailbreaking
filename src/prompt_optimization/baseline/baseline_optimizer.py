"""
Baseline optimizer for PTP experiments.

Usage:
    optimizer = BaselineOptimizer(config)  # setup() called in __init__
    result = optimizer.run_baseline()      # predict_baseline() + evaluate()
    result = optimizer.run_naive_optimization()  # predict_naive() + evaluate()

With LLM service reuse (avoids vLLM re-initialization):
    llm_service = LLMServiceFactory.create(...)
    optimizer = BaselineOptimizer(config, llm_service=llm_service)
"""
import os
import traceback
import pandas as pd
from typing import Any
import re

from json_repair import repair_json
import json

from .constants import (
    BASELINE_EXPERIMENT_DATA_DIR,
    NAIVE_OPTIMIZATION_EXPERIMENT_DATA_DIR,
    ANSWER_FIELD,
    EXPLANATION_FIELD,
    RESPONSE_STR,
)
from ..base_optimizer import BaseOptimizer
from ..constants import INTERMEDIATE_RESULTS_FILE
from src.evaluation import evaluate
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BaselineOptimizer(BaseOptimizer):
    """
    Optimizer that supports baseline and naive optimization modes.
    
    Inherits from BaseOptimizer:
    - setup() called in __init__ (data loader, LLM service)
    - Experiment directory and file logging
    - Final result saving
    
    Methods:
    - run_baseline(): predict_baseline() + evaluate()
    - run_naive_optimization(): predict_naive() + evaluate()
    """
    
    def __init__(self, config, llm_service=None):
        """
        Initialize optimizer. Calls setup() via super().__init__().
        
        Args:
            config: Namespace with llm_config, llm_model, data_loader_config,
                    evaluation_config, experiment_dir, naive_extra_instructions
            llm_service: Optional pre-initialized LLM service to reuse
        """
        super().__init__(config, llm_service=llm_service)
        self.config: BaselineConfig = config  # Type hint for IDE
    
    # ==================== Response Parsing ====================
    
    def _parse_response(self, response: str) -> dict[str, str]:
        """
        Parse LLM response to extract answer and explanation fields.
        
        Uses json_repair to handle malformed JSON, then extracts fields from
        dict or first dict in list.
        
        Args:
            response: Raw LLM response string
        
        Returns:
            Dict with 'answer' and 'explanation' fields
        """
        result = {ANSWER_FIELD: "", EXPLANATION_FIELD: ""}
        
        if not response:
            return result
        
        # Try to repair and parse JSON
        try:
            # Strip markdown code block wrappers (```json ... ``` or <json> ... </json>)
            cleaned = response.strip()
            cleaned = re.sub(r'^```\w*\s*\n?', '', cleaned)
            cleaned = re.sub(r'\n?```\s*$', '', cleaned)
            cleaned = re.sub(r'^<json>\s*\n?', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'\n?\s*</json>\s*$', '', cleaned, flags=re.IGNORECASE)
            
            repaired = repair_json(cleaned)
            parsed = json.loads(repaired)
            
            # Handle list: use first dict entry
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict):
                        parsed = item
                        break
                else:
                    # No dict found in list, fallback to raw response
                    result[ANSWER_FIELD] = response.strip()
                    return result
            
            # Extract fields from dict
            if isinstance(parsed, dict):
                result[ANSWER_FIELD] = str(parsed.get(ANSWER_FIELD, ""))
                result[EXPLANATION_FIELD] = str(parsed.get(EXPLANATION_FIELD, ""))
                return result
        except (json.JSONDecodeError, Exception):
            pass
        
        # Final fallback: return raw response as answer
        result[ANSWER_FIELD] = response.strip()
        return result
    
    # ==================== Conversation Preparation ====================
    
    def _prepare_conversations(self, test_dataset, extra_instruction: str = "") -> list[tuple[str, list[tuple[str, Any]]]]:
        """
        Prepare conversations for batch_chat from test dataset.
        
        Args:
            test_dataset: HuggingFace dataset with assembled_text and images columns
            extra_instruction: Optional extra instruction to prepend
        
        Returns:
            List of (data_id, messages) tuples for batch_chat
        """
        dl_config = self.config.data_loader_config
        conversations = []
        for example in test_dataset:
            data_id = str(example[dl_config.data_id_column])
            assembled_text = example.get(dl_config.assembled_text_column, "")
            images = example.get(dl_config.images_column, [])
            
            # Build prompt with optional extra instruction
            if extra_instruction:
                prompt_text = f"{extra_instruction}\n\n{assembled_text}\n\n{RESPONSE_STR}"
            else:
                prompt_text = f"{assembled_text}\n\n{RESPONSE_STR}"
            
            # Create message tuple: (text, images or None)
            image_input = images if images else None
            messages = [(prompt_text, image_input)]
            
            conversations.append((data_id, messages))
        
        return conversations
    
    # ==================== Intermediate Results ====================
    
    def _save_intermediate_results(self, test_dataset, responses: list[tuple[str, str]]) -> pd.DataFrame:
        """
        Save intermediate results with original data and parsed responses.
        
        Args:
            test_dataset: Original test dataset
            responses: List of (data_id, response) tuples from LLM
        
        Returns:
            DataFrame with all results
        """
        dl_config = self.config.data_loader_config
        
        # Create response lookup by data_id
        response_lookup = {data_id: response for data_id, response in responses}
        
        # Build results rows
        rows = []
        for example in test_dataset:
            data_id = str(example[dl_config.data_id_column])
            raw_response = response_lookup.get(data_id, "")
            parsed = self._parse_response(raw_response)
            
            row = {
                dl_config.data_id_column: data_id,
                dl_config.assembled_text_column: example.get(dl_config.assembled_text_column, ""),
                dl_config.label_column: example.get(dl_config.label_column, ""),
                "raw_response": raw_response,
                ANSWER_FIELD: parsed[ANSWER_FIELD],
                EXPLANATION_FIELD: parsed[EXPLANATION_FIELD],
            }
            rows.append(row)
        
        # Create DataFrame and save
        results_df = pd.DataFrame(rows)
        output_path = os.path.join(self.experiment_dir, INTERMEDIATE_RESULTS_FILE)
        results_df.to_csv(output_path, index=False)
        logger.info(f"Saved intermediate results to: {output_path}")
        
        return results_df
    
    # ==================== Prediction Methods ====================
    
    def _get_extra_instruction(self) -> str:
        """
        Get dataset-specific extra instruction for naive optimization.
        
        Returns:
            Extra instruction string, or empty string if not configured
        """
        dataset_name = self.config.data_loader_config.name
        extra = getattr(self.config, 'naive_extra_instructions', None) or {}
        return extra.get(dataset_name, "")
    
    def _predict(self, extra_instruction: str = ""):
        """
        Run LLM inference and save intermediate results.
        
        If intermediate_results.csv already exists, do nothing.
        
        Args:
            extra_instruction: Optional extra instruction to prepend to prompts
        """
        intermediate_path = os.path.join(self.experiment_dir, INTERMEDIATE_RESULTS_FILE)
        
        # Check if intermediate results already exist
        if os.path.exists(intermediate_path):
            logger.info(f"Intermediate results already exist: {intermediate_path}")
            logger.info("Skipping LLM inference.")
            return
        
        # Run LLM inference
        test_dataset = self.data_loader.test_dataset
        if test_dataset is None or len(test_dataset) == 0:
            raise ValueError("No test dataset available")
        
        logger.info(f"Running inference on {len(test_dataset)} test examples...")
        
        # Prepare conversations
        conversations = self._prepare_conversations(test_dataset, extra_instruction)
        if extra_instruction:
            logger.info(f"Using extra instruction: {extra_instruction[:100]}...")
        
        # Call LLM
        logger.info(f"Calling LLM (model: {self.config.llm_model.model_id})...")
        responses = self.llm_service.batch_chat(conversations, is_test=True)
        logger.info(f"Received {len(responses)} responses")
        
        # Save intermediate results
        self._save_intermediate_results(test_dataset, responses)
    
    def predict_baseline(self):
        """
        Run baseline prediction (no extra instruction).
        
        If intermediate_results.csv exists, do nothing.
        """
        logger.info("Running baseline prediction...")
        self._predict(extra_instruction="")
    
    def predict_naive(self):
        """
        Run naive optimization prediction (with extra instruction).
        
        If intermediate_results.csv exists, do nothing.
        """
        logger.info("Running naive optimization prediction...")
        extra_instruction = self._get_extra_instruction()
        self._predict(extra_instruction=extra_instruction)
    
    # ==================== Evaluation ====================
    
    def evaluate(self) -> dict[str, Any]:
        """
        Evaluate predictions from intermediate_results.csv.
        
        Returns:
            Dict with evaluation metrics
        """
        intermediate_path = os.path.join(self.experiment_dir, INTERMEDIATE_RESULTS_FILE)
        
        if not os.path.exists(intermediate_path):
            raise FileNotFoundError(f"Intermediate results not found: {intermediate_path}")
        
        logger.info(f"Loading intermediate results: {intermediate_path}")
        results_df = pd.read_csv(intermediate_path)
        logger.info(f"Loaded {len(results_df)} results")
        
        # Evaluate
        label_column = self.config.data_loader_config.label_column
        question_type = self._get_question_type()
        
        eval_results = evaluate(
            intermediate_result_df=results_df,
            data_id_column=self.config.data_loader_config.data_id_column,
            prediction_column=ANSWER_FIELD,
            label_column=label_column,
            question_type=question_type,
        )
        
        # Log primary metric
        if "accuracy" in eval_results:
            logger.info(f"Accuracy: {eval_results['accuracy']:.2%}")
        
        # Save final results
        self._save_final_results(eval_results)
        
        logger.info("Evaluation completed")
        return eval_results
    
    # ==================== Main Entry Points ====================
    
    def run_baseline(self) -> dict[str, Any]:
        """
        Run baseline: predict_baseline() + evaluate().
        
        Returns:
            Dict with evaluation results and experiment directory path
        """
        logger.info("=== Starting Baseline ===")
        try:
            self._setup_experiment_run(BASELINE_EXPERIMENT_DATA_DIR, mode="baseline")
            self.predict_baseline()
            eval_results = self.evaluate()
            return {
                "evaluation": eval_results,
                "experiment_dir": self.experiment_dir,
            }
        except Exception as e:
            logger.error(f"Baseline failed: {e}")
            logger.error(traceback.format_exc())
            raise
        finally:
            self._cleanup_file_logging()
    
    def run_naive_optimization(self) -> dict[str, Any]:
        """
        Run naive optimization: predict_naive() + evaluate().
        
        Returns:
            Dict with evaluation results and experiment directory path
        """
        logger.info("=== Starting Naive Optimization ===")
        try:
            self._setup_experiment_run(NAIVE_OPTIMIZATION_EXPERIMENT_DATA_DIR, mode="naive")
            self.predict_naive()
            eval_results = self.evaluate()
            return {
                "evaluation": eval_results,
                "experiment_dir": self.experiment_dir,
            }
        except Exception as e:
            logger.error(f"Naive optimization failed: {e}")
            logger.error(traceback.format_exc())
            raise
        finally:
            self._cleanup_file_logging()
