"""
Central path definitions for the PTP project.

All project-wide directory paths are defined here.
Import from this module instead of constructing paths manually.
"""
from pathlib import Path

# Project root: .../PTP/
PROJECT_ROOT = Path(__file__).parent.parent

# Input data (parallel to src/)
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATASETS_DIR = DATA_DIR / "original_datasets"
PROCESSED_DATASETS_DIR = DATA_DIR / "processed_datasets"

# Experiment outputs — per-run results, logs, configs (gitignored)
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# Curated analysis — figures, tables for paper (git tracked)
RESULTS_DIR = PROJECT_ROOT / "results"

# Hydra config directory
CONF_DIR = PROJECT_ROOT / "conf"
