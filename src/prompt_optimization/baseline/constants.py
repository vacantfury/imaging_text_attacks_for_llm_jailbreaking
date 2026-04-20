"""
Constants specific to baseline and naive optimization.
"""
import os
from src.paths import OUTPUTS_DIR

# Experiment data directories for each mode
BASELINE_EXPERIMENT_DATA_DIR = os.path.join(OUTPUTS_DIR, "baseline_experiment_data")
NAIVE_OPTIMIZATION_EXPERIMENT_DATA_DIR = os.path.join(OUTPUTS_DIR, "naive_optimization_experiment_data")

# Response parsing field names
ANSWER_FIELD = "answer"
EXPLANATION_FIELD = "explanation"

# Response instruction template with field names
RESPONSE_STR = f"""
Please respond in a json format.
<json>
{{
    "{ANSWER_FIELD}": "the answer",
    "{EXPLANATION_FIELD}": "the explanation"
}}
</json>
"""
