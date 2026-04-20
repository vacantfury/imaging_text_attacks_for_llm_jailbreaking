"""
Experiment directory utilities.
"""
import os
import time


def get_new_experiment_data_dir(experiment_dir: str, dataset: str = None, model: str = None) -> str:
    """
    Create a structured experiment output directory.
    
    Layout: {experiment_dir}/{dataset}/{model_shortname}_{timestamp}/
    
    Examples:
        outputs/baseline_experiment_data/BBEH/gpt-4o-mini_20260216_211530/
        outputs/naive_optimization_experiment_data/M3CoT/pixtral-12b_20260216_211545/
    
    Args:
        experiment_dir: Base directory (e.g., outputs/baseline_experiment_data)
        dataset: Dataset name (e.g., "BBEH"). Creates a subdirectory.
        model: Model identifier (e.g., "mistralai/Pixtral-12B-2409").
               Uses the short name after the last '/'.
    
    Returns:
        Path to the new experiment directory (already created).
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # Build path: base / dataset / model_timestamp
    path = experiment_dir
    if dataset:
        path = os.path.join(path, dataset)
    
    # Use short model name (after last '/')
    model_short = model.split("/")[-1] if model else None
    folder_name = f"{model_short}_{timestamp}" if model_short else timestamp
    
    path = os.path.join(path, folder_name)
    os.makedirs(path, exist_ok=True)
    return path