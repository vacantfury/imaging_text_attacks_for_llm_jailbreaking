"""
Central path definitions for the project.

All project-wide directory paths are defined here.
Import from this module instead of constructing paths manually.
"""
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Input data
DATA_DIR = PROJECT_ROOT / "data"

# Experiment outputs — per-run results, logs, configs (gitignored)
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# Curated analysis — figures, tables for paper (git tracked)
RESULTS_DIR = PROJECT_ROOT / "results"

# Config directory
CONF_DIR = PROJECT_ROOT / "conf"
