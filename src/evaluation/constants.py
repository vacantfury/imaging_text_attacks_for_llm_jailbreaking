# Column names for open-ended evaluation
BINARY_PREDICTION_COLUMN = "binary_prediction"
RANKED_PREDICTION_COLUMN = "ranked_prediction"
BINARY_LABEL_COLUMN = "binary_label"
RANKED_LABEL_COLUMN = "ranked_label"

# Metric keys for categorical evaluation
ACCURACY = "accuracy"
PRECISION_MICRO = "precision_micro"
RECALL_MICRO = "recall_micro"
F1_MICRO = "f1_micro"
PRECISION_MACRO = "precision_macro"
RECALL_MACRO = "recall_macro"
F1_MACRO = "f1_macro"

# Metric keys for ranking/regression evaluation
MAE = "mae"
MSE = "mse"
RMSE = "rmse"
SPEARMAN_CORR = "spearman_correlation"
PEARSON_CORR = "pearson_correlation"

# Metric keys for open-ended evaluation
NORMALIZED_MAE = "normalized_mae"
QWK = "qwk"

# Evaluation prompt placeholders
QUESTION_PLACEHOLDER = "question"
LABEL_PLACEHOLDER = "label"
PREDICTION_PLACEHOLDER = "prediction"
RANK_MAX_PLACEHOLDER = "rank_max"
REASONING_FIELD = "reasoning"

# LLM judge response field values
CORRECT_VALUE = "correct"
INCORRECT_VALUE = "incorrect"

# Default evaluation settings
DEFAULT_RANK_MAX = 3
DEFAULT_JUDGE_MODEL = "gpt-5-nano"
DEFAULT_JUDGE_MAX_TOKENS = 1024
DEFAULT_JUDGE_TEMPERATURE = 0.0

DEFAULT_EVALUATION_PROMPT = f"""You are an expert evaluator. Your task is to judge whether a model's prediction correctly answers the given question.

## Question:
{{{QUESTION_PLACEHOLDER}}}

## Reference Answer (Ground Truth):
{{{LABEL_PLACEHOLDER}}}

## Model's Prediction:
{{{PREDICTION_PLACEHOLDER}}}

## Instructions:
1. Determine if the prediction is correct ({BINARY_PREDICTION_COLUMN}):
   - 1 if the prediction captures the essential meaning of the reference answer
   - 0 if the prediction is wrong, incomplete, or misleading

2. Rate the quality of the prediction ({RANKED_PREDICTION_COLUMN}):
   - Use a scale from 0 to {{{RANK_MAX_PLACEHOLDER}}}
   - 0 = completely wrong or irrelevant
   - {{{RANK_MAX_PLACEHOLDER}}} = perfect answer, matches the reference exactly
   - Consider partial credit for partially correct answers

## Response Format:
<json>
{{{{
    "{BINARY_PREDICTION_COLUMN}": 1 (for correct) or 0 (for incorrect),
    "{RANKED_PREDICTION_COLUMN}": <integer from 0 to {{{RANK_MAX_PLACEHOLDER}}}>,
    "{REASONING_FIELD}": "<brief explanation for your judgment>"
}}}}
</json>
"""
