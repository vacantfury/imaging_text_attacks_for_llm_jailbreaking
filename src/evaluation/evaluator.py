"""
Evaluator for PTP experiments.
Provides evaluation metrics based on question type.
"""
import json
import re
import pandas as pd
import numpy as np
from typing import Any, Optional



from src.data_loader.constants import QuestionType
from src.llm_utils.llm_model import LLMModel
from src.utils.logger import get_logger
from .constants import (
    BINARY_PREDICTION_COLUMN, RANKED_PREDICTION_COLUMN,
    REASONING_FIELD,
    QUESTION_PLACEHOLDER, LABEL_PLACEHOLDER,
    PREDICTION_PLACEHOLDER, RANK_MAX_PLACEHOLDER,
    ACCURACY,
    PRECISION_MICRO, RECALL_MICRO, F1_MICRO,
    PRECISION_MACRO, RECALL_MACRO, F1_MACRO,
    MAE, MSE, RMSE, SPEARMAN_CORR, PEARSON_CORR,
    NORMALIZED_MAE, QWK,
    DEFAULT_RANK_MAX, DEFAULT_JUDGE_MODEL,
    DEFAULT_JUDGE_MAX_TOKENS, DEFAULT_JUDGE_TEMPERATURE,
    DEFAULT_EVALUATION_PROMPT,
)

logger = get_logger(__name__)


class Evaluator:
    """Evaluator for different question types."""
    
    def __init__(
        self,
        intermediate_result_df: Optional[pd.DataFrame] = None,
        intermediate_result_path: Optional[str] = None,
        data_id_column: str = "data_id",
        prediction_column: str = "answer",
        label_column: str = "label",
        question_column: str = "assembled_text",
        question_type: QuestionType = QuestionType.CONSTRAINED,
        evaluation_config=None,
    ):
        """
        Initialize evaluator.
        
        Args:
            intermediate_result_df: DataFrame with predictions and labels (priority if provided)
            intermediate_result_path: Path to CSV file with results (used if df not provided)
            data_id_column: Column name for data IDs
            prediction_column: Column name for model predictions
            label_column: Column name for ground truth labels
            question_column: Column name for question/context text (for open-ended evaluation)
            question_type: Type of question (determines evaluation metrics)
            evaluation_config: DictConfig/dict with evaluation settings (from conf/evaluation/default.yaml)
        """
        self.data_id_column = data_id_column
        self.prediction_column = prediction_column
        self.label_column = label_column
        self.question_column = question_column
        self.question_type = question_type
        if evaluation_config is None:
            evaluation_config = {}
        self.evaluation_config = evaluation_config
        
        # Load data
        if intermediate_result_df is not None:
            self.df = intermediate_result_df
        elif intermediate_result_path is not None:
            self.df = pd.read_csv(intermediate_result_path)
            logger.info(f"Loaded results from: {intermediate_result_path}")
        else:
            raise ValueError("Either intermediate_result_df or intermediate_result_path must be provided")
        
        # Validate columns exist
        required_cols = [prediction_column, label_column]
        missing = [c for c in required_cols if c not in self.df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}. Available: {list(self.df.columns)}")
    
    def _normalize_for_comparison(self, value) -> str:
        """Normalize a value for string comparison."""
        return str(value).strip().lower()
    
    def _try_parse_numeric(self, value) -> Optional[float]:
        """Try to parse a value as numeric, return None if not possible."""
        try:
            # Handle string representations
            val_str = str(value).strip()
            return float(val_str)
        except (ValueError, TypeError):
            return None
    
    def _label_at_front_of_prediction(self, label, prediction) -> bool:
        """
        Check if label lies at the front of prediction.
        Handles both int and str labels.
        
        Args:
            label: Ground truth label (can be int or str)
            prediction: Model prediction string
        
        Returns:
            True if label is at the front of prediction
        """
        # Normalize prediction
        pred_str = str(prediction).strip().lower()
        if not pred_str:
            return False
        
        # Try both str and int forms of label
        label_variants = set()
        label_str = str(label).strip().lower()
        label_variants.add(label_str)
        
        # If label is numeric, also try int form
        try:
            label_int = int(float(label))
            label_variants.add(str(label_int))
        except (ValueError, TypeError):
            pass
        
        # Check if any variant is at front of prediction
        for variant in label_variants:
            if not variant:
                continue
            # Exact match
            if pred_str == variant:
                return True
            # Label at front of prediction
            if pred_str.startswith(variant):
                # Make sure it's not a partial match (e.g., "10" shouldn't match "1")
                # Check if next char is not alphanumeric
                if len(pred_str) > len(variant):
                    next_char = pred_str[len(variant)]
                    if not next_char.isalnum():
                        return True
                else:
                    return True
        
        return False
    
    def _calculate_accuracy(self) -> float:
        """Calculate accuracy by checking if label is at front of prediction."""
        if len(self.df) == 0:
            return 0.0
        
        correct = 0
        for _, row in self.df.iterrows():
            label = row[self.label_column]
            prediction = row[self.prediction_column]
            
            if self._label_at_front_of_prediction(label, prediction):
                correct += 1
        
        return correct / len(self.df)
    
    def _evaluate_categorical(self) -> dict[str, float]:
        """
        Evaluate categorical close-ended questions.
        
        Uses prefix matching: checks if label is at front of prediction.
        Returns accuracy, micro/macro precision, recall, and F1.
        """
        from sklearn.metrics import precision_recall_fscore_support
        
        # Calculate accuracy using prefix matching
        accuracy = self._calculate_accuracy()
        
        # For precision/recall/F1, we need to map predictions to matched labels
        # Create matched predictions based on prefix matching
        y_true = []
        y_pred_matched = []
        
        for _, row in self.df.iterrows():
            label = row[self.label_column]
            prediction = row[self.prediction_column]
            label_normalized = self._normalize_for_comparison(label)
            
            y_true.append(label_normalized)
            
            # If prefix match, use label as prediction; otherwise use normalized prediction
            if self._label_at_front_of_prediction(label, prediction):
                y_pred_matched.append(label_normalized)
            else:
                y_pred_matched.append(self._normalize_for_comparison(prediction))
        
        # Micro-average
        precision_micro, recall_micro, f1_micro, _ = precision_recall_fscore_support(
            y_true, y_pred_matched, average='micro', zero_division=0
        )
        
        # Macro-average
        precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
            y_true, y_pred_matched, average='macro', zero_division=0
        )
        
        return {
            ACCURACY: accuracy,
            PRECISION_MICRO: precision_micro,
            RECALL_MICRO: recall_micro,
            F1_MICRO: f1_micro,
            PRECISION_MACRO: precision_macro,
            RECALL_MACRO: recall_macro,
            F1_MACRO: f1_macro,
        }
    
    def _evaluate_constrained(self) -> dict[str, float]:
        """
        Evaluate constrained questions.
        
        Returns accuracy only.
        """
        return {
            ACCURACY: self._calculate_accuracy(),
        }
    
    def _create_llm_service(self):
        """Create LLM service for judge from evaluation config."""
        from src.llm_utils.llm_service_factory import LLMServiceFactory
        
        judge_cfg = self.evaluation_config.get("judge_llm_config", {})
        model_str = judge_cfg.get("model", DEFAULT_JUDGE_MODEL) if judge_cfg else DEFAULT_JUDGE_MODEL
        temperature = judge_cfg.get("temperature", DEFAULT_JUDGE_TEMPERATURE) if judge_cfg else DEFAULT_JUDGE_TEMPERATURE
        max_tokens = judge_cfg.get("max_tokens", DEFAULT_JUDGE_MAX_TOKENS) if judge_cfg else DEFAULT_JUDGE_MAX_TOKENS
        
        model = LLMModel.from_string(model_str)
        llm_service = LLMServiceFactory.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        logger.info(f"Created LLM judge service: {model.model_id}")
        return llm_service
    
    def format_prompt(self, question: str, label: str, prediction: str) -> str:
        """Format the evaluation prompt with actual values."""
        template = getattr(self.evaluation_config, 'evaluation_prompt', None) or DEFAULT_EVALUATION_PROMPT
        rank_max = getattr(self.evaluation_config, 'rank_max', DEFAULT_RANK_MAX)
        return template.format(**{
            QUESTION_PLACEHOLDER: question,
            LABEL_PLACEHOLDER: label,
            PREDICTION_PLACEHOLDER: prediction,
            RANK_MAX_PLACEHOLDER: rank_max,
        })
    
    def _parse_judge_response(self, response: str) -> dict[str, Any]:
        """
        Parse LLM judge response to extract binary_prediction and ranked_prediction.
        
        Args:
            response: Raw LLM response string
        
        Returns:
            Dict with binary_prediction (0 or 1) and ranked_prediction (0 to rank_max)
        """
        result = {
            BINARY_PREDICTION_COLUMN: 0,
            RANKED_PREDICTION_COLUMN: 0,
            REASONING_FIELD: "",
        }
        
        if not response:
            return result
        
        # Try to extract JSON from <json>...</json> tags
        json_match = re.search(r'<json>\s*(.*?)\s*</json>', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            try:
                parsed = json.loads(json_str)
                result[BINARY_PREDICTION_COLUMN] = int(parsed.get(BINARY_PREDICTION_COLUMN, 0))
                result[RANKED_PREDICTION_COLUMN] = int(parsed.get(RANKED_PREDICTION_COLUMN, 0))
                result[REASONING_FIELD] = str(parsed.get(REASONING_FIELD, ""))
                return result
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
        
        # Fallback: try to parse entire response as JSON
        try:
            parsed = json.loads(response)
            result[BINARY_PREDICTION_COLUMN] = int(parsed.get(BINARY_PREDICTION_COLUMN, 0))
            result[RANKED_PREDICTION_COLUMN] = int(parsed.get(RANKED_PREDICTION_COLUMN, 0))
            result[REASONING_FIELD] = str(parsed.get(REASONING_FIELD, ""))
            return result
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
        
        # Fallback: try to find JSON-like structure with regex
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(0))
                result[BINARY_PREDICTION_COLUMN] = int(parsed.get(BINARY_PREDICTION_COLUMN, 0))
                result[RANKED_PREDICTION_COLUMN] = int(parsed.get(RANKED_PREDICTION_COLUMN, 0))
                result[REASONING_FIELD] = str(parsed.get(REASONING_FIELD, ""))
                return result
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
        
        logger.warning(f"Failed to parse judge response: {response[:200]}...")
        return result
    
    def _process_open_ended_predictions(self) -> None:
        """
        Process open-ended predictions using LLM-as-Judge.
        
        Adds two columns to self.df:
        - binary_prediction: 1 (correct) or 0 (incorrect)
        - ranked_prediction: integer from 0 to rank_max
        """
        llm_service = self._create_llm_service()
        
        # Prepare conversations for batch_chat
        conversations = []
        for idx, row in self.df.iterrows():
            data_id = str(row.get(self.data_id_column, idx))
            
            # Get question, label, prediction for prompt
            question = str(row.get(self.question_column, ""))
            label = str(row.get(self.label_column, ""))
            prediction = str(row.get(self.prediction_column, ""))
            
            # Format the evaluation prompt
            prompt = self.format_prompt(
                question=question,
                label=label,
                prediction=prediction,
            )
            
            # Create message tuple: (text, images or None)
            messages = [(prompt, None)]
            conversations.append((data_id, messages))
        
        logger.info(f"Calling LLM judge for {len(conversations)} examples...")
        
        # Call LLM judge
        responses = llm_service.batch_chat(conversations, is_test=True)
        logger.info(f"Received {len(responses)} responses from LLM judge")
        
        # Create response lookup by data_id
        response_lookup = {data_id: response for data_id, response in responses}
        
        # Parse responses and add columns
        binary_predictions = []
        ranked_predictions = []
        
        for idx, row in self.df.iterrows():
            data_id = str(row.get(self.data_id_column, idx))
            raw_response = response_lookup.get(data_id, "")
            parsed = self._parse_judge_response(raw_response)
            
            binary_predictions.append(parsed[BINARY_PREDICTION_COLUMN])
            ranked_predictions.append(parsed[RANKED_PREDICTION_COLUMN])
        
        # Add columns to dataframe
        self.df[BINARY_PREDICTION_COLUMN] = binary_predictions
        self.df[RANKED_PREDICTION_COLUMN] = ranked_predictions
        
        logger.info(f"Added {BINARY_PREDICTION_COLUMN} and {RANKED_PREDICTION_COLUMN} columns")
    
    def _evaluate_open_ended(self) -> dict[str, float]:
        """
        Evaluate open-ended questions using LLM-as-Judge.
        
        Assumes binary_prediction column contains 1 (correct) or 0 (incorrect).
        Assumes ranked_prediction column contains integer scores (0 to rank_max).
        
        Returns:
            - accuracy: proportion of correct predictions (from binary judgments)
            - normalized_mae: 1 - MAE/rank_max (0 = worst, 1 = perfect)
            - qwk: Quadratic Weighted Kappa between ranked predictions and perfect scores
        """
        from sklearn.metrics import cohen_kappa_score
        
        # Process predictions with LLM-as-Judge
        self._process_open_ended_predictions()
        
        # Check if processing added the required columns
        if BINARY_PREDICTION_COLUMN not in self.df.columns:
            logger.warning(f"Column '{BINARY_PREDICTION_COLUMN}' not found after processing, using placeholder")
            self.df[BINARY_PREDICTION_COLUMN] = 0
        if RANKED_PREDICTION_COLUMN not in self.df.columns:
            logger.warning(f"Column '{RANKED_PREDICTION_COLUMN}' not found after processing, using placeholder")
            self.df[RANKED_PREDICTION_COLUMN] = 0
        
        # Accuracy: proportion judged correct (from binary predictions)
        binary_preds = self.df[BINARY_PREDICTION_COLUMN].astype(float)
        accuracy = binary_preds.mean() if len(binary_preds) > 0 else 0.0
        
        # Ranked predictions and ideal labels (all should be rank_max = perfect)
        rank_max = getattr(self.evaluation_config, 'rank_max', DEFAULT_RANK_MAX)
        ranked_preds = self.df[RANKED_PREDICTION_COLUMN].astype(float).values
        ranked_labels = np.full(len(ranked_preds), rank_max, dtype=float)
        
        # Normalized MAE: 1 - mean(|pred - label|) / rank_max
        if len(ranked_preds) > 0 and rank_max > 0:
            errors = ranked_preds - ranked_labels
            mae = np.mean(np.abs(errors))
            mse = np.mean(errors ** 2)
            rmse = np.sqrt(mse)
            normalized_mae = 1.0 - mae / rank_max
        else:
            normalized_mae = 0.0
            mae = 0.0
            mse = 0.0
            rmse = 0.0
        
        # QWK: Quadratic Weighted Kappa
        if len(ranked_preds) > 0:
            ranked_preds_int = np.clip(np.round(ranked_preds), 0, rank_max).astype(int)
            ranked_labels_int = ranked_labels.astype(int)
            try:
                qwk = cohen_kappa_score(
                    ranked_labels_int, ranked_preds_int,
                    weights='quadratic',
                    labels=list(range(rank_max + 1)),
                )
            except (ValueError, ZeroDivisionError):
                logger.warning("Could not compute QWK, defaulting to 0.0")
                qwk = 0.0
        else:
            qwk = 0.0
        
        return {
            ACCURACY: accuracy,
            MAE: mae,
            MSE: mse,
            RMSE: rmse,
            NORMALIZED_MAE: normalized_mae,
            QWK: qwk,
        }
    
    def _evaluate_ranking(self) -> dict[str, float]:
        """
        Evaluate ranking/ordinal questions.
        
        Works for both discrete ordinal labels (e.g., 0-5) and continuous scores (e.g., 0.0-1.0).
        Returns MAE, MSE, RMSE, Spearman correlation, Pearson correlation, and QWK.
        """
        from scipy.stats import spearmanr, pearsonr
        from sklearn.metrics import cohen_kappa_score
        
        # Parse predictions and labels as numeric
        y_true = []
        y_pred = []
        
        for _, row in self.df.iterrows():
            true_val = self._try_parse_numeric(row[self.label_column])
            pred_val = self._try_parse_numeric(row[self.prediction_column])
            
            if true_val is not None and pred_val is not None:
                y_true.append(true_val)
                y_pred.append(pred_val)
        
        if len(y_true) == 0:
            logger.warning("No valid numeric pairs found for ranking evaluation")
            return {
                MAE: float('nan'),
                MSE: float('nan'),
                RMSE: float('nan'),
                SPEARMAN_CORR: float('nan'),
                PEARSON_CORR: float('nan'),
                QWK: float('nan'),
            }
        
        y_true = np.array(y_true)
        y_pred = np.array(y_pred)
        
        # Calculate error metrics
        errors = y_pred - y_true
        mae = np.mean(np.abs(errors))
        mse = np.mean(errors ** 2)
        rmse = np.sqrt(mse)
        
        # Calculate correlations
        if len(y_true) >= 2:
            spearman_corr, _ = spearmanr(y_true, y_pred)
            pearson_corr, _ = pearsonr(y_true, y_pred)
        else:
            spearman_corr = float('nan')
            pearson_corr = float('nan')
        
        # Calculate QWK (Quadratic Weighted Kappa)
        y_true_int = np.round(y_true).astype(int)
        y_pred_int = np.round(y_pred).astype(int)
        all_labels = list(range(min(y_true_int.min(), y_pred_int.min()),
                                max(y_true_int.max(), y_pred_int.max()) + 1))
        try:
            qwk = cohen_kappa_score(y_true_int, y_pred_int, weights='quadratic', labels=all_labels)
        except (ValueError, ZeroDivisionError):
            logger.warning("Could not compute QWK for ranking, defaulting to 0.0")
            qwk = 0.0
        
        # Also calculate accuracy for discrete ordinal (rounded match)
        accuracy = self._calculate_accuracy()
        
        return {
            ACCURACY: accuracy,
            MAE: mae,
            MSE: mse,
            RMSE: rmse,
            SPEARMAN_CORR: spearman_corr if not np.isnan(spearman_corr) else 0.0,
            PEARSON_CORR: pearson_corr if not np.isnan(pearson_corr) else 0.0,
            QWK: qwk,
        }
    
    def evaluate(self) -> dict[str, Any]:
        """
        Evaluate based on question type.
        
        Returns:
            Dict with evaluation metrics appropriate for the question type.
        """
        logger.info(f"Evaluating {len(self.df)} examples with question_type={self.question_type}")
        
        if self.question_type == QuestionType.CATEGORICAL_CLOSE_ENDED:
            results = self._evaluate_categorical()
        elif self.question_type == QuestionType.CONSTRAINED:
            results = self._evaluate_constrained()
        elif self.question_type == QuestionType.OPEN_ENDED:
            results = self._evaluate_open_ended()
        elif self.question_type == QuestionType.RANKING:
            results = self._evaluate_ranking()
        else:
            logger.warning(f"Unknown question_type: {self.question_type}, falling back to accuracy")
            results = self._evaluate_constrained()
        
        # Add metadata
        results["question_type"] = str(self.question_type.value)
        results["num_examples"] = len(self.df)
        
        logger.info(f"Evaluation results: {results}")
        return results


def evaluate(
    intermediate_result_df: Optional[pd.DataFrame] = None,
    intermediate_result_path: Optional[str] = None,
    data_id_column: str = "data_id",
    prediction_column: str = "answer",
    label_column: str = "label",
    question_column: str = "assembled_text",
    question_type: QuestionType = QuestionType.CONSTRAINED,
    evaluation_config=None,
) -> dict[str, Any]:
    """
    Convenience function to evaluate results.
    
    Args:
        intermediate_result_df: DataFrame with predictions and labels (priority if provided)
        intermediate_result_path: Path to CSV file with results (used if df not provided)
        data_id_column: Column name for data IDs
        prediction_column: Column name for model predictions
        label_column: Column name for ground truth labels
        question_column: Column name for question/context text (for open-ended evaluation)
        question_type: Type of question (determines evaluation metrics)
        evaluation_config: Config for LLM-as-Judge (required for open-ended evaluation)
    
    Returns:
        Dict with evaluation metrics appropriate for the question type:
        - CATEGORICAL_CLOSE_ENDED: accuracy, micro/macro precision, recall, F1
        - CONSTRAINED: accuracy
        - OPEN_ENDED: accuracy, normalized_mae, qwk (via LLM-as-Judge)
        - RANKING: accuracy, MAE, MSE, RMSE, Spearman, Pearson
    """
    evaluator = Evaluator(
        intermediate_result_df=intermediate_result_df,
        intermediate_result_path=intermediate_result_path,
        data_id_column=data_id_column,
        prediction_column=prediction_column,
        label_column=label_column,
        question_column=question_column,
        question_type=question_type,
        evaluation_config=evaluation_config,
    )
    return evaluator.evaluate()
